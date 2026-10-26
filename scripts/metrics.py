"""What a change cost, from this repo's Claude Code session transcripts: its timeline, read once at
close and written as `Sdlc-*` trailers on the `Close` commit, where history keeps it.

Loaded by path from `sdlc.py`, like the trackers: `uv run --script` and the tests put different
directories on sys.path. Pure functions only, and no import of `sdlc.py`.

The contract the follow-ups extend, never redefine:

    read_events(dirs, branch, ident, check_cmd)   -> [event]   time-ordered; numbers, never text
    summarize(events, dep_closes, cfg, way, tier) -> summary   stages, clocks, stops, tokens
    trailers(summary)                             -> [line]    `Sdlc-Key: name k=v k=v`
    parse_trailers(body)                          -> dict | None

Rework within a change, read from the same events and summary, written on lines of its own:

    rework(events, summary, factory, final, tier) -> dict      `Sdlc-Rework`, `Sdlc-Review`
    happy(events, summary, factory, tier, done)   -> dict      `Sdlc-Happy`
    spike(events, summary)                        -> dict | None   `Sdlc-Spike`
    in_change_trailers(done, first_time, spiked)  -> [line]

An event is a dict with `ts` (an aware datetime) and `kind`:

    skill{name}  turn{ms}  human{reply, command}  tokens{in, cache_create, cache_read, out}
    edit{artifact, added, removed, role?}  stage{to}  plan{action}  question  check{ok}
    permission  subagent{role, ms, in, cache_create, cache_read, out}

`edit.role` is set on an edit a sub-agent made, and absent on the session's own. `artifact()` is
the classifier, public so a reader of the change's diff names its files the same way.

No message text, file path or session id leaves `read_events`: a reply is a class (approve,
revise, other), an edit an artifact kind, a check pass or fail.

Read stops as upper bounds and token spans as lower: a harness message that arrives as a plain user
entry (a "Tool loaded." turn) looks like something the person typed, so it can add an `extra` stop
and end a wait early. The transcripts don't mark it, so it isn't guessed at.
"""

from __future__ import annotations

import json
import re
import statistics
from datetime import datetime
from pathlib import Path

TOKEN_FIELDS = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)
# The short names the timeline and trailers use for them.
TOKEN_KEYS = dict(zip(TOKEN_FIELDS, ("in", "cache_create", "cache_read", "out"), strict=True))
# Either plugin's skills, for stage boundaries: `sdlc:spec`, `sdlc-factory:build`.
SKILL_RE = re.compile(r"<command-name>/(sdlc(?:-factory)?:[a-z0-9-]+)</command-name>")
ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)
STAGE_LINE_RE = re.compile(r"^stage:\s*([a-z]+)\s*$", re.M)
# A change's branch: its number and slug (`sdlc.py`'s `DIR_RE`).
DIR_RE = re.compile(r"^\d{3,}-[a-z0-9][a-z0-9-]*$")
APPROVE_RE = re.compile(
    r"^\s*(yes|y|yep|yeah|ok|okay|go|go ahead|approve|approved|lgtm|ship it|do it|correct|"
    r"sure|proceed)\b",
    re.I,
)
REVISE_RE = re.compile(r"\b(revise|edit|change|fix|rethink|no|not yet|instead|rather)\b", re.I)
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")

STAGES = ("intent", "spike", "design", "build", "test", "ship", "close")
# What opens a stage: a skill, or the `stage:` an intent is edited to.
SKILL_STAGE = {
    "sdlc:intent": "intent",
    "sdlc:spec": "design",
    "sdlc-factory:spec": "design",
    "sdlc-factory:build": "build",
    "sdlc:ship": "ship",
    "sdlc:close": "close",
}
STAGE_EDIT = {
    "plan": "intent",
    "spike": "spike",
    "design": "design",
    "build": "build",
    "test": "test",
    "ship": "ship",
    "shipped": "ship",
}
# Where each gated skill's WAIT falls among its stops: last, after an interview or a draft, or
# first, for the factory's build, whose approval comes before an unattended run.
GATES = {
    "sdlc:intent": "last",
    "sdlc:spec": "last",
    "sdlc:ship": "last",
    "sdlc:close": "last",
    "sdlc-factory:spec": "last",
    "sdlc-factory:build": "first",
}
# The gates each way of running requires, so a change's stops can be read against them.
REQUIRED = {
    ("manual", 2): ("intent", "spec", "plan", "ship", "close"),
    ("manual", 1): ("intent", "ship", "close"),
    ("factory", 1): ("intent", "spec", "run", "ship", "close"),
    ("factory", 2): ("intent", "spec", "run", "ship", "close"),
}


