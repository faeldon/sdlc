"""landing — the factory's landing and train, apart from `factory.py` so a review can name them.

What lives here is the factory's one place that commits, and the code that moves a host's
branches: `land` (`cmd_land()`, `cmd_land_close()`, `cmd_land_fix()`), `land-check`, `train`
(`cmd_train()`, its state `TRAIN_STATE` in the git common dir, and `train --run`'s loop under
`TRAIN_RUN_LOCK`), `resolve` (`cmd_resolve()` and the rebase it stacks a change with) and
`land-verdicts`. This repo lists the file in `[review] sensitive`, read from the base branch, so a
change touching it is reviewed at full depth with the security reviewer, while a change elsewhere
in `factory.py` can stay light.

The line between here and `factory.py` is a rule `tests/test_modules.py` holds: a function lives
here when it is one of those commands or their train's named state, or when only code here calls
it; anything `factory.py` also calls stays there. So `factory.py` keeps `agent` (the landing tasks
included, the one place the factory runs `claude`), `gate` and `check` (`_run_check()`, the only
place it runs a host's command), the landing-step record (`_record_land()`, `read_land_step()`,
which the board's copies follow) and the review's depth. A constant moves only when it is named or
its whole commented block moves.

`factory.py` loads this file by path and binds `factory` here to a live view of its own names right
after (its own `_Names`: the factory never imports `sdlc.py`, and neither does this file). Every
name this code shares with the rest of the script (`_git`, `_sdlc`, `emit`, `find_change` …) is
read as `factory.<name>` when it runs, so a test's stand-in on the loaded `factory` module reaches
it; `factory.py` calls this file's names as `landing.<name>`, and the tests as
`factory.landing.<name>`. `factory` is unbound while this file loads, so nothing evaluated at load
may read it, and this file has no path of its own: the train runs each step through
`factory.FACTORY_SCRIPT`, never this file.

What it keeps: it commits only through `sdlc.py`'s own `ship` and `close` of the factory's own
version (`factory.sdlc_path()`); a branch moves only by `resolve --onto`, `land --close`,
`train --eject` and `--stop`, each printing its undo; the loop runs `RUN_STEPS` and no other
command. Of those, two run a host's command: `accept` (a change's own checks, as stacked, only
while `checks_clearance()` clears them: the file the person's yes covered, or changed commands
`read_only_command()` passes and the approver judged harmless, never the approver alone) and
`gate --land --build` (the base branch's `[commands] build`, once at the tip, `build_due()`).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

factory = None  # factory.py's own names, bound by factory.py right after it loads this file


# What the board shows for a stop `sdlc.py ship` caused, whose own words are its stderr.
SHIP_REFUSED = "sdlc.py ship refused to ship it: run /sdlc:ship {id} by hand to see why"


# The plain line for each why `_amend_record()` gives, by its opening words: what failed and what
# to do, for the board's card; the raw words stay under it. `{id}` is the change's number,
# `{rest}` what follows the colon (the paths, for the uncommitted one).
AMEND_PLAIN = {
    "git status couldn't be read": (
        "its worktree's state couldn't be read: run git status in its worktree, then rerun "
        "/sdlc-factory:land {id}"
    ),
    "uncommitted outside the change's folder": (
        "its worktree holds edits outside the change's folder ({rest}): commit or remove them, "
        "then rerun /sdlc-factory:land {id}"
    ),
    "HEAD isn't the landing's commit": (
        "its worktree isn't at the landing's commit, so the landing's record couldn't be saved "
        "with it: check git log in its worktree, then rerun /sdlc-factory:land {id}, or "
        "/sdlc:close {id} by hand"
    ),
    "the landing's record couldn't be added to the commit": (
        "the landing's record couldn't be saved with its commit: run git status in its worktree, "
        "then rerun /sdlc-factory:land {id}"
    ),
}


AMEND_OTHER = (
    "the landing's record couldn't be saved: read what the landing printed, then rerun "
    "/sdlc-factory:land {id}, or /sdlc:close {id} by hand"
)


def _amend_plain(why: str, ident: str) -> str:
    """The plain line for a why `_amend_record()` gave (`AMEND_PLAIN`, else `AMEND_OTHER`)."""
    for start, plain in AMEND_PLAIN.items():
        if why.startswith(start):
            return plain.format(id=ident, rest=why.partition(": ")[2])
    return AMEND_OTHER.format(id=ident)


def _land_refused(root: Path, folder: Path, out: dict, why: str, plain: str | None = None) -> int:
    """A refusal that stops a landing under way: recorded as its `stop`, then emitted. `plain`
    is what the board shows first when `why` is a tool's raw output: what failed and what to do;
    the raw words are recorded under it, and are the refusal in the output. A train that names
    the change is told (`_train_fail()`), and ejects it."""
    factory._record_land(root, folder, "stop", [plain, why] if plain and plain != why else [why])
    _train_fail(root, folder, plain or why)
    return factory.emit({**out, "state": "refused", "refusals": [why]}, 1)


def _land_gate_state(root: Path, folder: Path, n: int, settled: bool = False) -> dict | None:
    """The gate on landing round `n`'s rebased change, as `_gate_state` reads a build's: None when
    the base branch names no check. `settled` reads a round already reviewed: its last attempt's
    verdict stands whatever `HEAD` is now, which the landing's own record and later rebases move.
    In a train, the tip's PASS covers every change stacked under it (`train_names()`)."""
    base = factory._base(root)
    command = factory._base_check(root, base) if base else None
    if command is None:
        return None
    # In a train the tip's gate stands in for each change's own: a PASS on a commit that has the
    # change's stacked commit as an ancestor gated this change as it stands in the stack.
    named = train_names(root, folder)
    if named is not None:
        state, mine = named
        stacked = mine.get("stacked")
        for g in reversed(state["gates"]):
            if g["verdict"] == "PASS" and _is_ancestor(root, stacked, g["commit"]):
                return {"command": command, "current": "PASS", "exit": g["exit"]}
    record = factory.read_gate_file(factory.land_gate_path(folder, n)) or {
        "attempts": [],
        "fails": 0,
    }
    last = record["attempts"][-1] if record["attempts"] else None
    ran_on = last and (settled or last["build"] == factory.landed_build(root))
    current = last["verdict"] if ran_on else None
    return {"command": command, "current": current, "exit": last["exit"] if last else None}


def land_mended(folder: Path, n: int) -> set[str]:
    """The roles `agent` has mended in landing round `n`, from the `<role> land-<n>` lines of
    `runs/mended`: a landing round's allowance, apart from every build round's (`mended()`)."""
    path = folder / factory.MENDED
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    pairs = (line.partition(" ") for line in lines)
    return {factory.RENAMED.get(r, r) for r, _, rnd in pairs if rnd.strip() == f"land-{n}"}


def cases_failures(record: dict | None) -> dict[str, list[str]]:
    """Each failed case in a run's `scope.json` and the graders that failed in its runs, in
    order, once each. A copy of `sdlc.py`'s `cases_failures()`, pinned by a test."""
    out: dict[str, list[str]] = {}
    verdicts = (record or {}).get("verdicts")
    for case, v in sorted(verdicts.items()) if isinstance(verdicts, dict) else []:
        if not isinstance(v, dict) or v.get("result") != "failed":
            continue
        names = [g.get("name") for r in v.get("runs") or [] if isinstance(r, dict)
                 for g in r.get("graders") or [] if isinstance(g, dict)]  # fmt: skip
        out[case] = list(dict.fromkeys(n for n in names if isinstance(n, str)))
    return out


