"""factory_records — the core's one reader of the files a factory run leaves in a change's folder.

`sdlc-factory` is optional, and the core never imports or runs `factory.py`: it reads only the
files a run leaves (its decision, ledger, rounds, gate records, step and landing records, costs and
sessions) and parses them with copies of `factory.py`'s own parsing. Every such copy the core holds
lives here, and nothing else in core opens one of those files its own way or spells its name
(`tests/test_modules.py`, which also pins the copies). `status`, the hand gate and `vet` read
through it in `sdlc.py`, and the board, close's measure step and the retrospective's `autonomy`
through `sdlc`'s binding, as `sdlc.factory_records.<name>`.

What moves here: a constant, regex or path copied from `factory.py`, under the name `factory.py`
gives it, so one test pins every name the two share (`test_every_shared_name_is_the_factorys`);
and a function that turns a record's text, or a change folder's record files, into fields. What
stays in `sdlc.py`: core's own rules over those fields (`needs_of()`, `column()`, `seen_stage()`,
`answered()`, `decide_step()`, `FACTORY_STOP_NEEDS`), the hand gate's runner and writer, and the
copies of what isn't a run's record (`factory.toml`'s slots and `[ui]`).

Pure, like `metrics.py`: loaded by path once, by `sdlc.py`, with no `sdlc` bound into it, no
subprocess and nothing done at load but defining names. It reads files on disk in a change folder.
A record that must come from git history (close's measure step reads the branch, the
retrospective a closed change's own commit) comes in through the caller's callables:
`show(rel) -> str | None` reads `<folder>/<rel>`, and `listing(rel) -> str` lists every path under
`<folder>/<rel>`, one a line, relative to the folder. The module never runs git.

Two readers of the ledger sit side by side, as they were before they moved: `reading()`, what
`status` and `needs_of()` read, and `card_reading()`, a board card's. Merging them would change a
card's fields; that is for a change that means to.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import re
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------- the run's records
#
# The files, by name: the approver's decision and the ledger in the folder, a builder's sessions.
DECISION_FILE = "decision.md"
LEDGER_FILE = "decisions.md"
# An escalated decision a restart kept, `decision-<n>.md` beside the current one: a past escalation.
ARCHIVE_RE = re.compile(r"^decision-(\d+)\.md$")
# The mends `agent` filed: `<role> <round>` for a build's, `<role> land-<n>` for a landing's.
MENDED = Path("runs") / "mended"
BUILDER_SESSIONS = Path("runs") / "builder.sessions"
SESSIONS = ".sessions"
# A Tier 2's spec-writer: its sessions, one id a line, each added as it starts, and the draft it
# returns, which waits there for the person's yes (`factory.py`'s `agent --task spec`).
SPEC_SESSIONS = Path("runs") / "spec-writer.sessions"
SPEC_DRAFT = Path("runs") / "spec-draft.md"

VERDICT_RE = re.compile(r"^VERDICT: (PASS|CHANGES)\s*$")
DECISION_RE = re.compile(r"^DECISION: (READY|ESCALATE)\s*$")
CHANGE_RE = re.compile(r"^\s*- CHANGE:\s*(.+?)\s*$")
LEDGER_RE = re.compile(r"^- \[( |x)\] (D\d+) \(([^,)]+), (blocking|default|look)\): (.+?)\s*$")
# The approver's reasons beyond the ledger, `- ESCALATED: gate: …` or `look: …` (any other word
# but `D<n>` a look), and the source `decisions` files a look line under; with the factory's
# `newest_round()`, what tells a current look line from history.
REASON_RE = re.compile(r"^\s*- ESCALATED:\s*([^\s:]+):\s*(.+?)\s*$")
REASON_KINDS = ("gate", "look")
LOOK_SOURCE_RE = re.compile(r"^approver round (\d+)$")
DECIDED = " → decided: "
# A line autopilot answered (216): ticked, never the person's answer, so every count keeps it
# apart, as `autopilot`. A copy of `factory.py`'s, pinned by a test.
DECIDED_AUTOPILOT = " → decided by autopilot: "
# The mark `factory.py decisions` ticks a default with when the approver settled it: never the
# person's answer, so no reader counts it as one.
SETTLED = " → settled by the approver: "
# A default a later one replaced, ticked by `decisions` (never the person's answer); the answer
# `/sdlc-factory:decide` writes when the person keeps a default; the one the landing writes on
# every default still open at its yes, which `KEPT_ANSWER` is a prefix of; and a look the person
# acknowledged as it stood, as the decide skill words it (core's own name: `factory.py` has none).
SUPERSEDED = " → superseded by "
KEPT_ANSWER = "the assumed default, confirmed"
CONFIRMED = "the assumed default, confirmed when landing"
LOOK_SEEN = "seen"
KEPT_RE = re.compile(r"^\s*- KEPT:\s*([a-z]+):\s*(.+?)\s*$")
DROPPED_RE = re.compile(r"^\s*- DROPPED:\s*([a-z]+):\s*(.+?)\s*$")
VERIFIED = "verified.md"
# The heading an escalation a run's rounds ran out on holds, in `decision.md`.
RECONSIDER = "## Reconsider the approach"
# An open box the ledger can't read: a problem, never an answered decision.
OPEN_BOX = "- [ ]"
GARBLED_LEDGER = "decisions.md: an open line that doesn't read as a decision"
# A reply or a decision with no answer `opening()` reads, worded as `factory.py`'s `_no_verdict()`
# and `NO_DECISION` word it.
NO_DECISION = (
    "decision.md holds no DECISION: READY or DECISION: ESCALATE the script reads (first, or the "
    "only answer it gives)"
)
# The reviewers a round's replies come from, in `costs.jsonl`'s `role`.
REVIEWERS = ("code", "security", "test", "behaviour", "ui", "ux", "docs")
# A red attempt of the factory's script gate, in `build/round-<N>.gate.md`.
GATE_FAIL_RE = re.compile(r"^Verdict: FAIL\s*$")
# A stopped run's record, which `factory.py verdicts --record` writes and removes.
STOPPED = Path("runs") / "stopped.md"
STOPPED_RE = re.compile(r"^STOPPED: (mend|rerun|ship|parked)\s*$")
NEXT_RE = re.compile(r"^NEXT: (.+?)\s*$")
PROBLEM_RE = re.compile(r"^- PROBLEM: (.+?)\s*$")
# The step a run's last `verdicts --record` read, and the longest an agent session can run: what
# `first_build()` reads to tell a builder writing `plan.md` right now from a stale run.
STEP = Path("runs") / "step.md"
STEP_RE = re.compile(r"^STEP: ([a-z]+)\s*$")
STUCK_RE = re.compile(r"^- STUCK: (.+?)\s*$")
UNTESTABLE_RE = re.compile(r"^\s*- UNTESTABLE:\s*(?!\s*(?i:none|n/?a)\.?\s*$)(.+?)\s*$")
ROUND_RE = re.compile(r"^ROUND: ?(\d*)\s*$")
LIMIT_RE = re.compile(r"^LIMIT: ?(\d*)\s*$")
REVIEWERS_RE = re.compile(r"^REVIEWERS: ?(.*?)\s*$")
# The depth the reading reviews at (`depth()`), from 175 on: a run never lightens, so its last
# record's is its deepest; a record without the line has none, never `light`.
DEPTH_RE = re.compile(r"^DEPTH: (full|light)\s*$")
SINCE_RE = re.compile(r"^SINCE: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$")
AFTER_RE = re.compile(r"^AFTER: ([a-z]+)\s*$")
AGENT_TIMEOUT = 3 * 3600
# A change parked on a host resource (222): `runs/parked.md`, which only `factory.py gate` writes,
# its key lines then `- NOTE:` lines. Copies of `factory.py`'s, pinned by name and over a table of
# cases (`tests/test_modules.py`): `status` and the board show it, and never vouch for it.
PARKED = Path("runs") / "parked.md"
PARKED_RE = re.compile(r"^PARKED: (gate)\s*$")
RESOURCE_RE = re.compile(r"^RESOURCE: (.+?)\s*$")
HOLDER_RE = re.compile(r"^HOLDER: (.+?)\s*$")
RETRY_RE = re.compile(r"^RETRY: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$")
DEADLINE_RE = re.compile(r"^DEADLINE: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$")
ATTEMPTS_RE = re.compile(r"^ATTEMPTS: (\d+)\s*$")
NOTE_RE = re.compile(r"^- NOTE: (.+?)\s*$")
# The steps that pause a run for the person, each recorded with `AFTER:`, the step it paused at.
PAUSES = ("decide", "upgrade", "spec")
# A run upgraded to Tier 2 part way: `build/round-<P>.upgraded.md`, round P the upgraded run's
# first, which `upgraded_build()` reads.
UPGRADED_FILE_RE = re.compile(r"^round-(\d+)\.upgraded\.md$")
# The step a landing is at, written by each landing command as it starts (`factory.py`'s
# `_record_land()`): a `stop`, and a train's `eject`, name the step it stopped after and why.
# `LAND_STOPS` are the steps the board and `status` read as a stop, and `LAND_STEPS` the steps the
# board's track places (its `LAND_AT`), which are `factory.py`'s.
LAND_STEP = Path("runs") / "land-step.md"
LAND_STOPS = ("stop", "eject")
LAND_STEPS = (
    "checks", "cases", "ship", "rebase", "stack", "wait", "resolve", "fix", "gate", "recheck",
    "review", "mend", "arbitrate", "close", "eject",
)  # fmt: skip
# A name a record from before the verifier became the arbiter holds, read as its name now: a role
# (`costs.jsonl`'s `role`, `runs/<role>.sessions`), a build step or a landing step. `factory.py`'s.
RENAMED = {"verifier": "arbiter", "verify": "arbitrate", "land-verify": "land-arbitrate"}
MOVES_RE = re.compile(r"^MOVES: ?(\d*)\s*$")
TRAIN_RE = re.compile(r"^TRAIN: (\d+) of (\d+)\s*$")
WAITS_RE = re.compile(r"^WAITS: (.+?)\s*$")
LAND_TIMES = Path("runs") / "land-times.jsonl"
COSTS = Path("runs") / "costs.jsonl"
# What each row of `COSTS` was for, the parts that bought nothing, and the record of a train's
# ejection or stop: `factory.py`'s, read by `spend_rows()`.
PURPOSES = ("spec", "build", "rework", "gate-fix", "mend", "rerun", "land")
WASTE = ("rework", "gate-fix", "mend", "rerun", "ejected", "dropped")
EJECTIONS = Path("runs") / "ejections.jsonl"
# Core's own record of the files `sdlc.py resolve` merged, read by `resolved_files()`.
CONFLICTS = "conflicts.md"
# A train change's record of its train (each gate it took part in, `GATE: <prefix> <verdict>
# <commit> <file>`) and the acceptance checks a landing ran, in the gate file's shape.
LAND_TRAIN = Path("runs") / "land-train.md"
TRAIN_GATE_RE = re.compile(r"^GATE: (\d+) (PASS|FAIL) ([0-9a-f]+) (\S+)\s*$")
LAND_ACCEPT = Path("build") / "land-accept.md"
# A fix the person asked for at landing, round <n>, as `factory.py`'s `land_ask_path()` places it,
# relative to the folder: core's own name, pinned to that function.
LAND_ASK_RE = re.compile(r"^build/land-(\d+)\.ask\.md$")
# The parts a row's spend lands in (`spend_rows()`), core's own: each purpose, what became of the
# change (`ejected`, `dropped`), and a row from before purposes (`untagged`), which is never waste.
PARTS = (*PURPOSES, "ejected", "dropped", "untagged")


def opening(lines: list[str], regex: re.Pattern) -> tuple[int, re.Match] | None:
    """A factory reply's answer line, `(index, match)`, or None: a copy of `factory.py`'s
    `opening()`, pinned to it over a shared table of cases."""
    if lines and (m := regex.match(lines[0])):
        return 0, m
    found = [(i, m) for i, line in enumerate(lines) if (m := regex.match(line))]
    if found and len({m.group(1) for _, m in found}) == 1:
        return found[0]
    return None


def no_verdict(n: int, role: str, kind: str = "round") -> str:
    return (
        f"reviews/{kind}-{n}/{role}.md holds no VERDICT: PASS or VERDICT: CHANGES the script "
        "reads (first, or the only answer it gives)"
    )


def read_stop(folder: Path) -> dict | None:
    """The stop a factory run recorded in its folder's `runs/stopped.md`: its way on (`ship`,
    `mend`, `rerun` or `parked`), the sentence saying it, and its problems as the factory worded
    them. None without a record. Never raises: a record that won't read is a stop whose one
    problem says so, since what it stands for is still a run waiting on the person."""
    path = folder / STOPPED
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return None
    except OSError as e:
        lines, why = [], str(e)
    else:
        why = f"{STOPPED.as_posix()} doesn't open with STOPPED: and its NEXT: line"
    way = STOPPED_RE.match(lines[0]) if lines else None
    nxt = [m.group(1) for m in map(NEXT_RE.match, lines) if m]
    if not way or not nxt:
        return {"way": None, "next": f"read {STOPPED.as_posix()}", "problems": [why]}
    found = [m.group(1) for m in map(PROBLEM_RE.match, lines) if m]
    return {"way": way.group(1), "next": nxt[0], "problems": found}


def read_park(text: str) -> dict | None:
    """`runs/parked.md`'s fields, or None when it doesn't open with `PARKED:` or lacks any key
    line: `step`, `round`, `resource`, `holder`, `since`, `retry`, `deadline` (stamps, as text),
    `attempts` and its `notes`. A copy of `factory.py`'s `read_park()`, pinned to it."""
    lines = text.splitlines()
    step = PARKED_RE.match(lines[0]) if lines else None
    if not step:
        return None

    def field(regex: re.Pattern) -> str | None:
        found = [m.group(1) for m in map(regex.match, lines) if m]
        return found[0] if found else None

    keys = {"round": ROUND_RE, "resource": RESOURCE_RE, "holder": HOLDER_RE, "since": SINCE_RE,
            "retry": RETRY_RE, "deadline": DEADLINE_RE, "attempts": ATTEMPTS_RE}  # fmt: skip
    out = {key: field(regex) for key, regex in keys.items()}
    if not all(out.values()):
        return None
    out.update(step=step.group(1), round=int(out["round"]), attempts=int(out["attempts"]))
    out["notes"] = [m.group(1) for m in map(NOTE_RE.match, lines) if m]
    return out


STAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def capped_park(park: dict, minutes: int) -> dict:
    """`park` with its deadline cut to `SINCE` plus `minutes`, the base branch's `[park]
    deadline`, and its retry to that deadline (229). A copy of `factory.py`'s `capped_park()`,
    which takes the config the minutes come from, pinned to it."""

    def when(stamp: str) -> datetime:
        return datetime.strptime(stamp, STAMP_FORMAT).replace(tzinfo=UTC)

    cap = when(park["since"]) + timedelta(minutes=minutes)
    deadline = min(when(park["deadline"]), cap)
    retry = min(when(park["retry"]), deadline)
    return {**park, "deadline": deadline.strftime(STAMP_FORMAT),
            "retry": retry.strftime(STAMP_FORMAT)}  # fmt: skip


def park(folder: Path, minutes: int) -> dict | None:
    """The park a factory run left in `folder` (`read_park()`), its deadline cut by the base
    branch's `[park] deadline`, `minutes` (`capped_park()`), as `verdicts` reads it, for `status`
    and the board; None without one or for one that won't read: the run's own `verdicts` reads
    that as a stop, which `runs/stopped.md` then shows. Never raises."""
    try:
        text = (folder / PARKED).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    found = read_park(text)
    return capped_park(found, minutes) if found else None


