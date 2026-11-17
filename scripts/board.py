"""board — the dashboard of every open change, served on localhost by `sdlc.py board`.

`sdlc.py` loads this file by path, only when `board` runs, and binds `sdlc` to a live view of its
own globals, as it does `retro.py`: every reader the board shares with `status` (`change_dirs`,
`load_change`, `open_items`, …) is called as `sdlc.<name>`, so a test's stand-in reaches it.

The page (`board.html`, beside this file) polls `/state.json`, which is rebuilt from the change
folders on every request, so the board and the folders can't disagree. A change the factory ran
on (its folder holds `runs/`) adds its rounds, decisions and cost, read from the files the run
left with copies of `factory.py`'s parsing, each pinned to it by a test: the core never imports or
runs the factory. A run the factory stopped (`runs/stopped.md`, at `stage: build`) needs the
person, with the record's problems and its way on, read by `sdlc.factory_stop()` as `status`
reads it. Its card's step track is the step the
supervisor's last reading named (`runs/step.md`), timed against the median of that step in closed
factory runs, read from history once per base-branch tip and kept in memory. Nothing here
writes: three GET routes, every other method refused, and `/file` serves only a file inside an
open change's own folder.

A running board serves this file as it is on disk: each request compares its mtime, and a change
loads it afresh by path (`_Live`) and routes with the new `route()`. A file that won't load (half
written, or broken) keeps the code the board had, and `/state.json`'s `reload_error` says so. The
handler that checks the Host header and sends is the first one's, so `route(root, path, notice)`
is the contract between a running server and a reloaded module.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import statistics
import threading
import urllib.request
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sdlc = None  # sdlc.py's own names, bound by sdlc.py right after it loads this file

SOURCE = Path(__file__)
PAGE = SOURCE.with_name("board.html")
HOST = "127.0.0.1"
# What `/state.json` carries so a second `board` knows the port is already a board's.
MARKER = "sdlc"
CLOSED = ("shipped", "dropped")
GITHUB_RE = re.compile(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")

# The factory's files, read with copies of `factory.py`'s parsing, pinned to it by a test.
VERDICT_RE = re.compile(r"^VERDICT: (PASS|CHANGES)\s*$")
DECISION_RE = re.compile(r"^DECISION: (READY|ESCALATE)\s*$")
CHANGE_RE = re.compile(r"^\s*- CHANGE:\s*(.+?)\s*$")
KEPT_RE = re.compile(r"^\s*- KEPT:\s*([a-z]+):\s*(.+?)\s*$")
DROPPED_RE = re.compile(r"^\s*- DROPPED:\s*([a-z]+):\s*(.+?)\s*$")
LEDGER_RE = re.compile(r"^- \[( |x)\] (D\d+) \(([^,)]+), (blocking|default)\): (.+?)\s*$")
RECONSIDER = "## Reconsider the approach"
# An open box the ledger can't read: a problem, never an answered decision.
OPEN_BOX = "- [ ]"
VERIFIED = "verified.md"
COSTS = Path("runs") / "costs.jsonl"
STOPPED = Path("runs") / "stopped.md"
STEP = Path("runs") / "step.md"
STEP_RE = re.compile(r"^STEP: ([a-z]+)\s*$")
ROUND_RE = re.compile(r"^ROUND: ?(\d*)\s*$")
LIMIT_RE = re.compile(r"^LIMIT: ?(\d*)\s*$")
REVIEWERS_RE = re.compile(r"^REVIEWERS: ?(.*?)\s*$")
SINCE_RE = re.compile(r"^SINCE: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$")
AFTER_RE = re.compile(r"^AFTER: ([a-z]+)\s*$")
SECONDS_RE = re.compile(r"^Seconds: (\d+(?:\.\d+)?)\s*$")
REVIEWER_ROLES = ("code", "security", "test", "behaviour", "ui", "ux")

# A factory card's step track: the six positions of a round, and where each step the record names
# sits on it (`fix` is the gate, fixing). `decide` keeps the position it paused at; `done` is past
# them all. An estimate never fills its bar past `CAP` while the step runs.
TRACK = ("build", "gate", "review", "verify", "rework", "approve")
AT = {"build": 0, "gate": 1, "fix": 1, "review": 2, "verify": 3, "rework": 4, "approve": 5}
CAP = 0.95
# Typical times come from the newest `WINDOW` closed factory changes, and a step's figure at a tier
# only from `MIN_CHANGES` of them or more. Read once per base-branch tip, kept in memory only.
WINDOW = 20
MIN_CHANGES = 3
_HISTORY: dict[tuple[str, str], tuple[str, dict]] = {}
_HISTORY_LOCK = threading.Lock()


# ---------------------------------------------------------------- the state


def state(root: Path) -> dict:
    """Every open change this checkout can see, as `status` finds them, each a card's worth, and
    each shipped or dropped one still waiting on `/sdlc:close`."""
    home = sdlc.main_root(root)
    cfg = sdlc.load_config(home)[0]
    trunk = cfg["git"]["base"]
    issues = _issue_base(home, cfg)
    now = datetime.now(UTC).timestamp()
    history = typical_times(home, trunk)
    # A rebase detaches its worktree's HEAD; `_change_trees()` reads the branch from its record.
    rebasing = {b for _, b in sdlc._change_trees(home)} - {b for _, b in sdlc.worktrees(home)}
    return {
        "board": MARKER, "repo": home.name, "trunk": trunk, "at": now,
        "changes": [
            _entry(root, home, f, trunk, issues, now, history, rebasing=f.name in rebasing)
            for f in _on_board(root)
        ],
    }  # fmt: skip


def _on_board(root: Path) -> list[Path]:
    """The folders the board shows: every open change's, and a shipped or dropped one's while its
    worktree stands, which is what `status` lists as ready to close."""
    closing = {r["branch"] for r in sdlc.ready_to_close(root)}
    return [f for f in sdlc.change_dirs(root) if sdlc._stage(f) not in CLOSED or f.name in closing]


def _issue_base(home: Path, cfg: dict) -> str | None:
    """`https://github.com/<owner>/<repo>/issues/` when changes take their GitHub issue's number,
    read from the remote's URL: nothing records an issue's link, and the board makes no call."""
    try:
        if sdlc.ids_mode(home, cfg) != "github":
            return None
    except Exception:
        return None
    url = sdlc._git(home, "remote", "get-url", cfg["release"]["remote"] or "origin") or ""
    m = GITHUB_RE.search(url)
    return f"https://github.com/{m.group(1)}/{m.group(2)}/issues/" if m else None


def _entry(
    root: Path,
    home: Path,
    folder: Path,
    trunk: str | None,
    issues: str | None,
    now: float,
    history: dict | None = None,
    rebasing: bool = False,
) -> dict:
    """One change's card. A file that can't be read is a `problems` line, never a crash."""
    problems: list[str] = []

    def read(what: str, fn, default):
        try:
            return fn()
        except Exception as e:
            problems.append(f"{what} couldn't be read: {e}")
            return default

    rec = read("intent.md", lambda: sdlc.load_change(folder, root), None) or {
        "id": folder.name.split("-", 1)[0], "slug": folder.name.split("-", 1)[1], "tier": None,
        "stage": None, "title": "", "artifacts": [], "open_questions": 0, "depends_on": [],
        "serves": None, "dir": str(folder), "errors": [],
    }  # fmt: skip
    problems += rec["errors"]
    name = f"{rec['id']}-{rec['slug']}"
    findings = read("findings.md", lambda: sdlc.findings_entries(folder), {"entries": []})
    problems += findings.get("problems", [])
    counts: dict[str, int] = {}
    for f in findings.get("entries", []):
        counts[f["disposition"]] = counts.get(f["disposition"], 0) + 1
    touched = read("its history", lambda: sdlc.last_touched(root, rec, trunk), None)
    entry = {
        "change": name, "id": rec["id"], "slug": rec["slug"], "title": rec["title"],
        "tier": rec["tier"], "stage": rec["stage"], "serves": rec["serves"],
        "depends_on": [f"{d:03d}" for d in rec["depends_on"]],
        "artifacts": rec["artifacts"],
        "unfilled": read("its artifacts", lambda: [
            n for n in rec["artifacts"] if sdlc.is_unfilled(folder / n)
        ], []),
        "open_questions": rec["open_questions"],
        "undone": [i["text"] for i in read("notes.md", lambda: sdlc.open_items(folder), [])],
        "findings": counts,
        "checks": len(read("checks.md", lambda: sdlc.acceptance(folder), {"checks": []})["checks"]),
        "behind": read("the base branch", lambda: sdlc.behind_trunk(home, name, trunk), None),
        "touched_ago": None if touched is None else round(now - touched),
        "issue": f"{issues}{int(rec['id'])}" if issues else None,
        "files": read("the folder", lambda: _files(folder), []),
        "mode": "factory" if (folder / "runs").is_dir() else "manual",
        "rebasing": rebasing,
    }  # fmt: skip
    if entry["mode"] == "manual":
        # The record a gate run by hand left (`sdlc.py gate`); a factory run's gate is its own.
        entry["gate"] = read("build/gate.md", lambda: sdlc.hand_gate(folder, home, trunk), None)
        problems += (entry["gate"] or {}).get("problems", [])
    if entry["mode"] == "factory":
        entry.update(_factory(folder, problems))
        # A stopped run sits at `build`; past it the record is history, and read past.
        entry["stopped"] = (
            read("runs/stopped.md", lambda: _stopped(folder), None)
            if rec["stage"] == "build"
            else None
        )
        entry["progress"] = read(
            "runs/step.md", lambda: _progress(entry, folder, problems, history, now), None
        )
        if entry["progress"]:
            entry["progress"]["plan"] = read(
                "plan.md", lambda: _plan_hint(entry, folder, home, trunk), None
            )
    entry["seen"] = read("its progress", lambda: _seen(entry, folder, home, trunk), None)
    entry["problems"] = problems
    entry["spec_filled"] = "spec.md" in entry["artifacts"] and "spec.md" not in entry["unfilled"]
    # What it needs from the person, by the rules `status` reads too, and whether an escalation
    # is answered: read from its files on every request, never stamped.
    entry["needs"] = sdlc.needs_of(entry)
    entry["answered"] = sdlc.answered(entry)
    entry["next"] = next_action(entry)
    entry["column"] = column(entry)
    return entry


def _seen(entry: dict, folder: Path, home: Path, trunk: str | None) -> str | None:
    """How far a change built by hand has got, past what its `stage:` says: nothing moves that line
    between `plan` (or a Tier 2's `design`) and `shipped`, so the board reads what `status` does.
    `test` once ship's review has written `findings.md`, or once a gate run by hand passed on the
    build as it stands (`sdlc.py gate`'s record, current); `build` once the change touches a path
    outside the change folders and the plugin's own state, in its branch's commits or, in a
    worktree of its own, its uncommitted edits. None when neither says more, and always for a
    factory run, whose stage line the factory moves itself."""
    stage = entry["stage"]
    # A Tier 2 at `plan` has no spec yet: what it touches isn't its build.
    moving = ("plan", "design", "build") if entry["tier"] == 1 else ("design", "build")
    if entry["mode"] != "manual" or stage not in moving:
        return None
    if (folder / "findings.md").is_file():
        return "test"
    gate = entry.get("gate")
    if gate and gate["current"] and gate["verdict"] == "PASS":
        return "test"
    if stage == "build":
        return None
    own = (f"{sdlc.work_rel(home)}/", *(f".sdlc/{name}" for name in sdlc.STATE_FILES))
    paths = _touched(entry, folder, home, trunk)
    return "build" if any(not p.startswith(own) for p in paths) else None


def _touched(entry: dict, folder: Path, home: Path, trunk: str | None) -> list[str]:
    """Every path the change has touched: what its branch changed against the base branch, and in
    a worktree of its own, its uncommitted edits. Nothing from the branch without a base branch."""
    paths = []
    if trunk:
        span = f"refs/heads/{trunk}...refs/heads/{entry['change']}"
        # `-z`, as `_dirty_paths()` reads them: unquoted, so both compare as the same text.
        out = sdlc._git(home, "diff", "-z", "--name-only", "--no-renames", span) or ""
        paths += out.split("\0")
    checkout = sdlc.checkout_of(folder)
    if checkout.resolve() != home.resolve():
        paths += sdlc._dirty_paths(checkout)
    return [p for p in paths if p]


def _plan_named(text: str) -> list[str]:
    """The paths `plan.md`'s `## Files to change` names: each list item's first backtick-quoted
    span, else its first word, less a trailing `:`, `,` or ` (new)`; only one holding a `/` or a
    `.` and no `<`, so a prompt, a line of prose or an item's wrapped line names nothing."""
    named = []
    for line in sdlc._section(sdlc._body_of(text), "Files to change").splitlines():
        item = re.match(r"^(?:[-*+]|\d+[.)])\s+", line)
        if not item:
            continue
        line = line[item.end() :].strip()
        quoted = re.search(r"`([^`]+)`", line)
        token = quoted.group(1) if quoted else (line.split() or [""])[0]
        token = token.strip()
        token = token.removesuffix(" (new)").rstrip(":,").strip()
        if token and ("/" in token or "." in token) and "<" not in token:
            named.append(token)
    return list(dict.fromkeys(named))


def _plan_hint(entry: dict, folder: Path, home: Path, trunk: str | None) -> dict | None:
    """`{"named", "touched"}` for a Tier 2 factory change whose filled `plan.md` names a path:
    how many of those its branch has touched so far (a named directory, by any path under it)."""
    path = folder / "plan.md"
    if entry["tier"] != 2 or not path.is_file() or sdlc.is_unfilled(path):
        return None
    named = _plan_named(path.read_text(encoding="utf-8", errors="replace"))
    if not named:
        return None
    paths = set(_touched(entry, folder, home, trunk))
    hit = [
        n for n in named if n in paths or n.endswith("/") and any(p.startswith(n) for p in paths)
    ]
    return {"named": len(named), "touched": len(hit)}


def _files(folder: Path) -> list[str]:
    return sorted(
        p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file() and not
        p.is_symlink()
    )  # fmt: skip


def _factory(folder: Path, problems: list[str]) -> dict:
    """What a factory run left: its rounds, the approver's decision, the ledger and the cost."""
    rounds = []
    base = folder / "reviews"
    dirs = [p for p in base.glob("round-*") if p.is_dir() and p.name[6:].isdigit()]
    for path in sorted(dirs, key=lambda p: int(p.name[6:])):
        n = int(path.name[6:])
        reviews = {}
        for file in sorted(path.glob("*.md")):
            if file.name == VERIFIED:
                continue
            lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
            m = VERDICT_RE.match(lines[0]) if lines else None
            if not m:
                problems.append(f"reviews/round-{n}/{file.name} doesn't open with a VERDICT line")
                continue
            changes = sum(1 for line in lines[1:] if CHANGE_RE.match(line))
            reviews[file.stem] = {"verdict": m.group(1), "changes": changes}
        verified = None
        if (path / VERIFIED).is_file():
            lines = (path / VERIFIED).read_text(encoding="utf-8", errors="replace").splitlines()
            verified = {
                "kept": sum(1 for line in lines if KEPT_RE.match(line)),
                "dropped": sum(1 for line in lines if DROPPED_RE.match(line)),
            }
        built = (folder / "build" / f"round-{n}.md").is_file()
        rounds.append({"round": n, "built": built, "reviews": reviews, "verified": verified})
    built = sorted(
        int(p.stem[6:]) for p in (folder / "build").glob("round-*.md") if p.stem[6:].isdigit()
    )
    decision, reconsider = None, False
    path = folder / "decision.md"
    if path.is_file():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        m = DECISION_RE.match(lines[0]) if lines else None
        decision = m.group(1) if m else None
        reconsider = RECONSIDER in [line.strip() for line in lines]
        if not m:
            problems.append("decision.md doesn't open with DECISION: READY or ESCALATE")
    pending, assumed, ledger_lines, garbled = [], [], 0, False
    path = folder / "decisions.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        m = LEDGER_RE.match(line)
        ledger_lines += bool(m)
        garbled = garbled or not m and line.startswith(OPEN_BOX)
        if m and m.group(1) == " ":
            item = {"id": m.group(2), "by": m.group(3), "text": m.group(5)}
            (pending if m.group(4) == "blocking" else assumed).append(item)
    if garbled:
        problems.append(sdlc.GARBLED_LEDGER)
    return {
        "rounds": rounds, "built": built, "decision": decision, "pending": pending,
        "assumed": assumed, "cost": cost(folder), "reconsider": reconsider,
        "ledger_lines": ledger_lines,
    }  # fmt: skip


def _stopped(folder: Path) -> dict | None:
    """The stop `factory.py verdicts --record` left in `runs/stopped.md`, as `status` reads it:
    `sdlc.factory_stop()` itself, so the card and `status` can't say two things. None without
    one; a record that won't read is still a stop, whose way on is to read it."""
    return sdlc.factory_stop(folder)


def read_step(text: str) -> dict | None:
    """`runs/step.md`'s fields, as `factory.py`'s `read_step()` reads them (a test pins the two),
    or None when it doesn't open with a `STEP:` line."""
    lines = text.splitlines()
    step = STEP_RE.match(lines[0]) if lines else None
    if not step:
        return None

    def field(regex: re.Pattern) -> str | None:
        found = [m.group(1) for m in map(regex.match, lines) if m]
        return found[0] if found else None

    rnd, limit, names = field(ROUND_RE), field(LIMIT_RE), field(REVIEWERS_RE)
    return {
        "step": step.group(1), "round": int(rnd) if rnd else None,
        "limit": int(limit) if limit else None,
        "reviewers": [n.strip() for n in (names or "").split(",") if n.strip()],
        "since": field(SINCE_RE), "after": field(AFTER_RE),
    }  # fmt: skip


def _since(text: str | None) -> float | None:
    if not text:
        return None
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC).timestamp()


def _progress(
    entry: dict, folder: Path, problems: list[str], history: dict | None, now: float
) -> dict | None:
    """A factory card's step track, the current step's time against the typical one, and the plan
    hint, from the supervisor's last reading (`runs/step.md`) and the run's files: None for a
    stopped run, a record that won't read, or a run with neither a record nor a first build under
    way (`runs/builder.sessions`, no builder report yet)."""
    if entry.get("stopped") or (folder / STOPPED).is_file() and entry["stage"] == "build":
        return None
    path = folder / STEP
    # The approver's decision is the run's end only at the stages it belongs to, as in `column()`:
    # a change put back to `build` is building again, whatever `decision.md` still says.
    if entry.get("decision") and entry["stage"] in ("test", *CLOSED):
        rec = {"step": "done", "round": None, "limit": None, "reviewers": [], "since": None}
    elif path.is_file():
        rec = read_step(path.read_text(encoding="utf-8", errors="replace"))
        if rec is None:
            problems.append(f"{STEP.as_posix()} doesn't open with STEP:")
            return None
    elif (folder / "runs" / "builder.sessions").is_file() and not entry.get("built"):
        mtime = (folder / "runs" / "builder.sessions").stat().st_mtime
        rec = {"step": "build", "round": 1, "limit": None, "reviewers": [], "since": None}
        rec["at"] = mtime
    else:
        return None
    step = rec["step"]
    if step == "stop":
        return None
    paused = step == "decide"
    at = AT.get(rec.get("after") or "") if paused else AT.get(step)
    if step == "done":
        at = len(TRACK)
    if at is None:
        return None
    rnd = rec["round"] or (max(entry.get("built") or [0]) or None)
    steps = []
    for i, name in enumerate(TRACK):
        state = "done" if i < at else "todo" if i > at else "paused" if paused else "current"
        label = name
        if name == "gate" and step == "fix":
            label = "fixing"
        if name == "review" and rnd and rec["reviewers"]:
            label = f"reviews {_reviewed(folder, rnd)}/{len(rec['reviewers'])}"
        steps.append({"name": name, "state": state, "label": label})
    running = step in AT
    start = rec.get("at") or _since(rec["since"])
    elapsed = max(0, round(now - start)) if running and start is not None else None
    key = "rework" if step == "fix" else step
    found = (history or {}).get(f"{key}/{entry['tier']}") if running else None
    typical = found["seconds"] if found else None
    fraction = None
    if typical and elapsed is not None:
        fraction = round(min(elapsed / typical, CAP), 3)
    return {
        "steps": steps, "round": rnd, "limit": rec["limit"], "step": step, "paused": paused,
        "elapsed": elapsed, "typical": typical if fraction is not None else None,
        "fraction": fraction, "samples": found["samples"] if fraction is not None else None,
        "plan": None,
    }  # fmt: skip


def _reviewed(folder: Path, n: int) -> int:
    """How many replies in `reviews/round-<n>/` open with a `VERDICT:` line, `verified.md` aside."""
    count = 0
    for file in (folder / "reviews" / f"round-{n}").glob("*.md"):
        if file.name == VERIFIED:
            continue
        lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
        count += bool(lines and VERDICT_RE.match(lines[0]))
    return count


def typical_times(home: Path, trunk: str | None) -> dict:
    """`{"<step>/<tier>": {"seconds", "samples"}}`: the median seconds of each step at each tier
    over the closed factory changes `history_samples()` reads, where `MIN_CHANGES` or more give a
    sample. Each call runs one `rev-parse`; history is read again only when the tip has moved.
    Empty without a base branch, or when git fails: the card then shows elapsed time alone."""
    if not trunk:
        return {}
    tip = sdlc._git(home, "rev-parse", "--verify", "--quiet", f"refs/heads/{trunk}")
    if not tip:
        return {}
    key = (str(home), trunk)
    with _HISTORY_LOCK:
        cached = _HISTORY.get(key)
        if cached and cached[0] == tip:
            return cached[1]
        try:
            samples = history_samples(home, trunk)
        except Exception:
            samples = {}
        table = {}
        for (step, tier), by in samples.items():
            if len(by) >= MIN_CHANGES:
                values = [v for vs in by.values() for v in vs]
                table[f"{step}/{tier}"] = {
                    "seconds": round(statistics.median(values)), "samples": len(by),
                }  # fmt: skip
        _HISTORY[key] = (tip, table)
        return table


def history_samples(home: Path, trunk: str) -> dict[tuple[str, int], dict[str, list[float]]]:
    """Each step's seconds at each tier, by change, from the newest `WINDOW` `Close` commits on the
    base branch's first-parent line that removed a `runs/costs.jsonl`: the change's own files,
    read at the `Close` commit's parent, where its folder last stood."""
    work = sdlc.work_rel(home)
    out = sdlc._git(
        home, "log", "--first-parent", "--format=%H%x00%s", f"refs/heads/{trunk}", "--",
        f"{work}/*/runs/costs.jsonl",
    ) or ""  # fmt: skip
    closes = []
    for line in out.splitlines():
        sha, _, subject = line.partition("\0")
        name = subject[len("Close ") :].strip() if subject.startswith("Close ") else ""
        if sdlc.DIR_RE.match(name):
            closes.append((sha, name))
        if len(closes) == WINDOW:
            break
    found: dict[tuple[str, int], dict[str, list[float]]] = {}
    for sha, name in closes:
        at = f"{sha}^:{work}/{name}"
        costs = sdlc._git(home, "show", f"{at}/{COSTS.as_posix()}")
        tier = (sdlc.frontmatter_list(sdlc._git(home, "show", f"{at}/intent.md") or "", "tier")
                or [""])[0]  # fmt: skip
        if costs is None or not tier.isdigit():
            continue
        gates = []
        for gate in (sdlc._git(home, "ls-tree", "--name-only", f"{at}/build") or "").splitlines():
            if gate.startswith("round-") and gate.endswith(".gate.md"):
                text = sdlc._git(home, "show", f"{at}/build/{gate}") or ""
                gates += [float(m.group(1)) for m in map(SECONDS_RE.match, text.splitlines()) if m]
        for step, values in step_samples(costs, gates).items():
            if values:
                found.setdefault((step, int(tier)), {})[name] = values
    return found


def step_samples(costs: str, gates: list[float]) -> dict[str, list[float]]:
    """One run's seconds by step, from its `costs.jsonl` rows in the order its sessions ended: the
    first builder's is the build, every later one before the approver a rework (a gate fix among
    them); each run of reviewer rows one review round, as long as its slowest, since they run
    together; each verifier's a verification; the first approver's the approval. What follows the
    approver is the landing's, and a row without an integer `duration_ms` is skipped."""
    out: dict[str, list[float]] = {s: [] for s in TRACK}
    out["gate"] = list(gates)
    together: list[float] = []
    built = False
    for line in costs.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        ms = row.get("duration_ms") if isinstance(row, dict) else None
        if not isinstance(ms, int) or isinstance(ms, bool):
            continue
        role, seconds = row.get("role"), ms / 1000
        if role in REVIEWER_ROLES:
            together.append(seconds)
            continue
        if together:
            out["review"].append(max(together))
            together = []
        if role == "builder":
            out["rework" if built else "build"].append(seconds)
            built = True
        elif role == "verifier":
            out["verify"].append(seconds)
        elif role == "approver":
            out["approve"].append(seconds)
            break
    if together:
        out["review"].append(max(together))
    return out


def cost(folder: Path) -> dict | None:
    """What the run's agents cost, from `runs/costs.jsonl`, as `factory.py`'s `run_cost()` sums
    it (each session's last reported total; a test pins the two), plus their time: None without
    the file."""
    path = folder / COSTS
    if not path.is_file():
        return None
    last: dict[str, dict] = {}
    duration = runs = unknown = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        if not isinstance(row, dict) or not isinstance(row.get("session"), str):
            unknown += 1 if line.strip() else 0
            continue
        runs += 1
        duration += row["duration_ms"] if isinstance(row.get("duration_ms"), int) else 0
        if isinstance(row.get("cost_usd"), int | float) or row["session"] not in last:
            last[row["session"]] = row
    usd, by_role, by_model = 0.0, {}, {}
    for row in last.values():
        value = row.get("cost_usd")
        if not isinstance(value, int | float):
            unknown += 1
            continue
        usd += value
        for split, key in ((by_role, "role"), (by_model, "model")):
            name = str(row.get(key) or "unknown")
            split[name] = round(split.get(name, 0.0) + value, 4)
    return {
        "usd": round(usd, 4), "by_role": by_role, "by_model": by_model, "runs": runs,
        "unknown": unknown, "duration_ms": duration,
    }  # fmt: skip


def next_action(entry: dict) -> str:
    """What a person runs next on the change, from its stage and tier, and for a factory run its
    decision and the decisions its `needs` still holds (`sdlc.needs_of()`, so the step follows the
    card's `needs you:` line): the step `status` and each skill's report name. The first state a
    card holds names it, highest first: a stopped rebase, a missing stage, any other problem (with
    a decision that still waits named before it), shipped or dropped, a factory stop, a decision
    still to make, the approver's decision, a factory build, a red gate, then the stage's own step
    (`PRECEDENCE` and `BOTH` in `tests/test_board.py` pin every pair)."""
    stage, tier = entry.get("seen") or entry["stage"], entry["tier"]
    # A stopped rebase comes first: until it ends, no step of the stage's applies, and its
    # conflicted files may be what won't read. `sdlc.py resolve` finishes or undoes it, and an
    # undo keeps what was resolved under `refs/sdlc/end/<branch>` (`sdlc.RESOLVE_REFS`).
    if entry.get("rebasing"):
        ident = entry["id"]
        return (
            "a rebase is stopped in its worktree: resolve its conflicts, then "
            f"sdlc.py resolve {ident} --continue, or sdlc.py resolve {ident} --abort, which keeps "
            f"the resolved work under refs/sdlc/end/{entry['change']}"
        )
    if entry["problems"] and stage is None:
        return "fix intent.md's frontmatter"
    # The decisions its `needs` still holds: a blocking one at `build`, answered in the session
    # running the factory, or one an escalation at `test` still needs, answered at ship.
    ids = [n.removeprefix("decide ") for n in entry.get("needs") or [] if n.startswith("decide ")]
    decide = f"decide {', '.join(ids)}" + (
        " in the factory's supervisor" if stage == "build" else ""
    )
    # A problem is the card's column at any stage (`column()`), so it is the next step too.
    if entry["problems"]:
        return f"{decide}, and fix what its problems name" if ids else "fix what its problems name"
    if stage in CLOSED:
        return f"/sdlc:close {entry['id']}"
    if entry.get("stopped"):
        return entry["stopped"]["next"]
    if ids and stage == "build":
        return decide
    if ids:
        return f"{decide}, then /sdlc:ship, or /sdlc-factory:land with the others ready"
    if entry.get("decision") and stage == "test":
        return "/sdlc:ship, or /sdlc-factory:land with the others ready"
    if entry["mode"] == "factory" and stage in ("design", "build") and entry.get("built"):
        return "the factory is building it: wait for its decision"
    gate = entry.get("gate")
    if gate and gate["current"] and gate["verdict"] == "FAIL":
        return f"the gate is red: read build/gate.md, fix it, then sdlc.py gate {entry['id']}"
    if stage == "plan":
        return "/sdlc:spec" if tier == 2 else "plan mode, then build it"
    if stage == "design":
        return "plan mode, then build it"
    if stage == "build":
        return "build it, then /sdlc:ship"
    return "/sdlc:ship"


def column(entry: dict) -> str:
    """The board's column: a file that won't read first, at any stage; then a shipped or dropped
    change, waiting on close whatever the factory's files still say; then Needs you exactly when
    `sdlc.needs_of()` names something (a stop or a blocking decision at `build`, an escalation's
    open ledger at `test`, a written spec whose stage never moved), since a factory signal counts
    only at the stage it belongs to; then the approver's decision at `test`, an escalation by now
    answered, as Ready to ship; else how far it has got."""
    stage = entry["stage"]
    if entry["problems"]:
        return "needs-you"
    if stage in CLOSED:
        return "close"
    if entry.get("needs"):
        return "needs-you"
    if stage == "test" and entry.get("decision") in ("READY", "ESCALATE"):
        return "ready"
    return entry.get("seen") or stage or "needs-you"


def file_at(root: Path, change: str, rel: str) -> Path | None:
    """The file `rel` of the folder of change `change`, one the board shows, or None: a path that
    leaves the folder, by `..`, by being absolute or through a link, is never served."""
    if not change or not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        return None
    folders = {f.name: f for f in _on_board(root)}
    folder = folders.get(change)
    if folder is None:
        return None
    target = (folder / rel).resolve()
    if not target.is_relative_to(folder.resolve()) or not target.is_file():
        return None
    return target


# ---------------------------------------------------------------- the server


def route(root: Path, path: str, notice: str | None = None) -> tuple[int, bytes, str]:
    """The answer to a GET of `path`, a Host already checked: (status, body, content type).
    `notice` is the server's word that this file changed and wouldn't load."""
    url = urlparse(path)
    if url.path == "/":
        return 200, PAGE.read_bytes(), "text/html"
    if url.path == "/state.json":
        st = state(root) | ({"reload_error": notice} if notice else {})
        return 200, json.dumps(st, ensure_ascii=False).encode("utf-8"), "application/json"
    if url.path == "/file":
        q = parse_qs(url.query)
        found = file_at(root, q.get("change", [""])[0], q.get("path", [""])[0])
        if found is not None:
            return 200, found.read_bytes(), "text/plain"
    return 404, b"not found\n", "text/plain"


def _load(path: Path):
    """`path` loaded as a fresh module, bound to this one's `sdlc`, as `sdlc.py` binds it."""
    spec = importlib.util.spec_from_file_location("sdlc_board", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not callable(getattr(mod, "route", None)):
        raise ImportError("it defines no route()")
    mod.sdlc = sdlc
    return mod


def _mtime() -> int | None:
    try:
        return SOURCE.stat().st_mtime_ns
    except OSError:
        return None


class _Live:
    """The `route()` a request is answered with: this module's, until `board.py` changes on disk,
    then the changed file's, once it loads. One that won't keeps the last that did, and says why
    until the file changes again."""

    def __init__(self) -> None:
        self.route, self.error, self.mtime = route, None, _mtime()
        self.lock = threading.Lock()

    def current(self) -> tuple:
        with self.lock:
            now = _mtime()
            if now != self.mtime:
                self.mtime = now
                try:
                    self.route, self.error = _load(SOURCE).route, None
                except Exception as e:
                    self.error = (
                        f"{SOURCE.name} changed but won't load ({type(e).__name__}: {e}): "
                        "the board serves the code it had until the file loads"
                    )
            return self.route, self.error


class _Server(ThreadingHTTPServer):
    # Windows lets a second socket take a port another one holds when this is on; elsewhere it
    # only lets a restart take a port its last run left in TIME_WAIT.
    allow_reuse_address = os.name != "nt"
    daemon_threads = True


def _handler(root: Path, port: int) -> type[BaseHTTPRequestHandler]:
    hosts = {f"{HOST}:{port}", f"localhost:{port}"}
    live = _Live()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            # A page elsewhere that points its own name at 127.0.0.1 reads nothing here.
            if self.headers.get("Host") not in hosts:
                return self._send(404, b"not found\n", "text/plain")
            answer, notice = live.current()
            return self._send(*answer(root, self.path, notice))

        def _refuse(self) -> None:
            self._send(405, b"the board only reads\n", "text/plain", {"Allow": "GET"})

        do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = _refuse

        def _send(self, code: int, body: bytes, kind: str, extra: dict | None = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", f"{kind}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                "connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
            )
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def log_message(self, *args) -> None:
            pass

    return Handler


def serve(root: Path, port: int) -> ThreadingHTTPServer:
    """The board's server on 127.0.0.1:`port`, bound but not yet serving, answering only to the
    port it bound: port 0 takes one the OS picks, read back from `server_address`. Raises OSError
    when the port is taken."""
    server = _Server((HOST, port), BaseHTTPRequestHandler)
    server.RequestHandlerClass = _handler(root, server.server_address[1])
    return server


def _is_board(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/state.json", timeout=10) as r:
            return json.loads(r.read().decode("utf-8")).get("board") == MARKER
    except (OSError, ValueError, AttributeError):
        return False


def cmd_board(root: Path, port: int) -> int:
    """Serve the board until stopped. A board already on `port` is reported, not doubled; anything
    else on it is a refusal, naming the port."""
    url = f"http://{HOST}:{port}/"
    try:
        server = serve(root, port)
        url = f"http://{HOST}:{server.server_address[1]}/"  # port 0's is the one the OS picked
    except OSError:
        if _is_board(port):
            print(json.dumps({"url": url, "serving": "already"}, indent=2))
            return 0
        refusal = f"port {port} is in use by something other than a board: pass --port <N>"
        print(json.dumps({"refusals": [refusal]}, indent=2))
        return 1
    print(json.dumps({"url": url, "serving": True}, indent=2), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