def _case_failures(root: Path, note: dict) -> list[dict]:
    """The note's failed cases, each with the graders that failed in its runs, read from the run's
    `scope.json` in the main checkout; with no readable record, the cases alone."""
    record = None
    if note.get("run"):
        checkouts = factory._all_checkouts(root)
        home = checkouts[0] if checkouts else root
        try:
            record = json.loads((home / note["run"] / "scope.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            record = None
    graders = cases_failures(record if isinstance(record, dict) else None)
    return [{"case": c, "graders": graders.get(c, [])} for c in note["failed"]]


def read_impact(folder: Path) -> str | None:
    """The release impact the approver proposed in `decision.md`'s `- IMPACT:` line."""
    path = folder / "decision.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        if m := factory.IMPACT_RE.match(line):
            return m.group(1)
    return None


def resolved_files(folder: Path) -> list[str]:
    """Every file the change's `conflicts.md` says `sdlc.py resolve` merged, each once, in order:
    a copy of `sdlc.py`'s `conflicts_resolved()`, pinned to it by `tests/test_land.py`."""
    record = folder / "conflicts.md"
    lines = record.read_text(encoding="utf-8").splitlines() if record.is_file() else []
    return list(dict.fromkeys(ln[2:].strip() for ln in lines if ln.startswith("- ")))


LANDED_ROUND_RE = re.compile(r"^land-(\d+)$")


LANDING_RESOLVED = "a conflict was resolved while landing"


# A fix the person asked for at landing: new behaviour, a signal for the rest of the change's life.
LANDING_FIXED = "a fix was made while landing"


# The person's words for a fix asked at landing: a ticked line the land skill writes at the end of
# `decisions.md`, after the yes, whose id alone `land-fix --ask` takes. Never a shell argument,
# where a quote or `$(` in the words breaks the command or runs. The ledger reads past it.
FIX_WORDS_RE = re.compile(r"^- \[x\] (R\d+) \(person, fix\): (.+?)\s*$")


def read_fix_words(folder: Path, ident: str) -> str | None:
    """The person's words for fix `ident` (`R3`) in `decisions.md`, or None."""
    path = folder / "decisions.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        m = FIX_WORDS_RE.match(line)
        if m and m.group(1) == ident:
            return m.group(2)
    return None


def resolution_signals(root: Path, folder: Path, cfg: dict) -> list[str]:
    """A resolved conflict no reviewer has seen, as a signal: one made while landing until
    `land_verdict()` for the round its marker names (`runs/land-resolved`'s first line) says
    `pass`, a pass that stands when the landing's own record or a later rebase moves `HEAD`
    (`settled`), and always for a marker naming no round, written before the round was. And one
    `sdlc.py resolve` recorded in `conflicts.md` while any file it names hashes otherwise than
    in the newest complete build round's snapshot, whose reviewers read exactly that content, or
    always with no such round or snapshot. Content, never file times, which a checkout resets."""
    signals = []
    files = resolved_files(folder)
    if files:
        rounds, _, _ = factory._rounds_at_depth(root, folder, cfg)
        done = [r["round"] for r in rounds if r["complete"]]
        snap = factory.read_snapshot(folder, done[-1]) if done else None
        base = factory._base(root)
        if snap is None or base is None:
            unseen = files
        else:
            now = factory._tree_hashes(root, base)
            unseen = [f for f in files if now.get(f) != snap.get(f)]
        if unseen:
            signals.append(
                "a conflict resolved by sdlc.py resolve after the last review round: "
                + ", ".join(unseen)
            )
    marker = folder / "runs" / "land-resolved"
    if marker.is_file():
        lines = marker.read_text(encoding="utf-8").splitlines()
        m = LANDED_ROUND_RE.match(lines[0].strip()) if lines else None
        n = int(m.group(1)) if m else 0
        if not n or land_verdict(root, folder, cfg, n, settled=True)["next"] != "pass":
            signals.append(LANDING_RESOLVED)
    return signals


def _preflight(folder: Path, worktree: Path) -> tuple[dict | None, str]:
    """`sdlc.py preflight` on the change, from its worktree: its JSON, or None and what it said."""
    _, pre, out = factory._sdlc(["preflight", folder.name], worktree)
    return pre, out


def read_proposals(folder: Path) -> tuple[dict[str, tuple], list[tuple[str, str]]]:
    """What the approver proposed in `decision.md`: each undone item's disposition by its exact
    text, as (`seed`, title), (`dropped`, reason) or (`bug`, severity, paths, title), a bug line
    that doesn't read as one with no severity and no paths, and each `- RECOVER:` line as (the
    path or group it covers, the way back)."""
    path = folder / "decision.md"
    undone, recover = {}, []
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        if (m := factory.UNDONE_RE.match(line)) and m.group(2) == "bug":
            b = factory.BUG_PROPOSAL_RE.match(m.group(3))
            paths = [p.strip().strip("`") for p in b.group(2).split(",") if p.strip()] if b else []
            undone.setdefault(
                m.group(1), ("bug", b.group(1), paths, b.group(3)) if b else ("bug", "", [], "")
            )
        elif m:
            undone.setdefault(m.group(1), (m.group(2), m.group(3)))
        elif m := factory.RECOVER_RE.match(line):
            recover.append((m.group(1), m.group(2)))
    return undone, recover


def bad_bugs(undone: list[dict], words: list[str]) -> list[str]:
    """Why each bug the approver proposed can't be filed as it stands: an item not starting
    `pre-existing:`, no paths, or a severity outside `words`, the process doc's (any word when it
    names none). The script never guesses one: such a change is left for `/sdlc:ship`."""
    out = []
    for u in undone:
        if "bug" not in u:
            continue
        bug, item = u["bug"], u["text"]
        if not item.startswith(factory.PREEXISTING_ITEM):
            out.append(
                f"a bug proposed for {item!r}, which isn't a {factory.PREEXISTING_ITEM} item"
            )
        elif not bug["paths"]:
            out.append(f"a bug proposed for {item!r} names no paths")
        elif not bug["severity"] or (words and bug["severity"] not in words):
            out.append(f"a bug proposed for {item!r} is {bug['severity'] or 'without a severity'}"
                       + (f", not one of {', '.join(words)}" if words else ""))  # fmt: skip
    return out


def severity_words(worktree: Path) -> tuple[list[str] | None, str]:
    """The process doc's severity words, from `sdlc.py bugs`'s `severities`, or None and what it
    said when it can't be read."""
    _, data, said = factory._sdlc(["bugs"], worktree)
    words = (data or {}).get("severities")
    return (words, "") if isinstance(words, list) else (None, said)


def unrecovered(paths: list[str], recover: list[tuple[str, str]]) -> list[str]:
    """The irreversible `paths` no `- RECOVER:` line covers: one names it, or a pattern of it (a
    directory ending in `/`, or a glob), alone or in a comma-separated list."""
    named = [s.strip().strip("`") for subject, _ in recover for s in subject.split(",")]
    return [p for p in paths if p not in named and not factory.risk_paths([p], named)]


def note_items(folder: Path) -> dict[int, str]:
    """Each `- [ ]` note of `notes.md` by its line number, as `sdlc.py preflight` numbers them, with
    its whole text: the line's own, then each indented, non-blank line after it, up to the first
    that isn't, joined with single spaces. A fenced example is never a note."""
    path = folder / "notes.md"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    found, fenced = {}, False
    for i, line in enumerate(lines):
        if factory.FENCE_RE.match(line):
            fenced = not fenced
            continue
        m = None if fenced else factory.OPEN_NOTE_RE.match(line)
        if not m:
            continue
        words = [m.group(1)]
        for more in lines[i + 1 :]:
            if not more.strip() or not more[:1].isspace() or factory.OPEN_NOTE_RE.match(more):
                break
            words.append(more.strip())
        found[i + 1] = " ".join(" ".join(words).split())
    return found


def nit_findings(root: Path, folder: Path, cfg: dict) -> list[dict]:
    """The agents' findings of change `folder`, as `carry` writes them (`agent_findings()` of the
    rounds at the run's depth): the one reading the landing files nits from."""
    return factory.agent_findings(factory._rounds_at_depth(root, folder, cfg)[0])


def land_parts(folder: Path, pre: dict, root: Path | None = None, cfg: dict | None = None) -> dict:
    """What the batch's yes approves for change `folder`, each part empty when it has none: its
    acceptance checks, its skills' cases with the cap, its undone notes, each with its whole text
    (`note_items()`) and the disposition the approver proposed for its first line or its whole
    text (a seed titled by the note's first sentence when none was; a bug with what the question
    shows of it), its assumed decisions (the open defaults), the defaults the approver settled,
    each with its reason, never among those to confirm, the `How to recover:` lines its commit
    will carry, and,
    read from its worktree `root` with `cfg`, the agents' nits to file as `[nit]` entries
    (`nit_findings()`'s `file`, with the line the question shows of each); and for an ESCALATE,
    how each of its reasons was cleared (`escalation_lines()`)."""
    proposed, recover = read_proposals(folder)
    notes = note_items(folder)
    undone = []
    for item in (pre.get("undone") or {}).get("items") or []:
        full = notes.get(item["line"], item["text"])
        kind, *said = (
            proposed.get(full)
            or proposed.get(item["text"])
            or ("seed", factory.first_sentence(full))
        )
        part = {"line": item["line"], "text": full}
        if kind == "bug":
            severity, paths, title = said
            part["bug"] = {"severity": severity, "paths": paths, "title": title}
            part["shown"] = f"filed as a bug, {severity}: {title} ({', '.join(paths)})"
        else:
            part["seed" if kind == "seed" else "dropped"] = said[0]
        undone.append(part)
    scope = (pre.get("cases") or {}).get("scope") or []
    found = nit_findings(root, folder, cfg) if root is not None and cfg is not None else []
    nits = [
        {**n, "shown": f"[nit] {n['title']} ({n['theme']}, {n['cost']}, {n['value']}; "
                       f"{', '.join(n['paths'])})"}
        for n in (i["file"] for i in found) if n
    ]  # fmt: skip
    ledger = factory.read_ledger(folder)
    return {
        "checks": [{"name": c["name"], "command": c["command"]}
                   for c in (pre.get("checks") or {}).get("checks") or []],
        "cases": _cases_part(root or folder.parents[2], folder, scope) if scope else {},
        "undone": undone,
        "assumed": [{"id": d["id"], "text": d["text"]} for d in ledger
                    if d["open"] and d["kind"] == "default"],
        "settled": [{"id": d["id"], "text": d["text"], "reason": d["settled"]} for d in ledger
                    if d["settled"]],
        "recover": [f"{subject}: {way}" for subject, way in recover],
        "nits": nits,
        "escalations": escalation_lines(root or folder.parents[2], folder, ledger),
    }  # fmt: skip


def _cases_part(root: Path, folder: Path, scope: list[str]) -> dict:
    """A change's skills' cases as the landing shows them: the `scope` and `cap_usd`, whether its
    note says anything yet (`noted`), and from it the cases that `failed` (each with its failing
    graders), hit the `environment`, or why they were `skipped`, and the `run`."""
    note = factory.read_cases_note(folder)
    return {
        "scope": scope, "cap_usd": factory.CASE_CAP_USD, "noted": note is not None,
        "failed": _case_failures(root, note) if note else [],
        "environment": note["environment"] if note else [],
        "skipped": note["skipped"] if note else None, "run": note["run"] if note else None,
    }  # fmt: skip


def escalation_lines(root: Path, folder: Path, ledger: list[dict] | None = None) -> list[str]:
    """For a change the approver escalated, one line per reason saying how it was cleared, read
    beside `decision.md`, which no one rewrites: each blocking or default line it holds (never one
    the approver settled, nor a superseded one) `D2: decided: <answer>`, each current look
    `D7: acknowledged: <words>`, each `gate` reason `gate: green on the build as it stands
    (attempt <n>)`, and `<id>: not cleared` or `gate: not cleared` while it isn't. [] for READY."""
    if factory.read_decision(folder)[0] != "ESCALATE":
        return []
    lines = []
    for d in factory.read_ledger(folder) if ledger is None else ledger:
        if d["settled"] or d["superseded_by"] or not d["current"]:
            continue
        said = "acknowledged" if d["kind"] == "look" else "decided"
        lines.append(f"{d['id']}: {said}: {d['answer']}" if d["decided"]
                     else f"{d['id']}: not cleared")  # fmt: skip
    if any(r["kind"] == "gate" for r in factory.escalation_reasons(folder)):
        state = factory.hand_gate_state(root, folder)
        green = f"gate: green on the build as it stands (attempt {state['attempt']})"
        reasons = [r for r in factory.escalation_reasons(folder) if r["kind"] == "gate"]
        lines += [green if state["green"] else "gate: not cleared" for _ in reasons]
    return lines


def intent_parts(folder: Path) -> dict:
    """What change `folder` is, quoted from its `intent.md`, never summarised: its `# ` title less
    its `NNN — ` number, and its Problem and Outcome as written; each empty when it has none."""
    path = folder / "intent.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), "")
    return {
        "title": re.sub(r"^\d+\s+—\s+", "", title),
        "problem": factory._section(text, "## Problem").strip(),
        "outcome": factory._section(text, "## Outcome").strip(),
    }


def land_shown(batch: list[dict]) -> str:
    """What the batch's question calls `as shown`, for the dialog to show beside its yes: each
    change by its name and intent's title, then each part `land_parts()` gives it, only those it
    has: its checks, its cases and their cap, each undone note with its disposition, each assumed
    decision, each default the approver settled with its reason, its `How to recover:` lines,
    the agents' nits to file, by their `shown` line, and for an escalation how each of its reasons
    was cleared."""

    def listed(head: str, items: list[str]) -> list[str]:
        return [f"  {head}:", *(f"  - {i}" for i in items)] if items else []

    blocks = []
    for c in batch:
        title = (c.get("intent") or {}).get("title")
        lines = [f"{c['change']} — {title}" if title else c["change"]]
        lines += listed("Acceptance checks", [f"{k['name']}: {k['command']}" for k in c["checks"]])
        if c["cases"]:
            scope = ", ".join(c["cases"]["scope"])
            lines.append(f"  Skills' cases (at most ${c['cases']['cap_usd']}): {scope}")
            lines += _cases_shown(c["cases"])
        disposed = [
            f"{u['text']} → {u['shown']}" if "bug" in u
            else f"{u['text']} → seed: {u['seed']}" if "seed" in u
            else f"{u['text']} → dropped: {u['dropped']}"
            for u in c["undone"]
        ]  # fmt: skip
        lines += listed("Undone notes", disposed)
        lines += listed("Assumed decisions to confirm",
                        [f"{d['id']}: {d['text']}" for d in c["assumed"]])  # fmt: skip
        lines += listed("Settled by the approver",
                        [f"{d['id']}: {d['text']} ({d['reason']})"
                         for d in c.get("settled") or []])  # fmt: skip
        lines += listed("How to recover", c["recover"])
        lines += listed("Agents' nits to file", [n["shown"] for n in c.get("nits") or []])
        lines += listed("Escalated", c.get("escalations") or [])
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _cases_shown(cases: dict) -> list[str]:
    """The lines under a change's cases that its yes accepts: each failed case with its failing
    graders and where its traces are, the cases the sandbox spoiled, and a skip with why."""
    lines = []
    where = f", trace in {cases['run']}/traces" if cases.get("run") else ""
    for f in cases.get("failed") or []:
        graders = f" ({', '.join(f['graders'])})" if f["graders"] else ""
        lines.append(f"  - failed: {f['case']}{graders}{where}")
    if cases.get("environment"):
        lines.append(f"  - hit the environment: {', '.join(cases['environment'])}")
    if cases.get("skipped"):
        lines.append(f"  - skipped: {cases['skipped']}")
    return lines


def land_unreviewed(root: Path, folder: Path, cfg: dict) -> list[str] | None:
    """The paths the change touches that hash otherwise than in the newest complete build round's
    snapshot, whose reviewers read exactly that content: changed since its last review, by hand or
    by `sdlc.py resolve`. A path absent from both is unchanged, and the change folders never count
    (`_changed_paths()`). None with no complete round, no snapshot of it, or no base branch."""
    rounds, _, _ = factory._rounds_at_depth(root, folder, cfg)
    done = [r["round"] for r in rounds if r["complete"]]
    snap = factory.read_snapshot(folder, done[-1]) if done else None
    base = factory._base(root)
    if snap is None or base is None:
        return None
    now = factory._tree_hashes(root, base)
    return sorted(p for p in set(now) | set(snap) if now.get(p) != snap.get(p))


UNREVIEWED_UNKNOWN = "no snapshot of its last review"


def land_signals(
    folder: Path,
    worktree: Path,
    decision: str,
    cfg: dict,
    pre: dict | None = None,
    unreviewed: list[str] | None = (),
) -> tuple[list, list]:
    """Why change `folder` needs the person at the batch's gate (`signals`), and why it can't land
    in a batch at all, only by hand (`excluded`): what `sdlc.py preflight` reads of its risk, its
    notes, its checks, its skills' cases and its issues, and what the run left in its folder,
    a resolved conflict no reviewer has seen among it (`resolution_signals()`). The exclusions
    are an irreversible path the approver proposed no way back for, and a bug it proposed that
    `bad_bugs()` refuses. A nit to file is a signal, so no agent's nit is filed without the
    person's yes. `unreviewed` is
    `land_unreviewed()` as the caller read it at `stage: test`: paths, or None for no snapshot."""
    signals, excluded = [], []
    if pre is None:
        pre, out = _preflight(folder, worktree)
        if pre is None:
            return [f"preflight couldn't be read: {out.strip()[-300:]}"], []
    risk = pre.get("risk") or {}
    if risk.get("sensitive"):
        signals.append(f"touches sensitive paths: {', '.join(risk['sensitive'][:5])}")
    if risk.get("irreversible"):
        signals.append(f"touches irreversible paths: {', '.join(risk['irreversible'][:5])}")
        missing = unrecovered(risk["irreversible"], read_proposals(folder)[1])
        if missing:
            excluded.append(
                f"decision.md proposes no How to recover for {', '.join(missing[:5])}: "
                "ship it by hand"
            )
    parts = land_parts(folder, pre, worktree, cfg)
    undone = parts["undone"]
    if any("bug" in u for u in undone):
        words, said = severity_words(worktree)
        if words is None:
            excluded.append(f"sdlc.py bugs couldn't be read: {said.strip()[-300:]}")
        else:
            excluded += [f"{why}: ship it by hand" for why in bad_bugs(undone, words)]
    if (pre.get("closes") or {}).get("closes"):
        signals.append("came from a public issue (closes:)")
    impact = read_impact(folder)
    if impact is None:
        signals.append("decision.md proposes no `- IMPACT:`")
    elif impact == "major":
        signals.append("impact: major")
    if decision == "ESCALATE":
        signals.append("the approver escalated")
    ledger = factory.read_ledger(folder)
    if [d for d in ledger if d["open"]]:
        signals.append("decisions still open or assumed in decisions.md")
    assumed = [d["id"] for d in ledger if d["open"] and d["kind"] == "default"]
    if assumed:
        signals.append(f"assumed decisions to confirm: {', '.join(assumed)}")
    if settled := [d["id"] for d in ledger if d["settled"]]:
        signals.append(f"defaults settled by the approver: {', '.join(settled)}")
    signals += resolution_signals(worktree, folder, cfg)
    if list(folder.glob("build/land-*.ask.md")):
        signals.append(LANDING_FIXED)
    if unreviewed is None:
        signals.append(UNREVIEWED_UNKNOWN)
    elif unreviewed:
        signals.append(f"changed since its last review: {', '.join(unreviewed)}")
    if not cfg["land"]["auto"]:
        signals.append("land.auto is off on the base branch")
    if n := len((pre.get("undone") or {}).get("items") or []):
        signals.append(f"undone notes to dispose of: {n}")
    if n := len((pre.get("checks") or {}).get("checks") or []):
        signals.append(f"acceptance checks to run: {n}")
    if n := len((pre.get("cases") or {}).get("scope") or []):
        signals.append(f"skills' cases in scope: {n}")
        signals += _cases_signals(parts["cases"])
    if n := len(parts["nits"]):
        past = sum(i["reason"] == factory.CAP_REASON for i in nit_findings(worktree, folder, cfg))
        signals.append(
            f"nits to file: {n}" + (f", {past} past the cap of {factory.NIT_CAP}" if past else "")
        )
    return signals, excluded


def _cases_signals(cases: dict) -> list[str]:
    """What a change's note says its skills' cases did that only the person accepts: cases that
    failed (with their graders, and the run), hit the environment, or were skipped."""
    out = []
    if cases.get("failed"):
        each = [f["case"] + (f" ({', '.join(f['graders'])})" if f["graders"] else "")
                for f in cases["failed"]]  # fmt: skip
        where = f", trace in {cases['run']}" if cases.get("run") else ""
        out.append(f"skills' cases failed: {', '.join(each)}{where}")
    if cases.get("environment"):
        out.append(f"skills' cases hit the environment: {', '.join(cases['environment'])}")
    if cases.get("skipped"):
        out.append(f"skills' cases skipped: {cases['skipped']}")
    return out


def land_question(batch: list[dict], base: str, moves: int | None = None) -> str:
    """The batch's question, worded here so the skill never words its own: a clause for the checks
    (run as shown, and again as stacked), the cases, the base branch's build at the tip (a change
    whose `build` is true, `build_due()`), for failed or skipped cases approved as shown, for the
    dispositions and confirmations, for the agents' nits to file, and for `How to recover:`, each
    only when some change in the batch has one, and the cases' total ceiling, the cap per change
    with any; what the train does (stacked in this order, gated once at the
    tip, a red tip bisected and the change at fault left out, a conflict resolved by one landing
    agent and reviewed again, closed in order); the most times it follows `base` moving
    (`land.moves`, the default's when none is given); and its four answers, `yes, with a fix`
    among them."""
    if moves is None:
        moves = factory.DEFAULTS["land"]["moves"]
    n = len(batch)
    names = ", ".join(c["change"] for c in batch)
    parts = ["each shipped with its approver's impact"]
    with_cases = sum(1 for c in batch if c["cases"])
    if any(c["checks"] for c in batch):
        # Again as stacked, by the loop itself while `checks.md` is the file this yes covers.
        parts.append("its acceptance checks run as shown, and again as stacked")
    if with_cases:
        parts.append(
            f"its skills' cases run as shown (at most ${factory.CASE_CAP_USD * with_cases})"
        )
    if any(c.get("build") for c in batch):
        parts.append("its slow gate run once at the tip")
    if any((c["cases"] or {}).get("failed") or (c["cases"] or {}).get("skipped") for c in batch):
        parts.append("its failed or skipped skills' cases approved as shown")
    undone = any(c["undone"] for c in batch)
    assumed = any(c["assumed"] for c in batch)
    bugs = any("bug" in u for c in batch for u in c["undone"])
    notes = ("its undone notes carried, filed as bugs or dropped" if bugs
             else "its undone notes carried or dropped")  # fmt: skip
    if undone and assumed:
        parts.append(f"{notes} and its assumed decisions confirmed as shown")
    elif undone:
        parts.append(f"{notes} as shown")
    elif assumed:
        parts.append("its assumed decisions confirmed as shown")
    if any(c.get("nits") for c in batch):
        parts.append("its agents' nits filed as shown")
    if any(c["recover"] for c in batch):
        parts.append("with how to recover shown")
    return (
        f"Land {n} change{'s' if n != 1 else ''} in this order, {names}, {', '.join(parts)}, "
        f"committed, stacked in this order on {base}, gated once at the tip (a red tip bisected, "
        "the change at fault left out with why and the rest landed; a conflict resolved by one "
        f"landing agent and reviewed again), brought up to date as often as {base} moves while "
        f"landing, up to {moves} times, and closed in order, pushed as git.push says? "
        "(yes / yes, with a fix / leave one out / no)"
    )


def cmd_land_check(root: Path, idents: list[str]) -> int:
    """The batch: the ready changes in `ready`'s order (or those named), at most `land.batch`, each
    with its signals, what it is (`intent_parts()`), what the yes approves for it (`land_parts()`),
    whether it calls for the base branch's build (`build`, `build_due()`) and why any is left
    out, the question to ask (`land_question()`), the text the dialog shows beside it
    (`land_shown()`), and `clear`: true when no change in it has a signal, so
    the gate passes itself. Read-only."""
    cfg, warnings = factory.load_config(root)
    picked = [
        r
        for r in factory.ready(root)
        if not idents or any(factory.names_change(r["change"], i) for i in idents)
    ]
    batch, left_out, over = [], [], []
    for r in picked:
        worktree = Path(r["worktree"])
        folder = worktree / factory.work_rel(worktree) / r["change"]
        pre, said = _preflight(folder, worktree)
        unreviewed = _unreviewed_at_test(worktree, folder, cfg)
        base = factory._base(worktree)
        signals, excluded = land_signals(
            folder, worktree, r["decision"], cfg, pre or {}, unreviewed=unreviewed
        )
        if pre is None:
            signals = [f"preflight couldn't be read: {said.strip()[-300:]}"]
        entry = {
            "change": r["change"], "worktree": r["worktree"], "decision": r["decision"],
            "impact": read_impact(folder), "signals": signals, "overlaps": r["overlaps"],
            "intent": intent_parts(folder), **land_parts(folder, pre or {}, worktree, cfg),
            "build": bool(base) and build_due(worktree, base),
        }  # fmt: skip
        if excluded:
            left_out.append({**entry, "excluded": excluded})
        elif len(batch) >= cfg["land"]["batch"]:
            over.append(r["change"])
        else:
            batch.append(entry)
    clear = bool(batch) and not any(c["signals"] for c in batch)
    base = factory._base(root) or "the base branch"
    question = land_question(batch, base, cfg["land"]["moves"]) if batch else None
    return factory.emit({
        "batch": batch, "excluded": left_out, "over_limit": over, "clear": clear,
        "question": question, "shown": land_shown(batch) if batch else None,
        "auto": cfg["land"]["auto"], "limit": cfg["land"]["batch"],
        "warnings": warnings,
    })  # fmt: skip


# What a landing files and retires, held in the change's folder until `sdlc.py close` lands it
# in the `Close` commit: copies of `sdlc.py`'s `ENTRIES` and `RETIRE_LINE_RE`, pinned by tests.
ENTRIES = "entries.md"


RETIRE_RE = re.compile(r"^Retire (\d{4}-\d{2}-\d{2}-\d+):\s*(.*)$")


def held_text(folder: Path) -> str:
    """The change's `entries.md`, or the title it starts from: `# NNN-slug — entries`."""
    path = folder / ENTRIES
    return path.read_text(encoding="utf-8") if path.is_file() else f"# {folder.name} — entries\n"


def retired_ids(folder: Path) -> list[str]:
    """The nits the change's `entries.md` retires: each `Retire <id>:` line before its first
    entry."""
    found = []
    for line in held_text(folder).splitlines():
        if line.startswith("## "):
            break
        if m := RETIRE_RE.match(line.strip()):
            found.append(m.group(1))
    return found


def retire_nits(folder: Path, ids: list[str]) -> None:
    """A `Retire <id>: taken in by <change>` line in the change's `entries.md` for each nit `ids`
    names that it doesn't retire yet, after its title and any earlier ones, before its first
    entry: close deletes each from the register in the `Close` commit, as it does for
    `/sdlc:ship`. The branch's register is never edited."""
    new = [i for i in dict.fromkeys(ids) if i not in retired_ids(folder)]
    if not new:
        return
    lines = held_text(folder).splitlines()
    at = next((n for n, line in enumerate(lines) if line.startswith("## ")), len(lines))
    while at > 1 and not lines[at - 1].strip():
        at -= 1
    retire = [f"Retire {i}: taken in by {folder.name}" for i in new]
    gap = [""] if at > 0 and not RETIRE_RE.match(lines[at - 1].strip()) else []
    rest = lines[at:]
    while rest and not rest[0].strip():
        rest.pop(0)
    out = lines[:at] + gap + retire + ([""] + rest if rest else [])
    (folder / ENTRIES).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def drop_entries(root: Path, ids: list[str]) -> list[str]:
    """Delete each entry `ids` names, by id alone, from the checkout's register, its heading up to
    the next heading outside a fence, every other line left byte for byte. The ids it deleted, in
    the register's order."""
    register = root / factory.INBOX
    if not register.is_file():
        return []
    kept, gone, dropping, fenced = [], [], False, False
    for line in register.read_text(encoding="utf-8").splitlines(keepends=True):
        if factory.FENCE_RE.match(line):
            fenced = not fenced
        elif not fenced and factory.ENTRY_END_RE.match(line):
            m = factory.ENTRY_RE.match(line)
            dropping = bool(m and m.group(1) in ids)
            if dropping:
                gone.append(m.group(1))
        if not dropping:
            kept.append(line)
    if gone:
        register.write_text("".join(kept), encoding="utf-8", newline="\n")
    return gone


# The programs a changed acceptance check may run unattended (185 R5), each read-only as called:
# `git` only with `READ_ONLY_GIT`'s subcommands as its very next word, never with an option that
# writes a file or runs a program (`READ_ONLY_GIT_REFUSED`). Everything else stops the train.
READ_ONLY_PROGRAMS = frozenset({"grep", "cat", "head", "tail", "wc", "test", "[", "true", "false",
                                "git"})  # fmt: skip
READ_ONLY_GIT = frozenset({"log", "show", "diff"})
READ_ONLY_GIT_REFUSED = ("--output", "--ext-diff", "--textconv")
# grep's flags that follow a symlink while recursing (GNU `-R`, BSD `-S` and `-O`), which the path
# rule can't see: a link inside the checkout read through to a file outside it.
GREP_FOLLOWS = frozenset("RSO")
# GNU grep takes any unambiguous prefix of a long option, so every name with three or more
# characters after its `--` (`GREP_FOLLOWS_MIN`) that begins this one is refused (`--der` on),
# with `=value` or not.
GREP_FOLLOWS_LONG = "--dereference-recursive"
GREP_FOLLOWS_MIN = 3
# Outside single quotes: a redirect, a substitution, an escape, a subshell or group.
READ_ONLY_REFUSED = frozenset(">`$\\(){}<")
GLOBS = frozenset("*?[")


def _simple_commands(text: str) -> tuple[list[str], str | None]:
    """`text` split into its simple commands on `&&`, `||`, `|`, `;` and newlines outside quotes,
    or why it can't be: a character `READ_ONLY_REFUSED` names outside single quotes, a lone `&`,
    an unquoted glob past a command's first character, or a quote left open."""
    parts, quote, i = [""], None, 0
    while i < len(text):
        ch = text[i]
        if quote == "'":
            quote = None if ch == "'" else quote
        elif ch in READ_ONLY_REFUSED or (ch == "&" and text[i : i + 2] != "&&"):
            return [], f"`{ch}` outside single quotes"
        elif quote == '"':
            quote = None if ch == '"' else quote
        elif ch in "'\"":
            quote = ch
        elif ch in "|;\n" or text[i : i + 2] == "&&":
            step = 2 if text[i : i + 2] in ("&&", "||") else 1
            parts.append("")
            i += step
            continue
        elif ch in GLOBS and parts[-1].strip():
            # Past a command's first character: `[ -f x ]` is the one first word that is one.
            return [], f"an unquoted `{ch}`, which the shell expands"
        parts[-1] += ch
        i += 1
    if quote:
        return [], "a quote left open"
    return parts, None


def _path_refusal(word: str, checkout: Path) -> str | None:
    """Why `word`, a command's argument, reaches outside `checkout`: absolute, `~`, a `..`
    component, or an existing path that resolves outside it (a symlink out). None when it
    doesn't."""
    if word.startswith(("/", "~")) or re.match(r"^[A-Za-z]:[/\\]", word):
        return f"`{word}` names a path outside the checkout"
    if ".." in re.split(r"[/\\]", word):
        return f"`{word}` has a `..` component"
    path = checkout / word
    if os.path.lexists(path):
        try:
            path.resolve().relative_to(checkout.resolve())
        except (ValueError, OSError):
            return f"`{word}` resolves outside the checkout"
    return None


def read_only_command(text: str, checkout: Path) -> str | None:
    """Why the shell command `text`, a changed acceptance check, isn't on the read-only list
    (185 R5), or None when it is: every simple command in it (`_simple_commands()`) starts with
    one of `READ_ONLY_PROGRAMS`, named bare, with no `VAR=value` before it; `git` takes one of
    `READ_ONLY_GIT` as its very next word and none of `READ_ONLY_GIT_REFUSED`; `grep` none of the
    flags that follow symlinks as it recurses (`GREP_FOLLOWS`, and any prefix of
    `GREP_FOLLOWS_LONG` grep would take for it); and no word, nor an option's value (after `=`, or
    glued to a short option), is absolute, starts `~`, has a `..` component, or names an existing
    path that resolves outside `checkout`. That last rule sees only the paths the words name: a
    symlink out met by a program walking the tree itself is refused only by the grep flags above,
    grep being the one program on the list that can follow a link as it recurses. It never runs
    anything, and never judges intent: `cat .env` passes, which is why the approver reads it
    too."""
    parts, why = _simple_commands(text)
    if why:
        return why
    for part in parts:
        try:
            words = shlex.split(part, posix=True)
        except ValueError as e:
            return f"`{part.strip()}` can't be read: {e}"
        if not words:
            return "an empty command between separators"
        program = words[0]
        if program not in READ_ONLY_PROGRAMS:
            return f"`{program}` isn't a read-only program the list names"
        if program == "git" and (len(words) < 2 or words[1] not in READ_ONLY_GIT):
            said = " ".join(words[:2])
            return f"`{said}`: git runs unattended only as git log, git show or git diff"
        for word in words[1:]:
            if program == "git" and word.startswith(READ_ONLY_GIT_REFUSED):
                return f"`{word}` makes git write a file or run a program"
            short = word.startswith("-") and not word.startswith("--")
            name = word.partition("=")[0] if word.startswith("--") else ""
            if program == "grep" and (
                (len(name) - 2 >= GREP_FOLLOWS_MIN and GREP_FOLLOWS_LONG.startswith(name))
                or (short and GREP_FOLLOWS & set(word[1:]))
            ):
                return f"`{word}` makes grep follow symlinks, which can lead out of the checkout"
            values = [word]
            if word.startswith("-"):
                values = [word.partition("=")[2]] if "=" in word else []
                if not values and not word.startswith("--") and len(word) > 2:
                    values = [word[2:]]
            for value in values:
                if value and (why := _path_refusal(value, checkout)):
                    return why
    return None


def checks_sha(folder: Path) -> str | None:
    """The sha256 of change `folder`'s `checks.md` bytes, or None when it has none: what the
    person's yes covered, as `train --begin` records it, and what the approver judged."""
    path = folder / "checks.md"
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _checks_now(folder: Path, tree: Path) -> tuple[list[dict], str | None]:
    """Each acceptance check as `sdlc.py preflight` gives it (`acceptance()`, the parser `sdlc.py
    accept` runs them with), `name` and `command`; or why they can't be read."""
    pre, said = _preflight(folder, tree)
    if pre is None:
        return [], f"preflight couldn't be read: {said.strip()[-300:]}"
    part = pre.get("checks") or {}
    if part.get("problems"):
        return [], "; ".join(part["problems"])
    return [{"name": c["name"], "command": c["command"]} for c in part.get("checks") or []], None


# The approver's judgement of a changed `checks.md`, `build/land-<n>.checks.md`: the first line,
# which the script writes, is the hash of the file it judged; the reply under it opens with its
# answer (`factory.CHECKS_RE`).
JUDGED_RE = re.compile(r"^Judged: ([0-9a-f]{16})\s*$")


def read_checks_record(path: Path) -> dict | None:
    """The approver's judgement in `path`: `judged`, the hash it judged (None when the first line
    isn't one), `answer`, `HARMLESS` or `ESCALATE` when `opening()` reads it and every `CHECKS:`
    line agrees, else None, and `said`, the reply's words after its answer; None with no file."""
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    m = JUDGED_RE.match(lines[0]) if lines else None
    reply = lines[1:] if m else lines
    while reply and not reply[0].strip():
        reply = reply[1:]
    found = factory.opening(reply, factory.CHECKS_RE)
    answers = {a.group(1) for a in map(factory.CHECKS_RE.match, reply) if a}
    answer = found[1].group(1) if found and len(answers) == 1 else None
    rest = reply[found[0] + 1 :] if answer else reply
    said = " ".join(" ".join(rest).split())
    return {"judged": m.group(1) if m else None, "answer": answer, "said": said}


CHANGED = "checks.md changed since the yes"


def checks_clearance(tree: Path, folder: Path, mine: dict) -> dict:
    """Whether a train may run change `folder`'s acceptance checks as stacked without the person
    (185 R2–R8), from its entry `mine` in the train: `clear`, the `step` to name (`accept`, or
    `checks` for the approver's judgement), `why`, and what changed. Clear `as approved` when
    `checks.md` hashes to the `checks_sha` the yes covered (`train --begin`); otherwise the checks
    added or edited (`changed`: a name and command not among the approved) must each pass
    `read_only_command()` (`off_list` names those that don't, which stops it before any agent),
    and the approver's judgement of the file as it stands (`read_checks_record()`, current when
    its `Judged:` hash is the file's) must open `CHECKS: HARMLESS`: missing or stale, `checks`;
    anything else, not clear, with its words. A state from before `checks_sha` approved
    nothing, so every check counts as changed. Removed checks run nothing; the approver is told."""
    sha = checks_sha(folder)
    approved = mine.get("checks") or []
    out = {"clear": False, "step": "accept", "why": "", "sha": sha, "approved": approved,
           "current": [], "changed": [], "removed": [], "off_list": []}  # fmt: skip
    if "checks_sha" in mine and sha == mine["checks_sha"]:
        return {**out, "clear": True, "why": "as approved"}
    if sha is None:
        # Removed since the yes: nothing runs (`land_verdict()` reads no file as a PASS), and
        # nothing is left for the approver to judge.
        return {**out, "why": f"{CHANGED}: checks.md is gone, so there is nothing to judge"}
    current, problem = _checks_now(folder, tree)
    if problem:
        return {**out, "why": f"{CHANGED}, and its checks can't be read: {problem}"}
    pairs = {(c["name"], c["command"]) for c in approved}
    now = {(c["name"], c["command"]) for c in current}
    out["current"] = current
    out["changed"] = [c for c in current if (c["name"], c["command"]) not in pairs]
    out["removed"] = [c for c in approved if (c["name"], c["command"]) not in now]
    for c in out["changed"]:
        if why := read_only_command(c["command"], tree):
            out["off_list"].append({**c, "why": why})
    if out["off_list"]:
        listed = "; ".join(f"{c['name']}: `{c['command']}` ({c['why']})" for c in out["off_list"])
        return {**out, "why": f"{CHANGED}, and a changed check isn't read-only: {listed}"}
    record = read_checks_record(factory.land_checks_path(folder, factory.land_round(folder) or 1))
    if record is None or record["judged"] != sha[:16]:
        return {**out, "step": "checks", "why": f"{CHANGED}: the approver judges what changed"}
    if record["answer"] == "HARMLESS":
        why = f"{CHANGED}: read-only by the list, and judged harmless by the approver"
        return {**out, "clear": True, "why": why}
    said = record["said"][:300] or "no reasons given"
    if record["answer"] is None:
        said = ("its reply holds no CHECKS: HARMLESS or CHECKS: ESCALATE the script reads "
                "(first, or the only answer it gives)")  # fmt: skip
    return {**out, "why": f"{CHANGED}, and the approver didn't clear it: {said}"}


def _accept_state(root: Path, folder: Path, settled: bool = False) -> str | None:
    """The latest accept attempt's verdict when it ran on the build as it stands, else None.
    `settled` reads a landing round already reviewed, as `_land_gate_state()` does: its verdict
    stands whatever `HEAD` is now, which the landing's own record and later rebases move."""
    record = factory.read_gate_file(factory.accept_path(folder)) or {"attempts": []}
    last = record["attempts"][-1] if record["attempts"] else None
    ran_on = last and (settled or last["build"] == factory.accept_build(root, folder))
    return last["verdict"] if ran_on else None


def _note_says(folder: Path, line_re: re.Pattern) -> bool:
    """Whether `findings.md`'s note, before its first finding, holds a line `line_re` reads."""
    path = folder / "findings.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        if line.startswith("## "):
            break
        if line_re.match(line.strip()):
            return True
    return False


def _unreviewed_at_test(root: Path, folder: Path, cfg: dict) -> list[str] | None:
    """`land_unreviewed()` for a change at `stage: test`, before any landing rebase can move a
    file; nothing for one already shipped."""
    meta = factory.frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    return land_unreviewed(root, folder, cfg) if meta.get("stage") == "test" else []


def land_message(
    root: Path,
    folder: Path,
    by: str,
    refs: bool,
    nits: list[str] = (),
    unreviewed: list[str] | None = (),
) -> str:
    """The landed change's commit message: its title, its Problem's first sentence and its folder,
    a `Retired nits:` paragraph naming each nit it took in, ship's `Carried forward:`, `Dropped:`
    and `How to recover:` paragraphs, each when it holds anything (read from `notes.md`'s ticks
    and `decision.md`'s `- RECOVER:` lines, so a rerun's message is the same), as `/sdlc:ship`
    writes them, the paths changed since its last review (`unreviewed`, None when there is no
    snapshot to compare), `Refs #N` when its number is its issue's, and who passed the gate, with
    `unreviewed=<n|unknown>` when anything is. No `Sdlc-Findings`: the factory's rounds stood in
    for ship's review, and retro reads a missing line as unanswered. Paths go in the body, never
    in a trailer."""
    text = (folder / "intent.md").read_text(encoding="utf-8")
    title = next((ln for ln in text.splitlines() if ln.startswith("# ")), f"# {folder.name}")
    title = re.sub(r"^#\s+\d{3,}\s+—\s+", "", title).lstrip("# ").strip()
    problem = text.split("## Problem", 1)[1] if "## Problem" in text else ""
    prose = " ".join(problem.split("\n## ", 1)[0].split())
    first = factory.first_sentence(prose)
    body = f"{first} See {folder.relative_to(root).as_posix()}/.".strip()
    paragraphs = [title, body]
    notes = folder / "notes.md"
    ticked = [m for line in (notes.read_text(encoding="utf-8").splitlines() if notes.is_file()
                             else []) if (m := factory.TICKED_RE.match(line))]  # fmt: skip
    carried = [f"- {m.group(1)} → {m.group(3)}" for m in ticked if m.group(2) == "seed"]
    dropped = [f"- {m.group(1)}: {m.group(3)}" for m in ticked if m.group(2) == "dropped"]
    recover = [f"- {subject}: {way}" for subject, way in read_proposals(folder)[1]]
    retired = [f"- {n}: taken in by {folder.name}" for n in nits]
    for head, lines in (("Retired nits:", retired), ("Carried forward:", carried),
                        ("Dropped:", dropped), ("How to recover:", recover)):  # fmt: skip
        if lines:
            paragraphs.append("\n".join([head, *lines]))
    landed = f"{factory.LANDED}: by={by}"
    if unreviewed is None:
        paragraphs.append("No snapshot of its last review.")
        landed += " unreviewed=unknown"
    elif unreviewed:
        paragraphs.append(f"Changed since its last review: {', '.join(unreviewed)}")
        landed += f" unreviewed={len(unreviewed)}"
    tail = [f"Refs #{int(folder.name.split('-')[0])}"] if refs else []
    tail.append(landed)
    return "\n\n".join([*paragraphs, "\n".join(tail)]) + "\n"


def _set_impact(intent: Path, impact: str) -> bool:
    """`intent.md`'s `impact:` line set in place, by line, never through YAML."""
    lines = intent.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            break
        if line.split(":", 1)[0].strip() == "impact":
            lines[i] = f"impact: {impact}\n"
            intent.write_text("".join(lines), encoding="utf-8", newline="\n")
            return True
    return False


def _fresh_round(folder: Path, mine: dict) -> None:
    """Open a landing round for a train's change already in place, when its newest round is an
    earlier train's (`rounds_before`, from `train --begin`): a change brought up to date by hand
    after an ejection would otherwise be judged by that landing's replies. A stack that moves a
    change opens its round itself."""
    if (n := factory.land_round(folder)) and n == mine.get("rounds_before"):
        (folder / "reviews" / f"land-{n + 1}").mkdir(parents=True, exist_ok=True)


def filed_nit(text: str, change: str, nit: dict) -> bool:
    """Whether the register `text` already holds `nit` for `change`: a `[nit]` entry whose
    `Raised by:` names the change and whose body holds the nit's text. Never by title alone."""
    entry, fenced = None, False
    for line in [*text.splitlines(), "## end"]:
        if factory.FENCE_RE.match(line):
            fenced = not fenced
        if fenced or not line.startswith("## "):
            if entry is not None:
                entry.append(line)
            continue
        if entry is not None:
            body = "\n".join(entry)
            raised = re.search(rf"^Raised by: {re.escape(change)}\b", body, re.M)
            if raised and nit["text"] in body:
                return True
        entry = [] if factory.NIT_RE.match(line) else None
    return False


def _dispose(root: Path, folder: Path, pre: dict) -> tuple[list[str], str | None]:
    """What the person's yes approved for change `folder`'s undone notes, its agents' nits and its
    assumed decisions, written in its worktree before `sdlc.py ship`, every edit by line: each
    carried item appended to the change's `entries.md` (never the register, which close files it
    into) as an `[idea]` seed, each approved bug as a `[bug]` with its `Severity:` and `Paths:`
    and no `Introduced by:`, and each nit to file (`land_parts()`'s `nits`) as a `[nit]` with its
    `Theme:`, `Paths:`, `Cost:`, `Value:` and `Raised by:` (ids from one `next-entry` call; the
    file started with its title when missing), each item ticked
    `→ seed: <id>` or `→ bug: <id>`, each dropped one ticked `→ dropped: <reason>`, and each
    assumed decision ticked as confirmed. What a rerun finds ticked, or filed (`filed_nit()`), it
    never writes again. The ids of the nits it filed, and None or why nothing was
    written."""
    cfg, _ = factory.load_config(root)
    parts = land_parts(folder, pre, root, cfg)
    seeds = [u for u in parts["undone"] if "seed" in u or "bug" in u]
    notes, ids, filed = folder / "notes.md", [], []
    nits = parts["nits"]
    if seeds or nits:
        held = folder / ENTRIES
        text = held_text(folder)
        nits = [n for n in nits if not filed_nit(text, folder.name, n)]
    if seeds or nits:
        want = len(seeds) + len(nits)
        code, _, said = factory._sdlc(["next-entry", "--count", str(want)], root)
        ids = [w for w in said.split() if re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d+", w)]
        if code or len(ids) != want:
            return [], f"sdlc.py next-entry gave no ids: {said.strip()[-300:]}"
        rel = folder.relative_to(root).as_posix()
        for entry_id, item in zip(ids, seeds, strict=False):
            if bug := item.get("bug"):
                text = text.rstrip("\n") + (
                    f"\n\n## [{entry_id}] [bug] {bug['title']}\n\nFound by the review of "
                    f"{folder.name}.\n{item['text']}\n\nSeverity: {bug['severity']}\n"
                    f"Paths: {', '.join(bug['paths'])}\n"
                )
                continue
            text = text.rstrip("\n") + (
                f"\n\n## [{entry_id}] [idea] {item['seed']}\n\nLeft undone by {folder.name}, "
                f"carried forward when it landed: {item['text']}\nSee {rel}/notes.md in its "
                f"commit.\nRaised {entry_id[:10]}.\n"
            )
        for entry_id, nit in zip(ids[len(seeds) :], nits, strict=True):
            text = text.rstrip("\n") + (
                f"\n\n## [{entry_id}] [nit] {nit['title']}\n\nRaised by the {nit['role']} "
                f"review of {folder.name}, round {nit['round']}: {nit['text']}\n\n"
                f"Theme: {nit['theme']}\nPaths: {', '.join(nit['paths'])}\nCost: {nit['cost']}\n"
                f"Value: {nit['value']}\nRaised by: {folder.name} ({nit['pass']})\n"
            )
            filed.append(entry_id)
        held.write_text(text, encoding="utf-8", newline="\n")
    if parts["undone"]:
        lines = notes.read_text(encoding="utf-8").splitlines()
        given = iter(ids)
        for item in parts["undone"]:
            if "dropped" in item:
                said = f"dropped: {item['dropped']}"
            else:
                said = f"{'bug' if 'bug' in item else 'seed'}: {next(given)}"
            at = item["line"] - 1
            lines[at] = lines[at].replace("[ ]", "[x]", 1).rstrip() + f" → {said}"
        notes.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    if parts["assumed"]:
        ledger = folder / "decisions.md"
        lines = ledger.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            m = factory.LEDGER_RE.match(line)
            if m and m.group(1) == " " and m.group(4) == "default":
                lines[i] = "- [x]" + line.rstrip()[5:] + factory.DECIDED + factory.CONFIRMED
        ledger.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return filed, None


def _land_readiness(root: Path, folder: Path, by: str) -> dict:
    """Whether `land --by` can take change `folder`, read before anything is written: `refusal`,
    why it can't at all (not ready, `ship it by hand`, or `the gate is the person's` for `auto`
    with a signal standing), else None; `before`, what the skill runs first at `stage: test`
    (`accept`, `cases`); and what the landing reads on the way (`meta`, `impact`, `pre`,
    `unreviewed`). The gate's rule is the script's, never only the skill's: a change only a
    person can ship is refused whoever passed the gate. The train's reading asks the same
    question before it names `commit`."""
    out: dict = {"refusal": None, "before": [], "pre": None, "unreviewed": (), "impact": None}
    out["meta"] = meta = factory.frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    out["impact"] = impact = read_impact(folder)
    decision = factory.read_decision(folder)[0]
    if meta.get("stage") not in ("test", "shipped") or decision is None:
        return {**out, "refusal": f"{folder.name} isn't ready: stage test with a decision"}
    if (
        meta.get("stage") == "shipped"
        and not _commit_failed(root, folder)
        and (
            f"\n{factory.LANDED}: "
            not in "\n" + (factory._git(root, "log", "-1", "--format=%B") or "")
        )
    ):
        # A commit a person made, `stage: shipped` in it: never amended into or committed over.
        return {**out, "refusal": (
            f"HEAD isn't the landing's commit: {folder.name} was shipped by hand, so /sdlc:close "
            "closes it"
        )}  # fmt: skip
    cfg, _ = factory.load_config(root)
    pre, said = _preflight(folder, root)
    if pre is None:
        return {**out, "refusal": f"preflight couldn't be read: {said.strip()[-300:]}"}
    out["pre"] = pre
    out["unreviewed"] = unreviewed = _unreviewed_at_test(root, folder, cfg)
    signals, excluded = land_signals(folder, root, decision, cfg, pre, unreviewed=unreviewed)
    if excluded:
        return {**out, "refusal": f"ship it by hand: {'; '.join(excluded)}"}
    if by == "auto" and signals:
        return {**out, "refusal": f"the gate is the person's: {'; '.join(signals)}"}
    if meta.get("stage") == "test":
        if impact is None:
            return {**out, "refusal": "no impact to set: decision.md has no - IMPACT:"}
        if (pre.get("checks") or {}).get("checks") and _accept_state(root, folder) != "PASS":
            out["before"].append("accept")
        if (pre.get("cases") or {}).get("scope") and not _note_says(folder, factory.CASES_RE):
            out["before"].append("cases")
    return out


def cmd_land(root: Path, ident: str, by: str) -> int:
    """Land change `ident`'s first half, in its worktree: the approver's impact on `intent.md`,
    `sdlc.py ship` (stamped, every path staged; the seed is retired at close) and the commit with
    `land_message()`; `filed_nits`, the `[nit]` entries the person's yes filed (`_dispose()`). It
    stops there, `state: committed`, the commit the train's pre-train commit: bringing the change
    up to date is the train's (`cmd_train()`, `resolve --onto`), never a rebase here. A change
    landed before, its commit made, is `committed` again with nothing written. Or `refused`,
    with why."""
    folder, refusal = factory.find_change(root, ident)
    out: dict = {"change": None, "state": "refused", "refusals": [], "filed_nits": []}
    if refusal:
        return factory.emit({**out, "refusals": [refusal]}, 1)
    out["change"] = folder.name
    nits: list[str] = []
    ready_ = _land_readiness(root, folder, by)
    if ready_["refusal"]:
        return factory.emit({**out, "refusals": [ready_["refusal"]]}, 1)
    meta, impact, pre, unreviewed = (ready_[k] for k in ("meta", "impact", "pre", "unreviewed"))
    if meta.get("stage") == "test":
        # Every refusal before the first write: what the person's yes approved running has run,
        # on the change as it stands.
        num = folder.name.split("-")[0]
        if "accept" in ready_["before"]:
            why = (f"its acceptance checks haven't passed on the change as it stands: run "
                   f"factory.py accept {num}")  # fmt: skip
            return factory.emit({**out, "refusals": [why]}, 1)
        if "cases" in ready_["before"]:
            why = f"its skills' cases haven't run: run factory.py cases {num}"
            return factory.emit({**out, "refusals": [why]}, 1)
        if not _set_impact(folder / "intent.md", impact):
            return factory.emit(
                {**out, "refusals": ["no impact to set: intent.md has no impact: line"]}, 1
            )
        if by == "person":
            out["filed_nits"], refused = _dispose(root, folder, pre)
            if refused:
                return factory.emit({**out, "refusals": [refused]}, 1)
        if (pre.get("risk") or {}).get("deep") and not _note_says(folder, factory.FRESH_RE):
            factory._note_line(folder, factory.FRESH_RE, factory.FRESH_SKIPPED)
        nits = factory.named_nits(root, folder)
        # Before ship stages every path, so the step goes into the change's commit.
        factory._record_land(root, folder, "ship")
        code, _, said = factory._sdlc(["ship", folder.name], root)
        if code:
            why = f"sdlc.py ship refused: {said.strip()[-500:]}"
            plain = SHIP_REFUSED.format(id=folder.name.split("-")[0])
            return _land_refused(root, folder, out, why, plain)
        # The nits the change took in are retired at close, from `Retire` lines in its
        # `entries.md`: after ship, so every refusal of its comes before this write.
        if nits:
            retire_nits(folder, nits)
            factory._git(root, "add", "--", (folder / ENTRIES).relative_to(root).as_posix())
        if why := _land_commit(root, folder, by, nits, unreviewed):
            plain = "its commit failed: the landing's output gives git's words; rerun it once fixed"
            return _land_refused(root, folder, out, why, plain)
    elif _commit_failed(root, folder):
        # Shipped, but its commit never made: ship again (a rerun is harmless) and commit what
        # the first run would have. Its disposals, checks and impact ran before ship stamped it.
        factory._record_land(root, folder, "ship")
        code, _, said = factory._sdlc(["ship", folder.name], root)
        if code:
            why = f"sdlc.py ship refused: {said.strip()[-500:]}"
            plain = SHIP_REFUSED.format(id=folder.name.split("-")[0])
            return _land_refused(root, folder, out, why, plain)
        # The nits it takes in, retired as the first run would have, whether or not it got that far.
        nits = factory.named_nits(root, folder)
        if nits:
            retire_nits(folder, nits)
            factory._git(root, "add", "--", (folder / ENTRIES).relative_to(root).as_posix())
        if why := _land_commit(root, folder, by, nits, unreviewed):
            plain = "its commit failed: the landing's output gives git's words; rerun it once fixed"
            return _land_refused(root, folder, out, why, plain)
    # Else landed before, its commit made: it stands, and the train stacks it.
    out.update(head=factory._git(root, "rev-parse", "--short", "HEAD"), retired_nits=nits)
    out.update(state="committed", round=factory.land_round(folder) or None)
    return factory.emit(out)


def _land_commit(
    root: Path, folder: Path, by: str, nits: list[str], unreviewed: list[str] | None
) -> str | None:
    """The landing's one commit of what `sdlc.py ship` staged, with `land_message()`: None, or
    why it failed, in git's own words (the tail of its stderr, else its stdout)."""
    _, cfg_out, _ = factory._sdlc(["config"], root)
    refs = ((cfg_out or {}).get("archive") or {}).get("ids_from") == "github"
    message = land_message(root, folder, by, refs, nits, unreviewed)
    try:
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-F", "-"], input=message,
            capture_output=True, encoding="utf-8", check=True,
        )  # fmt: skip
    except subprocess.CalledProcessError as e:
        said = (e.stderr or "").strip() or (e.stdout or "").strip() or str(e)
        return f"the commit failed: {said[-500:]}"
    except OSError as e:
        return f"the commit failed: {e}"
    return None


def _commit_failed(root: Path, folder: Path) -> bool:
    """Whether a landing stopped after `sdlc.py ship` and before its commit: `HEAD`'s message has
    no `Sdlc-Landed:` line and `HEAD`'s `intent.md` isn't shipped. One a person shipped and
    committed by hand says `stage: shipped` in `HEAD`, and is never committed again."""
    if f"\n{factory.LANDED}: " in "\n" + (factory._git(root, "log", "-1", "--format=%B") or ""):
        return False
    rel = (folder / "intent.md").relative_to(root).as_posix()
    return (
        factory.frontmatter(factory._git(root, "show", f"HEAD:{rel}") or "").get("stage")
        != "shipped"
    )


def _status_entries(root: Path) -> list[tuple[str, str]] | None:
    """Each entry `git status --porcelain -z --untracked-files=all` prints for `root`, as its
    two-letter `XY` code and its path, read as git printed it: never through `_git()`, whose strip
    takes the first entry's leading space (` M path`) and so a character of its path. A rename's
    old path is skipped. None when git fails."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "-z", "--untracked-files=all"],
            capture_output=True, encoding="utf-8", check=True,
        )  # fmt: skip
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    entries, found = done.stdout.split("\0"), []
    i = 0
    while i < len(entries):
        entry = entries[i]
        if len(entry) > 3:
            found.append((entry[:2], entry[3:]))
            if entry[0] in "RC":
                i += 1
        i += 1
    return found


def _dirty(root: Path) -> list[str] | None:
    """Every path `root` has uncommitted, untracked ones included (`_status_entries()`). None
    when git fails."""
    entries = _status_entries(root)
    return None if entries is None else [path for _, path in entries]


# `git status`'s codes for an unmerged path: the files a conflict left for its resolution.
UNMERGED = ("DD", "AU", "UD", "UA", "DU", "AA", "UU")


def _stray(root: Path, records: list[str]) -> list[str] | None:
    """The paths a resolution changed in its worktree outside its conflicted files and the
    change's landing `records` (root-relative POSIX paths), from one `_status_entries()` listing:
    an entry that isn't unmerged whose worktree column isn't blank, or an untracked one (`??`). A
    staged path (worktree column blank) is never judged here: `--continue` holds each to
    `REBASE_HEAD`'s own paths (`_replayed()`, `_staged()`). None when git fails."""
    entries = _status_entries(root)
    if entries is None:
        return None
    allowed = {*records, *(path for xy, path in entries if xy in UNMERGED)}
    return [
        path for xy, path in entries
        if xy not in UNMERGED and (xy == "??" or xy[1] != " ") and path not in allowed
    ]  # fmt: skip


def _z_listing(root: Path, *args: str) -> list[str] | None:
    """The `\\0`-separated fields a git listing prints in `root`, read as git printed them: never
    through `_git()`, whose strip takes a leading space. None when git fails."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [f for f in done.stdout.split("\0") if f]


def _replayed(root: Path) -> dict[str, str] | None:
    """`REBASE_HEAD`'s own paths, each with its status letter (`A`, `M`, `D`, ...), from one
    listing of the commit a rebase is replaying: a rename is its deletion and its addition. Read
    only while a rebase is under way, since `REBASE_HEAD` outlives it. None when git fails."""
    fields = _z_listing(
        root, "diff-tree", "-r", "--root", "--no-commit-id", "--no-renames", "--name-status", "-z",
        "REBASE_HEAD",
    )  # fmt: skip
    if fields is None or len(fields) % 2:
        return None
    return {fields[i + 1]: fields[i][:1] for i in range(0, len(fields), 2)}


def _staged(root: Path) -> list[str] | None:
    """Every path the index holds differently from `HEAD`, unmerged ones included: what the next
    commit would add. A rename is its old path and its new one (`--no-renames`), so a `git mv`
    can't hide the path it took away. None when git fails."""
    return _z_listing(root, "diff", "--cached", "--name-only", "--no-renames", "-z")


def _neither_side(root: Path, path: str) -> bool:
    """Whether `path`'s text in `root` is neither `HEAD`'s nor `REBASE_HEAD`'s: a resolution
    changed it, whether it is staged or not. True when git can't hash it."""
    mine = factory._git(root, "hash-object", "--", path)
    sides = [factory._git(root, "rev-parse", "-q", "--verify", f"{rev}:{path}")
             for rev in ("HEAD", "REBASE_HEAD")]  # fmt: skip
    return mine is None or mine not in sides


def _amend_record(root: Path, folder: Path, also: list[str] = ()) -> str | None:
    """The landing's own record (its gate, its review, a resolved conflict's marker, the run's
    costs), written after the change's commit, amended into that commit, so the change lands as
    one commit, and `sdlc.py base` and `close` find the worktree clean. Why not, or None: anything
    dirty outside the change's folder is not the landing's, and is refused, but the paths `also`
    names: a fix the builder made at landing (`cmd_land_fix()`), staged with the record."""
    dirty = _dirty(root)
    if dirty is None:
        return "git status couldn't be read"
    rel = folder.relative_to(root).as_posix() + "/"
    stray = [p for p in dirty if not p.startswith(rel) and p not in also]
    if stray:
        return f"uncommitted outside the change's folder: {', '.join(stray)}"
    if dirty:
        if f"\n{factory.LANDED}: " not in "\n" + (
            factory._git(root, "log", "-1", "--format=%B") or ""
        ):
            return "HEAD isn't the landing's commit, so its record has nothing to be amended into"
        factory._git(root, "add", "--", rel, *also)
        if factory._git(root, "commit", "-q", "--amend", "--no-edit") is None:
            return "the landing's record couldn't be added to the commit"
    return None


def _close_stopped(root: Path, folder: Path, why: str, plain: str | None = None) -> int:
    """A stop at the landing's close: recorded, the plain line (what failed and what to do, for the
    board) over the raw `why`, then amended in with the round it stopped on, as `_amend_record()`
    takes the rest, so the person's `/sdlc:ship` finds the worktree clean and `sdlc.py base` can
    rebase it. Nothing has landed yet, so the commit is still the branch's own; an amend that
    can't be made leaves the record uncommitted, as before."""
    factory._record_land(root, folder, "stop", [plain, why] if plain and plain != why else [why])
    _amend_record(root, folder)
    return factory.emit({"refusals": [why]}, 1)


def _train_moved(root: Path, folder: Path, state: dict, tip: str) -> int:
    """The base moved under the train: every change not landed re-stacks onto its new tip, is
    gated again at the new tip, and the move counts once for the train (`state: moved`)."""
    state["moves"] += 1
    state["base_tip"] = state["expected"] = tip
    for name in train_live(state):
        state["changes"][name]["stacked"] = None
    write_train(root, state)  # before the record, which reads the train's moves from it
    factory._record_land(root, folder, "stack")
    if why := _amend_record(root, folder):
        return _close_stopped(root, folder, why, _amend_plain(why, folder.name.split("-")[0]))
    return factory.emit({"change": folder.name, "state": "moved", "moves": state["moves"]})


def cmd_land_close(root: Path, ident: str) -> int:
    """Land change `ident`'s second half: `sdlc.py close` run from the main checkout (from inside
    the change's worktree it would keep the worktree), which merges, archives, removes the folder,
    the worktree and the branch, and pushes as `git.push` says. Its JSON passes through. In a
    train (`train_names()`), only the next change to close: the base's tip is checked against the
    tip the train expects (another tip is a move: counted once for the train, every change not
    landed unstacked to stack on the base anew, `state: moved`, nothing closed), the change's own
    commits are rebased onto the base past the `Close` commits before it (`--onto <base> <on>`),
    its `runs/land-train.md` and record amended in, and after the close the train records it
    landed and the new tip it expects. Outside a train a base that moved is a stop: the train is
    what brings a change up to date."""
    folder, refusal = factory.find_change(root, ident)
    if refusal:
        return factory.emit({"refusals": [refusal]}, 1)
    # Before the amend, so the step is in the commit close merges.
    factory._record_land(root, folder, "close")
    # A batch that passed itself closes a change resolved while landing only once its review
    # passed: the script's rule, never only the skill's. Read before the amend moves `HEAD`. Only
    # the landing's signal: `land` read the rest before it committed, and its own rebase can move
    # the files `conflicts.md` names with nothing resolved.
    num = folder.name.split("-")[0]
    if f"\n{factory.LANDED}: by=auto" in "\n" + (
        factory._git(root, "log", "-1", "--format=%B") or ""
    ):
        cfg, _ = factory.load_config(root)
        if LANDING_RESOLVED in resolution_signals(root, folder, cfg):
            why = f"landed by=auto, and {LANDING_RESOLVED}: no landing review has passed it"
            plain = (
                "the landing passed itself, but it resolved a conflict that no landing "
                "review has passed: read the resolution (runs/land-resolved names the files), "
                f"then /sdlc:close {num} by hand"
            )
            return _close_stopped(root, folder, why, plain)
        if list(folder.glob("build/land-*.ask.md")):
            why = f"landed by=auto, and {LANDING_FIXED}: the gate is the person's"
            plain = (
                "the landing passed itself, but a fix was made while it landed, which only you "
                f"may pass: read the fix (build/land-<n>.ask.md says what was asked), then "
                f"/sdlc:close {num} by hand"
            )
            return _close_stopped(root, folder, why, plain)
    # The base branch moved since the change was gated and reviewed: close would only refuse (it
    # fast-forwards), so the landing goes back to its rebase, `land` again, with the move
    # recorded before the amend so the commit it was found on carries it.
    cfg, _ = factory.load_config(root)
    # The landing's review rounds join carry's record before it is amended in, every rerun
    # included; with none reviewed, carry's file stands as it is.
    landing, _ = factory.read_rounds(folder, [], "land")
    for r in landing:
        r["complete"] = bool(r["reviews"])
    if any(r["complete"] for r in landing):
        factory.write_findings(folder, factory._rounds_at_depth(root, folder, cfg)[0] + landing)
    main = factory.worktrees(root)[0][0] if factory.worktrees(root) else root
    named = train_names(root, folder)
    if named is None:
        # Outside a train nothing rebases: a base that moved since the change was gated is the
        # train's to follow, never this command's.
        if _behind(root) > 0:
            base = factory._base(root) or "the base branch"
            why = (f"{base} moved since {folder.name} was gated: run /sdlc-factory:land again, "
                   "which stacks it on the base anew")  # fmt: skip
            return _close_stopped(root, folder, why)
        if why := _amend_record(root, folder):
            return _close_stopped(root, folder, why, _amend_plain(why, num))
    else:
        state, mine = named
        if (first := train_live(state)[0]) != folder.name:
            why = f"{folder.name} isn't the next change to close: {first} is"
            return factory.emit({"change": folder.name, "refusals": [why]}, 1)
        base = state["base"]
        tip = factory._git(root, "rev-parse", f"refs/heads/{base}") or ""
        head = factory._git(root, "rev-parse", "HEAD") or ""
        _write_train_record(root, folder, state, folder.name)
        merged = _is_ancestor(root, head, tip)  # a close that stopped after its merge, rerun
        if tip != state["expected"] and not merged:
            return _train_moved(root, folder, state, tip)
        if why := _amend_record(root, folder):
            return _close_stopped(root, folder, why, _amend_plain(why, num))
        if not merged and mine.get("on") and mine["on"] != tip:
            # Past the `Close` commits of the changes before it: its own commits, replayed onto
            # the base, whose tree differs from what it sat on only under the change folders.
            onto = f"refs/heads/{base}"
            done = subprocess.run(
                ["git", "-C", str(root), "rebase", "-q", "--onto", onto, mine["on"]],
                capture_output=True, encoding="utf-8", env={**os.environ, "GIT_EDITOR": "true"},
            )  # fmt: skip
            if done.returncode:
                factory._git(root, "rebase", "--abort")
                said = (done.stderr or done.stdout).strip()[-300:]
                why = f"rebasing {folder.name} onto {base} past the Close commits failed: {said}"
                return _close_stopped(root, folder, why)
            mine["on"] = tip
            write_train(root, state)
    code, closed, said = factory._sdlc(["close", ident], main)
    if named is not None:
        # Landed once the base's tip is this change's `Close`; the next change's close expects
        # that tip, and stacks on this change's stacked commit as it did.
        state, mine = named
        tip = factory._git(main, "rev-parse", f"refs/heads/{state['base']}") or ""
        if tip and factory._git(main, "log", "-1", "--format=%s", tip) == f"Close {folder.name}":
            mine["landed"] = state["expected"] = tip
            state["base_tip"] = mine["stacked"]
            write_train(main, state)
        elif code and not (closed or {}).get("done") and tip != state["expected"]:
            # A move racing the close, read from the base, never from close's words.
            return _train_moved(root, folder, state, tip)
    if code and not (closed or {}).get("done") and folder.is_dir():
        plain = (closed or {}).get("refusals") or [
            f"sdlc.py close failed: run /sdlc:close {ident} by hand to see why"
        ]
        factory._record_land(root, folder, "stop", plain)
        _amend_record(root, folder)
    return factory.emit(closed or {"refusals": [said.strip()[-500:]]}, code)


def _behind(root: Path) -> int:
    """How many commits the base branch has that the change's branch lacks: 0 when it hasn't
    moved, or when there is no base to count."""
    base = factory._base(root)
    count = factory._git(root, "rev-list", "--count", f"HEAD..refs/heads/{base}") if base else None
    return int(count) if count and count.isdigit() else 0


def cmd_land_fix(root: Path, ident: str, ask: str | None, commit: bool) -> int:
    """A fix the person asked for at landing, after the change's commit. `ask`: the id (`R3`) of
    the person's ticked `(person, fix)` line in `decisions.md`, never their words; on a shipped
    change whose landing round under way no reviewer has answered, take that round `land-<n>`,
    or, when it passed or none is open, open round `land-<n+1>`, and copy the line's words to
    `build/land-<round>.ask.md`, for the builder (`agent --task
    land-fix`) and then every reviewer at the run's depth. `commit`: amend what the builder
    changed outside the folder (`fixed`) into the change's commit through `_amend_record()`, so
    the new `HEAD` is gated again before its review. With nothing changed, it goes on only when the
    builder's report answers `FIX: ALREADY MADE` with its evidence (`_not_already_made()`), and
    amends nothing (`already_made`): the ask file stays, so the fix is still a signal (181)."""
    folder, refusal = factory.find_change(root, ident)
    if refusal:
        return factory.emit({"refusals": [refusal]}, 1)
    n = factory.land_round(folder)
    out = {"change": folder.name}
    if commit:
        if factory.land_ask(folder, n) is None:
            return factory.emit(
                {**out, "refusals": ["no fix was asked for: run land-fix --ask first"]}, 1
            )
        dirty = _dirty(root)
        if dirty is None:
            return factory.emit({**out, "refusals": ["git status couldn't be read"]}, 1)
        rel = folder.relative_to(root).as_posix() + "/"
        fixed = [p for p in dirty if not p.startswith(rel)]
        if not fixed:
            if refusals := _not_already_made(root, folder, n):
                return factory.emit({**out, "refusals": refusals}, 1)
        elif why := _amend_record(root, folder, also=fixed):
            return factory.emit({**out, "refusals": [why]}, 1)
        _train_fix(root, folder, done=True)
        head = factory._git(root, "rev-parse", "--short", "HEAD")
        made = {"fixed": fixed, "already_made": not fixed, "head": head}
        return factory.emit({**out, "round": n, **made})
    meta = factory.frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    if meta.get("stage") != "shipped":
        return factory.emit({**out, "refusals": [f"{folder.name} isn't shipped: land it first"]}, 1)
    words = read_fix_words(folder, ask or "")
    if words is None:
        why = f"{ask} isn't a `- [x] {ask} (person, fix): …` line in decisions.md"
        return factory.emit({**out, "refusals": [why]}, 1)
    cfg, _ = factory.load_config(root)
    # A round a stack opened, which no reviewer has answered yet, takes the fix itself, so its
    # review reads it at the run's depth (154); one answered takes it only once it has passed.
    # A round counted, its folder gone by now, is one no reviewer has answered (nit -80).
    answered = n and (d := folder / "reviews" / f"land-{n}").is_dir() and any(d.iterdir())
    untouched = n and factory.land_ask(folder, n) is None and not answered
    if n and not untouched and land_verdict(root, folder, cfg, n)["next"] != "pass":
        why = f"landing round {n} hasn't passed: a fix is asked only after it does"
        return factory.emit({**out, "refusals": [why]}, 1)
    k = n if untouched else n + 1
    (folder / "reviews" / f"land-{k}").mkdir(parents=True, exist_ok=True)
    path = factory.land_ask_path(folder, k)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(words + "\n", encoding="utf-8", newline="\n")
    _train_fix(root, folder, opened=k)
    return factory.emit({**out, "round": k, "ask": path.relative_to(root).as_posix()})


def _not_already_made(root: Path, folder: Path, n: int) -> list[str]:
    """Why an empty fix in landing round `n` can't go on: no builder's report, no
    `FIX: ALREADY MADE` answer `opening()` reads in it, or its `## Evidence` failing
    `read_evidence()`; empty when the builder says, with its evidence, that the fix was already
    made. Each case is worded once, short, the answer named only where it is missing (nit -47)."""
    path = folder / "build" / f"land-{n}.md"
    rel = path.relative_to(folder).as_posix()
    nothing = "the builder changed nothing outside the change's folder"
    if not path.is_file():
        return [f"{nothing}, and wrote no report ({rel})"]
    text = path.read_text(encoding="utf-8")
    found = factory.opening(text.splitlines(), factory.FIX_RE)
    if found is None or found[1].group(1) != factory.FIX_MADE:
        return [f"{nothing}, and {rel} doesn't say `FIX: {factory.FIX_MADE}` first, or as its "
                "only answer"]  # fmt: skip
    if problems := factory.read_evidence(text, rel):
        return [f"{nothing}, and its report's evidence doesn't hold:", *problems]
    return []


def _train_fix(root: Path, folder: Path, opened: int | None = None, done: bool = False) -> None:
    """The fix a train stores for change `folder` (R9), marked as `land-fix` takes it: the round
    `--ask` opened, then done once `--commit` amended it in, so the train's `fix` step is taken
    once, and a loop killed between the two resumes past the `--ask`."""
    named = train_names(root, folder)
    fix = named[0].get("fix") if named else None
    if not fix or fix["change"] != folder.name:
        return
    if opened is not None:
        fix["round"] = opened
    if done:
        fix["done"] = True
    write_train(root, named[0])


# ---------------------------------------------------------------- the landing train
#
# `/sdlc-factory:land` lands its batch as a train: each change committed in its worktree (`land`),
# then stacked on the one before it in `land-check`'s order (`resolve --onto`), the base branch's
# gate run once at the tip (`gate --land`), a red tip bisected by prefix and the change at fault
# ejected (`train --eject`), each moved change's landing round reviewed as today (`land-verdicts`),
# and the changes closed in order (`land --close`, which rebases each onto the base past the
# `Close` commits before it and runs `sdlc.py close`). `train` is the one reader of the train's
# state, `TRAIN_STATE` in the git common dir, never in a tree: each reading names the next step and
# writes the state file alone, with what it derived (a change's pre-train commit, a gate's record,
# a stacked tree that changed). Branches move only by `resolve --onto`, `land --close`, `--eject`
# and `--stop`, each printing its undo.


TRAIN_STATE = "sdlc-factory-train.json"


def train_path(root: Path) -> Path | None:
    where = factory._slot_dir(root)
    return where / TRAIN_STATE if where else None


def write_train(root: Path, state: dict | None) -> None:
    """Write the train's state, or remove it (None): the train is over."""
    path = train_path(root)
    if path is None:
        return
    if state is None:
        path.unlink(missing_ok=True)
        return
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8", newline="\n")


def train_live(state: dict) -> list[str]:
    """The changes still in the train, in its order: neither ejected nor landed."""
    return [
        n for n in state["order"]
        if not state["changes"][n].get("ejected") and not state["changes"][n].get("landed")
    ]  # fmt: skip


def train_onto(state: dict, name: str) -> str | None:
    """What change `name` stacks on: the stacked commit of the live change before it, or, first
    in the train as it stands, `base_tip` (the base's tip at the start, the last landed change's
    stacked commit, or the base's tip after a move)."""
    live = train_live(state)
    before = live[: live.index(name)] if name in live else []
    return state["changes"][before[-1]]["stacked"] if before else state["base_tip"]


def _stacked(state: dict, name: str) -> bool:
    """Whether `name` sits where the train wants it: stacked, and on what it should stack on."""
    mine = state["changes"][name]
    onto = train_onto(state, name)
    return bool(mine.get("stacked")) and onto is not None and mine.get("on") == onto


def train_names(root: Path, folder: Path) -> tuple[dict, dict] | None:
    """The train under way and change `folder`'s entry in it, while it is live; else None."""
    state = factory.read_train(root)
    if state is None or folder.name not in train_live(state):
        return None
    return state, state["changes"][folder.name]


def _train_fail(root: Path, folder: Path, why: str) -> None:
    """A landing command's refusal, told to the train that names the change: its next reading
    ejects the change, and the rest of the train goes on (R8)."""
    named = train_names(root, folder)
    if named is None:
        return
    state, mine = named
    mine["failed"] = why
    write_train(root, state)


def _stacked_now(root: Path, folder: Path, state: dict, mine: dict) -> None:
    """A stack that finished: the change sits on what it was stacking onto."""
    mine["on"], mine["stacking"] = mine["stacking"], None
    mine["stacked"] = factory._git(root, "rev-parse", "HEAD")
    write_train(root, state)


def _is_ancestor(root: Path, older: str, newer: str) -> bool:
    return (
        bool(older and newer)
        and factory._git(root, "merge-base", "--is-ancestor", older, newer) is not None
    )


def _tree_changed(root: Path, a: str, b: str) -> bool:
    """Whether commits `a` and `b` differ outside `.sdlc/work/`: a fix amended into a stacked
    change, which what is above it must re-stack on; never the records, nor the `Close` commits'
    removals, which a rebase past them brings."""
    done = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", a, b, "--", ".",
         f":(exclude){factory.work_rel(root)}"],
        capture_output=True, encoding="utf-8",
    )  # fmt: skip
    return done.returncode == 1