def read_land_stop(folder: Path) -> dict | None:
    """The stop a factory landing recorded in `folder`'s `runs/land-step.md`, a `stop` or a train's
    `eject` (`LAND_STOPS`, as the board reads them): the step it stopped after (`after`, None when
    the record names none) and its problems as the factory worded them, the plain line first. None
    for a landing under way, no record, or one that won't read: a landing is the factory's until
    its record says it stopped, so `status` never says it did on a guess; the board reads a
    garbled record as a problem of its own."""
    try:
        lines = (folder / LAND_STEP).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    lines = lines.splitlines()
    step = STEP_RE.match(lines[0]) if lines else None
    if not step or step.group(1) not in LAND_STOPS:
        return None
    after = [m.group(1) for m in map(AFTER_RE.match, lines) if m]
    return {
        "after": after[0] if after else None,
        "problems": [m.group(1) for m in map(PROBLEM_RE.match, lines) if m],
    }


def landing(folder: Path, stage: str | None) -> tuple[bool, str | None]:
    """Whether a factory landing is in flight in `folder`, and the problem its record makes: at
    `test` or `shipped`, a `runs/land-step.md` opening with a `STEP:` line that names a step of
    the landing's track (`LAND_STEPS`) other than a stop (`LAND_STOPS`). A record that doesn't open
    with `STEP:` is the board's problem, worded as it words it; no record, or one at any other
    stage, is neither. Never raises. The board and `status` both read it, so `column()` sees one
    answer."""
    if stage not in ("test", "shipped"):
        return False, None
    try:
        text = (folder / LAND_STEP).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False, None
    lines = text.splitlines()
    step = STEP_RE.match(lines[0]) if lines else None
    if not step:
        return False, f"{LAND_STEP.as_posix()} doesn't open with STEP:"
    name = RENAMED.get(step.group(1), step.group(1))
    return name in LAND_STEPS and name not in LAND_STOPS, None


def first_build(folder: Path) -> bool:
    """Whether a factory run's first build is under way in `folder`, so its builder is writing
    `plan.md` now: a builder session started less than `AGENT_TIMEOUT` ago (no session outlives
    it), no builder report yet, no stop recorded, and `runs/step.md` absent (a fresh run builds
    before its first `verdicts --record`) or naming `build` at round 1. Never raises: a file that
    won't read is no live build, so `vet` reports as it would without the factory."""
    try:
        started = (folder / BUILDER_SESSIONS).stat().st_mtime
        if time.time() - started >= AGENT_TIMEOUT:
            return False
        if any((folder / "build").glob("round-*.md")) or (folder / STOPPED).exists():
            return False
        step = folder / STEP
        if not step.exists():
            return True
        lines = step.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    first = STEP_RE.match(lines[0]) if lines else None
    rounds = [m.group(1) for m in map(ROUND_RE.match, lines) if m]
    return bool(first) and first.group(1) == "build" and (rounds or [""])[0] in ("", "1")


def upgraded_build(folder: Path) -> bool:
    """Whether a factory run upgraded to Tier 2 is building its first round, P, in `folder`, so
    its resumed builder is rewriting `plan.md` now: `first_build()`'s rule for round P. An upgrade
    record for P, no `build/round-<P>.md`, no stop recorded, and `runs/step.md` naming `build` at
    round P, written less than `AGENT_TIMEOUT` ago (the builder is resumed, so its session file is
    as old as round 1). Never raises: a file that won't read is no live build."""
    try:
        rounds = [
            int(m.group(1))
            for m in (UPGRADED_FILE_RE.match(p.name) for p in (folder / "build").iterdir())
            if m
        ]
        if not rounds:
            return False
        n = max(rounds)
        if (folder / "build" / f"round-{n}.md").exists() or (folder / STOPPED).exists():
            return False
        step = folder / STEP
        if time.time() - step.stat().st_mtime >= AGENT_TIMEOUT:
            return False
        lines = step.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    first = STEP_RE.match(lines[0]) if lines else None
    found = [m.group(1) for m in map(ROUND_RE.match, lines) if m]
    return bool(first) and first.group(1) == "build" and (found or [""])[0] == str(n)


