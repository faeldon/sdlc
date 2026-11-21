"""retro — the retrospective's readers, apart from `sdlc.py` so a change to them reads on its own.

`sdlc.py` loads this file by path, as it loads `metrics.py`, and binds `sdlc` here to a live view of
its own names right after: every helper this code shares with the rest of the process (`_git`,
`load_config`, `closed_changes`, `inbox_entries` …) is read as `sdlc.<name>` when it runs, so a
test's stand-in on the loaded `sdlc` module reaches it. Unlike `metrics.py` and `indicators.py` it
is not pure, and it is never run on its own: `sdlc.py retro` and `sdlc.py retro-commit` are its
commands. The tests call this file's own names as `sdlc.retro.<name>`.

In the plugin's own repo alone, with a host list (`.sdlc/hosts.local`, gitignored), it also reads
the host repos the list names, by git reads alone (`hosts_figures()`). Every figure from them is a
number, a bool, null or a word of a fixed vocabulary (`_vocabulary()`: the plugin's own skill,
command, key and template names, its stages and tiers, and the section's own words); each host
record is reduced to that before anything sums it (`_host_safe()`), and a string outside it is
dropped as a last guard (`_scrub()`), so no host's name, path, title or prose reaches a figure,
an insight bundle or a report. Only `sdlc.py hosts` prints paths, to the terminal.

`sdlc` is unbound while this file loads, so a default argument here can't read it. What `status`
and release call on every run (`retro_due()`, `next_up()`, the doc readers, the history walks)
stays in `sdlc.py`.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import math
import re
import statistics
import subprocess
import tomllib
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

sdlc = None  # sdlc.py's own names, bound by sdlc.py right after it loads this file


# Fewer closed changes than this in either window, and the escape rate's trend is `unknown`.
RATE_MIN_CHANGES = 5

# This many closed changes serving no outcome under one seed theme in the window, and the theme
# recurs: an aim the outcomes don't name, for the product pass to propose an outcome for.
NONE_THEME_RECURS = 3


# The closed changes hotspots and co-change read, back past the retrospective's boundary: where
# changes land is structure, and one window is too few changes to show it.
ARCH_LOOKBACK = 30


# Each evidence command's limits: seconds before it's stopped, and characters of output kept.
EVIDENCE_TIMEOUT = 60


EVIDENCE_LIMIT = 20_000


# A `retro.test_times` command's limits: a suite's JUnit report runs to megabytes, and a run that
# makes it can take minutes. A report cut at the limit is a failure, never a partial read.
TIMES_TIMEOUT = 600


TIMES_LIMIT = 5_000_000


# A test is slow when it takes at least this many times the suite's median, and this many seconds.
SLOW_OVER = 10


SLOW_LEAST = 1.0


# The autonomy figure no record holds: see `UNMEASURED`.
OVERTURNED = "an approver's settled call the person overturned"


# Signals the process doc names that history doesn't record, and what would record them.
UNMEASURED = [
    {
        # Ship's side is recorded (`Sdlc-Findings` on its commit); "later" isn't yet.
        "signal": "findings caught at ship vs. found later",
        "needs": "a later change to say which earlier change it fixes",
    },
    {
        "signal": "a test a newer one repeats",
        "needs": "per-test coverage: which lines each test runs",
    },
    {
        "signal": "a test that passes for the wrong reason",
        "needs": "mutation results: which tests still pass when the code they test is broken",
    },
    {
        # The decide skill never asks one, and a hand edit of the ledger has no defined shape.
        "signal": OVERTURNED,
        "needs": "a ledger mark the person's answer writes when it overturns an approver's settled "
        "call",
    },
    {
        # `runs/stopped.md` is removed when its cause clears, and `runs/step.md` overwritten.
        "signal": "a factory stop that cleared with nothing changed",
        "needs": "a committed log of each stop the factory records, and what cleared it",
    },
    {
        # A hand commit on the change's branch is the change's own (`_workarounds()`): nothing
        # tells it from what a command writes there.
        "signal": "a change's own records edited by hand before it landed",
        "needs": "a mark each command leaves on the records it writes, so an edit without one "
        "shows",
    },
]


def _load_indicators():
    """`scripts/indicators.py`, the architecture pass's counts, by path like `metrics.py`: beside
    this file, since it loads before `sdlc` is bound."""
    spec = importlib.util.spec_from_file_location(
        "sdlc_indicators", Path(__file__).with_name("indicators.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


indicators = _load_indicators()


# Side files a host's session never reads: ship's branch for the skills' cases, which
# `SHIP_BRANCHES` names only where the suite is (`_cases_report()`), this plugin's own repo.
OWN_REPO_BRANCHES = {"ship": ("cases.md",)}


def prose_metrics(home: Path, cfg: dict) -> dict:
    """How much each skill is, the plugin's: what every session in a host reads and follows. A
    skill's size is its `SKILL.md`'s, which every run reads; the files beside it, read only when
    their branch applies, are its `branches`, and its commands are counted across them all. And
    the host docs the skills read on top. Tokens are an estimate, bytes / 4. In a host, the
    branches only this plugin's own repo reads (`OWN_REPO_BRANCHES`) are left out."""
    own = sdlc._own_repo(home)

    def size(text: str) -> dict:
        n = len(text.encode("utf-8"))
        return {"lines": len(text.splitlines()), "bytes": n, "est_tokens": n // 4}

    skills = {}
    for path in sorted((sdlc.PLUGIN_DIR / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        side = {
            p.name: p.read_text(encoding="utf-8")
            for p in sorted(path.parent.glob("*.md"))
            if p.name != "SKILL.md"
            and (own or p.name not in OWN_REPO_BRANCHES.get(path.parent.name, ()))
        }
        commands = [c for t in (text, *side.values()) for c in sdlc.bash_commands(t)]
        skills[path.parent.name] = {
            **size(text),
            "commands": len(commands),
            "script_calls": sum("scripts/sdlc.py" in c for c in commands),
            **({"branches": {name: size(t) for name, t in side.items()}} if side else {}),
        }
    docs = {}
    wanted = [(k, cfg["docs"][k]) for k in ("process", "policy", "review") if cfg["docs"][k]]
    for key, rel in [*wanted, *(("context", rel) for rel in cfg["docs"]["context"])]:
        found = sdlc.doc_path(home, key, rel)
        path = Path(found["path"]) if Path(found["path"]).is_absolute() else home / found["path"]
        if found["exists"] and found["path"] not in docs:
            size = path.stat().st_size
            docs[found["path"]] = {"bytes": size, "est_tokens": size // 4}
    script = sdlc.PLUGIN_DIR / "scripts" / "sdlc.py"
    return {
        "estimate": "est_tokens is bytes / 4",
        "skills": skills,
        "docs": docs,
        "sdlc_py_lines": len(script.read_text(encoding="utf-8").splitlines()),
    }


def _release_of(home: Path, cfg: dict, sha: str) -> str | None:
    """The first release tag that holds a change's commit: when its users could have had it. None
    while no release does."""
    pattern = cfg["release"]["tag"].replace("{version}", "*")
    tags = sdlc._git(home, "tag", "--contains", sha, "--list", pattern, "--sort=creatordate")
    return (tags or "").splitlines()[0] if tags else None


def _evidence(
    home: Path, commands: list[str], timeout: float | None = None, limit: int | None = None
) -> list[dict]:
    """Each evidence command's output, run from the repo root, one after another. Passed through
    unread: what it means is the host's, and the retrospective's to judge. A command that fails or
    hangs is a row saying so, never a failed retrospective. The limits are `EVIDENCE_TIMEOUT` and
    `EVIDENCE_LIMIT` unless given, read when it runs."""
    timeout = EVIDENCE_TIMEOUT if timeout is None else timeout
    limit = EVIDENCE_LIMIT if limit is None else limit
    rows = []
    for command in commands:
        row: dict = {"command": command, "exit": None, "output": "", "truncated": False}
        row["error"] = None
        try:
            # Output that isn't UTF-8 (a binary export, a stray byte) is replaced, not raised.
            ran = subprocess.run(
                sdlc._sh(command), cwd=home, capture_output=True, encoding="utf-8",
                errors="replace", timeout=timeout,
            )  # fmt: skip
        except subprocess.TimeoutExpired:
            row["error"] = f"timed out after {timeout}s"
            rows.append(row)
            continue
        except OSError as e:
            row["error"] = str(e)
            rows.append(row)
            continue
        row["exit"] = ran.returncode
        row["output"] = ran.stdout[:limit]
        row["truncated"] = len(ran.stdout) > limit
        if ran.returncode != 0:
            why = ran.stderr.strip()[:500] or "no output"
            row["error"] = f"exited {ran.returncode}: {why}"
        rows.append(row)
    return rows


def _times(home: Path, commands: list[str]) -> dict:
    """The suite's run times, from `retro.test_times`: each command's JUnit XML report through
    `_evidence()` at `TIMES_TIMEOUT` and `TIMES_LIMIT`, read by `indicators.junit_times()`, every
    command's cases pooled. `unset` with no command, `failed` when none gave a case, else `ok`
    with the counts, the median and the `TOP` slowest, `slow` those at least `SLOW_OVER` times
    the median and `SLOW_LEAST` seconds. Each command's row says what it gave, never its output."""
    if not commands:
        return {"state": "unset", "commands": []}
    rows, cases = [], []
    for ran in _evidence(home, commands, timeout=TIMES_TIMEOUT, limit=TIMES_LIMIT):
        row = {k: ran[k] for k in ("command", "exit", "error", "truncated")} | {"cases": None}
        if ran["truncated"] and not row["error"]:
            row["error"] = f"truncated at {TIMES_LIMIT} characters"
        if not row["error"]:
            read = indicators.junit_times(ran["output"])
            row["error"] = read["error"]
            if not read["error"]:
                row["cases"] = len(read["cases"])
                cases += read["cases"]
        rows.append(row)
    if not cases:
        return {"state": "failed", "commands": rows}
    timed = [c for c in cases if not c["skipped"] and c["seconds"] is not None]
    total = sum(c["seconds"] for c in timed)
    mid = statistics.median(c["seconds"] for c in timed) if timed else None
    ranked = sorted(timed, key=lambda c: (-c["seconds"], c["test"]))[: indicators.TOP]
    slowest = [
        {"test": c["test"], "file": c["file"], "seconds": round(c["seconds"], 3),
         "share": round(c["seconds"] / total, 3)}
        for c in ranked
    ]  # fmt: skip
    slow = [
        r for r in slowest if mid and r["seconds"] >= SLOW_OVER * mid and r["seconds"] >= SLOW_LEAST
    ]
    return {
        "state": "ok",
        "commands": rows,
        "tests": len(cases),
        "skipped": sum(1 for c in cases if c["skipped"]),
        "untimed": sum(1 for c in cases if not c["skipped"] and c["seconds"] is None),
        "seconds": round(total, 3),
        "median": None if mid is None else round(mid, 3),
        "slowest": slowest,
        "slow": slow,
    }


def _reader(home: Path, ref: str):
    """A reader of a file's text at `ref`: None when git can't show it. Read as UTF-8, any byte
    that isn't replaced, since a test file's bytes are the host's."""

    def read(path: str) -> str | None:
        shown = subprocess.run(
            ["git", "-C", str(home), "show", f"{ref}:{path}"],
            capture_output=True, encoding="utf-8", errors="replace",
        )  # fmt: skip
        return shown.stdout if shown.returncode == 0 else None

    return read


def _tests(home: Path, cfg: dict, lookback: tuple | None) -> dict:
    """What the pruning pass reads: the suite's run times (`_times()`); the tests whose code moved
    without them over `lookback` (`_lookback()`), each test read as the base branch holds it,
    None without one, as with no base branch; and whether a pass is `due`, when any test is slow
    or drifted."""
    times = _times(home, cfg["retro"]["test_times"])
    drifted = None
    if lookback is not None:
        _, rows, present = lookback
        read = _reader(home, cfg["git"]["base"])
        drifted = indicators.drifted_tests(rows, _kind(cfg), _skip(home), present, read)
    return {"times": times, "drifted": drifted, "due": bool(times.get("slow") or drifted)}


def _product(
    home: Path,
    cfg: dict,
    doc: dict,
    changes: list[dict],
    open_recs: list[dict],
    direction: dict,
    bases: dict[str, str | None],
) -> dict:
    """What the product pass counts: for each open outcome, the changes closed since the last
    retrospective that serve it and the open ones that do; the closed changes that name no outcome
    (`unlinked`, from before the doc) or say `none`, and those by their seeds' themes; the open
    outcomes nothing serves; the open changes still naming one a retrospective has struck
    (`stale`); and the direction doc's open goals and milestones that reach no open outcome
    (`uncited`). Then the evidence."""
    open_ids = [i["id"] for i in doc["items"] if i["status"] == "open"]
    struck = {i["id"] for i in doc["items"] if i["status"] != "open"}
    outcomes: dict[str, dict] = {o: {"closed": [], "open": []} for o in open_ids}
    for rec in changes:
        for o in rec["serves"] or []:
            if o in outcomes:
                moves = [m["text"] for m in rec["moves"] if o in m["ids"]]
                outcomes[o]["closed"].append(
                    {"change": rec["name"], "release": rec["release"], "moves": moves}
                )
    stale = []
    for r in open_recs:
        name = f"{r['id']}-{r['slug']}"
        for o in r.get("serves") or []:
            if o in outcomes:
                outcomes[o]["open"].append(name)
            elif o in struck:
                stale.append({"change": name, "outcome": o})
    return {
        "items": doc["items"],
        "problems": doc["problems"],
        "next_ids": doc["next_ids"],
        "outcomes": outcomes,
        "unlinked": [c["name"] for c in changes if c["serves"] is None],
        "none": [c["name"] for c in changes if c["serves"] == ["none"]],
        "unserved": [o for o, rows in outcomes.items() if not rows["closed"] and not rows["open"]],
        "stale": stale,
        "uncited": _uncited(direction["items"], doc["items"]),
        "none_themes": _none_themes(home, changes, bases),
        "evidence": _evidence(home, cfg["retro"]["evidence"]),
    }


def _uncited(items: list[dict], outcomes: list[dict]) -> list[dict]:
    """The open goals and milestones, in the direction doc's order, whose citations reach no open
    outcome: a goal through the outcomes it ends with, a milestone through its `Serves:` line's
    outcomes and the outcomes of each goal it names, at whatever status. `why` is `none` when it
    reaches no outcome at all, `closed` when all it reaches is struck, and `unknown` when it names
    an id neither doc holds."""
    open_o = {o["id"] for o in outcomes if o["status"] == "open"}
    every_o = {o["id"] for o in outcomes}
    goals = {i["id"]: i for i in items if i["kind"] == "goal"}
    rows = []
    for item in items:
        if item["status"] != "open":
            continue
        reaches: list[str] = []
        unknown = False
        for ref in item["serves"]:
            if ref.startswith("G"):
                unknown |= ref not in goals
                cited = goals[ref]["serves"] if ref in goals else []
            else:
                cited = [ref]
            reaches += [o for o in cited if o not in reaches]
        unknown |= any(o not in every_o for o in reaches)
        if any(o in open_o for o in reaches):
            continue
        why = "unknown" if unknown else "closed" if reaches else "none"
        rows.append({
            "id": item["id"], "kind": item["kind"], "name": item["name"], "title": item["title"],
            "serves": item["serves"], "reaches": reaches, "why": why,
        })  # fmt: skip
    return rows


def _register_at(home: Path, base: str | None, cache: dict[str, list[dict]]) -> list[dict]:
    """The register's entries as `base` held them, read once a base into `cache`; [] with no
    base."""
    if not base:
        return []
    if base not in cache:
        rel = f"{sdlc.work_rel(home)}/{sdlc.INBOX}"
        cache[base] = sdlc.parse_entries(sdlc._git(home, "show", f"{base}:{rel}") or "")
    return cache[base]


def _none_themes(home: Path, changes: list[dict], bases: dict[str, str | None]) -> list[dict]:
    """The closed changes serving no outcome, by the `Theme:` of the seeds their `idea:` names, as
    the register held them at each change's base: ship deletes a change's seeds on its branch, so
    the base is the last the base branch saw of them. A change counts once under each theme, and
    under `(no theme)` when none of its seeds has one. Rows by count, then theme; `recurring` at
    NONE_THEME_RECURS changes, never for `(no theme)`."""
    registers: dict[str, list[dict]] = {}
    grouped: dict[str, list[str]] = {}
    for rec in changes:
        if rec["serves"] != ["none"]:
            continue
        entries = _register_at(home, bases.get(rec["name"]), registers)
        themes: list[str] = []
        for ref in sdlc.ideas_of(rec):
            for e in entries:
                theme = sdlc.ref_matches(ref, e) and sdlc.entry_theme(e)
                if theme and theme not in themes:
                    themes.append(theme)
        for theme in themes or [sdlc.NO_THEME]:
            grouped.setdefault(theme, []).append(rec["name"])
    return [
        {"theme": theme, "changes": names,
         "recurring": theme != sdlc.NO_THEME and len(names) >= NONE_THEME_RECURS}
        for theme, names in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]  # fmt: skip


# A landed change's work class, the first of these whose rule applies (`_work_class()`).
WORK_CLASSES = ("fix", "capability", "process", "debt")


# The guide's nit themes (`guide/process.md`, *Nits*): the plugin's own words for small debt.
DEBT_THEMES = ("docs", "refactor", "robustness", "tests", "style")


def _is_process(home: Path, cfg: dict, paths: list[str]) -> bool:
    """Whether every path a change touched, past the change folders and the register, is under
    `.sdlc/` or is the configured process, review or policy doc; at least one. Setup's record
    (`.sdlc/setup.json`) counts like any other `.sdlc/` path. git's quoted paths are unquoted and
    the docs compared `as_posix()`, so a non-ASCII name matches."""
    skip = {f"{sdlc.work_rel(home)}/{sdlc.INBOX}"}
    docs = {
        Path(rel).as_posix()
        for rel in (cfg["docs"][k] for k in ("process", "review", "policy"))
        if rel and not Path(rel).is_absolute()
    }
    own = [indicators._unquote(p) for p in paths]
    own = [p for p in own if not p.startswith(sdlc.CHANGE_FOLDERS) and p not in skip]
    return bool(own) and all(p.startswith(f"{sdlc.HOST_DIR}/") or p in docs for p in own)


def _work_class(rec: dict, seeds: list[dict], process: bool) -> dict:
    """A change's `{class, by, also}`: the first class in WORK_CLASSES whose rule applies, the
    signal that decided it, and the other classes whose rules applied too. All None (`also` [])
    when none does. `seeds` are the register's entries its `idea:` and `fixes:` name, as its base
    held them."""
    impact = rec.get("impact") or ""
    signals: list[tuple[str, str]] = []
    if rec.get("fixes"):
        signals.append(("fix", "fixes"))
    if rec.get("reworks"):
        signals.append(("fix", "reworks"))
    if any(sdlc.is_bug(e) for e in seeds):
        signals.append(("fix", "bug seed"))
    if impact in ("major", "minor"):
        signals.append(("capability", f"impact: {impact}"))
    if process:
        signals.append(("process", "process paths"))
    if any(sdlc.is_nit(e) for e in seeds):
        signals.append(("debt", "nit seed"))
    theme = next((t for e in seeds if (t := sdlc.entry_theme(e)) in DEBT_THEMES), None)
    if theme:
        signals.append(("debt", f"theme: {theme}"))
    if impact in ("patch", "none"):
        signals.append(("debt", f"impact: {impact}"))
    if not signals:
        return {"class": None, "by": None, "also": []}
    first, by = signals[0]
    return {"class": first, "by": by,
            "also": list(dict.fromkeys(c for c, _ in signals if c != first))}  # fmt: skip


def _work_mix(
    home: Path,
    cfg: dict,
    changes: list[dict],
    bases: dict[str, str | None],
    paths: dict[str, list[str]],
) -> dict:
    """Each change's `work`, set on its record, and the window's mix: `n` classed, `unmeasured`
    no rule classes, the count and share of each class against `n` (shares None at 0), and
    `mixed`, the changes more than one rule applied to."""
    registers: dict[str, list[dict]] = {}
    for rec in changes:
        refs = [*sdlc.ideas_of(rec), *(rec.get("fixes") or [])]
        entries = _register_at(home, bases.get(rec["name"]), registers) if refs else []
        seeds = [e for e in entries if any(sdlc.ref_matches(r, e) for r in refs)]
        process = _is_process(home, cfg, paths.get(rec["name"]) or [])
        rec["work"] = _work_class(rec, seeds, process)
    counts = Counter(rec["work"]["class"] for rec in changes if rec["work"]["class"])
    n = sum(counts.values())
    return {
        "n": n,
        "unmeasured": len(changes) - n,
        "classes": {c: counts[c] for c in WORK_CLASSES},
        "shares": {c: round(counts[c] / n, 2) for c in WORK_CLASSES} if n else None,
        "mixed": sum(bool(rec["work"]["also"]) for rec in changes),
    }


def _tag_times(home: Path, cfg: dict) -> dict[str, str]:
    """Each release tag's creation time, ISO 8601, from one `for-each-ref`."""
    pattern = cfg["release"]["tag"].replace("{version}", "*")
    fmt = "--format=%(refname:short)%00%(creatordate:iso-strict)"
    listed = sdlc._git(home, "for-each-ref", f"refs/tags/{pattern}", fmt) or ""
    return dict(line.split("\x00", 1) for line in listed.splitlines() if "\x00" in line)


def _time_to_users(home: Path, cfg: dict, since: dict | None, changes: list[dict]) -> dict:
    """How long users waited: the median days, to one place, from each change's `Close` to the
    first release tag holding it (0 for a tag made before it), over the `n` released. A change no
    release holds, or whose tag's time can't be read, is `unmeasured`, by reason under `why`,
    never zero days. `releases` is the release tags in the window."""
    times = _tag_times(home, cfg)
    gaps: list[float] = []
    why: Counter = Counter()
    for rec in changes:
        tag = rec["release"] if "release" in rec else _release_of(home, cfg, rec["sha"])
        if not tag:
            why["unreleased"] += 1
            continue
        try:
            gap = datetime.fromisoformat(times[tag]) - datetime.fromisoformat(rec["close_at"])
        except (KeyError, TypeError, ValueError):
            why["no date"] += 1
            continue
        gaps.append(round(max(gap.total_seconds(), 0) / 86400, 1))
    return {
        "n": len(gaps),
        "median_days": round(statistics.median(gaps), 1) if gaps else None,
        "unmeasured": sum(why.values()),
        "why": dict(why),
        "releases": len(sdlc._release_tags(home, cfg, since)),
    }


# What follow-through can never score: Step 7 of the retro skill only reports its intent titles.
NO_INTENTS = "the intent titles a retrospective proposes: nothing records them"


# A follow-through verdict, in the order its counts are given.
FOLLOWED = ("done", "dropped", "carried", "vanished")


def _followed(rows: list[dict]) -> dict:
    """A kind's follow-through: `n` the rows scored, each verdict's count, and the rows."""
    counts = Counter(r["verdict"] for r in rows)
    return {"n": sum(counts[v] for v in FOLLOWED), **{v: counts[v] for v in FOLLOWED},
            "rows": rows}  # fmt: skip


def _seed_follow(
    home: Path, since: dict, trunk: str, changes: list[dict], missing: list[str]
) -> dict | None:
    """The seeds the retrospective at `since` added to the register, each `done` (a change in the
    window names it), `dropped` (a `Retire` subject since names it), `carried` (still in the
    register) or `vanished`. None, and a line in `missing`, when its register can't be read."""
    rel = f"{sdlc.work_rel(home)}/{sdlc.INBOX}"
    at = sdlc._git(home, "show", f"{since['sha']}:{rel}")
    if at is None:
        missing.append(f"the register at the retrospective ({rel})")
        return None
    before = sdlc._git(home, "show", f"{since['sha']}^:{rel}") or ""
    known = {e["id"] for e in sdlc.parse_entries(before)}
    retired = {e["id"] for e in sdlc.retired_entries(home, trunk, since["sha"])}
    current = {e["id"] for e in sdlc.inbox_entries(home)}
    rows = []
    for e in sdlc.parse_entries(at):
        if e["id"] in known:
            continue
        by = next(
            (c["name"] for c in changes
             if any(sdlc.ref_matches(r, e) for r in [*sdlc.ideas_of(c), *(c.get("fixes") or [])])),
            None,
        )  # fmt: skip
        if by:
            rows.append({"id": e["id"], "verdict": "done", "change": by})
        else:
            verdict = (
                "dropped" if e["id"] in retired else "carried" if e["id"] in current else "vanished"
            )
            rows.append({"id": e["id"], "verdict": verdict})
    return _followed(rows)


def _milestone_follow(
    home: Path, cfg: dict, since: dict, trunk: str, missing: list[str]
) -> dict | None:
    """The milestones open in the direction doc at `since`, each by the first that holds: struck
    now (`done` for Done, `dropped` for Dropped or Revised), gone from the doc (`vanished`), every
    grouped row closed, shipped or dropped (`done` with one closed or shipped, else `dropped`), an
    unknown change among them (`unmeasured`, in no count), else `carried`. None, and a line in
    `missing`, when that doc can't be read."""
    rel = cfg["docs"]["direction"]
    text = sdlc._git(home, "show", f"{since['sha']}:{rel}") if rel else None
    if text is None:
        missing.append(f"the direction doc at the retrospective ({rel or 'not configured'})")
        return None
    then = [
        i for i in sdlc.direction_items(text)["items"]
        if i["kind"] == "milestone" and i["status"] == "open"
    ]  # fmt: skip
    now = {i["id"]: i for i in sdlc.direction_items(sdlc._direction_text(home, cfg))["items"]}
    still = [now[i["id"]] for i in then if now.get(i["id"], {}).get("status") == "open"]
    open_names = [p.name for p in sdlc.change_dirs(home)]
    grouped = sdlc._milestone_verdicts(home, still, open_names, trunk) if still else {}
    rows = []
    for item in then:
        cur = now.get(item["id"])
        found = grouped.get(item["id"]) or []
        if cur is None:
            verdict = "vanished"
        elif cur["status"] == "done":
            verdict = "done"
        elif cur["status"] in ("dropped", "revised"):
            verdict = "dropped"
        elif found and all(r["verdict"] in ("closed", "shipped", "dropped") for r in found):
            built = any(r["verdict"] in ("closed", "shipped") for r in found)
            verdict = "done" if built else "dropped"
        elif any(r["kind"] == "change" and r["verdict"] == "unknown" for r in found):
            verdict = "unmeasured"
        else:
            verdict = "carried"
        rows.append({"id": item["id"], "verdict": verdict})
    return _followed(rows)


def _follow_through(home: Path, cfg: dict, since: dict | None, changes: list[dict]) -> dict:
    """Whether the last retrospective's plans were kept: its seeds and the milestones open at it,
    `share` (done + dropped) over the `n` scored, `unmeasured` the milestones that couldn't be,
    and under `missing` each source that couldn't be read, its intent titles always. With no
    earlier retrospective, every figure is null and `n` 0."""
    missing = [NO_INTENTS]
    if not since:
        return {"since": None, "n": 0, "share": None, "unmeasured": 0, "seeds": None,
                "milestones": None,
                "missing": ["no earlier retrospective to follow through on", *missing]}  # fmt: skip
    trunk = cfg["git"]["base"]
    seeds = _seed_follow(home, since, trunk, changes, missing)
    milestones = _milestone_follow(home, cfg, since, trunk, missing)
    kinds = [k for k in (seeds, milestones) if k]
    n = sum(k["n"] for k in kinds)
    kept = sum(k["done"] + k["dropped"] for k in kinds)
    unmeasured = sum(r["verdict"] == "unmeasured" for r in (milestones or {}).get("rows", []))
    return {"since": since["date"], "n": n, "share": round(kept / n, 2) if n else None,
            "unmeasured": unmeasured, "missing": missing, "seeds": seeds,
            "milestones": milestones}  # fmt: skip


def value_band(
    home: Path,
    cfg: dict,
    since: dict | None,
    changes: list[dict],
    bases: dict[str, str | None],
    paths: dict[str, list[str]],
) -> dict:
    """The Value band's figures, the one function `retro()` and `retro_report()` both call: work
    mix (setting each change's `work`), time to users and follow-through."""
    return {
        "work_mix": _work_mix(home, cfg, changes, bases, paths),
        "time_to_users": _time_to_users(home, cfg, since, changes),
        "follow_through": _follow_through(home, cfg, since, changes),
    }


# The totals a retrospective compares, as medians per tier and way of running.
COMPARED = (
    "elapsed", "agent", "response", "away", "blocked", "stops", "required", "prompts",
    "ship_runs", "reenter", "in", "cache_read", "out",
)  # fmt: skip


def _coverage(changes: list[dict], measured, why) -> dict:
    """A headline's reach over the window's `changes`: how many `measured(c)` holds for, of how
    many, `greyed` when that is under half; and `missing_because`, each other change counted under
    `why(c)`, so its counts sum to the changes not measured."""
    missing = Counter(why(c) for c in changes if not measured(c))
    n = len(changes) - sum(missing.values())
    return {
        "coverage": {"measured": n, "of": len(changes), "greyed": 2 * n < len(changes)},
        "missing_because": dict(missing),
    }


def _none_reason(coverage: object) -> str | None:
    """Why close measured a change from history alone: `Sdlc-Coverage: none: <reason>`'s reason,
    without the `key=value` words close appends after it (` lead=failed`, ` runtime=failed`);
    None when the coverage isn't `none:`."""
    text = str(coverage or "")
    if not text.startswith("none:"):
        return None
    # A key holds no `=`, so each word splits one way: no backtracking on `a=b=c` words.
    return re.sub(r"(\s+[^\s=]+=\S*)+$", "", text.removeprefix("none:")).strip()


# Why a closed change has no lead time, by the word close left in `Sdlc-Coverage` (`_lead_why()`).
LEAD_MISSING = {
    "lead=none": "no opened: line",
    "lead=bad-opened": "opened: unreadable",
    "lead=failed": "timing failed",
}


def _lead_why(c: dict) -> str:
    """Why a closed change has no `Sdlc-Lead`, from what its `Close` commit carries alone."""
    m = c.get("metrics")
    if not m:
        return "not measured at close"
    words = str(m.get("coverage") or "").split()
    return next((why for w, why in LEAD_MISSING.items() if w in words),
                "closed before lead time was recorded")  # fmt: skip


def _minutes_measured(c: dict) -> bool:
    """Whether close measured the person's time on a change from its transcripts: its totals,
    and no `none:` coverage, which is elapsed from history alone."""
    m = c.get("metrics") or {}
    return bool(m.get("totals")) and _none_reason(m.get("coverage")) is None


def _minutes_why(c: dict) -> str:
    """Why the person's minutes on a change weren't measured: the `none:` reason, or nothing at
    close."""
    return _none_reason((c.get("metrics") or {}).get("coverage")) or "not measured at close"


def _stop_target(totals: dict, allowance: int) -> int | None:
    """The stops a change was measured against: its own gates plus the allowance. A `Close`
    commit from before `allowance=` was recorded carries one flat `target=` for every change, so
    its target is worked out again from its own `required=` and today's allowance."""
    if "allowance" in totals:
        return totals.get("target")
    required = totals.get("required")
    return required + allowance if isinstance(required, int) else None


def metrics_summary(changes: list[dict], allowance: int | None = None) -> dict:
    """What the `Close` trailers of the changes in range add up to: per tier and way of running,
    the median of each total, its stop target and the stops over it, tokens and agent time per
    stage and role, and ship's findings. Changes close couldn't measure are counted, not guessed
    at. `allowance` defaults to the config's, read when called: `sdlc` isn't bound at load."""
    if allowance is None:
        allowance = sdlc.CONFIG_KEYS["metrics"]["stop_allowance"]

    def median(values: list) -> float | None:
        values = [v for v in values if isinstance(v, int)]
        return statistics.median(values) if values else None

    def over(totals: dict) -> int | None:
        target, stops = _stop_target(totals, allowance), totals.get("stops")
        return stops - target if isinstance(stops, int) and isinstance(target, int) else None

    captured = [c for c in changes if (c.get("metrics") or {}).get("totals")]
    groups: dict[str, dict] = {}
    for c in captured:
        m = c["metrics"]
        key = f"tier {c['tier']}, {m.get('mode') or 'manual'}"
        g = groups.setdefault(key, {"changes": [], "findings": _no_findings()})
        g["changes"].append(m)
        _add_findings(g["findings"], c.get("findings") or {})
    out: dict = {
        "captured": len(captured),
        "uncaptured": len(changes) - len(captured),
        **_coverage(changes, _minutes_measured, _minutes_why),
        "prompts": _prompt_report(captured),
        "extra": _extra_report(captured),
        "groups": {},
    }
    for key, g in groups.items():
        ms = g["changes"]
        stages = sorted({s for m in ms for s in m["stages"]}, key=sdlc.metrics.STAGES.index)
        roles = sorted({r for m in ms for r in m["roles"]})
        out["groups"][key] = {
            "changes": len(ms),
            "median": {
                **{k: median([m["totals"].get(k) for m in ms]) for k in COMPARED},
                "over": median([over(m["totals"]) for m in ms]),
            },
            "target": median([_stop_target(m["totals"], allowance) for m in ms]),
            "stages": {
                s: {
                    k: median([(m["stages"].get(s) or {}).get(k) for m in ms])
                    for k in ("elapsed", "agent", "response", "away", "gate", "extra", "cache_read")
                }
                for s in stages
            },
            "roles": {
                r: {
                    k: sum((m["roles"].get(r) or {}).get(k) or 0 for m in ms)
                    for k in ("runs", "agent", "cache_read", "out")
                }
                for r in roles
            },
            "findings": g["findings"],
            "in_change": _in_change_summary(ms, median),
        }
    return out


def _prompt_report(captured: list[dict]) -> dict:
    """The tool prompts across the window, from each `Close` commit's `Sdlc-Prompt` lines: each
    name's asks and rejections and how many changes it came from, most asked first, and how many
    changes ran in each permission mode. Only commits that carry `prompts=` are `recorded`: an
    older one's `permission=` counted questions and plan approvals, and is never read here."""
    names: dict[str, dict] = {}
    modes: Counter = Counter()
    recorded = 0
    for c in captured:
        m = c["metrics"]
        if not isinstance(m["totals"].get("prompts"), int):
            continue
        recorded += 1
        for mode in str(m["totals"].get("prompt_modes") or "-").split(","):
            modes[mode] += 1
        for name, p in (m.get("prompts") or {}).items():
            row = names.setdefault(name, {"asked": 0, "rejected": 0, "changes": 0})
            row["asked"] += p.get("asked") or 0
            row["rejected"] += p.get("rejected") or 0
            row["changes"] += 1
    ordered = dict(sorted(names.items(), key=lambda kv: (-kv[1]["asked"], kv[0])))
    return {"recorded": recorded, "names": ordered, "modes": dict(sorted(modes.items()))}


def _extra_report(captured: list[dict]) -> dict:
    """The extra stops across the window, from each `Close` commit's `Sdlc-Extra` lines: each
    kind's count and how many changes it came from, and the harness entries and other commands
    left out of the stops. Only commits that carry `harness=` on `Sdlc-Totals` are `recorded`: an
    older one counted those as `extra`, unclassified, and is never read here as none. Each skill's
    `after_gate` stops come from the `Sdlc-AfterGate` lines (`after_gate_by`); a recorded commit
    without them names no skill, and its `after_gate` stops are `after_gate_unnamed`."""
    kinds = {k: {"count": 0, "changes": 0} for k in sdlc.metrics.EXTRA_KINDS}
    by_skill: dict[str, dict] = {}
    recorded = harness = command = unnamed = 0
    for c in captured:
        m = c["metrics"]
        if not isinstance(m["totals"].get("harness"), int):
            continue
        recorded += 1
        harness += m["totals"]["harness"]
        command += m["totals"].get("command") or 0
        for kind, row in kinds.items():
            n = sum((s.get(kind) or 0) for s in (m.get("extra") or {}).values())
            row["count"] += n
            row["changes"] += 1 if n else 0
        named = m.get("after_gate") or {}
        if not named:
            unnamed += sum((s.get("after_gate") or 0) for s in (m.get("extra") or {}).values())
        for skill, fields in named.items():
            row = by_skill.setdefault(skill, {"count": 0, "changes": 0})
            row["count"] += fields.get("stops") or 0
            row["changes"] += 1
    return {
        "recorded": recorded, "kinds": kinds, "harness": harness, "command": command,
        "after_gate_by": dict(sorted(by_skill.items())), "after_gate_unnamed": unnamed,
    }  # fmt: skip


def _records_at(home: Path, rec: dict):
    """`show` and `listing` over a closed change's folder at its own commit, as
    `factory_records` takes them: `show(rel)` the file `<folder>/<rel>`, or None; `listing(rel)`
    every path under `<folder>/<rel>`, one a line, relative to the folder."""
    sha, folder = rec["sha"], f"{sdlc.work_rel(home)}/{rec['name']}"

    def show(rel: str) -> str | None:
        return sdlc._git(home, "show", f"{sha}:{folder}/{rel}")

    def listing(rel: str) -> str:
        listed = sdlc._git(home, "ls-tree", "-r", "--name-only", sha, f"{folder}/{rel}") or ""
        return "\n".join(path[len(folder) + 1 :] for path in listed.splitlines())

    return show, listing


def _share(part: int, n: int) -> float | None:
    """`part / n` to two places, or None when there is nothing to divide by."""
    return round(part / n, 2) if n else None


def _cost_why(c: dict, waste: bool = False) -> str:
    """Why a change's cost (174 R8), or with `waste` its waste (R9), isn't measured: no rows (by
    hand, or a factory run that recorded none), rows from before purposes, or rows with no
    dollars, which are never read as $0."""
    if not c["rows"]:
        factory = (c["rec"].get("metrics") or {}).get("mode") == "factory"
        return "no agent runs recorded" if factory else "built by hand"
    if waste and c["untagged"]:
        return "runs recorded before purposes"
    return "no cost reported"


def _sums(rows: list[dict]) -> dict:
    """Rows' dollars (a row with none adds nothing), minutes and count."""
    return {
        "usd": round(sum(r["usd"] or 0 for r in rows), 4),
        "minutes": round(sum(r["minutes"] for r in rows), 4),
        "runs": len(rows),
    }


def _cost(home: Path, changes: list[dict], dropped: list[dict]) -> dict:
    """The Cost pillar's figures (174 R7–R9), from each closed change's own commit and each
    dropped change's tip, through `factory_records.spend_rows()` alone: dollars and agent-minutes
    per landed change by tier, over the landed changes with dollars; the waste share and its parts,
    over the changes (landed and dropped) with dollars and no row from before purposes; spend by
    role and model, every run; the rows with no dollars (`unknown`) and with no purpose
    (`untagged`); and `changes`, each change's own, which `cmd_retro()` prints only with
    `--metrics`. Each figure carries its `n` and coverage, and is null, never 0, with nothing to
    divide by. `_landed` is each landed change's read (`rec`, `usd`, `rows`), which `by_way()`
    weighs and its callers pop. Read-only."""
    fr = sdlc.factory_records
    read = []
    for rec, gone in [*((c, False) for c in changes), *((d, True) for d in dropped)]:
        spent = fr.spend_rows(_records_at(home, rec)[0], dropped=gone)
        rows = spent["rows"]
        known = [r["usd"] for r in rows if r["usd"] is not None]
        read.append({
            "rec": rec, "dropped": gone, "rows": rows, "untagged": spent["untagged"],
            "unknown": spent["unknown"], "usd": round(sum(known), 4) if known else None,
            "minutes": round(sum(r["minutes"] for r in rows), 4),
        })  # fmt: skip
    landed = [c for c in read if not c["dropped"]]
    per_change: dict[str, dict] = {}
    for c in landed:
        if c["usd"] is not None:
            per_change.setdefault(str(c["rec"]["tier"]), []).append(c)
    for tier, group in per_change.items():
        usd, minutes = [c["usd"] for c in group], [c["minutes"] for c in group]
        per_change[tier] = {
            "n": len(group),
            "usd": {"median": round(statistics.median(usd), 4), "total": round(sum(usd), 4)},
            "minutes": {
                "median": round(statistics.median(minutes), 4), "total": round(sum(minutes), 4),
            },
        }  # fmt: skip

    def weighed(c: dict) -> bool:
        return c["usd"] is not None and not c["untagged"]

    measured = [r for c in read if weighed(c) for r in c["rows"]]
    parts = {p: _sums([r for r in measured if r["part"] == p]) for p in fr.PARTS}
    lost = [r for r in measured if r["part"] in fr.WASTE]
    usd, of_usd = _sums(lost)["usd"], _sums(measured)["usd"]
    minutes, of_minutes = _sums(lost)["minutes"], _sums(measured)["minutes"]
    waste = {
        "usd": usd, "of_usd": of_usd, "share": _share(usd, of_usd),
        "minutes": minutes, "of_minutes": of_minutes, "minutes_share": _share(minutes, of_minutes),
        "n": sum(1 for c in read if weighed(c)), "parts": parts,
        **_coverage(read, weighed, lambda c: _cost_why(c, waste=True)),
    }  # fmt: skip

    def split(key: str) -> dict:
        names = sorted({r[key] for c in read for r in c["rows"]})
        return {
            name: {
                **_sums([r for c in read for r in c["rows"] if r[key] == name]),
                "changes": sum(1 for c in read if any(r[key] == name for r in c["rows"])),
            }
            for name in names
        }

    untagged = [r for c in read for r in c["rows"] if r["part"] == "untagged"]
    return {
        # Each landed change's dollars, for `by_way()`; its callers pop it before showing `cost`.
        "_landed": landed,
        "per_change": per_change,
        **_coverage(landed, lambda c: c["usd"] is not None, _cost_why),
        "waste": waste,
        "by_role": split("role"),
        "by_model": split("model"),
        "unknown": sum(c["unknown"] for c in read),
        "untagged": {
            "runs": len(untagged),
            "usd": _sums(untagged)["usd"],
            "changes": sum(1 for c in read if c["untagged"]),
        },  # fmt: skip
        "changes": [
            {
                "name": c["rec"]["name"],
                "tier": c["rec"]["tier"],
                "state": "dropped" if c["dropped"] else "landed",
                "usd": c["usd"],
                "minutes": c["minutes"],
                "runs": len(c["rows"]),
                "parts": {
                    p: _sums([r for r in c["rows"] if r["part"] == p])["usd"]
                    for p in fr.PARTS
                    if any(r["part"] == p for r in c["rows"])
                },
            }
            for c in read
            if c["rows"]
        ],  # fmt: skip
    }


def _autonomy(home: Path, changes: list[dict]) -> tuple[dict, list[str]]:
    """How often the window's factory changes needed the person, from the records each run left
    in its change's commit (`factory_records.autonomy_counts()`), and a problem for each decision
    file no answer reads. A change built by hand counts only in `by_hand`: every figure is over
    the factory changes, carries its `n`, and is null, never 0, when `n` is 0."""
    problems: list[str] = []
    found = []
    for rec in changes:
        counts = sdlc.factory_records.autonomy_counts(*_records_at(home, rec))
        if counts is not None:
            found.append((rec, counts))
        for rel in (counts or {}).get("unread") or []:
            problems.append(
                f"{rec['name']}: {rel} holds no answer the script reads, so its escalations "
                "aren't counted"
            )
    n = len(found)
    read = [c for _, c in found if not c["unread"]]
    esc = sum(c["escalations"] for c in read)

    def get(part: str, key: str) -> int:
        return sum(c[part][key] for _, c in found)

    asked = get("blocking", "answered") + get("defaults", "kept") + get("defaults", "changed")
    asked += get("looks", "seen") + get("looks", "checked")
    ruled = get("defaults", "kept") + get("defaults", "changed")
    looked = get("looks", "seen") + get("looks", "checked")
    by = Counter(((rec.get("landed") or {}).get("by") or "shipped") for rec, _ in found)
    mends = get("mends", "build") + get("mends", "landing")
    return {
        "factory": n,
        "by_hand": len(changes) - n,
        "escalations": {
            "total": esc,
            "changes": sum(1 for c in read if c["escalations"]),
            "per_change": _share(esc, len(read)),
            "n": len(read),
        },
        "asked": {
            "blocking": get("blocking", "answered"),
            "default": ruled,
            "look": looked,
            "per_change": _share(asked, n),
            "n": n,
            # A hand-built change asks the person nothing the records count (189 R11).
            "missing_because": {"built by hand": len(changes) - n} if len(changes) > n else {},
        },
        "kept_default": {
            "kept": get("defaults", "kept"),
            "changed": get("defaults", "changed"),
            "rate": _share(get("defaults", "kept"), ruled),
            "n": ruled,
            "confirmed": get("defaults", "confirmed"),
            "settled": get("defaults", "settled"),
        },
        "overturned": {"count": None, "n": 0, "unmeasured": OVERTURNED},
        "auto_landed": {
            "auto": by["auto"],
            "person": by["person"],
            # Autopilot's landings (216), apart from both: never the person's, never `auto`.
            "autopilot": by["autopilot"],
            "shipped": n - by["auto"] - by["person"] - by["autopilot"],
            "share": _share(by["auto"], n),
            "n": n,
        },
        "spurious_stops": {
            "build": get("mends", "build"),
            "landing": get("mends", "landing"),
            "changes": sum(1 for _, c in found if any(c["mends"].values())),
            "per_change": _share(mends, n),
            "n": n,
        },
        "looks": {
            "seen": get("looks", "seen"),
            "checked": get("looks", "checked"),
            "open": get("looks", "open"),
            "seen_share": _share(get("looks", "seen"), looked),
            "n": looked,
        },
    }, problems


# The causes a train ejects for (`landing.py`'s `_record_ejection()`), each counted, 0 included.
EJECT_CAUSES = ("gate", "review", "refusal", "stop")


def _spread(values: list[float]) -> dict:
    """`values`' count, median and nearest-rank 85th percentile, each null with none."""
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "median": round(statistics.median(ordered), 2) if ordered else None,
        "p85": _p85(ordered),
    }


def _gate_spreads(read: list[dict]) -> dict:
    """The round and landing gates' attempts over `read` (each a factory change's counts), as
    their seconds and slot waits; an attempt without a `Waited:` line counts in `seconds` alone."""
    out = {}
    for kind in ("round", "land"):
        tried = [g for c in read for g in c["gates"] if g["kind"] == kind]
        out[kind] = {
            "seconds": _spread([g["seconds"] for g in tried if g["seconds"] is not None]),
            "wait": _spread([g["waited"] for g in tried if g["waited"] is not None]),
        }
    return out


def _pipeline(home: Path, changes: list[dict], previous: list[dict] | None) -> dict:
    """Where the pipeline spends time and takes risks (175), from the records each factory run
    left in its change's commit (`factory_records.pipeline_counts()`) and its `Sdlc-Landed`: the
    gates' seconds and slot waits, this window and the one before (`previous`, None with no
    retrospective before it); the red-gate rate per build; the landing's gates, ejections,
    bisections, base moves, accept stops and conflicts, over the changes a factory landing made;
    the share of runs at full depth; and the landings with paths no review read. A change built by
    hand counts only in `by_hand`; every figure carries its `n` and is null, never 0, with nothing
    to divide by. Mends are `autonomy.spurious_stops`', never counted twice. `changes`, each
    change's own figures, is printed only with `--metrics`. Read-only."""
    counts = sdlc.factory_records.pipeline_counts
    window = [{"rec": rec, "counts": counts(*_records_at(home, rec))} for rec in changes]
    found = [c["counts"] for c in window if c["counts"] is not None]
    before = None
    if previous is not None:
        read = (counts(*_records_at(home, rec)) for rec in previous)
        before = _gate_spreads([c for c in read if c is not None])

    builds = [red for c in found for red in c["builds"]]

    def landed(c: dict) -> bool:
        return c["counts"] is not None and c["counts"]["landed"]

    lands = [c["counts"] for c in window if landed(c)]
    n = len(lands)
    land_gates = sum(1 for c in lands for g in c["gates"] if g["kind"] == "land")
    causes = {cause: 0 for cause in EJECT_CAUSES}
    for c in lands:
        for cause, k in c["ejections"].items():
            causes[cause] = causes.get(cause, 0) + k
    bisected = {
        (commit, file) for c in lands for prefix, verdict, commit, file in c["train_gates"]
        if verdict == "FAIL" and prefix > 1
    }  # fmt: skip
    moves = [c["moves"] for c in lands if c["moves"] is not None]
    deep = [c["depth"] for c in found if c["depth"] is not None]

    def by_landing(c: dict) -> bool:
        return ((c["rec"].get("landed") or {}).get("by")) in ("auto", "person", "autopilot")

    def recorded(c: dict) -> bool:
        value = (c["rec"].get("landed") or {}).get("unreviewed")
        return value == "unknown" or isinstance(value, int)

    landings = [c for c in window if by_landing(c)]
    said = [c["rec"]["landed"]["unreviewed"] for c in landings if recorded(c)]
    paths = [v for v in said if isinstance(v, int) and v > 0]
    return {
        "factory": len(found),
        "by_hand": len(changes) - len(found),
        "gates": {"window": _gate_spreads(found), "previous": before},
        "red_gate": {
            "builds": len(builds),
            "red": sum(builds),
            "rate": _share(sum(builds), len(builds)),
            "n": len(builds),
        },  # fmt: skip
        "landing": {
            "n": n,
            **_coverage(
                window,
                landed,
                lambda c: "built by hand" if c["counts"] is None else "no landing record",
            ),  # fmt: skip
            "gates": {"total": land_gates, "per_change": _share(land_gates, n)},
            "ejections": {
                **causes,
                "total": sum(causes.values()),
                "changes": sum(1 for c in lands if c["ejections"]),
            },  # fmt: skip
            "bisections": {"total": len(bisected), "per_change": _share(len(bisected), n)},
            "base_moves": {
                "total": sum(moves),
                "per_change": _share(sum(moves), len(moves)),
                "changes": sum(1 for m in moves if m),
            },  # fmt: skip
            "accept_stops": {
                "total": sum(c["accepts"] for c in lands),
                "changes": sum(1 for c in lands if c["accepts"]),
                "per_change": _share(sum(c["accepts"] for c in lands), n),
            },
            "conflicts": {
                "landing": sum(c["resolves"] for c in lands),
                "ship": sum(c["conflicts"] for c in lands),
            },
        },
        "depth": {
            "full": deep.count("full"),
            "light": deep.count("light"),
            "share": _share(deep.count("full"), len(deep)),
            "n": len(deep),
            **_coverage(found, lambda c: c["depth"] is not None, lambda c: "depth not recorded"),
        },  # fmt: skip
        "unreviewed": {
            "with_paths": len(paths),
            "paths": sum(paths),
            "unknown": sum(1 for v in said if v == "unknown"),
            "none": sum(1 for v in said if v == 0),
            "n": len(said),
            **_coverage(landings, recorded, lambda c: "unreviewed not recorded"),
        },  # fmt: skip
        "changes": [
            {
                "name": c["rec"]["name"],
                "gates": {
                    kind: sum(1 for g in c["counts"]["gates"] if g["kind"] == kind)
                    for kind in ("round", "land")
                },
                "red_builds": sum(c["counts"]["builds"]),
                "landed": c["counts"]["landed"],
                "moves": c["counts"]["moves"],
                "ejections": c["counts"]["ejections"],
                "accepts": c["counts"]["accepts"],
                "resolves": c["counts"]["resolves"],
                "conflicts": c["counts"]["conflicts"],
                "depth": c["counts"]["depth"],
                "unreviewed": (c["rec"].get("landed") or {}).get("unreviewed"),
            }
            for c in window
            if c["counts"] is not None
        ],
    }


def _no_findings() -> dict:
    """What a group's ship findings add up to before any change is counted."""
    return {
        "important": 0, "nit": 0, "preexisting": 0,
        "passes": dict.fromkeys(sdlc.FINDING_PASSES, 0),
        "dispositions": {d: dict.fromkeys(sdlc.FINDING_PASSES, 0) for d in sdlc.COUNTED},
        "answered": 0,
        "fresh": 0, "fresh_wrong": 0, "fresh_counted": 0,
    }  # fmt: skip


def _add_findings(total: dict, found: dict) -> None:
    """Add one change's `Sdlc-Findings` to `total`. Counts add whatever the trailer's age; its
    dispositions add only when it carries them, and `answered` counts those changes, so a
    trailer from before dispositions is unknown there, never zero."""
    for k in ("important", "nit", "preexisting"):
        total[k] += found.get(k) if isinstance(found.get(k), int) else 0
    for p in sdlc.FINDING_PASSES:
        total["passes"][p] += found.get(p) if isinstance(found.get(p), int) else 0
    # The fresh reviewer's count, only from trailers that carry it, as `fresh_counted` says.
    if isinstance(found.get("fresh"), int):
        total["fresh_counted"] += 1
        total["fresh"] += found["fresh"]
        total["fresh_wrong"] += found.get("fresh_wrong") or 0
    if not all(d in found for d in sdlc.COUNTED):
        return
    total["answered"] += 1
    for d in sdlc.COUNTED:
        # `fixed=correctness:2` reads as a dict, `fixed=0` as 0, and a lone `pass:n` as a dict.
        by = found[d] if isinstance(found[d], dict) else {}
        for p in sdlc.FINDING_PASSES:
            total["dispositions"][d][p] += by.get(p) or 0


def _in_change_summary(ms: list[dict], median) -> dict:
    """Rework within the changes of one group: how often each stage went through first time, the
    share of changes where every stage seen did, the median of each rework count, and what spikes
    cost. Retro's own `rework` (a later change fixing this one) is another measure."""
    happy = [m["happy"] for m in ms if m.get("happy")]
    first_time = {}
    # A ship that stopped only for its own review's findings (`fixed`) went through first time; a
    # trailer from before that value has only yes and no, read as they always were.
    for stage in sdlc.metrics.HAPPY_STAGES:
        marks = [h.get(stage) for h in happy if h.get(stage) in ("yes", "fixed", "no")]
        if marks:
            first_time[stage] = round(sum(m != "no" for m in marks) / len(marks), 2)
    ships = [h.get("ship") for h in happy if h.get("ship") in ("yes", "fixed", "no")]
    judged = [h for h in happy if h.get("of")]
    done = [m["rework"] for m in ms if m.get("rework")]
    spikes = [m["spike"] for m in ms if m.get("spike")]
    return {
        "first_time": first_time,
        "ship_fixed": round(ships.count("fixed") / len(ships), 2) if ships else None,
        "all_first": (
            round(sum(1 for h in judged if h["first"] == h["of"]) / len(judged), 2)
            if judged
            else None
        ),
        "rework": {
            k: median([d.get(k) for d in done]) for k in sorted({k for d in done for k in d})
        },
        "spike": {
            "changes": len(spikes),
            **{k: sum(s.get(k) or 0 for s in spikes) for k in ("segments", "agent", "edits")},
        },
    }


# What a dropped change's trailers add up to: the time and tokens spent on work that didn't ship.
DROPPED_COST = ("elapsed", "agent", "in", "cache_read", "out")


def dropped_cost(dropped: list[dict]) -> dict:
    """The `Drop` trailers in range summed by the stage each change reached, and by tier and way of
    running. Changes close couldn't measure are counted, not guessed at."""
    captured = [d for d in dropped if (d.get("metrics") or {}).get("totals")]
    by_stage: dict[str, dict] = {}
    by_group: dict[str, dict] = {}
    for d in captured:
        m = d["metrics"]
        group = f"tier {d['tier']}, {m.get('mode') or 'manual'}"
        for key, table in ((d.get("dropped_at", "unknown"), by_stage), (group, by_group)):
            sums = table.setdefault(key, {"changes": 0, **dict.fromkeys(DROPPED_COST, 0)})
            sums["changes"] += 1
            for k in DROPPED_COST:
                value = m["totals"].get(k)
                sums[k] += value if isinstance(value, int) else 0
    return {
        "captured": len(captured),
        "uncaptured": len(dropped) - len(captured),
        "by_stage": by_stage,
        "by_group": by_group,
    }


CLOCKS = ("agent", "response", "away", "blocked")


# The ways a change was built, as its `Close` commit's `Sdlc-Mode` records them, in the order
# every by-way figure gives them; `unknown` when it records none (`_way()`).
WAYS = ("factory", "manual", "unknown")


def _way(c: dict) -> str:
    """A closed change's way of building, from `Sdlc-Mode` alone: `factory`, `manual`, or
    `unknown` when its `Close` commit records neither. Never guessed from its folder or branch."""
    mode = (c.get("metrics") or {}).get("mode")
    return mode if mode in ("factory", "manual") else "unknown"


# The parts of a change's lead time (`metrics.LEAD_PARTS`), as the report names them.
LEAD_NAMES = {
    "queued": "queued", "agents": "agents working", "idle": "idle",
    "ready_wait": "ready and waiting", "landing": "landing",
}  # fmt: skip


def _p85(ordered: list):
    """The nearest-rank 85th percentile of `ordered`, already sorted; None when it is empty."""
    return ordered[math.ceil(0.85 * len(ordered)) - 1] if ordered else None


def lead_view(changes: list[dict]) -> dict:
    """Lead time from each change's `Sdlc-Lead`: per tier and way of building (`Sdlc-Mode`)
    the count, median and nearest-rank 85th percentile of `lead`, and the same per way over every
    tier (`ways`, each of WAYS, n 0 and null with none); each part's share, its sum
    over the changes that recorded it against their leads' sum, with how many those are; and
    how many changes have the line and how many don't, which move no figure."""
    led = []
    for c in changes:
        lead = (c.get("metrics") or {}).get("lead")
        if isinstance(lead, dict) and isinstance(lead.get("lead"), int):
            led.append((c, lead))
    groups: dict[tuple[str, str], list[int]] = {}
    for c, lead in led:
        groups.setdefault((str(c["tier"]), _way(c)), []).append(lead["lead"])
    rows = []
    for (tier, way), leads in sorted(groups.items()):
        leads.sort()
        rows.append({
            "tier": tier, "way": way, "n": len(leads), "median": statistics.median(leads),
            "p85": _p85(leads),
        })  # fmt: skip
    ways = {}
    for way in WAYS:
        leads = sorted(lead["lead"] for c, lead in led if _way(c) == way)
        ways[way] = {"n": len(leads), "median": statistics.median(leads) if leads else None,
                     "p85": _p85(leads)}  # fmt: skip
    shares = {}
    for part in LEAD_NAMES:
        had = [lead for _, lead in led if isinstance(lead.get(part), int)]
        total = sum(lead["lead"] for lead in had)
        if had and total:
            share = round(sum(lead[part] for lead in had) / total, 2)
            shares[part] = {"share": share, "changes": len(had)}
    measured = {id(c) for c, _ in led}
    return {
        "measured": len(led), "unmeasured": len(changes) - len(led), "groups": rows,
        "ways": ways, "shares": shares,
        **_coverage(changes, lambda c: id(c) in measured, _lead_why),
    }  # fmt: skip


def _lead_text(lead: dict) -> str:
    """The report's lead-time block: its table, then the shares and what isn't measured."""
    table = _table(
        ["Tier", "Way", "Changes", "Median lead", "85th percentile"],
        [[r["tier"], r["way"], r["n"], _hm(r["median"]), _hm(r["p85"])] for r in lead["groups"]],
    )
    said = [
        f"{LEAD_NAMES[k]} {round(v['share'] * 100)}% (of {v['changes']})"
        for k, v in lead["shares"].items()
    ]
    text = f"\n\nLead time's shares: {', '.join(said)}." if said else ""
    n = lead["unmeasured"]
    if n:
        text += f" {n} change{' has' if n == 1 else 's have'} no lead time recorded."
    return table + text


# What ran underneath a change, as its `Sdlc-Runtime` names each (`underneath()`).
UNDERNEATH = ("claude", "models", "plugin")


def _underneath_side(changes: list[dict]) -> dict:
    """One window's `Sdlc-Runtime` values, each with the changes that ran on it, and how many
    changes recorded the line. A change closed before it gives its models from its `Sdlc-Role`
    `model=`, and counts as unrecorded for the rest."""
    found = {k: Counter() for k in UNDERNEATH}
    recorded = 0
    for c in changes:
        m = c.get("metrics") or {}
        ran = m.get("runtime") if isinstance(m.get("runtime"), dict) else None
        recorded += ran is not None
        values = {k: {v for v in str((ran or {}).get(k) or "").split(",") if v} for k in UNDERNEATH}
        if not values["models"]:
            roles = m.get("roles") if isinstance(m.get("roles"), dict) else {}
            values["models"] = {
                v for r in roles.values() if isinstance(r, dict)
                for v in str(r.get("model") or "").split(",") if v
            }  # fmt: skip
        for k, vs in values.items():
            found[k].update(vs)
    return {
        **{k: dict(sorted(found[k].items())) for k in UNDERNEATH},
        "recorded": recorded, "unrecorded": len(changes) - recorded,
    }  # fmt: skip


def underneath(changes: list[dict], previous: list[dict] | None) -> dict:
    """What the window's changes ran on against the last window's (`_previous_window()`, None
    with no earlier window): each side's values, and per dimension whether they changed, null
    when either side recorded none. Read from the `Close` trailers alone."""
    now = _underneath_side(changes)
    before = _underneath_side(previous) if previous is not None else None
    changed = {
        k: None if before is None or not now[k] or not before[k] else set(now[k]) != set(before[k])
        for k in UNDERNEATH
    }
    return {"window": now, "previous": before, "changed": changed}


def _previous_window(home: Path, trunk: str | None, since: dict | None) -> list[dict] | None:
    """The changes closed in the window before this one: from the retrospective before `since`
    (the start of history with none) to `since`; None when there is no `since`."""
    if not since:
        return None
    bounds = sdlc.retrospectives(home, trunk)
    at = next((i for i, b in enumerate(bounds) if b["sha"] == since["sha"]), 0)
    older = bounds[at + 1]["sha"] if at + 1 < len(bounds) else None
    return sdlc.closed_changes(home, older, since["sha"])


def process_views(
    changes: list[dict], dropped: list[dict], rework: list[dict], questions: list[dict],
    bugs: dict, since: dict | None, today: date, previous: list[dict] | None = None,
) -> dict:  # fmt: skip
    """The retrospective's process views, the report's figures: cycle time, throughput, where the
    time went, how many changes ran at once and what that did to them, rework and escapes, and
    what ran underneath against `previous`, the last window's changes (`underneath()`). Only
    changes close measured (`Sdlc-Totals` with `elapsed`) are in the four timed views, which are
    None with none; the rest count every change. No figure combines them into one."""

    def median(values: list) -> float | None:
        values = [v for v in values if isinstance(v, int)]
        return statistics.median(values) if values else None

    def totals(c: dict) -> dict:
        return (c.get("metrics") or {}).get("totals") or {}

    def mode(c: dict) -> str | None:
        return (c.get("metrics") or {}).get("mode") or None

    measured = [c for c in changes if isinstance(totals(c).get("elapsed"), int)]
    factory = [c for c in changes if mode(c) == "factory"]
    by_tier = lambda rows: {str(t): [c for c in rows if c["tier"] == t]  # noqa: E731
                            for t in sorted({c["tier"] for c in rows}, key=str)}  # fmt: skip
    # Each week's tiers, ways and work classes (`unclassed` when no `work` was set on it).
    weeks: dict[str, tuple[Counter, Counter, Counter]] = {}
    for c in changes:
        day = date.fromisoformat(c["close_date"])
        week = (day - timedelta(days=day.weekday())).isoformat()
        tiers, ways, classes = weeks.setdefault(week, (Counter(), Counter(), Counter()))
        tiers[str(c["tier"])] += 1
        ways[_way(c)] += 1
        classes[(c.get("work") or {}).get("class") or "unclassed"] += 1
    out: dict = {
        "window": {
            "since": since["date"] if since else None,
            "today": today.isoformat(),
            "closed": len(changes),
            "tiers": dict(sorted(Counter(str(c["tier"]) for c in changes).items())),
            "dropped": len(dropped),
            "measured": len(measured),
            "unmeasured": len(changes) - len(measured),
            "factory": len(factory),
            "mode_unknown": sum(1 for c in changes if not mode(c)),
        },
        "throughput": [
            {"week": w, "tiers": dict(sorted(n.items())), "total": sum(n.values()),
             "ways": {k: ways[k] for k in WAYS},
             "classes": {k: classes[k] for k in (*WORK_CLASSES, "unclassed")}}
            for w, (n, ways, classes) in sorted(weeks.items())
        ],
        "rework": {
            "links": len(rework),
            "reworked": len({r["reworks"] for r in rework}),
            "per_change": round(len(rework) / len(changes), 2) if changes else None,
            "questions": len(questions),
        },
        "escapes": {
            "reported": sum((bugs.get("reported") or {}).values()),
            "fixed": sum((bugs.get("fixed") or {}).values()),
            "days_to_fix": (bugs.get("days_to_fix") or {}).get("median"),
            "rate": ((bugs.get("rate") or {}).get("window") or {}).get("rate"),
            "previous": ((bugs.get("rate") or {}).get("previous") or {}).get("rate"),
            "trend": (bugs.get("rate") or {}).get("trend"),
            # The rate rests on every closed change: none is left out of it.
            **_coverage(changes, lambda c: True, lambda c: ""),
        },
        "review_sources": bugs.get("review_sources") or {},
        # A window the factory built nothing in has no landing to catch anything: no figure.
        "landing_catches": bugs.get("landing_catches") if factory else None,
        "cycle": None, "time": None, "wip": None, "capacity": None,
        # Each tier's reach for the person's minutes, over all its changes, measured or not, so a
        # null median says why even when `time` is None (189 R11).
        "response": {tier: _coverage(rows, _minutes_measured, _minutes_why)
                     for tier, rows in by_tier(changes).items()},
        "lead": lead_view(changes),
        "underneath": underneath(changes, previous),
    }  # fmt: skip
    if not measured:
        return out
    out["cycle"] = {
        tier: {
            "n": len(rows),
            "elapsed": median([totals(c)["elapsed"] for c in rows]),
            "max": max(totals(c)["elapsed"] for c in rows),
            "agent": median([totals(c).get("agent") for c in rows]),
            "days_open": median([c.get("days_open") for c in rows]),
        }
        for tier, rows in by_tier(measured).items()
    }
    sums = {k: sum(v for c in measured if isinstance(v := totals(c).get(k), int)) for k in CLOCKS}
    spent = sums["agent"] + sums["response"] + sums["away"]
    out["time"] = {
        "tiers": {
            tier: {k: median([totals(c).get(k) for c in rows]) for k in CLOCKS}
            for tier, rows in by_tier(measured).items()
        },
        "sums": sums,
        "agent_share": round(sums["agent"] / spent, 2) if spent else None,
    }
    # A change's span ends at its `Close` commit and starts `elapsed` minutes before it; its
    # concurrency is the most spans open at once while it was, its own included.
    spans = []
    for c in measured:
        end = datetime.fromisoformat(c["close_at"]) if c.get("close_at") else None
        if end:
            spans.append((end - timedelta(minutes=totals(c)["elapsed"]), end, c))
    at_once = []
    for start, end, c in spans:
        points = sorted(s for s, _, _ in spans if start <= s <= end) or [start]
        most = max(sum(1 for s, e, _ in spans if s <= p <= e) for p in [start, *points])
        at_once.append((most, c))
    counts = [n for n, _ in at_once]
    out["wip"] = {
        "spans": len(at_once),
        "median": statistics.median(counts) if counts else None,
        "max": max(counts, default=None),
    }
    rows: dict[str, list[dict]] = {"1": [], "2": [], "3+": []}
    for n, c in at_once:
        rows["1" if n == 1 else "2" if n == 2 else "3+"].append(c)
    out["capacity"] = {
        key: {"n": len(cs), **{k: median([totals(c).get(k) for c in cs])
                               for k in ("elapsed", "agent", "response")}}
        for key, cs in rows.items()
    }  # fmt: skip
    return out


def _median(values: list):
    """The median of `values`, None with none."""
    return statistics.median(values) if values else None


def _no_way(way: str) -> dict:
    """Why a figure of one way is null when the window closed no change built that way: the one
    reason the escape rate and the lead time by way both give."""
    return {f"no {way} change in the window": 0}


def by_way(
    changes: list[dict], lead: dict, landed: list[dict], bugs: dict, since: dict | None,
    today: date,
) -> dict:  # fmt: skip
    """The window's figures by way of building (`_way()`), each of WAYS in every part, with its
    `n`: the closed `changes`; `lead`, `lead_view()`'s `ways`; `throughput`, each way's closed
    changes per week over the window's span (from `since`, or with none the first close, to
    `today`; at least a day), null with `why` under a week, where a day's changes would read as a
    week's; `cost`, tokens (`in + cache_read + out` over the changes whose
    totals came from transcripts) and dollars (over `landed`, `_cost()`'s, with dollars), each
    with its `missing_because`; and `escapes`, `bugs_retro()`'s rate by way. A median with `n` 0
    is null. Pure: no git."""
    of = {way: [c for c in changes if _way(c) == way] for way in WAYS}
    start = since["date"] if since else min((c["close_date"] for c in changes), default=None)
    days = (today - date.fromisoformat(start)).days if start else 0
    weeks = max(days, 1) / 7

    def tokens(c: dict) -> int:
        totals = c["metrics"]["totals"]
        return sum(v for k in ("in", "cache_read", "out") if isinstance(v := totals.get(k), int))

    def cost(way: str) -> dict:
        told = [c for c in of[way] if _minutes_measured(c)]
        spent = [c for c in landed if _way(c["rec"]) == way]
        usd = [c["usd"] for c in spent if c["usd"] is not None]
        median = _median(usd)
        return {
            "tokens": {
                "n": len(told), "median": _median([tokens(c) for c in told]),
                "missing_because": _coverage(of[way], _minutes_measured, _minutes_why)[
                    "missing_because"],
            },
            "usd": {
                "n": len(usd), "median": None if median is None else round(median, 4),
                "missing_because": _coverage(spent, lambda c: c["usd"] is not None, _cost_why)[
                    "missing_because"],
            },
        }  # fmt: skip

    rate = ((bugs.get("rate") or {}).get("window") or {}).get("by_way") or {}

    def escapes(way: str) -> dict:
        got = rate.get(way) or {"escapes": 0, "changes": 0, "rate": None}
        # A way with no change has no rate, and says so (189 R11).
        return {**got, "missing_because": {} if got["changes"] else _no_way(way)}

    return {
        "changes": {way: len(of[way]) for way in WAYS},
        "lead": {way: (lead.get("ways") or {}).get(way) for way in WAYS},
        "throughput": {
            way: {
                "closed": len(of[way]),
                "weeks": round(weeks, 1),
                "per_week": round(len(of[way]) / weeks, 2) if days >= 7 else None,
                "why": None if days >= 7 else "window under a week",
            }
            for way in WAYS
        },  # fmt: skip
        "cost": {way: cost(way) for way in WAYS},
        "escapes": {way: escapes(way) for way in WAYS},
    }


# Where a retrospective's report is committed, under the host's `.sdlc/`, one a day.
RETROS = "retros"


def report_rel(today: date) -> str:
    """The report `retro-commit` writes for `today`, as a repo path."""
    return f"{sdlc.HOST_DIR}/{RETROS}/{today.isoformat()}.md"


def insights_rel(today: date) -> str:
    """The insights draft the retro skill writes for `today` after its yes, which `retro-commit`
    renders into the report and removes, never commits (189 R6)."""
    return f"{sdlc.HOST_DIR}/{RETROS}/{today.isoformat()}.insights.md"


def experience_rel(today: date) -> str:
    """The experience draft the retro skill writes for `today` after its yes, holding the person's
    rating answer verbatim, which `retro-commit` renders into the report and removes, never
    commits (190 R3, R5)."""
    return f"{sdlc.HOST_DIR}/{RETROS}/{today.isoformat()}.experience.md"


def _hm(minutes: float | None) -> str:
    """Minutes as `1h 16m`, `—` for none."""
    if minutes is None:
        return "—"
    hours, mins = divmod(round(minutes), 60)
    return f"{hours}h {mins}m" if hours else f"{mins}m"


def _table(head: list[str], rows: list[list]) -> str:
    """A Markdown table, `—` for a missing value."""
    cell = lambda v: "—" if v is None else str(int(v) if v == int(v) else v) if isinstance(  # noqa: E731
        v, float) else str(v)  # fmt: skip
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return "\n".join([*lines, *("| " + " | ".join(cell(v) for v in r) + " |" for r in rows)])


# The spend measures as the report names them.
SPEND_NAMES = {
    "comment_share": "comment share",
    "out_per_line": "out tokens per code line",
    "tools_per_line": "tool calls per code line",
}


def _spend_text(spend: dict | None, closed: int) -> str:
    """`## Spend`: how many changes the token and call figures rest on and why the rest don't,
    each tier's medians, the changes over twice theirs, and the tools most called and failed."""
    if spend is None:
        return "Not counted."
    left = "; ".join(f"{why}: {n}" for why, n in sorted(spend.get("why", {}).items()))
    head = (
        f"{spend['recorded']} of the {closed} changes closed recorded their tool calls and words; "
        "the token and call figures rest on those alone, and comment lines come from every "
        "change's diff." + (f" Left out of them: {left}." if left else "")
    )
    tiers = _table(
        ["Tier", "Changes", *(f"Median {n}" for n in SPEND_NAMES.values())],
        [[t, r["changes"], *(r[k] for k in SPEND_NAMES)] for t, r in spend["tiers"].items()],
    )
    outliers = (
        _table(
            ["Change", "Tier", "Measure", "Value", "Tier median", "Times"],
            [
                [
                    o["change"],
                    o["tier"],
                    SPEND_NAMES[o["measure"]],
                    o["value"],
                    o["median"],
                    o["times"],
                ]
                for o in spend["outliers"]
            ],
        )  # fmt: skip
        if spend["outliers"]
        else "No change is over twice its tier's median on any measure."
    )
    head_tools = ["Tool", "Calls", "Errors", "Error share", "Changes"]
    rows = lambda ts: [[t[k] for k in ("name", "calls", "errors", "error_share", "changes")]  # noqa: E731
                       for t in ts]  # fmt: skip
    called, failed = spend["tools"]["most_called"], spend["tools"]["most_errors"]
    return "\n\n".join([
        head, tiers, outliers,
        "Most called:\n\n" + (_table(head_tools, rows(called)) if called else "No calls recorded."),
        "Most errors:\n\n" + (_table(head_tools, rows(failed)) if failed else "No call failed."),
        _agents_text(spend.get("agents")),
    ])  # fmt: skip


def _agents_text(agents: dict | None) -> str:
    """The "Agents by role and model" table: each group's changes, runs and per-change medians,
    then how many role lines were closed before the counts were."""
    groups = (agents or {}).get("groups") or []
    names = [k.replace("_", " ") for k in sdlc.metrics.BEHAVIOURS]
    table = (
        _table(
            ["Role", "Model", "Changes", "Runs", *(f"Median {n}" for n in names)],
            [
                [
                    g["role"],
                    g["model"],
                    g["changes"],
                    g["runs"],
                    *(g["median"][k] for k in sdlc.metrics.BEHAVIOURS),
                ]
                for g in groups
            ],
        )  # fmt: skip
        if groups
        else "No agent's counts recorded."
    )
    left = (agents or {}).get("unrecorded") or 0
    note = f"\n\n{left} role lines were closed before these were counted." if left else ""
    return "Agents by role and model:\n\n" + table + note


def _no_factory_text(window: dict) -> str:
    """Where the landing catches would be when the window holds no factory change: a sentence,
    never `0 of 0`, naming the changes that record no way of building."""
    if window.get("factory", 1):
        return ""
    n = window.get("mode_unknown") or 0
    unknown = (
        f" {n} change{' records' if n == 1 else 's record'} no way of building, so "
        f"{'it' if n == 1 else 'they'} may have been."
        if n
        else ""
    )
    return f"\n\nNo factory changes in this window.{unknown}"


def _sources_text(
    sources: dict[str, dict], catches: dict | None = None, window: dict | None = None
) -> str:
    """Who found what in the window's reviews, one line per source (`_review_sources()`), after
    the escapes: ship's own beside the fresh reviewer's and each factory role's; then how many of
    the factory-reviewed changes their landing caught out (`_landing_catches()`), or, with no
    factory change in the `window`, a sentence saying so (`_no_factory_text()`)."""
    none = _no_factory_text(window or {})
    if not sources:
        return none
    text = (
        "\n\nFindings by who raised them:\n\n"
        + _table(
            ["Source", "Changes", "Important", "Nit", "Pre-existing", "Wrong"],
            [[s, *(r[k] for k in ("changes", *REVIEW_KINDS))] for s, r in sources.items()],
        )
        + none
    )
    if catches:
        text += (
            f"\n\nLanding catches: {catches['caught']} of {catches['reviewed']} factory-reviewed "
            "changes"
        )
    return text


def _pct(share: float) -> str:
    return f"{round(share * 100)}%"


def _value_text(value: dict) -> str:
    """`value_band()`'s figures as three sentences, each with its `n` and what it left out."""
    mix, ttu, ft = value["work_mix"], value["time_to_users"], value["follow_through"]
    classed = sorted(
        (c for c in WORK_CLASSES if mix["classes"][c]),
        key=lambda c: (-mix["classes"][c], WORK_CLASSES.index(c)),
    )
    shown = ", ".join(f"{c} {mix['classes'][c]} ({_pct(mix['shares'][c])})" for c in classed)
    mix_text = (
        f"Work mix: {shown}, of {mix['n']} classed changes; {mix['unmeasured']} not classed."
        if mix["n"]
        else f"Work mix: no change was classed; {mix['unmeasured']} not classed."
    )
    left = [f"{ttu['why'].get('unreleased', 0)} not yet released"]
    if ttu["why"].get("no date"):
        left.append(f"{ttu['why']['no date']} with no tag date")
    ttu_text = (
        f"Time to users: a median {ttu['median_days']} days from landing to release, over "
        f"{ttu['n']} changes; {', '.join(left)}."
        if ttu["n"]
        else f"Time to users: no change in the window was released; {', '.join(left)}."
    ) + f" {ttu['releases']} releases in the window."
    if ft["since"] is None:
        ft_text = "Follow-through: no earlier retrospective to follow through on."
    else:
        kinds = {kind: ft[kind] for kind in ("seeds", "milestones")}
        done = {kind: k["done"] + k["dropped"] for kind, k in kinds.items() if k}
        parts = [
            f"{kind} {done[kind]} of {k['n']}" if k else f"{kind} unread"
            for kind, k in kinds.items()
        ]
        share = f" ({_pct(ft['share'])})" if ft["share"] is not None else ""
        kept = f"{sum(done.values())} of {ft['n']} done or dropped{share}"
        unmeasured = f"; {ft['unmeasured']} milestones not scored" if ft["unmeasured"] else ""
        ft_text = (
            f"Follow-through on the retrospective of {ft['since']}: {kept}, "
            f"{' and '.join(parts)}{unmeasured}; intent titles aren't recorded."
        )
    return f"{mix_text}\n\n{ttu_text}\n\n{ft_text}"


# `by_way()`'s ways as the report's columns name them.
WAY_NAMES = {"factory": "Factory", "manual": "By hand", "unknown": "Unknown"}


def _by_way_text(ways: dict) -> str:
    """The *By way of building* table: one row a figure, one column a way, each figure followed
    by its `n` in brackets and `–` where it is null, never 0."""

    def num(v: float) -> str:
        return str(int(v)) if v == int(v) else str(v)

    def cell(value, n: int, shown=num) -> str:
        return f"{'–' if value is None else shown(value)} ({n})"

    def row(name: str, figure) -> list:
        return [name, *(figure(w) for w in WAYS)]

    lead, cost = ways["lead"], ways["cost"]
    tput, esc = ways["throughput"], ways["escapes"]
    rows = [
        row("Changes", lambda w: ways["changes"][w]),
        row("Median lead", lambda w: cell(lead[w]["median"], lead[w]["n"], _hm)),
        row("85th percentile lead", lambda w: cell(lead[w]["p85"], lead[w]["n"], _hm)),
        row("Closed per week", lambda w: cell(tput[w]["per_week"], tput[w]["closed"])),
        row("Median tokens", lambda w: cell(
            cost[w]["tokens"]["median"], cost[w]["tokens"]["n"], lambda v: f"{round(v):,}")),
        row("Median dollars", lambda w: cell(
            cost[w]["usd"]["median"], cost[w]["usd"]["n"], lambda v: f"${v:.2f}")),
        row("Escape rate", lambda w: cell(esc[w]["rate"], esc[w]["changes"])),
    ]  # fmt: skip
    return _table(["By way of building", *(WAY_NAMES[w] for w in WAYS)], rows)


def _coverage_line(name: str, block: dict | None, note: str = "") -> str:
    """One headline's *Coverage* line: the changes it rests on and why the rest are missing, and
    `note` after them, in italics and marked a hint under half; `not given` without its block.
    Every reason is a phrase with no path (`metrics._word_text()`), whatever a hand-written
    trailer said."""
    if block is None or "coverage" not in block:
        return f"- Coverage, {name}: not given."
    cov = block["coverage"]
    why = sorted(block["missing_because"].items(), key=lambda kv: (-kv[1], kv[0]))
    said = ", ".join(f"{sdlc.metrics._word_text(str(k))} {n}" for k, n in why)
    line = f"Coverage, {name}: {cov['measured']} of {cov['of']} changes"
    line += f"; missing: {said}" if said else ""
    line += f"; {note}" if note else ""
    if cov["greyed"]:
        return f"- *{line}; a hint: under half the changes*"
    return f"- {line}."


# Each `underneath()` dimension as the report names it.
UNDERNEATH_NAMES = {"claude": "Claude Code", "models": "models", "plugin": "the plugin"}


def _underneath_text(under: dict) -> str:
    """The *What changed underneath* line: each dimension's values against the last window's,
    whether they changed, and how many changes recorded none. Every value is a word again
    (`metrics._word()`), so no trailer puts a path in the report."""
    now, before = under["window"], under["previous"]

    def values(side: dict, k: str) -> str:
        return ", ".join(sdlc.metrics._word(v) for v in side[k]) or "none recorded"

    def none(side: dict, where: str) -> str:
        total = side["recorded"] + side["unrecorded"]
        return f"{side['unrecorded']} of {total} changes {where} recorded none"

    if before is None:
        ran = "; ".join(f"{UNDERNEATH_NAMES[k]} {values(now, k)}" for k in UNDERNEATH)
        return (
            f"- What changed underneath: no earlier window to compare. This window ran {ran}; "
            f"{none(now, 'in this window')}."
        )
    state = {True: "changed", False: "unchanged", None: "not known"}
    said = "; ".join(
        f"{UNDERNEATH_NAMES[k]} {values(now, k)} against {values(before, k)} "
        f"({state[under['changed'][k]]})"
        for k in UNDERNEATH
    )
    return (
        f"- What changed underneath, against the last window: {said}. "
        f"{none(now, 'in this window')}, {none(before, 'in the last')}."
    )


def _coverage_lines(
    process: dict, spend: dict | None, metrics: dict | None, cost: dict | None = None
) -> str:
    """The *Coverage* lines for the report's window, one a headline, then what changed underneath;
    none with no change closed. `cost` is `_cost()`'s: its waste line names the runs recorded
    before purposes, which count in no share."""
    if not process["window"]["closed"]:
        return ""
    heads = [
        ("lead time", process["lead"]), ("escape rate", process["escapes"]),
        ("the person's minutes", metrics), ("spend", spend),
    ]  # fmt: skip
    lines = [_coverage_line(name, block) for name, block in heads]
    untagged = (cost or {}).get("untagged", {}).get("runs", 0)
    lines += [
        _coverage_line("cost per landed change", cost),
        _coverage_line(
            "waste share",
            (cost or {}).get("waste"),
            f"{untagged} runs untagged" if untagged else "",
        ),
    ]
    if process.get("underneath"):
        lines.append(_underneath_text(process["underneath"]))
    return "\n\n" + "\n".join(lines)


NO_INDICATORS = (
    "No indicators set: name commands in retro.indicators (.sdlc/config.toml) to see them here."
)


def _code(text: str) -> str:
    """`text` as a Markdown code span, its fence longer than any backtick run inside it."""
    fence = "`" * (max((len(r) for r in re.findall(r"`+", text)), default=0) + 1)
    pad = " " if "`" in text else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def _indicators_text(host: list[dict] | None) -> str:
    """`## Indicators`: each `retro.indicators` command by name, in config order, with its rows as
    a table under `indicators.HEADER`, which the next retrospective reads back, or one sentence
    saying why there are none. A command's raw output or stderr is never written here."""
    if not host:
        return NO_INDICATORS
    parts = []
    for row in host:
        if row["rows"] is not None:
            body = _table(list(indicators.INDICATOR_HEAD), [
                [indicators.cell(r["name"]), indicators.cell(r["unit"]) if r["unit"] else "—",
                 indicators.number(r["value"]),
                 "—" if r["last"] is None else indicators.number(r["last"]),
                 indicators.signed(r["change"])]
                for r in row["rows"]
            ])  # fmt: skip
        elif row["not_rows"].startswith(("failed", "timed out")):
            body = f"It {row['not_rows']}."
        else:
            body = (
                f"Its output isn't indicator rows ({row['not_rows']}), so it is in "
                "`sdlc.py retro`'s output only."
            )
        parts.append(f"{_code(row['command'])}\n\n{body}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------- the scorecard's sections (184)

NOT_GIVEN = "Not given."
GUARDED = (
    "Quality and Simplicity are guarded by Speed's lead time, and Cost by Quality's escape rate."
)
OUTCOMES_MOVED = (
    "Outcomes moved: scored by the retrospective's product pass, in the direction doc, not here."
)


def _num(value) -> str:
    """A figure as the report writes it, `—` for none."""
    return "—" if value is None else indicators.number(value)


def _scorecard_text(
    card: dict | None, value: dict | None, process: dict, spend: dict | None,
    metrics: dict | None, cost: dict | None,
) -> str:  # fmt: skip
    """`## Scorecard`: the Value band (`_value_text()`) and how outcomes are scored, the pillar
    table under `SCORECARD_HEAD`, which the next retrospective reads back, and what guards the
    pillars that have no guardrail row; then the Trust band: the coverage lines, what changed
    underneath, and the signals no record holds."""
    parts = []
    if value:
        parts += [_value_text(value), OUTCOMES_MOVED]
    if card:
        parts.append(_table(list(SCORECARD_HEAD), [
            [indicators.cell(r["pillar"]), r["role"], indicators.cell(r["figure"]), r["unit"],
             _num(r["value"]), r["n"], _num(r["last"]), r["trend"], indicators.cell(r["note"])]
            for r in card["rows"]
        ]))  # fmt: skip
        parts.append(GUARDED)
    else:
        parts.append("No pillar table given.")
    trust = _coverage_lines(process, spend, metrics, cost).strip()
    signals = "; ".join(u["signal"] for u in UNMEASURED)
    parts.append((trust + "\n" if trust else "") + f"- Unmeasured signals: {signals}.")
    return "\n\n".join(parts)


def _spread_text(spread: dict, unit: str = "s") -> str:
    if not spread["n"]:
        return "none recorded"
    return (
        f"median {_num(spread['median'])}{unit}, 85th percentile {_num(spread['p85'])}{unit}, "
        f"over {spread['n']}"
    )


def _pipeline_speed_text(pipeline: dict | None, window: dict) -> str:
    """Speed's pipeline part: the gates' seconds and slot waits, this window's and the last's, and
    the landing's gates, ejections, bisections, base moves, accept stops and conflicts, each with
    its `n`; with no factory change, a sentence saying so (`_no_factory_text()`)."""
    if pipeline is None:
        return ""
    if not pipeline["factory"]:
        return _no_factory_text(window).strip()
    lines = []
    for side, gates in (("this window", pipeline["gates"]["window"]),
                        ("the last", pipeline["gates"]["previous"])):  # fmt: skip
        if gates is None:
            lines.append(f"- Gates, {side}: no earlier window to compare.")
            continue
        for kind, said in (("round", "round"), ("land", "landing")):
            g = gates[kind]
            lines.append(
                f"- {said.capitalize()} gates, {side}: {_spread_text(g['seconds'])}; slot wait "
                f"{_spread_text(g['wait'])}."
            )
    land = pipeline["landing"]
    e, n = land["ejections"], land["n"]
    causes = ", ".join(f"{c} {e.get(c, 0)}" for c in EJECT_CAUSES)
    lines += [
        f"- Landing gates: {land['gates']['total']} over {n} factory landings "
        f"({_num(land['gates']['per_change'])} per change).",
        f"- Ejections: {e['total']} ({causes}), in {e['changes']} of {n} landings.",
        f"- Bisections: {land['bisections']['total']} "
        f"({_num(land['bisections']['per_change'])} per change), over {n}.",
        f"- Base moves: {land['base_moves']['total']} "
        f"({_num(land['base_moves']['per_change'])} per change), in "
        f"{land['base_moves']['changes']} of {n}.",
        f"- Accept stops: {land['accept_stops']['total']} "
        f"({_num(land['accept_stops']['per_change'])} per change), in "
        f"{land['accept_stops']['changes']} of {n}.",
        f"- Conflicts: {land['conflicts']['landing']} at landing, {land['conflicts']['ship']} at "
        "ship.",
        _coverage_line("landing", land),
    ]
    return "Pipeline:\n\n" + "\n".join(lines)


def _pipeline_quality_text(pipeline: dict | None) -> str:
    """Quality's pipeline part: the red-gate rate per build, the share of runs at full depth, and
    the landings with paths no review read, each with its `n`; nothing with no factory change,
    which the escapes' part already says."""
    if pipeline is None or not pipeline["factory"]:
        return ""
    red, depth, unread = pipeline["red_gate"], pipeline["depth"], pipeline["unreviewed"]
    return "\n".join([
        f"- Red gates: {red['red']} of {red['builds']} builds (rate {_num(red['rate'])}).",
        f"- Full-depth runs: {depth['full']} of {depth['n']} (share {_num(depth['share'])}); "
        f"light {depth['light']}.",
        f"- Landings with paths no review read: {unread['with_paths']} of {unread['n']} "
        f"({unread['paths']} paths); unknown {unread['unknown']}, none {unread['none']}.",
    ])  # fmt: skip


def _autonomy_text(autonomy: dict | None, metrics: dict | None) -> str:
    """`## Autonomy`: how often the factory changes needed the person, each figure with its `n`
    and `—` where null; then the extra stops by kind (`metrics.extra`)."""
    if autonomy is None:
        return NOT_GIVEN
    a = autonomy
    esc, asked, kept = a["escalations"], a["asked"], a["kept_default"]
    auto, stops, looks = a["auto_landed"], a["spurious_stops"], a["looks"]
    head = (
        f"{a['factory']} factory changes, {a['by_hand']} built by hand; every figure is over the "
        "factory changes."
    )
    lines = [
        f"- Escalations: {esc['total']} in {esc['changes']} of {esc['n']} changes "
        f"({_num(esc['per_change'])} per change).",
        f"- Questions answered: blocking {asked['blocking']}, defaults {asked['default']}, looks "
        f"{asked['look']} ({_num(asked['per_change'])} per change, over {asked['n']}).",
        f"- Defaults kept: {kept['kept']} of {kept['n']} (rate {_num(kept['rate'])}); changed "
        f"{kept['changed']}, confirmed {kept['confirmed']}, settled {kept['settled']}.",
        f"- Auto-landed: {auto['auto']} of {auto['n']} (share {_num(auto['share'])}); by the "
        f"person {auto['person']}, by autopilot {auto['autopilot']}, shipped {auto['shipped']}.",
        f"- Spurious stops: build {stops['build']}, landing {stops['landing']}, in "
        f"{stops['changes']} of {stops['n']} changes ({_num(stops['per_change'])} per change).",
        f"- Looks: seen {looks['seen']}, checked {looks['checked']}, open {looks['open']} (seen "
        f"share {_num(looks['seen_share'])}, over {looks['n']}).",
    ]
    extra = (metrics or {}).get("extra")
    if extra:
        kinds = ", ".join(
            f"{k.replace('_', ' ')} {r['count']} ({r['changes']} changes)"
            for k, r in extra["kinds"].items()
        )
        lines.append(f"- Extra stops by kind, over {extra['recorded']} recorded changes: {kinds}.")
    return head + "\n\n" + "\n".join(lines)


def _cost_text(cost: dict | None) -> str:
    """`## Cost`: dollars and agent-minutes per landed change by tier, the waste share with its
    parts, and spend by role and by model, each with its `n`."""
    if cost is None:
        return NOT_GIVEN
    tiers = (
        _table(
            [
                "Tier",
                "Changes",
                "Median dollars",
                "Total dollars",
                "Median agent minutes",
                "Total agent minutes",
            ],
            [
                [
                    t,
                    r["n"],
                    r["usd"]["median"],
                    r["usd"]["total"],
                    r["minutes"]["median"],
                    r["minutes"]["total"],
                ]
                for t, r in sorted(cost["per_change"].items())
            ],
        )  # fmt: skip
        if cost["per_change"]
        else "No landed change reported dollars."
    )
    w = cost["waste"]
    parts = ", ".join(f"{p} ${r['usd']} ({r['runs']} runs)" for p, r in w["parts"].items()
                      if r["runs"])  # fmt: skip
    waste = (
        f"Waste share: {_num(w['share'])} of the dollars (${w['usd']} of ${w['of_usd']}), "
        f"{_num(w['minutes_share'])} of the minutes, over {w['n']} changes"
        + (f"; by part: {parts}." if parts else ".")
    )

    def split(name: str, rows: dict) -> str:
        if not rows:
            return f"By {name}: no runs recorded."
        return f"By {name}:\n\n" + _table(
            [name.capitalize(), "Runs", "Dollars", "Minutes", "Changes"],
            [[k, r["runs"], r["usd"], r["minutes"], r["changes"]] for k, r in rows.items()],
        )

    return "\n\n".join([tiers, waste, split("role", cost["by_role"]),
                         split("model", cost["by_model"])])  # fmt: skip


WORKAROUND_NAMES = {
    "outside": "Commits outside the loop",
    "hand_record": "Records edited by hand",
    "restored": "Register entries restored",
}


def _simplicity_text(workarounds: dict | None, shown: dict | None) -> str:
    """`## Simplicity`: the workarounds, each count with its `n` and its rows, and the factory's
    overrides; then, in the plugin's own repo alone (`shown`), its share used, retire candidates,
    footprint and growth. A host's is never the plugin's."""
    if workarounds is None:
        return NOT_GIVEN
    parts = []
    for kind, said in WORKAROUND_NAMES.items():
        block = workarounds[kind]
        rows = "".join(
            f"\n- {r['id'] + ' at ' if 'id' in r else ''}{_code(r['sha'])} {r['subject']}"
            for r in block["rows"]
        )
        parts.append(f"{said}: {_num(block['count'])} of {block['n']}.{rows}")
    o = workarounds["overrides"]
    causes = ", ".join(f"{c} {k}" for c, k in o["ejections"]["by_cause"].items())
    parts.append(
        f"Overrides, over {o['ejections']['n']} factory changes: ejections "
        f"{_num(o['ejections']['count'])}{f' ({causes})' if causes else ''}, stops "
        f"{_num(o['stops']['count'])}, fixes asked at landing {_num(o['fixes']['count'])}."
    )
    if shown:
        share = shown["share"]
        parts.append(
            f"The plugin's surface used: {_num(share['overall'])} (skills {_num(share['skills'])}, "
            f"commands {_num(share['commands'])}, keys {_num(share['keys'])})."
        )
        retire = shown["retire"]
        named = ", ".join(f"{i['kind']} {i['name']}" for i in retire["items"]) or "none"
        parts.append(
            f"Retire candidates, unused in {retire['after']} measured windows ({retire['windows']} "
            f"read): {named}."
        )
        foot = shown["footprint"]
        parts.append(
            f"Setup's footprint: {foot['created']} paths created, {foot['keys']} keys set, "
            f"{foot['lines']} lines."
            if foot
            else f"Setup's footprint: not read ({shown['why'].get('footprint')})."
        )
        growth = shown["growth"]
        if growth:
            parts.append("The surface's growth by release:\n\n" + _table(
                ["Tag", *(k.replace("_", " ").capitalize() for k in GROWTH_COUNTS)],
                [[g["tag"], *(g[k] for k in GROWTH_COUNTS)] for g in growth],
            ))  # fmt: skip
        else:
            why = shown["why"].get("growth") or "no release in the window"
            parts.append(f"The surface's growth by release: {why}.")
    return "\n\n".join(parts)


def render_report(
    template: str,
    figures: dict,
    *,
    indicators: list[dict] | None = None,
    insights: list[dict] | None = None,
    experience: str | None = None,
) -> str:
    """The report: `template` with each `{{key}}` replaced by its view as a table, or by
    "not measured" where close measured none of the window's changes. `figures` is
    `report_figures()`'s dict (189 R10): it must hold `process`, and any other key it lacks reads
    as None. Its `spend` is `_spend()`'s block, "not counted" without it. `value` is
    `value_band()`'s, its sentences after the window's paragraph; nothing is added without it.
    `metrics` is `metrics_summary()`'s, whose coverage line says "not given" without it, as
    `cost`'s (`_cost()`) two do. The coverage lines follow the window's sentence, in `{{window}}`.
    `indicators` is `_indicator_rows()`'s, and with none `{{indicators}}` says no indicators are
    set. `by_way` is `by_way()`'s, its table ending `{{window}}`; nothing is added without it.
    `insights` is `insight_answers()`'s, and with none `{{insights}}` says they weren't answered.
    `experience` is the person's rating answer (`_draft_experience()`'s), rendered into
    `{{experience}}` against `figures["experience_last"]` (`_experience_text()`); with none it
    says no rating was given. `hosts` is `hosts_figures()`'s, rendered into `{{hosts}}`
    (`_hosts_text()`), one line outside the plugin's own repo.

    A template with `{{scorecard}}` (184) gets the scorecard there instead (`_scorecard_text()`,
    `scorecard` being `scorecard()`'s), `{{window}}` is the window's sentence alone, and each
    pillar's section is built from the same parts the old placeholders get: `{{speed}}` (cycle,
    throughput, time, capacity, the by-way table and the pipeline's landing), `{{quality}}`
    (escapes, rework, the pipeline's red gates), `{{autonomy}}`, `{{cost}}` and `{{simplicity}}`
    (`surface` only in the plugin's own repo). One without it renders as before, so each figure
    appears once either way."""
    process = figures["process"]
    spend, value, metrics, cost = (figures.get(k) for k in ("spend", "value", "metrics", "cost"))
    ways, autonomy, pipeline = (figures.get(k) for k in ("by_way", "autonomy", "pipeline"))
    workarounds, surface, card = (figures.get(k) for k in ("workarounds", "surface", "scorecard"))
    w = process["window"]
    unmeasured = f"Not measured: none of the {w['closed']} changes closed has its numbers."
    tiers = ", ".join(f"tier {t}: {n}" for t, n in w["tiers"].items()) or "none"
    values = {
        "since": w["since"] or "the start of history",
        "today": w["today"],
        "window": (
            f"From {w['since'] or 'the start of history'} to {w['today']}: {w['closed']} changes "
            f"closed ({tiers}), {w['dropped']} dropped. {w['measured']} of them were measured, and "
            f"the timed views rest on those alone; {w['unmeasured']} weren't."
        ),
        "throughput": _table(
            ["Week of", "Tiers", "Ways", "Classes", "Closed"],
            [[r["week"], *(", ".join(f"{k}: {n}" for k, n in (r.get(part) or {}).items() if n)
                           for part in ("tiers", "ways", "classes")), r["total"]]
             for r in process["throughput"]],
        ),  # fmt: skip
        "rework": _table(
            ["Declared links", "Changes reworked", "Links per closed change", "Questions"],
            [[process["rework"][k] for k in ("links", "reworked", "per_change", "questions")]],
        ),
        "escapes": _table(
            ["Reported", "Fixed", "Median days to fix", "Rate", "Previous rate", "Trend"],
            [[process["escapes"][k]
              for k in ("reported", "fixed", "days_to_fix", "rate", "previous", "trend")]],
        ) + _sources_text(process.get("review_sources") or {},
                          process.get("landing_catches"), w),  # fmt: skip
        "cycle": unmeasured, "time": unmeasured, "capacity": unmeasured,
        "spend": _spend_text(spend, w["closed"]),
        "indicators": _indicators_text(indicators),
        "insights": _insights_text(insights),
        "experience": _experience_text(experience, figures.get("experience_last")),
        "hosts": _hosts_text(figures.get("hosts")),
    }  # fmt: skip
    scored = "{{scorecard}}" in template
    if not scored:
        values["window"] += _coverage_lines(process, spend, metrics, cost)
        if value:
            values["window"] += "\n\n" + _value_text(value)
        if ways:
            values["window"] += "\n\n" + _by_way_text(ways)
    if process["cycle"]:
        values["cycle"] = _table(
            ["Tier", "Changes", "Median elapsed", "Longest", "Median agent", "Median days open"],
            [[t, r["n"], _hm(r["elapsed"]), _hm(r["max"]), _hm(r["agent"]), r["days_open"]]
             for t, r in process["cycle"].items()],
        )  # fmt: skip
        if process["lead"]["measured"]:
            values["cycle"] += "\n\n" + _lead_text(process["lead"])
        t = process["time"]
        values["time"] = _table(
            ["Tier", *(f"Median {k}" for k in CLOCKS)],
            [[tier, *(_hm(r[k]) for k in CLOCKS)] for tier, r in t["tiers"].items()],
        ) + (
            f"\n\nOver the window: agent {_hm(t['sums']['agent'])}, the person's response "
            f"{_hm(t['sums']['response'])}, away {_hm(t['sums']['away'])}, blocked "
            f"{_hm(t['sums']['blocked'])}. Agent share of agent, response and away: "
            f"{t['agent_share']}."
        )
        wip = process["wip"]
        values["capacity"] = (
            f"Changes open at once: median {wip['median']}, most {wip['max']}, over "
            f"{wip['spans']} changes.\n\n"
            + _table(
                ["Open at once", "Changes", "Median elapsed", "Median agent", "Median response"],
                [
                    [k, r["n"], _hm(r["elapsed"]), _hm(r["agent"]), _hm(r["response"])]
                    for k, r in process["capacity"].items()
                ],
            )  # fmt: skip
        )
    if not process["cycle"] and process["lead"]["measured"]:
        values["cycle"] = _lead_text(process["lead"])
    if scored:
        speed = [
            values["cycle"], "Throughput by week:\n\n" + values["throughput"],
            "Where the time went:\n\n" + values["time"],
            "Work in progress and capacity:\n\n" + values["capacity"],
            _by_way_text(ways) if ways else "",
            _pipeline_speed_text(pipeline, w),
        ]  # fmt: skip
        quality = [
            "Escapes:\n\n" + values["escapes"], "Rework:\n\n" + values["rework"],
            _pipeline_quality_text(pipeline),
        ]  # fmt: skip
        values.update(
            scorecard=_scorecard_text(card, value, process, spend, metrics, cost),
            speed="\n\n".join(p for p in speed if p),
            quality="\n\n".join(p for p in quality if p),
            autonomy=_autonomy_text(autonomy, metrics),
            cost=_cost_text(cost),
            simplicity=_simplicity_text(workarounds, surface),
        )
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


NOT_ANSWERED = "Not answered: this report was written without the retrospective's insights."


def _insights_text(answers: list[dict] | None) -> str:
    """`## Insights` (189 R7): each answer as `### <title>: <headline>`, its question in italics,
    then its Evidence, Recommendation and Disposition as bullets; `NOT_ANSWERED` with none, never
    an empty section."""
    if not answers:
        return NOT_ANSWERED
    parts = []
    for a in answers:
        question = " ".join(a["question"].split())
        bullets = "\n".join(
            f"- {field}: {' '.join(a[field.lower()].split())}" for field in INSIGHT_FIELDS[1:]
        )
        parts.append(f"### {a['title']}: {' '.join(a['headline'].split())}\n\n*{question}*\n\n"
                     + bullets)  # fmt: skip
    return "\n\n".join(parts)


# ---------------------------------------------------------------- the experience (190)

# The Experience table's header line, which the next retrospective reads back (`_last_rows()`).
EXPERIENCE_HEAD = ("Figure", "Value", "Last retrospective", "Trend")
EXPERIENCE_FIGURE = "How working with the process felt (1 to 4)"
EXPERIENCE_LABELS = {4: "smooth", 3: "fine", 2: "rough", 1: "in the way"}
LINE_PREFIX = "Their line: "
NO_LINE = "No line given."
NOT_RATED = "Not rated: the person gave no rating at this retrospective's question."
RATING_RE = re.compile(r"([1-4])(?!\d)(.*)", re.S)


def experience_answer(text: str) -> tuple[int | None, str | None]:
    """The rating and the line in the person's answer (190 R4): a leading 1 to 4, not followed by
    another digit, is the rating, and the rest, its leading spaces and `—-:,.` stripped, the line,
    none when it is only that rating's option label; anything else is no rating and all of it the
    line. Empty is neither. Pure."""
    text = (text or "").strip()
    if not text:
        return None, None
    m = RATING_RE.match(text)
    if not m:
        return None, text
    rating = int(m.group(1))
    rest = m.group(2).lstrip(" \t—-:,.").strip()
    if not rest or rest.casefold() == EXPERIENCE_LABELS[rating]:
        return rating, None
    return rating, rest


def _experience_trend(rating: int | None, last: int | None) -> str:
    """`up`, `down` or `flat` from the rating against the last retrospective's, `unknown` without
    both. No minimum count, unlike `_trend()`: it is one person's single answer (190 R9)."""
    if rating is None or last is None:
        return "unknown"
    return "up" if rating > last else "down" if rating < last else "flat"


def _experience_text(answer: str | None, last: dict | None) -> str:
    """`## Experience` (190 R5, R6): the one-row table under `EXPERIENCE_HEAD`, the rating against
    `last` (`_last_rows()`'s `experience`), then the line, outside the table so a `|` in it can't
    break the read-back, its whitespace collapsed; `NO_LINE` with none, and `NOT_RATED` with no
    answer, never an empty section."""
    rating, line = experience_answer(answer) if answer is not None else (None, None)
    before = (last or {}).get("rating")
    table = _table(list(EXPERIENCE_HEAD), [
        [EXPERIENCE_FIGURE, _num(rating), _num(before), _experience_trend(rating, before)],
    ])  # fmt: skip
    if rating is None and line is None:
        return f"{table}\n\n{NOT_RATED}"
    said = LINE_PREFIX + " ".join(line.split()) if line else NO_LINE
    return f"{table}\n\n{said}"


def _draft_experience(home: Path, day: date) -> tuple[str | None, list[str]]:
    """The answer in `day`'s experience draft, its first `Answer:` line's text; None, with no
    problem, when there is no draft, and a problem when it has no such line (190 R7)."""
    rel = experience_rel(day)
    path = home / rel
    if not path.is_file():
        return None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Answer:"):
            return line.removeprefix("Answer:").strip(), []
    return None, [f"experience: {rel} has no Answer: line"]


def _last_experience(text: str, day: str | None) -> dict | None:
    """The rating and line a report's `## Experience` shows, with the report's `day`; None for a
    report without the table. A rating cell that isn't a whole 1 to 4, as a hand edit may leave,
    reads as no rating (nit 2026-11-20-33)."""
    got = indicators.report_rows(text, EXPERIENCE_HEAD, (0,), 1)
    if (EXPERIENCE_FIGURE,) not in got:
        return None
    rating = got[(EXPERIENCE_FIGURE,)]
    section = text.split("\n## Experience\n", 1)[-1].split("\n## ", 1)[0]
    line = next(
        (ln.removeprefix(LINE_PREFIX).strip() for ln in section.splitlines()
         if ln.startswith(LINE_PREFIX)), None,
    )  # fmt: skip
    rating = int(rating) if rating in EXPERIENCE_LABELS else None
    return {"date": day, "rating": rating, "line": line or None}


# ---------------------------------------------------------------- the scorecard (184)

# The pillar table's header line, which the next retrospective reads back (`_last_rows()`).
SCORECARD_HEAD = (
    "Pillar", "Role", "Figure", "Unit", "Value", "n", "Last retrospective", "Trend", "Note",
)  # fmt: skip
# The table's key columns, Pillar and Figure, and its Value and n columns.
SCORECARD_KEYS = (0, 2)
SCORECARD_VALUE, SCORECARD_N = 4, 5
# The ways a by-way row names, as the figure says them; `unknown` has no row.
CARD_WAYS = {"factory": "factory", "manual": "by hand"}
GREYED_NOTE = "a hint: under half the changes"
NONE_NOTE = "none in the window"


def _row_note(value, block: dict | None) -> str:
    """A row's Note: with no value, the source `block`'s most counted `missing_because` reason
    (`none in the window` without one); and the hint mark when the block is greyed."""
    notes = []
    if value is None:
        why = sorted(((block or {}).get("missing_because") or {}).items(),
                     key=lambda kv: (-kv[1], kv[0]))  # fmt: skip
        notes.append(sdlc.metrics._word_text(str(why[0][0])) if why and why[0][0] else NONE_NOTE)
    if ((block or {}).get("coverage") or {}).get("greyed"):
        notes.append(GREYED_NOTE)
    return "; ".join(notes)


def _trend(value, n: int, last: tuple | None) -> str:
    """`up`, `down` or `flat` from `value` against the last retrospective's, `unknown` without
    both, or when either side rests on fewer than `RATE_MIN_CHANGES`."""
    if value is None or not last or last[0] is None or last[1] is None:
        return "unknown"
    if min(n, last[1]) < RATE_MIN_CHANGES:
        return "unknown"
    # The value as the table writes it and the next retrospective reads it (nit 2026-11-19-65).
    shown = indicators._parsed(_num(value))
    if shown is None:
        return "unknown"
    return "up" if shown > last[0] else "down" if shown < last[0] else "flat"


def _minutes(value) -> float | None:
    """A median in minutes as the table writes it: to one decimal place, so a short response isn't
    flattened to a whole minute (nit 2026-11-19-66), and it reads back the same."""
    return None if value is None else round(value, 1)


def scorecard(
    process: dict, autonomy: dict, ways: dict, cost: dict, workarounds: dict,
    surface: dict | None, last: dict[tuple, tuple],
) -> dict:  # fmt: skip
    """The scorecard's pillar table (184 R3): each pillar's headline and guardrail figures, every
    one from a block `retro` already computes, one row a way or tier present where the block
    gives it only that way, with its unit, value, `n`, the last retrospective's value (`last`, by
    `(pillar, figure)`: `(value, n)` from its report), the trend and a note. The surface's share
    only with `surface`, which only the plugin's own repo passes. The escape rate's last and trend
    are `process.escapes`' own. Pure."""
    rows: list[dict] = []

    def add(pillar, role, figure, unit, value, n, block=None, own_last=None) -> None:
        mine = last.get((pillar, figure))
        rows.append({
            "pillar": pillar, "role": role, "figure": figure, "unit": unit, "value": value,
            "n": n, "last": mine[0] if mine else None, "trend": _trend(value, n, mine),
            "note": _row_note(value, block),
            **(own_last or {}),
        })  # fmt: skip

    w = process["window"]
    lead = process["lead"]
    for way, said in CARD_WAYS.items():
        got = (lead.get("ways") or {}).get(way) or {"n": 0, "median": None}
        # No change of the way: the escape rate's reason, not the coverage's (seed 2026-11-20-24).
        block = lead if ways["changes"][way] else {**lead, "missing_because": _no_way(way)}
        add("Speed", "headline", f"Median lead time, {said}", "minutes",
            _minutes(got["median"]), got["n"], block)  # fmt: skip
    add("Speed", "guardrail", "Rework links per closed change", "per change",
        process["rework"]["per_change"], w["closed"])  # fmt: skip
    esc = process["escapes"]
    add("Quality", "headline", "Escape rate", "per change", esc["rate"], w["closed"], esc,
        {"last": esc["previous"], "trend": esc["trend"]})  # fmt: skip
    tiers = list(w["tiers"])
    for tier in tiers or [None]:
        said = f"Median response, tier {tier}" if tier else "Median response"
        timed = ((process.get("time") or {}).get("tiers") or {}).get(tier) or {}
        n = ((process.get("cycle") or {}).get(tier) or {}).get("n", 0)
        reach = (process.get("response") or {}).get(tier)
        add("Autonomy", "headline", said, "minutes", _minutes(timed.get("response")), n, reach)
    asked = autonomy["asked"]
    add("Autonomy", "headline", "Questions answered per factory change", "per change",
        asked["per_change"], asked["n"], asked)  # fmt: skip
    for way, said in CARD_WAYS.items():
        got = ways["escapes"][way]
        add("Autonomy", "guardrail", f"Escape rate, {said}", "per change", got["rate"],
            got["changes"], got)  # fmt: skip
    for tier in tiers or [None]:
        said = "Median dollars per landed change" + (f", tier {tier}" if tier else "")
        got = cost["per_change"].get(tier) or {"n": 0, "usd": {"median": None}}
        add("Cost", "headline", said, "USD", got["usd"]["median"], got["n"], cost)
    if surface is not None:
        measured = sum(1 for r in surface["items"] if r["state"] in ("used", "unused"))
        add("Simplicity", "headline", "Share of the surface used", "share",
            surface["share"]["overall"], measured, surface)  # fmt: skip
    for kind, said, unit in (
        ("outside", "Commits outside the loop", "commits"),
        ("hand_record", "Records edited by hand", "commits"),
        ("restored", "Register entries restored", "entries"),
    ):
        got = workarounds[kind]
        add("Simplicity", "headline", said, unit, got["count"], got["n"], got)
    return {"rows": rows, "since": w["since"]}


def report_figures(home: Path, cfg: dict, today: date, *, surface: bool) -> dict:
    """The figures the report shows, and `retro()` gives, worked out once for the window since the
    last retrospective, so the two never disagree: each closed change's start (`bases`), its rows
    and paths, `days_open` and `release`; the dropped changes; the rework, the bugs, the Value band
    (before the process views, so each change's `work` is set when the weeks are counted by it),
    the process views, the metrics, the cost (`_cost()`'s one call, `_landed` popped into
    `by_way()`), the figures by way, autonomy, the pipeline, the workarounds and the spend; with
    `surface`, the plugin's surface (a host's report leaves it out); and the `scorecard()`, its
    surface row only in the plugin's own repo; and the last retrospective's rating
    (`experience_last`, 190 R9), from the same read of its report. Each closed change keeps
    its `problems`, which `retro()` pops; `problems` here are what the passes found. Read-only."""
    trunk = cfg["git"]["base"]
    since = sdlc.last_retrospective(home, trunk)
    changes = sdlc.closed_changes(home, since["sha"] if since else None, trunk)
    bases: dict[str, str | None] = {}
    rows: dict[str, list] = {}
    paths: dict[str, list[str]] = {}
    for rec in changes:
        # A change ships as one commit or several, and its size is all of them: its branch from
        # where it started. Without that start, the last commit still says what it touched.
        bases[rec["name"]], rows[rec["name"]] = _change_rows(home, rec)
        paths[rec["name"]] = [path for path, _, _ in rows[rec["name"]]]
        rec["days_open"] = sdlc._days_between(rec["created"], rec["close_date"])
        rec["release"] = _release_of(home, cfg, rec["sha"])
    dropped = sdlc.dropped_changes(home, since["sha"] if since else None, trunk)
    autonomy, unread = _autonomy(home, changes)
    previous = _previous_window(home, trunk, since)
    diffs = _diffs(home, changes, bases)
    rework, questions, unnamed = _rework(home, trunk, changes, bases, diffs)
    bugs = bugs_retro(home, cfg, since, changes, today)
    value = value_band(home, cfg, since, changes, bases, paths)
    workarounds, unknown = _workarounds(home, cfg, since, changes, dropped, bases)
    process = process_views(changes, dropped, rework, questions, bugs, since, today, previous)
    cost = _cost(home, changes, dropped)
    ways = by_way(changes, process["lead"], cost.pop("_landed"), bugs, since, today)
    pipeline = _pipeline(home, changes, previous)
    shown = _surface(home, cfg, changes, since) if surface else None
    last = _last_rows(home, since)
    card = scorecard(
        process, autonomy, ways, cost, workarounds, shown if sdlc._own_repo(home) else None,
        last["scorecard"],
    )  # fmt: skip
    return {
        "since": since, "changes": changes, "dropped": dropped, "bases": bases, "rows": rows,
        "paths": paths, "diffs": diffs, "rework": rework, "questions": questions, "bugs": bugs,
        "previous": previous, "value": value, "process": process,
        "metrics": metrics_summary(changes, cfg["metrics"]["stop_allowance"]),
        "cost": cost, "by_way": ways, "autonomy": autonomy,
        "pipeline": pipeline, "workarounds": workarounds,
        "spend": _spend(home, cfg, changes, diffs), "surface": shown, "scorecard": card,
        "experience_last": last["experience"],
        "hosts": hosts_figures(home, since),
        "problems": [*unread, *unnamed, *unknown],
    }  # fmt: skip


def retro_report(
    home: Path, cfg: dict, today: date, insights: list[dict] | None = None,
    experience: str | None = None,
) -> str:  # fmt: skip
    """The report for the window since the last retrospective: `report_figures()`, without the
    product pass, the rest of the architecture or the prose, and the plugin's surface only in its
    own repo; and the host's `retro.indicators`, run through `_evidence()` as the architecture pass
    runs them, the only host command it runs. `insights` are the answers `{{insights}}` renders
    (`insight_answers()`'s), and `experience` the rating answer `{{experience}}` renders."""
    f = report_figures(home, cfg, today, surface=sdlc._own_repo(home))
    template = sdlc.template_path(home, "retro.md")[0].read_text(encoding="utf-8")
    host = _indicator_rows(home, f["since"], _evidence(home, cfg["retro"]["indicators"]))
    return render_report(template, f, indicators=host, insights=insights, experience=experience)


# ---------------------------------------------------------------- the surface: what is used

# An item unused in this many measured windows running, the current one first, is a retire
# candidate. A constant, not a key: a key to say how many windows would grow the surface it counts.
RETIRE_AFTER = 3

# Whether a skill's run reaches a `Close` commit's trailers, for each skill that `metrics.py`'s
# `SKILL_STAGE` doesn't name or names wrongly: only a change's sessions are measured
# (`metrics.read_events()`). `outside`: run from the main checkout outside any change, or recorded
# on no `Close` commit (a drop's is a `Drop`), so neither it nor its calls are ever counted.
# `supervised`: the factory's supervisor, in the main checkout, keeps for a change only the typed
# command naming it (`metrics._supervised()`), so its run is counted and its calls never are.
# Every other skill is `inside`: its run and its calls are the change's.
SKILL_RUNS = {
    "sdlc:bug": "outside",
    "sdlc:dashboard": "outside",
    "sdlc:drop": "outside",
    "sdlc:health": "outside",
    "sdlc:idea": "outside",
    "sdlc:publish": "outside",
    "sdlc:release": "outside",
    "sdlc:retro": "outside",
    "sdlc:setup": "outside",
    "sdlc:status": "outside",
    "sdlc:triage": "outside",
    "sdlc:uninstall": "outside",
    "sdlc:update": "outside",
    "sdlc-factory:autopilot": "outside",
    "sdlc-factory:build": "supervised",
    "sdlc-factory:decide": "outside",
    "sdlc-factory:eval": "outside",
    "sdlc-factory:land": "supervised",
    "sdlc-factory:review": "outside",
}

# A command's registration, read from a script's text: `@command("name"` or `@command(` with the
# name on the next line. `factory.py` is never imported; the copy is pinned to both registries.
COMMAND_RE = re.compile(r'@command\(\s*"([a-z][a-z0-9-]*)"')
# A plugin script's command in a skill's bash, `…/scripts/sdlc.py" ship 179`.
SCRIPT_CALL_RE = re.compile(r"scripts/(sdlc\.py|factory\.py)['\"]?\s+([a-z][a-z0-9-]*)")
# A plugin script's call as `Sdlc-Tool` names it (`metrics._prompt_name()`).
TOOL_CALL_RE = re.compile(r"^Bash:(sdlc\.py|factory\.py):([a-z][a-z0-9-]*)$")
FACTORY_DIR = "plugins/factory"
# The skills' cases' commands, this plugin's own like ship's branch for them (`OWN_REPO_BRANCHES`):
# a host's surface never lists them.
OWN_REPO_COMMANDS = ("cases", "run-cases")
OUTSIDE_WHY = "runs outside a change's sessions"
NO_CALLER_WHY = "no skill runs it"
UNRECORDED_WHY = "no change recorded it"
# A key whose every reader, command or skill, runs where no record shows its use.
UNSEEN_READ_WHY = "read only where no record shows it"


def _skill_where(name: str) -> str:
    """`inside`, `supervised` or `outside`: whether a skill's run, and its calls, are counted."""
    return SKILL_RUNS.get(name, "inside")


def _skill_dirs(factory: bool) -> list[tuple[str, Path]]:
    """Each skill's `plugin:name` and folder: the core's, then the factory's when in play."""
    roots = [("sdlc", sdlc.PLUGIN_DIR / "skills")]
    if factory:
        roots.append(("sdlc-factory", sdlc.PLUGIN_DIR / FACTORY_DIR / "skills"))
    return [
        (f"{plugin}:{p.parent.name}", p.parent)
        for plugin, root in roots
        for p in sorted(root.glob("*/SKILL.md"))
    ]


def _factory_in_play(home: Path) -> bool:
    """Whether the factory's surface is counted: enabled for the repo, or the plugin's own."""
    return sdlc._own_repo(home) or sdlc.factory_enabled(home)[0]


def _inventory(home: Path) -> list[dict]:
    """Every skill, script command and config key, from the code as it is now: `{kind, name,
    plugin}`, a command named as `Sdlc-Tool` names its call without the `Bash:`."""
    factory = _factory_in_play(home)
    own = sdlc._own_repo(home)
    items = [
        {"kind": "skill", "name": name, "plugin": name.split(":")[0]}
        for name, _ in _skill_dirs(factory)
    ]
    items += [
        {"kind": "command", "name": f"sdlc.py:{c}", "plugin": "sdlc"}
        for c in sorted(sdlc.COMMANDS)
        if own or c not in OWN_REPO_COMMANDS
    ]
    script = sdlc.PLUGIN_DIR / FACTORY_DIR / "scripts" / "factory.py"
    if factory and script.is_file():
        found = sorted(set(COMMAND_RE.findall(script.read_text(encoding="utf-8"))))
        items += [{"kind": "command", "name": f"factory.py:{c}", "plugin": "sdlc-factory"}
                  for c in found]  # fmt: skip
    items += [
        {"kind": "key", "name": f"{section}.{key}", "plugin": "sdlc"}
        for section, keys in sdlc.CONFIG_KEYS.items()
        for key in keys
        if f"{section}.{key}" not in sdlc.RETIRED_KEYS
    ]
    return items


def _callers(factory: bool) -> dict[str, set[str]]:
    """Each script command's callers: the skills whose bash blocks, `SKILL.md` and side files,
    run it (`sdlc.bash_commands()`, as `prose_metrics()` reads them)."""
    found: dict[str, set[str]] = {}
    for skill, folder in _skill_dirs(factory):
        for path in sorted(folder.glob("*.md")):
            for line in sdlc.bash_commands(path.read_text(encoding="utf-8")):
                for script, cmd in SCRIPT_CALL_RE.findall(line):
                    found.setdefault(f"{script}:{cmd}", set()).add(skill)
    return found


def _text_of(node) -> str | None:
    """A string literal's value, or None for any other node."""
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _callee(call: ast.Call) -> str | None:
    """The name a call calls: `f(...)`'s `f`, `x.f(...)`'s `f`."""
    f = call.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def _code_reads(texts: tuple[str, ...], config: dict) -> dict[str, set[str]]:
    """Each `@command("name")` in `texts`, scripts sharing one namespace, with the `section.key`s
    of `config` it reads by name, it or any function it reaches by name (a method included):
    `x["section"]["key"]`, `x["section"].get("key")`, the same through a name bound to
    `x["section"]`, and through a parameter a section is handed to, followed from call to call.
    A key only written is not read; a whole section printed or iterated reads no key by name.
    Reaching a function is any mention of its name, so a key read on one branch counts: a read
    the scan wrongly finds keeps a key off the retire list, which is the safer error. Pure."""
    defs: dict[str, list] = {}
    commands: dict[str, str] = {}
    for text in texts:
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                defs.setdefault(node.name, []).append(node)
                for d in node.decorator_list:
                    name = _text_of(d.args[0]) if isinstance(d, ast.Call) and d.args else None
                    if name and _callee(d) == "command":
                        commands[name] = node.name
    info: dict = {}  # each function: its parents, calls, names it mentions, sections it binds
    for nodes in defs.values():
        for node in nodes:
            parent, calls, refs, local = {}, [], set(), {}
            for n in ast.walk(node):
                for child in ast.iter_child_nodes(n):
                    parent[child] = n
                if isinstance(n, ast.Name | ast.Attribute):
                    refs.add(n.id if isinstance(n, ast.Name) else n.attr)
                if isinstance(n, ast.Call) and _callee(n) in defs:
                    calls.append(n)
                if (
                    isinstance(n, ast.Assign) and len(n.targets) == 1
                    and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Subscript)
                    and _text_of(n.value.slice) in config
                ):  # fmt: skip
                    local[n.targets[0].id] = _text_of(n.value.slice)
            info[node] = (parent, calls, refs & defs.keys(), local)
    bound: dict = {node: {} for node in info}  # each function's parameters handed a section

    def section(n, names: dict) -> str | None:
        if isinstance(getattr(n, "ctx", None), ast.Load):
            if isinstance(n, ast.Subscript) and _text_of(n.slice) in config:
                return _text_of(n.slice)
            if isinstance(n, ast.Name):
                return names.get(n.id)
        return None

    changed = True
    while changed:
        changed = False
        for node, (_, calls, _, local) in info.items():
            names = {**bound[node], **local}
            for call in calls:
                for target in defs[_callee(call)]:
                    params = [a.arg for a in target.args.posonlyargs + target.args.args]
                    if params[:1] in (["self"], ["cls"]) and isinstance(call.func, ast.Attribute):
                        params = params[1:]
                    given = list(zip(params, call.args, strict=False))
                    given += [(k.arg, k.value) for k in call.keywords if k.arg]
                    for param, arg in given:
                        sec = section(arg, names)
                        if sec and bound[target].get(param) != sec:
                            bound[target][param], changed = sec, True
    reads: dict[str, set[str]] = {}
    for node, (parent, _, _, local) in info.items():
        names, got = {**bound[node], **local}, reads.setdefault(node.name, set())
        for n in parent:
            sec = section(n, names)
            up = parent.get(n)
            key = None
            if sec and isinstance(up, ast.Subscript) and up.value is n:
                key = _text_of(up.slice) if isinstance(up.ctx, ast.Load) else None
            elif sec and isinstance(up, ast.Attribute) and up.attr == "get":
                call = parent.get(up)
                key = _text_of(call.args[0]) if isinstance(call, ast.Call) and call.args else None
            if key in config.get(sec or "", {}):
                got.add(f"{sec}.{key}")
    out = {}
    for name, fn in commands.items():
        seen, todo = set(), [fn]
        while todo:
            if (at := todo.pop()) not in seen:
                seen.add(at)
                todo += [ref for node in defs[at] for ref in info[node][2]]
        out[name] = set().union(*(reads[f] for f in seen))
    return out


# Each key's readers, by the plugin's folder, whether the factory is in play and the keys: the
# scan reads every script once a run.
_READERS: dict[tuple, dict[str, set[tuple[str, str]]]] = {}


def _key_readers(factory: bool) -> dict[str, set[tuple[str, str]]]:
    """Each config key's readers, from the code as it is now: the `sdlc.py` commands that read it
    by name (`_code_reads()`, over the core's scripts and trackers as one namespace; `factory.py`
    reads its own settings, never these keys), and the skills, the factory's with `factory`, whose
    files name it as `section.key`, as `(kind, name)` like the surface's items."""
    cache = (sdlc.PLUGIN_DIR, factory, tuple((s, tuple(k)) for s, k in sdlc.CONFIG_KEYS.items()))
    if cache in _READERS:
        return _READERS[cache]
    found: dict[str, set[tuple[str, str]]] = {}
    paths = sorted(p for g in ("scripts/*.py", "scripts/trackers/*.py")
                   for p in sdlc.PLUGIN_DIR.glob(g))  # fmt: skip
    texts = tuple(p.read_text(encoding="utf-8") for p in paths)
    for cmd, keys in _code_reads(texts, sdlc.CONFIG_KEYS).items():
        for key in keys:
            found.setdefault(key, set()).add(("command", f"sdlc.py:{cmd}"))
    names = [f"{s}.{k}" for s, keys in sdlc.CONFIG_KEYS.items() for k in keys]
    named = re.compile(r"(?<![\w.])(" + "|".join(map(re.escape, names)) + r")(?![\w])")
    for skill, folder in _skill_dirs(factory):
        for path in sorted(folder.glob("*.md")):
            for key in named.findall(path.read_text(encoding="utf-8")):
                found.setdefault(key, set()).add(("skill", skill))
    _READERS[cache] = found
    return found


def _keys_set(home: Path, ref: str | None) -> set[str] | None:
    """The `section.key`s the config at `ref` sets itself, read raw, never merged over the
    defaults; None with no ref to read."""
    if not ref:
        return None
    text = sdlc._git(home, "show", f"{ref}:{sdlc.HOST_DIR}/config.toml")
    try:
        data = tomllib.loads(text) if text else {}
    except tomllib.TOMLDecodeError:
        data = {}
    return {f"{s}.{k}" for s, table in data.items() if isinstance(table, dict) for k in table}


def _recorded(c: dict, kind: str) -> bool:
    """Whether a closed change's `Close` commit carries the lines that would show `kind`'s use:
    `Sdlc-Skill` for a skill, `Sdlc-Tool` for a command."""
    return bool((c.get("metrics") or {}).get("skills" if kind == "skill" else "tools"))


def _counted_before(changes: list[dict], kind: str) -> bool:
    """Whether a window's changes closed before `kind`'s lines were written: none carries them,
    and one was measured from its transcripts (`_minutes_measured()`), so a run would have."""
    return not any(_recorded(c, kind) for c in changes) and any(
        _minutes_measured(c) for c in changes
    )


def _uses(changes: list[dict]) -> Counter:
    """Each skill's runs and each command's calls across `changes`: a command's from `Sdlc-Tool`
    alone, never `Sdlc-Calls`, which splits the same calls by role."""
    uses: Counter = Counter()
    for c in changes:
        m = c.get("metrics") or {}
        for name, fields in (m.get("skills") or {}).items():
            runs = fields.get("runs")
            uses[("skill", name)] += runs if isinstance(runs, int) else 0
        for name, fields in (m.get("tools") or {}).items():
            hit = TOOL_CALL_RE.match(name)
            n = fields.get("calls")
            if hit and isinstance(n, int):
                uses[("command", f"{hit[1]}:{hit[2]}")] += n
    return uses


def _states(
    items: list[dict],
    changes: list[dict],
    keys: set[str] | None,
    callers: dict[str, set[str]],
    readers: dict[str, set[tuple[str, str]]],
) -> list[dict]:
    """Each item with its `uses` and `state` in one window: `used` when anything counted it;
    `unmeasured`, with its `why`, when nothing could have (run outside a change, run by no skill,
    or recorded by no change in the window); `unused` only where a record could have shown it.
    A key's uses are the config setting it (1) and its `readers`' uses (`_key_readers()`); unused
    is a reader a record could show not running, or no reader at all; unmeasured otherwise, with
    `no change recorded it` when that is a reader's why, else `UNSEEN_READ_WHY`."""
    uses = _uses(changes)
    recorded = {k: any(_recorded(c, k) for c in changes) for k in ("skill", "command")}

    def measured(kind: str, name: str) -> tuple[int, str | None]:
        if kind == "skill" and _skill_where(name) == "outside":
            why = OUTSIDE_WHY
        elif kind == "command" and not callers.get(name):
            why = NO_CALLER_WHY
        elif kind == "command" and all(_skill_where(s) != "inside" for s in callers[name]):
            why = OUTSIDE_WHY
        else:
            why = None if recorded[kind] else UNRECORDED_WHY
        return uses[(kind, name)], why

    out = []
    for item in items:
        kind, name = item["kind"], item["name"]
        if kind == "key":
            seen = [measured(*r) for r in sorted(readers.get(name, ()))]
            n = (int(name in keys) if keys is not None else 0) + sum(u for u, _ in seen)
            whys = {w for _, w in seen}
            if keys is None:
                why = "no base branch"
            elif not seen or None in whys:
                why = None
            else:
                why = UNRECORDED_WHY if UNRECORDED_WHY in whys else UNSEEN_READ_WHY
        else:
            n, why = measured(kind, name)
        state = "used" if n else ("unmeasured" if why else "unused")
        out.append({**item, "uses": n, "state": state, **({"why": why} if state == "unmeasured"
                                                              else {})})  # fmt: skip
    return out


def _surface_share(states: list[dict]) -> dict:
    """`used / (used + unused)` per kind and overall: the unmeasured are in neither."""

    def share(rows: list[dict]) -> float | None:
        used = sum(r["state"] == "used" for r in rows)
        return _share(used, used + sum(r["state"] == "unused" for r in rows))

    kinds = {"skills": "skill", "commands": "command", "keys": "key"}
    return {
        **{k: share([r for r in states if r["kind"] == v]) for k, v in kinds.items()},
        "overall": share(states),
    }


def _surface_why(c: dict) -> str:
    """Why a closed change carries neither `Sdlc-Skill` nor `Sdlc-Tool` lines."""
    if not c.get("metrics"):
        return "not measured at close"
    reason = _none_reason(c["metrics"].get("coverage"))
    return reason or "closed before skills and calls were counted"


def surface(home: Path, cfg: dict, changes: list[dict], since: dict | None) -> dict:
    """The plugin's surface and how much of it the window used (the scorecard's Simplicity): every
    skill, script command and config key, built from the code, with each one's use; the share
    used, the unmeasured left out; the retire candidates; setup's footprint; and, in the plugin's
    own repo, the surface's growth per release. Read-only."""
    trunk = cfg["git"]["base"]
    items = _inventory(home)
    factory = _factory_in_play(home)
    callers, readers = _callers(factory), _key_readers(factory)
    states = _states(items, changes, _keys_set(home, trunk), callers, readers)
    footprint, footprint_why = _footprint(home, trunk)
    growth, growth_why = _growth(home, cfg, since)
    why = {"footprint": footprint_why, "growth": growth_why}
    return {
        "items": states,
        "share": _surface_share(states),
        **_coverage(
            changes, lambda c: _recorded(c, "skill") or _recorded(c, "command"), _surface_why
        ),
        "retire": _retire(home, trunk, items, states, callers, readers),
        "footprint": footprint,
        "growth": growth,
        "why": {k: v for k, v in why.items() if v},
    }


# `report_figures()` takes a `surface` flag, which shadows the function there.
_surface = surface


def _window_trailers(home: Path, older: str | None, newer: str) -> list[dict]:
    """The changes closed between two retrospectives with their `Close` commits' trailers alone,
    as `metrics`: `closed_changes()`'s walk without the intents, and every body in one git call."""
    recs = sdlc.closed_changes(home, older, newer, read=False)
    if not recs:
        return []
    shas = [r["close_sha"] for r in recs]
    out = sdlc._git(home, "show", "-s", "--format=%x1e%B", *shas) or ""
    # Every body holds its subject, so none is empty; `_git()`'s strip takes the first `\x1e`.
    bodies = [b for b in out.split("\x1e") if b.strip()]
    for rec, body in zip(recs, bodies + [""] * (len(recs) - len(bodies)), strict=False):
        rec["metrics"] = sdlc.metrics.parse_trailers(body)
    return recs


def _retire(
    home: Path, trunk: str | None, items: list[dict], current: list[dict], callers: dict,
    readers: dict,
) -> dict:  # fmt: skip
    """The items unused in each of the last `RETIRE_AFTER` windows they were measured in, the
    current one first. A window that couldn't measure an item is passed over, neither counting
    nor breaking its run; an item whose use is never recorded (`OUTSIDE_WHY`, `NO_CALLER_WHY`,
    and a key's `UNSEEN_READ_WHY`) is never a candidate. The walk back stops once every item is
    decided, and for a kind at a window closed before that kind was counted
    (`_counted_before()`), since no older one was either.
    `windows` is how many windows the answer rests on: the windows actually read, which is below
    `RETIRE_AFTER` when every item was decided early (each used, or never a candidate), and no
    candidate is hidden then."""
    never = (OUTSIDE_WHY, NO_CALLER_WHY, UNSEEN_READ_WHY)
    runs: dict[tuple, list[str]] = {
        (r["kind"], r["name"]): [] for r in current if r.get("why") not in never
    }
    bounds = sdlc.retrospectives(home, trunk)
    starts = [b["sha"] for b in bounds] + [None]
    ends = [trunk, *(b["sha"] for b in bounds)]
    spent: set[str] = set()  # the kinds no older window can have recorded
    read = 0

    def open_items() -> list[tuple]:
        return [
            k
            for k, seen in runs.items()
            if k[0] not in spent and len(seen) < RETIRE_AFTER and "used" not in seen
        ]

    for at, (older, newer) in enumerate(zip(starts, ends, strict=True)):
        if not trunk or not open_items():
            break
        if at == 0:
            states = current
        else:
            changes = _window_trailers(home, older, newer)
            for kind in ("skill", "command"):
                if _counted_before(changes, kind):
                    spent.add(kind)
            wanted = [i for i in items if (i["kind"], i["name"]) in open_items()]
            states = _states(wanted, changes, _keys_set(home, newer), callers, readers)
        read += 1
        for r in states:
            key = (r["kind"], r["name"])
            if key in runs and r["state"] != "unmeasured" and len(runs[key]) < RETIRE_AFTER:
                runs[key].append(r["state"])
    named = {(i["kind"], i["name"]): i for i in items}
    candidates = [
        {**named[k], "windows": len(seen)}
        for k, seen in runs.items()
        if len(seen) == RETIRE_AFTER and set(seen) == {"unused"}
    ]
    return {"after": RETIRE_AFTER, "windows": read, "items": candidates}


def _lines_under(home: Path, ref: str, paths: list[str]) -> dict[str, int]:
    """Lines per text file under `paths` at `ref`, in one git call."""
    out = sdlc._git(home, "grep", "-I", "-c", "", ref, "--", *paths) or ""
    return indicators.grep_counts(out, ref)


def _footprint(home: Path, trunk: str | None) -> tuple[dict | None, str | None]:
    """What setup left in the host, on the base branch: the paths `setup.json` says it created,
    the keys the config sets, and the lines of `.sdlc/`'s tracked files but the change folders,
    the reports and the retrospectives. None, with why, without a `setup.json`."""
    text = sdlc._git(home, "show", f"{trunk}:{sdlc.MANIFEST}") if trunk else None
    try:
        manifest = json.loads(text) if text else None
    except ValueError:
        manifest = None
    if not isinstance(manifest, dict):
        return None, f"no {sdlc.MANIFEST} on the base branch"
    left_out = (
        f"{sdlc.work_rel(home)}/",
        f"{sdlc.HOST_DIR}/{RETROS}/",
        f"{sdlc.REPORTS}/",
    )
    lines = _lines_under(home, trunk, [f"{sdlc.HOST_DIR}/"])
    created = manifest.get("created")
    return {
        "created": len(created) if isinstance(created, list) else 0,
        "keys": len(_keys_set(home, trunk) or ()),
        "lines": sum(n for p, n in lines.items() if not p.startswith(left_out)),
    }, None


# The prose a person or a session reads, counted at each release for `doc_lines`.
DOC_PATHS = (
    "skills/", f"{FACTORY_DIR}/skills/", "agents/", f"{FACTORY_DIR}/agents/", "guide/",
    "defaults/", "templates/", "docs/", "README.md",
)  # fmt: skip
SKILL_PATH_RE = re.compile(rf"^(?:{FACTORY_DIR}/)?skills/[^/]+/SKILL\.md$")
GROWTH_COUNTS = ("skills", "commands", "keys", "doc_lines")


def _surface_at(home: Path, tag: str) -> dict:
    """The surface's size at `tag`, each count None when it can't be read there: commands before
    the `@command` registry, keys without a `setup.json`."""
    listed = sdlc._git(home, "ls-tree", "-r", "--name-only", tag, "--", "skills", FACTORY_DIR)
    skills = sum(bool(SKILL_PATH_RE.match(p)) for p in (listed or "").splitlines())
    core = COMMAND_RE.findall(sdlc._git(home, "show", f"{tag}:scripts/sdlc.py") or "")
    more = COMMAND_RE.findall(
        sdlc._git(home, "show", f"{tag}:{FACTORY_DIR}/scripts/factory.py") or ""
    )
    try:
        manifest = json.loads(sdlc._git(home, "show", f"{tag}:{sdlc.MANIFEST}") or "null")
    except ValueError:
        manifest = None
    keys = manifest.get("config_keys") if isinstance(manifest, dict) else None
    return {
        "skills": skills if listed is not None else None,
        # `core` is empty only at a tag from before the `@command` registry (or with no
        # `sdlc.py`), where no command can be counted: None there, never the factory's alone.
        "commands": len(set(core)) + len(set(more)) if core else None,
        "keys": len(keys) if isinstance(keys, list) else None,
        "doc_lines": sum(_lines_under(home, tag, list(DOC_PATHS)).values()),
    }


def _growth(home: Path, cfg: dict, since: dict | None) -> tuple[list | None, str | None]:
    """The surface at each release tag in the window and the tag before the first, oldest first,
    each with its change since the one before and the `major` and `minor` changes between them.
    Only in the plugin's own repo: a host's tags are its own releases, not the plugin's."""
    if not sdlc._own_repo(home):
        return None, "only in the plugin's own repo"
    tags = [t["tag"] for t in sdlc._release_tags(home, cfg, since)]
    if not tags:
        return [], None
    every = [t["tag"] for t in sdlc._release_tags(home, cfg, None)]
    at = every.index(tags[0]) if tags[0] in every else 0
    rows: list[dict] = []
    prev: dict | None = None
    for tag in every[max(at - 1, 0) : at] + tags:
        counts = _surface_at(home, tag)
        row: dict = {"tag": tag, **counts, "change": None, "capability": None}
        if prev:
            row["change"] = {
                k: counts[k] - prev[k] if counts[k] is not None and prev[k] is not None else None
                for k in GROWTH_COUNTS
            }
            row["capability"] = [
                c["name"]
                for c in sdlc.closed_changes(home, prev["tag"], tag)
                if c["impact"] in ("major", "minor")
            ]
        rows.append(row)
        prev = row
    return rows, None


def rankable_entries(home: Path, today: date) -> list[dict]:
    """The register's entries a retrospective may re-rank: open ideas and bugs, each with its
    `Priority:` and `Theme:` as they stand. Nits are ranked by their `Cost:` and `Value:`, and an
    entry being built (tagged, or named by an open change's `idea:` or `fixes:`) is its change's,
    so neither is listed."""
    claims = [ref for ref, _ in sdlc._open_claims(home)]
    return [
        {"id": e["id"], "title": e["title"], "kind": sdlc.entry_kind(e),
         "priority": sdlc.entry_priority(e), "theme": sdlc.entry_theme(e),
         "age_days": sdlc._age_days({"created": e["date"]}, today)}
        for e in sdlc.inbox_entries(home)
        if not (sdlc.is_nit(e) or sdlc.is_building(e)
                or any(sdlc.ref_matches(r, e) for r in claims))
    ]  # fmt: skip


def _rework(
    home: Path,
    trunk: str | None,
    changes: list[dict],
    bases: dict[str, str | None],
    diffs: dict[str, str],
) -> tuple[list[dict], list[dict], list[str]]:
    """Retro's rework, from what people declared, and the questions blame raises beside it.

    A link is declared on a change's own `reworks:` line, or by a bug it fixed whose
    `Introduced by:` names a change: `{change, reworks, days, via}`, the earlier change anywhere in
    history (`dropped` when it never landed), whatever the gap. A question is what blame finds and
    no link explains: lines an earlier change in the window wrote that a later one removed or
    replaced, blamed at the later change's start. Appending touches nothing, so it is never one.
    Questions are never counted: a planned follow-up replacing a first draft isn't a fix. Each id
    naming no change is a problem. `diffs` is `_diffs()`'s, read once for `_spend()` too."""
    if not changes:
        return [], [], []
    closed = {
        c["name"]: c["close_date"] for c in sdlc.closed_changes(home, None, trunk, read=False)
    }
    gone = {d["name"]: d["drop_date"] for d in sdlc.dropped_changes(home, None, trunk)}
    links: dict[tuple[str, str], dict] = {}
    problems: list[str] = []

    def link(later: dict, ident: str, why: str) -> bool:
        name = next((n for n in [*closed, *gone] if sdlc.names_change(n, ident)), None)
        if name is None:
            return False
        if name != later["name"]:
            row = links.setdefault((later["name"], name), {
                "change": later["name"], "reworks": name, "via": [],
                "days": sdlc._days_between(closed.get(name) or gone.get(name) or "",
                                      later["close_date"]),
            })  # fmt: skip
            if name not in closed:
                row["dropped"] = True
            if why not in row["via"]:
                row["via"].append(why)
        return True

    for rec in changes:
        for ident in rec.get("reworks") or []:
            if not link(rec, ident, "reworks"):
                problems.append(f"{rec['name']}: reworks {ident!r} names no change")
        for bug_id, fixed in ((rec.get("metrics") or {}).get("fixes") or {}).items():
            by = str(fixed.get("introduced_by") or "")
            if by and by != "unknown":
                link(rec, by, f"bug {bug_id}")

    # Which change wrote each commit in the window: its branch from where it started. A commit two
    # ranges share is the earlier change's.
    order = {rec["name"]: i for i, rec in enumerate(changes)}
    owners: dict[str, str] = {}
    for rec in changes:
        if base := bases.get(rec["name"]):
            for sha in (sdlc._git(home, "rev-list", f"{base}..{rec['sha']}") or "").split():
                owners.setdefault(sha, rec["name"])
    # The register and setup's record are rewritten by the script, never by one change's hand.
    written = {f"{sdlc.work_rel(home)}/{sdlc.INBOX}", sdlc.MANIFEST}
    hits: dict[tuple[str, str], dict] = {}
    for rec in changes:
        base = bases.get(rec["name"])
        if not base:
            continue
        diff = diffs[rec["name"]]
        for path, runs in indicators.removed_ranges(diff).items():
            if path.startswith(sdlc.CHANGE_FOLDERS) or path in written:
                continue
            spans = [arg for start, n in runs for arg in ("-L", f"{start},+{n}")]
            blame = sdlc._git(home, "blame", "--porcelain", *spans, base, "--", path) or ""
            for sha in indicators.blame_commits(blame):
                owner = owners.get(sha)
                if owner and order[owner] < order[rec["name"]]:
                    hit = hits.setdefault((rec["name"], owner), {
                        "change": rec["name"], "touches": owner, "files": [], "lines": 0,
                    })  # fmt: skip
                    hit["lines"] += 1
                    if path not in hit["files"]:
                        hit["files"].append(path)
    questions = [hit for pair, hit in hits.items() if pair not in links]
    return list(links.values()), questions, problems


# ---------------------------------------------------------------- workarounds (180)
#
# What the process didn't plan for, read from history: a commit on the base branch no command
# made, a record edited there by hand, an entry the register held before and gained again, and
# the factory's overrides each change's own commit records. A reading, not a guard: a hand commit
# worded as a command's is counted as the command's.

# A release's commit, as `cmd_release` words it.
RELEASE_SUBJECT_RE = re.compile(r"^Release \d+\.\d+\.\d+$")


def _commands_commit(subject: str) -> bool:
    """Whether a commit on the base branch is one the plugin's commands or skills make there:
    `Close` or `Drop` a change, a register commit (every `; ` part `File`, `Retire`, `Update` or
    `Triage`), a release, a retrospective, or setup's and uninstall's own (`SETUP_SUBJECTS`)."""
    if _closing_subject(subject):
        return True
    words = tuple(f"{w} " for w in (*sdlc.INBOX_SUBJECTS, sdlc.TRIAGE_SUBJECT))
    if all(part.startswith(words) for part in subject.split("; ")):
        return True
    if RELEASE_SUBJECT_RE.match(subject) or sdlc.RETRO_RE.match(subject):
        return True
    return any(
        subject == s or (s.endswith(" ") and subject.startswith(s)) for s in sdlc.SETUP_SUBJECTS
    )


def _is_record(path: str) -> bool:
    """Whether a path git prints is one of the process's records: a change folder or the register
    (`CHANGE_FOLDERS`), a retrospective's report, the setup manifest or the change counter."""
    host = sdlc.HOST_DIR
    return path.startswith((*sdlc.CHANGE_FOLDERS, f"{host}/{RETROS}/")) or path in (
        sdlc.MANIFEST, f"{host}/{sdlc.LAST_ID}",
    )  # fmt: skip


def _log_blocks(home: Path, *args: str) -> list[tuple[str, str, str, str]]:
    """`git log --first-parent --reverse` with `args`, each commit as `(sha, short, subject,
    rest)`, `rest` whatever `args` asked git to print after it (paths, a patch). Paths come
    unescaped (`core.quotePath=false`), as the record prefixes they are compared with are."""
    fmt = "--format=%x01%H%x00%h%x00%s"
    first = ("-c", "core.quotePath=false", "log", "--first-parent", "--reverse", "--no-renames")
    log = sdlc._git(home, *first, fmt, *args) or ""
    found = []
    for block in log.split("\x01")[1:]:
        head, _, rest = block.partition("\n")
        sha, short, subject = (head.split("\x00") + ["", ""])[:3]
        found.append((sha, short, subject, rest))
    return found


# Why `restored` is null: nothing was added that could have been restored (189 R11).
NO_ENTRY_ADDED = {"no register entry added in the window": 0}


def _restored(home: Path, trunk: str, window: set[str]) -> dict:
    """The entries the register gained in the window that it held before (R3): every first-parent
    commit to the tip, read in order, keeps the ids the register holds and has ever held; an id a
    window commit adds that it held once and not now is restored. An id a commit removes and adds
    is an edit or a move. `n` is every id the window's commits added."""
    paths = [f"{w}{name}" for w in sdlc.CHANGE_FOLDERS for name in (sdlc.INBOX, sdlc.OLD_INBOX)]
    held: set[str] = set()
    ever: set[str] = set()
    rows, gained = [], 0
    for sha, short, subject, diff in _log_blocks(home, "-p", trunk, "--", *paths):
        added, removed = set(), set()
        for line in diff.splitlines():
            m = sdlc.ENTRY_RE.match(line[1:]) if line[:1] in ("+", "-") else None
            if m and not line.startswith(("+++", "---")):
                (added if line[0] == "+" else removed).add(f"{m.group(1)}-{m.group(2)}")
        new = added - removed
        if sha in window:
            gained += len(new)
            rows += [
                {"id": i, "sha": short, "subject": subject}
                for i in sorted(new)
                if i in ever and i not in held
            ]
        held = (held - removed) | added
        ever |= added
    return {"count": len(rows) if gained else None, "n": gained, "rows": rows,
            "missing_because": {} if gained else dict(NO_ENTRY_ADDED)}  # fmt: skip


def _overrides(home: Path, changes: list[dict], dropped: list[dict]) -> dict:
    """The factory's overrides (R6), from each closed change's own commit and each dropped one's
    tip, over the changes a factory run built (a `decision.md`): the train's ejections by cause
    and its stops by train, from `runs/ejections.jsonl` (a stop row from before it named its
    train counts once per change), and the fixes the person asked for at landing. Null over 0."""
    fr = sdlc.factory_records
    n, fixes = 0, 0
    causes: Counter = Counter()
    trains: set = set()
    for rec in [*changes, *dropped]:
        show, listing = _records_at(home, rec)
        if show(fr.DECISION_FILE) is None:
            continue
        n += 1
        fixes += fr.land_asks(listing)
        for row in fr.ejections(show):
            cause = str(row.get("cause") or "unknown")
            if cause != "stop":
                causes[cause] += 1
            else:
                train = row.get("train")
                trains.add(train if isinstance(train, str) else ("change", rec["name"]))
    return {
        "ejections": {
            "count": sum(causes.values()) if n else None, "by_cause": dict(sorted(causes.items())),
            "n": n,
        },
        "stops": {"count": len(trains) if n else None, "n": n},
        "fixes": {"count": fixes if n else None, "n": n},
    }  # fmt: skip


def _workarounds(
    home: Path,
    cfg: dict,
    since: dict | None,
    changes: list[dict],
    dropped: list[dict],
    bases: dict[str, str | None],
) -> tuple[dict, list[str]]:
    """The Simplicity pillar's workarounds (180), from history alone, and a problem for each change
    whose start is unknown. Every first-parent commit from the last retrospective (else the
    adoption commit, else the start) to the base's tip is a closed change's own (`<its
    base>..<its commit>`), a command's (`_commands_commit()`), or outside the loop: `hand_record`
    when it touches a record (`_is_record()`), `outside` when not. A change with no start claims
    only its own commit, and the commits before it back to the last `Close` or `Drop` are
    `unknown`, never outside. Each count carries its `n` and is null, never 0, when `n` is 0.
    Read-only: git reads alone."""
    trunk = cfg["git"]["base"]
    problems: list[str] = []
    start = since["sha"] if since else sdlc._adoption_commit(home)
    commits = _log_blocks(home, "--name-only", f"{start}..{trunk}" if start else trunk)
    commits = commits if trunk else []
    line = [sha for sha, *_ in commits]
    own: set[str] = set()
    unknown: dict[str, str] = {}
    for rec in changes:
        base = bases.get(rec["name"])
        if base:
            span = f"{base}..{rec['sha']}"
            own.update((sdlc._git(home, "rev-list", "--first-parent", span) or "").split())
            continue
        sha = sdlc._git(home, "rev-parse", "--verify", "-q", f"{rec['sha']}^{{commit}}")
        own.add(sha or "")
        i = line.index(sha) - 1 if sha in line else -1
        mine = 0
        while i >= 0 and not _closing_subject(commits[i][2]):
            if line[i] not in own and not _commands_commit(commits[i][2]):
                unknown[line[i]] = rec["name"]
                mine += 1
            i -= 1
        if mine:
            problems.append(
                f"{rec['name']}: its start is unknown, so {mine} commit(s) before it on {trunk} "
                "are counted as unknown, not outside"
            )
    rows: dict[str, list[dict]] = {"outside": [], "hand_record": [], "unknown": []}
    for sha, short, subject, paths in commits:
        if sha in own or _commands_commit(subject):
            continue
        row = {"sha": short, "subject": subject}
        if sha in unknown:
            rows["unknown"].append({**row, "change": unknown[sha]})
        elif any(_is_record(p) for p in paths.splitlines() if p):
            rows["hand_record"].append(row)
        else:
            rows["outside"].append(row)
    n = len(commits)
    # Why a count is null (189 R11): with no commit, nothing could be outside the loop.
    no_commit = {} if n else {"no commit on the base branch in the window": 0}
    block = {
        kind: {"count": len(rows[kind]) if n else None, "n": n, "rows": rows[kind],
               "missing_because": no_commit}
        for kind in ("outside", "hand_record", "unknown")
    }  # fmt: skip
    block["restored"] = (
        _restored(home, trunk, set(line))
        if trunk
        else {"count": None, "n": 0, "rows": [], "missing_because": dict(NO_ENTRY_ADDED)}
    )
    block["overrides"] = _overrides(home, changes, dropped)
    return block, problems


def _closing_subject(subject: str) -> bool:
    """Whether a commit closes or drops a change: where one change's commits end on the line."""
    return any(
        subject.startswith(p) and sdlc.DIR_RE.match(subject[len(p) :].strip())
        for p in (sdlc.CLOSE_PREFIX, sdlc.DROP_PREFIX)
    )


def retro(home: Path, cfg: dict, today: date | None = None) -> dict:
    """What the retrospective counts: everything since the last one, from history. Read-only."""
    today = today or date.today()
    trunk = cfg["git"]["base"]
    f = report_figures(home, cfg, today, surface=True)
    since, changes, dropped, bases = f["since"], f["changes"], f["dropped"], f["bases"]
    problems: list[str] = [] if trunk else [sdlc.trunk_refusal(home, trunk)]
    kind = _kind(cfg)
    for rec in changes:
        problems += rec.pop("problems")
        base, rows = bases[rec["name"]], f["rows"][rec["name"]]
        if not base:
            name, work = rec["name"], sdlc.work_rel(home)
            problems.append(
                f"{name}: no commit holds {work}/{name}/intent.md, so its size is unknown"
            )
        lines = sum((added or 0) + (deleted or 0) for _, added, deleted in rows)
        size = indicators.change_size(rows, kind)
        rec.update(
            files=len(rows) if base else None,
            lines=lines if base else None,
            added=size["added"] if base else None,
            deleted=size["deleted"] if base else None,
            by_kind=size["by_kind"] if base else None,
        )
    for rec in dropped:
        problems += rec.pop("problems")
        # What the dropped branch touched: its tip against where it left the base.
        fork = sdlc._git(home, "merge-base", f"{rec['drop_sha']}^1", f"{rec['drop_sha']}^2")
        files = (
            (sdlc._git(home, "diff", "--name-only", fork, rec["sha"]) or "").split() if fork else []
        )
        rec["files"] = len(files)
    problems += f["problems"]
    rework, questions, bugs = f["rework"], f["questions"], f["bugs"]
    a = sdlc.analyze(home, today)
    ideas = [
        i
        for i in sdlc.inbox_entries(home)
        if not (sdlc.is_building(i) or sdlc.is_nit(i) or sdlc.is_bug(i))
    ]
    direction = sdlc.direction_items(sdlc._direction_text(home, cfg))
    open_names = [f"{r['id']}-{r['slug']}" for r in a["open"]]
    direction["milestones"] = sdlc._milestone_verdicts(home, direction["items"], open_names, trunk)
    doc = sdlc.product_doc(home, cfg)
    product = (
        None if doc is None else _product(home, cfg, doc, changes, a["open"], direction, bases)
    )
    lookback = _lookback(home, trunk) if trunk else None
    process = f["process"]
    return {
        "since": since,
        "today": today.isoformat(),
        "changes": changes,
        "dropped": dropped,
        "dropped_at_counts": dict(Counter(d.get("dropped_at", "unknown") for d in dropped)),
        "dropped_cost": dropped_cost(dropped),
        "problems": problems,
        "rework": rework,
        "rework_questions": questions,
        "open": [
            {
                "name": f"{r['id']}-{r['slug']}",
                "title": sdlc.TITLE_ID_RE.sub("", r["title"]),
                "tier": r["tier"],
                "stage": r["stage"],
                "age_days": r.get("age_days"),
            }
            for r in a["open"]
        ],  # fmt: skip
        "ideas": {
            "open": len(ideas),
            "oldest": min((i["date"] for i in ideas), default=None),
        },
        "entries": rankable_entries(home, today),
        "nits": sdlc.nits_summary(sdlc.nit_entries(home)[0], today),
        "bugs": bugs,
        "process": process,
        "by_way": f["by_way"],
        "report": report_rel(today),
        "tiers": dict(Counter(str(c["tier"]) for c in changes)),
        "impacts": dict(Counter(c["impact"] or "unset" for c in changes)),
        "origins": _origins(changes),
        "releases": sdlc._release_tags(home, cfg, since),
        "unmeasured": UNMEASURED,
        "autonomy": f["autonomy"],
        "pipeline": f["pipeline"],
        "direction": direction,
        "metrics": f["metrics"],
        "product": product,
        "prose": prose_metrics(home, cfg),
        "architecture": _architecture(home, cfg, since, changes, kind, lookback),
        "spend": f["spend"],
        "cost": f["cost"],
        "tests": _tests(home, cfg, lookback),
        "surface": f["surface"],
        "simplicity": {"workarounds": f["workarounds"]},
        "scorecard": f["scorecard"],
        "experience": {"last": f["experience_last"]},
        "hosts": f["hosts"],
        **f["value"],
    }


def _origins(changes: list[dict]) -> dict:
    """The window's closed changes by where their findings came from, each list their names:
    `unknown` for every change with no valid `origin:` line, never folded into `self`."""
    out: dict = {"host": [], "self": [], "unknown": []}
    for rec in changes:
        out[rec.get("origin") if rec.get("origin") in sdlc.ORIGINS else "unknown"].append(
            rec["name"]
        )
    return {**out, "n": len(changes)}


def _change_rows(home: Path, rec: dict) -> tuple[str | None, list]:
    """A closed change's numstat rows: its whole branch from where it started, or, with no start,
    its last commit alone. The start comes first, None when it couldn't be found."""
    base = sdlc._change_base(home, rec["name"], rec["sha"], rec["close_sha"])
    if base:
        numstat = sdlc._git(home, "diff", "--numstat", "--no-renames", base, rec["sha"]) or ""
    else:
        numstat = (
            sdlc._git(home, "diff-tree", "--no-commit-id", "--numstat", "-r", rec["sha"]) or ""
        )
    return base, indicators.numstat_rows(numstat)


def _added_diff(home: Path, rec: dict, base: str | None) -> str:
    """A closed change's `git diff -U0`, on the same base as `_change_rows()`: its whole branch
    from where it started, or its last commit alone without a start."""
    if base:
        return sdlc._git(home, "diff", "-U0", "--no-renames", base, rec["sha"]) or ""
    return sdlc._git(home, "diff-tree", "-U0", "-p", "--no-commit-id", "-r", rec["sha"]) or ""


def _diffs(home: Path, changes: list[dict], bases: dict[str, str | None]) -> dict[str, str]:
    """Each change's `_added_diff()`, by name: one git call per change, which `_rework()`'s blame
    and `_spend()`'s comment count share."""
    return {rec["name"]: _added_diff(home, rec, bases.get(rec["name"])) for rec in changes}


def _unrecorded(m: dict | None) -> str | None:
    """Why a change's `Close` commit carries no tool calls or words, None when it does."""
    totals = (m or {}).get("totals") or {}
    if isinstance(totals.get("tools"), int) and isinstance(totals.get("words"), int):
        return None
    if not totals:
        return "not measured at close"
    reason = _none_reason((m or {}).get("coverage"))
    return reason if reason is not None else "closed before tool calls and words were counted"


def _spend(home: Path, cfg: dict, changes: list[dict], diffs: dict[str, str]) -> dict:
    """What each change in the window spent beside its size: its added code lines and their line
    comments (`indicators.comment_lines()`, code alone as `_kind()` tells it), its agent `out`
    tokens, the person's words per stage and its tool calls from its `Close` commit, then
    `indicators.spend()`'s medians, outliers and tool ranking over them. A change whose commit has
    no `tools=` or `words=` is `recorded: false` with `why`, and its missing counts stay None.
    `diffs` is `_diffs()`'s. `changes` holds a change's own numbers: `cmd_retro()` prints them
    only with `--metrics`."""
    kind = _kind(cfg)
    register = f"{sdlc.work_rel(home)}/{sdlc.INBOX}"

    def code(path: str) -> bool:
        return (
            not path.startswith(sdlc.CHANGE_FOLDERS) and path != register and kind(path) == "code"
        )

    rows = []
    for rec in changes:
        m = rec.get("metrics") or {}
        totals = m.get("totals") or {}
        why = _unrecorded(m)
        counted = indicators.comment_lines(diffs[rec["name"]], code)
        tools = m.get("tools") or {}
        rows.append({
            "change": rec["name"], "tier": rec["tier"],
            "code_added": counted["added"] + counted["unknown_lines"],
            "comment_lines": counted["comment_lines"], "comment_base": counted["added"],
            "out": totals.get("out") if isinstance(totals.get("out"), int) else None,
            "words": None if why else {
                s: v.get("words") for s, v in (m.get("stages") or {}).items()
                if isinstance(v.get("words"), int)
            },
            "tools": None if why else totals["tools"],
            "errors": None if why else sum(t.get("errors") or 0 for t in tools.values()),
            "by_tool": {} if why else {
                n: {"calls": t.get("calls") or 0, "errors": t.get("errors") or 0}
                for n, t in tools.items()
            },
            "recorded": why is None, "why": why,
        })  # fmt: skip
    out = indicators.spend(rows)
    out["why"] = dict(Counter(r["why"] for r in rows if r["why"]))
    out.update(_coverage(rows, lambda r: r["recorded"], lambda r: r["why"]))
    out["changes"] = rows
    out["agents"] = _agents(changes)
    return out


def _agents(changes: list[dict]) -> dict:
    """How the window's factory agents worked, from each `Close` commit's `Sdlc-Role` lines:
    grouped by role and model (`unknown` with no `model=`), each group's changes, runs, and the
    per-change median of each count in `metrics.BEHAVIOURS`, a role from before read as its name
    now (`factory_records.RENAMED`: the verifier is the arbiter). A role line without `edits=` was
    closed before they were counted: `unrecorded`, in no group. `changes` holds each change's
    own rows, in close order: `cmd_retro()` prints them only with `--metrics`."""
    counts = sdlc.metrics.BEHAVIOURS
    rows: list[dict] = []
    unrecorded = 0
    renamed = sdlc.factory_records.RENAMED
    for rec in changes:
        for role, fields in sorted(((rec.get("metrics") or {}).get("roles") or {}).items()):
            role = renamed.get(role, role)
            if not isinstance(fields.get("edits"), int):
                unrecorded += 1
                continue
            model = fields.get("model")
            rows.append({
                "change": rec["name"], "role": role,
                "model": str(model) if model not in (None, "") else "unknown",
                "runs": fields.get("runs") if isinstance(fields.get("runs"), int) else 0,
                **{k: fields.get(k) if isinstance(fields.get(k), int) else None for k in counts},
            })  # fmt: skip
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((row["role"], row["model"]), []).append(row)

    def median(values: list) -> float | None:
        values = [v for v in values if isinstance(v, int)]
        return statistics.median(values) if values else None

    return {
        "groups": [
            {
                "role": role, "model": model, "changes": len({r["change"] for r in rs}),
                "runs": sum(r["runs"] for r in rs),
                "median": {k: median([r[k] for r in rs]) for k in counts},
            }
            for (role, model), rs in sorted(groups.items())
        ],
        "unrecorded": unrecorded,
        "changes": rows,
    }  # fmt: skip


def _kind(cfg: dict):
    """A path's kind (code, tests or docs): `retro.test_paths` and `retro.doc_paths` where set,
    the conventions in `scripts/indicators.py` where not."""
    tests, docs = cfg["retro"]["test_paths"], cfg["retro"]["doc_paths"]
    is_tests = (lambda p: bool(sdlc.risk_paths([p], tests))) if tests else indicators.is_test
    is_docs = (lambda p: bool(sdlc.risk_paths([p], docs))) if docs else indicators.is_doc
    return lambda p: indicators.classify(p, is_tests, is_docs)


def _line_counts(home: Path, ref: str) -> dict[str, int]:
    """Lines per text file at `ref`, in one git call."""
    return indicators.grep_counts(sdlc._git(home, "grep", "-I", "-c", "", ref) or "", ref)


def _skip(home: Path):
    """The paths the architecture and pruning passes leave out: change folders and the register."""
    register = f"{sdlc.work_rel(home)}/{sdlc.INBOX}"
    return lambda path: path.startswith(sdlc.CHANGE_FOLDERS) or path == register


def _lookback(home: Path, trunk: str) -> tuple[list[dict], list[tuple[str, list]], set | None]:
    """The last `ARCH_LOOKBACK` closed changes, past the boundary, oldest first; each one's name
    and numstat rows; and every path on the base branch, None when the listing fails. Read once,
    for the architecture pass and the pruning pass both."""
    recent = sdlc.closed_changes(home, None, trunk, read=False)[-ARCH_LOOKBACK:]
    rows = [(rec["name"], _change_rows(home, rec)[1]) for rec in recent]
    # Quoted as numstat quotes its paths (git's default), so the two compare.
    listed = sdlc._git(home, "ls-tree", "-r", "--name-only", trunk)
    return recent, rows, None if listed is None else set(listed.splitlines())


def _architecture(
    home: Path, cfg: dict, since: dict | None, changes: list[dict], kind, lookback=None
) -> dict | None:
    """What the architecture pass reads: size per tier over the window; hotspots and co-change
    over `lookback` (`_lookback()`, read here when not given); the largest files and each
    kind's totals now and at the last retrospective; and the host's `retro.indicators` output,
    through `_evidence()`. None without a base branch."""
    trunk = cfg["git"]["base"]
    if not trunk:
        return None
    skip = _skip(home)
    recent, named, present = lookback or _lookback(home, trunk)
    lookback = [rows for _, rows in named]
    now = _line_counts(home, trunk)
    # `present`: every path on the base branch, so a hotspot with no lines to count reads as
    # binary or empty when it's there, and as gone when it isn't; None leaves `gone` unknown.
    then = _line_counts(home, since["sha"]) if since else None
    tests, docs = cfg["retro"]["test_paths"], cfg["retro"]["doc_paths"]
    return {
        "lookback": {
            "changes": len(recent),
            "first": recent[0]["name"] if recent else None,
            "last": recent[-1]["name"] if recent else None,
        },
        "kinds": {"tests": tests or "conventions", "docs": docs or "conventions"},
        "size": indicators.size_by_tier(changes),
        "hotspots": indicators.hotspots(lookback, now, skip, present=present),
        "co_change": indicators.co_change(lookback, skip),
        "largest": indicators.largest(now, then, skip),
        "totals": {
            "now": indicators.totals(now, kind, skip),
            "then": None if then is None else indicators.totals(then, kind, skip),
        },
        "host": _indicator_rows(home, since, _evidence(home, cfg["retro"]["indicators"])),
    }


def _last_rows(home: Path, since: dict | None) -> dict[str, dict]:
    """The rows the last retrospective's report shows, read from its own commit by the one table
    reader: `indicators`, each indicator row's value by `(name, unit)`; and `scorecard`, each
    pillar row's `(value, n)` by `(pillar, figure)`. Each empty with no retrospective, none
    committed at that commit, or a report without that table. And `experience`, its rating and
    line (`_last_experience()`), None for any of those (190 R9)."""
    text = ""
    if since:
        rel = report_rel(date.fromisoformat(since["date"]))
        text = sdlc._git(home, "show", f"{since['sha']}:{rel}") or ""
    read = indicators.report_rows
    values = read(text, SCORECARD_HEAD, SCORECARD_KEYS, SCORECARD_VALUE)
    ns = read(text, SCORECARD_HEAD, SCORECARD_KEYS, SCORECARD_N)
    return {
        "indicators": read(text),
        "scorecard": {k: (v, ns.get(k)) for k, v in values.items()},
        "experience": _last_experience(text, since["date"]) if since else None,
    }


def _indicator_rows(home: Path, since: dict | None, ran: list[dict]) -> list[dict]:
    """`_evidence()`'s rows for `retro.indicators`, each read as `indicators.host_rows()`: with
    `rows` (each against the last retrospective's report, `last` and `change`, null where it has
    no such row) and `output` null; or with `rows` null and `not_rows` saying why, its `output`,
    `exit`, `error` and `truncated` as they were. A failure, a timeout or a cut output is never
    read as rows."""
    last = None
    for row in ran:
        if row["error"]:
            timed_out = row["exit"] is None and row["error"].startswith("timed out")
            if timed_out:
                why = "timed out"
            elif row["exit"] is None:
                why = "failed: could not start"
            else:
                why = f"failed: exited {row['exit']}"
            row["rows"], row["not_rows"] = None, why
            continue
        if row["truncated"]:
            row["rows"], row["not_rows"] = None, f"truncated at {len(row['output'])} characters"
            continue
        row["rows"], row["not_rows"] = indicators.host_rows(row["output"])
        if row["rows"] is None:
            continue
        last = _last_rows(home, since)["indicators"] if last is None else last
        for r in row["rows"]:
            r["last"] = last.get((r["name"], r["unit"]))
            r["change"] = None if r["last"] is None else round(r["value"] - r["last"], 3)
        row["output"] = None
    return ran


def bugs_retro(home: Path, cfg: dict, since: dict | None, changes: list[dict], today: date) -> dict:
    """What retro counts about bugs in its window: each reported one once, by id and its reported
    date (open in the register, fixed on a `Close` commit's `Sdlc-Fixes:`, retired on a `Retire`
    commit's `Sdlc-Retired:`), the fixed by severity, the retired by reason, the days from report
    to fix, the open ones by age, and the escapes: each introducing change with its tier, and how
    many no one attributed. Each escape and the window's rate (`by_way`) are also given by the
    introducing change's way (`_way()`). Read from the register and history alone."""
    trunk = cfg["git"]["base"]
    start = since["date"] if since else None
    words = sdlc.severities(home, cfg)
    open_bugs = sdlc.bug_entries(home, words)[0]
    fixed = []
    for rec in changes:
        for bug_id, f in ((rec.get("metrics") or {}).get("fixes") or {}).items():
            fixed.append({"id": bug_id, "change": rec["name"], "date": rec["close_date"],
                          **{k: str(v) for k, v in f.items()}})  # fmt: skip
    retired = []
    triaged: Counter = Counter()
    span = f"{since['sha']}..{trunk}" if since else trunk
    log = sdlc._git(home, "log", "--first-parent", "--format=%x1e%cs%x00%B", span) if trunk else ""
    for record in (log or "").split("\x1e"):
        day, _, body = record.partition("\x00")
        trailers = sdlc.metrics.parse_trailers(body) or {}
        for bug_id, f in (trailers.get("retired") or {}).items():
            retired.append({"id": bug_id, "date": day.strip(), **{k: str(v) for k, v in f.items()}})
        # Issues triage closed without a change: already resolved, or nothing will be done.
        for f in (trailers.get("triaged") or {}).values():
            triaged[str(f.get("verdict") or "unset")] += 1

    def in_window(reported: str | None) -> bool:
        return bool(reported) and reported != "unknown" and (start is None or reported >= start)

    reported: dict[str, str] = {}
    for b in open_bugs:
        if b["id"] and in_window(b["reported"]):
            reported.setdefault(b["id"], b["severity"] or "unset")
    for f in fixed + retired:
        if in_window(f.get("reported")):
            reported.setdefault(f["id"], f.get("severity") or "unset")
    days = sorted(
        d for f in fixed if (d := sdlc._days_between(f.get("reported", ""), f["date"])) is not None
    )
    history = {c["name"]: c for c in sdlc.closed_changes(home, None, trunk, read=True)}
    reviews: dict[str, dict] = {}
    # Each `Introduced by:` value's change in history, worked out once however many bugs name it.
    introducers: dict[str, str | None] = {}

    def introducer(by: str) -> str | None:
        if by not in introducers:
            introducers[by] = next((n for n in history if sdlc.names_change(n, by)), None)
        return introducers[by]

    def review(name: str) -> dict:
        """What the change's ship review left, read once."""
        if name not in reviews:
            rec = history.get(name)
            reviews[name] = (
                _review_at(home, name, rec["sha"], rec.get("findings"))
                if rec
                else {"state": "unknown", "counts": None, "findings": [], "problems": []}
            )
        return reviews[name]

    escapes: dict[str, dict] = {}
    unattributed = 0
    opened = [
        {"id": b["id"], "title": b["title"], "severity": b["severity"] or None,
         "paths": b["paths"] or None, "introduced_by": b["introduced_by"],
         "reported": b["reported"]}
        for b in open_bugs
    ]  # fmt: skip
    for source in [*fixed, *opened]:
        if not in_window(source.get("reported")):
            continue
        by = source.get("introduced_by")
        if not by or by == "unknown":
            unattributed += 1
            continue
        name = introducer(by) or by
        row = escapes.setdefault(
            name,
            {"bugs": 0, "tier": (history.get(name) or {}).get("tier"),
             "way": _way(history[name]) if name in history else "unknown", "escaped": []},
        )  # fmt: skip
        row["bugs"] += 1
        row["escaped"].append(
            {"id": source.get("id"), "title": source.get("title"),
             "severity": source.get("severity"), "paths": _bug_paths(source.get("paths"))}
        )  # fmt: skip
    for name, row in escapes.items():
        known = [p for b in row["escaped"] for p in b["paths"] or []]
        paths = known if any(b["paths"] is not None for b in row["escaped"]) else None
        seen = review(name)
        marked = [{**f, "on_paths": _on_paths(f["evidence"], paths)} for f in seen["findings"]]
        row["review"] = {**seen, "findings": marked}

    # The escape rate, this window's against the one before: bugs reported in a window and tied
    # to a change, over the changes closed in it, whenever they're fixed. Retired ones never.
    ever_fixed = [
        f
        for rec in history.values()
        for f in ((rec.get("metrics") or {}).get("fixes") or {}).values()
    ]
    attributed = [
        (str(b["reported"]), str(b["introduced_by"]))
        for b in [*opened, *ever_fixed]
        if b.get("introduced_by") not in (None, "", "unknown")
        and str(b.get("reported") or "unknown") != "unknown"
    ]

    # Each attributed bug's introducer's way, from the names worked out above, before any rate.
    way_of = {by: _way(history[n]) if (n := introducer(by)) else "unknown" for _, by in attributed}

    def window_rate(first: str | None, last: str | None, closed: int, way: str | None = None):
        n = sum(
            (first is None or r >= first)
            and (last is None or r < last)
            and (way is None or way_of[by] == way)
            for r, by in attributed
        )
        return {"escapes": n, "changes": closed, "rate": round(n / closed, 2) if closed else None}

    now = window_rate(start, None, len(changes))
    # The same rate split by the introducing change's way, over that way's changes in the window.
    now["by_way"] = {
        way: window_rate(start, None, sum(_way(c) == way for c in changes), way) for way in WAYS
    }
    bounds = sdlc.retrospectives(home, trunk)
    before = None
    if len(bounds) >= 2:
        newer, older = bounds[0], bounds[1]
        closed = len(sdlc.closed_changes(home, older["sha"], newer["sha"], read=False))
        before = window_rate(older["date"], newer["date"], closed)
    trend = "unknown"
    if before and min(now["changes"], before["changes"]) >= RATE_MIN_CHANGES:
        a, b = now["rate"], before["rate"]
        trend = "up" if a > b else "down" if a < b else "flat"

    # The window's Important findings, for a class that recurs across changes, each with who
    # raised it, and the findings by who raised them (`_review_sources()`).
    important, important_unknown = [], 0
    for rec in changes:
        seen = review(rec["name"])
        if seen["state"] != "file":
            important_unknown += 1
            continue
        if seen["problems"]:  # what parsed is listed, but the count isn't known
            important_unknown += 1
        important += [
            {"change": rec["name"], **{k: f[k] for k in ("id", "pass", "title", "class",
                                                         "disposition", "by")}}
            for f in seen["findings"]
            if f["rank"] == "important"
        ]  # fmt: skip
    sources, review_unknown = _review_sources(changes, review)
    catches = _landing_catches(changes, review)

    def by_severity(rows: list[dict] | list[str]) -> dict[str, int]:
        counts = Counter(r if isinstance(r, str) else r.get("severity") or "unset" for r in rows)
        order = [w for w in words if counts[w]] + sorted(k for k in counts if k not in words)
        return {k: counts[k] for k in order}

    return {
        "reported": by_severity(list(reported.values())),
        "fixed": by_severity(fixed),
        "retired": dict(Counter(r.get("reason") or "unset" for r in retired)),
        "triaged": dict(triaged),
        "days_to_fix": {
            "median": days[len(days) // 2] if days else None,
            "max": days[-1] if days else None,
        },
        "open": sorted(
            (
                {
                    "id": b["id"],
                    "title": b["title"],
                    "severity": b["severity"],
                    "age_days": sdlc._age_days({"created": b["reported"]}, today),
                }
                for b in open_bugs
            ),
            key=lambda b: -(b["age_days"] or 0),
        ),
        "escapes": [{"change": n, **row} for n, row in sorted(escapes.items())],
        "unattributed": unattributed,
        "rate": {"window": now, "previous": before, "trend": trend},
        "important": important,
        "important_unknown": important_unknown,
        "review_sources": sources,
        "review_unknown": review_unknown,
        "landing_catches": catches,
    }


# Who a finding's `By:` says raised it, as retro counts them: ship's own passes (no `By:`), its
# fresh-context reviewer, then each factory role, so the two ways of building compare from one
# record and an agent's finding is never counted as ship's.
REVIEW_KINDS = ("important", "nit", "preexisting", "wrong")


def _review_sources(changes: list[dict], review) -> tuple[dict[str, dict], int]:
    """Per source (`ship`, `fresh`, ship's own passes, then each factory role, in that order, only
    those that counted any), the window's findings by rank, the ones answered `wrong`, and the
    changes the source reviewed: one whose findings.md holds a finding of its, and for ship any
    change whose commit carries `Sdlc-Findings` too. A change whose findings.md wasn't read is
    counted in `unknown`, never as a review that found nothing."""
    order = ("ship", "fresh", *sdlc.SHIP_PASSES, *sdlc.AGENT_ROLES)
    rows: dict[str, dict] = {}
    unknown = 0
    for rec in changes:
        seen = review(rec["name"])
        if seen["state"] != "file":
            unknown += 1
            continue
        found = {f.get("by") or "ship" for f in seen["findings"]}
        if rec.get("findings") is not None:
            found.add("ship")
        for source in found:
            row = rows.setdefault(source, {"changes": 0, **dict.fromkeys(REVIEW_KINDS, 0)})
            row["changes"] += 1
        for f in seen["findings"]:
            row = rows[f.get("by") or "ship"]
            row[f["rank"]] += 1
            row["wrong"] += f["disposition"] == "wrong"
    ranked = [s for s in order if s in rows] + sorted(set(rows) - set(order))
    return {s: rows[s] for s in ranked}, unknown


# A finding's `Class:` when a landing round raised it (`factory.py`'s `finding_section()`).
LANDING_CLASS_RE = re.compile(r"\blanding round \d+$")


def _landing_catches(changes: list[dict], review) -> dict[str, int]:
    """How often a landing caught what a factory run's build rounds passed: `reviewed`, the
    window's changes whose findings.md holds any finding `By:` a factory role; `caught`, those of
    them holding an `important` one whose `Class:` names a landing round, `fixed` or `recorded`,
    each change once. A factory run that left no findings isn't counted, so the rate can only
    read high, never hide a catch."""
    reviewed = caught = 0
    for rec in changes:
        found = review(rec["name"])["findings"]
        if not any(f.get("by") in sdlc.AGENT_ROLES for f in found):
            continue
        reviewed += 1
        caught += any(
            f["rank"] == "important"
            and LANDING_CLASS_RE.search(f.get("class") or "")
            and f["disposition"] in ("fixed", "recorded")
            for f in found
        )
    return {"caught": caught, "reviewed": reviewed}


def _bug_paths(raw: object) -> list[str] | None:
    """A bug's paths, from the register (a list) or an `Sdlc-Fixes` line's `paths=` (text, or
    `unknown`); None when nobody recorded them, as on a line written before the key."""
    if isinstance(raw, list):
        return raw or None
    if not isinstance(raw, str) or raw in ("", "unknown"):
        return None
    return [p for p in raw.split(",") if p]


def _on_paths(evidence: str, paths: list[str] | None) -> bool | None:
    """Whether a finding's `Evidence:` path is one of an escaped bug's paths, under one, or holds
    one; None when the bug's paths are unknown."""
    if paths is None:
        return None
    where = (evidence.split() or [""])[0].split(":", 1)[0].strip("`").rstrip("/")
    for p in paths:
        p = p.strip("`").rstrip("/")
        if where and p and (where == p or where.startswith(p + "/") or p.startswith(where + "/")):
            return True
    return False


def _review_at(home: Path, name: str, sha: str, counts: dict | None) -> dict:
    """What a closed change's ship review left, from its own commit: its findings.md (`file`), only
    the `Sdlc-Findings` counts (`trailer`), or neither (`unknown`, never a clean review)."""
    text = sdlc._git(home, "show", f"{sha}:{sdlc.work_rel(home)}/{name}/{sdlc.FINDINGS}")
    entries, problems = sdlc._findings_from_text(text) if text else ([], [])
    keys = ("id", "rank", "pass", "title", "class", "disposition", "by", "evidence")
    return {
        "state": "file" if text else "trailer" if counts else "unknown",
        "counts": counts,
        "findings": [{k: e[k] for k in keys} for e in entries],
        # A section that no longer parses is said, never quietly one finding fewer.
        "problems": problems,
    }


# ---------------------------------------------------------------- the hosts (208)

# The person's list of host repos to read, in the main checkout, gitignored like `terms.local`.
HOSTS_FILE = ".sdlc/hosts.local"
OWN_ONLY_WHY = "read only in the plugin's own repo"
NO_LIST_WHY = "no host list"
# The one line a report outside the plugin's own repo gets for `{{hosts}}`.
HOSTS_ELSEWHERE = "Other repos are read only in the plugin's own repo."
HOST_NOTE = (
    "The host repos on one machine: a sample of one person's, never pooled with this repo's "
    "figures."
)
# Why a listed host couldn't be read, each a fixed word (R5).
UNREADABLE = ("missing", "not-a-repo", "no-base", "failed")
# What a host holds that no figure here reads, and what would measure it.
HOSTS_UNMEASURED = [
    {
        "signal": "friction in a host's sessions outside a change (refusals, prompts, errors)",
        "needs": "a count read from those sessions' transcripts, which this retro never reads",
    },
]
TIERS = ("0", "1", "2")
# The `Sdlc-Totals` and `Sdlc-Stage` fields a host's records keep: numbers alone.
HOST_NUMBERS = (*COMPARED, "target", "allowance", "gate", "extra", "harness", "command")


def host_list(text: str) -> tuple[list[Path], list[Path]]:
    """The listed host paths and the `!`-excluded ones in a host list's `text` (R3), each `~`
    expanded and resolved, in order: one path a line, blank and `#` lines ignored. Pure but for
    resolving."""
    paths: list[Path] = []
    excluded: list[Path] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        into = excluded if line.startswith("!") else paths
        into.append(Path(line.removeprefix("!").strip()).expanduser().resolve())
    return paths, excluded


def _git_dir(path: Path) -> bool:
    return sdlc._git(path, "rev-parse", "--git-dir") is not None


def read_host(path: Path) -> dict | str:
    """One host's records, or the word for why it can't be read (R4, R5): its closed and dropped
    changes on its base branch, its `setup.json` version, the config keys it sets and the files
    under `.sdlc/templates/`, all at the base branch. Git reads alone (`log`, `show`, `rev-parse`,
    `symbolic-ref`): no host command, hook, fetch or write. Any failure while reading is
    `failed`, never raised."""
    if not path.is_dir():
        return "missing"
    try:
        if not _git_dir(path):
            return "not-a-repo"
        checkout = sdlc.main_root(path)
        trunk = sdlc.load_config(checkout)[0]["git"]["base"]
        if not trunk or sdlc._git(checkout, "rev-parse", "--verify", "-q", trunk) is None:
            return "no-base"
        try:
            setup = json.loads(
                sdlc._git(checkout, "show", f"{trunk}:{sdlc.HOST_DIR}/setup.json") or ""
            )
        except ValueError:
            setup = {}
        listing = sdlc._git(checkout, "show", f"{trunk}:{sdlc.HOST_DIR}/templates/") or ""
        return {
            "checkout": checkout,
            "closed": sdlc.closed_changes(checkout, None, trunk),
            "dropped": sdlc.dropped_changes(checkout, None, trunk),
            "version": setup.get("version") if isinstance(setup, dict) else None,
            "keys": _keys_set(checkout, trunk) or set(),
            # `git show <tree>` prints `tree <ref>`, a blank line, then one name a line.
            "templates": {n for n in listing.splitlines()[2:] if n and not n.endswith("/")},
        }
    except Exception:
        return "failed"


def _vocabulary(home: Path) -> dict[str, set[str]]:
    """The fixed words a host figure may hold (R7), by kind: the plugin's own names, from the code
    as it is now, and the words this section uses."""
    items = _inventory(home)
    names = {
        kind: {i["name"] for i in items if i["kind"] == kind}
        for kind in ("skill", "command", "key")
    }
    names["template"] = {p.name for p in sdlc.TEMPLATE_DIR.glob("*.md")}
    names["stage"] = set(sdlc.metrics.STAGES)
    names["reached"] = set(sdlc.REACHED)
    names["words"] = {
        *TIERS, "unknown", *WAYS, *UNREADABLE, "read", "unmeasured", OWN_ONLY_WHY, NO_LIST_WHY,
        HOST_NOTE, *(u[k] for u in HOSTS_UNMEASURED for k in ("signal", "needs")),
    }  # fmt: skip
    return names


def _numbers(fields: object) -> dict:
    """A trailer's fields kept to the numbers `HOST_NUMBERS` names."""
    if not isinstance(fields, dict):
        return {}
    return {
        k: v for k, v in fields.items()
        if k in HOST_NUMBERS and isinstance(v, int | float) and not isinstance(v, bool)
    }  # fmt: skip


def _host_safe(rec: dict, vocab: dict[str, set[str]]) -> dict:
    """One host change reduced to the vocabulary before anything sums it (R7): its tier, way,
    when it closed or stopped, its escape counts, and its numbers. Names, titles, prompts' and
    roles' names, `Sdlc-Origin`, `Sdlc-Base`, reasons and problems never pass."""
    tier = str(rec.get("tier"))
    m = rec.get("metrics") or None
    safe: dict = {
        "tier": tier if tier in TIERS else "unknown",
        "close_at": rec.get("close_at"),
        "drop_at": rec.get("drop_at"),
        "dropped_at": (rec.get("dropped_at") if rec.get("dropped_at") in vocab["reached"]
                       else "unknown"),
        "reworks": len(rec.get("reworks") or []),
        "metrics": None,
    }  # fmt: skip
    if m:
        coverage = str(m.get("coverage") or "")
        safe["metrics"] = {
            "mode": m.get("mode") if m.get("mode") in ("factory", "manual") else None,
            "totals": _numbers(m.get("totals")),
            "stages": {
                s: _numbers(f) for s, f in (m.get("stages") or {}).items() if s in vocab["stage"]
            },
            "roles": {},
            "coverage": "none: unmeasured" if coverage.startswith("none:") else None,
            "fixes": len(m.get("fixes") or {}),
            "skills": {
                n: {"runs": f.get("runs")} for n, f in (m.get("skills") or {}).items()
                if n in vocab["skill"] and isinstance(f, dict)
            },
            "tools": {
                n: {"calls": f.get("calls")} for n, f in (m.get("tools") or {}).items()
                if (hit := TOOL_CALL_RE.match(n)) and f"{hit[1]}:{hit[2]}" in vocab["command"]
                and isinstance(f, dict)
            },
        }  # fmt: skip
        if not safe["metrics"]["totals"]:
            safe["metrics"]["totals"] = None
    return safe


def _scrub(value: object, words: set[str]) -> tuple[object, int]:
    """`value` with every string leaf outside `words` dropped, and how many were: the last guard
    under R7, after the filter that should leave none (`_host_safe()`). Pure."""
    if isinstance(value, dict):
        out, n = {}, 0
        for k, v in value.items():
            if isinstance(v, str) and v not in words:
                n += 1
                continue
            out[k], m = _scrub(v, words)
            n += m
        return out, n
    if isinstance(value, list):
        kept, n = [], 0
        for v in value:
            if isinstance(v, str) and v not in words:
                n += 1
                continue
            got, m = _scrub(v, words)
            kept.append(got)
            n += m
        return kept, n
    return value, 0


def _pool(closed: list[dict], dropped: list[dict], read: int) -> dict:
    """The counts over safe records (`_host_safe()`'s): every figure None when no host was read,
    since `n` is 0; honest zeros when hosts were read and hold none."""
    keys = ("closed", "dropped", "by_way", "tiers", "dropped_at", "escapes", "prompts", "metrics",
            "drop_share")  # fmt: skip
    if not read:
        return dict.fromkeys(keys)
    summary = metrics_summary(closed)
    groups = {
        k: {g: v[g] for g in ("changes", "median", "target", "stages")}
        for k, v in summary["groups"].items()
    }
    prompts = [((c["metrics"] or {}).get("totals") or {}).get("prompts") for c in closed]
    n = len(closed) + len(dropped)
    return {
        "closed": len(closed),
        "dropped": len(dropped),
        "by_way": {w: sum(1 for c in closed if _way(c) == w) for w in WAYS},
        "tiers": dict(sorted(Counter(c["tier"] for c in closed).items())),
        "dropped_at": dict(sorted(Counter(d["dropped_at"] for d in dropped).items())),
        "escapes": {
            "fixes": sum((c["metrics"] or {}).get("fixes") or 0 for c in closed),
            "reworks": sum(c["reworks"] for c in closed),
        },
        "prompts": sum(p for p in prompts if isinstance(p, int)),
        "metrics": {
            "captured": summary["captured"],
            "uncaptured": summary["uncaptured"],
            "coverage": summary["coverage"],
            "groups": groups,
        },  # fmt: skip
        "drop_share": _share(len(dropped), n),
    }


def _by_way_medians(closed: list[dict]) -> dict:
    """Per way, how many changes carry their totals, and their median stops and elapsed."""
    out = {}
    for w in WAYS:
        totals = [c["metrics"]["totals"] for c in closed if _way(c) == w and c["metrics"]
                  and c["metrics"]["totals"]]  # fmt: skip
        out[w] = {
            "n": len(totals),
            **{k: _median([t.get(k) for t in totals if isinstance(t.get(k), int | float)])
               for k in ("stops", "elapsed")},
        }  # fmt: skip
    return out


def _host_surface(hosts: list[dict]) -> dict:
    """The plugin's skills by the hosts running them and their runs, its commands by calls, its
    config keys and templates by the hosts that set or override them, from safe records alone."""
    skills: dict[str, dict] = {}
    commands: Counter = Counter()
    keys: Counter = Counter()
    templates: Counter = Counter()
    for h in hosts:
        ran: set[str] = set()
        for c in h["closed"]:
            m = c["metrics"] or {}
            for name, f in m.get("skills", {}).items():
                row = skills.setdefault(name, {"hosts": 0, "runs": 0})
                row["runs"] += f["runs"] if isinstance(f["runs"], int) else 0
                ran.add(name)
            for name, f in m.get("tools", {}).items():
                hit = TOOL_CALL_RE.match(name)
                commands[f"{hit[1]}:{hit[2]}"] += f["calls"] if isinstance(f["calls"], int) else 0
        for name in ran:
            skills[name]["hosts"] += 1
        keys.update(h["keys"])
        templates.update(h["templates"])
    return {
        "skills": dict(sorted(skills.items())),
        "commands": dict(sorted(commands.items())),
        "keys": dict(sorted(keys.items())),
        "templates": dict(sorted(templates.items())),
    }


def _when(text: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(text) if text else None
    except ValueError:
        return None


def _own_path(path: Path, main: Path) -> bool:
    """Whether `path` is this repo's main checkout or under its worktrees."""
    p, m = path.resolve().as_posix(), main.resolve().as_posix()
    return p == m or p.startswith(f"{m}/.claude/worktrees/")


def _discover(home: Path, known: set[str]) -> tuple[list[str] | None, str]:
    """The `sdlc` installs at project or local scope `claude plugin list` shows that are neither
    this repo, nor one of its worktrees, nor in `known` (the listed and excluded paths, and the
    listed hosts' main checkouts, as posix): each path once, and `read`; or (None, `unmeasured`)
    when the list couldn't be read, its reason never kept (it can hold a path) (R9)."""
    installs, why = sdlc.plugin_installs(home)
    if why:
        return None, "unmeasured"
    found = {
        i["project"] for i in installs
        if i["plugin"] == "sdlc" and i["scope"] in ("project", "local") and i["project"]
    }  # fmt: skip
    return sorted(p for p in found if p not in known and not _own_path(Path(p), home)), "read"


def _read_hosts(home: Path) -> dict | None:
    """The host list read and each host's state, for `hosts_figures()` and `cmd_hosts()`; None
    when there is no list. Each row is `(path, state, records)`, `state` one of `read`, `own`,
    `repeated` or an `UNREADABLE` word."""
    path = home / HOSTS_FILE
    if not path.is_file():
        return None
    paths, excluded = host_list(path.read_text(encoding="utf-8"))
    rows: list[tuple[Path, str, dict | None]] = []
    mains: set[str] = set()
    for p in paths:
        if _own_path(p, home):
            rows.append((p, "own", None))
            continue
        got = read_host(p)
        if isinstance(got, str):
            rows.append((p, got, None))
            continue
        checkout = got["checkout"].resolve().as_posix()
        if _own_path(got["checkout"], home):
            rows.append((p, "own", None))
        elif checkout in mains:
            rows.append((p, "repeated", None))
        else:
            mains.add(checkout)
            rows.append((p, "read", got))
    known = {p.as_posix() for p in (*paths, *excluded)} | mains
    unlisted, discovery = _discover(home, known)
    return {"rows": rows, "excluded": excluded, "unlisted": unlisted, "discovery": discovery}


def hosts_figures(home: Path, since: dict | None) -> dict:
    """The `hosts` block (R6): what the listed host repos' records add up to, as counts and fixed
    words alone, apart from this repo's figures. `unmeasured` outside the plugin's own repo and
    with no list, having run nothing. `window` is what closed or stopped after this repo's last
    retrospective (`since`), by its commit time. Read-only: git reads in each host."""
    if not sdlc._own_repo(home):
        return {"state": "unmeasured", "why": OWN_ONLY_WHY}
    listed = _read_hosts(home)
    if listed is None:
        return {"state": "unmeasured", "why": NO_LIST_WHY}
    vocab = _vocabulary(home)
    states = Counter(state for _, state, _ in listed["rows"])
    hosts = []
    for _, state, got in listed["rows"]:
        if state == "read":
            hosts.append({
                "closed": [_host_safe(c, vocab) for c in got["closed"]],
                "dropped": [_host_safe(d, vocab) for d in got["dropped"]],
                "version": (got["version"] if sdlc.SEMVER_RE.match(str(got["version"] or ""))
                            else "unknown"),
                "keys": got["keys"] & vocab["key"],
                "templates": got["templates"] & vocab["template"],
            })  # fmt: skip
    edge = _when(sdlc._git(home, "show", "-s", "--format=%cI", since["sha"])) if since else None

    def after(at: str | None) -> bool:
        when = _when(at)
        return edge is None or (when is not None and when > edge)

    closed = [c for h in hosts for c in h["closed"]]
    dropped = [d for h in hosts for d in h["dropped"]]
    window = _pool([c for c in closed if after(c["close_at"])],
                   [d for d in dropped if after(d["drop_at"])], len(hosts))  # fmt: skip
    busiest = max(hosts, key=lambda h: len(h["closed"]), default=None)
    current = sdlc.plugin_version() or ""

    def behind(v: str) -> bool:
        return bool(sdlc.SEMVER_RE.match(v) and sdlc.SEMVER_RE.match(current)
                    and sdlc._semver(v)[:2] < sdlc._semver(current)[:2])  # fmt: skip

    figures = {
        "state": "read",
        "read": {
            "listed": len(listed["rows"]),
            "read": len(hosts),
            "own": states["own"],
            "repeated": states["repeated"],
            "excluded": len(listed["excluded"]),
            "unreadable": {w: states[w] for w in UNREADABLE if states[w]},
            "unlisted": None if listed["unlisted"] is None else len(listed["unlisted"]),
            "discovery": listed["discovery"],
            "note": HOST_NOTE,
            "unmeasured": HOSTS_UNMEASURED,
            "dropped_names": 0,
        },
        "window": window,
        "all": _pool(closed, dropped, len(hosts)),
        "busiest": None
        if busiest is None
        else {
            "closed": len(busiest["closed"]),
            "by_way": _by_way_medians(busiest["closed"]),
        },  # fmt: skip
        "versions": {
            "hosts": dict(sorted(Counter(h["version"] for h in hosts).items())),
            "behind": sum(1 for h in hosts if behind(h["version"])),
        },
        "surface": _host_surface(hosts),
    }
    words = set().union(*vocab.values())
    figures, dropped_names = _scrub(figures, words)
    figures["read"]["dropped_names"] = dropped_names
    return figures


def _hosts_text(hosts: dict | None) -> str:
    """`{{hosts}}` (R11): in the plugin's own repo, how many hosts were read of how many listed,
    the unreadable and the unlisted, the note, and the tables; outside it, one line."""
    if not hosts or hosts.get("why") == OWN_ONLY_WHY:
        return HOSTS_ELSEWHERE
    if hosts["state"] != "read":
        return f"Not measured: {hosts['why']} ({HOSTS_FILE})."
    r = hosts["read"]
    unread = sum(r["unreadable"].values())
    unlisted = "not known" if r["unlisted"] is None else str(r["unlisted"])
    parts = [
        f"{r['read']} host repos read of {r['listed']} listed; {unread} couldn't be read; "
        f"{unlisted} installed repos not in the host list. {HOST_NOTE}"
    ]
    if not r["read"]:
        return parts[0]
    w, a = hosts["window"], hosts["all"]
    parts.append(_table(
        ["Way", "Closed in the window", "Closed, all time"],
        [[WAY_NAMES[k], w["by_way"][k], a["by_way"][k]] for k in WAYS],
    ) + f"\n\nDropped: {w['dropped']} in the window, {a['dropped']} all time.")  # fmt: skip
    rows = [
        [k, g["changes"], g["median"]["stops"], _hm(g["median"]["elapsed"])]
        for k, g in a["metrics"]["groups"].items()
    ]
    if rows:
        parts.append("All time, by tier and way:\n\n" + _table(
            ["Tier and way", "Changes", "Median stops", "Median elapsed"], rows))  # fmt: skip
    parts.append(f"Factory-built changes, all time: {a['by_way']['factory']}.")
    v = hosts["versions"]
    parts.append(_table(["Version", "Hosts"], [[k, n] for k, n in v["hosts"].items()])
                 + f"\n\n{v['behind']} behind this plugin's minor version.")  # fmt: skip
    return "\n\n".join(parts)


def cmd_hosts(root: Path) -> int:
    """`sdlc.py hosts` (R10): each listed host's path and state, and each installed repo the list
    doesn't name, with the two lines to append, `<path>` to read it or `!<path>` to exclude it for
    good. Paths go to the terminal alone, never into a figure or a report. Writes nothing."""
    home = sdlc.main_root(root)
    if not sdlc._own_repo(home):
        print(f"Hosts are {OWN_ONLY_WHY}; nothing is read here.")
        return 0
    listed = _read_hosts(home)
    if listed is None:
        print(f"No host list: write one path a line to {(home / HOSTS_FILE).as_posix()} (it may "
              "start empty) and rerun to see the installed repos it doesn't name.")  # fmt: skip
        return 0
    print(f"Host list: {(home / HOSTS_FILE).as_posix()}")
    for path, state, _ in listed["rows"]:
        print(f"{state}: {path.as_posix()}")
    for path in listed["excluded"]:
        print(f"excluded: {path.as_posix()}")
    if listed["unlisted"] is None:
        print("unlisted: not known (claude plugin list couldn't be read)")
    for path in listed["unlisted"] or []:
        print(f"unlisted: {path}\n  to read it, append:\n    {path}\n"
              f"  to exclude it for good, append:\n    !{path}")  # fmt: skip
    return 0


# ---------------------------------------------------------------- the insights (189)

# The pillars the synthesis questions are asked on, in the guide's order (`guide/insights.md`).
INSIGHT_PILLARS = ("Value", "Speed", "Quality", "Autonomy", "Cost", "Simplicity", "Tradeoffs")
# The one answer shape, fixed here, never by a guide a host could reword: `agents/insight.md`
# returns it, the skill writes it to the draft, `insight_answers()` reads it back.
INSIGHT_FIELDS = ("Headline", "Evidence", "Recommendation", "Disposition")
# A Disposition's kinds: `seed <entry id>`, `intent: <title>`, `dropped: <reason>`, `none: <why>`.
INSIGHT_KINDS = ("seed", "intent", "dropped", "none")
# The paths in `retro()`'s output each pillar's question is given, and nothing else (189 R3): every
# bundle also gets its pillar's scorecard rows (Tradeoffs all of them), `process.window` and
# `process.underneath`. None names `product.evidence`, `architecture.host` or `tests`: a host
# command's output never reaches an agent (R4). `surface` is the plugin's own repo's alone. Every
# bundle also gets `hosts.state`, `hosts.why` and `hosts.read` (`INSIGHT_EVERY`), and its pillar's
# slice of the other repos' counts (208 R13).
INSIGHT_DATA: dict[str, tuple[str, ...]] = {
    "Value": (
        "work_mix", "time_to_users", "follow_through", "direction.milestones", "hosts.all",
        "hosts.versions",
    ),
    "Speed": (
        "process.cycle", "process.lead", "process.throughput", "process.time", "process.wip",
        "process.capacity", "by_way", "pipeline.gates", "pipeline.landing",
        "hosts.window.by_way", "hosts.window.metrics", "hosts.busiest",
    ),
    "Quality": (
        "process.escapes", "process.rework", "process.review_sources", "rework_questions", "bugs",
        "pipeline.red_gate", "pipeline.depth", "pipeline.unreviewed", "architecture", "nits",
        "hosts.window.escapes", "hosts.window.dropped_at",
    ),
    "Autonomy": (
        "autonomy", "process.response", "metrics.extra", "metrics.prompts", "hosts.window.prompts",
    ),
    "Cost": (
        "cost", "spend", "metrics.groups", "metrics.captured", "metrics.uncaptured",
        "metrics.coverage", "metrics.missing_because", "hosts.window.metrics",
    ),
    "Simplicity": ("simplicity.workarounds", "surface", "prose", "hosts.surface"),
    "Tradeoffs": ("work_mix", "time_to_users", "follow_through", "hosts.all"),
}  # fmt: skip
# The paths every bundle carries, whatever its pillar.
INSIGHT_EVERY = ("process.window", "process.underneath", "hosts.state", "hosts.why", "hosts.read")
# Under a path a bundle names, what it never carries: the host's indicator rows.
INSIGHT_LEFT_OUT = ("architecture.host",)
# The host commands `retro --insights` empties before it counts, so none of them runs (R4).
HOST_COMMANDS = ("evidence", "indicators", "test_times")


def _question_blocks(text: str) -> list[tuple[str | None, int, str, str]]:
    """A question doc's heading blocks, in order, from `doc_units()`: each as `(the ## title above
    it, None for a ## itself; its level; its title; its text)`, a `- **lead**` bullet's block
    folded into the heading block above it."""
    out: list[list] = []
    top: str | None = None
    for key, block in sdlc.doc_units(text):
        if key == "#":
            continue
        first, _, rest = block.partition("\n")
        m = sdlc.HEADING_RE.match(first)
        if not m:  # a bullet's block, which belongs to the heading above it
            if out:
                out[-1][3] += "\n" + block
            continue
        level, title = len(m.group(1)), first[m.end() :].strip()
        if level == 2:
            top = title
        out.append([None if level == 2 else top, level, title, rest])
    return [(a, b, c, d.strip()) for a, b, c, d in out]


def insight_questions(home: Path, cfg: dict) -> tuple[list[dict], list[str]]:
    """The synthesis questions this retrospective asks (189 R2), each with its `title`, `pillar`
    and `question`, in the guide's pillar order, and what is wrong with the repo's doc. The guide's
    `##` per pillar comes first; then the repo's `[docs] insights`, block by block: a pillar's
    `##` holding text replaces its question, one without only places what follows, a `###` under a
    pillar's `##` adds a question on that pillar's figures, and any other `##` (or a `###` under
    one) adds one on the tradeoffs'. A second question with a title already asked is a problem,
    and dropped."""
    guide = (sdlc.GUIDE_DIR / sdlc.GUIDES["insights"]).read_text(encoding="utf-8")
    asked = {p: [{"title": p, "pillar": p, "question": ""}] for p in INSIGHT_PILLARS}
    for _, level, title, text in _question_blocks(guide):
        if level == 2 and title in asked:
            asked[title][0]["question"] = text
    rel = cfg["docs"].get("insights")
    path = home / rel if rel else None
    problems: list[str] = []
    seen = set(INSIGHT_PILLARS)
    if path and path.is_file():
        for top, level, title, text in _question_blocks(path.read_text(encoding="utf-8")):
            if level == 2 and title in INSIGHT_PILLARS:
                if text:
                    asked[title][0]["question"] = text
                continue
            if not text:
                continue  # a heading alone only places what follows
            if title in seen:
                problems.append(f"{rel}: the question {title!r} is asked twice; the second is "
                                "dropped")  # fmt: skip
                continue
            seen.add(title)
            pillar = top if level > 2 and top in INSIGHT_PILLARS else "Tradeoffs"
            asked[pillar].append({"title": title, "pillar": pillar, "question": text})
    return [q for p in INSIGHT_PILLARS for q in asked[p]], problems


def _pick(out: dict, path: str) -> tuple[bool, object]:
    """`out`'s value at a dotted `path`, and whether it is there."""
    node: object = out
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def _put(into: dict, path: str, value: object) -> None:
    """Set `into`'s value at a dotted `path`, making the dicts above it."""
    *parents, last = path.split(".")
    for part in parents:
        into = into.setdefault(part, {})
    into[last] = value


def insight_bundles(out: dict, questions: list[dict], own: bool) -> list[dict]:
    """Each question with its `data`: the paths of `retro()`'s (lean) output `INSIGHT_DATA` names
    for its pillar, less `INSIGHT_LEFT_OUT`, its pillar's scorecard rows (every row for
    Tradeoffs), and `INSIGHT_EVERY`'s paths. `surface` only when `own`, the
    plugin's own repo. Pure."""
    rows = (out.get("scorecard") or {}).get("rows") or []
    bundles = []
    for q in questions:
        data: dict = {}
        for path in (*INSIGHT_EVERY, *INSIGHT_DATA[q["pillar"]]):
            found, value = _pick(out, path)
            if not found or (path == "surface" and not own):
                continue
            # A copy without what is left out beneath it: `architecture` without its `host`.
            drop = {
                x.removeprefix(path + ".") for x in INSIGHT_LEFT_OUT if x.startswith(path + ".")
            }
            if drop and isinstance(value, dict):
                value = {k: v for k, v in value.items() if k not in drop}
            _put(data, path, value)
        mine = [r for r in rows if q["pillar"] == "Tradeoffs" or r["pillar"] == q["pillar"]]
        data["scorecard"] = {"rows": mine}
        bundles.append({**q, "data": data})
    return bundles


FIELD_RE = re.compile(rf"^({'|'.join(INSIGHT_FIELDS)}):[ \t]*(.*)$")
DISPOSITION_RE = re.compile(r"^(?:seed\s+(\S+)|(?:intent|dropped|none):\s*\S.*)$")


def insight_answers(
    text: str, questions: list[dict], register: set[str]
) -> tuple[list[dict], list[str]]:
    """The answers an insights draft holds (189 R6), in `questions`' order, and every problem with
    it: a title no question has, one answered twice, a question not answered, a field missing or
    empty, a Disposition of no known kind, or a `seed` naming no id in `register`. The draft is a
    `## <title>` block per question, each field a `<Field>: ` line running to the next field's.
    Pure."""
    blocks: list[tuple[str, dict[str, list[str]]]] = []
    field: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            blocks.append((line[3:].strip(), {}))
            field = None
        elif blocks and (m := FIELD_RE.match(line)):
            field = blocks[-1][1].setdefault(m.group(1), [])
            field.append(m.group(2))
        elif field is not None:
            field.append(line)
    known = {q["title"]: q for q in questions}
    got: dict[str, dict] = {}
    problems: list[str] = []
    for title, fields in blocks:
        if title not in known:
            problems.append(f"insights: {title!r} is not a question this retrospective asks")
            continue
        if title in got:
            problems.append(f"insights: {title!r} is answered twice")
            continue
        said = {f: " ".join(" ".join(fields.get(f, [])).split()) for f in INSIGHT_FIELDS}
        problems += [f"insights: {title!r} has no {f}" for f in INSIGHT_FIELDS if not said[f]]
        d = said["Disposition"]
        if d and not (m := DISPOSITION_RE.match(d)):
            problems.append(f"insights: {title!r}: Disposition {d!r} is none of seed <id>, "
                            "intent: <title>, dropped: <reason>, none: <why>")  # fmt: skip
        elif d and m.group(1) and m.group(1) not in register:
            problems.append(f"insights: {title!r}: Disposition names seed {m.group(1)}, which the "
                            "register doesn't hold")  # fmt: skip
        got[title] = {**known[title], **{f.lower(): v for f, v in said.items()}}
    problems += [f"insights: {t!r} is not answered" for t in known if t not in got]
    return [got[t] for t in known if t in got], problems


def _draft_answers(home: Path, cfg: dict, day: date) -> tuple[list[dict] | None, list[str]]:
    """The answers in `day`'s insights draft, against this retrospective's questions and the
    register as it stands; None, with no problem, when there is no draft."""
    path = home / insights_rel(day)
    if not path.is_file():
        return None, []
    questions, _ = insight_questions(home, cfg)
    register = sdlc.register_path(sdlc.work_dir(home))
    text = register.read_text(encoding="utf-8") if register.is_file() else ""
    ids = {e["id"] for e in sdlc.parse_entries(text) if e["id"]}
    return insight_answers(path.read_text(encoding="utf-8"), questions, ids)


def _lean_out(out: dict, metrics: bool) -> dict:
    """`retro()`'s output as `retro` prints it: each change's own numbers only with `metrics`."""
    out["changes"], out["dropped"] = (
        sdlc._lean(out["changes"], metrics),
        sdlc._lean(out["dropped"], metrics),
    )
    if not metrics:  # each change's own spend, as its `metrics` are: the summary stays
        out["spend"] = {k: v for k, v in out["spend"].items() if k != "changes"}
        agents = out["spend"].get("agents")
        if isinstance(agents, dict):
            out["spend"]["agents"] = {k: v for k, v in agents.items() if k != "changes"}
        out["cost"] = {k: v for k, v in out["cost"].items() if k != "changes"}
        out["pipeline"] = {k: v for k, v in out["pipeline"].items() if k != "changes"}
    return out


def retro_insights(home: Path, cfg: dict, today: date | None = None) -> dict:
    """`retro --insights` (189 R3, R4): each question `insight_questions()` gives, with its
    figures (`insight_bundles()`), and `problems`, the question doc's. The figures are `retro()`'s
    with every host command list emptied, so none runs and no output of one is in a bundle.
    Read-only."""
    quiet = {**cfg, "retro": {**cfg["retro"], **{k: [] for k in HOST_COMMANDS}}}
    out = _lean_out(retro(home, quiet, today), metrics=False)
    out = json.loads(json.dumps(out, default=str))  # what an agent is shown, as `retro` prints it
    questions, problems = insight_questions(home, cfg)
    return {
        "questions": insight_bundles(out, questions, sdlc._own_repo(home)),
        "problems": problems,
    }


def cmd_retro(
    root: Path, metrics: bool = False, report: bool = False, insights: bool = False
) -> int:
    """The retrospective's counts as JSON, each change's measured numbers only with `metrics`
    (their medians are always there), or with `report` the report `retro-commit` would write, as
    Markdown, or with `insights` each synthesis question and its figures (`retro_insights()`).
    Writes nothing. It reads nothing outside the repo but, in the plugin's own repo with a host
    list, the listed host repos' history, by git reads alone (`hosts_figures()`)."""
    home = sdlc.main_root(root)
    cfg, _, parsed = sdlc.load_config(home)
    if report:
        # A draft there is previewed as `retro-commit` would render it; nothing is written.
        answers, _ = _draft_answers(home, cfg, date.today())
        experience, _ = _draft_experience(home, date.today())
        print(retro_report(home, cfg, date.today(), answers, experience), end="")
        return 0 if parsed else 1
    if insights:
        print(json.dumps(retro_insights(home, cfg), indent=2, ensure_ascii=False))
        return 0 if parsed else 1
    out = _lean_out(retro(home, cfg), metrics)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0 if parsed else 1


# What a retrospective may change on an entry already in the register: its rank and its theme.
RERANK_KEYS = ("Priority", "Theme")


def register_drift(old: str, new: str) -> list[str]:
    """What a retrospective did to the register beyond re-ranking: each entry the committed text
    held that is gone, or changed in more than its `RERANK_KEYS` lines (its heading, tag, prose,
    or any other key line). Entries added are a retrospective's seeds, and fine."""
    after = {e["id"]: e for e in sdlc.parse_entries(new) if e["id"]}

    def kept(e: dict) -> tuple:
        rest = {k: v for k, v in e["fields"].items() if k not in RERANK_KEYS}
        return e["status"], e["title"], e["text"], rest

    problems = []
    for e in sdlc.parse_entries(old):
        if not e["id"]:
            continue
        if e["id"] not in after:
            problems.append(f"{e['id']} was removed: retire it with /sdlc:idea, not a retro")
        elif kept(after[e["id"]]) != kept(e):
            keys = " and ".join(f"{k}:" for k in RERANK_KEYS)
            problems.append(f"{e['id']} changed beyond its {keys} lines")
    return problems


def cmd_retro_commit(root: Path, today: date | None = None) -> int:
    """Record a retrospective: one commit, `Retrospective YYYY-MM-DD`, holding the direction doc,
    the register, the product doc's outcomes, and the report it writes itself, and nothing else,
    so main is never left dirty. The day's insights draft (`insights_rel()`), when there is one, is
    rendered into the report's `{{insights}}`, never committed, and removed once the commit is
    made (189 R6); the day's experience draft (`experience_rel()`) the same way, into
    `{{experience}}` (190 R5).
    Every refusal is found before anything is written, the draft's problems included."""
    home = sdlc.main_root(root)
    cfg, _, _ = sdlc.load_config(home)
    stamp = (today or date.today()).isoformat()
    allowed = {
        cfg["docs"]["direction"],
        f"{sdlc.work_rel(home)}/{sdlc.register_path(sdlc.work_dir(home)).name}",
    }
    if cfg["docs"]["product"]:
        allowed.add(cfg["docs"]["product"])
    report: dict = {
        "commit": f"{sdlc.RETRO_PREFIX}{stamp}",
        "paths": [],
        "refusals": [],
        "done": [],
    }
    refusals = report["refusals"]

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    if root.resolve() != home.resolve():
        refusals.append(f"run it from the main checkout ({home}), not a change's worktree")
    trunk = cfg["git"]["base"]
    if why := sdlc.trunk_refusal(home, trunk, cfg["git"]["base_source"]):
        refusals.append(why)
    elif sdlc._git(home, "branch", "--show-current") != trunk:
        refusals.append(f"the main checkout ({home}) isn't on {trunk}")
    # Staged, unstaged and untracked, by name: porcelain's columns don't survive `_git`'s strip.
    tracked = sdlc._git(home, "-c", "core.quotePath=false", "diff", "--name-only", "HEAD") or ""
    untracked = (
        sdlc._git(home, "-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard")
        or ""
    )
    changed = sorted({p for p in (*tracked.splitlines(), *untracked.splitlines()) if p})
    # The report is the script's to write, below, once nothing refuses; one already there was
    # written by hand, or by a retrospective today.
    day = today or date.today()
    report_at = report_rel(day)
    if (home / report_at).exists():
        refusals.append(f"{report_at} already exists: retro-commit writes the report itself")
    # The insights draft is read, never committed: it leaves the list of what the commit takes.
    draft_at, felt_at = insights_rel(day), experience_rel(day)
    changed = [p for p in changed if p not in (draft_at, felt_at)]
    stray = [p for p in changed if p not in allowed and p != report_at]
    if stray:
        refusals.append(
            f"only {' and '.join(sorted(allowed))} may be uncommitted; also changed: "
            + ", ".join(stray)
        )
    elif not changed:
        refusals.append(f"nothing to record: {' and '.join(sorted(allowed))} are unchanged")
    last = sdlc.last_retrospective(home, trunk)
    if last and last["date"] == stamp:
        refusals.append(f"{report['commit']} is already on {trunk} ({last['sha']}): one a day")
    # Follow-through: every goal, milestone or outcome the committed docs left open is still
    # there, carried or struck with its status. One already struck may go: it stayed one
    # retrospective. A product doc the retrospective didn't touch is checked all the same.
    docs = [("direction", "GM")] + ([("product", "O")] if cfg["docs"]["product"] else [])
    for key, kinds in docs:
        rel = cfg["docs"][key]
        committed = sdlc.doc_items(sdlc._git(home, "show", f"HEAD:{rel}") or "", kinds)
        path = home / rel
        new = sdlc.doc_items(path.read_text(encoding="utf-8") if path.is_file() else "", kinds)
        kept = {i["id"] for i in new["items"]}
        for item in committed["items"]:
            if item["status"] == "open" and item["id"] not in kept:
                refusals.append(
                    f"{item['id']} was open and the new {key} doc drops it: carry it, or strike "
                    "it with Done, Dropped or Revised"
                )
        refusals += [f"{key} doc: {p}" for p in new["problems"]]
    # The register: a retrospective appends seeds and re-ranks, and nothing else; an entry leaves
    # through ship, /sdlc:idea or /sdlc:bug, never through a retro.
    register = f"{sdlc.work_rel(home)}/{sdlc.register_path(sdlc.work_dir(home)).name}"
    committed = sdlc._git(home, "show", f"HEAD:{register}")
    if committed is not None:
        path = home / register
        refusals += register_drift(
            committed, path.read_text(encoding="utf-8") if path.is_file() else ""
        )
    answers, problems = _draft_answers(home, cfg, day)
    refusals += problems
    experience, problems = _draft_experience(home, day)
    refusals += problems
    if refusals:
        return emit(1)
    path = home / report_at
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        retro_report(home, cfg, day, answers, experience), encoding="utf-8", newline="\n"
    )
    changed = sorted({*changed, report_at})
    report["paths"] = changed
    for args in (["add", "--", *changed], ["commit", "-q", "-m", report["commit"], "--", *changed]):
        made = subprocess.run(
            ["git", "-C", str(home), *args], capture_output=True, encoding="utf-8"
        )
        if made.returncode != 0:
            refusals.append(f"git {args[0]} failed: {made.stderr.strip()}")
            path.unlink(missing_ok=True)
            return emit(1)
    report["done"].append("commit")
    report["sha"] = sdlc._git(home, "rev-parse", "--short", "HEAD")
    # Only once the commit holds the report: a failed git step above leaves it for a rerun.
    if answers is not None:
        (home / draft_at).unlink(missing_ok=True)
        report["done"].append("draft removed")
    if experience is not None:
        (home / felt_at).unlink(missing_ok=True)
        report["done"].append("experience draft removed")
    return emit(0)