def _train_took_part(root: Path, state: dict, name: str) -> list[dict]:
    """The train's gates change `name` took part in: those whose gated commit has its stacked
    commit as an ancestor, itself included."""
    stacked = state["changes"][name].get("stacked")
    return [g for g in state["gates"] if stacked and _is_ancestor(root, stacked, g["commit"])]


def train_record(state: dict, name: str, gates: list[dict]) -> str:
    """`runs/land-train.md`: the change's place in the train, what it stacked on, the tip's gate
    (verdict, commit, the change folder whose gate file holds it) and each gate it took part in."""
    order = state["order"]
    k, n = order.index(name) + 1, len(order)
    before = [c for c in order[: k - 1] if not state["changes"][c].get("ejected")]
    lines = [f"# {name} — landing train", "", f"TRAIN: {k} of {n}"]
    lines.append(f"STACKED ON: {before[-1] if before else state['base']}")
    tip = next((g for g in reversed(gates) if g["verdict"] == "PASS"), None)
    if tip:
        lines.append(f"TIP GATE: PASS {tip['commit'][:12]} {tip['file']}")
    lines += [f"GATE: {g['prefix']} {g['verdict']} {g['commit'][:12]} {g['file']}" for g in gates]
    return "\n".join(lines) + "\n"


def _write_train_record(root: Path, folder: Path, state: dict, name: str) -> None:
    text = train_record(state, name, _train_took_part(root, state, name))
    (folder / factory.LAND_TRAIN).parent.mkdir(parents=True, exist_ok=True)
    (folder / factory.LAND_TRAIN).write_text(text, encoding="utf-8", newline="\n")