def builder_started(folder: Path) -> float | None:
    """When the run's first builder session started (`runs/builder.sessions`' mtime), or None
    without one."""
    path = folder / BUILDER_SESSIONS
    return path.stat().st_mtime if path.is_file() else None


def specifying(folder: Path) -> bool:
    """Whether a run's spec is under way: its draft waits for the person's yes
    (`runs/spec-draft.md`), an upgraded run's last reading named `spec` (`runs/step.md`), or the
    newest spec-writer session has no `runs/costs.jsonl` row yet, so it hasn't returned (a first
    draft records no step). A returned session whose draft is gone is none. Never raises."""
    try:
        if (folder / SPEC_DRAFT).is_file():
            return True
        path = folder / STEP
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        if (read_step(text) or {}).get("step") == "spec":
            return True
        path = folder / SPEC_SESSIONS
        ids = path.read_text(encoding="utf-8", errors="replace").split() if path.is_file() else []
        if not ids:
            return False
        path = folder / COSTS
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    except OSError:
        return False
    return ids[-1] not in {row.get("session") for row in _json_rows(text)}


def newest_round(folder: Path) -> int:
    """The newest round built or reviewed: a copy of `factory.py`'s `newest_round()` (and its
    `build_round()`), pinned to it by a test."""
    names = [p.stem[6:] for p in (folder / "build").glob("round-*.md")]
    built = max((int(n) for n in names if n.isdigit()), default=0)
    reviewed = [
        int(p.name[6:]) for p in (folder / "reviews").glob("round-*")
        if p.is_dir() and p.name[6:].isdigit()
    ]  # fmt: skip
    return max([built, *reviewed])


def reasons(lines: list[str]) -> list[dict]:
    """A decision's `gate` and `look` reasons, as `factory.py`'s `escalation_reasons()` reads them
    (a test pins the two): each `{"kind", "text"}`, in order."""
    found = []
    for line in lines:
        m = REASON_RE.match(line)
        if not m or re.fullmatch(r"D\d+", m.group(1)):
            continue
        word, text = m.group(1), m.group(2)
        if word in REASON_KINDS:
            found.append({"kind": word, "text": text})
        else:
            found.append({"kind": "look", "text": f"{word}: {text}"})
    return found


def reading(folder: Path) -> dict:
    """What `needs_of()` reads from a factory run's folder, as the board reads it: the approver's
    decision, whether it asks to reconsider the approach, the ledger's open blocking (`pending`)
    and default (`assumed`) decisions, its count of decision lines (a default the approver settled
    is none: it is no answer of the person's; a `look` line is none either), and `problems`: an
    open box the ledger can't read, or a file that won't. `reasons` are the current decision's
    `gate` and `look` reasons, each with whether it is `filed` (a look with a current ledger line)
    and `cleared` (a look acknowledged; a gate never here: `needs_of()` reads the hand gate), and
    `looks` the current look lines still open, and `specifying`, whether its spec is under way
    (`specifying()`). A look line is current only while it names the newest round and the
    current decision gives it word for word. Never raises."""
    found = {"decision": None, "reconsider": False, "pending": [], "assumed": [],
             "ledger_lines": 0, "problems": [], "reasons": [], "looks": [],
             "specifying": False}  # fmt: skip
    lines: list[str] = []
    try:
        path = folder / DECISION_FILE
        if path.is_file():
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            answer = opening(lines, DECISION_RE)
            found["decision"] = answer[1].group(1) if answer else None
            found["reconsider"] = RECONSIDER in [line.strip() for line in lines]
        path = folder / LEDGER_FILE
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    except OSError as e:
        found["problems"].append(str(e))
        return found
    given = reasons(lines)
    looked = {r["text"] for r in given if r["kind"] == "look"}
    newest = f"approver round {newest_round(folder)}" if looked else None
    garbled, filed, seen = False, set(), set()
    for line in text.splitlines():
        m = LEDGER_RE.match(line)
        garbled = garbled or not m and line.startswith("- [ ]")
        if not m:
            continue
        if m.group(4) == "look":
            words = m.group(5).partition(DECIDED)[0].strip()
            if m.group(3) != newest or words not in looked:
                continue  # history: an older decision's, or a restart's
            filed.add(words)
            if m.group(1) == "x":
                seen.add(words)
            else:
                found["looks"].append({"id": m.group(2), "by": m.group(3), "text": words})
            continue
        found["ledger_lines"] += SETTLED not in line
        if m.group(1) == " ":
            item = {"id": m.group(2), "by": m.group(3), "text": m.group(5)}
            found["pending" if m.group(4) == "blocking" else "assumed"].append(item)
    found["reasons"] = [
        r | {"filed": r["kind"] == "gate" or r["text"] in filed,
             "cleared": r["kind"] == "look" and r["text"] in seen}
        for r in given
    ]  # fmt: skip
    if garbled:
        found["problems"].append(GARBLED_LEDGER)
    found["specifying"] = specifying(folder)
    return found


def card_reading(folder: Path, problems: list[str]) -> dict:
    """What a factory run left, as a board card shows it: its rounds, the approver's decision, the
    ledger, the cost, the last acceptance run's verdict and whether its spec is under way
    (`specifying()`), each file that won't parse a line added to `problems`."""
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
            answer = opening(lines, VERDICT_RE)
            if not answer:
                problems.append(no_verdict(n, file.stem))
                continue
            at, m = answer
            changes = sum(1 for line in lines[at + 1 :] if CHANGE_RE.match(line))
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
    path = folder / DECISION_FILE
    if path.is_file():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        answer = opening(lines, DECISION_RE)
        m = answer[1] if answer else None
        decision = m.group(1) if m else None
        reconsider = RECONSIDER in [line.strip() for line in lines]
        if not m:
            problems.append(NO_DECISION)
    pending, assumed, ledger_lines, garbled = [], [], 0, False
    path = folder / LEDGER_FILE
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        m = LEDGER_RE.match(line)
        garbled = garbled or not m and line.startswith(OPEN_BOX)
        # A look line is the approver's reason, read with the decision (`reading()`).
        if m and m.group(4) == "look":
            continue
        ledger_lines += bool(m) and SETTLED not in line
        if m and m.group(1) == " ":
            item = {"id": m.group(2), "by": m.group(3), "text": m.group(5)}
            (pending if m.group(4) == "blocking" else assumed).append(item)
    if garbled:
        problems.append(GARBLED_LEDGER)
    # The approver's `gate` and `look` reasons and the look lines still open, as `status` reads
    # them: `reading()` itself, so the card and `status` can't say two things.
    read = reading(folder)
    return {
        "rounds": rounds, "built": built, "decision": decision, "pending": pending,
        "assumed": assumed, "cost": cost(folder), "reconsider": reconsider,
        "ledger_lines": ledger_lines, "reasons": read["reasons"], "looks": read["looks"],
        "accept": accept_verdict(folder), "specifying": read["specifying"],
    }  # fmt: skip


