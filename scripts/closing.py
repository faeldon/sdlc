"""closing — close, the push and the main lock, apart from `sdlc.py` so a review can name them.

What lives here is where a mistake costs a host its work or its history: `cmd_close()` (the merge,
the `Close` commit, the register's entries filed and retired in it, the measure step's trailers, the
cleanup, the handoff to the merged script), run as named steps (`_step_merge()` …
`_step_cleanup()`, each taking the `_Close` that holds what they share, listed by `_close_steps()`
and run under the lock by `_run_close_steps()`), `_main_lock()` and its family (`_lock_path()`,
`_lock_depth()`, `_inherit_lock()`, `LOCK_HELD_ENV`), and `_push()` with `_push_plan()`. This
repo lists the file in `[review] sensitive`, read from the base branch, so a change touching it is
reviewed at full depth with the security reviewer, while a change elsewhere in `sdlc.py` can stay
light.

The line between here and `sdlc.py` is a rule `tests/test_modules.py` holds: a function lives
here when it is one of close's, the push's or the lock's named entries, or when only code here
calls it; anything `sdlc.py` (or `retro.py`, `board.py`) also calls stays there. A constant moves
only when it is named or its whole commented block moves, so a family of pinned copies never
splits.

`sdlc.py` loads this file by path, as it loads `retro.py`, and binds `sdlc` here to a live view of
its own names right after: every name this code shares with the rest of the script (`_git`,
`load_config`, `work_rel`, `tracker` …) is read as `sdlc.<name>` when it runs, so a test's stand-in
on the loaded `sdlc` module reaches it. `sdlc.py` calls this file's names as `closing.<name>`
(`claim()` and `inbox-commit` take the lock, release and publish push, `main()` runs close), and
the tests as `sdlc.closing.<name>`. `sdlc` is unbound while this file loads, so nothing evaluated
at load (a default argument, a module-level statement) may read it.

What it keeps: `_push()` is the core's one git push, never forced, called only by `cmd_publish`,
and by `cmd_close` and `cmd_release` through `_push_plan()`; close holds `_main_lock()` from its
merge to its `Close` commit, reentrant within a thread and inherited by a handed-off close through
`LOCK_HELD_ENV`; `fcntl` and `msvcrt` are imported only inside the functions that need them.
The measure step reads a factory run's files on the change's branch through
`sdlc.factory_records` (`scripts/factory_records.py`): the git reads are here (`_branch_files()`),
the parsing is the module's.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from datetime import UTC, date, datetime, timedelta
from datetime import time as dtime
from pathlib import Path

import frontmatter

sdlc = None  # sdlc.py's own names, bound by sdlc.py right after it loads this file


def _msvcrt_lock(fd: int) -> None:
    """Wait for byte 0 of the lock file, on Windows. `LK_LOCK` gives up after ten tries, so it
    can't be the wait: retry the non-blocking form until the holder lets go. Only a held lock
    (EACCES, or EDEADLOCK, 36, the C runtime's) is retried; any other failure raises, as a
    `flock` would, rather than hang."""
    import errno
    import msvcrt
    import time

    held = {errno.EACCES, getattr(errno, "EDEADLOCK", 36)}
    os.lseek(fd, 0, os.SEEK_SET)
    while True:
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return
        except OSError as e:
            if e.errno not in held:
                raise
            time.sleep(0.05)


def _msvcrt_unlock(fd: int) -> None:
    import msvcrt

    os.lseek(fd, 0, os.SEEK_SET)
    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)


def _flock_lock(fd: int) -> None:
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_EX)


def _flock_unlock(fd: int) -> None:
    pass  # closing the descriptor releases a flock


# Each module is imported only where it exists: neither is at the top of the file.
_lock, _unlock = (_msvcrt_lock, _msvcrt_unlock) if os.name == "nt" else (_flock_lock, _flock_unlock)


def _lock_path(home: Path) -> Path:
    """The file `_main_lock()` locks: `sdlc.lock` in the git common dir, which every worktree
    shares and no tree or `git status` shows, or `.sdlc/lock` outside git. A file, since Windows
    won't open a directory to lock it."""
    common = sdlc._git(home, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common) / "sdlc.lock" if common else sdlc.main_root(home) / ".sdlc" / "lock"


# How deep each thread holds each lock file: only the outermost hold takes the OS lock, so a
# hold can nest (`_close_commit()` inside close's) and never waits on itself, while another thread
# or process still waits. A close handed off (`_handoff()`) tells its child the parent holds it,
# through `LOCK_HELD_ENV`, naming the lock file; the child takes none for that file.
_LOCK_DEPTH = threading.local()


LOCK_HELD_ENV = "SDLC_LOCK_HELD"


def _lock_depth() -> dict[str, int]:
    held = getattr(_LOCK_DEPTH, "held", None)
    if held is None:
        held = _LOCK_DEPTH.held = {}
    return held


@contextmanager
def _main_lock(home: Path) -> Iterator[None]:
    """An exclusive lock on `_lock_path()`, which every worktree shares, held for the `with`
    block: what `claim()` takes a number under, `inbox-commit` the register, and `close` its
    span from its merge to its `Close` commit. Reentrant within a thread (`_lock_depth()`): a
    nested `with` counts, and the OS lock is taken once, by the outermost. The file stays after:
    removing it would let a waiter hold a lock on a name the next caller makes anew."""
    lock = _lock_path(home)
    depth, key = _lock_depth(), str(lock)
    if depth.get(key, 0):
        depth[key] += 1
        try:
            yield
        finally:
            depth[key] -= 1
        return
    lock.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        _lock(fd)
        depth[key] = 1
        try:
            yield
        finally:
            depth[key] = 0
            _unlock(fd)
    finally:
        os.close(fd)  # and with it a flock


def _inherit_lock(home: Path, held: str | None) -> bool:
    """The hold a parent process passed down: with `held` naming this repo's lock file (the
    value of `LOCK_HELD_ENV`, popped by the caller before any other process starts), every
    `_main_lock()` of this thread nests on it and takes no OS lock, since the parent holds it and
    waits on this process, for the life of the process: a handed-off close is a process of its
    own. Anything else is no hold. True when inherited."""
    key = str(_lock_path(home))
    if held != key:
        return False
    depth = _lock_depth()
    depth[key] = max(depth.get(key, 0), 1)
    return True


def _without_entry(lines: list[str], start: int) -> list[str]:
    """`lines` without the entry whose heading is line `start`, through the line before the next
    `## ` (or the end): no blank line left trailing the one before it when it was the last."""
    end = next((n for n in range(start + 1, len(lines)) if lines[n].startswith("## ")), len(lines))
    before, after = lines[:start], lines[end:]
    if not after:
        while before and not before[-1].strip():
            before.pop()
    return before + after


def register_plan(register: str, intent: str, held: dict) -> dict:
    """What close makes of the register text `register` for a change whose intent is `intent`,
    holding `held` (`held_entries()`): every seed its `idea:` names (by id or title, as ship
    matches them), every bug its `fixes:` names and every nit a `Retire` line names, removed, then
    each held entry appended, every other line byte for byte. Returns the new `text`, the refs
    retired (`retire`), the ids filed (`file`), what was already gone (`gone`), the held entries
    the register holds word for word already (`skipped`, a rerun's), and `refusals`: a held file
    that can't be read, a title naming two entries, a held id the register holds otherwise."""
    plan: dict = {"text": register, "retire": [], "file": [], "gone": [], "skipped": [],
                  "refusals": [f"{sdlc.ENTRIES}: {p}" for p in held["problems"]]}  # fmt: skip
    lines = register.splitlines(keepends=True)
    spans = sdlc._entry_spans(lines)
    starts: list[int] = []
    for idea in sdlc.intent_ideas(intent):
        found = [n for n, line in enumerate(lines)
                 if (h := sdlc._heading_entry(line.rstrip("\n")))
                 and sdlc.ref_matches(idea, h)]  # fmt: skip
        if len(found) > 1:
            plan["refusals"].append(
                f"the register has {len(found)} entries named {sdlc.entry_ref(idea)[1]!r}: retitle "
                "one, or name the seed by its id"
            )
        elif found:
            plan["retire"].append(idea)
            starts.append(found[0])
        else:
            plan["gone"].append(idea)
    by_id = [f for f in sdlc.frontmatter_list(intent, "fixes") or [] if sdlc.ENTRY_ID_RE.match(f)]
    by_id += [i for i, _ in held["retire"]]
    for i in dict.fromkeys(by_id):
        if i in spans:
            plan["retire"].append(i)
            starts.append(spans[i][0])
        else:
            plan["gone"].append(i)
    for start in sorted(set(starts), reverse=True):
        lines = _without_entry(lines, start)
    text = "".join(lines)
    left = sdlc._entry_spans(lines)
    for i in held["ids"]:
        chunk = held["chunks"].get(i, "")
        if i in left:
            s, e = left[i]
            if "".join(lines[s:e]).rstrip("\n") + "\n" == chunk:
                plan["skipped"].append(i)
            else:
                plan["refusals"].append(
                    f"{sdlc.ENTRIES} holds {i}, which the register holds with other text: give the "
                    "held entry a new id from `next-entry`"
                )
            continue
        text = text.rstrip("\n")
        text = f"{text}\n\n{chunk}" if text else chunk
        plan["file"].append(i)
    plan["text"] = text
    return plan


def _close_times(main: Path, trunk: str) -> dict[str, datetime]:
    """When each change's `Close` commit landed on the base branch, by the change's name."""
    log = sdlc._git(main, "log", "--first-parent", "--format=%cI%x00%s", trunk) or ""
    found = {}
    for line in log.splitlines():
        when, _, subject = line.partition("\x00")
        name = (
            subject[len(sdlc.CLOSE_PREFIX) :].strip()
            if subject.startswith(sdlc.CLOSE_PREFIX)
            else ""
        )
        if sdlc.DIR_RE.match(name):
            found[name] = datetime.fromisoformat(when)
    return found


def _branch_files(main: Path, branch: str, folder: str):
    """`show` and `listing` over the change's folder on its branch, as `factory_records` takes
    them: `show(rel)` the file `<folder>/<rel>`, or None; `listing(rel)` every path under
    `<folder>/<rel>`, one a line, relative to the folder. Close's measure step is the only place
    those git reads run."""

    def show(rel: str) -> str | None:
        return sdlc._git(main, "show", f"{branch}:{folder}/{rel}")

    def listing(rel: str) -> str:
        listed = sdlc._git(main, "ls-tree", "-r", "--name-only", branch, f"{folder}/{rel}") or ""
        return "\n".join(path[len(folder) + 1 :] for path in listed.splitlines())

    return show, listing


def _factory_files(main: Path, branch: str) -> dict | None:
    """What the factory left in the change's commit, as counts (`factory_records.run_counts()`):
    None for a change built by hand."""
    show, listing = _branch_files(main, branch, f"{sdlc.work_rel(main)}/{branch}")
    return sdlc.factory_records.run_counts(show, listing)


def _change_diff(main: Path, branch: str) -> int | None:
    """Lines added to code and tests by the change, from `_change_base()` to the branch's tip.
    Files are named by `metrics.artifact`, as the edits were; the plugin's own state in `.sdlc/`
    (the counter `new` writes in the change's worktree) is nobody's code."""
    base = sdlc._change_base(main, branch)
    numstat = sdlc._git(main, "diff", "--numstat", "--no-renames", base, branch) if base else None
    if numstat is None:
        return None
    total = 0
    for row in numstat.splitlines():
        plus, _, rest = row.partition("\t")
        path = rest.partition("\t")[2]
        if path.startswith(".sdlc/"):
            continue
        if plus.isdigit() and sdlc.metrics.artifact(path, branch) in ("code", "test"):
            total += int(plus)
    return total


def _agent_sessions(main: Path, branch: str, folder: str) -> dict[str, str]:
    """The sessions the factory ran as its agents, by session id, from the change's
    `runs/<role>.sessions` on its branch (`factory_records.session_roles()`). A transcript names
    no `--agent` role, so this is how measuring tells a builder's session from the person's."""
    return sdlc.factory_records.session_roles(*_branch_files(main, branch, folder))


def _agent_models(main: Path, branch: str, folder: str) -> dict[str, str]:
    """The model each factory session ran on, by session id, from the change's `runs/costs.jsonl`
    on its branch (`factory_records.session_models()`)."""
    return sdlc.factory_records.session_models(_branch_files(main, branch, folder)[0])


def opened_at(text: str) -> datetime | None:
    """When the change was opened, from its intent's `opened:` line (`new`'s `OPENED_FORMAT`,
    read as text), as an aware datetime; None when the line is missing or doesn't fit."""
    value = (sdlc.frontmatter_list(text, "opened") or [""])[0]
    try:
        return datetime.strptime(value, sdlc.OPENED_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return None


def _lead_marks(
    main: Path, branch: str, folder: str, factory: bool, events: list[dict]
) -> tuple[datetime | None, datetime | None, datetime | None, list, str]:
    """`(first, ready, landing, intervals, source)` for `metrics.lead_time()`, from the first
    source that has them. A factory change: its committed run files (`runs`), its landing from
    the earliest `since`, else the tip's author date; else the factory sessions' runs in
    `events` (`transcripts`). A change built by hand: ready at ship's commit (the tip's author
    date, which a rebase keeps), no landing but close; its first event and turns from `events`
    (`transcripts`). Without either, `git`: no first, so no split."""
    authored = sdlc._git(main, "show", "-s", "--format=%aI", branch)
    tip = datetime.fromisoformat(authored) if authored else None
    landing = None
    if factory:
        records = sdlc.factory_records
        times = sdlc._git(main, "show", f"{branch}:{folder}/{records.LAND_TIMES.as_posix()}")
        sinces = records.land_sinces(times or "")
        landing, ready = min(sinces) if sinces else tip, None
    else:
        ready = tip

    def before_landing(role: str, rows: list[tuple[datetime, datetime, str]]):
        done = [r for r in rows if r[2] == role and (landing is None or r[0] < landing)]
        return max(done)[1] if done else None

    if factory:
        costs = sdlc._git(
            main, "show", f"{branch}:{folder}/{sdlc.factory_records.COSTS.as_posix()}"
        )
        timed = sdlc.factory_records.timed_rows(costs or "")
        source = "runs"
        if not timed:
            timed = [
                (e["ts"], e["ts"] + timedelta(milliseconds=e["ms"]), e["role"])
                for e in events
                if e["kind"] == "subagent"
            ]
            source = "transcripts"
        if timed:
            first = min(r[0] for r in timed)
            return first, before_landing("approver", timed), landing, [r[:2] for r in timed], source
        return None, None, landing, [], "git"
    if not events:
        return None, ready, None, [], "git"
    intervals = [
        (e["ts"] - timedelta(milliseconds=e["ms"]), e["ts"])
        if e["kind"] == "turn"
        else (e["ts"], e["ts"] + timedelta(milliseconds=e["ms"]))
        for e in events
        if e["kind"] in ("turn", "subagent")
    ]
    first = next((e["ts"] for e in events if e["kind"] != "runtime"), events[0]["ts"])
    return first, ready, None, intervals, "transcripts"


def _lead_line(
    main: Path,
    branch: str,
    folder: str,
    text: str,
    factory: bool,
    events: list[dict],
    errors: list[str] | None = None,
) -> tuple[str | None, str | None]:
    """The `Sdlc-Lead` line for a landing change, or None and the word `Sdlc-Coverage` gains
    instead (`lead=none`, `lead=bad-opened`, `lead=failed`). Never raises: what made it fail is
    added to `errors`, as `lead: <type>: <message>`, so a programming error is seen in close's
    report rather than hidden behind `lead=failed`. That message is the exception's raw text, for
    the person running close: it must never become a trailer, which holds numbers and names
    only."""
    if sdlc.frontmatter_list(text, "opened") is None:
        return None, "lead=none"
    opened = opened_at(text)
    if opened is None:
        return None, "lead=bad-opened"
    try:
        first, ready, landing, intervals, source = _lead_marks(
            main, branch, folder, factory, events
        )
        parts = sdlc.metrics.lead_time(opened, datetime.now(UTC), first, ready, landing, intervals)
        if not parts:
            return None, "lead=bad-opened"
        return sdlc.metrics.lead_trailer(parts, source), None
    except Exception as e:
        if errors is not None:
            errors.append(f"lead: {type(e).__name__}: {str(e)[:200]}")
        return None, "lead=failed"


def _day_start(created: date | None, now: datetime) -> datetime:
    """When a change's `created:` day began, for its elapsed time: midnight in this machine's
    timezone, since `created:` is the local day `new` stamped (`date.today()`), never after `now`
    (east of UTC, UTC midnight of that day can still lie ahead), and `now` when there is no day.
    A day the platform can't place falls back to UTC midnight."""
    if not created:
        return now
    try:
        start = datetime.combine(created, dtime()).astimezone()
    except (OverflowError, OSError, ValueError):
        start = datetime.combine(created, dtime(), UTC)
    return min(start, now)


def measure_change(main: Path, branch: str, cfg: dict) -> tuple[dict, list[str]]:
    """What a change cost, as a summary and its `Sdlc-*` trailer lines: from this repo's
    transcripts when `metrics.transcripts` allows and they hold the change, else what history
    gives (elapsed since `created`, the way of running), saying why. Never raises: measuring
    must never stop a change landing. The summary's `errors`, when there are any, hold raw
    exception text for the person running close (`_lead_line()`), shown in close's report and
    never turned into a trailer line."""
    settings = cfg["metrics"]
    folder = f"{sdlc.work_rel(main)}/{branch}"
    text = sdlc._git(main, "show", f"{branch}:{folder}/intent.md") or ""
    decision = sdlc.factory_records.DECISION_FILE
    decided = sdlc._git(main, "cat-file", "-e", f"{branch}:{folder}/{decision}")
    way = "factory" if decided is not None else "manual"
    try:
        post = frontmatter.loads(text)
        tier = int(post.get("tier") or 2)
        created = date.fromisoformat(str(post.get("created")))
    except Exception:
        tier, created = 2, None
    # Who passed the gate of a change `/sdlc-factory:land` landed: `person`, or `auto` when the
    # batch had no risk signal, written on the change's own commit, the branch's tip.
    tip = (
        sdlc.metrics.parse_trailers(sdlc._git(main, "show", "-s", "--format=%B", branch) or "")
        or {}
    )
    landed = (tip.get("landed") or {}).get("by") if isinstance(tip.get("landed"), dict) else None
    landed = landed if landed in ("auto", "person") else None

    def finish(summary: dict, events: list[dict]) -> tuple[dict, list[str]]:
        # Rework within the change, on lines of its own. A failure here drops only those lines.
        try:
            factory = _factory_files(main, branch)
            done = sdlc.metrics.rework(events, summary, factory, _change_diff(main, branch), tier)
            review = sdlc._git(main, "show", f"{branch}:{folder}/{sdlc.FINDINGS}")
            fixed = sum(
                e["disposition"] == "fixed" for e in sdlc._findings_from_text(review or "")[0]
            )
            first_time = sdlc.metrics.happy(events, summary, factory, tier, done, fixed, landed)
            extra = sdlc.metrics.in_change_trailers(
                done, first_time, sdlc.metrics.spike(events, summary)
            )
        except Exception:
            summary["coverage"] += " rework=failed"
            extra = []
        # What changed after the landed change's last review, carried from its tip to the totals.
        sdlc.metrics.landed_unreviewed(summary, tip)
        # Lead time, only for a change that lands: a dropped one never did.
        lead = None
        if sdlc.frontmatter_list(text, "stage") != ["dropped"]:
            errors: list[str] = []
            lead, missing = _lead_line(main, branch, folder, text, way == "factory", events, errors)
            if missing:
                summary["coverage"] += f" {missing}"
            if errors:
                summary["errors"] = errors
        # What ran underneath: Claude Code's versions and the models, from the events and the
        # factory roles' rows, and this plugin's version. A failure drops only this line.
        try:
            models = _agent_models(main, branch, folder).values()
            ran = sdlc.metrics.runtime_trailer(events, list(models), sdlc.plugin_version())
        except Exception:
            summary["coverage"] += " runtime=failed"
            ran = None
        tail = [line for line in (lead, ran) if line]
        return summary, sdlc.metrics.trailers(summary) + extra + tail

    def from_history(reason: str) -> tuple[dict, list[str]]:
        now = datetime.now(UTC)
        start = _day_start(created, now)
        summary = sdlc.metrics.history_summary(
            (now - start).total_seconds(), way, tier, settings, reason
        )
        return finish(summary, [])

    if not settings["transcripts"]:
        return from_history("metrics.transcripts is off")
    try:
        dirs = sdlc._project_dirs(main)
        files = sum(1 for d in dirs for _ in d.glob("*.jsonl"))
        if not files:
            return from_history("no transcripts for this repo")
        roles = _agent_sessions(main, branch, folder)
        models = _agent_models(main, branch, folder)
        events = sdlc.metrics.read_events(
            dirs, branch, branch, cfg["commands"]["check"], roles, models
        )
        if not events:
            return from_history("no transcripts for this change")
        closes = _close_times(main, cfg["git"]["base"])
        dep_closes = {}
        for ident in sdlc.depends_on(text):
            name = next((n for n in closes if sdlc.names_change(n, ident)), ident)
            dep_closes[name] = closes.get(name)
        summary = sdlc.metrics.summarize(events, dep_closes, settings, way, tier, landed)
        summary["coverage"] = f"transcripts={files} {summary['coverage']}"
        return finish(summary, events)
    except Exception as e:
        return from_history(f"capture failed: {type(e).__name__}")


def fix_trailers(main: Path, branch: str) -> list[str]:
    """An `Sdlc-Fixes:` line for each bug the change's intent names on `fixes:`, with its
    severity, reported date and introducing change as the register held them in the newest commit
    on the branch that still had the entry; `unknown` where none did. Never raises: a fix that
    can't be described is still recorded."""
    try:
        rel = sdlc.work_rel(main)
        intent = sdlc._git(main, "show", f"{branch}:{rel}/{branch}/intent.md") or ""
        fixes = sdlc.frontmatter_list(intent, "fixes") or []
        found: dict[str, dict] = {}
        paths = [f"{rel}/{sdlc.INBOX}", f"{rel}/{sdlc.OLD_INBOX}"]
        shas = (sdlc._git(main, "log", "--format=%H", branch, "--", *paths) or "").split()
        for sha in shas:
            if all(f in found for f in fixes):
                break
            for rel in paths:
                for e in sdlc.parse_entries(sdlc._git(main, "show", f"{sha}:{rel}") or ""):
                    if e["id"] in fixes and e["id"] not in found:
                        found[e["id"]] = e
        lines = []
        for f in fixes:
            e = found.get(f)
            fields = e["fields"] if e else {}
            severity = (fields.get("Severity") or "unknown").replace(" ", "-")
            introduced = (fields.get("Introduced by") or "unknown").strip()
            reported = e["date"] if e else "unknown"
            # The register loses the entry with the fix, so retro reads its paths here.
            paths = ",".join(
                p.strip().strip("`").replace(" ", "")
                for p in (fields.get("Paths") or "").split(",")
                if p.strip()
            )
            lines.append(
                f"Sdlc-Fixes: {f} severity={severity} reported={reported} "
                f"introduced_by={introduced} paths={paths or 'unknown'}"
            )
        return lines
    except Exception:
        return []


def origin_trailer(main: Path, branch: str) -> list[str]:
    """An `Sdlc-Origin:` line for where the change's finding came from, its intent's `origin:`
    on the branch; none for no line or a word outside `ORIGINS`, never one guessed. Never raises:
    an origin that can't be read is unknown."""
    try:
        rel = sdlc.work_rel(main)
        intent = sdlc._git(main, "show", f"{branch}:{rel}/{branch}/intent.md") or ""
        origin = sdlc.frontmatter_list(intent, "origin") or []
        if len(origin) == 1 and origin[0] in sdlc.ORIGINS:
            return [f"Sdlc-Origin: {origin[0]}"]
        return []
    except Exception:
        return []


def _drop_commit(main: Path, branch: str, trunk: str) -> str | None:
    """The `Drop <branch>` commit on the base's first-parent line whose second parent is the
    branch's tip: a rerun's sign that `record` is done. None when there is none."""
    tip = sdlc._git(main, "rev-parse", branch)
    log = sdlc._git(main, "log", "--first-parent", "--format=%H%x00%P%x00%s", trunk) or ""
    for line in log.splitlines():
        sha, parents, subject = (line.split("\x00") + ["", ""])[:3]
        if subject == f"{sdlc.DROP_PREFIX}{branch}" and parents.split()[1:2] == [tip]:
            return sha
    return None


def _drop_record(
    main: Path,
    branch: str,
    sha: str,
    where: str | None,
    reached: str,
    reason: str,
    trailers: list[str] | None = None,
) -> str | None:
    """Record a dropped change on main: `Drop <branch>`, a merge that keeps main's tree, so the
    branch's commits stay reachable and `branch -d` can delete it. Only the state `new` wrote
    comes along: the higher counter, so the number stays spent. `measure`'s trailers end the
    message, as on a `Close` commit. Returns why it failed, or None once the commit is made; a
    failure aborts the merge and leaves main as it was."""
    steps = [["merge", "-q", "-s", "ours", "--no-ff", "--no-commit", branch]]
    shown = sdlc._git(main, "show", f"{branch}:.sdlc/{sdlc.LAST_ID}") or ""
    theirs = int(shown) if shown.isdigit() else None
    if theirs is not None and theirs > (sdlc.read_last_id(main) or 0):
        steps.append(["write", sdlc.LAST_ID, f"{theirs:03d}\n"])
    note = f"Dropped at {reached}; its artifacts are in {sha}" + (
        f", and archived to {where}." if where else "."
    )
    message = ["-m", f"{sdlc.DROP_PREFIX}{branch}", "-m", reason, "-m", note]
    if trailers:
        message += ["-m", "\n".join(trailers)]
    steps.append(["commit", "-q", *message])
    for args in steps:
        if args[0] == "write":
            sdlc._write_state(main, args[1], args[2])
            args = ["add", "--", f".sdlc/{args[1]}"]
        err = sdlc._git_err(main, *args)
        if err:
            sdlc._git(main, "merge", "--abort")
            return f"git {args[0]} failed: {err}"
    return None


def _branch_register_plan(main: Path, branch: str, register: str) -> dict:
    """`register_plan()` for the shipped change on `branch`, against the register text
    `register`: its intent and its `entries.md` as the change's own commit holds them, so what
    lands is what was shipped, never a worktree's later edit."""
    rel = f"{sdlc.work_rel(main)}/{branch}"
    intent = sdlc._git(main, "show", f"{branch}:{rel}/intent.md") or ""
    held = sdlc._git(main, "show", f"{branch}:{rel}/{sdlc.ENTRIES}")
    return register_plan(register, intent, sdlc.held_entries(held or ""))


def _close_commit(
    main: Path,
    branch: str,
    sha: str,
    where: str | None,
    trailers: list[str] | None = None,
    closes: str | None = None,
) -> str | None:
    """Remove the change's folder from `main` in a commit of its own, with the change's register
    edits (`_branch_register_plan()`): why not, or None. The register is read, written and
    committed under `_main_lock()`, which `inbox-commit` takes, so an entry filed meanwhile is
    kept. A folder `main` no longer tracks was removed by an earlier run, register and all, which
    is done, so a rerun writes no second set of trailers or entries. `trailers` end the message,
    where git reads them as trailers; `closes`, the tracker's line for closing its issue on the
    push, ends the paragraph before."""
    folder = f"{sdlc.work_rel(main)}/{branch}"
    if not sdlc._git(main, "ls-files", folder):
        return None
    said = f"Its artifacts are in {sha}" + (f", and archived to {where}." if where else ".")
    register = sdlc.register_path(sdlc.work_dir(main))
    reg = f"{sdlc.work_rel(main)}/{register.name}"
    with _main_lock(main):
        before = register.read_text(encoding="utf-8") if register.is_file() else None
        plan = _branch_register_plan(main, branch, before or "")
        if plan["refusals"]:
            return "; ".join(plan["refusals"])
        wrote = plan["text"] != (before or "")
        if wrote:
            register.parent.mkdir(parents=True, exist_ok=True)
            register.write_text(plan["text"], encoding="utf-8", newline="\n")
        for args in (
            *([["add", "--", reg]] if wrote else []),
            ["rm", "-r", "-q", folder],
            [
                "commit", "-q", "-m", f"Close {branch}",
                "-m", said + (f"\n{closes}" if closes else ""),
                *(["-m", "\n".join(trailers)] if trailers else []),
            ],
        ):  # fmt: skip
            made = subprocess.run(
                ["git", "-C", str(main), *args], capture_output=True, encoding="utf-8"
            )
            if made.returncode != 0:
                # Put the folder and the register back, or the rerun that finishes this would
                # find main dirty.
                sdlc._git(main, "reset", "-q", "HEAD", "--", folder, *([reg] if wrote else []))
                sdlc._git(main, "checkout", "-q", "--", folder)
                if wrote and before is None:
                    register.unlink(missing_ok=True)
                elif wrote:
                    register.write_text(before, encoding="utf-8", newline="\n")
                return f"git {args[0]} failed: {made.stderr.strip() or made.stdout.strip()}"
    return None


# Set on a close that another close handed off to: `home` once it runs main's script, `merged` once
# it runs the code its own merge brought. Read only here, so a handoff never loops.
HANDOFF_ENV = "SDLC_CLOSE_RAN"


RAN = {"home": "main's code", "merged": "merged code"}


def _handoff(main: Path, argv: list[str], ran: str, report: dict) -> int:
    """Run this close again with the main checkout's `scripts/sdlc.py`, as the skills run it, and
    give its report and exit code as this one's. A close is safe to rerun at any step, so the
    second one finds what this one did and carries on. If it prints no report (it didn't start),
    say so in `report` and stop: never carry on with the code this process loaded."""
    script = main / "scripts" / "sdlc.py"
    # After the merge this process holds `_main_lock()` (`cmd_close()`), and waits here: the
    # child is told so, and takes none of its own, or the two would deadlock on the one file.
    lock = str(_lock_path(main))
    passed = {LOCK_HELD_ENV: lock} if _lock_depth().get(lock) else {}
    made = subprocess.run(
        [*sdlc._script_cmd(), str(script), "close", *argv],
        capture_output=True,
        encoding="utf-8",
        env=os.environ | {HANDOFF_ENV: ran} | passed,
    )
    try:
        out = json.loads(made.stdout)
    except ValueError:
        out = None
    if isinstance(out, dict):
        out.setdefault("ran", RAN[ran])  # the innermost close says what ran it
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return made.returncode
    said = [ln for ln in made.stderr.splitlines() if ln.strip()]
    why = said[-1].strip() if said else f"exited {made.returncode}"
    if ran == "home":
        report["refusals"].append(f"main's sdlc.py didn't run: {why}")
    else:
        number = str(report.get("change") or "").split("-")[0]
        report["refusals"].append(
            f"merged code didn't run: {why}; main is merged, rerun /sdlc:close {number}"
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1


CLEANUP_TIMEOUT = 600  # seconds for the host's cleanup; a hung one is reported, never waited out


def _cleanup_plan(cfg: dict | None, fallback: dict, number: str) -> dict | None:
    """What close's last step runs: `close_cleanup` with `{id}` filled and a leading `!` (the
    prompt's prefix, which `sh` reads as negation) dropped, and whether it `runs`, from `cfg`, the
    base branch's config from before the merge. With that unreadable (None), the command comes
    from `fallback` and nothing runs: it is handed over. None when no cleanup is set."""
    command = (cfg or fallback)["commands"]["close_cleanup"]
    if not command:
        return None
    plan = {"command": re.sub(r"^!\s*", "", command.replace("{id}", number)), "runs": False}
    if cfg is None:
        plan["because"] = "the base branch's config from before the merge can't be read"
    else:
        plan["runs"] = bool(cfg["commands"]["close_cleanup_runs"])
    return plan


def _carries_others(main: Path, branch: str, trunk: str) -> list[str]:
    """The other changes whose folders a commit in `<trunk>..<branch>` adds or changes: a branch
    stacked on another change's commit by a landing train that didn't finish."""
    names = sdlc._git(main, "log", "--format=", "--name-only", f"{trunk}..{branch}") or ""
    prefix = sdlc.work_rel(main) + "/"
    found = set()
    for line in names.splitlines():
        if not line.startswith(prefix):
            continue
        head = line[len(prefix) :].split("/", 1)[0]
        if head != branch and sdlc.DIR_RE.match(head):
            found.add(head)
    return sorted(found)


class _Close:
    """What close's steps share, in place of the locals one long function held: the change and
    its settings, the refs and plans the preview works out, and the report every step writes
    into. Each `_step_*` takes it and returns an error, or None. A plain class, not a dataclass:
    this file is loaded by path and never registered in `sys.modules`, where `dataclass` looks
    up a class's module."""

    def __init__(
        self,
        main: Path,
        report: dict,
        check_only: bool,
        cfg: dict,
        own_repo: bool,
        unavailable: str | None,
    ) -> None:
        self.main, self.report, self.check_only, self.cfg = main, report, check_only, cfg
        self.own_repo = own_repo  # the plugin's own repo, where close hands off
        self.unavailable = unavailable  # why there is no archive, or None
        self.tree: Path | None = None
        self.branch = ""  # empty while no one change is found
        self.folder: Path | None = None
        self.kind: str | None = None
        self.trunk = ""
        self.landed = False
        self.sha = "?"
        self.start = ""  # the start ref, `BASE_REF` + the branch
        self.plan: dict = {}  # the push plan
        self.wipe: dict | None = None  # the cleanup plan
        self.kept: dict = {}  # a drop's `reached` and `reason`
        self.captured: list[str] = []  # the measure step's trailers


def cmd_close(root: Path, ident: str | None, check_only: bool = False) -> int:
    """Land a shipped change, mirror it, remove its folder, its worktree and its branch; or, for
    a dropped one, mirror it, record it on main in a `Drop` commit, and remove its worktree and
    branch.

    The steps, in order: `merge` (`--ff-only`), `verify`, `measure`, `archive` (the tracker's
    `archive()`, read back), `remove folder` (`_close_commit()`), `remove worktree`, `delete
    branch`; then `push` when `git.push` names close (`_push_plan()`), a refusal of which is
    `push_failed`, never a failed close, and last `cleanup`. A dropped change's `record`
    (`_drop_record()`) stands in for the merge and the folder's removal. The fast-forward
    deletes from the main checkout's disk each tracked file the change removed
    (`_ff_deletions()`), which close's question names; close never restores one. Each step is
    its own function (`_step_merge()` … `_step_cleanup()`) on a `_Close`, which holds what they
    share; `_close_target()` finds the change, `_close_refusals()` and `_close_preview()` check
    and work out everything before anything is written, `_close_steps()` lists the steps for a
    shipped or a dropped change, and `_run_close_steps()` runs them under the lock.

    Every git step is one git refuses when something would be lost: `merge --ff-only`,
    `worktree remove` without --force, `branch -d`. The folder is removed only once the change's
    commit, which holds it, is on `main`: history is the copy, and the tracker a mirror of it. A
    dropped change's folder never reaches main's tree; its `Drop` merge makes its commits
    reachable from main before the branch goes. A rerun resumes: the merge is a no-op, the archive
    reuses its issue, a removed folder or a recorded drop is skipped.

    In the plugin's own repo, the close is run by main's script, then by the code its merge
    brought (`_handoff()`), so a change to close runs on its own close, and a stale copy of the
    plugin never closes anything.

    With `commands.close_cleanup_runs`, the host's `close_cleanup` runs last, once all of that
    and the push are done, read from the base branch's config before the merge
    (`_cleanup_plan()`). A failure is `cleanup_failed`, never a failed close: it has landed.

    `_main_lock()` is held from before the merge until `_close_commit()` has committed (the
    `record` step, for a drop), and let go before the issues are told, the worktree's removal,
    the push and the cleanup: no `File` commit can come between the change's commit and its
    `Close`, where `closed_changes()` reads the `Close`'s first parent as the change. A rerun that
    finds the change merged takes it before its `remove folder` step. A close handed off after
    its merge runs under the parent's hold (`_inherit_lock()`), told by `LOCK_HELD_ENV`, which
    is cleared here before any other process starts.

    A branch carrying another change's commits (`_carries_others()`: a train that stopped part
    way leaves one stacked) is refused before anything is written: its fast-forward would put the
    other change on the base branch with no `Close`."""
    # Before `main_root()`'s own git: no process this close starts carries the variable.
    held = os.environ.pop(LOCK_HELD_ENV, None)
    main = sdlc.main_root(root)
    _inherit_lock(main, held)
    own = sdlc._own_repo(main)
    if own and sdlc.PLUGIN_DIR.resolve() != main.resolve() and not os.environ.get(HANDOFF_ENV):
        argv = [*([ident] if ident else []), *(["--check"] if check_only else [])]
        report = {"change": ident, "main_checkout": str(main), "refusals": [], "done": []}
        return _handoff(main, argv, "home", report | {"skipped": []})
    c = _close_target(root, main, ident, check_only, own)
    if not c.branch or _close_refusals(c):
        return _emit(c.report, 1)
    _close_preview(c)
    steps = _close_steps(c)
    if check_only:
        names = [name for name, _ in steps] + (["push"] if c.plan["on"] else [])
        names += ["cleanup"] if c.wipe and c.wipe["runs"] else []
        c.report["skipped"] = [f"{name} (--check)" for name in names]
        return _emit(c.report, 0)
    return _run_close_steps(c, steps)


def _emit(report: dict, code: int) -> int:
    """Print close's report, its keys in the order the steps wrote them, and return `code`."""
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return code


def _close_target(
    root: Path, main: Path, ident: str | None, check_only: bool, own_repo: bool
) -> _Close:
    """The change close was asked for, in a `_Close` with the report begun; its `branch` is
    empty when no change was named or the name matches no worktree, or several, which the
    report's refusals then say. An archive set up wrong is a refusal said here, checked with
    the rest by `_close_refusals()`."""
    cfg, _, _ = sdlc.load_config(main)
    trees = [(t, b) for t, b in sdlc.worktrees(root) if sdlc.DIR_RE.match(b)]
    if ident is None:
        here = sdlc._git(root, "branch", "--show-current") or ""
        ident = here if sdlc.DIR_RE.match(here) else None
    found = [(t, b) for t, b in trees if sdlc.names_change(b, ident)] if ident else []
    unavailable = sdlc.archive_unavailable(main, cfg)
    report: dict = {
        "change": ident,
        "main_checkout": str(main),
        "archive": {"target": cfg["archive"]["target"], "location": None},
        "refusals": [],
        "done": [],
        "skipped": [],
    }
    c = _Close(main, report, check_only, cfg, own_repo, unavailable)
    # Nowhere to mirror to is an answer; a target set up wrong is a refusal.
    if unavailable and cfg["archive"]["target"] in ("none", "github"):
        report["archive"]["kept_because"] = unavailable
    elif unavailable:
        report["refusals"].append(f"archive: {unavailable}")

    if not ident:
        report["refusals"].append(
            "no change named, and this checkout isn't on an NNN-slug branch: give its number"
        )
        return c
    if len(found) != 1:
        report["refusals"].append(
            f"{ident!r} matches {'no' if not found else len(found)} worktree(s)"
            + (f": {', '.join(b for _, b in found)}" if found else "")
        )
        return c
    c.tree, c.branch = found[0]
    c.folder = sdlc.work_dir(c.tree) / c.branch
    c.kind = sdlc._stage(c.folder)
    report.update(change=c.branch, worktree=str(c.tree), branch=c.branch, kind=c.kind)
    return c


def _close_refusals(c: _Close) -> bool:
    """Whether close refuses the change, each reason added to the report's refusals: not shipped
    or dropped with its reason, a worktree or main checkout not clean, a base branch close
    can't use, a branch that can't fast-forward or carries another change, or a register its
    `Close` commit couldn't write. Checked before anything is written; merged already is a
    rerun's state, not a refusal."""
    main, tree, branch, folder, kind = c.main, c.tree, c.branch, c.folder, c.kind
    report = c.report
    if kind not in ("shipped", "dropped"):
        report["refusals"].append(
            f"{branch} isn't shipped: {folder}/intent.md with stage: shipped is missing. Run "
            "/sdlc:ship first, or /sdlc:drop to drop it."
        )
    elif kind == "dropped" and not sdlc.dropped_reason((folder / "intent.md").read_text("utf-8")):
        report["refusals"].append(
            f"{branch} is dropped with no `## {sdlc.DROPPED}` section saying why: run /sdlc:drop"
        )
    if sdlc._git(tree, "status", "--porcelain") not in ("", None):
        report["refusals"].append(f"{tree} has uncommitted or untracked files")
    c.trunk = trunk = c.cfg["git"]["base"]
    if why := sdlc.trunk_refusal(main, trunk, c.cfg["git"]["base_source"]):
        report["refusals"].append(why)
        return True
    if sdlc._git(main, "branch", "--show-current") != trunk:
        report["refusals"].append(f"the main checkout ({main}) isn't on {trunk}")
    if sdlc._git(main, "status", "--porcelain", "--untracked-files=no") not in ("", None):
        report["refusals"].append(f"the main checkout ({main}) has uncommitted changes")
    # Merged already is a rerun's state, not a refusal.
    c.landed = landed = sdlc._git(main, "merge-base", "--is-ancestor", branch, trunk) is not None
    if kind == "dropped":
        # A dropped change is recorded whatever the base has done since: nothing of it lands.
        if landed and not _drop_commit(main, branch, trunk):
            report["refusals"].append(
                f"{branch} is already on {trunk} with no {sdlc.DROP_PREFIX}{branch} commit: it "
                "landed, so it isn't a drop"
            )
    elif not landed and sdlc.behind_trunk(main, branch, trunk) != 0:
        report["refusals"].append(
            f"{trunk} has moved past {branch}'s base, so it can't fast-forward; rebase {branch} "
            f"onto {trunk} in its worktree and ship again"
        )
    elif not landed and (others := _carries_others(main, branch, trunk)):
        report["refusals"].append(
            f"{branch} carries another change's commits ({', '.join(others)}): a landing train "
            f"left it stacked. Put it back with git reset --keep <its commit before the train> "
            "in its worktree, or finish the train with /sdlc-factory:land"
        )
    # What the `Close` commit does to the register, checked before anything is written: against
    # the base's register now, and again under the lock when it is written.
    if kind == "shipped" and not (
        landed and not sdlc._git(main, "ls-files", f"{sdlc.work_rel(main)}/{branch}")
    ):
        reg = f"{sdlc.work_rel(main)}/{sdlc.register_path(sdlc.work_dir(main)).name}"
        planned = _branch_register_plan(
            main, branch, sdlc._git(main, "show", f"{trunk}:{reg}") or ""
        )
        report["register"] = {k: planned[k] for k in ("file", "retire", "gone")}
        report["refusals"] += [f"register: {r}" for r in planned["refusals"]]
    return bool(report["refusals"])


def _close_preview(c: _Close) -> None:
    """What close will do, worked out before any step runs, into `c` and its report: the start
    ref (written unless `--check`), the cleanup's plan, what the fast-forward deletes, whom the
    change reaches, and the push's plan with what it sends."""
    main, tree, branch, kind, trunk, landed = c.main, c.tree, c.branch, c.kind, c.trunk, c.landed
    report, cfg = c.report, c.cfg
    c.start = start = sdlc.BASE_REF + branch
    tip = sdlc._git(main, "rev-parse", "--verify", "-q", trunk)
    if kind == "shipped" and not c.check_only and not landed and tip:
        # Until the merge, `trunk`'s tip is where the change starts, so a ref an earlier run left
        # before a failed merge is brought up to it; once merged, a rerun keeps it. A failure
        # only leaves the trailer out.
        sdlc._git(main, "update-ref", start, tip)
    # The cleanup's config is the base branch's before the merge: the start ref's once there is
    # one, main's own while nothing has landed, and none to go by after. A drop lands nothing.
    if kind == "dropped" or (
        not landed and not sdlc._git(main, "rev-parse", "--verify", "-q", start)
    ):
        at = cfg
    else:
        at = sdlc._config_at(main, start)
    if wipe := _cleanup_plan(at, cfg, branch.split("-")[0]):
        report["cleanup"] = c.wipe = wipe
    # What the fast-forward deletes from the main checkout, for the question to name: a file the
    # change stopped tracking goes from disk there too, whatever the ignore rules now say.
    if kind == "shipped" and not landed:
        report["deletes"] = _ff_deletions(main, tree, trunk, branch)
    # A check writes no start ref, so it previews from where the close would write it.
    preview = tip if c.check_only and not landed else None
    if c.own_repo and kind == "shipped" and (reaches := _reaches(main, branch, preview)):
        report["reaches"] = reaches
    # What the push of the base branch sends, newest first: the Close or Drop commit while this run
    # has yet to write it, the change's own commits not on the base branch yet, then everything the
    # base branch already holds that the remote doesn't. A dropped branch may be behind the base
    # branch, and a rerun may find the merge done, so it's never read from the branch's tip alone.
    report["push"] = c.plan = plan = _push_plan(main, cfg, "close")
    if plan["on"] and plan["unpushed"] is not None:
        if kind == "dropped":
            written = bool(_drop_commit(main, branch, trunk))
        else:
            written = landed and not sdlc._git(main, "ls-files", f"{sdlc.work_rel(main)}/{branch}")
        ahead = (sdlc._git(main, "log", "--format=%h %s", f"{trunk}..{branch}") or "").splitlines()
        coming = [] if written else [f"(new) {'Drop' if kind == 'dropped' else 'Close'} {branch}"]
        plan["unpushed"]["ahead"] = coming + ahead + plan["unpushed"]["ahead"]
    c.sha = sdlc._git(main, "rev-parse", "--short", branch) or "?"


def _close_steps(c: _Close) -> list[tuple[str, object]]:
    """The steps for the change's kind, as `(name, step)`, the names the report shows. Built on
    each call, never at load, so nothing evaluated at load reads `sdlc`."""
    if c.kind == "dropped":
        landing = [("verify", _step_verify), ("measure", _step_measure), ("archive", _step_archive)]
        landing.append(("record", _step_record))
    else:
        landing = [("merge", _step_merge), ("verify", _step_verify), ("measure", _step_measure)]
        landing += [("archive", _step_archive), ("remove folder", _step_remove_folder)]
    return [
        *landing,
        ("remove worktree", _step_remove_worktree),
        ("delete branch", _step_delete_branch),
    ]


def _run_close_steps(c: _Close, steps: list[tuple[str, object]]) -> int:
    """Run the steps in order, under `_main_lock()` from the first until the `Close` or `Drop`
    commit; then the push, or the nudge, and the cleanup. A step that fails stops the close with
    what's left skipped (exit 1), a close run from inside the worktree stops before removing it
    (exit 3), and a merge that brings new scripts hands the rest to them (`_handoff()`)."""
    main, tree, branch, trunk, report = c.main, c.tree, c.branch, c.trunk, c.report
    inside = Path.cwd().resolve().is_relative_to(tree.resolve())
    before = sdlc._git(main, "rev-parse", trunk)
    # The lock, from the first landing step (the merge) until the `Close` or `Drop` commit is
    # made: let go once the folder is removed, before the worktree, the push and the cleanup. A
    # handoff after the merge runs inside it, so the child's commit is still under this hold.
    with ExitStack() as hold:
        for i, (name, step) in enumerate(steps):
            if i == 0:
                hold.enter_context(_main_lock(main))
            if name == "remove worktree":
                hold.close()
            if name == "remove worktree" and inside:
                report["skipped"] = [n for n, _ in steps[i:]]
                report["refusals"].append(
                    f"worktree kept: this process runs inside {tree}. Run /sdlc:close "
                    f"{branch.split('-')[0]} from the main checkout to finish."
                )
                return _emit(report, 3)
            if name == "archive" and c.unavailable:
                continue
            err = step(c)
            if err:
                report["skipped"] = [n for n, _ in steps[i:]]
                report["refusals"].append(f"{name} failed: {err}")
                return _emit(report, 1)
            report["done"].append(name)
            if name == "remove folder":
                hold.close()
                _step_tell_issues(c)
            if name == "merge" and c.own_repo and _merged_scripts(main, before, trunk):
                # The rest runs as the code this merge brought.
                report["skipped"] = [n for n, _ in steps[i + 1 :]]
                return _handoff(main, [branch], "merged", report)
    if c.plan["on"]:
        _step_push(c)
    elif nudge := sdlc._nudge(main, c.cfg):
        report["unpushed"] = nudge
    if c.wipe and c.wipe["runs"]:
        _step_cleanup(c)
    return _emit(report, 0)


def _step_merge(c: _Close) -> str | None:
    return sdlc._git_err(c.main, "merge", "--ff-only", "-q", c.branch)


def _step_verify(c: _Close) -> str | None:
    # The copy that counts: the change's own commit, in main's history once it lands.
    intent = f"{sdlc.work_rel(c.main)}/{c.branch}/intent.md"
    text = sdlc._git(c.main, "show", f"{c.branch}:{intent}")
    try:
        ok = text is not None and frontmatter.loads(text).get("stage") == c.kind
    except Exception:
        ok = False
    if not ok:
        return f"{c.branch}'s commit doesn't hold {intent}, {c.kind}"
    if c.kind == "dropped":
        if not sdlc.dropped_reason(text):
            return f"{c.branch}'s commit has no `## {sdlc.DROPPED}` section in its intent.md"
        c.kept["reached"] = (sdlc.frontmatter_list(text, "dropped_at") or [""])[0] or "unknown"
        c.kept["reason"] = sdlc.first_paragraph(sdlc._body_of(text), sdlc.DROPPED)
    return None


def _step_measure(c: _Close) -> str | None:
    # Never a refusal: a change that can't be measured still lands, and says why.
    try:
        summary, lines = measure_change(c.main, c.branch, c.cfg)
    except Exception as e:
        summary, lines = {"coverage": f"none: capture failed: {type(e).__name__}"}, []
        lines = [f"Sdlc-Coverage: {summary['coverage']}"]
    c.captured[:] = lines
    c.report["measure"] = {"coverage": summary["coverage"], "trailers": lines}
    # What failed while measuring, only when something did, so a healthy report is unchanged.
    if summary.get("errors"):
        c.report["measure"]["errors"] = summary["errors"]
    return None


def _step_archive(c: _Close) -> str | None:
    if c.unavailable:
        return None
    change = sdlc._tracker_change(c.main, c.folder, c.sha)
    mirror_to = sdlc.tracker(c.main, c.cfg)
    where, err = mirror_to.archive(change)
    c.report["archive"]["location"] = where
    # What the tracker says about closing its issue: a line for the Close commit, so the
    # push closes it, or why it closed it now, and any issue on the change's `closes:` line
    # it couldn't close or let go. Only a tracker that has them sets them.
    for key in ("closes", "closed_because", "closes_errors"):
        if getattr(mirror_to, key, None):
            c.report["archive"][key] = getattr(mirror_to, key)
    return err


def _step_remove_folder(c: _Close) -> str | None:
    where, closes = c.report["archive"]["location"], c.report["archive"].get("closes")
    fixes = fix_trailers(c.main, c.branch)
    if fixes:
        c.report["fixes"] = fixes
    at = sdlc._git(c.main, "rev-parse", "--verify", "-q", c.start)
    based = [f"{sdlc.BASE_KEY}: {at}"] if at else []
    trailers = c.captured + based + fixes + origin_trailer(c.main, c.branch)
    return _close_commit(c.main, c.branch, c.sha, where, trailers, closes)


def _step_tell_issues(c: _Close) -> None:
    # The entries the change brought to main, a seed split off at ship among them, are
    # committed now, so their issues are told where to follow. Never a refusal, and after the
    # lock is let go: the tracker's calls are no part of the span it guards.
    if c.unavailable:
        return
    found = sdlc.tracker(c.main, c.cfg)
    if hasattr(found, "mark"):
        marked = sdlc.mark_issues(c.main, found)
        if marked["done"] or marked["failed"]:
            c.report["intake"] = marked


def _step_record(c: _Close) -> str | None:
    if _drop_commit(c.main, c.branch, c.trunk):
        return None  # recorded by an earlier run that stopped before removing the worktree
    where = c.report["archive"]["location"]
    return _drop_record(
        c.main, c.branch, c.sha, where, c.kept["reached"], c.kept["reason"], c.captured
    )


def _step_remove_worktree(c: _Close) -> str | None:
    return sdlc._git_err(c.main, "worktree", "remove", str(c.tree))


def _step_delete_branch(c: _Close) -> str | None:
    main, branch, start, report = c.main, c.branch, c.start, c.report
    err = sdlc._git_err(main, "branch", "-d", branch)
    # Its start is on the `Close` commit now; a ref left behind is said, never refused.
    if err is None and sdlc._git(main, "rev-parse", "--verify", "-q", start):
        gone = sdlc._git_err(main, "update-ref", "-d", start)
        if gone:
            report["base_ref"] = f"{start} kept: {gone}"
    # A resolution's refs (`cmd_resolve()`) go with the branch, the work they kept landed.
    for which in sdlc.RESOLVE_REFS if err is None else ():
        ref = sdlc._resolve_ref(which, branch)
        left = sdlc._git(main, "rev-parse", "--verify", "-q", ref) and sdlc._git_err(
            main, "update-ref", "-d", ref
        )
        if left:
            report.setdefault("resolve_refs", []).append(f"{ref} kept: {left}")
    return err


def _step_push(c: _Close) -> None:
    # Never a refusal: the change has landed, and publish pushes what this couldn't. In `done`
    # only once it went, so `done` never says main is on the remote when it isn't.
    sent = sdlc._unpushed(c.main, c.cfg)
    if err := _push(c.main, c.plan["remote"], f"refs/heads/{c.trunk}"):
        c.report["push_failed"] = (
            f"{err}; /sdlc:publish pushes it, or set [git] push = [] to leave it to publish"
        )
        return
    c.plan["closed"] = sent["closes"] if sent else []
    c.report["done"].append("push")


def _step_cleanup(c: _Close) -> None:
    # Never a refusal, like the push: the change has landed and its worktree is gone, so a
    # rerun can't find it to run this twice. In `done` only once it exited 0.
    err = None
    try:
        ran = subprocess.run(
            sdlc._sh(c.wipe["command"]), cwd=c.main, capture_output=True, encoding="utf-8",
            errors="replace", timeout=CLEANUP_TIMEOUT, stdin=subprocess.DEVNULL,
        )  # fmt: skip
        if ran.returncode != 0:
            said = (ran.stderr.strip() or ran.stdout.strip())[-500:] or "no output"
            err = f"exited {ran.returncode}: {said}"
    except subprocess.TimeoutExpired:
        err = f"timed out after {CLEANUP_TIMEOUT}s"
    except OSError as e:
        err = f"didn't run: {e}"
    if err:
        c.report["cleanup_failed"] = err
    else:
        c.report["done"].append("cleanup")


def _reaches(main: Path, branch: str, start: str | None = None) -> dict | None:
    """`landing_reach()` over everything the change's branch touched, from `start` when given (the
    base branch's tip, which close's `--check` writes no ref for); None when it touched
    nothing that reaches anyone. Never a refusal: a change whose paths can't be read lands, and
    `unknown` says why, so "nothing to do" is never a guess."""
    try:
        base = start or sdlc._change_base(main, branch)
        if base is None:
            return {"unknown": f"no commit on {branch} holds its intent"}
        names = sdlc._git(main, "diff", "--name-only", "--no-renames", base, branch)
        if names is None:
            return {"unknown": f"git couldn't diff {branch} against its base"}
        return sdlc.landing_reach(names.splitlines()) or None
    except Exception as e:
        return {"unknown": f"reading the change's paths failed: {type(e).__name__}"}


def _ff_deletions(main: Path, tree: Path, trunk: str, branch: str) -> dict:
    """The tracked paths close's fast-forward of `trunk` to `branch` deletes from the main
    checkout, `ignored` (the branch's ignore rules now cover them, read in its worktree) apart
    from the `other`, sorted; a rename is a move, never a deletion. Never a refusal: when git
    can't say, `unknown` says why, and close goes ahead."""
    try:
        names = sdlc._git(
            main, "diff", "--name-only", "-z", "--diff-filter=D", "--find-renames", trunk, branch
        )
        if names is None:
            return {"unknown": f"git couldn't diff {branch} against {trunk}"}
        paths = [p for p in names.split("\0") if p]
        ignored: set[str] = set()
        if paths:
            # Exit 1 is "none of them", which `_git` can't tell from a failure.
            made = subprocess.run(
                ["git", "-C", str(tree), "check-ignore", "--no-index", "-z", "--stdin"],
                input="\0".join(paths), capture_output=True, encoding="utf-8",
            )  # fmt: skip
            if made.returncode not in (0, 1):
                said = made.stderr.strip().splitlines()[-1:] or [f"exited {made.returncode}"]
                return {"unknown": f"git couldn't read {branch}'s ignore rules: {said[0]}"}
            ignored = {p for p in made.stdout.split("\0") if p}
        return {
            "ignored": sorted(p for p in paths if p in ignored),
            "other": sorted(p for p in paths if p not in ignored),
        }
    except Exception as e:
        return {"unknown": f"reading the deletions failed: {type(e).__name__}"}


def _merged_scripts(main: Path, before: str | None, trunk: str) -> bool:
    """Whether a merge just brought this plugin's scripts into the main checkout it runs from, so
    the rest of the close must run as the merged code. Never twice for one close."""
    after = sdlc._git(main, "rev-parse", trunk)
    return (
        sdlc.PLUGIN_DIR.resolve() == main.resolve()
        and os.environ.get(HANDOFF_ENV) != "merged"
        and before is not None
        and after != before
        and bool(sdlc._git(main, "diff", "--name-only", before, after, "--", "scripts"))
    )


def _push(home: Path, remote: str, ref: str) -> str | None:
    """Push one ref; why not, or None. The plugin's only push, called by publish, and by close and
    release when `git.push` names them. Never --force: a remote that has moved refuses, and that
    refusal is the answer. It never asks: no terminal prompt for credentials and stdin closed, so a
    remote that wants a password fails at once and is reported, rather than waiting on nobody."""
    made = subprocess.run(
        ["git", "-C", str(home), "push", "-q", remote, ref], capture_output=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )  # fmt: skip
    if made.returncode == 0:
        return None
    return made.stderr.strip() or made.stdout.strip() or f"exited {made.returncode}"


def _push_plan(home: Path, cfg: dict, point: str) -> dict:
    """Whether `point` (close or release) pushes, and what: `on`, the remote and branch, and the
    commits and issues `_unpushed()` reads, or `off_because` when `git.push` doesn't name it or
    there's no remote. A missing tracking ref leaves `unpushed` None: the push still goes."""
    remote = cfg["release"]["remote"]
    plan: dict = {"on": False, "remote": remote, "branch": cfg["git"]["base"]}
    if point not in cfg["git"]["push"]:
        plan["off_because"] = f"git.push doesn't name {point}"
    elif sdlc._git(home, "remote", "get-url", remote) is None:
        plan["off_because"] = f"no remote {remote!r}: set release.remote"
    else:
        plan["on"] = True
        plan["unpushed"] = sdlc._unpushed(home, cfg)
    return plan