def _landing_commit(tree: Path, name: str) -> str | None:
    """The branch's tip when it is the landing's commit (`Sdlc-Landed:` on it, its intent
    shipped), else None."""
    head = factory._git(tree, "rev-parse", f"refs/heads/{name}")
    if not head:
        return None
    body = factory._git(tree, "log", "-1", "--format=%B", head) or ""
    if f"\n{factory.LANDED}: " not in "\n" + body:
        return None
    intent = factory._git(tree, "show", f"{head}:{factory.work_rel(tree)}/{name}/intent.md") or ""
    return head if factory.frontmatter(intent).get("stage") == "shipped" else None


def _put_back(tree: Path, folder: Path, mine: dict) -> tuple[str | None, str | None]:
    """A change's branch back at its pre-train commit, `git reset --keep`, its records from the
    train's attempt (the gate files, its landing round, its steps) checked out into its folder
    for the caller to record over and amend in: the undo, and why it couldn't."""
    if factory._rebasing(tree):
        factory._git(tree, "rebase", "--abort")
    head = factory._git(tree, "rev-parse", "HEAD") or ""
    if not mine.get("pre") or head == mine["pre"]:
        return None, None
    _amend_record(tree, folder)  # dirty records into the stacked commit, so the reset is clean
    kept = factory._git(tree, "rev-parse", "HEAD") or head
    done = subprocess.run(
        ["git", "-C", str(tree), "reset", "-q", "--keep", mine["pre"]],
        capture_output=True, encoding="utf-8",
    )  # fmt: skip
    if done.returncode:
        return None, f"git reset --keep {mine['pre'][:12]} refused: {done.stderr.strip()[-300:]}"
    factory._git(tree, "checkout", "-q", kept, "--", folder.relative_to(tree).as_posix())
    marker = folder / "runs" / "land-resolved"
    if marker.is_file():
        first = marker.read_text(encoding="utf-8").splitlines()[:1]
        if first == [f"land-{factory.land_round(folder)}"]:
            marker.unlink()  # the resolution it names went with the stacked commit
    return f"git reset --keep {kept}", None