def accept_verdict(folder: Path) -> str | None:
    """The verdict of the last attempt in the landing's acceptance record (`LAND_ACCEPT`), `PASS`
    or `FAIL`; None before one ran, or when its last attempt has no verdict line."""
    try:
        attempts = gate_attempts(folder / LAND_ACCEPT)
    except OSError:
        return None
    return attempts[-1]["verdict"] if attempts else None


def reviewed(folder: Path, n: int) -> int:
    """How many replies in `reviews/round-<n>/` hold a verdict `opening()` reads, `verified.md`
    aside."""
    count = 0
    for file in (folder / "reviews" / f"round-{n}").glob("*.md"):
        if file.name == VERIFIED:
            continue
        lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
        count += opening(lines, VERDICT_RE) is not None
    return count


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
        "stuck": [m.group(1) for m in map(STUCK_RE.match, lines) if m],
        "untestable": [m.group(1) for m in map(UNTESTABLE_RE.match, lines) if m],
        "depth": field(DEPTH_RE),
    }  # fmt: skip


def read_land_step(text: str) -> dict | None:
    """`runs/land-step.md`'s fields, as `factory.py`'s `read_land_step()` reads them (a test pins
    the two), or None when it doesn't open with a `STEP:` line."""
    lines = text.splitlines()
    step = STEP_RE.match(lines[0]) if lines else None
    if not step:
        return None

    def field(regex: re.Pattern) -> str | None:
        found = [m.group(1) for m in map(regex.match, lines) if m]
        return found[0] if found else None

    rnd, moves, limit = field(ROUND_RE), field(MOVES_RE), field(LIMIT_RE)
    train = next((m for m in map(TRAIN_RE.match, lines) if m), None)
    return {
        "step": step.group(1), "round": int(rnd) if rnd else None,
        "moves": int(moves) if moves else None, "limit": int(limit) if limit else None,
        "since": field(SINCE_RE), "after": field(AFTER_RE),
        "problems": [m.group(1) for m in map(PROBLEM_RE.match, lines) if m],
        "train": {"k": int(train.group(1)), "n": int(train.group(2))} if train else None,
        "waits": field(WAITS_RE),
    }  # fmt: skip


def read_land_times(text: str) -> list[dict]:
    """`runs/land-times.jsonl`'s rows, as `factory.py`'s `read_land_times()` reads them (a test
    pins the two over a shared table): each `{"step", "round", "seconds"}`, a row that won't read
    passed over."""
    rows = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or not isinstance(row.get("step"), str):
            continue
        rnd, seconds = row.get("round"), row.get("seconds")
        if rnd is not None and (not isinstance(rnd, int) or isinstance(rnd, bool)):
            continue
        if not isinstance(seconds, int | float) or isinstance(seconds, bool) or seconds < 0:
            continue
        rows.append({"step": row["step"], "round": rnd, "seconds": float(seconds)})
    return rows


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


# ---------------------------------------------------------------- a run's files in history
#
# Close's measure step reads them on the change's branch, through the caller's `show` and
# `listing` (see the docstring); the board's typical times read the gate files at a `Close`
# commit's parent with its own walk.


def run_counts(show, listing) -> dict | None:
    """What the factory left in the change's commit, as counts: review rounds, each reviewer's
    `CHANGES` verdicts, change requests and requests the arbiter dropped (`dropped`, from each
    round's `verified.md`), the approver's decision, the ledger's blocking and default decisions,
    the defaults still open and those the approver settled, and the script gate's red attempts
    (`gate_fail`, only when a gate file exists). None for a change built by hand (no
    `decision.md`)."""
    decision = show(DECISION_FILE)
    if decision is None:
        return None
    answer = opening(decision.splitlines(), DECISION_RE)
    m = answer[1] if answer else None
    listed = listing("reviews") or ""
    rounds: set[str] = set()
    reviews: dict[str, dict] = {}
    for path in listed.splitlines():
        parts = path.split("/")  # reviews, round-N, role.md
        if len(parts) != 3 or not parts[1].startswith("round-") or not parts[2].endswith(".md"):
            continue
        rounds.add(parts[1])
        lines = (show(path) or "").splitlines()
        if parts[2] == VERIFIED:
            # The arbiter's answers, counted on the reviewer whose request it dropped.
            for m in filter(None, map(DROPPED_RE.match, lines)):
                r = reviews.setdefault(m.group(1), {"changes": 0, "requests": 0})
                r["dropped"] = r.get("dropped", 0) + 1
            continue
        answer = opening(lines, VERDICT_RE)
        at, verdict = answer if answer else (0, None)
        r = reviews.setdefault(parts[2].removesuffix(".md"), {"changes": 0, "requests": 0})
        r["changes"] += int(bool(verdict) and verdict.group(1) == "CHANGES")
        r["requests"] += sum(1 for line in lines[at + 1 :] if CHANGE_RE.match(line))
    if any(p.endswith(f"/{VERIFIED}") for p in listed.splitlines()):
        # A run with an arbiter says `dropped` for every reviewer, 0 included; one from before
        # it says nothing, so its trailer reads as unknown there, never as nothing dropped.
        for r in reviews.values():
            r.setdefault("dropped", 0)
    ledger = show(LEDGER_FILE) or ""
    entries = [e for e in map(LEDGER_RE.match, ledger.splitlines()) if e]
    defaults = [e for e in entries if e.group(4) == "default"]
    found = {
        "rounds": len(rounds),
        "reviews": reviews,
        "decision": m.group(1) if m else None,
        "blocking": sum(1 for e in entries if e.group(4) == "blocking"),
        "defaults": len(defaults),
        "defaults_open": sum(1 for e in defaults if e.group(1) == " "),
        "defaults_settled": sum(1 for e in defaults if SETTLED in e.group(5)),
    }
    # The script gate's red attempts, known only for a run that had the gate: one from before it,
    # or with no gate configured, says nothing, never 0.
    built = listing("build") or ""
    gates = [p for p in built.splitlines() if p.endswith(".gate.md")]
    if gates:
        found["gate_fail"] = sum(
            1 for p in gates for line in (show(p) or "").splitlines() if GATE_FAIL_RE.match(line)
        )
    return found