# ---------------------------------------------------------------- the transcripts


def _project_dirs(main: Path) -> list[Path]:
    """Claude Code's transcript folders for this repo: the main checkout's and its change
    worktrees', exactly. A folder name is the checkout's path with every other character a `-`, so
    a sibling repo whose name only starts with this one's is never matched."""
    base = Path.home() / ".claude" / "projects"
    names = {re.sub(r"[^A-Za-z0-9]", "-", str(p)) for p in (main, main.resolve())}
    try:
        found = [p for p in base.iterdir() if p.is_dir()]
    except OSError:
        return []
    return sorted(
        p
        for p in found
        if p.name in names or any(p.name.startswith(n + "--claude-worktrees-") for n in names)
    )


def _only_tool_results(content: object) -> bool:
    """A user entry that is a tool's answer, not something the person typed."""
    return (
        isinstance(content, list)
        and bool(content)
        and all(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
    )


def _entry_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def _lines(path: Path) -> list[dict] | None:
    """A transcript's entries, skipping lines that aren't JSON objects; None when unreadable."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    out = []
    for line in raw:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict):
            out.append(entry)
    return out


# ---------------------------------------------------------------- one change's events


def _ts(entry: dict) -> datetime | None:
    raw = entry.get("timestamp")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _names(ident: str, args: str) -> bool:
    """Whether a command's arguments name this change: `012`, `12`, `012-slug`."""
    number = int(re.match(r"\d+", ident).group(0)) if re.match(r"\d+", ident) else None
    for word in re.findall(r"[0-9][0-9a-z-]*", args):
        lead = re.match(r"\d+", word)
        if word == ident or (lead and number is not None and int(lead.group(0)) == number):
            return True
    return False


def _reply(text: str) -> str:
    text = re.sub(r"<[^>]+>.*?</[^>]+>", " ", text, flags=re.S).strip()
    if APPROVE_RE.match(text):
        return "approve"
    if REVISE_RE.search(text):
        return "revise"
    return "other"


def artifact(path: str, branch: str) -> str:
    """What a file is, by its path, absolute or relative to the worktree: the change's own
    `intent | spec | plan | notes | decisions` (`artifact` for its other files), `test`, `doc` or
    `code`. Public: whatever reads a change's diff classifies its files the same way. The path is
    dropped after."""
    path = path if path.startswith("/") else f"/{path}"
    # The change folder under `.sdlc/work/` or the old `work/`: both end in this.
    marker = f"/work/{branch}/"
    if marker in path:
        name = path.rsplit("/", 1)[-1].removesuffix(".md")
        return name if name in ("intent", "spec", "plan", "notes", "decisions") else "artifact"
    base = path.rsplit("/", 1)[-1]
    if "/tests/" in path or base.startswith("test_") or "_test." in base or ".test." in base:
        return "test"
    return "doc" if base.endswith(".md") else "code"


def _changed_lines(name: str, inp: dict) -> tuple[int, int]:
    def count(value: object) -> int:
        return len(value.splitlines()) if isinstance(value, str) else 0

    if name == "Write":
        return count(inp.get("content")), 0
    if name == "MultiEdit" and isinstance(inp.get("edits"), list):
        edits = [e for e in inp["edits"] if isinstance(e, dict)]
        return (
            sum(count(e.get("new_string")) for e in edits),
            sum(count(e.get("old_string")) for e in edits),
        )
    return count(inp.get("new_string") or inp.get("new_source")), count(inp.get("old_string"))


def _membership(entries: list[dict], branch: str, ident: str) -> list[bool]:
    """Which of one session's entries belong to the change: those on its branch; on `main`, from
    the session's last `/sdlc:intent` before it first reaches the branch; and from a
    `/sdlc:close` naming the change until what is typed after close's approval, the next skill,
    or another change's branch."""
    on_branch = [e.get("gitBranch") == branch for e in entries]
    keep = list(on_branch)
    if any(on_branch):
        first = on_branch.index(True)
        start = None
        for i in range(first):
            m = SKILL_RE.search(_entry_text((entries[i].get("message") or {}).get("content")))
            if entries[i].get("type") == "user" and m and m.group(1) == "sdlc:intent":
                start = i
        if start is not None:
            for i in range(start, first):
                keep[i] = True
    # Close's own run: from its invocation until whatever the person types after approving it, the
    # next skill, or another change's branch. A session often goes on to other work after a close.
    for i, entry in enumerate(entries):
        if entry.get("type") != "user":
            continue
        text = _entry_text((entry.get("message") or {}).get("content"))
        m = SKILL_RE.search(text)
        args = ARGS_RE.search(text)
        if m and m.group(1) == "sdlc:close" and (on_branch[i] or (args and _names(ident, args[1]))):
            approved = False
            for j in range(i, len(entries)):
                other = entries[j].get("gitBranch")
                if j > i and DIR_RE.match(str(other or "")) and other != branch:
                    break
                content = (entries[j].get("message") or {}).get("content")
                typed = (
                    j > i
                    and entries[j].get("type") == "user"
                    and not entries[j].get("isMeta")
                    and not _only_tool_results(content)
                    and _entry_text(content).strip()
                )
                if typed and (approved or SKILL_RE.search(_entry_text(content))):
                    break
                if typed and _reply(_entry_text(content)) == "approve":
                    approved = True
                keep[j] = True
    return keep


def _usage(msg: dict) -> dict:
    usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
    return {
        TOKEN_KEYS[f]: usage.get(f) if isinstance(usage.get(f), int) else 0 for f in TOKEN_FIELDS
    }


def _subagent(path: Path, branch: str) -> dict | None:
    """One sub-agent's run, from its transcript and the `.meta.json` beside it: role, time and
    tokens, the parent tool call that started it, and its edits, as `edit` events tagged with
    its role (the factory's builder writes the code)."""
    try:
        meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    role = str(meta.get("agentType") or "agent")
    entries = _lines(path) or []
    stamps = [t for t in (_ts(e) for e in entries) if t]
    tokens = dict.fromkeys(TOKEN_KEYS.values(), 0)
    edits = []
    seen: set[str] = set()
    for e in entries:
        msg = e.get("message") if isinstance(e.get("message"), dict) else {}
        if e.get("type") != "assistant":
            continue
        if isinstance(msg.get("usage"), dict) and msg.get("id") not in seen:
            seen.add(msg.get("id"))
            for k, v in _usage(msg).items():
                tokens[k] += v
        content = msg.get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("name") in EDIT_TOOLS and _ts(e):
                inp = block.get("input") if isinstance(block.get("input"), dict) else {}
                target = str(inp.get("file_path") or inp.get("notebook_path") or "")
                added, removed = _changed_lines(block["name"], inp)
                edits.append(
                    {"ts": _ts(e), "kind": "edit", "artifact": artifact(target, branch),
                     "added": added, "removed": removed, "role": role}
                )  # fmt: skip
    if not stamps:
        return None
    run = {
        "ts": stamps[0],
        "kind": "subagent",
        "role": role,
        "ms": int((stamps[-1] - stamps[0]).total_seconds() * 1000),
        **tokens,
    }
    return {"parent": meta.get("toolUseId"), "events": [run, *edits]}


def read_events(dirs: list[Path], branch: str, ident: str, check_cmd: str | None) -> list[dict]:
    """The change's events from every session in `dirs`, oldest first. Numbers only."""
    events: list[dict] = []
    check = (check_cmd or "").strip()
    for folder in dirs:
        for path in sorted(folder.glob("*.jsonl")):
            entries = _lines(path)
            if not entries:
                continue
            keep = _membership(entries, branch, ident)
            if not any(keep):
                continue
            checks: dict[str, datetime] = {}
            agents: set[str] = set()
            seen: set[str] = set()
            for entry, mine in zip(entries, keep, strict=True):
                ts = _ts(entry)
                if not mine or ts is None:
                    continue
                kind = entry.get("type")
                msg = entry.get("message") if isinstance(entry.get("message"), dict) else {}
                content = msg.get("content")
                if kind == "system" and entry.get("subtype") == "turn_duration":
                    ms = entry.get("durationMs")
                    ms = ms if isinstance(ms, int) else 0
                    events.append({"ts": ts, "kind": "turn", "ms": ms})
                elif kind == "user":
                    decision = entry.get("permissionDecision")
                    if isinstance(decision, dict) and decision.get("source") == "user_temporary":
                        events.append({"ts": ts, "kind": "permission"})
                    if isinstance(content, list):
                        for block in content:
                            if (
                                isinstance(block, dict)
                                and block.get("type") == "tool_result"
                                and block.get("tool_use_id") in checks
                            ):
                                ok = not block.get("is_error")
                                events.append({"ts": ts, "kind": "check", "ok": ok})
                    if entry.get("isMeta") or _only_tool_results(content):
                        continue
                    text = _entry_text(content)
                    m = SKILL_RE.search(text)
                    if m:
                        events.append({"ts": ts, "kind": "skill", "name": m.group(1)})
                    if text.strip():
                        events.append(
                            {"ts": ts, "kind": "human", "reply": _reply(text), "command": bool(m)}
                        )
                elif kind == "assistant":
                    mid = msg.get("id")
                    if isinstance(msg.get("usage"), dict) and mid not in seen:
                        if isinstance(mid, str):
                            seen.add(mid)
                        events.append({"ts": ts, "kind": "tokens", **_usage(msg)})
                    for block in content if isinstance(content, list) else []:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        name = block.get("name")
                        inp = block.get("input") if isinstance(block.get("input"), dict) else {}
                        if name in EDIT_TOOLS:
                            target = str(inp.get("file_path") or inp.get("notebook_path") or "")
                            added, removed = _changed_lines(name, inp)
                            events.append(
                                {"ts": ts, "kind": "edit", "artifact": artifact(target, branch),
                                 "added": added, "removed": removed}
                            )  # fmt: skip
                            new = inp.get("new_string") or inp.get("content") or ""
                            stage = STAGE_LINE_RE.search(new) if isinstance(new, str) else None
                            if target.endswith(f"/work/{branch}/intent.md") and stage:
                                events.append({"ts": ts, "kind": "stage", "to": stage.group(1)})
                        elif name in ("EnterPlanMode", "ExitPlanMode"):
                            action = "enter" if name == "EnterPlanMode" else "exit"
                            events.append({"ts": ts, "kind": "plan", "action": action})
                        elif name == "AskUserQuestion":
                            events.append({"ts": ts, "kind": "question"})
                        elif name == "Bash" and check:
                            # The gate, alone or piped on (`./check.sh 2>&1 | tail`).
                            if str(inp.get("command", "")).strip().startswith(check):
                                checks[str(block.get("id"))] = ts
                        elif name == "Agent":
                            agents.add(str(block.get("id")))
            for sub in sorted((folder / path.stem / "subagents").glob("agent-*.jsonl")):
                found = _subagent(sub, branch)
                if found and found["parent"] in agents:
                    events.extend(found["events"])
    events.sort(key=lambda e: e["ts"])
    return events


# ---------------------------------------------------------------- what they add up to


def _minutes(seconds: float) -> int:
    return int(round(seconds / 60))


def _blank_stage() -> dict:
    return {
        "segments": 0,
        "elapsed": 0.0,
        "agent": 0.0,
        "response": [],
        "away": 0.0,
        "blocked": 0.0,
        "gate": 0,
        "question": 0,
        "extra": 0,
        "permission": 0,
        "reply": [],
        "checks": 0,
        "checks_failed": 0,
        "edits": {},
        **dict.fromkeys(TOKEN_KEYS.values(), 0),
    }


def _active(stage: dict) -> bool:
    """Whether anything was counted in a stage, seen as a segment or not."""
    counted = ("agent", "away", "blocked", "gate", "question", "extra", "permission", "checks")
    return bool(
        stage["response"]
        or stage["edits"]
        or any(stage[k] for k in counted)
        or any(stage[k] for k in TOKEN_KEYS.values())
    )


def _stage_of(event: dict) -> str | None:
    if event["kind"] == "skill":
        return SKILL_STAGE.get(event["name"])
    if event["kind"] == "stage":
        return STAGE_EDIT.get(event["to"])
    if event["kind"] == "plan" and event["action"] == "enter":
        return "build"
    return None


def summarize(
    events: list[dict], dep_closes: dict[str, datetime | None], cfg: dict, way: str, tier: int
) -> dict:
    """Stages as segments, the four clocks, stops against the gates required, and tokens, from
    one change's events. `dep_closes` maps each `depends_on:` change to when its `Close` commit
    landed (None while it hasn't): an idle gap before then is blocked, not away."""
    idle = cfg["idle_minutes"] * 60
    stages = {s: _blank_stage() for s in STAGES}
    roles: dict[str, dict] = {}
    blocked_by = dict.fromkeys(dep_closes, 0.0)
    stops: list[dict] = []
    segments: list[dict] = []
    current: str | None = None
    furthest = -1
    reenter = 0
    turn_end: datetime | None = None
    turn_stage = "intent"
    turns: list[tuple[datetime, float, str]] = []  # (end, seconds, stage at its end)
    span: dict | None = None  # the gated skill whose stops are being gathered

    def close_span() -> None:
        if not span or not span["stops"]:
            return
        if GATES[span["skill"]] == "first":
            pick = span["stops"][0]
        else:
            # The WAIT is the last approval: a request typed after it ("now start the plan") is
            # the person moving on, not the gate.
            approvals = [s for s in span["stops"] if s["reply"] == "approve"]
            pick = approvals[-1] if approvals else span["stops"][-1]
        for stop in span["stops"]:
            if stop is pick:
                stop["kind"] = "gate"
            elif span["skill"] == "sdlc-factory:build":
                stop["kind"] = "question"
        stops.extend(span["stops"])

    for event in events:
        opens = _stage_of(event)
        if opens and opens != current:
            if segments:
                segments[-1]["end"] = event["ts"]
            order = STAGES.index(opens)
            if order < furthest:
                reenter += 1
            furthest = max(furthest, order)
            current = opens
            segments.append({"stage": opens, "start": event["ts"], "end": event["ts"]})
            stages[opens]["segments"] += 1
        here = stages[current or "intent"]
        if segments:
            segments[-1]["end"] = event["ts"]
        kind = event["kind"]
        if kind == "skill":
            close_span()
            span = {"skill": event["name"], "stops": []} if event["name"] in GATES else None
        elif kind == "turn":
            turns.append((event["ts"], event["ms"] / 1000, current or "intent"))
            turn_end, turn_stage = event["ts"], current or "intent"
        elif kind == "human":
            if turn_end is not None:
                gap = (event["ts"] - turn_end).total_seconds()
                waited = stages[turn_stage]
                if gap <= idle:
                    waited["response"].append(gap)
                else:
                    blocked = 0.0
                    for dep, closed in dep_closes.items():
                        until = event["ts"] if closed is None else min(event["ts"], closed)
                        part = max(0.0, (until - turn_end).total_seconds())
                        blocked_by[dep] += part
                        blocked = max(blocked, part)
                    waited["blocked"] += blocked
                    waited["away"] += gap - blocked
                if not event["command"]:
                    stop = {"stage": turn_stage, "kind": "extra", "reply": event["reply"]}
                    if span is not None:
                        span["stops"].append(stop)
                    else:
                        stops.append(stop)
            turn_end = None
        elif kind == "plan" and event["action"] == "exit":
            stops.append({"stage": current or "build", "kind": "gate", "reply": "approve"})
        elif kind == "question":
            stops.append({"stage": current or "intent", "kind": "question", "reply": None})
        elif kind == "permission":
            here["permission"] += 1
        elif kind == "check":
            here["checks"] += 1
            here["checks_failed"] += 0 if event["ok"] else 1
        elif kind == "edit":
            here["edits"][event["artifact"]] = here["edits"].get(event["artifact"], 0) + 1
        elif kind == "tokens":
            for k in TOKEN_KEYS.values():
                here[k] += event[k]
        elif kind == "subagent":
            role = roles.setdefault(
                event["role"], {"runs": 0, "agent": 0.0, **dict.fromkeys(TOKEN_KEYS.values(), 0)}
            )
            role["runs"] += 1
            role["agent"] += event["ms"] / 1000
            for k in TOKEN_KEYS.values():
                role[k] += event[k]
    close_span()

    for seg in segments:
        stages[seg["stage"]]["elapsed"] += (seg["end"] - seg["start"]).total_seconds()
    # A turn can outlast a stage (a whole build in one turn that ends after `stage: test`), so its
    # time goes to each segment it overlaps, and only what falls outside them to its last stage.
    for end, seconds, last in turns:
        start = end.timestamp() - seconds
        placed = 0.0
        for seg in segments:
            lo = max(start, seg["start"].timestamp())
            hi = min(end.timestamp(), seg["end"].timestamp())
            if hi > lo:
                stages[seg["stage"]]["agent"] += hi - lo
                placed += hi - lo
        stages[last]["agent"] += max(0.0, seconds - placed)
    for stop in stops:
        stage = stages[stop["stage"]]
        stage[stop["kind"]] += 1
        if stop["kind"] == "gate":
            stage["reply"].append(stop["reply"])

    plan_made = any(e["kind"] == "plan" and e["action"] == "exit" for e in events)
    required = list(REQUIRED.get((way, tier), REQUIRED[("manual", 2)]))
    if way == "manual" and tier == 1 and plan_made:
        required.insert(1, "plan")
    seen = [s for s in STAGES if stages[s]["segments"]]
    totals = {
        "elapsed": sum(s["elapsed"] for s in stages.values()),
        "agent": sum(s["agent"] for s in stages.values()) + sum(r["agent"] for r in roles.values()),
        "response": sum(sum(s["response"]) for s in stages.values()),
        "away": sum(s["away"] for s in stages.values()),
        "blocked": sum(s["blocked"] for s in stages.values()),
        "stops": sum(s["gate"] + s["question"] + s["extra"] for s in stages.values()),
        "required": len(required),
        # Measured against its own gates: a change that stops only at them is on target.
        "target": len(required) + cfg["stop_allowance"],
        "allowance": cfg["stop_allowance"],
        "permission": sum(s["permission"] for s in stages.values()),
        "ship_runs": sum(1 for e in events if e["kind"] == "skill" and e["name"] == "sdlc:ship"),
        "reenter": reenter,
    }
    for k in TOKEN_KEYS.values():
        totals[k] = sum(s[k] for s in stages.values()) + sum(r[k] for r in roles.values())
    return {
        "mode": way,
        # The caller, which knows how many transcripts it read, puts that number first.
        "coverage": f"stages={','.join(seen) or 'none'}",
        "totals": totals,
        # A stage seen, or one with activity before any stage opened (counted under intent), so
        # the stage lines always add up to the totals.
        "stages": {s: v for s, v in stages.items() if v["segments"] or _active(v)},
        "roles": roles,
        "blocked": blocked_by,
        "stops": stops,
        "segments": segments,
        "required": required,
    }


def history_summary(elapsed_seconds: float, way: str, tier: int, cfg: dict, reason: str) -> dict:
    """What history alone gives when the transcripts can't be read: elapsed time, the way of
    running and the gates it requires. Says why."""
    required = REQUIRED.get((way, tier), REQUIRED[("manual", 2)])
    totals = {
        "elapsed": elapsed_seconds,
        "required": len(required),
        "target": len(required) + cfg["stop_allowance"],
        "allowance": cfg["stop_allowance"],
    }
    return {
        "mode": way,
        "coverage": f"none: {reason}",
        "totals": totals,
        "stages": {},
        "roles": {},
        "blocked": {},
        "stops": [],
        "segments": [],
        "required": list(required),
    }


# ---------------------------------------------------------------- rework within a change

# Not retro's `rework` (a later change fixing this one): the trial and error inside one change, the
# happy path it measures against, and spikes, deliberate trial and error reported apart.
HAPPY_STAGES = ("intent", "design", "build", "test", "ship", "close")
SPEC_SKILLS = ("sdlc:spec", "sdlc-factory:spec")


def _walk(events: list[dict]) -> list[tuple[dict, str, str | None]]:
    """Each event with the stage it falls in and the gated skill whose span is open, by
    `summarize`'s own rules, for the counts that need order: what came before the first pass, an
    edit after its stage ended, a reply inside a skill's span."""
    current: str | None = None
    span: str | None = None
    out = []
    for event in events:
        opens = _stage_of(event)
        if opens:
            current = opens
        if event["kind"] == "skill":
            span = event["name"] if event["name"] in GATES else None
        out.append((event, current or "intent", span))
    return out


def _reentries(segments: list[dict]) -> int:
    """`summarize`'s re-entries, less any into or out of a spike: going back to explore, and
    coming back from it, is the spike's own trial and error."""
    furthest, count, prev = -1, 0, None
    for seg in segments:
        order = STAGES.index(seg["stage"])
        if order < furthest and "spike" not in (seg["stage"], prev):
            count += 1
        furthest, prev = max(furthest, order), seg["stage"]
    return count


def _revised(walked: list[tuple[dict, str, str | None]]) -> set[str]:
    """The gated skills a person answered `revise` inside. An upper bound, like the stops."""
    return {
        span
        for e, _, span in walked
        if span and e["kind"] == "human" and not e["command"] and e["reply"] == "revise"
    }


def rework(
    events: list[dict], summary: dict, factory: dict | None, final: int | None, tier: int
) -> dict:
    """Trial and error inside the change, outside its spikes. Without events (no transcripts)
    only what the commit gives: the factory's files and the diff's size, never a zero standing in
    for a count nobody took."""
    out: dict = {}
    if events:
        walked = [w for w in _walk(events) if w[1] != "spike"]
        spec_edits = spec_lines = plan_edits = plan_lines = written = 0
        design_seen = design_done = coding = False
        checks: list[bool] = []
        for e, stage, _ in walked:
            design_seen = design_seen or stage == "design"
            design_done = design_done or (design_seen and stage != "design")
            if e["kind"] == "check":
                checks.append(e["ok"])
            if e["kind"] != "edit":
                continue
            lines = e["added"] + e["removed"]
            if e["artifact"] == "spec" and design_done:
                spec_edits, spec_lines = spec_edits + 1, spec_lines + lines
            if e["artifact"] == "plan" and coding:
                plan_edits, plan_lines = plan_edits + 1, plan_lines + lines
            if e["artifact"] in ("code", "test"):
                written += e["added"]
            coding = coding or e["artifact"] == "code"
        first_pass = checks.index(True) if True in checks else len(checks)
        revise = sum(
            1
            for e, _, span in walked
            if span and e["kind"] == "human" and not e["command"] and e["reply"] == "revise"
        )
        out = {
            "spec_edits": spec_edits,
            "spec_lines": spec_lines,
            "plan_edits": plan_edits,
            "plan_lines": plan_lines,
            "revise": revise,
            "reenter": _reentries(summary["segments"]),
            "check_fail_first": first_pass,
            "check_fail": checks.count(False),
            "ship_reruns": max(0, summary["totals"].get("ship_runs", 0) - 1),
            "written": written,
        }
    if final is not None:
        out["final"] = final
        if events and final:
            out["rewrite"] = out["written"] * 100 // final
    if factory is not None:
        reviews = factory["reviews"]
        out.update(
            {
                "rounds": factory["rounds"],
                "changes": sum(r["changes"] for r in reviews.values()),
                "escalate": int(factory["decision"] == "ESCALATE"),
                "blocking": factory["blocking"],
                "defaults": factory["defaults"],
                "defaults_open": factory["defaults_open"],
                "reviews": reviews,
            }
        )
    return out


def happy(events: list[dict], summary: dict, factory: dict | None, tier: int, done: dict) -> dict:
    """Per stage, whether it went through first time: `yes`, `no`, or `unknown` for a stage
    the transcripts never saw open. `done` is `rework()`'s result. Strict: one failed check is a
    `no`; rates over many changes absorb the odd flaky test."""
    seen = {s for s, v in summary["stages"].items() if v.get("segments")}
    walked = [w for w in _walk(events) if w[1] != "spike"]
    revised = _revised(walked)
    checks = [e["ok"] for e, _, _ in walked if e["kind"] == "check"]
    if factory is not None:
        build = (
            factory["rounds"] == 1
            and not any(r["changes"] for r in factory["reviews"].values())
            and factory["decision"] == "READY"
            and not factory["blocking"]
        )
    else:
        exits = sum(1 for e, _, _ in walked if e["kind"] == "plan" and e["action"] == "exit")
        build = exits <= 1 and (not checks or checks[0])
    design = summary["stages"].get("design") or {}
    rules = {
        "intent": "sdlc:intent" not in revised,
        "design": not revised & set(SPEC_SKILLS)
        and not done.get("spec_edits")
        and design.get("segments") == 1,
        "build": build,
        "test": not any(e["kind"] == "check" and not e["ok"] for e, s, _ in walked if s == "test"),
        "ship": summary["totals"].get("ship_runs") == 1 and "sdlc:ship" not in revised,
        "close": sum(1 for e in events if e["kind"] == "skill" and e["name"] == "sdlc:close") == 1,
    }
    out: dict = {}
    for stage in HAPPY_STAGES:
        if stage == "design" and tier < 2:
            continue
        out[stage] = ("yes" if rules[stage] else "no") if stage in seen else "unknown"
    out["first"] = sum(1 for v in out.values() if v == "yes")
    out["of"] = sum(1 for v in out.values() if v in ("yes", "no"))
    return out


def spike(events: list[dict], summary: dict) -> dict | None:
    """What the change's spikes cost, apart from everything else; None when it had none."""
    s = summary["stages"].get("spike")
    if not s or not s.get("segments"):
        return None
    edits = [e for e, stage, _ in _walk(events) if stage == "spike" and e["kind"] == "edit"]
    return {
        "segments": s["segments"],
        "elapsed": _minutes(s["elapsed"]),
        "agent": _minutes(s["agent"]),
        **{k: s[k] for k in TOKEN_KEYS.values()},
        "edits": len(edits),
        "lines": sum(e["added"] + e["removed"] for e in edits),
    }


# ---------------------------------------------------------------- trailers


def _word(value: str) -> str:
    """A name safe in a trailer: no spaces, slashes or tildes, so no path can hide in one."""
    return re.sub(r"[^A-Za-z0-9_.:,-]", "-", str(value))


def _pairs(values: dict) -> str:
    return " ".join(f"{k}={v}" for k, v in values.items())


def trailers(summary: dict) -> list[str]:
    """The summary as `Sdlc-*` trailer lines: minutes and token counts as whole numbers."""
    clocks = ("elapsed", "agent", "response", "away", "blocked")
    head = {k: _minutes(v) if k in clocks else v for k, v in summary["totals"].items()}
    lines = [
        f"Sdlc-Mode: {_word(summary['mode'])}",
        f"Sdlc-Coverage: {_word_text(summary['coverage'])}",
        f"Sdlc-Totals: {_pairs(head)}",
    ]
    for name, s in summary["stages"].items():
        response = s["response"]
        fields = {
            "segments": s["segments"],
            "elapsed": _minutes(s["elapsed"]),
            "agent": _minutes(s["agent"]),
            "response": _minutes(sum(response)),
            "response_median": _minutes(statistics.median(response)) if response else 0,
            "away": _minutes(s["away"]),
            "blocked": _minutes(s["blocked"]),
            "gate": s["gate"],
            "question": s["question"],
            "extra": s["extra"],
            "permission": s["permission"],
            "reply": ",".join(s["reply"]) or "-",
            "checks": s["checks"],
            "checks_failed": s["checks_failed"],
            "edits": ",".join(f"{k}:{v}" for k, v in sorted(s["edits"].items())) or "-",
            **{k: s[k] for k in TOKEN_KEYS.values()},
        }
        lines.append(f"Sdlc-Stage: {name} {_pairs(fields)}")
    for role, r in sorted(summary["roles"].items()):
        fields = {"runs": r["runs"], "agent": _minutes(r["agent"])}
        fields.update({k: r[k] for k in TOKEN_KEYS.values()})
        lines.append(f"Sdlc-Role: {_word(role)} {_pairs(fields)}")
    for dep, seconds in sorted(summary["blocked"].items()):
        lines.append(f"Sdlc-Blocked: {_word(dep)} minutes={_minutes(seconds)}")
    return lines


def in_change_trailers(done: dict, first_time: dict, spiked: dict | None) -> list[str]:
    """`rework()`, `happy()` and `spike()` as their own `Sdlc-*` lines, after `trailers()`' and
    apart from them, so those stay exactly as they were."""
    fields = {k: v for k, v in done.items() if k != "reviews"}
    lines = [f"Sdlc-Rework: {_pairs(fields)}"] if fields else []
    for role, r in sorted((done.get("reviews") or {}).items()):
        lines.append(f"Sdlc-Review: {_word(role)} {_pairs(r)}")
    lines.append(f"Sdlc-Happy: {_pairs(first_time)}")
    if spiked:
        lines.append(f"Sdlc-Spike: {_pairs(spiked)}")
    return lines


def _word_text(value: str) -> str:
    """Coverage is a short phrase: kept readable, but never a path."""
    return re.sub(r"[/~\\]", "-", value)


def _value(raw: str) -> object:
    if raw.isdigit():
        return int(raw)
    if raw == "-":
        return None
    if ":" in raw and "," in raw or re.fullmatch(r"[a-z]+:\d+", raw):
        return {k: int(v) for k, v in (p.split(":", 1) for p in raw.split(","))}
    return raw


def parse_trailers(body: str | None) -> dict | None:
    """`Sdlc-*` trailers back into a dict, or None when a commit has none."""
    out: dict = {"stages": {}, "roles": {}, "blocked": {}}
    found = False
    for line in (body or "").splitlines():
        m = re.match(r"^Sdlc-([A-Za-z]+):\s*(.*)$", line.strip())
        if not m:
            continue
        found = True
        key, rest = m.group(1).lower(), m.group(2).strip()
        if key in ("mode", "coverage", "base"):
            out[key] = rest
            continue
        words = rest.split()
        name = words[0] if words and "=" not in words[0] else None
        fields = {}
        for word in words[1:] if name else words:
            k, _, v = word.partition("=")
            fields[k] = _value(v)
        if key == "stage" and name:
            if isinstance(fields.get("reply"), str):
                fields["reply"] = fields["reply"].split(",")
            out["stages"][name] = fields
        elif key == "role" and name:
            out["roles"][name] = fields
        elif key == "blocked" and name:
            out["blocked"][name] = fields.get("minutes", 0)
        elif key == "review" and name:
            out.setdefault("reviews", {})[name] = fields
        elif key in ("fixes", "retired", "triaged") and name:
            out.setdefault(key, {})[name] = fields
        else:
            out[key] = fields
    return out if found else None