def cmd_train(
    root: Path,
    begin: list[str] | None = None,
    by: str | None = None,
    eject: str | None = None,
    stop: bool = False,
    run: bool = False,
    cancel: bool = False,
    fix: str | None = None,
) -> int:
    """The landing train. `--begin <NNN…> --by auto|person` starts one over the named ready
    changes in `ready`'s order, refused while one is under way (R19). The plain reading names the
    step the skill takes next and the change it is for, writing the state file alone: `commit`
    (`land <NNN> --by`, after `before`'s `accept` or `cases`), `stack` (`resolve <NNN> --onto
    <onto>`), `resolve` (the stack conflicts in `files`: `agent --task train-resolve`, then
    `resolve --continue`), `gate` (`gate <NNN> --land`, at the tip or a bisected prefix),
    `eject` (`train --eject <NNN>`, with its `reason` and `cause`: `gate`, `review` or
    `refusal`), `accept`, `review`, `arbitrate` and `mend` (as `land-verdicts` names them, in
    `verdict`), `fix` (the person's fix stored at `--begin --fix <NNN>=R<n>`, once that change
    sits in the stack, before any gate: `land-fix --ask`, unless `asked`, `agent --task
    land-fix`, `land-fix --commit`),
    `close` (`land <NNN> --close`), `stop` (`train --stop`, with its `reason`) or `done`.
    `--eject` puts the change at fault back at its pre-train commit, its records and the reason
    amended in, and the rest re-stack; `--stop` puts every change not landed back and ends the
    train (R11). `--run` takes the steps itself until `done` or a stop (`_run_loop()`), holding
    the run lock; `--cancel` asks a running loop to stop after the step in flight. While a loop
    runs, `--run`, `--begin`, `--eject` and `--stop` refuse and the plain reading says `running`,
    writing nothing, but in the loop's own children (`TRAIN_RUN_ENV`)."""
    trees = factory.worktrees(root)
    main = trees[0][0] if trees else root
    cfg, _ = factory.load_config(main)
    if cancel:
        return _train_cancel(main)
    if (run or not os.environ.get(TRAIN_RUN_ENV)) and train_running(main):
        if begin or eject or stop or run:
            return factory.emit({"refusals": [RUN_UNDER_WAY]}, 1)
        return factory.emit({"under_way": factory.read_train(main) is not None, "running": True})
    if run:
        return _train_run(main)
    if begin:
        return _train_begin(main, cfg, begin, by, fix)
    state = factory.read_train(main)
    if state is None:
        if eject or stop:
            return factory.emit({"refusals": ["no train is under way: run train --begin first"]}, 1)
        return factory.emit({"under_way": False, "next": None})
    if eject:
        return _train_eject(main, state, eject)
    if stop:
        return _train_stop(main, state)
    return _train_reading(main, cfg, state)