def autonomy_counts(show, listing) -> dict | None:
    """How often the run needed the person, from what it left in the change's commit: the
    escalations (the current decision and each restart's archive, `ARCHIVE_RE`), each ledger line
    by its mark, and the mends (`MENDED`), a build's apart from a landing's. A decision file whose
    answer `opening()` can't read is listed in `unread` and never counted. None for a change built
    by hand (no `decision.md`). Never raises."""
    decision = show(DECISION_FILE)
    if decision is None:
        return None
    archives = sorted(
        path
        for path in (listing("") or "").splitlines()
        if "/" not in path and ARCHIVE_RE.match(path)
    )
    escalations, unread = 0, []
    for rel, text in [(DECISION_FILE, decision), *((p, show(p)) for p in archives)]:
        answer = opening((text or "").splitlines(), DECISION_RE)
        if answer is None:
            unread.append(rel)
        elif answer[1].group(1) == "ESCALATE":
            escalations += 1
    defaults = dict.fromkeys(
        ("kept", "changed", "confirmed", "settled", "superseded", "open", "autopilot"), 0
    )
    blocking = {"answered": 0, "open": 0, "autopilot": 0}
    looks = {"seen": 0, "checked": 0, "open": 0, "autopilot": 0}
    for e in filter(None, map(LEDGER_RE.match, (show(LEDGER_FILE) or "").splitlines())):
        kind, text = e.group(4), e.group(5)
        answer = text.split(DECIDED, 1)[1].strip() if DECIDED in text else ""
        if DECIDED_AUTOPILOT in text and e.group(1) == "x":
            # Autopilot's call, never the person's answer nor an override (216 R23).
            {"default": defaults, "blocking": blocking}.get(kind, looks)["autopilot"] += 1
            continue
        if kind == "default":
            # Only a default carries `SUPERSEDED` or `SETTLED`: `factory.py decisions` writes those
            # marks on defaults alone, so a blocking or look line never needs the check.
            mark = (
                "superseded" if SUPERSEDED in text
                else "settled" if SETTLED in text
                else "open" if e.group(1) == " "
                else "confirmed" if answer == CONFIRMED
                else "kept" if answer == KEPT_ANSWER
                else "changed"
            )  # fmt: skip
            defaults[mark] += 1
        elif kind == "blocking":
            blocking["open" if e.group(1) == " " else "answered"] += 1
        else:
            mark = "open" if e.group(1) == " " else "seen" if answer == LOOK_SEEN else "checked"
            looks[mark] += 1
    mends = {"build": 0, "landing": 0}
    for line in (show(MENDED.as_posix()) or "").splitlines():
        if re.fullmatch(r"\S+ \d+", line):
            mends["build"] += 1
        elif re.fullmatch(r"\S+ land-\d+", line):
            mends["landing"] += 1
    return {
        "escalations": escalations, "unread": unread, "blocking": blocking,
        "defaults": defaults, "looks": looks, "mends": mends,
    }  # fmt: skip


def resolved_files(text: str) -> list[str]:
    """Every file a change's `conflicts.md` (`CONFLICTS`, core's own record, which `sdlc.py
    resolve` writes) says a resolution merged, each once, in order: its `- ` lines. The one rule
    `sdlc.py`'s `conflicts_resolved()` and `pipeline_counts()` both read it by."""
    return list(dict.fromkeys(ln[2:].strip() for ln in text.splitlines() if ln.startswith("- ")))


def pipeline_counts(show, listing) -> dict | None:
    """The pipeline's raw figures from what a run left in the change's commit, for the
    retrospective's `pipeline` (175): `gates`, each gate attempt (`gate_kind()`: a round's or a
    landing's, never the hand gate's) as its `kind`, `seconds`, `waited` and `verdict`; `builds`,
    each round gate file with attempts, whether any failed; `landed`, whether `LAND_STEP` exists,
    and `moves`, its last `MOVES:`; `ejections`, `EJECTIONS`' rows by cause; `train_gates`, each
    `GATE:` line of `LAND_TRAIN` as `(prefix, verdict, commit, file)`; `accepts`, the attempts in
    `LAND_ACCEPT`; `resolves`, the `resolve` rows of `LAND_TIMES`; `conflicts`, the files
    `CONFLICTS` names; and `depth`, `STEP`'s `DEPTH:`. A figure no record holds is None or empty,
    never a zero made up. None for a change built by hand (no `decision.md`). Never raises."""
    if show(DECISION_FILE) is None:
        return None
    gates, builds = [], []
    for path in sorted((listing("build") or "").splitlines()):
        parts = path.split("/")
        kind = gate_kind(parts[1]) if len(parts) == 2 else None
        if kind is None:
            continue
        attempts = read_gate_attempts(show(path) or "")
        gates += [
            {"kind": kind, "seconds": a["seconds"], "waited": a["waited"], "verdict": a["verdict"]}
            for a in attempts
        ]
        if kind == "round" and attempts:
            builds.append(any(a["verdict"] == "FAIL" for a in attempts))
    step_text = show(LAND_STEP.as_posix())
    land = read_land_step(step_text or "")
    ejections: dict[str, int] = {}
    for row in _json_rows(show(EJECTIONS.as_posix()) or ""):
        cause = str(row.get("cause") or "refusal")
        ejections[cause] = ejections.get(cause, 0) + 1
    train = [
        (int(m.group(1)), m.group(2), m.group(3), m.group(4))
        for m in map(TRAIN_GATE_RE.match, (show(LAND_TRAIN.as_posix()) or "").splitlines())
        if m
    ]
    step = read_step(show(STEP.as_posix()) or "")
    return {
        "gates": gates, "builds": builds, "landed": step_text is not None,
        "moves": land["moves"] if land else None, "ejections": ejections, "train_gates": train,
        "accepts": len(read_gate_attempts(show(LAND_ACCEPT.as_posix()) or "")),
        "resolves": sum(
            1 for r in read_land_times(show(LAND_TIMES.as_posix()) or "") if r["step"] == "resolve"
        ),
        "conflicts": len(resolved_files(show(CONFLICTS) or "")),
        "depth": step["depth"] if step else None,
    }  # fmt: skip


def session_roles(show, listing) -> dict[str, str]:
    """The sessions the factory ran as its agents, by session id, from the change's
    `runs/<role>.sessions`: one id a line, written by `factory.py agent`, a role from before read
    as its name now (`RENAMED`). A transcript names no `--agent` role, so this is how measuring
    tells a builder's session from the person's."""
    roles: dict[str, str] = {}
    for path in (listing("runs") or "").splitlines():
        parts = path.split("/")
        if len(parts) != 2 or not parts[1].endswith(SESSIONS):
            continue
        role = parts[1].removesuffix(SESSIONS)
        for line in (show(path) or "").splitlines():
            if line.strip():
                roles[line.strip()] = RENAMED.get(role, role)
    return roles


