"""board — the dashboard of every open change, served on localhost by `sdlc.py board`.

`sdlc.py` loads this file by path, only when `board` runs, and binds `sdlc` to a live view of its
own globals, as it does `retro.py`: every reader the board shares with `status` (`change_dirs`,
`load_change`, `open_items`, …) is called as `sdlc.<name>`, so a test's stand-in reaches it.

The page (`board.html`, beside this file) polls `/state.json`, which is rebuilt from the change
folders on every request, so the board and the folders can't disagree. A change the factory ran
on (its folder holds `runs/`) adds its rounds, decisions and cost, read from the files the run
left with copies of `factory.py`'s parsing, each pinned to it by a test: the core never imports or
runs the factory. Nothing here writes: three GET routes, every other method refused, and `/file`
serves only a file inside an open change's own folder.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sdlc = None  # sdlc.py's own names, bound by sdlc.py right after it loads this file

PAGE = Path(__file__).with_name("board.html")
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
VERIFIED = "verified.md"
COSTS = Path("runs") / "costs.jsonl"


# ---------------------------------------------------------------- the state


def state(root: Path) -> dict:
    """Every open change this checkout can see, as `status` finds them, each a card's worth."""
    home = sdlc.main_root(root)
    cfg = sdlc.load_config(home)[0]
    trunk = cfg["git"]["base"]
    issues = _issue_base(home, cfg)
    now = datetime.now(UTC).timestamp()
    changes = [_entry(root, home, f, trunk, issues, now) for f in sdlc.change_dirs(root)]
    return {
        "board": MARKER, "repo": home.name, "trunk": trunk, "at": now,
        "changes": [c for c in changes if c["stage"] not in CLOSED],
    }  # fmt: skip


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
    root: Path, home: Path, folder: Path, trunk: str | None, issues: str | None, now: float
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
    }  # fmt: skip
    if entry["mode"] == "factory":
        entry.update(_factory(folder, problems))
    entry["problems"] = problems
    entry["next"] = next_action(entry)
    entry["column"] = column(entry)
    return entry


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
    decision = None
    path = folder / "decision.md"
    if path.is_file():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        m = DECISION_RE.match(lines[0]) if lines else None
        decision = m.group(1) if m else None
        if not m:
            problems.append("decision.md doesn't open with DECISION: READY or ESCALATE")
    pending, assumed = [], []
    path = folder / "decisions.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        m = LEDGER_RE.match(line)
        if m and m.group(1) == " ":
            item = {"id": m.group(2), "by": m.group(3), "text": m.group(5)}
            (pending if m.group(4) == "blocking" else assumed).append(item)
    return {
        "rounds": rounds, "built": built, "decision": decision, "pending": pending,
        "assumed": assumed, "cost": cost(folder),
    }  # fmt: skip


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
    decision and ledger: the step `status` and each skill's report name."""
    stage, tier = entry["stage"], entry["tier"]
    if entry["problems"] and stage is None:
        return "fix intent.md's frontmatter"
    if entry.get("pending"):
        return "answer its decision in the factory's supervisor"
    if entry.get("decision") and stage == "test":
        return "/sdlc:ship, or /sdlc-factory:land with the others ready"
    if entry["mode"] == "factory" and stage in ("design", "build") and entry.get("built"):
        return "the factory is building it: wait for its decision"
    if stage == "plan":
        return "/sdlc:spec" if tier == 2 else "plan mode, then build it"
    if stage == "design":
        return "plan mode, then build it"
    if stage == "build":
        return "build it, then /sdlc:ship"
    return "/sdlc:ship"


def column(entry: dict) -> str:
    """The board's column: a stop that is the person's first, then a factory change ready to ship,
    else its stage."""
    if entry["problems"] or entry.get("pending") or entry.get("decision") == "ESCALATE":
        return "needs-you"
    if entry["stage"] == "test" and entry.get("decision") == "READY":
        return "ready"
    return entry["stage"] or "needs-you"


def file_at(root: Path, change: str, rel: str) -> Path | None:
    """The file `rel` of open change `change`'s own folder, or None: a path that leaves the
    folder, by `..`, by being absolute or through a link, is never served."""
    if not change or not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        return None
    folders = {f.name: f for f in sdlc.change_dirs(root) if sdlc._stage(f) not in CLOSED}
    folder = folders.get(change)
    if folder is None:
        return None
    target = (folder / rel).resolve()
    if not target.is_relative_to(folder.resolve()) or not target.is_file():
        return None
    return target


# ---------------------------------------------------------------- the server


class _Server(ThreadingHTTPServer):
    # Windows lets a second socket take a port another one holds when this is on; elsewhere it
    # only lets a restart take a port its last run left in TIME_WAIT.
    allow_reuse_address = os.name != "nt"
    daemon_threads = True


def _handler(root: Path, port: int) -> type[BaseHTTPRequestHandler]:
    hosts = {f"{HOST}:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            url = urlparse(self.path)
            # A page elsewhere that points its own name at 127.0.0.1 reads nothing here.
            if self.headers.get("Host") not in hosts:
                return self._send(404, b"not found\n", "text/plain")
            if url.path == "/":
                return self._send(200, PAGE.read_bytes(), "text/html")
            if url.path == "/state.json":
                body = json.dumps(state(root), ensure_ascii=False).encode("utf-8")
                return self._send(200, body, "application/json")
            if url.path == "/file":
                q = parse_qs(url.query)
                found = file_at(root, q.get("change", [""])[0], q.get("path", [""])[0])
                if found is not None:
                    return self._send(200, found.read_bytes(), "text/plain")
            return self._send(404, b"not found\n", "text/plain")

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
    """The board's server on 127.0.0.1:`port`, bound but not yet serving. Raises OSError when the
    port is taken."""
    return _Server((HOST, port), _handler(root, port))


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