def _train_begin(
    main: Path, cfg: dict, idents: list[str], by: str | None, fix: str | None = None
) -> int:
    if (state := factory.read_train(main)) is not None:
        live = ", ".join(train_live(state)) or "nothing left"
        why = (f"a train is under way ({live}): run train to resume it, or train --stop to put "
               "its changes back")  # fmt: skip
        return factory.emit({"refusals": [why]}, 1)
    if by not in ("auto", "person"):
        return factory.emit({"refusals": ["train --begin needs --by auto|person"]}, 1)
    base = factory._base(main)
    if base is None:
        return factory.emit(
            {"refusals": ["no base branch: set [git] base in .sdlc/config.toml"]}, 1
        )
    picked = [
        r for r in factory.ready(main) if any(factory.names_change(r["change"], i) for i in idents)
    ]
    unmatched = [i for i in idents if not any(factory.names_change(r["change"], i) for r in picked)]
    if unmatched:
        return factory.emit({"refusals": [f"not ready to land: {', '.join(unmatched)}"]}, 1)
    stored = None
    if fix:
        # The person's fix (R9), by the id of its line in the change's `decisions.md`: made once,
        # as soon as that change is stacked, before the gate, by `train`'s `fix` step. Only the
        # person's yes asks for one.
        if by != "person":
            return factory.emit({"refusals": ["train --begin --fix needs --by person: a fix is "
                                              "asked for in the person's yes"]}, 1)  # fmt: skip
        ident, _, ask = fix.partition("=")
        at = next((r for r in picked if factory.names_change(r["change"], ident)), None)
        if at is None:
            return factory.emit({"refusals": [f"--fix names {ident}, which isn't in the batch"]}, 1)
        tree = Path(at["worktree"])
        if read_fix_words(tree / factory.work_rel(tree) / at["change"], ask) is None:
            why = (f"{ask} isn't a `- [x] {ask} (person, fix): …` line in {at['change']}'s "
                   "decisions.md")  # fmt: skip
            return factory.emit({"refusals": [why]}, 1)
        stored = {"change": at["change"], "ask": ask, "round": None, "done": False}
    tip = factory._git(main, "rev-parse", f"refs/heads/{base}") or ""
    # The landing round each change already has, from an earlier train: this train never judges
    # a change by that round's replies (`_fresh_round()` opens a new one).
    before, approved = {}, {}
    for r in picked:
        tree = Path(r["worktree"])
        folder = tree / factory.work_rel(tree) / r["change"]
        before[r["change"]] = factory.land_round(folder)
        # What the person's yes covered of its acceptance checks (185 R1): the file's hash, and
        # each check as the parser that runs them reads it. Where preflight can't be read, this
        # records `checks: []` beside the hash, which is safe: every check then counts as changed.
        sha = checks_sha(folder)
        approved[r["change"]] = {"checks_sha": sha,
                                 "checks": _checks_now(folder, tree)[0] if sha else []}  # fmt: skip
    state = {
        "base": base, "by": by, "order": [r["change"] for r in picked],
        "changes": {
            r["change"]: {"worktree": r["worktree"], "pre": None, "on": None, "stacked": None,
                          "stacking": None, "landed": None, "ejected": None, "failed": None,
                          "fault": None, "rounds_before": before[r["change"]],
                          **approved[r["change"]]}
            for r in picked
        },
        "base_tip": tip, "expected": tip, "moves": 0, "gates": [], "ejections": [],
        "began": factory._utc_now(), "fix": stored,
    }  # fmt: skip
    write_train(main, state)
    out = {"state": "begun", "order": state["order"], "by": by, "base": base, "tip": tip}
    if stored:
        out["fix"] = {"change": stored["change"], "ask": stored["ask"]}
    return factory.emit(out)


def _change_checkouts(main: Path) -> dict[str, Path]:
    """Each change's checkout by its branch, one mid-rebase included (its HEAD detached, its
    branch read from the rebase's own state, `current_branch()`), which `worktrees()` leaves out."""
    found = {}
    for path in factory._all_checkouts(main):
        branch = factory.current_branch(path)
        if factory.DIR_RE.match(branch):
            found[branch] = path
    return found


def _train_reading(main: Path, cfg: dict, state: dict) -> int:
    base = state["base"]
    trees = _change_checkouts(main)
    out: dict = {
        "under_way": True, "next": None, "change": None, "worktree": None, "by": state["by"],
        "base": base, "order": state["order"], "live": train_live(state),
        "landed": [n for n in state["order"] if state["changes"][n].get("landed")],
        "ejected": [{"change": e["change"], "reason": e["reason"],
                     "cause": e.get("cause") or "refusal"} for e in state["ejections"]],
        "moves": state["moves"], "limit": cfg["land"]["moves"], "gates": len(state["gates"]),
        "problems": [],
    }  # fmt: skip

    def done(step: str, name: str | None = None, **more) -> int:
        tree = trees.get(name) if name else None
        if name and step not in ("eject", "stop"):
            _train_waits(state, trees, name)
        out.update(next=step, change=name, worktree=str(tree) if tree else None, **more)
        out["changes"] = {
            n: {k: c.get(k) for k in ("pre", "on", "stacked", "landed", "ejected", "failed")}
            for n, c in state["changes"].items()
        }
        write_train(main, None if step == "done" else state)
        return factory.emit(out)

    def stopping(why: str) -> int:
        state["stop_reason"] = why
        out["problems"].append(why)
        return done("stop", reason=why)

    def ejecting(name: str, why: str, cause: str) -> int:
        """The change at fault, and why (R16): `gate`, the first red prefix's last change;
        `review`, a landing round that stops; `refusal`, a landing command's own."""
        state["changes"][name].update(fault=why, fault_cause=cause)
        return done("eject", name, reason=why, cause=cause)

    live = train_live(state)
    if not live:
        return done("done")
    if state["moves"] > cfg["land"]["moves"]:
        return stopping(
            f"{base} moved {state['moves']} times while the train landed, past [land] moves = "
            f"{cfg['land']['moves']}: run /sdlc-factory:land again"
        )
    # 1. Every change committed, in order, each in its worktree.
    for name in live:
        mine, tree = state["changes"][name], trees.get(name)
        if tree is None:
            return stopping(f"{name}'s worktree is gone: close or drop it by hand")
        mine["worktree"] = str(tree)
        folder = tree / factory.work_rel(tree) / name
        if mine.get("failed"):
            return ejecting(name, mine["failed"], "refusal")
        head = _landing_commit(tree, name)
        if head is None:
            ready_ = _land_readiness(tree, folder, state["by"])
            if ready_["refusal"]:
                return ejecting(name, ready_["refusal"], "refusal")
            return done("commit", name, before=ready_["before"])
        if mine.get("pre") is None:
            mine["pre"] = head
            mine["on"] = factory._git(tree, "merge-base", f"refs/heads/{base}", head)
    # 2. Each stacked on the one before it; a fix the person asked for made once its change sits
    # there (its conflict resolved), before any gate, so the gate and the review read it (154).
    fix = state.get("fix")
    for name in live:
        mine, tree = state["changes"][name], trees[name]
        if factory._rebasing(tree):
            return done("resolve", name, files=factory._conflicted(tree), round=factory.land_round(
                tree / factory.work_rel(tree) / name))  # fmt: skip
        onto = train_onto(state, name)
        head = factory._git(tree, "rev-parse", f"refs/heads/{name}") or ""
        if not _stacked(state, name):
            if mine.get("on") == onto and not mine.get("stacked"):
                _fresh_round(tree / factory.work_rel(tree) / name, mine)
                mine["stacked"] = head  # already there: it never moved
            else:
                return done("stack", name, onto=onto)
        elif head != mine["stacked"] and _tree_changed(tree, mine["stacked"], head):
            mine["stacked"] = head  # a fix amended in: what is above re-stacks on it
        if fix and fix["change"] == name and not fix.get("done"):
            return done("fix", name, ask=fix["ask"], asked=fix.get("round") is not None)
    # 3. The gate, once at the tip; a red tip bisected. Then the build, once at the tip, when a
    # change calls for it (185 R13).
    gate = _train_gate(main, cfg, state, trees) or _train_build(main, state, trees)
    write_train(main, state)  # the gates read, for `_land_gate_state()` under `land_verdict()`
    if gate is not None:
        if gate["next"] == "stop":
            return stopping(gate["reason"])
        if gate["next"] == "eject":
            return ejecting(gate["change"], gate["reason"], "gate")
        return done(gate["next"], gate.get("change"), **{
            k: v for k, v in gate.items() if k not in ("next", "change")
        })  # fmt: skip
    # 4. Each moved change's landing round, as `land-verdicts` reads it.
    for name in train_live(state):
        tree = trees[name]
        folder = tree / factory.work_rel(tree) / name
        n = factory.land_round(folder)
        if not n:
            continue
        verdict = land_verdict(tree, folder, cfg, n)
        if verdict["next"] == "pass":
            continue
        if verdict["next"] == "stop":
            return ejecting(name, "; ".join(verdict["problems"]), "review")
        if verdict["next"] == "accept":
            # Run again as stacked: by the loop itself only while cleared (185 R2–R8).
            cleared = checks_clearance(tree, folder, state["changes"][name])
            shown = {"clear": cleared["clear"], "why": cleared["why"]}
            return done(cleared["step"], name, verdict=verdict, checks=shown)
        return done(verdict["next"], name, verdict=verdict)
    # 5. Closed in order.
    return done("close", train_live(state)[0])


def _train_waits(state: dict, trees: dict[str, Path], name: str) -> None:
    """As the train turns to change `name`, each committed live change after it records the step
    `wait` (`_record_land()`), naming the live change before it: `stack on` it while it isn't
    stacked, `close after` it once it is. A change mid-rebase, or whose record is a stop, is left
    as it is. For the board alone: the train never reads the record."""
    live = train_live(state)
    if name not in live:
        return
    for i in range(live.index(name) + 1, len(live)):
        other, tree = live[i], trees.get(live[i])
        if tree is None or not state["changes"][other].get("pre") or factory._rebasing(tree):
            continue
        folder = tree / factory.work_rel(tree) / other
        try:
            old = factory.read_land_step((folder / factory.LAND_STEP).read_text(encoding="utf-8"))
        except OSError:
            old = None
        if old and old["step"] in ("stop", "eject"):
            continue
        verb = "close after" if _stacked(state, other) else "stack on"
        factory._record_land(tree, folder, "wait", waits=f"{verb} {live[i - 1]}")


def _train_gate(main: Path, cfg: dict, state: dict, trees: dict[str, Path]) -> dict | None:
    """The gate's step, or None when the tip is green or no gate is due: `gate` at the tip (no
    attempt on the stack as it stands), `gate` at a bisected prefix, `eject` of the change at
    fault (the last of the first red prefix), or `stop` when the first change is ejected twice
    in a row, the base's own check being the likelier fault. The green prefix `g` and red prefix
    `r` come from the recorded gates still valid for the stack: each prefix's gated commit is its
    change's stacked commit."""
    base = state["base"]
    if factory._base_check(main, base) is None:
        return None
    live = train_live(state)
    m = len(live)
    tip = state["changes"][live[-1]]
    if m == 1 and tip.get("stacked") == tip.get("pre"):
        return None  # a train of one that never moved: gated as its build was
    _read_gates(main, state, trees)
    verdicts: dict[int, dict] = {}
    for i, name in enumerate(live):
        stacked = state["changes"][name].get("stacked")
        for g in state["gates"]:
            if g["change"] == name and g["commit"] == stacked:
                verdicts[i + 1] = g  # newest last
    green = max([0, *(p for p, g in verdicts.items() if g["verdict"] == "PASS")])
    reds = [p for p, g in verdicts.items() if g["verdict"] != "PASS" and p > green]
    red = min(reds) if reds else None
    if red is None:
        if green == m:
            return None
        return {"next": "gate", "change": live[m - 1], "prefix": m, "of": m}
    if red == green + 1:
        fault = live[red - 1]
        g = verdicts[red]
        reason = (f"the gate failed on the stack up to {fault} (exit {g['exit']}), in "
                  f"{g['file']}")  # fmt: skip
        last = state["ejections"][-1:]
        if red == 1 and last and last[0].get("first") and last[0]["change"] != fault:
            return {
                "next": "stop",
                "reason": (
                    f"the first change is at fault twice in a row ({last[0]['change']}, then "
                    f"{fault}): {base}'s own check is the likelier fault; {reason}"
                ),
            }
        return {"next": "eject", "change": fault, "reason": reason, "prefix": red}
    p = (green + red) // 2
    return {"next": "gate", "change": live[p - 1], "prefix": p, "of": m, "green": green, "red": red}


def build_due(tree: Path, base: str) -> bool:
    """Whether the change in `tree` calls for the base branch's `[commands] build` (185 R12), as
    `/sdlc:ship` would run it on the same change built by hand: the base branch sets it, and its
    `build_when` is unset, matches a path the change touches (`_changed_paths()`, by `re.search`),
    or isn't a valid regex, which errs towards running; or a path it touches is on the base
    branch's `[review] sensitive`. All of it read from the base branch, never the checkout."""
    if factory._base_command(tree, base, "build") is None:
        return False
    when = factory._base_command(tree, base, "build_when")
    if when is None:
        return True
    paths = factory._changed_paths(tree, base)
    try:
        pattern = re.compile(when)
    except re.error:
        return True
    return any(pattern.search(p) for p in paths) or bool(
        factory.risk_paths(paths, factory._sensitive(tree, base))
    )


def _train_build(main: Path, state: dict, trees: dict[str, Path]) -> dict | None:
    """The build's step, after the tip's gate is green or none is due (185 R13, R14): None when
    the base branch names no `[commands] build`, no live change calls for it (`build_due()`), or a
    PASS sits on a commit that has the tip's stacked commit as an ancestor, which covers every
    change stacked under it, as a gate's PASS does; `build` at the tip when no attempt sits on its
    stacked commit; `stop` when the last one there is red. Never bisected: a slow build that
    needs what no change caused is the person's to read."""
    base = state["base"]
    live = train_live(state)
    if factory._base_command(main, base, "build") is None:
        return None
    if not any(build_due(trees[name], base) for name in live):
        return None
    _read_builds(main, state, trees)
    tip = live[-1]
    stacked = state["changes"][tip].get("stacked")
    builds = state["builds"]
    if any(b["verdict"] == "PASS" and _is_ancestor(main, stacked, b["commit"]) for b in builds):
        return None
    mine = [b for b in builds if b["commit"] == stacked]
    if not mine:
        return {"next": "build", "change": tip}
    last = mine[-1]
    return {"next": "stop", "reason": (
        f"the build failed on the train's tip, {tip} (exit {last['exit']}), in {last['file']}: "
        "it isn't bisected; read it, then rerun /sdlc-factory:land"
    )}  # fmt: skip


def _read_builds(main: Path, state: dict, trees: dict[str, Path]) -> None:
    """Every attempt in the live changes' current build files that ran on a stacked commit of the
    train, recorded once each in the state (`builds`), oldest first, as `_read_gates()` does."""
    builds = state.setdefault("builds", [])
    seen = {(b["change"], b["commit"], b["attempt"]) for b in builds}
    for name in train_live(state):
        tree = trees[name]
        folder = tree / factory.work_rel(tree) / name
        path = factory.land_build_path(folder, factory.land_round(folder) or 1)
        stacked = state["changes"][name].get("stacked") or ""
        for i, attempt in enumerate((factory.read_gate_file(path) or {"attempts": []})["attempts"],
                                    1):  # fmt: skip
            if not attempt["build"] or not stacked.startswith(attempt["build"]):
                continue
            if (name, stacked, i) in seen:
                continue
            seen.add((name, stacked, i))
            builds.append({
                "change": name, "commit": stacked, "attempt": i, "verdict": attempt["verdict"],
                "exit": attempt["exit"], "file": f"{name}/{path.relative_to(folder).as_posix()}",
            })  # fmt: skip


def _read_gates(main: Path, state: dict, trees: dict[str, Path]) -> None:
    """Every attempt in the live changes' current gate files that gated a stacked commit of the
    train, recorded once each in the state (`gates`), oldest first."""
    seen = {(g["change"], g["commit"], g["attempt"]) for g in state["gates"]}
    for name in train_live(state):
        tree = trees[name]
        folder = tree / factory.work_rel(tree) / name
        path = factory.land_gate_path(folder, factory.land_round(folder) or 1)
        record = factory.read_gate_file(path)
        if record is None:
            continue
        stacked = state["changes"][name].get("stacked") or ""
        for i, attempt in enumerate(record["attempts"], 1):
            if not attempt["build"] or not stacked.startswith(attempt["build"]):
                continue
            if (name, stacked, i) in seen:
                continue
            seen.add((name, stacked, i))
            state["gates"].append({
                "change": name, "commit": stacked, "attempt": i, "verdict": attempt["verdict"],
                "exit": attempt["exit"], "prefix": train_live(state).index(name) + 1,
                "file": f"{name}/{path.relative_to(folder).as_posix()}",
            })  # fmt: skip


def _record_ejection(folder: Path, cause: str, train: str | None) -> str | None:
    """One row appended to the change's `runs/ejections.jsonl` (`factory.EJECTIONS`) as a train
    puts it back: when, its landing round, why (`gate`, `review`, `refusal` or `stop`), and which
    train, by its `began` (180 R4), the new key last. The retrospective reads it to count the
    landing's runs before it as `ejected` (174 R4), and its ejections and stops as overrides
    (180 R6); the caller amends it into the change's commit with the rest of the landing's record.
    Recording never blocks the ejection: a row that can't be written comes back as a problem for
    the caller's output (180 R5), and None once it is written."""
    path = folder / factory.EJECTIONS
    row = {"at": factory._utc_now(), "land": factory.land_round(folder), "cause": cause,
           "train": train}  # fmt: skip
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row) + "\n")
    except OSError as e:
        return f"couldn't record the {cause} in {factory.EJECTIONS.as_posix()}: {e.strerror or e}"
    return None