def session_models(show) -> dict[str, str]:
    """The model each factory session ran on, by session id, from the change's
    `runs/costs.jsonl`, which `factory.py agent` appends a row to for every run. A line that
    doesn't parse, or names no session or model, is skipped; no file gives none."""
    models: dict[str, str] = {}
    for line in (show(COSTS.as_posix()) or "").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        model = row.get("model") if isinstance(row, dict) else None
        if isinstance(row, dict) and isinstance(row.get("session"), str) and isinstance(model, str):
            models[row["session"]] = model
    return models


def gate_kind(name: str) -> str | None:
    """Which gate a file in `build/` records: `round` for a round's script gate
    (`round-<N>.gate.md`), `land` for a landing's (`land-<N>.gate.md`), else None."""
    if not name.endswith(".gate.md"):
        return None
    return next((k for k in ("round", "land") if name.startswith(f"{k}-")), None)


def gate_seconds(text: str) -> list[float]:
    """Every attempt's `Seconds:` in a gate record's text."""
    return [float(m.group(1)) for m in map(SECONDS_RE.match, text.splitlines()) if m]


# The factory's run files' times (`factory.py`'s `_utc_now()`), read with this copy of its format.
RUN_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _run_time(value: object) -> datetime | None:
    try:
        return datetime.strptime(value, RUN_TIME_FORMAT).replace(tzinfo=UTC)
    except (TypeError, ValueError):
        return None


def _json_rows(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def timed_rows(text: str) -> list[tuple[datetime, datetime, str]]:
    """`runs/costs.jsonl`'s rows that say when they ran, as `(started, ended, role)`, in order:
    `record_cost()`'s `started` and `ended`. A row without them, or out of order, is passed
    over."""
    out = []
    for row in _json_rows(text):
        start, end = _run_time(row.get("started")), _run_time(row.get("ended"))
        if start and end and start <= end:
            out.append((start, end, str(row.get("role") or "")))
    return out


def ejections(show) -> list[dict]:
    """`runs/ejections.jsonl`'s rows, read through `show`, in order: each time a train put the
    change back, `{"at", "land", "cause", "train"}` (`train`, the train's `began`, from 180 on). A
    line that doesn't parse as an object is passed over."""
    return _json_rows(show(EJECTIONS.as_posix()) or "")


def land_asks(listing) -> int:
    """How many fixes the person asked for at landing: the change's `build/land-<n>.ask.md`
    files (`LAND_ASK_RE`), read through `listing`."""
    return sum(1 for path in (listing("build") or "").splitlines() if LAND_ASK_RE.match(path))


def spend_rows(show, dropped: bool = False) -> dict:
    """Each agent run's spend in a change's `runs/costs.jsonl`, read through `show`, in order:
    `{"rows": [...], "unknown": n, "untagged": n}`, each row its `usd`, `minutes`, `role`,
    `model`, `session` and `part` (one of `PARTS`).

    A row's `cost_usd` is its session's running total across `--resume`, so its `usd` is that
    total less the highest an earlier row of the session reported, floored at 0; a row with no
    cost has `usd` None and counts in `unknown`, and the next that reports one carries its spend.
    Its part, in this order: `untagged` with no purpose (never waste); `dropped` for every row of a
    `dropped` change; `ejected` for a landing's run (`land`) that ended at or before an ejection
    in `runs/ejections.jsonl`; else its purpose. A row naming no session is skipped, as `cost()`
    skips it."""
    ejected_at = [t for t in (_run_time(r.get("at")) for r in ejections(show)) if t]
    highest: dict[str, float] = {}
    rows, unknown, untagged = [], 0, 0
    for row in _json_rows(show(COSTS.as_posix()) or ""):
        session = row.get("session")
        if not isinstance(session, str):
            continue
        total = row.get("cost_usd")
        if isinstance(total, int | float) and not isinstance(total, bool):
            usd = round(max(0.0, total - highest.get(session, 0.0)), 6)
            highest[session] = max(highest.get(session, 0.0), total)
        else:
            usd, unknown = None, unknown + 1
        ended = _run_time(row.get("ended"))
        if row.get("purpose") not in PURPOSES:
            part, untagged = "untagged", untagged + 1
        elif dropped:
            part = "dropped"
        elif row.get("land") is not None and ended and any(ended <= at for at in ejected_at):
            part = "ejected"
        else:
            part = row["purpose"]
        ms = row.get("duration_ms")
        minutes = ms / 60000 if isinstance(ms, int | float) and not isinstance(ms, bool) else 0.0
        rows.append({
            "usd": usd, "minutes": round(minutes, 4), "role": str(row.get("role") or "unknown"),
            "model": str(row.get("model") or "unknown"), "session": session, "part": part,
        })  # fmt: skip
    return {"rows": rows, "unknown": unknown, "untagged": untagged}


def land_sinces(text: str) -> list[datetime]:
    """When each landing step in `runs/land-times.jsonl` began (`_record_land()`'s `since`)."""
    return [t for t in (_run_time(r.get("since")) for r in _json_rows(text)) if t]


# ---------------------------------------------------------------- the gate record
#
# `sdlc.py gate` records a hand gate's attempt in the change's `build/gate.md`, in the shape
# `factory.py gate` writes `build/round-<N>.gate.md`, so the board and status read both alike.
CLONE_MARK = "<path-to-clone>"
HOME_MARK = "<home>"
TMP_MARK = "<tmp>"
USER_MARK = "<user>"
ATTEMPT_VERDICT_RE = re.compile(r"^Verdict: (PASS|FAIL)\s*$")
BUILD_RE = re.compile(r"^Build: ([0-9a-f]+)\s*$")
SECONDS_RE = re.compile(r"^Seconds: (\d+(?:\.\d+)?)\s*$")
# The slot wait before the attempt, from 175 on: an attempt without it has no wait, never 0.
WAITED_RE = re.compile(r"^Waited: (\d+(?:\.\d+)?)\s*$")
# The heading the gate's output tail follows, each of its lines indented by four spaces.
TAIL_RE = re.compile(r"^Last \d+ lines of its output:\s*$")
# The record, in the change's folder: beside the factory's round files, and matched by none of
# their readers (`round-*`, `*.gate.md`).
HAND_GATE = Path("build") / "gate.md"


# The factory's records ledger, in the git common dir: one line for each version of a gate,
# build or accept record a script wrote, the factory reading a record as a verdict only while a
# line vouches for it (199). `sdlc.py gate` appends the hand gate's line through these copies of
# `factory.py`'s `RECORDS_LEDGER`, `RECORDS_LOCK`, `_record_digest()` and `_ledger_line()`,
# pinned by `tests/test_records_ledger.py`; core never reads the ledger to decide anything but
# whether the hand gate may append to its own record.
RECORDS_LEDGER = "sdlc-factory-records.jsonl"
RECORDS_LOCK = "sdlc-factory-records.lock"


def record_digest(text: str) -> str:
    """A record's hash: sha256 of its text with `\\r\\n` read as `\\n`."""
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def ledger_line(change: str, record: str, text: str) -> str:
    """The ledger's line for one version of `record` (its path from the change's folder, POSIX)
    in change folder `change`."""
    row = {"change": change, "record": record, "sha256": record_digest(text)}
    return json.dumps(row) + "\n"


def vouched_in(ledger: Path, change: str, record: str, text: str) -> bool:
    """Whether `ledger` holds the line for this version of the record, as `factory.py`'s
    `vouched()` reads it: a missing or unreadable ledger vouches nothing, a garbled line is
    skipped."""
    want = json.loads(ledger_line(change, record, text))
    try:
        lines = ledger.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    for line in lines:
        try:
            if json.loads(line) == want:
                return True
        except ValueError:
            continue
    return False


def gate_attempts(path: Path) -> list[dict]:
    """A gate record's attempts on disk (`read_gate_attempts()`), [] without the file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return []
    return read_gate_attempts(text)


def read_gate_attempts(text: str) -> list[dict]:
    """A gate record's attempts, oldest first, each its verdict, build, exit, seconds and slot
    wait (`waited`, None for an attempt from before the `Waited:` line), the command it ran
    (`command`, None before the `Command:` line) and its output's tail, unindented (`tail`, [] for
    none), read by line as `factory.py`'s `read_gate_file()` reads one: the output is indented,
    so a line of it never reads as the record's."""
    attempts: list[dict] = []
    in_tail = False
    for line in text.splitlines():
        if line.startswith("## Attempt "):
            attempts.append(
                {"verdict": None, "build": None, "exit": None, "seconds": None, "waited": None,
                 "command": None, "tail": []}
            )  # fmt: skip
            in_tail = False
        elif in_tail and line.startswith("    "):
            attempts[-1]["tail"].append(line[4:])
        elif attempts and line.startswith("Command: "):
            attempts[-1]["command"] = line[len("Command: ") :].strip()
        elif attempts and TAIL_RE.match(line):
            in_tail = True
        elif attempts and (m := ATTEMPT_VERDICT_RE.match(line)):
            attempts[-1]["verdict"] = m.group(1)
        elif attempts and (m := BUILD_RE.match(line)):
            attempts[-1]["build"] = m.group(1)
        elif attempts and line.startswith("Exit: "):
            attempts[-1]["exit"] = line[len("Exit: ") :].strip()
        elif attempts and (m := SECONDS_RE.match(line)):
            attempts[-1]["seconds"] = float(m.group(1))
        elif attempts and (m := WAITED_RE.match(line)):
            attempts[-1]["waited"] = float(m.group(1))
    return attempts


def _login() -> str | None:
    """The login name, as pytest names its temp folder by it; None when the platform can't say.
    A copy of `factory.py`'s `_login()`."""
    try:
        return getpass.getuser() or None
    except (OSError, KeyError, ImportError):
        return None


def placeholders(text: str, root: Path, main: Path) -> str:
    """`text` with the main checkout's root (`main`, which the caller reads from git), then
    `root` when it lies elsewhere, written as `CLONE_MARK`, then the home directory as `HOME_MARK`
    and the temp directory as `TMP_MARK`: in that order, so a checkout under the home directory
    reads `<path-to-clone>/…`, never `<home>/…`, and a home under the temp directory `<home>/…`.
    Each path is matched as given and resolved (macOS prints `/private/var` for `/var`), and in
    its POSIX form too, only as a whole path: never inside a longer one. Then the login name,
    where no letter or digit borders it inside a path a mark begins, is `USER_MARK`, and never in
    prose. Last, each shape the repo's scan refuses is its placeholder (`DEFUSE`), and each local
    term `TERM_MARK`. A copy of `factory.py`'s `_placeholders()`, pinned to it by a test: the
    record is committed with the change, and a machine's layout never reaches its history."""
    for path, mark in (
        (main, CLONE_MARK),
        (root, CLONE_MARK),
        (Path.home(), HOME_MARK),
        (Path(tempfile.gettempdir()), TMP_MARK),
    ):
        forms = {str(path), path.as_posix(), str(path.resolve()), path.resolve().as_posix()}
        for form in sorted(forms - {"", "/", "."}, key=len, reverse=True):
            text = re.sub(rf"(?<![\w.-]){re.escape(form)}(?![\w-])", mark, text)
    if login := _login():
        name = re.compile(rf"(?<![A-Za-z0-9]){re.escape(login)}(?![A-Za-z0-9])")
        marked = "|".join(re.escape(m) for m in (CLONE_MARK, HOME_MARK, TMP_MARK))
        text = re.sub(rf"(?:{marked})[^\s'\"]*", lambda m: name.sub(USER_MARK, m[0]), text)
    for shape, mark in DEFUSE:
        text = re.sub(shape, mark, text, flags=re.IGNORECASE)
    for term in _terms(main):
        text = re.sub(term, TERM_MARK, text, flags=re.IGNORECASE)
    return text


def _terms(home: Path) -> list[str]:
    """The regexes in the main checkout's `TERMS_FILE`, one a line, blank lines and `#` comments
    skipped, and a line that isn't a regex left out. A copy of `factory.py`'s `_terms()`, pinned
    to it by `tests/test_hand_gate.py`."""
    path = home / TERMS_FILE
    try:
        lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    except (OSError, UnicodeDecodeError):
        return []
    terms = []
    for line in (line.strip() for line in lines):
        try:
            if line and not line.startswith("#") and re.compile(line):
                terms.append(line)
        except re.error:
            continue
    return terms


# The shapes the repo's own scan refuses, each with the placeholder a filed record writes
# instead. A copy of `factory.py`'s `DEFUSE`, pinned to it by `tests/test_hand_gate.py`.
DEFUSE = (
    (r"\bwork/\d{3,}\b(?!-)", lambda m: f"{m[0][:5]}<{m[0][5:]}>"),
    (r"/Users/[\w.-]+/", "/Users/<name>/"),
    (r"/home/[\w.-]+/", "/home/<name>/"),
    (r"~/[\w-]+/", "~/<dir>/"),
)
# The scan's own terms, in the main checkout's gitignored file, and the mark a record writes
# for one.
TERMS_FILE = Path(".sdlc", "terms.local")
TERM_MARK = "<term>"