def _train_eject(main: Path, state: dict, ident: str) -> int:
    name = next((n for n in state["order"] if factory.names_change(n, ident)), None)
    if name is None or name not in train_live(state):
        return factory.emit({"refusals": [f"{ident} isn't a live change of the train"]}, 1)
    mine = state["changes"][name]
    reason = mine.get("fault") or mine.get("failed")
    if not reason:
        return factory.emit(
            {"refusals": [f"the train names no fault in {name}: run train first"]}, 1
        )
    # A fault from a state written before the cause was kept reads as a refusal, which pauses.
    cause = (mine.get("fault_cause") if mine.get("fault") else None) or "refusal"
    tree = Path(mine["worktree"])
    folder = tree / factory.work_rel(tree) / name
    out = {"change": name, "state": "ejected", "reason": reason, "cause": cause, "undo": None,
           "problems": []}  # fmt: skip
    undo, why = _put_back(tree, folder, mine)
    if why:
        return factory.emit(
            {**out, "state": "refused", "refusals": [f"couldn't put {name} back: {why}"]}, 1
        )
    if mine.get("pre"):
        factory._record_land(tree, folder, "eject", [f"ejected from the train: {reason}"])
        if problem := _record_ejection(folder, cause, state.get("began")):
            out["problems"].append(problem)
        _write_train_record(tree, folder, state, name)
        _amend_record(tree, folder)
    first = train_live(state)[0] == name
    mine.update(ejected=reason, stacked=None, stacking=None, fault=None, fault_cause=None,
                failed=None)  # fmt: skip
    state["ejections"].append({"change": name, "reason": reason, "cause": cause, "first": first})
    write_train(main, state)
    out.update(undo=undo, head=(factory._git(tree, "rev-parse", "HEAD") or "")[:12])
    return factory.emit(out)


def _train_stop(main: Path, state: dict) -> int:
    reason = state.get("stop_reason") or "the train was stopped"
    put_back, problems = [], []
    for name in train_live(state):
        mine = state["changes"][name]
        tree = Path(mine["worktree"] or "")
        if not tree.is_dir():
            problems.append(f"{name}'s worktree is gone")
            continue
        folder = tree / factory.work_rel(tree) / name
        undo, why = _put_back(tree, folder, mine)
        if why:
            problems.append(f"couldn't put {name} back: {why}")
            continue
        if mine.get("pre"):
            factory._record_land(tree, folder, "stop", [f"the train stopped: {reason}"])
            if problem := _record_ejection(folder, "stop", state.get("began")):
                problems.append(f"{name}: {problem}")
            _amend_record(tree, folder)
        put_back.append({"change": name, "undo": undo,
                         "head": (factory._git(tree, "rev-parse", "HEAD") or "")[:12]})  # fmt: skip
    write_train(main, None)
    return factory.emit(
        {"state": "stopped", "reason": reason, "put_back": put_back, "problems": problems}
    )


# ---------------------------------------------------------------- the loop: train --run
#
# `train --run` takes the steps `train` names, each through the command the land skill ran, until
# `done` or the first stop that is the person's (147). The loop is this script, never an agent:
# it commits nothing itself, and each step is a subprocess of this script, so the step is the
# command the tests pin, several agents run at once without sharing stdout, and the next reading
# alone decides. It holds `TRAIN_RUN_LOCK` for its whole life, on an open descriptor, so the OS
# frees it however the loop ends; its children are told by `TRAIN_RUN_ENV`, as `sdlc.py`'s
# `LOCK_HELD_ENV` tells a handed-off close. `--cancel` writes `TRAIN_CANCEL`, read between steps.


TRAIN_RUN_LOCK = "sdlc-factory-train-run.lock"


TRAIN_CANCEL = "sdlc-factory-train.cancel"


TRAIN_RUN_ENV = "SDLC_FACTORY_TRAIN_RUN"


RUN_UNDER_WAY = "a train --run is under way: wait for it to end, or train --cancel"


# Every `next` a train's reading can name.
TRAIN_STEPS = (
    "commit", "stack", "resolve", "gate", "build", "eject", "accept", "checks", "review",
    "arbitrate", "mend", "fix", "close", "stop", "done",
)  # fmt: skip


# The commands the loop runs for each step, and no others (R3): `{role}` is each role the round
# names, started together (R10); `fix`'s `--ask` is skipped once `asked`.
RUN_STEPS = {
    "commit": (("land", "{change}", "--by", "{by}"),),
    "stack": (("resolve", "{change}", "--onto", "{onto}"),),
    "resolve": (
        ("agent", "{change}", "--task", "train-resolve"), ("resolve", "{change}", "--continue"),
    ),
    "gate": (("gate", "{change}", "--land"),),
    "build": (("gate", "{change}", "--land", "--build"),),
    "eject": (("train", "--eject", "{change}"),),
    "accept": (("accept", "{change}"),),
    "checks": (("agent", "{change}", "--task", "land-checks"),),
    "review": (("agent", "{change}", "--task", "land-review", "--role", "{role}"),),
    "arbitrate": (("agent", "{change}", "--task", "land-arbitrate"),),
    "mend": (("agent", "{change}", "--task", "land-mend", "--role", "{role}"),),
    "fix": (
        ("land-fix", "{change}", "--ask", "{ask}"), ("agent", "{change}", "--task", "land-fix"),
        ("land-fix", "{change}", "--commit"),
    ),
    "close": (("land", "{change}", "--close"),),
}  # fmt: skip


# The one ejection the loop makes itself: a gate's fault, which the person's yes approved leaving
# out ("the change at fault left out with why and the rest landed"). Every other cause pauses.
RUN_EJECTS = ("gate",)


# The steps that are the person's: a train that stops, and `accept` when the reading doesn't clear
# its checks (`checks_clearance()`): a `checks.md` changed since the yes that the read-only list and
# the approver haven't both cleared. A cleared `accept` the loop runs itself, from `RUN_STEPS`.
RUN_STOPS = ("accept", "stop")


RERUN = "rerun /sdlc-factory:land"


PUT_BACK = "train --stop to put every change not landed back"


@contextmanager
def run_lock(root: Path) -> Iterator[bool]:
    """Try the run lock for the `with` block without waiting: True when this process holds it,
    False when another does. Outside a git repo there is none to take: True."""
    where = factory._slot_dir(root)
    if where is None:
        yield True
        return
    fd = os.open(where / TRAIN_RUN_LOCK, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        held = factory._try_lock(fd)
        try:
            yield held
        finally:
            if held:
                factory._unlock(fd)
    finally:
        os.close(fd)


def train_running(root: Path) -> bool:
    """Whether a `train --run` holds the run lock now."""
    with run_lock(root) as held:
        return not held


def _train_cancel(main: Path) -> int:
    """Ask the running loop to stop after the step in flight (R7): it reads the file between
    steps, removes it and exits `cancel`, the train still under way."""
    where = factory._slot_dir(main)
    if where is None or not train_running(main):
        return factory.emit({"refusals": ["no train --run is under way: nothing to cancel"]}, 1)
    (where / TRAIN_CANCEL).write_text("cancel\n", encoding="utf-8", newline="\n")
    return factory.emit({"state": "cancelling", "after": "the step in flight"})


def _train_run(main: Path) -> int:
    if factory.read_train(main) is None:
        return factory.emit({"refusals": ["no train is under way: run train --begin first"]}, 1)
    with run_lock(main) as held:
        if not held:
            return factory.emit({"refusals": [RUN_UNDER_WAY]}, 1)
        return _run_loop(main)


def _run_env(main: Path) -> dict[str, str]:
    where = factory._slot_dir(main)
    return {**os.environ, TRAIN_RUN_ENV: str(where / TRAIN_RUN_LOCK) if where else "held"}


def _run_one(main: Path, argv: list[str], cwd: Path) -> tuple[int, dict | None, str]:
    """One command of this script, as a subprocess: its exit, its JSON, its stderr."""
    done = subprocess.run(
        [sys.executable, str(factory.FACTORY_SCRIPT), *argv], cwd=cwd, env=_run_env(main),
        capture_output=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
    )  # fmt: skip
    try:
        data = json.loads(done.stdout)
    except ValueError:
        data = None
    return done.returncode, data if isinstance(data, dict) else None, done.stderr or done.stdout


def _run_group(main: Path, group: list[tuple[list[str], Path]]) -> list[dict]:
    """Commands of this script started together and waited for, each a subprocess writing to a
    file of its own (R10): each one's `argv`, exit (`code`), JSON (`out`) and stderr (`said`)."""
    results = []
    with ExitStack() as files:
        started = []
        for argv, cwd in group:
            out_f = files.enter_context(tempfile.TemporaryFile())
            err_f = files.enter_context(tempfile.TemporaryFile())
            proc = subprocess.Popen(
                [sys.executable, str(factory.FACTORY_SCRIPT), *argv], cwd=cwd,
                env=_run_env(main), stdin=subprocess.DEVNULL, stdout=out_f, stderr=err_f,
            )  # fmt: skip
            started.append((argv, proc, out_f, err_f))
        for argv, proc, out_f, err_f in started:
            code = proc.wait()
            texts = []
            for f in (out_f, err_f):
                f.seek(0)
                texts.append(f.read().decode("utf-8", "replace"))
            try:
                data = json.loads(texts[0])
            except ValueError:
                data = None
            results.append({"argv": argv, "code": code, "said": texts[1],
                            "out": data if isinstance(data, dict) else None})  # fmt: skip
    return results


def _run_plan(main: Path, reading: dict) -> tuple[list | None, dict | None]:
    """The groups of commands the reading's step takes, each group started together; or, for a
    step that is the person's (R4), the stop: `next`, `change`, `cause`, `reason`, `way_on`."""
    nxt, name = reading.get("next"), reading.get("change")
    num = name.split("-")[0] if name else ""

    def stop(reason: str, way_on: str) -> tuple[None, dict]:
        return None, {"next": nxt, "change": name, "cause": reading.get("cause"),
                      "reason": reason, "way_on": way_on, "record": True}  # fmt: skip

    if nxt == "stop":
        return stop(reading.get("reason") or "the train stopped", f"{PUT_BACK}, then {RERUN}")
    if nxt == "accept":
        # Read again from `checks.md` as it is now, just before the run (R9): a file edited since
        # the reading is never run on the reading's word.
        said, now = reading.get("checks") or {}, _clearance_now(main, reading)
        if not (said.get("clear") and now["clear"]):
            why = now["why"] if said.get("clear") else said.get("why") or now["why"]
            return stop(
                f"{why}: {name}'s acceptance checks run again on it as stacked, behind your prompt",
                f"factory.py accept {num}, then {RERUN}",
            )
    if nxt == "commit" and reading.get("before"):
        firsts = reading["before"]
        return stop(
            f"{name} needs {' and '.join(firsts)} run before its commit, behind your prompt",
            ", ".join(f"factory.py {b} {num}" for b in firsts) + f", then {RERUN}",
        )
    if nxt == "resolve" and not reading.get("files"):
        return stop(
            f"a rebase is under way in {name}'s worktree with no conflicted file",
            f"run git status in its worktree, then {RERUN}",
        )
    if nxt == "eject" and reading.get("cause") not in RUN_EJECTS:
        return stop(
            reading.get("reason") or f"the train names a fault in {name}",
            f"{RERUN} to leave {num} out and go on, or {PUT_BACK}",
        )
    if nxt not in RUN_STEPS or not name or not reading.get("worktree"):
        return stop(f"the loop can't take the step {nxt!r}", f"run train, then {RERUN} by hand")
    templates = list(RUN_STEPS[nxt])
    if nxt == "fix" and reading.get("asked"):
        templates = templates[1:]
    verdict = reading.get("verdict") or {}
    roles = verdict.get("missing") if nxt == "review" else verdict.get("mend")
    fill = {"change": name, "by": reading.get("by"), "onto": reading.get("onto"),
            "ask": reading.get("ask")}  # fmt: skip
    groups = []
    for template in templates:
        cwd = main if template[0] == "train" or "--close" in template else Path(reading["worktree"])
        each = roles or [] if "{role}" in template else [None]
        groups.append([
            ([part.format(**fill, role=role) for part in template], cwd) for role in each
        ])  # fmt: skip
    return groups, None


def _clearance_now(main: Path, reading: dict) -> dict:
    """`checks_clearance()` for the change a reading names, from the train's state and its
    `checks.md` as they are now; not clear when no live train names it."""
    state, name = factory.read_train(main), reading.get("change")
    if state is None or name not in train_live(state) or not reading.get("worktree"):
        return {"clear": False, "why": f"no train under way names {name}"}
    tree = Path(reading["worktree"])
    return checks_clearance(tree, tree / factory.work_rel(tree) / name, state["changes"][name])


def _run_end(main: Path, reading: dict, undos: list[dict], stopped: dict | None = None) -> int:
    """The loop's exit JSON: the train as it now stands (`landed`, `live`, `moves`, `gates`,
    `ejected` with each one's `reason` and `cause`), the undo of each ejection it made, and `done`
    or `stopped`. A stop that names a change is recorded in its `runs/land-step.md` (R2), with
    its reason and the way on, unless the command that failed recorded its own."""
    state = factory.read_train(main)
    if state is not None:
        summary = {
            "landed": [n for n in state["order"] if state["changes"][n].get("landed")],
            "live": train_live(state), "moves": state["moves"], "gates": len(state["gates"]),
            "ejected": [{"change": e["change"], "reason": e["reason"],
                         "cause": e.get("cause") or "refusal"} for e in state["ejections"]],
        }  # fmt: skip
    else:
        summary = {k: reading.get(k) for k in ("landed", "live", "moves", "gates", "ejected")}
    out = {**summary, "undos": undos}
    if stopped is None:
        return factory.emit({**out, "done": True})
    record = stopped.pop("record", False)
    tree = Path(reading["worktree"]) if reading.get("worktree") else None
    if record and stopped.get("change") and tree is not None:
        folder = tree / factory.work_rel(tree) / stopped["change"]
        if folder.is_dir():
            factory._record_land(tree, folder, "stop", [stopped["reason"], stopped["way_on"]])
    print(f"train: stopped at {stopped['next']}: {stopped['reason']}", file=sys.stderr, flush=True)
    return factory.emit({**out, "stopped": stopped}, 1)


# A SIGKILL of the loop alone, not its process group, leaves the step it started running (nit
# 2026-11-18-69): an agent, a gate or a close lives on as an orphan. The run lock is held on the
# loop's own descriptor, which no child inherits, so it goes with the loop, and a second `--run`
# can start while the orphan still writes. The one guard is the loop's own: the same step named
# twice with nothing changed stops it. The way out is to kill the group, as the kill tests do.
def _run_loop(main: Path) -> int:
    """Read the train, take the step it names, read again: until `done`, or the first stop
    (R4), a cancel between steps (R7), or the same step named twice with nothing changed."""
    where = factory._slot_dir(main)
    cancel = where / TRAIN_CANCEL if where else None
    if cancel is not None:
        cancel.unlink(missing_ok=True)  # one no loop read: the loop it was for is gone
    undos: list[dict] = []
    reading: dict = {}
    last = None
    while True:
        if cancel is not None and cancel.is_file():
            cancel.unlink(missing_ok=True)
            return _run_end(main, reading, undos, {
                "next": "cancel", "change": None, "cause": None,
                "reason": "cancelled by train --cancel, after the step in flight",
                "way_on": f"{RERUN} to go on, or {PUT_BACK}",
            })  # fmt: skip
        code, found, said = _run_one(main, ["train"], main)
        if found is None or code or found.get("refusals"):
            why = "; ".join((found or {}).get("refusals") or []) or said.strip()[-300:]
            return _run_end(main, reading, undos, {
                "next": "train", "change": None, "cause": None,
                "reason": why or f"train exited {code}", "way_on": f"run train, then {RERUN}",
            })  # fmt: skip
        reading = found
        nxt, name = reading.get("next"), reading.get("change")
        if nxt == "done":
            return _run_end(main, reading, undos)
        path = train_path(main)
        key = (nxt, name, path.read_bytes() if path and path.is_file() else None)
        if key == last:
            return _run_end(main, reading, undos, {
                "next": nxt, "change": name, "cause": reading.get("cause"), "record": True,
                "reason": f"train named {nxt} for {name} twice in a row with nothing changed: "
                          "the step didn't take",
                "way_on": f"run train to see where it stands, then {RERUN} by hand",
            })  # fmt: skip
        last = key
        print(f"train: {nxt} {name or ''}".rstrip(), file=sys.stderr, flush=True)
        groups, stopped = _run_plan(main, reading)
        if stopped is not None:
            return _run_end(main, reading, undos, stopped)
        for group in groups:
            for result in _run_group(main, group):
                out = result["out"] or {}
                if result["argv"][-1] == "--close" and out.get("push_failed"):
                    return _run_end(main, reading, undos, {
                        "next": nxt, "change": name, "cause": None,
                        "reason": f"{name} landed, but its push was refused",
                        "way_on": out["push_failed"],
                    })  # fmt: skip
                # A red gate or a failed check is the next reading's to read (R3); a refusal
                # still stops the loop.
                failed = result["code"] and result["argv"][0] not in ("gate", "accept")
                if failed or out.get("problem") or out.get("refusals"):
                    why = out.get("problem") or "; ".join(out.get("refusals") or [])
                    why = why or result["said"].strip()[-300:] or f"exit {result['code']}"
                    return _run_end(main, reading, undos, {
                        "next": nxt, "change": name, "cause": None, "reason": why,
                        "way_on": f"fix what it says in {name}'s worktree, then {RERUN}; or "
                                  f"{PUT_BACK}",
                    })  # fmt: skip
                if result["argv"][:2] == ["train", "--eject"]:
                    undo = {"change": name, "undo": out.get("undo")}
                    if out.get("problems"):  # a row the ejection couldn't record (180 R5)
                        undo["problems"] = out["problems"]
                    undos.append(undo)
                    print(f"train: ejected {name} ({reading.get('cause')}): undo with "
                          f"{out.get('undo')}", file=sys.stderr, flush=True)  # fmt: skip


def _settle_counter(root: Path) -> None:
    """`.sdlc/last-id` conflicted, as it is whenever two locally numbered changes land one after
    the other: never the builder's, it keeps the higher of the two numbers, as `sdlc.py base` does
    on a fast-forward, so no number is handed out twice."""
    if factory.COUNTER not in factory._conflicted(root):
        return
    sides = [factory._git(root, "show", f":{n}:{factory.COUNTER}") or "" for n in (2, 3)]
    numbers = [int(s) for s in sides if s.strip().isdigit()]
    if not numbers:
        return
    (root / factory.COUNTER).write_text(f"{max(numbers):03d}\n", encoding="utf-8", newline="\n")
    factory._git(root, "add", "--", factory.COUNTER)


def _rebase_settling(
    root: Path, onto: str, upstream: str, env: dict
) -> tuple[subprocess.CompletedProcess, list[str]]:
    """`git rebase --onto <onto> <upstream>`, the one rebase `resolve` runs: when only
    `.sdlc/last-id` conflicts, it settles itself (`_settle_counter()`) and the rebase goes on, a
    commit at a time, up to `RESOLVE_STEPS`. Returns git's last result and the files left
    conflicted for the builder."""
    done = subprocess.run(["git", "-C", str(root), "rebase", "-q", "--onto", onto, upstream],
                          capture_output=True, encoding="utf-8", env=env)  # fmt: skip
    _settle_counter(root)
    files = factory._conflicted(root)
    for _ in range(factory.RESOLVE_STEPS):
        if not (done.returncode and not files and factory._rebasing(root)):
            break
        done = subprocess.run(["git", "-C", str(root), "rebase", "--continue"],
                              capture_output=True, encoding="utf-8", env=env)  # fmt: skip
        _settle_counter(root)
        files = factory._conflicted(root)
    return done, files


def cmd_resolve(root: Path, ident: str, cont: bool, onto: str | None = None) -> int:
    """A rebase that conflicts, left for an agent: exactly one of `--onto` and `--continue`.
    `--onto <commit>` in a train is the train's stack: the change's own commits (from `on`, where
    the train found them) rebased onto `onto`, the commit of the change before it or the base's
    tip, its dirty records amended in first, a landing round opened when it moves: `current`
    (already there), `stacked`, or `conflict`, for `agent --task train-resolve`. Outside a train
    `--onto` takes only the base branch, by name or by its tip: the change's own commits, from
    their merge base with it, rebased onto it, with no train state and no landing round: `current`,
    `stacked` or `conflict`. Either way `.sdlc/last-id` settles itself (`_rebase_settling()`).
    `--continue` refuses when no rebase is under way, since `REBASE_HEAD` outlives one. It checks
    no conflict marker is left in the conflicted files, that a file the resolution deleted (staged
    or not) is one side of a modify/delete (`factory.deleted_sides()`, which reads one whose
    deletion is already staged from the commits), that nothing in the worktree changed outside
    them, the files a modify/delete's deleting commit added or changed (`carried` when their text
    is neither side's, staged or not) and the change's landing records (`_stray()`), and that
    every staged path is one of those or `REBASE_HEAD`'s own (`_replayed()`, `_staged()`, each
    read once, before anything is staged), then writes `runs/land-resolved`, stages the files, the
    marker, the agent's reply and the other records (`RESOLVE_RECORDS`), and continues, so the
    rebased commit holds them and the worktree is clean; on a second conflict it aborts, which
    takes the staged marker with it.
    Every git step is this script's: the resolver, or the builder, only edits the files it is
    given. A conflicted register loses, before it is staged, every entry the landing deleted from
    it, whatever the agent kept: the change's `idea:` and `fixes:` entries and the nits it retired,
    each by id (`dropped`). The marker reads `land-<n>`, the round under way, then the files. It is
    a resolved conflict no reviewer has seen until round `n`'s review passes
    (`resolution_signals()`)."""
    if cont == (onto is not None):
        return factory.emit(
            {"refusals": ["resolve takes exactly one of --onto <commit> and --continue"]}, 1
        )
    folder, refusal = factory.find_change(root, ident)
    if refusal:
        return factory.emit({"refusals": [refusal]}, 1)
    base = factory._base(root)
    if base is None:
        why = "no base branch: set [git] base in .sdlc/config.toml"
        return _land_refused(root, folder, {}, why)
    env = {**os.environ, "GIT_EDITOR": "true"}
    named = train_names(root, folder)
    if onto is not None and named is None:
        tip = factory._git(root, "rev-parse", f"refs/heads/{base}") or ""
        if not tip or (
            onto != base and factory._git(root, "rev-parse", "--verify", "-q", onto) != tip
        ):
            why = (f"outside a train, resolve --onto takes only the base branch ({base}), by name "
                   "or by its tip")  # fmt: skip
            return factory.emit({"refusals": [why]}, 1)
        if factory._rebasing(root):
            return factory.emit({"refusals": ["a rebase is under way: resolve --continue"]}, 1)
        head = factory._git(root, "rev-parse", "HEAD") or ""
        upstream = factory._git(root, "merge-base", "HEAD", tip) or ""
        if upstream == tip:
            return factory.emit({"change": folder.name, "state": "current", "head": head[:12]})
        done, files = _rebase_settling(root, tip, upstream, env)
        if done.returncode and not files:
            why = f"git rebase failed: {done.stderr.strip()[-300:]}"
            plain = f"the rebase onto {base} failed: run git status in its worktree to see why"
            return _land_refused(root, folder, {}, why, plain)
        if files:
            return factory.emit({"change": folder.name, "state": "conflict", "conflicted": files,
                         "onto": base})  # fmt: skip
        return factory.emit({"change": folder.name, "state": "stacked", "onto": base,
                     "head": (factory._git(root, "rev-parse", "HEAD") or "")[:12]})  # fmt: skip
    if onto is not None:
        state, mine = named
        if not mine.get("on"):
            return factory.emit(
                {"refusals": [f"{folder.name} isn't committed yet: run land first"]}, 1
            )
        if factory._rebasing(root):
            return factory.emit({"refusals": ["a rebase is under way: resolve --continue"]}, 1)
        num = folder.name.split("-")[0]
        if why := _amend_record(root, folder):
            return _land_refused(root, folder, {}, why, _amend_plain(why, num))
        head = factory._git(root, "rev-parse", "HEAD") or ""
        if mine["on"] == onto:
            _fresh_round(folder, mine)
            mine["stacked"], mine["stacking"] = head, None
            write_train(root, state)
            return factory.emit({"change": folder.name, "state": "current", "head": head[:12]})
        (folder / "reviews" / f"land-{factory.land_round(folder) + 1}").mkdir(
            parents=True, exist_ok=True
        )
        mine["stacking"] = onto
        write_train(root, state)
        done, files = _rebase_settling(root, onto, mine["on"], env)
        if done.returncode and not files:
            factory._git(root, "rebase", "--abort")
            mine["stacking"] = None
            write_train(root, state)
            why = f"git rebase --onto {onto[:12]} failed: {done.stderr.strip()[-300:]}"
            plain = (
                f"stacking it onto {onto[:12]} failed: run git status in its worktree to see why, "
                f"then rerun /sdlc-factory:land {num}"
            )
            return _land_refused(root, folder, {}, why, plain)
        if files:
            factory._record_land(root, folder, "stack")
            return factory.emit({"change": folder.name, "state": "conflict", "conflicted": files,
                         "onto": onto, "round": factory.land_round(folder)})  # fmt: skip
        _stacked_now(root, folder, state, mine)
        factory._record_land(root, folder, "stack")
        return factory.emit({"change": folder.name, "state": "stacked", "onto": onto,
                     "head": (factory._git(root, "rev-parse", "HEAD") or "")[:12],
                     "round": factory.land_round(folder)})  # fmt: skip
    num = folder.name.split("-")[0]
    # `REBASE_HEAD` outlives its rebase: with none under way, nothing is read or staged (198 R8).
    if not factory._rebasing(root):
        why = "no rebase under way: nothing to continue"
        plain = (
            f"resolve {num} --continue found no rebase under way: run git status in its worktree "
            f"to see where it stands"
        )
        return _land_refused(root, folder, {}, why, plain)
    files = factory._conflicted(root)
    # Where a deleted file's content went (`factory.deleted_sides()`): the resolver may carry the
    # other side's edit into those files, so they pass the fence and are staged with the conflict's.
    sides = factory.deleted_sides(root)
    moved = list(dict.fromkeys(p for d in sides for p in d["moved"]))
    # The replayed commit's own paths and the index as the resolution left it, each read once,
    # before this script stages anything (198 R8, R9).
    replayed, staged = _replayed(root), _staged(root)
    if replayed is None or staged is None:
        why = "git couldn't read the index or REBASE_HEAD in the change's worktree"
        return _land_refused(root, folder, {}, why)
    # Only one side of a modify/delete may go (nit 2026-11-20-20): a conflicted file that is gone,
    # or a deletion staged of a file the replayed commit keeps, is the resolution's, so it must be
    # one `deleted_sides()` names, never a file both sides changed. A staged deletion of a path the
    # replayed commit doesn't own is the fence's, below.
    deletable = {d["path"] for d in sides}
    staged_gone = [
        p for xy, p in _status_entries(root) or []
        if xy == "D " and replayed.get(p, "D") != "D"
    ]  # fmt: skip
    gone = [
        f for f in dict.fromkeys([*files, *staged_gone])
        if not (root / f).exists() and f not in deletable
    ]  # fmt: skip
    if gone:
        listed = ", ".join(gone)
        why = f"deleted {listed}, which no modify/delete conflict lets go"
        plain = (
            f"the resolution deleted {listed}, which both sides kept: restore it in its worktree "
            f"(git checkout --merge -- <path>), then factory.py resolve {num} --continue, or "
            f"eject {num} from the train"
        )
        return _land_refused(root, folder, {}, why, plain)
    # A conflicted file the resolution deleted is a staged deletion, with nothing to read.
    marked = [
        f for f in files
        if (root / f).is_file() and factory.CONFLICT_MARKER_RE.search(
            (root / f).read_text(encoding="utf-8", errors="replace"))
    ]  # fmt: skip
    if marked:
        plain = (
            f"the resolution left conflict markers in {', '.join(marked)}: remove them in its "
            f"worktree, then sdlc.py resolve {num} --continue finishes the rebase (or --abort "
            f"undoes it, for /sdlc:ship {num} by hand)"
        )
        why = f"conflict markers left in: {', '.join(marked)}"
        return _land_refused(root, folder, {}, why, plain)
    # Only the conflicted files, the moved files and the change's landing records may have changed
    # in the worktree, and a staged path must be one of those or `REBASE_HEAD`'s own (198 R1-R4):
    # the script, not the prompt, holds a resolution to the files it was given (149 R8, R9),
    # whoever resolved it, whether it staged its change or not.
    n = factory.land_round(folder)
    marker = folder / "runs" / "land-resolved"
    own = (*factory.RESOLVE_RECORDS, marker.relative_to(folder), Path("build") / f"land-{n}.md")
    records = [(folder / r).relative_to(root).as_posix() for r in own]
    stray = _stray(root, [*records, *moved])
    if stray is None:
        return _land_refused(root, folder, {}, "git status failed in the change's worktree")
    allowed = {*replayed, *files, *moved, *records}
    stray = list(dict.fromkeys([*stray, *(p for p in staged if p not in allowed)]))
    # A moved file the resolution changed, staged or not: its text is neither side's.
    carried = [p for p in moved if _neither_side(root, p)]
    if stray:
        listed = ", ".join(stray)
        why = f"edited outside its conflicted files: {listed}"
        plain = (
            f"the resolution changed {listed}, outside the conflicted files: undo those edits in "
            f"its worktree (git checkout HEAD -- <path>, or git rm --cached and delete a new "
            f"file), then factory.py resolve "
            f"{num} --continue, or eject {num} from the train"
        )
        return _land_refused(root, folder, {}, why, plain)
    # What the landing deleted from the register stays deleted, whatever the agent kept: the
    # change's own seeds and the bugs it fixes, by id, and the nits it retired (`named_nits()`).
    dropped: list[str] = []
    if factory.INBOX.as_posix() in files:
        text = (folder / "intent.md").read_text(encoding="utf-8")
        ids = [*factory.frontmatter_ids(text, "idea"), *factory.frontmatter_ids(text, "fixes")]
        dropped = drop_entries(root, [*ids, *factory.named_nits(root, folder)])
    for f in [*files, *carried]:
        factory._git(root, "add", "--", f)
    # The resolution's marker, written before the rebase goes on, so it goes into the rebased
    # commit with the resolver's reply and the worktree is left clean (R14); an abort below
    # takes the staged marker with it. It names the files a deleted one's content was carried
    # into too, for the review.
    marker.parent.mkdir(parents=True, exist_ok=True)
    resolved = list(dict.fromkeys([*files, *(d["path"] for d in sides)]))
    marker.write_text(
        f"land-{n}\n" + ", ".join([*resolved, *carried]) + "\n", encoding="utf-8", newline="\n"
    )
    # The agent's resolve run added its cost line to this tracked file mid-rebase: the change's
    # own record, so it goes into the rebased commit, or `--continue` refuses on it.
    # So did the agent's step, `resolve`, in the landing's step record.
    for record in own:
        if (folder / record).is_file():
            factory._git(root, "add", "--", (folder / record).relative_to(root).as_posix())
    done = subprocess.run(["git", "-C", str(root), "rebase", "--continue"], capture_output=True,
                          encoding="utf-8", env=env)  # fmt: skip
    if done.returncode:
        factory._git(root, "rebase", "--abort")
        if named is not None:
            named[1]["stacking"] = None
            write_train(root, named[0])
        why = "a second conflict: the rebase was aborted, ship it by hand"
        plain = (
            f"its rebase conflicted a second time and was undone: /sdlc:ship {num} by hand brings "
            f"it up to date with {base}"
        )
        return _land_refused(root, folder, {}, why, plain)
    if named is not None and named[1].get("stacking"):
        _stacked_now(root, folder, named[0], named[1])
    head = factory._git(root, "rev-parse", "--short", "HEAD")
    return factory.emit({"change": folder.name, "resolved": resolved, "carried": carried,
                 "state": "resolved", "dropped": dropped, "head": head})  # fmt: skip


def cmd_land_verdicts(root: Path, ident: str, record: bool = False) -> int:
    """The landing review of round `land-<n>`, and the step it takes next: `gate` (the script's
    gate on the change as rebased, before any reviewer, while the base branch names one),
    `accept` (a change with acceptance checks runs them again on its commit as rebased, through
    `factory.py accept`, after the gate; a train's reading adds whether they're cleared to run
    unattended, `checks_clearance()`),
    `review` for the `missing` reviewers (behaviour alone after a clean rebase, every reviewer at
    the run's depth after a resolved conflict or a fix the person asked for, `fixed`), `arbitrate`
    when one asks for changes, `pass` when none is kept, `mend` when every problem is one the
    agent that wrote it can answer again (a behaviour check's missing `## Evidence` or `exit:`,
    verdict lines that disagree, the arbiter's unread answers), with the roles in `mend`, each
    once a landing round (`land_mended()`), or `stop`, with why: a red gate or check, a kept
    change, a reply without a verdict, or a mendable problem beside one of those or after its one
    mend.
    It writes nothing but with `record`, which the land skill passes: then a `stop` is written to
    `runs/land-step.md` with its problems, for the board."""
    cfg, _ = factory.load_config(root)
    folder, refusal = factory.find_change(root, ident)
    if refusal:
        return factory.emit({"refusals": [refusal]}, 1)
    n = factory.land_round(folder)
    if not n:
        return factory.emit({"change": folder.name, "round": None, "next": "pass", "missing": []})
    out = land_verdict(root, folder, cfg, n)
    if record and out["next"] == "stop":
        factory._record_land(root, folder, "stop", out["problems"])
    return factory.emit(out)


def land_verdict(root: Path, folder: Path, cfg: dict, n: int, settled: bool = False) -> dict:
    """Landing round `n`'s verdicts and the step it takes next, as `land-verdicts` emits them for
    the round under way: the one reading of whether a landing review passed, which
    `resolution_signals()` asks too, `settled` (see `_land_gate_state()`)."""
    path = folder / "reviews" / f"land-{n}"
    resolved = (folder / "runs" / "land-resolved").is_file()
    fixed = factory.land_ask(folder, n) is not None
    rounds, _, run = factory._rounds_at_depth(root, folder, cfg)
    wanted = list(run["reviewers"]) if resolved or fixed else ["behaviour"]
    reviews, problems = {}, []
    # Kept apart as they're added, by the role that mends each, as `loop_state()` keeps them: a
    # missing `## Evidence`, verdict lines that disagree, the arbiter's unread answers.
    mendable: dict[str, list[str]] = {}
    for role in wanted:
        file = path / f"{role}.md"
        if not file.is_file():
            continue
        lines = file.read_text(encoding="utf-8").splitlines()
        found = factory.opening(lines, factory.VERDICT_RE)
        if not found:
            problem = factory._no_verdict(n, role, "land")
            problems.append(problem)
            if factory.preamble(file):
                mendable.setdefault(role, []).append(problem)
            continue
        at, m = found
        reviews[role] = {
            "verdict": m.group(1),
            "changes": [c.group(1) for c in map(factory.CHANGE_RE.match, lines[at + 1 :]) if c],
        }
        if role in factory.RUNS_THE_CHANGE:
            found = factory.read_evidence("\n".join(lines), f"reviews/land-{n}/{role}.md")
            problems += found
            mendable.setdefault(role, []).extend(found)
    missing = [r for r in wanted if r not in reviews]
    verified, wrong = factory.read_verified(
        path / factory.VERIFIED, n, reviews, f"reviews/land-{n}/{factory.VERIFIED}"
    )
    problems += wrong
    if wrong:
        mendable["arbiter"] = wrong
    # Each role is mended once a landing round: one already mended is a stop like any other.
    for role in land_mended(folder, n) & set(mendable):
        del mendable[role]
    every = {p for found in mendable.values() for p in found}
    # The rebased change is gated by the script before any reviewer reads it, as each build was.
    # Red is a stop, never a fix: the landing has no builder round, so the person ships it.
    gate = _land_gate_state(root, folder, n, settled)
    if gate and gate["current"] == "FAIL":
        problems.append(
            f"the gate failed on the change as rebased (exit {gate['exit']}), in "
            f"build/land-{n}.gate.md: ship it by hand"
        )
    # So are its acceptance checks, on its commit as rebased, after the gate and before review.
    has_checks = (folder / "checks.md").is_file()
    accept = _accept_state(root, folder, settled) if has_checks else "PASS"
    if accept == "FAIL":
        problems.append(
            f"its acceptance checks failed on the change as rebased, in "
            f"{factory.accept_path(folder).relative_to(folder).as_posix()}: ship it by hand"
        )
    out = {"change": folder.name, "round": n, "reviews": reviews, "missing": missing,
           "resolved": resolved, "fixed": fixed, "gate": gate, "accept": accept,
           "problems": problems, "mend": []}  # fmt: skip
    asks = any(r["verdict"] == "CHANGES" for r in reviews.values())
    if problems and set(problems) <= every:
        out["next"], out["mend"] = "mend", [role for role, found in mendable.items() if found]
    elif problems:
        out["next"] = "stop"
    elif gate and gate["current"] is None:
        out["next"] = "gate"
    elif accept is None:
        out["next"] = "accept"
    elif missing:
        out["next"] = "review"
    elif asks and verified is None:
        out["next"] = "arbitrate"
    elif verified and verified["kept"]:
        out["next"], out["problems"] = (
            "stop",
            [f"the landing review kept {len(verified['kept'])} change(s): ship it by hand"],
        )
    else:
        out["next"] = "pass"
    return out
