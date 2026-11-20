"""What a change cost, read from fixture transcripts: which entries are the change's, its stages,
the four clocks, stops against the gates, tokens, and the trailers close writes.

Every fixture is a transcript built here under a made-up path, the shape Claude Code writes (an
entry per line, `gitBranch` and `timestamp` on each); nothing reads this machine's own.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("sdlc_metrics_test", ROOT / "scripts" / "metrics.py")
metrics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(metrics)

BRANCH = "012-reopen-drafts"
OTHER = "013-draft-titles"
SENTINEL = "words only the person typed"
T0 = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
CFG = {"idle_minutes": 30, "stop_allowance": 1}


def _at(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def user(t: float, text: object, branch: str = BRANCH, **kw) -> dict:
    return {"type": "user", "timestamp": _at(t), "gitBranch": branch, "message": {"content": text},
            **kw}  # fmt: skip


def cmd(t: float, name: str, args: str = "", branch: str = BRANCH) -> dict:
    text = f"<command-name>/{name}</command-name>\n<command-args>{args}</command-args>"
    return user(t, text, branch)


def turn(t: float, minutes: float, branch: str = BRANCH) -> dict:
    return {"type": "system", "subtype": "turn_duration", "timestamp": _at(t), "gitBranch": branch,
            "durationMs": int(minutes * 60_000)}  # fmt: skip


def asst(t: float, mid: str, tools: list[dict] = (), branch: str = BRANCH, tokens: int = 10,
         text: str = SENTINEL):  # fmt: skip
    usage = {"input_tokens": 1, "cache_creation_input_tokens": tokens,
             "cache_read_input_tokens": tokens * 100, "output_tokens": tokens}  # fmt: skip
    content = [{"type": "text", "text": text}, *tools]
    return {"type": "assistant", "timestamp": _at(t), "gitBranch": branch,
            "message": {"id": mid, "content": content, "usage": usage}}  # fmt: skip


def tool(name: str, ident: str = "t1", **inp) -> dict:
    return {"type": "tool_use", "id": ident, "name": name, "input": inp}


def result(t: float, ident: str, error: bool = False, branch: str = BRANCH, **kw) -> dict:
    block = {"type": "tool_result", "tool_use_id": ident, "is_error": error, "content": SENTINEL}
    return user(t, [block], branch, **kw)


def _write(folder: Path, name: str, entries: list[dict]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    return path


def _events(tmp_path: Path, *sessions: list[dict], check: str | None = "./check.sh") -> list:
    folder = tmp_path / "projects" / "-made-up-repo"
    for n, entries in enumerate(sessions):
        _write(folder, f"s{n}", entries)
    return metrics.read_events([folder], BRANCH, "012", check)


def _summary(events: list, deps: dict | None = None, way: str = "manual", tier: int = 2):
    return metrics.summarize(events, deps or {}, CFG, way, tier)


# ---------------------------------------------------------------- which entries are the change's


def test_attribution_by_branch_with_the_intent_and_close_on_main(tmp_path: Path) -> None:
    intent_session = [
        cmd(0, "sdlc:status", "", "main"),  # before the intent: another matter
        turn(1, 0.5, "main"),
        cmd(2, "sdlc:intent", "reopen drafts", "main"),
        turn(4, 1, "main"),
        user(5, "yes", "main"),
        turn(6, 0.5, BRANCH),  # the session moved into the change's worktree
    ]
    other_work = [cmd(3, "sdlc:spec", "", OTHER), turn(5, 2, OTHER), user(7, "yes", OTHER)]
    close_session = [
        cmd(100, "sdlc:intent", "titles", "main"),  # another change's intent, on main
        turn(101, 1, "main"),
        cmd(110, "sdlc:close", "12", "main"),
        turn(111, 1, "main"),
        user(112, "yes", "main"),
        turn(113, 1, "main"),
        user(120, f"now something else: {SENTINEL}", "main"),  # after close's approval
        turn(121, 3, "main"),
    ]
    events = _events(tmp_path, intent_session, other_work, close_session)
    skills = [e["name"] for e in events if e["kind"] == "skill"]
    assert skills == ["sdlc:intent", "sdlc:close"]
    assert sum(e["ms"] for e in events if e["kind"] == "turn") == (1 + 0.5 + 1 + 1) * 60_000
    assert SENTINEL not in json.dumps(events, default=str)


def test_a_sub_agent_counts_toward_the_change_by_its_parent_call(tmp_path: Path) -> None:
    folder = tmp_path / "projects" / "-made-up-repo"
    _write(folder, "s0", [
        cmd(0, "sdlc-factory:build", "12"),
        asst(1, "m1", [tool("Agent", "a1")]),
        asst(1, "m2", [tool("Agent", "a2")], branch=OTHER),
    ])  # fmt: skip
    for agent, role, mins in (("a1", "builder", 7), ("a2", "reviewer-code", 3)):
        sub = folder / "s0" / "subagents"
        edit = tool("Edit", "e1", file_path="/x/src/thing.py", new_string="a\nb", old_string="a")
        _write(sub, f"agent-{agent}", [asst(2, f"x{agent}", [edit]), asst(2 + mins, f"y{agent}")])
        (sub / f"agent-{agent}.meta.json").write_text(
            json.dumps({"agentType": role, "toolUseId": agent})
        )
    events = metrics.read_events([folder], BRANCH, "012", None)
    [sub] = [e for e in events if e["kind"] == "subagent"]
    assert (sub["role"], sub["ms"], sub["out"]) == ("builder", 7 * 60_000, 20)
    [edit] = [e for e in events if e["kind"] == "edit"]
    assert (edit["role"], edit["artifact"], edit["added"]) == ("builder", "code", 2)
    roles = _summary(events)["roles"]
    assert set(roles) == {"builder"} and roles["builder"]["runs"] == 1


def test_a_prompt_answered_for_a_sub_agent_s_tool_is_counted(tmp_path: Path) -> None:
    """A reviewer's tool prompt stops the person as the session's own do."""
    folder = tmp_path / "projects" / "-made-up-repo"
    _write(folder, "s0", [cmd(0, "sdlc:ship"), asst(1, "m1", [tool("Agent", "a1")])])
    sub = folder / "s0" / "subagents"
    _write(sub, "agent-a1", [
        asst(2, "x1", [tool("Bash", "b1", command="git log --oneline -3")]),
        result(3, "b1", permissionDecision={"decision": "accept", "source": "user_temporary"}),
        asst(4, "x2", [tool("Read", "r1", file_path="/x/a.md")]),
        result(5, "r1", permissionDecision={"decision": "accept", "source": "config"}),
    ])  # fmt: skip
    (sub / "agent-a1.meta.json").write_text(
        json.dumps({"agentType": "sdlc:reviewer", "toolUseId": "a1"})
    )
    summary = _summary(metrics.read_events([folder], BRANCH, "012", None))
    assert summary["prompts"] == {"Bash:git:log": {"asked": 1, "rejected": 0}}
    assert summary["stages"]["ship"]["prompts"] == 1


@pytest.mark.parametrize(
    "path, kind",
    [(f"work/{BRANCH}/spec.md", "spec"), (f"/abs/work/{BRANCH}/notes.md", "notes"),
     (f"work/{BRANCH}/build/round-1.md", "artifact"), ("tests/test_x.py", "test"),
     ("src/x.test.ts", "test"), ("README.md", "doc"), ("work/inbox.md", "doc"),
     ("scripts/x.py", "code")],
)  # fmt: skip
def test_the_classifier_takes_paths_relative_or_absolute(path: str, kind: str) -> None:
    assert metrics.artifact(path, BRANCH) == kind


def test_a_message_repeated_per_content_block_counts_once(tmp_path: Path) -> None:
    events = _events(tmp_path, [cmd(0, "sdlc:spec"), asst(1, "m1"), asst(1, "m1"), asst(2, "m2")])
    assert sum(e["out"] for e in events if e["kind"] == "tokens") == 20


# ---------------------------------------------------------------- stages


def test_stages_from_skills_plan_mode_and_stage_edits_with_reentry(tmp_path: Path) -> None:
    intent = f"/x/.claude/worktrees/{BRANCH}/work/{BRANCH}/intent.md"
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"),
        asst(10, "m1", [tool("EnterPlanMode", "p1")]),
        asst(20, "m2", [tool("Edit", "e1", file_path=intent, new_string="stage: test\n")]),
        cmd(30, "sdlc:spec"),  # back to design: a re-entry
        cmd(40, "sdlc:ship"),
    ])  # fmt: skip
    s = _summary(events)
    assert [seg["stage"] for seg in s["segments"]] == ["design", "build", "test", "design", "ship"]
    assert s["totals"]["reenter"] == 1
    assert s["stages"]["design"]["segments"] == 2
    assert s["stages"]["test"]["elapsed"] == 10 * 60
    assert "intent" not in s["stages"] and "close" not in s["stages"], "unseen, never guessed"


def _ship_after_spec(asked: list[dict]) -> list[dict]:
    """A spec run approved, then ship asked for by `asked`, then its WAIT approved."""
    return [
        cmd(0, "sdlc:spec"), turn(1, 1), user(2, "yes"),
        *asked,
        turn(14, 2), user(15, "yes"),
    ]  # fmt: skip


def _skill_call(t: float, name: str) -> list[dict]:
    """The session starting `name` itself: its tool call, the result, the skill's text as meta."""
    return [
        asst(t, f"m{t}", [tool("Skill", f"s{t}", skill=name)]),
        result(t + 0.5, f"s{t}"),
        user(t + 0.5, "Base directory for this skill: ...", isMeta=True),
    ]


def test_a_skill_the_session_starts_counts_as_typed(tmp_path: Path) -> None:
    """A ` /sdlc:ship` that reaches the session as text, which then starts the skill with the
    Skill tool, opens ship where the person asked, and is no stop, as the typed command is."""
    typed = _summary(_events(tmp_path / "a", _ship_after_spec([cmd(10, "sdlc:ship")])))
    started = _events(tmp_path / "b", _ship_after_spec(
        [user(10, " /sdlc:ship"), *_skill_call(11, "sdlc:ship")]
    ))  # fmt: skip
    s = _summary(started)
    assert [seg["stage"] for seg in s["segments"]] == ["design", "ship"]
    assert s["segments"] == typed["segments"]
    assert s["coverage"] == typed["coverage"]
    assert s["totals"]["stops"] == typed["totals"]["stops"]
    assert s["totals"]["ship_runs"] == typed["totals"]["ship_runs"] == 1
    assert s["stages"]["design"]["extra"] == typed["stages"]["design"]["extra"] == 0


def test_a_typed_command_and_its_skill_call_count_once(tmp_path: Path) -> None:
    events = _events(tmp_path, [cmd(0, "sdlc:ship"), *_skill_call(1, "sdlc:ship")])
    assert [e["name"] for e in events if e["kind"] == "skill"] == ["sdlc:ship"]


def test_a_refused_skill_call_opens_nothing(tmp_path: Path) -> None:
    """A call the harness refuses ran no skill: the stage stays where it was."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"), turn(1, 1), user(2, " /sdlc:ship"),
        asst(3, "m3", [tool("Skill", "s3", skill="sdlc:ship")]),
        result(3.5, "s3", error=True),
    ])  # fmt: skip
    assert [e["name"] for e in events if e["kind"] == "skill"] == ["sdlc:spec"]
    assert [seg["stage"] for seg in _summary(events)["segments"]] == ["design"]


def test_a_skill_started_unasked_opens_at_its_call(tmp_path: Path) -> None:
    """Started with no mention in the person's text, the stage opens at the call; a skill that
    isn't the plugins' opens nothing."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"), turn(1, 1), user(2, "carry on"),
        *_skill_call(5, "simplify"),
        *_skill_call(8, "sdlc:ship"),
    ])  # fmt: skip
    assert [e["name"] for e in events if e["kind"] == "skill"] == ["sdlc:spec", "sdlc:ship"]
    s = _summary(events)
    assert s["segments"][-1]["stage"] == "ship"
    assert s["segments"][-1]["start"] == T0 + timedelta(minutes=8)


def test_a_turn_longer_than_its_stage_is_split_across_the_segments(tmp_path: Path) -> None:
    intent = f"/x/work/{BRANCH}/intent.md"
    events = _events(tmp_path, [
        asst(0, "m1", [tool("EnterPlanMode", "p1")]),
        asst(30, "m2", [tool("Edit", "e1", file_path=intent, new_string="stage: test\n")]),
        turn(40, 40),  # one turn from minute 0 to 40, across build and test
    ])  # fmt: skip
    s = _summary(events)
    assert s["stages"]["build"]["agent"] == 30 * 60
    assert s["stages"]["test"]["agent"] == 10 * 60


def test_activity_before_any_stage_opens_is_counted_under_intent(tmp_path: Path) -> None:
    """A session on the branch before any skill: its tokens still add up in a stage line."""
    events = _events(tmp_path, [asst(0, "m0"), turn(2, 2), cmd(3, "sdlc:ship"), asst(4, "m1")])
    s = _summary(events)
    assert s["stages"]["intent"]["segments"] == 0 and s["stages"]["intent"]["out"] == 10
    assert sum(v["out"] for v in s["stages"].values()) == s["totals"]["out"] == 20
    assert "stages=ship" in s["coverage"], "seen means opened, not merely counted"


# ---------------------------------------------------------------- the clocks


def test_a_short_wait_is_response_and_a_long_one_is_away(tmp_path: Path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"),
        turn(5, 5), user(15, "tell me more"),  # 10 minutes: answering
        turn(20, 5), user(20 + 9 * 60, "yes"),  # 9 hours: asleep
    ])  # fmt: skip
    design = _summary(events)["stages"]["design"]
    assert design["agent"] == 10 * 60
    assert design["response"] == [10 * 60]
    assert design["away"] == 9 * 3600


def test_waiting_on_a_dependency_is_blocked_until_it_closes(tmp_path: Path) -> None:
    events = _events(tmp_path, [cmd(0, "sdlc:spec"), turn(10, 10), user(10 + 5 * 60, "yes")])
    closes = T0 + timedelta(minutes=10 + 2 * 60)  # the dependency closes two hours in
    s = _summary(events, {"011-first": closes, "010-done": T0 - timedelta(days=1)})
    design = s["stages"]["design"]
    assert design["blocked"] == 2 * 3600 and design["away"] == 3 * 3600
    assert s["blocked"] == {"011-first": 2 * 3600, "010-done": 0.0}


# ---------------------------------------------------------------- stops


def test_the_gate_is_the_last_approval_and_the_rest_are_extra_or_questions(tmp_path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"),
        turn(1, 1), user(2, "what about drafts?"),  # an interview answer
        asst(3, "m1", [tool("AskUserQuestion", "q1")]),
        turn(4, 1), user(5, "yes"),  # the WAIT
        turn(6, 1), user(7, "now plan it"),  # moving on: not the gate
        asst(7.5, "m2", [tool("EnterPlanMode", "p1")]),
        asst(8, "m3", [tool("ExitPlanMode", "x1")]),
    ])  # fmt: skip
    s = _summary(events)
    design = s["stages"]["design"]
    assert (design["gate"], design["question"], design["extra"]) == (1, 1, 2)
    assert design["reply"] == ["approve"]
    assert s["stages"]["build"]["gate"] == 1, "the plan approval is a gate too"
    assert s["totals"]["stops"] == 5
    assert design["kinds"] == {"after_gate": 1, "revise": 0, "asked": 0, "unprompted": 1,
                               "interrupt": 0, "fix": 0}  # fmt: skip


def _spec_session(*between: dict) -> list[dict]:
    """A spec run with one prose answer, and `between` after it, before the WAIT."""
    return [
        cmd(0, "sdlc:spec"),
        turn(1, 1), user(2, "what about drafts?"),
        *between,
        turn(8, 1), user(9, "yes"),
    ]  # fmt: skip


def test_harness_entries_are_not_the_person(tmp_path: Path) -> None:
    """R1: a background task's notice and a compaction summary add no stop and end no wait."""
    plain = _summary(_events(tmp_path / "a", _spec_session()))
    events = _events(tmp_path / "b", _spec_session(
        turn(3, 1),
        user(4, "<task-notification>done</task-notification>",
             origin={"kind": "task-notification", "producer": "session-task"}),
        user(5, f"This session is being continued. {SENTINEL}", isCompactSummary=True),
    ))  # fmt: skip
    assert {e["kind"] for e in events} >= {"harness"}
    s = _summary(events)
    design = s["stages"]["design"]
    assert (design["extra"], design["harness"], s["totals"]["harness"]) == (1, 2, 2)
    assert s["totals"]["stops"] == plain["totals"]["stops"]
    assert design["away"] == plain["stages"]["design"]["away"]
    assert design["response"] == plain["stages"]["design"]["response"] == [60.0, 60.0]


def test_another_slash_command_is_not_a_stop(tmp_path: Path) -> None:
    """R2: `/reload-plugins` is the person's, and a command like the plugins' own: no stop."""
    plain = _summary(_events(tmp_path / "a", _spec_session()))
    s = _summary(_events(tmp_path / "b", _spec_session(turn(3, 1), cmd(4, "reload-plugins"))))
    assert (s["stages"]["design"]["command"], s["totals"]["command"]) == (1, 1)
    assert s["totals"]["stops"] == plain["totals"]["stops"]
    assert s["coverage"] == plain["coverage"], "only the plugins' skills open stages"


def test_each_extra_stop_has_its_kind(tmp_path: Path) -> None:
    """R3: by shape alone: answering a prose question, revising before the WAIT, moving on after
    it, an interrupt, and the rest."""
    events = _events(tmp_path, [
        turn(0, 0.5), user(0.5, "an idea before anything"),
        cmd(1, "sdlc:spec"),
        asst(2, "m1", text="Shall I fold it in?"), turn(2, 1), user(3, "fold it in"),
        asst(4, "m2"), turn(4, 1), user(5, "revise R2 first"),
        turn(6, 1), user(7, "[Request interrupted by user]"),
        turn(8, 1), user(9, "yes"),
        turn(10, 1), user(11, "now plan it"),
    ])  # fmt: skip
    s = _summary(events)
    kinds = s["stages"]["design"]["kinds"]
    assert kinds == {"after_gate": 1, "revise": 1, "asked": 1, "unprompted": 0, "interrupt": 1,
                     "fix": 0}  # fmt: skip
    assert s["stages"]["intent"]["kinds"]["unprompted"] == 1
    assert s["stages"]["design"]["extra"] == sum(kinds.values())


@pytest.mark.parametrize(
    "text, asked",
    [
        ("Shall I fold it in?", True),
        ("Fix F1, then commit this, with 049-x stamped shipped? (yes / edit the message)", True),
        ("Fix F2, then review again? (yes / edit the findings)\n\n", True),
        ("> `Create this as Tier 1 change 050-x? (yes / change the tier / edit a section)`", True),
        ("**Ready to go?**", True),
        ("Done. Next: `/sdlc:close 049`.", False),
        ("It reads (yes / no) everywhere.", False),
    ],
)  # fmt: skip
def test_a_question_ends_with_a_question_mark_its_answers_after_it_or_not(text, asked) -> None:
    assert metrics._ends_with_question(text) is asked


def test_answering_ship_s_question_before_its_gate_is_asked_not_unprompted(tmp_path) -> None:
    """049's ship: two questions ending with their options, each answered, then the commit's."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:ship"),
        asst(1, "m1", text="Fix F1, then commit this, …? (yes / edit the message)"),
        turn(1, 1), user(2, "yes"),
        asst(3, "m2", text="Fix F2, then review again? (yes / edit the findings)"),
        turn(3, 1), user(4, "yes"),
        asst(5, "m3", text="Commit this, …? (yes / edit the message)"),
        turn(5, 1), user(6, "yes"),
    ])  # fmt: skip
    kinds = _summary(events)["stages"]["ship"]["kinds"]
    assert (kinds["asked"], kinds["unprompted"]) == (2, 0)


def test_harness_entries_never_move_where_a_change_s_run_starts_or_ends() -> None:
    main = "main"
    summary = user(1, f"Continued. It ran <command-name>/sdlc:intent</command-name> {SENTINEL}",
                   main, isCompactSummary=True)  # fmt: skip
    entries = [user(0, "unrelated work", main), summary, user(2, "more", main), user(3, "x")]
    assert metrics._membership(entries, BRANCH, "012") == [False, False, False, True]
    notice = user(5, "<command-name>/sdlc:close</command-name><command-args>012</command-args>",
                  main, origin={"kind": "task-notification"})  # fmt: skip
    entries = [user(4, "x"), notice, user(6, "elsewhere", main)]
    assert metrics._membership(entries, BRANCH, "012") == [True, False, False]
    close = [
        user(4, "x"), cmd(5, "sdlc:close", "012", main), user(6, "yes", main),
        user(7, "<task-notification>done</task-notification>", main,
             origin={"kind": "task-notification"}),
        user(8, "next thing", main),
    ]  # fmt: skip
    assert metrics._membership(close, BRANCH, "012") == [True, True, True, True, False], (
        "a notice after close's approval doesn't end its run; what's typed next does"
    )


def test_no_text_leaves_a_human_event(tmp_path: Path) -> None:
    """R3: a human or harness event holds classes and flags, never what was said."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"),
        asst(1, "m1", text=f"{SENTINEL}?"), turn(1, 1), user(2, f"no {SENTINEL}"),
        user(3, SENTINEL, isCompactSummary=True),
    ])  # fmt: skip
    for e in events:
        if e["kind"] in ("human", "harness"):
            rest = {k: v for k, v in e.items() if k not in ("ts", "kind")}
            flags = {k: v for k, v in rest.items() if k not in ("reply", "words")}
            assert all(isinstance(v, bool) for v in flags.values()), e
            assert isinstance(rest.get("words", 0), int) and not isinstance(rest.get("words"), bool)
            assert rest.get("reply") in (None, "approve", "revise", "other")


def test_extra_kinds_round_trip_through_the_trailers(tmp_path: Path) -> None:
    """R4: `Sdlc-Extra` per stage with any, and `harness=`/`command=` on `Sdlc-Totals` always."""
    events = _events(tmp_path, _spec_session(
        turn(3, 1), cmd(4, "reload-plugins"),
        user(5, "<task-notification/>", origin={"kind": "task-notification"}),
    ) + [cmd(20, "sdlc:ship"), turn(21, 1), user(22, "yes")])  # fmt: skip
    lines = metrics.trailers(_summary(events))
    assert (
        "Sdlc-Extra: design after_gate=0 revise=0 asked=0 unprompted=1 interrupt=0 fix=0 harness=1 "
        "command=1"
    ) in lines
    assert not any(line.startswith("Sdlc-Extra: ship") for line in lines), "nothing extra there"
    back = metrics.parse_trailers("\n".join(lines))
    assert back["extra"]["design"]["unprompted"] == 1 and set(back["extra"]) == {"design"}
    assert (back["totals"]["harness"], back["totals"]["command"]) == (1, 1)
    assert back["stages"]["design"]["extra"] == 1


def test_an_after_gate_stop_names_the_skill_whose_gate_it_followed(tmp_path: Path) -> None:
    """169 R11: each `after_gate` stop keeps the gated skill whose span it fell in, written as one
    `Sdlc-AfterGate` line a skill and read back; the `Sdlc-Extra` lines are as they were."""
    events = _events(tmp_path, [
        *_spec_session(), turn(10, 1), user(11, "now plan it"),
        cmd(20, "sdlc:ship"), turn(21, 1), user(22, "yes"),
        turn(23, 1), user(24, "and the next one"), turn(25, 1), user(26, "then close it"),
    ])  # fmt: skip
    s = _summary(events)
    assert s["after_gate"] == {"sdlc:spec": 1, "sdlc:ship": 2}
    lines = metrics.trailers(s)
    assert [x for x in lines if x.startswith("Sdlc-AfterGate:")] == [
        "Sdlc-AfterGate: sdlc:ship stops=2", "Sdlc-AfterGate: sdlc:spec stops=1",
    ]  # fmt: skip
    extra = [x for x in lines if x.startswith("Sdlc-Extra:")]
    assert extra == [
        "Sdlc-Extra: design after_gate=1 revise=0 asked=0 unprompted=1 interrupt=0 fix=0 "
        "harness=0 command=0",
        "Sdlc-Extra: ship after_gate=2 revise=0 asked=0 unprompted=0 interrupt=0 fix=0 "
        "harness=0 command=0",
    ]
    back = metrics.parse_trailers("\n".join(lines))
    assert back["after_gate"] == {"sdlc:ship": {"stops": 2}, "sdlc:spec": {"stops": 1}}
    plain = metrics.trailers(_summary(_events(tmp_path / "b", _spec_session())))
    assert not any(x.startswith("Sdlc-AfterGate") for x in plain), "none written for none"


def test_close_names_each_skill_it_ran(tmp_path: Path) -> None:
    """One `Sdlc-Skill` line a plugin skill the change's events started, typed or by the
    Skill tool, each run counted; read back as `skills`. A commit without one is unrecorded."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"), turn(1, 1), user(2, "yes"),
        cmd(10, "sdlc:ship"), turn(11, 1), user(12, "fix all 2 first"),
        user(20, " /sdlc:ship"), *_skill_call(21, "sdlc:ship"), turn(22, 1), user(23, "yes"),
    ])  # fmt: skip
    s = _summary(events)
    assert s["skills"] == {"sdlc:ship": 2, "sdlc:spec": 1}
    lines = metrics.trailers(s)
    assert [x for x in lines if x.startswith("Sdlc-Skill:")] == [
        "Sdlc-Skill: sdlc:ship runs=2", "Sdlc-Skill: sdlc:spec runs=1",
    ]  # fmt: skip
    back = metrics.parse_trailers("\n".join(lines))
    assert back["skills"] == {"sdlc:ship": {"runs": 2}, "sdlc:spec": {"runs": 1}}
    assert "skills" not in metrics.parse_trailers("Sdlc-Mode: manual"), "unrecorded, never zero"


def test_the_factorys_build_gate_comes_first_and_its_decisions_are_questions(tmp_path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc-factory:build", "12"),
        turn(1, 1), user(2, "yes"),  # the run's approval
        turn(30, 28), user(31, "option b"),  # a blocking decision
    ])  # fmt: skip
    s = _summary(events, way="factory")
    build = s["stages"]["build"]
    assert (build["gate"], build["question"], build["extra"]) == (1, 1, 0)
    assert s["totals"]["required"] == 4, "the supervisor drafted the spec before its gate"


def test_a_revise_of_the_supervisors_spec_draft_is_a_question_and_the_yes_the_gate(
    tmp_path,
) -> None:
    """The supervisor shows the spec-writer's draft before its one WAIT: a revise of it comes first
    and is answered, but the gate is the first approval, never the revise."""
    events = _events(tmp_path, [
        cmd(0, "sdlc-factory:build", "12"),
        asst(1, "m1", [tool("AskUserQuestion", "q1")]), chose(2, "q1", "revise a requirement"),
        asst(3, "m2", [tool("AskUserQuestion", "q2")]), chose(4, "q2", "yes"),  # the WAIT
        asst(5, "m3", [tool("AskUserQuestion", "q3")]), chose(6, "q3", "option b"),  # a decision
    ])  # fmt: skip
    stops = _summary(events, way="factory")["stops"]
    assert [(s["kind"], s["reply"]) for s in stops] == [
        ("question", "revise"), ("gate", "approve"), ("question", "other"),
    ]  # fmt: skip


def test_a_close_on_main_is_found_in_a_session_read_after_a_tool_result(tmp_path) -> None:
    """`read_events` once reused its `ident` for a tool result's id, so every session read after
    the first tool result lost the change's number, and its typed close with it."""
    events = _events(
        tmp_path,
        [asst(0, "m1", [tool("Bash", "b1", command="ls")]), result(1, "b1")],
        [cmd(110, "sdlc:close", "12", "main"), turn(111, 1, "main")],
    )
    assert [e["name"] for e in events if e["kind"] == "skill"] == ["sdlc:close"]


def ask(t: float, ident: str, question: str, branch: str = "main") -> dict:
    """An `AskUserQuestion` call asking `question`, from the supervisor's session on `main`."""
    call = tool("AskUserQuestion", ident, questions=[{"question": question}])
    return asst(t, f"m-{ident}", [call], branch=branch)


def test_the_supervisor_gives_each_change_only_its_own_command_and_dialogs(tmp_path) -> None:
    """One supervisor session on `main` carries two changes: each change's span opens at the
    `/sdlc-factory:build` naming it and holds only the dialogs naming its `NNN-slug`, so the other
    change's command never closes it and its gate never lands in it."""
    folder = tmp_path / "projects" / "-made-up-repo"
    _write(folder, "supervisor", [
        cmd(0, "sdlc-factory:build", "12", "main"),
        cmd(1, "sdlc-factory:build", "13", "main"),
        ask(2, "q1", f"Run the factory on {OTHER}: at most 12 agent runs?"),
        chose(3, "q1", "yes", "main"),
        ask(4, "q2", f"Write this spec and run the factory on {BRANCH}?"),
        chose(5, "q2", "revise a requirement", "main"),
        ask(6, "q3", f"Write this spec and run the factory on {BRANCH}?"),
        chose(7, "q3", "yes", "main"),
        ask(8, "q4", f"{BRANCH}: D1, which store?"), chose(9, "q4", "option b", "main"),
    ])  # fmt: skip
    events = metrics.read_events([folder], BRANCH, "012", None)
    assert [e["name"] for e in events if e["kind"] == "skill"] == ["sdlc-factory:build"]
    stops = _summary(events, way="factory")["stops"]
    assert [(s["kind"], s["reply"]) for s in stops] == [
        ("question", "revise"), ("gate", "approve"), ("question", "other"),
    ]  # fmt: skip
    assert OTHER not in json.dumps(events, default=str), "no question text leaves"


def test_a_session_the_factory_ran_as_an_agent_is_a_run_of_its_role(tmp_path) -> None:
    """The factory runs each agent as a headless session in the change's worktree, by a session id
    it records: that session is one run of its role, its own read-only explorers runs of theirs,
    and none of it is the person's stages."""
    folder = tmp_path / "projects" / "-made-up-repo--claude-worktrees-012-reopen-drafts"
    _write(folder, "sess-b", [
        user(0, "Build it: plan.md first (Tier 2), then the code, test first."),
        asst(1, "m1", [tool("Agent", "a1", subagent_type="Explore")], tokens=5),
        asst(9, "m2", [tool("Edit", "e1", file_path="/x/drafts.py", new_string="a\nb",
                            old_string="a")], tokens=7),
        turn(10, 10),
    ])  # fmt: skip
    sub = folder / "sess-b" / "subagents"
    _write(sub, "agent-x1", [asst(2, "s1", tokens=3), asst(4, "s2", tokens=3)])
    (sub / "agent-x1.meta.json").write_text(
        json.dumps({"agentType": "Explore", "toolUseId": "a1"}), encoding="utf-8"
    )
    events = metrics.read_events([folder], BRANCH, "012", None, roles={"sess-b": "builder"})
    runs = {e["role"]: e for e in events if e["kind"] == "subagent"}
    assert set(runs) == {"builder", "Explore"}
    assert runs["builder"]["out"] == 12 and runs["Explore"]["out"] == 6
    assert not [e for e in events if e["kind"] in ("turn", "human", "skill")]
    assert [e.get("role") for e in events if e["kind"] == "edit"] == ["builder"]
    lines = metrics.trailers(_summary(events, way="factory"))
    assert any(line.startswith("Sdlc-Role: builder runs=1") for line in lines)
    assert any(line.startswith("Sdlc-Role: Explore runs=1") for line in lines)


def chose(t: float, ident: str, answer: str | None, branch: str = BRANCH, error: bool = False):
    """A dialog's result: the answer the person chose, or none (dismissed, timed out empty)."""
    answers = {"Write this?": answer} if answer is not None else {}
    return result(t, ident, error, branch, toolUseResult={"answers": answers})


def test_a_gate_answered_in_a_dialog_is_the_gate_and_other_dialogs_questions(tmp_path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc:intent"),
        asst(1, "m1", [tool("AskUserQuestion", "q1")]), chose(2, "q1", "O3 (Few stops)"),
        asst(3, "m2", [tool("AskUserQuestion", "q2")]), chose(4, "q2", "yes"),  # the WAIT
        turn(5, 5),
    ])  # fmt: skip
    assert [e["reply"] for e in events if e["kind"] == "answer"] == ["other", "approve"]
    intent = _summary(events)["stages"]["intent"]
    assert (intent["gate"], intent["question"], intent["extra"]) == (1, 1, 0)
    assert intent["reply"] == ["approve"]


@pytest.mark.parametrize("first, second, reply", [
    ("yes", "3 fine", "approve"), ("revise", "4 smooth", "revise"),
])  # fmt: skip
def test_a_two_question_gate_reads_its_approval_from_the_first_answer(
    tmp_path, first, second, reply
) -> None:
    """190 R11: the retro's WAIT asks the approval and then the rating in one dialog; the answer
    is the first question's, so the rating never reads as the reply."""
    answers = {"Write the direction doc?": first, "How did it feel?": second}
    events = _events(tmp_path, [
        cmd(0, "sdlc:retro"),
        asst(1, "m1", [tool("AskUserQuestion", "q1")]),
        result(2, "q1", False, BRANCH, toolUseResult={"answers": answers}),
    ])  # fmt: skip
    assert [e["reply"] for e in events if e["kind"] == "answer"] == [reply]


def test_a_dialog_nobody_answered_is_a_question_and_never_the_gate(tmp_path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"),
        asst(1, "m1", [tool("AskUserQuestion", "q1")]), chose(2, "q1", None),  # dismissed
        asst(3, "m2", [tool("AskUserQuestion", "q2")]), chose(4, "q2", "yes", error=True),
        turn(5, 5), user(6, "no, rethink the design"),
    ])  # fmt: skip
    assert not [e for e in events if e["kind"] == "answer"]
    design = _summary(events)["stages"]["design"]
    assert (design["gate"], design["question"], design["extra"]) == (1, 2, 0)
    assert design["reply"] == ["revise"]


def test_a_dialogs_wait_is_the_persons_time_never_the_agents(tmp_path) -> None:
    """Claude Code's turn duration leaves out the time a dialog waits, so the 42 minutes from the
    command to the turn's end record as a 2-minute turn, and the 40 are the person's."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"),
        asst(1, "m1", [tool("AskUserQuestion", "q1")]),
        chose(41, "q1", "yes"),  # answered after 40 minutes away
        turn(42, 2),
    ])  # fmt: skip
    design = _summary(events)["stages"]["design"]
    assert design["away"] == 40 * 60
    assert design["agent"] == pytest.approx(2 * 60)
    assert design["gate"] == 1


def test_a_revise_chosen_in_a_dialog_counts_as_rework(tmp_path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"),
        asst(1, "m1", [tool("AskUserQuestion", "q1")]), chose(2, "q1", "revise a requirement"),
        asst(3, "m2", [tool("AskUserQuestion", "q2")]), chose(4, "q2", "yes"),
        turn(5, 5),
    ])  # fmt: skip
    s = _summary(events)
    assert s["stages"]["design"]["gate"] == 1 and s["stages"]["design"]["question"] == 1
    assert metrics.rework(events, s, None, None, 2)["revise"] == 1


def test_close_approved_in_a_dialog_ends_its_window_at_what_is_typed_next(tmp_path) -> None:
    events = _events(tmp_path, [
        cmd(110, "sdlc:close", "12", "main"),
        asst(111, "m1", [tool("AskUserQuestion", "q1")], branch="main"),
        chose(112, "q1", "yes", "main"),
        turn(113, 3, "main"),
        user(120, f"now something else: {SENTINEL}", "main"),  # after close's approval
        turn(121, 5, "main"),
    ])  # fmt: skip
    assert [e["ms"] for e in events if e["kind"] == "turn"] == [3 * 60_000]
    assert not [e for e in events if e["kind"] == "human" and not e["command"]]


@pytest.mark.parametrize(
    "text, reply",
    [("yes", "approve"), ("Yes, go ahead", "approve"), ("lgtm", "approve"),
     ("revise R3 first", "revise"), ("no, change the tier", "revise"),
     ("what does this do?", "other")],
)  # fmt: skip
def test_a_reply_is_kept_as_its_class_only(text: str, reply: str) -> None:
    assert metrics._reply(text) == reply


def test_tool_prompts_and_gate_runs_are_counted(tmp_path: Path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc:ship"),
        asst(1, "m1", [tool("Bash", "c1", command="./check.sh 2>&1 | tail -3")]),
        result(2, "c1", error=True, permissionDecision={"source": "user_temporary"}),
        asst(3, "m2", [tool("Bash", "c2", command="./check.sh")]),
        result(4, "c2"),
        asst(5, "m3", [tool("Bash", "c3", command="git status")]),
        result(6, "c3", permissionDecision={"source": "config"}),
    ])  # fmt: skip
    summary = _summary(events)
    ship = summary["stages"]["ship"]
    assert (ship["checks"], ship["checks_failed"], ship["prompts"]) == (2, 1, 1)
    assert summary["prompts"] == {"Bash:check.sh": {"asked": 1, "rejected": 0}}


@pytest.mark.parametrize("check", ["./check.sh", None])
def test_a_hand_gate_is_counted_as_a_check(tmp_path: Path, check) -> None:
    """091 R12: `sdlc.py gate` runs the base branch's check, so it is a `check` event like the
    command itself, failed on an error; with no `commands.check` set too. Nothing else is."""
    gate = "uv run --quiet --script /x/scripts/sdlc.py gate 012"
    status = gate.replace("gate 012", "status")
    quoted = "uv run --quiet --script '/a b/scripts/sdlc.py' gate 012"  # 168 R13
    events = _events(tmp_path, [
        cmd(0, "sdlc:ship"),
        asst(1, "m1", [tool("Bash", "g1", command=gate)]),
        result(2, "g1", error=True),
        asst(3, "m2", [tool("Bash", "g2", command=f"FOO=1 {gate} 2>&1 | tail -3")]),
        result(4, "g2"),
        asst(5, "m3", [tool("Bash", "g3", command=status)]),
        result(6, "g3"),
        asst(7, "m4", [tool("Bash", "g4", command=quoted)]),
        result(8, "g4"),
    ], check=check)  # fmt: skip
    ship = _summary(events)["stages"]["ship"]
    assert (ship["checks"], ship["checks_failed"]) == (3, 1)


def _decided(source: str, decision: str = "accept", **extra) -> dict:
    return {"decision": decision, "source": source, **extra}


def test_a_prompt_is_a_tool_the_person_was_asked_to_allow(tmp_path: Path) -> None:
    """R1: the person's own decisions on a tool, rejections included; never their questions or
    plan gates, which are `question` and `gate`, and never a rule, the mode or the classifier."""
    script = "FOO=1 uv run --quiet --script /x/scripts/sdlc.py accept 042"
    events = _events(tmp_path, [
        cmd(0, "sdlc:ship"),
        asst(1, "m1", [tool("Bash", "b1", command="git push -q origin main")]),
        result(2, "b1", permissionDecision=_decided("user_temporary", grantScope="once")),
        asst(3, "m2", [tool("Bash", "b2", command=script)]),
        result(4, "b2", permissionDecision=_decided("user_reject", "reject")),
        asst(5, "m3", [tool("AskUserQuestion", "q1", questions=[])]),
        result(6, "q1", permissionDecision=_decided("user_temporary", grantScope="once")),
        asst(7, "m4", [tool("ExitPlanMode", "p1")]),
        result(8, "p1", permissionDecision=_decided("user_temporary", grantScope="session")),
        asst(9, "m5", [tool("Bash", "b3", command="git status")]),
        result(10, "b3", permissionDecision=_decided("config", reasonType="classifier")),
        result(11, "gone", permissionDecision=_decided("user_temporary")),
    ])  # fmt: skip
    prompts = [(e["name"], e["rejected"]) for e in events if e["kind"] == "permission"]
    assert prompts == [
        ("Bash:git:push", False),
        ("Bash:sdlc.py:accept", True),
        ("unknown", False),
    ]
    summary = _summary(events)
    assert summary["totals"]["prompts"] == 3
    assert summary["prompts"]["Bash:sdlc.py:accept"] == {"asked": 1, "rejected": 1}
    ship = summary["stages"]["ship"]
    assert (ship["question"], ship["gate"]) == (1, 1)  # still counted, as a question and the plan


@pytest.mark.parametrize(
    ("command", "name"),
    [
        ("git -C /x/y push -q origin main", "Bash:git:push"),
        ("cd /x/y && make -j4 test", "Bash:make"),
        ('cd "$(git rev-parse --show-toplevel)" && ./scripts/client-report.sh --token abc',
         "Bash:client-report.sh"),
        ("uv run --quiet --script /x/plugins/factory/scripts/factory.py verdicts 042",
         "Bash:factory.py:verdicts"),
        ("uv run --group dev pytest -q", "Bash:uv"),
        ("gh issue view 41 --json state", "Bash:gh:issue"),
        ("echo 'unbalanced", "Bash:echo"),
        ("A=1 B=2", "Bash:unknown"),
        ("", "Bash:unknown"),
    ],
)  # fmt: skip
def test_a_prompt_is_named_by_its_program_never_its_arguments(command: str, name: str) -> None:
    """R2: the program's basename, and a fixed subcommand for git, gh and the plugin's scripts."""
    got = metrics._prompt_name("Bash", {"command": command})
    assert got == name
    assert not {"/", "=", " "} & set(got)


def test_a_tool_other_than_bash_is_named_by_the_tool() -> None:
    assert metrics._prompt_name("Edit", {"file_path": "/x/secret.txt"}) == "Edit"
    assert metrics._prompt_name("mcp__notes__search", {"q": "x"}) == "mcp__notes__search"
    assert metrics._prompt_name("", {}) == "unknown"


def test_the_modes_a_change_ran_in_are_kept_beside_its_prompts(tmp_path: Path) -> None:
    """R4: `auto` decides without asking, so a reader needs the mode to read zero prompts."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:ship"),
        user(1, "go on", permissionMode="auto"),
        user(2, "and on", permissionMode="plan"),
    ], [
        user(3, "more", permissionMode="default"),
    ])  # fmt: skip
    assert _summary(events)["totals"]["prompt_modes"] == "auto,default"
    assert (
        _summary(_events(tmp_path / "none", [cmd(0, "sdlc:ship")]))["totals"]["prompt_modes"] == "-"
    )


def test_prompts_round_trip_through_the_trailers(tmp_path: Path) -> None:
    """R3: `Sdlc-Prompt` lines and `prompts=` back out as written; no `permission=` any more."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:ship"),
        user(1, "go on", permissionMode="default"),
        asst(2, "m1", [tool("Bash", "b1", command="git push origin main")]),
        result(3, "b1", permissionDecision=_decided("user_reject", "reject")),
    ])  # fmt: skip
    lines = metrics.trailers(_summary(events))
    assert "Sdlc-Prompt: Bash:git:push asked=1 rejected=1" in lines
    assert not any("permission=" in line for line in lines)
    back = metrics.parse_trailers("\n".join(lines))
    assert back["prompts"] == {"Bash:git:push": {"asked": 1, "rejected": 1}}
    assert (back["totals"]["prompts"], back["totals"]["prompt_modes"]) == (1, "default")
    assert back["stages"]["ship"]["prompts"] == 1


def test_edits_are_kept_as_artifact_kinds(tmp_path: Path) -> None:
    base = f"/x/work/{BRANCH}"
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"),
        asst(1, "m1", [tool("Write", "w1", file_path=f"{base}/spec.md", content="a\nb\n")]),
        asst(2, "m2", [tool("Edit", "e1", file_path="/x/scripts/thing.py", new_string="x",
                            old_string="y\nz")]),
        asst(3, "m3", [tool("Edit", "e2", file_path="/x/tests/test_thing.py", new_string="x")]),
        asst(4, "m4", [tool("Edit", "e3", file_path="/x/README.md", new_string="x")]),
    ])  # fmt: skip
    edits = [e for e in events if e["kind"] == "edit"]
    assert [e["artifact"] for e in edits] == ["spec", "code", "test", "doc"]
    assert (edits[0]["added"], edits[1]["removed"]) == (2, 2)
    assert "/x/" not in json.dumps(events, default=str)


@pytest.mark.parametrize(
    "way, tier, plan, specced, required",
    [("manual", 2, False, False, 5), ("manual", 1, False, False, 3), ("manual", 1, True, False, 4),
     ("factory", 2, False, False, 4), ("factory", 2, False, True, 5),
     ("factory", 1, False, False, 4)],
)  # fmt: skip
def test_the_gates_each_way_of_running_requires(
    tmp_path, way, tier, plan, specced, required
) -> None:
    """A factory change's spec is drafted by the supervisor before its one gate, so it owes no
    spec gate, unless it ran a spec stage of its own; a Tier 1 never has one."""
    entries = [cmd(0, "sdlc:intent")]
    if plan:
        entries.append(asst(1, "m1", [tool("ExitPlanMode", "x1")]))
    if specced:
        entries.append(cmd(2, "sdlc-factory:spec"))
    s = _summary(_events(tmp_path, entries), way=way, tier=tier)
    assert s["totals"]["required"] == required
    assert s["totals"]["target"] == required + 1, "measured against its own gates, plus one"
    assert s["totals"]["allowance"] == 1


def test_an_allowance_of_zero_targets_the_gates_alone(tmp_path: Path) -> None:
    events = _events(tmp_path, [cmd(0, "sdlc:intent")])
    s = metrics.summarize(events, {}, {**CFG, "stop_allowance": 0}, "manual", 1)
    assert s["totals"]["target"] == s["totals"]["required"] == 3


# ---------------------------------------------------------------- trailers


def test_trailers_hold_numbers_and_names_and_read_back(tmp_path: Path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"), turn(5, 5), user(6, f"yes {SENTINEL}"),
        cmd(10, "sdlc:ship"), turn(12, 2), user(13, "yes"),
    ])  # fmt: skip
    s = _summary(events, {"011-first": None})
    s["coverage"] = f"transcripts=1 {s['coverage']}"
    lines = metrics.trailers(s)
    body = "\n".join(lines)
    assert all(line.startswith("Sdlc-") for line in lines)
    assert "/" not in body and "~" not in body and SENTINEL not in body
    back = metrics.parse_trailers(f"Close {BRANCH}\n\nIts artifacts are in abc.\n\n{body}")
    assert back["mode"] == "manual"
    assert back["coverage"] == "transcripts=1 stages=design,ship"
    assert back["totals"]["agent"] == 7 and back["totals"]["required"] == 5
    assert (back["totals"]["target"], back["totals"]["allowance"]) == (6, 1)
    assert back["stages"]["design"]["reply"] == ["approve"]
    assert back["stages"]["design"]["edits"] is None
    assert back["blocked"] == {"011-first": 0}


def test_history_alone_says_why_and_still_reads_back() -> None:
    s = metrics.history_summary(3 * 3600, "factory", 2, CFG, "no transcripts for this change")
    back = metrics.parse_trailers("\n".join(metrics.trailers(s)))
    assert back["coverage"] == "none: no transcripts for this change"
    assert back["totals"] == {"elapsed": 180, "required": 4, "target": 5, "allowance": 1}
    assert back["mode"] == "factory"


def test_where_a_change_started_reads_back_as_its_sha() -> None:
    body = "Close 001-x\n\nIts artifacts are in abc.\n\nSdlc-Mode: manual\nSdlc-Base: 158aa72\n"
    assert metrics.parse_trailers(body)["base"] == "158aa72"


def test_a_commit_without_trailers_reads_as_none() -> None:
    assert metrics.parse_trailers("Close 001-x\n\nIts artifacts are in abc.") is None
    assert metrics.parse_trailers(None) is None


def test_fixes_and_retirements_read_by_id_beside_the_rest() -> None:
    """Two lines of one key never overwrite each other, and the other keys read as before."""
    body = (
        "Close 001-x\n\nIts artifacts are in abc.\n\n"
        "Sdlc-Mode: manual\n"
        "Sdlc-Fixes: 2026-10-01-1 severity=high reported=2026-10-01 introduced_by=000-start\n"
        "Sdlc-Fixes: 2026-10-02-1 severity=low reported=2026-10-02 introduced_by=unknown\n"
        "Sdlc-Retired: 2026-10-03-1 severity=med reported=2026-10-03 reason=duplicate\n"
    )
    back = metrics.parse_trailers(body)
    assert back["mode"] == "manual"
    assert back["fixes"]["2026-10-01-1"] == {
        "severity": "high",
        "reported": "2026-10-01",
        "introduced_by": "000-start",
    }
    assert back["fixes"]["2026-10-02-1"]["severity"] == "low"
    assert back["retired"]["2026-10-03-1"]["reason"] == "duplicate"


# ---------------------------------------------------------------- rework within a change


def ev(t: float, kind: str, **kw) -> dict:
    """An event as `read_events` makes it, built directly."""
    return {"ts": T0 + timedelta(minutes=t), "kind": kind, **kw}


def skill(t: float, name: str) -> dict:
    return ev(t, "skill", name=name)


def say(t: float, reply: str) -> dict:
    return ev(t, "human", reply=reply, command=False)


def stage(t: float, to: str) -> dict:
    return ev(t, "stage", to=to)


def edit(t: float, artifact: str, added: int = 10, removed: int = 0, **kw) -> dict:
    return ev(t, "edit", artifact=artifact, added=added, removed=removed, **kw)


def check(t: float, ok: bool) -> dict:
    return ev(t, "check", ok=ok)


TOKENS = dict.fromkeys(("in", "cache_create", "cache_read", "out"), 1)


def _measure(events, factory=None, final=None, tier=2, way="manual"):
    s = _summary(events, way=way, tier=tier)
    done = metrics.rework(events, s, factory, final, tier)
    return s, done, metrics.happy(events, s, factory, tier, done)


# A change that goes through first time: each gate approved once, the gate green at once.
CLEAN = [
    skill(0, "sdlc:intent"), say(1, "approve"), stage(2, "plan"),
    skill(3, "sdlc:spec"), say(4, "approve"), edit(5, "spec"), stage(5, "design"),
    ev(6, "plan", action="enter"), ev(7, "plan", action="exit"), edit(8, "plan"),
    edit(9, "code", 300), edit(10, "test", 100), check(11, True), stage(12, "test"),
    check(13, True), skill(14, "sdlc:ship"), say(15, "approve"),
    skill(16, "sdlc:close"), say(17, "approve"),
]  # fmt: skip


# A factory change landed by `/sdlc-factory:land`: no ship or close skill of its own.
LANDED = [
    skill(0, "sdlc:intent"), say(1, "approve"), stage(2, "plan"),
    skill(3, "sdlc-factory:build"), say(4, "approve"), stage(5, "build"), edit(6, "code", 50),
    stage(7, "test"), skill(8, "sdlc-factory:land"),
]  # fmt: skip


@pytest.mark.parametrize("by, auto", [("auto", 1), ("person", 0)])
def test_a_landed_change_owes_one_gate_for_ship_and_close_and_an_auto_pass_is_apart(
    by, auto
) -> None:
    """One gate, the batch's, stands for ship's and close's; when it passed itself it is counted
    as `auto`, beside `stops`, never as the person's, and its ship and close read `auto`, which
    no first-time rate counts."""
    events = [*LANDED, say(9, "approve")] if by == "person" else LANDED
    s = metrics.summarize(events, {}, CFG, "factory", 1, by)
    assert s["required"] == ["intent", "run", "land"]
    unlanded = metrics.summarize(events, {}, CFG, "factory", 1)
    assert s["totals"]["auto"] == auto and s["totals"]["stops"] == unlanded["totals"]["stops"]
    back = metrics.parse_trailers("\n".join(metrics.trailers(s)))
    assert back["totals"]["auto"] == auto, "auto= reads back"
    first = metrics.happy(events, s, None, 1, metrics.rework(events, s, None, None, 1), 0, by)
    assert (first["ship"], first["close"]) == (("auto", "auto") if by == "auto" else ("yes", "yes"))


@pytest.mark.parametrize("unreviewed", [2, "unknown"])
def test_a_landing_with_unreviewed_paths_carries_them_to_totals(unreviewed) -> None:
    """104 R15: `unreviewed=` on a landed change's `Sdlc-Landed` is carried to `Sdlc-Totals`,
    beside `auto=`, and reads back. It appears only on a landed change whose tip has the field."""
    tip = metrics.parse_trailers(f"Sdlc-Landed: by=person unreviewed={unreviewed}")
    s = metrics.summarize([*LANDED, say(9, "approve")], {}, CFG, "factory", 1, "person")
    metrics.landed_unreviewed(s, tip)
    back = metrics.parse_trailers("\n".join(metrics.trailers(s)))
    assert back["totals"]["unreviewed"] == unreviewed and back["totals"]["auto"] == 0
    bare = metrics.summarize(LANDED, {}, CFG, "factory", 1, "auto")
    metrics.landed_unreviewed(bare, metrics.parse_trailers("Sdlc-Landed: by=auto"))
    assert "unreviewed" not in bare["totals"], "a landing with nothing unreviewed"
    unlanded = metrics.summarize(LANDED, {}, CFG, "factory", 1)
    metrics.landed_unreviewed(unlanded, None)
    assert "unreviewed" not in unlanded["totals"], "never on a change no landing made"
    odd = metrics.summarize(LANDED, {}, CFG, "factory", 1, "person")
    metrics.landed_unreviewed(odd, metrics.parse_trailers("Sdlc-Landed: by=person unreviewed=x"))
    assert "unreviewed" not in odd["totals"], "an unreadable value is left out"


def test_a_land_typed_on_main_names_each_change_it_lands(tmp_path) -> None:
    """The supervisor's `/sdlc-factory:land 012 013` opens each change's span, so a dialog naming
    one change counts on it alone."""
    folder = tmp_path / "projects" / "-made-up-repo"
    _write(folder, "lander", [
        cmd(0, "sdlc-factory:land", "12 13", "main"),
        ask(1, "q1", f"Land {BRANCH} and {OTHER}, each closed and pushed?"),
        chose(2, "q1", "yes", "main"),
    ])  # fmt: skip
    for branch, ident in ((BRANCH, "012"), (OTHER, "013")):
        events = metrics.read_events([folder], branch, ident, None)
        assert [e["name"] for e in events if e["kind"] == "skill"] == ["sdlc-factory:land"]
        assert _summary(events, way="factory")["stages"]["ship"]["gate"] == 1


def test_a_clean_change_is_happy_at_every_stage_with_no_rework() -> None:
    _, done, first = _measure(CLEAN, final=400)
    assert first == {"intent": "yes", "design": "yes", "build": "yes", "test": "yes",
                     "ship": "yes", "close": "yes", "first": 6, "of": 6}  # fmt: skip
    assert done == {
        "spec_edits": 0, "spec_lines": 0, "plan_edits": 0, "plan_lines": 0, "revise": 0,
        "reenter": 0, "check_fail_first": 0, "check_fail": 0, "ship_reruns": 0,
        "written": 400, "final": 400, "rewrite": 100,
    }  # fmt: skip


def test_a_circling_change_counts_each_kind_of_rework() -> None:
    events = [
        skill(0, "sdlc:intent"), say(1, "revise"), say(2, "approve"), stage(3, "plan"),
        skill(4, "sdlc:spec"), say(5, "approve"), edit(6, "spec"), stage(6, "design"),
        ev(7, "plan", action="enter"), ev(8, "plan", action="exit"),
        ev(9, "plan", action="exit"),  # the first plan was sent back
        edit(10, "plan"), edit(11, "code", 300), edit(12, "plan", 4, 2),  # changed mid-build
        check(13, False), check(14, False), check(15, True), check(16, False),
        edit(17, "spec", 3, 1),  # the spec reworded after design
        skill(18, "sdlc:spec"), say(19, "approve"),  # back to design: a re-entry
        skill(20, "sdlc:ship"), say(21, "revise"),
        skill(22, "sdlc:ship"), say(23, "approve"),
        skill(24, "sdlc:close"), skill(25, "sdlc:close"),  # rerun after a refusal
    ]  # fmt: skip
    _, done, first = _measure(events, final=200)
    assert (done["spec_edits"], done["spec_lines"]) == (1, 4)
    assert (done["plan_edits"], done["plan_lines"]) == (1, 6)
    assert done["revise"] == 2 and done["reenter"] == 1
    assert (done["check_fail_first"], done["check_fail"]) == (2, 3)
    assert done["ship_reruns"] == 1
    assert (done["written"], done["final"], done["rewrite"]) == (300, 200, 150)
    assert first["intent"] == first["design"] == first["build"] == "no"
    assert first["ship"] == first["close"] == "no"
    assert (first["first"], first["of"]) == (0, 5) and first["test"] == "unknown"


# Ship run, stopped for its review's findings ("fix them", not a revise word), and run again.
RERUN = [
    *CLEAN[:14], skill(14, "sdlc:ship"), say(15, "approve"), say(15.5, "other"),
    skill(15.8, "sdlc:ship"), say(15.9, "approve"), *CLEAN[16:],
]  # fmt: skip


@pytest.mark.parametrize(
    "events, fixed, ship",
    [
        (CLEAN, 0, "yes"),
        (CLEAN, 2, "yes"),  # fixed inside one run's yes: first time, plainly
        (RERUN, 2, "fixed"),  # rerun only for its own review's findings
        (RERUN, 0, "no"),  # rerun with nothing the review fixed
        ([*RERUN[:-2], say(15.95, "revise"), *RERUN[-2:]], 2, "no"),  # the person revised
        # "fix all 5 first" inside one run: the review working, never a revise
        ([*CLEAN[:15], say(15.2, "fix"), *CLEAN[15:]], 1, "yes"),
        # "fix F1", then ship run again, the finding fixed
        ([*RERUN[:16], say(15.6, "fix"), *RERUN[16:]], 1, "fixed"),
    ],
    ids=[
        "one-run",
        "one-run-fixed",
        "rerun-for-findings",
        "rerun-for-else",
        "revised",
        "fix-all-in-one-run",
        "fix-then-rerun",
    ],  # fmt: skip
)
def test_a_ship_rerun_for_its_own_findings_reads_fixed(events, fixed, ship) -> None:
    s = _summary(events, way="manual", tier=2)
    done = metrics.rework(events, s, None, None, 2)
    first = metrics.happy(events, s, None, 2, done, fixed)
    assert first["ship"] == ship
    assert first["first"] == sum(first[k] in ("yes", "fixed") for k in metrics.HAPPY_STAGES)


@pytest.mark.parametrize(
    "text, reply",
    [
        ("fix all 5 first", "fix"),
        ("Fix F1", "fix"),
        ("fix F2 and F4, then commit", "fix"),
        ("fix the spec's second requirement", "revise"),
        ("commit without fixing, recording F2 as a nit", "other"),
        ("yes", "approve"),
    ],
)
def test_asking_for_the_reviews_fixes_is_its_own_reply_class(text: str, reply: str) -> None:
    assert metrics._reply(text) == reply


def test_a_failed_check_in_test_is_a_test_rework_not_a_build_one() -> None:
    events = [*CLEAN[:14], check(12.5, False), *CLEAN[14:]]
    _, done, first = _measure(events)
    assert first["build"] == "yes" and first["test"] == "no"
    assert (done["check_fail_first"], done["check_fail"]) == (0, 1)


@pytest.mark.parametrize(
    "path",
    [["build", "spike", "build"], ["plan", "spike", "design"], ["design", "spike", "plan"]],
)
def test_a_spike_and_the_way_back_are_never_rework(path: list[str]) -> None:
    events = [stage(0, path[0]), edit(1, "code", 5),
              stage(10, path[1]), edit(11, "code", 50, 40), check(12, False), say(13, "revise"),
              stage(30, path[2]), check(31, True)]  # fmt: skip
    s, done, _ = _measure(events)
    assert done["reenter"] == 0 and done["check_fail"] == 0 and done["revise"] == 0
    assert done["written"] == 5, "a spike's edits aren't written lines"
    spiked = metrics.spike(events, s)
    assert spiked["segments"] == 1 and spiked["elapsed"] == 20
    assert (spiked["edits"], spiked["lines"]) == (1, 90)


def test_a_change_without_a_spike_reports_none() -> None:
    assert metrics.spike(CLEAN, _summary(CLEAN)) is None


def test_a_stage_never_opened_is_unknown_and_tier_one_has_no_design() -> None:
    events = [ev(0, "tokens", **TOKENS), skill(1, "sdlc:ship"), say(2, "approve")]
    _, _, first = _measure(events, tier=1)
    assert "design" not in first
    assert first["intent"] == "unknown", "activity before any stage opens isn't the stage seen"
    assert (first["ship"], first["first"], first["of"]) == ("yes", 1, 1)


FACTORY = {
    "rounds": 2,
    "reviews": {"code": {"changes": 1, "requests": 3}, "test": {"changes": 0, "requests": 0}},
    "decision": "READY", "blocking": 1, "defaults": 2, "defaults_open": 1,
}  # fmt: skip


def test_the_factorys_rework_comes_from_its_files_and_its_builders_edits() -> None:
    events = [skill(0, "sdlc-factory:build"), say(1, "approve"),
              edit(5, "code", 120, role="builder"),
              ev(6, "subagent", role="builder", ms=1, **TOKENS)]  # fmt: skip
    _, done, first = _measure(events, FACTORY, final=80, way="factory")
    assert (done["written"], done["rewrite"]) == (120, 150), "the builder's lines count"
    assert (done["rounds"], done["changes"], done["escalate"]) == (2, 1, 0)
    assert (done["blocking"], done["defaults"], done["defaults_open"]) == (1, 2, 1)
    assert first["build"] == "no"
    one = {**FACTORY, "rounds": 1, "blocking": 0,
           "reviews": {"code": {"changes": 0, "requests": 0}}}  # fmt: skip
    assert _measure(events, one, way="factory")[2]["build"] == "yes"
    assert _measure(events, {**one, "decision": "ESCALATE"}, way="factory")[2]["build"] == "no"


def test_without_transcripts_only_the_commits_numbers_are_written() -> None:
    s = metrics.history_summary(60, "factory", 2, CFG, "no transcripts for this change")
    done = metrics.rework([], s, FACTORY, 80, 2)
    assert set(done) == {"final", "rounds", "changes", "escalate", "blocking", "defaults",
                         "defaults_open", "reviews"}, "absent, never a zero"  # fmt: skip
    assert "defaults_settled" not in metrics.rework([], s, None, 80, 2), "by hand: no key"
    first = metrics.happy([], s, FACTORY, 2, done)
    assert set(first.values()) - {0} == {"unknown"}


def test_the_walk_opens_the_same_segments_as_summarize() -> None:
    events = [*CLEAN, stage(18, "spike"), stage(19, "test")]
    walked: list[str] = []
    for _, st, _ in metrics._walk(events):
        if not walked or walked[-1] != st:
            walked.append(st)
    assert walked == [seg["stage"] for seg in _summary(events)["segments"]]


def test_the_new_lines_read_back_and_leave_012s_lines_as_they_were() -> None:
    events = [*CLEAN, stage(18, "spike"), edit(19, "code", 2)]
    s = _summary(events)
    s["coverage"] = f"transcripts=1 {s['coverage']}"
    before = metrics.trailers(s)
    done = metrics.rework(events, s, FACTORY, 400, 2)
    first = metrics.happy(events, s, FACTORY, 2, done)
    extra = metrics.in_change_trailers(done, first, metrics.spike(events, s))
    assert metrics.trailers(s) == before, "012's trailers are untouched"
    assert [ln.split(":")[0] for ln in extra] == [
        "Sdlc-Rework", "Sdlc-Review", "Sdlc-Review", "Sdlc-Happy", "Sdlc-Spike"]  # fmt: skip
    body = "\n".join(before + extra)
    assert "/" not in body and "~" not in body and SENTINEL not in body
    back = metrics.parse_trailers(body)
    assert back["rework"]["rewrite"] == 100 and back["rework"]["rounds"] == 2
    assert back["reviews"] == {"code": {"changes": 1, "requests": 3},
                               "test": {"changes": 0, "requests": 0}}  # fmt: skip
    assert back["happy"]["build"] == "no" and back["happy"]["first"] == 5
    assert back["spike"]["edits"] == 1 and back["stages"]["design"]["segments"] == 1


def test_sdlcs_copies_of_the_factorys_patterns_match_its_own() -> None:
    def load(path: Path, name: str):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    sdlc = load(ROOT / "scripts" / "sdlc.py", "sdlc_for_patterns")
    factory = load(ROOT / "plugins" / "factory" / "scripts" / "factory.py", "factory_patterns")
    names = ("VERDICT_RE", "DECISION_RE", "CHANGE_RE", "LEDGER_RE", "KEPT_RE", "DROPPED_RE")
    for name in (*names, "STOPPED_RE", "NEXT_RE", "PROBLEM_RE", "STEP_RE", "ROUND_RE"):
        assert getattr(sdlc.factory_records, name).pattern == getattr(factory, name).pattern, name
    assert sdlc.factory_records.STOPPED == factory.STOPPED
    assert sdlc.factory_records.STEP == factory.STEP
    assert sdlc.factory_records.AGENT_TIMEOUT == factory.AGENT_TIMEOUT
    assert sdlc.factory_records.RECONSIDER == factory.RECONSIDER
    assert sdlc.factory_records.SETTLED == factory.SETTLED
    # 145: the approver's reasons, and what tells a current look line from history.
    for name in ("REASON_RE", "LOOK_SOURCE_RE"):
        assert getattr(sdlc.factory_records, name).pattern == getattr(factory, name).pattern, name
    assert sdlc.factory_records.REASON_KINDS == factory.REASON_KINDS
    assert sdlc.factory_records.DECIDED == factory.DECIDED


SUPERSEDED_LEDGER = """\
# Decisions

- [ ] D1 (builder round 1, blocking): Keep drafts 30 days or forever?
- [x] D2 (builder round 1, default): No badge on a shipped card. → superseded by D4
- [x] D3 (code round 1, default): Log the draft id? → decided: no
- [ ] D4 (builder round 2, default): Keep `was ESCALATE` on a card.
"""


def test_a_superseded_default_is_counted_but_not_open(tmp_path: Path) -> None:
    """105 R8: `_factory_files()` reads a superseded line, ticked by `decisions`, as no open
    default, with no edit to its copy of the ledger's pattern; `defaults` still counts it."""

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    spec = importlib.util.spec_from_file_location("sdlc_superseded", ROOT / "scripts" / "sdlc.py")
    sdlc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sdlc)
    name = "008-reopen-drafts"
    git("init", "-q", "-b", "main")
    (tmp_path / "README.md").write_text("a repo\n", encoding="utf-8")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    git("checkout", "-q", "-b", name)
    folder = tmp_path / ".sdlc" / "work" / name
    folder.mkdir(parents=True)
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    (folder / "decisions.md").write_text(SUPERSEDED_LEDGER, encoding="utf-8", newline="\n")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "built")
    found = sdlc.closing._factory_files(tmp_path, name)
    assert (found["blocking"], found["defaults"], found["defaults_open"]) == (1, 3, 1)


def test_the_metrics_read_a_verdict_and_a_decision_after_prose(tmp_path: Path) -> None:
    """140 R8: `_factory_files()` counts a round's verdict and changes, and the decision, where
    each follows prose, as `verdicts` reads them; a reply whose verdicts disagree counts none."""

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    spec = importlib.util.spec_from_file_location("sdlc_prose", ROOT / "scripts" / "sdlc.py")
    sdlc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sdlc)
    name = "008-reopen-drafts"
    git("init", "-q", "-b", "main")
    (tmp_path / "README.md").write_text("a repo\n", encoding="utf-8")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    git("checkout", "-q", "-b", name)
    folder = tmp_path / ".sdlc" / "work" / name
    (folder / "reviews" / "round-1").mkdir(parents=True)
    (folder / "decision.md").write_text("I read every round.\n\nDECISION: READY\n", "utf-8")
    (folder / "reviews" / "round-1" / "code.md").write_text(
        "Status: read.\nVERDICT: CHANGES\n- CHANGE: src/drafts.py:3: saves twice\n", "utf-8"
    )
    (folder / "reviews" / "round-1" / "test.md").write_text(
        "Hmm.\nVERDICT: PASS\nVERDICT: CHANGES\n- CHANGE: tests/x.py: one\n", "utf-8"
    )
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "built")
    found = sdlc.closing._factory_files(tmp_path, name)
    assert found["decision"] == "READY"
    assert found["reviews"]["code"] == {"changes": 1, "requests": 1}
    assert found["reviews"]["test"]["changes"] == 0


def test_a_settled_default_is_counted_apart(tmp_path: Path) -> None:
    """137 R11: a line the approver settled is a default, no open one, and `defaults_settled`;
    its sub-lines are no lines of the ledger."""

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    spec = importlib.util.spec_from_file_location("sdlc_settled", ROOT / "scripts" / "sdlc.py")
    sdlc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sdlc)
    name = "008-reopen-drafts"
    git("init", "-q", "-b", "main")
    (tmp_path / "README.md").write_text("a repo\n", encoding="utf-8")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    git("checkout", "-q", "-b", name)
    folder = tmp_path / ".sdlc" / "work" / name
    folder.mkdir(parents=True)
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    ledger = SUPERSEDED_LEDGER + (
        "  - OPTION: keep it — the card says what happened; one more badge\n"
        "- [x] D5 (code round 2, default): Page at 50? → settled by the approver: spec R2\n"
    )
    (folder / "decisions.md").write_text(ledger, encoding="utf-8", newline="\n")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "built")
    found = sdlc.closing._factory_files(tmp_path, name)
    assert (found["blocking"], found["defaults"], found["defaults_open"],
            found["defaults_settled"]) == (1, 4, 1, 1)  # fmt: skip
    done = metrics.rework([], {}, {**FACTORY, "defaults_settled": 1}, None, 2)
    assert done["defaults_settled"] == 1


def test_both_intent_yes_answers_read_as_approval() -> None:
    """093 R9: intent's two yes answers, by hand and for the factory, are both the gate's yes."""
    assert metrics._reply("yes, by hand") == "approve"
    assert metrics._reply("yes, for the factory") == "approve"


# ---------------------------------------------------------------- words and tool calls (118)


def test_words_are_counted_and_no_text_leaves(tmp_path: Path) -> None:
    """R1: a typed reply's words, a command's name and arguments; never the text itself."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec", "12 reopen"), turn(1, 1), user(2, f"yes {SENTINEL}"),
        cmd(10, "sdlc:ship"), turn(11, 1), user(12, "fix all please"),
    ])  # fmt: skip
    humans = [e["words"] for e in events if e["kind"] == "human"]
    assert humans == [3, 1 + len(SENTINEL.split()), 1, 3]
    s = _summary(events)
    assert (s["stages"]["design"]["words"], s["stages"]["ship"]["words"]) == (9, 4)
    assert s["totals"]["words"] == 13
    lines = metrics.trailers(s)
    body = "\n".join(lines)
    assert SENTINEL not in json.dumps(events, default=str) and SENTINEL not in body
    back = metrics.parse_trailers(body)
    assert back["stages"]["design"]["words"] == 9 and back["totals"]["words"] == 13


def test_every_tool_call_is_counted_with_its_error(tmp_path: Path) -> None:
    """R2: each `tool_use`, named as a prompt is, with its result's `is_error`; one with no
    result has no error. A factory agent's session counts its calls with its role."""
    folder = tmp_path / "projects" / "-made-up-repo"
    _write(folder, "s0", [
        cmd(0, "sdlc:ship"),
        asst(1, "m1", [tool("Bash", "b1", command="git -C /x push origin main"),
                       tool("Read", "r1", file_path="/x/secret.py")]),
        result(2, "b1", error=True),
        result(2, "r1"),
        asst(3, "m2", [tool("Bash", "b2", command="git status")]),  # interrupted: no result
    ])  # fmt: skip
    _write(folder, "builder", [
        user(4, "build it"),
        asst(5, "m3", [tool("Edit", "e1", file_path="/x/a.py", new_string="x")]),
        result(6, "e1"),
    ])  # fmt: skip
    events = metrics.read_events([folder], BRANCH, "012", None, {"builder": "builder"})
    calls = [(e["name"], e["error"], e.get("role")) for e in events if e["kind"] == "tool"]
    assert calls == [
        ("Bash:git:push", True, None), ("Read", False, None), ("Bash:git:status", None, None),
        ("Edit", False, "builder"),
    ]  # fmt: skip
    assert "/x/" not in json.dumps(events, default=str)
    s = _summary(events)
    assert s["tools"]["Bash:git:push"] == {"calls": 1, "errors": 1, "ship": 1}
    assert s["tools"]["Edit"] == {"calls": 1, "errors": 0, "ship": 1}
    assert s["totals"]["tools"] == 4
    assert s["stages"]["ship"]["tools"]["Read"] == 1


def test_tool_lines_round_trip(tmp_path: Path) -> None:
    """R3: one `Sdlc-Tool` line a name, `tools=` on the totals, read back as written."""
    events = _events(tmp_path, [
        cmd(0, "sdlc:spec"),
        asst(1, "m1", [tool("Grep", "g1", pattern="x")]),
        result(2, "g1"),
        cmd(3, "sdlc:ship"),
        asst(4, "m2", [tool("Grep", "g2", pattern="y"), tool("Bash", "b1", command="make")]),
        result(5, "g2", error=True),
        result(5, "b1"),
    ])  # fmt: skip
    lines = metrics.trailers(_summary(events))
    assert "Sdlc-Tool: Grep calls=2 errors=1 design=1 ship=1" in lines
    assert "Sdlc-Tool: Bash:make calls=1 errors=0 ship=1" in lines
    back = metrics.parse_trailers("\n".join(lines))
    assert back["tools"] == {
        "Bash:make": {"calls": 1, "errors": 0, "ship": 1},
        "Grep": {"calls": 2, "errors": 1, "design": 1, "ship": 1},
    }
    assert back["totals"]["tools"] == 3


def test_a_close_from_before_tool_lines_is_unrecorded() -> None:
    """R3, R8: no `tools=` is unrecorded, never no calls; history alone writes none either."""
    old = "Sdlc-Mode: manual\nSdlc-Totals: elapsed=10 agent=5 prompts=0 out=7"
    back = metrics.parse_trailers(old)
    assert "tools" not in back["totals"] and "words" not in back["totals"]
    assert "tools" not in back
    s = metrics.history_summary(600, "manual", 1, CFG, "metrics.transcripts is off")
    lines = metrics.trailers(s)
    assert not any(line.startswith("Sdlc-Tool:") or "tools=" in line for line in lines)


def test_a_cleared_escalation_still_measures_as_escalate(tmp_path: Path) -> None:
    """145 R14: every reason cleared (a look acknowledged, a gate green by hand) leaves the
    approver's call as measuring reads it, since `decision.md` is never rewritten; the look line
    counts in no ledger figure."""

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    spec = importlib.util.spec_from_file_location("sdlc_cleared", ROOT / "scripts" / "sdlc.py")
    sdlc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sdlc)
    name = "008-reopen-drafts"
    git("init", "-q", "-b", "main")
    (tmp_path / "README.md").write_text("a repo\n", encoding="utf-8")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    git("checkout", "-q", "-b", name)
    folder = tmp_path / ".sdlc" / "work" / name
    (folder / "build").mkdir(parents=True)
    (folder / "decision.md").write_text(
        "DECISION: ESCALATE\n\n- ESCALATED: gate: red\n- ESCALATED: look: odd\n", encoding="utf-8"
    )
    (folder / "decisions.md").write_text(
        "# Decisions\n\n- [x] D1 (approver round 1, look): odd → decided: seen\n",
        encoding="utf-8",
        newline="\n",
    )
    (folder / "build" / "gate.md").write_text(
        "GATE: PASS\n\n## Attempt 1\n\nVerdict: PASS\n", encoding="utf-8"
    )
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "built")
    found = sdlc.closing._factory_files(tmp_path, name)
    assert found["decision"] == "ESCALATE"
    assert (found["blocking"], found["defaults"], found["defaults_open"]) == (0, 0, 0)
    assert "gate_fail" not in found, "the hand gate's record is no round's gate"


def test_sdlcs_reasons_and_newest_round_are_the_factorys(tmp_path: Path) -> None:
    """145: `factory_reasons()` reads a decision as `escalation_reasons()` does, and
    `factory_newest_round()` is `newest_round()`, on one folder as it grows."""

    def load(path: Path, name: str):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    sdlc = load(ROOT / "scripts" / "sdlc.py", "sdlc_for_reasons")
    factory = load(ROOT / "plugins" / "factory" / "scripts" / "factory.py", "factory_reasons")
    folder = tmp_path / "008-reopen-drafts"
    folder.mkdir()
    text = (
        "DECISION: ESCALATE\n\n- ESCALATED: D2: the product's call\n- ESCALATED: gate: red\n"
        "  - ESCALATED: look: odd at 390px\n- ESCALATED: taste: flat\n- ESCALATED: D3x: what\n"
        "- ESCALATED: no word here\n"
    )
    (folder / "decision.md").write_text(text, encoding="utf-8")
    assert sdlc.factory_records.reasons(text.splitlines()) == factory.escalation_reasons(folder)
    assert len(factory.escalation_reasons(folder)) == 4
    for files in ([], ["build/round-1.md"], ["reviews/round-2/code.md", "build/round-1.md"],
                  ["build/round-3.restart.md", "build/round-3.gate.md"]):  # fmt: skip
        for rel in files:
            (folder / rel).parent.mkdir(parents=True, exist_ok=True)
            (folder / rel).write_text("x\n", encoding="utf-8")
        assert sdlc.factory_records.newest_round(folder) == factory.newest_round(folder)


# ---------------------------------------------------------------- how an agent worked


@pytest.mark.parametrize(
    "command, writes",
    [
        ("echo x > notes.txt", True),
        ("echo x >> notes.txt", True),
        ("echo x 1> notes.txt", True),
        ("printf x | tee notes.txt", True),
        ("sed -i '' 's/a/b/' lib.py", True),
        ("perl -pi -e 's/a/b/' lib.py", True),
        ("patch -p1 < fix.diff", True),
        ("git apply fix.diff", True),
        ("python3 -c \"from pathlib import Path; Path('a').write_text('x')\"", True),
        ("uv run python -c \"open('a', 'w').write('x')\"", True),
        ("python3 - <<'EOF'\nimport pathlib\npathlib.Path('a').write_text('x')\nEOF", True),
        ("cat > lib.py <<'EOF'\nx = 1\nEOF", True),
        ("pytest -q 2>&1 | tail", False),
        ("make > /dev/null", False),
        ("echo x > /tmp/scratch.txt", False),
        ('echo x > "$TMPDIR/scratch.txt"', False),
        ("grep '>' lib.py", False),
        ("sed -n '1,5p' lib.py", False),
        ("python3 -c \"print(open('lib.py').read())\"", False),
        ("cat <<'EOF'\nx > y\nEOF", False),
    ],
)
def test_a_shell_edit_is_known_by_its_command(command: str, writes: bool) -> None:
    """R3: a `Bash` command writes a file by the named shapes alone."""
    assert metrics._shell(command, None)[0] is writes


@pytest.mark.parametrize(
    "command, check, test",
    [
        ("uv run --group dev pytest -q", None, True),
        ("./check.sh 2>&1 | tail", "./check.sh", True),
        ("python -m pytest tests", None, True),
        ("cd x && CI=1 npx jest", None, True),
        ("cargo test", None, True),
        ("npm test", None, True),
        ('uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py gate 012', None, True),
        ("uv run --quiet --script /x/plugins/factory/scripts/factory.py check 155", None, True),
        ("uv run --quiet --script '/a b/scripts/factory.py' check 155", None, True),
        ("uv run --quiet --script '/a b/scripts/sdlc.py' gate 012", None, True),
        ("npx --yes pnpm test", None, True),
        ("uvx --quiet tox", None, True),
        ("uv run --quiet --script /x/scripts/factory.py land-check", None, False),
        ("uv run --quiet --script /x/scripts/factory.py gate 155", None, False),
        ("grep pytest x", None, False),
        ("cat pytest.ini", None, False),
        ("go build ./...", None, False),
    ],
)
def test_a_test_run_is_known_by_its_program(command: str, check, test: bool) -> None:
    """R5: the host's check, the hand gate, the factory's `check` (155 R11), or a known runner past
    `uv run`, `npx`, `python -m` and `VAR=`: never a word that only names one, nor the factory's
    `gate` or `land-check`, which the script runs, not an agent."""
    assert metrics._shell(command, check)[2] is test


@pytest.mark.parametrize(
    "command, bg", [("pytest -q &", True), ("sleep 5 & ", True), ("a && b", False),
                    ("make 2>&1", False), ("a &\nb", True), ("sleep 5 & echo hi", True),
                    ("make &> log", False), ("cat <&3", False), ("a |& b", False),
                    ("echo 'a & b'", False), ("echo a \\& b", False),
                    ("curl x?a=1&b=2", True), ("curl 'x?a=1&b=2'", False)],
)  # fmt: skip
def test_a_command_ending_in_a_lone_ampersand_goes_to_the_background(command, bg) -> None:
    """R4: the `&` half; the result's half is read from the transcript below. An unquoted `&`
    inside a URL backgrounds the command before it, as the shell runs it (174 R10)."""
    assert metrics._shell(command, None)[1] is bg


BEHAVIOURS = ("edits", "shell_edits", "bg", "tool_errors", "test_runs", "broke")
WORKTREE = "-made-up-repo--claude-worktrees-012-reopen-drafts"


def said(t: float, ident: str, text: str, error: bool = False, **kw) -> dict:
    """A tool's result whose output is `text`."""
    block = {"type": "tool_result", "tool_use_id": ident, "is_error": error, "content": text}
    return user(t, [block], **kw)


def _role_events(
    tmp_path: Path,
    sessions: dict,
    roles: dict,
    models: dict | None = None,
    check: str | None = None,
) -> list:
    folder = tmp_path / "projects" / WORKTREE
    for name, entries in sessions.items():
        _write(folder, name, entries)
    return metrics.read_events([folder], BRANCH, "012", check, roles, models=models)


def _role_line(events: list, role: str = "builder") -> dict:
    back = metrics.parse_trailers("\n".join(metrics.trailers(_summary(events, way="factory"))))
    return back["roles"][role]


ONE_OF_EACH = [
    user(0, "Build it."),
    asst(1, "m1", [tool("Edit", "e1", file_path="/x/a.py", new_string="x", old_string="y")]),
    result(2, "e1"),
    asst(3, "m2", [tool("Bash", "b1", command="uv run --group dev pytest -q 2>&1 | tail")]),
    said(4, "b1", "E   SyntaxError: invalid syntax", error=True),
    asst(5, "m3", [tool("Bash", "b2", command="sed -i '' 's/a/b/' /x/a.py")]),
    result(6, "b2"),
    asst(7, "m4", [tool("Bash", "b3", command="sleep 100", run_in_background=True)]),
    said(8, "b3", "Command running in background",
         toolUseResult={"stdout": "", "stderr": "", "backgroundTaskId": "bt1"}),
    asst(9, "m5", [tool("Read", "r1", file_path="/x/a.py")]),  # interrupted: no result
]  # fmt: skip


def test_a_role_s_behaviours_are_counted_from_its_transcript(tmp_path: Path) -> None:
    """R1, R2: one of each behaviour, each counted once; an interrupted call adds nothing."""
    events = _role_events(tmp_path, {"sess-b": ONE_OF_EACH}, {"sess-b": "builder"})
    line = _role_line(events)
    assert {k: line.get(k) for k in BEHAVIOURS} == dict.fromkeys(BEHAVIOURS, 1)
    assert line["runs"] == 1


def test_a_backgrounded_command_is_known_by_its_result(tmp_path: Path) -> None:
    """R4: `run_in_background`, the harness moving a long command there, and a trailing `&`; a
    plain `a && b` is none of them."""
    entries = [
        user(0, "Build it."),
        asst(1, "m1", [tool("Bash", "b1", command="./check.sh", run_in_background=True)]),
        said(2, "b1", "running", toolUseResult={"stdout": "", "backgroundTaskId": "bt1"}),
        asst(3, "m2", [tool("Bash", "b2", command="uv run pytest -q | tail")]),
        said(4, "b2", "moved", toolUseResult={"stdout": "", "stderr": "", "interrupted": False,
                                              "backgroundTaskId": "bt2",
                                              "timedOutAfterMs": 120000}),
        asst(5, "m3", [tool("Bash", "b3", command="make serve &")]),
        said(6, "b3", ""),
        asst(7, "m4", [tool("Bash", "b4", command="git status && git diff")]),
        said(8, "b4", "", toolUseResult={"stdout": "", "stderr": ""}),
    ]  # fmt: skip
    events = _role_events(tmp_path, {"sess-b": entries}, {"sess-b": "builder"})
    assert _role_line(events)["bg"] == 3


@pytest.mark.parametrize(
    "edit, output, broke",
    [
        (True, "E   SyntaxError: invalid syntax", 1),
        (True, "ModuleNotFoundError: No module named 'drafts'", 1),
        (False, "E   SyntaxError: invalid syntax", 0),
        (True, "E   assert 1 == 2\n1 failed", 0),
    ],
)
def test_a_broken_build_is_a_failed_parse_after_an_edit(tmp_path, edit, output, broke) -> None:
    """R6: a test run that couldn't parse or import, with an edit since the last run; never the
    same output with no edit before it, nor a failing assertion."""
    entries = [user(0, "Build it.")]
    if edit:
        entries += [asst(1, "m1", [tool("Write", "w1", file_path="/x/a.py", content="x")]),
                    result(2, "w1")]  # fmt: skip
    entries += [
        asst(3, "m2", [tool("Bash", "b1", command="python -m pytest -q")]),
        said(4, "b1", output, error=True),
        asst(5, "m3", [tool("Bash", "b2", command="python -m pytest -q")]),  # no edit since
        said(6, "b2", output, error=True),
    ]
    events = _role_events(tmp_path, {"sess-b": entries}, {"sess-b": "builder"})
    line = _role_line(events)
    assert line["broke"] == broke and line["test_runs"] == 2


def test_a_broken_build_is_read_from_text_blocks_too(tmp_path: Path) -> None:
    """R6: a result's output as a list of text blocks, the other shape a transcript holds."""
    entries = [
        user(0, "Build it."),
        asst(1, "m1", [tool("Bash", "b0", command="echo x > a.py")]),
        result(2, "b0"),
        asst(3, "m2", [tool("Bash", "b1", command="pytest")]),
        user(4, [{"type": "tool_result", "tool_use_id": "b1", "is_error": True,
                  "content": [{"type": "text", "text": "ERROR collecting tests/test_a.py"}]}]),
    ]  # fmt: skip
    events = _role_events(tmp_path, {"sess-b": entries}, {"sess-b": "builder"})
    line = _role_line(events)
    assert (line["shell_edits"], line["broke"]) == (1, 1)


def test_a_role_s_tools_are_listed_by_name(tmp_path: Path) -> None:
    """R7: one `Sdlc-Calls` line a role, every name it called with its count, sorted, never
    more than `Sdlc-Tool` counts for the name."""
    builder = [
        user(0, "Build it."),
        asst(1, "m1", [tool("Bash", "b1", command="sed -n '1,5p' /x/a.py"),
                       tool("Bash", "b2", command="sed -i '' 's/a/b/' /x/a.py")]),
        result(2, "b1"), result(2, "b2"),
        asst(3, "m2", [tool("Edit", "e1", file_path="/x/a.py", new_string="x", old_string="y")]),
        result(4, "e1"),
    ]  # fmt: skip
    reviewer = [user(5, "Review it."), asst(6, "m3", [tool("Bash", "b3", command="sed -n 1p a")]),
                result(7, "b3")]  # fmt: skip
    events = _role_events(tmp_path, {"sess-b": builder, "sess-r": reviewer},
                          {"sess-b": "builder", "sess-r": "code"})  # fmt: skip
    lines = metrics.trailers(_summary(events, way="factory"))
    assert "Sdlc-Calls: builder Bash:sed=2 Edit=1" in lines
    assert "Sdlc-Calls: code Bash:sed=1" in lines
    back = metrics.parse_trailers("\n".join(lines))
    for name, row in back["tools"].items():
        assert sum(c.get(name, 0) for c in back["calls"].values()) <= row["calls"]
    assert back["calls"]["builder"] == {"Bash:sed": 2, "Edit": 1}


@pytest.mark.parametrize(
    "models, want",
    [
        ({"sess-b": "model-a"}, "model-a"),
        ({"sess-b": "model-b", "sess-c": "model-a"}, "model-a,model-b"),
        ({"sess-b": "provider:model/x"}, "provider-model-x"),
        ({}, None),
        (None, None),
    ],
)
def test_a_role_s_model_comes_from_its_costs(tmp_path, models, want) -> None:
    """R8: `model=` from the session ids' `costs.jsonl` rows, several joined sorted, every name
    made a word; with no row, left off."""
    entries = lambda t: [user(t, "Build it."), asst(t + 1, f"m{t}")]  # noqa: E731
    events = _role_events(tmp_path, {"sess-b": entries(0), "sess-c": entries(10)},
                          {"sess-b": "builder", "sess-c": "builder"}, models)  # fmt: skip
    lines = metrics.trailers(_summary(events, way="factory"))
    [role] = [ln for ln in lines if ln.startswith("Sdlc-Role: builder")]
    back = metrics.parse_trailers(role)["roles"]["builder"]
    assert back.get("model") == want and back["runs"] == 2
    assert ("model=" in role) is (want is not None)


def test_a_behaviour_count_that_fails_drops_only_its_fields(tmp_path, monkeypatch) -> None:
    """R10: counting that raises drops that role's counts, `model=` and `Sdlc-Calls`, says
    `behaviour=failed`, and leaves every other line as it was."""
    sessions, roles = {"sess-b": ONE_OF_EACH}, {"sess-b": "builder"}
    models = {"sess-b": "model-a"}
    good = metrics.trailers(
        _summary(_role_events(tmp_path, sessions, roles, models), way="factory")
    )

    def broken(*_):
        raise RuntimeError("a transcript shape nobody planned for")

    monkeypatch.setattr(metrics, "_behaviour", broken)
    s = _summary(_role_events(tmp_path, sessions, roles, models), way="factory")
    bad = metrics.trailers(s)
    assert s["coverage"].endswith(" behaviour=failed")
    keep = ("Sdlc-Totals", "Sdlc-Stage", "Sdlc-Tool")
    assert [ln for ln in bad if ln.startswith(keep)] == [ln for ln in good if ln.startswith(keep)]
    [role] = [ln for ln in bad if ln.startswith("Sdlc-Role:")]
    assert role.startswith("Sdlc-Role: builder runs=1 agent=")
    assert not any(f"{k}=" in role for k in (*BEHAVIOURS, "model"))
    assert not any(ln.startswith("Sdlc-Calls:") for ln in bad)


def test_behaviour_trailers_carry_no_text(tmp_path: Path) -> None:
    """R11: numbers and names only: no command, path or output reaches a role's lines."""
    marker = "zzmarker"
    entries = [
        user(0, f"Build {marker}."),
        asst(1, "m1", [tool("Edit", "e1", file_path=f"~/{marker}/a.py", new_string=marker)]),
        said(2, "e1", f"edited {marker}"),
        asst(3, "m2", [tool("Bash", "b1", command=f"pytest tests/{marker} -k '{marker} x'")]),
        said(4, "b1", f"SyntaxError in /{marker}/a.py", error=True),
        asst(5, "m3", [tool("Bash", "b2", command=f"echo {marker} > ~/{marker}.txt &")]),
        said(6, "b2", marker, toolUseResult={"backgroundTaskId": marker}),
    ]  # fmt: skip
    events = _role_events(tmp_path, {"sess-b": entries}, {"sess-b": "builder"},
                          {"sess-b": "m x/y~z"})  # fmt: skip
    lines = [ln for ln in metrics.trailers(_summary(events, way="factory"))
             if ln.startswith(("Sdlc-Role:", "Sdlc-Calls:"))]  # fmt: skip
    assert len(lines) == 2
    for line in lines:
        assert marker not in line
        assert "/" not in line and "~" not in line
        for word in line.split(": ", 1)[1].split()[1:]:
            assert "=" in word, word
    role = next(ln for ln in lines if ln.startswith("Sdlc-Role:"))
    assert "model=m-x-y-z" in role, "the model is a name, made a word"


def test_a_close_from_before_behaviours_parses_as_before() -> None:
    """R12: an old body reads exactly as it did: no `calls`, no new role fields."""
    old = (
        "Sdlc-Mode: factory\n"
        "Sdlc-Coverage: transcripts=3 stages=build,ship\n"
        "Sdlc-Totals: elapsed=90 agent=40 tools=12 words=5 out=7\n"
        "Sdlc-Role: builder runs=1 agent=30 in=1 cache_create=2 cache_read=3 out=4\n"
        "Sdlc-Role: Explore runs=2 agent=5 in=1 cache_create=0 cache_read=0 out=1\n"
        "Sdlc-Tool: Bash:sed calls=3 errors=0 build=3\n"
    )
    assert metrics.parse_trailers(old) == {
        "mode": "factory",
        "coverage": "transcripts=3 stages=build,ship",
        "stages": {},
        "blocked": {},
        "totals": {"elapsed": 90, "agent": 40, "tools": 12, "words": 5, "out": 7},
        "roles": {
            "builder": {"runs": 1, "agent": 30, "in": 1, "cache_create": 2, "cache_read": 3,
                        "out": 4},
            "Explore": {"runs": 2, "agent": 5, "in": 1, "cache_create": 0, "cache_read": 0,
                        "out": 1},
        },
        "tools": {"Bash:sed": {"calls": 3, "errors": 0, "build": 3}},
    }  # fmt: skip


# ---------------------------------------------------------------- lead time (162)


def _t(minutes: float) -> datetime:
    return T0 + timedelta(minutes=minutes)


@pytest.mark.portable
def test_lead_time_parts_sum_to_lead_and_overlapping_agents_count_once() -> None:
    """162 R4: opened 0, first 10, ready 100, landing 130, closed 150. A builder 10 to 30, two
    reviewers overlapping in 40 to 70 and a run past `ready` cut at it make 60 minutes of
    agents, never 70."""
    intervals = [(_t(10), _t(30)), (_t(40), _t(70)), (_t(50), _t(60)), (_t(90), _t(120))]
    got = metrics.lead_time(_t(0), _t(150), _t(10), _t(100), _t(130), intervals)
    assert got == {"lead": 9000, "queued": 600, "agents": 3600, "idle": 1800,
                   "ready_wait": 1800, "landing": 1200}  # fmt: skip
    assert sum(v for k, v in got.items() if k != "lead") == got["lead"]


@pytest.mark.portable
def test_without_a_landing_ready_waits_until_close() -> None:
    got = metrics.lead_time(_t(0), _t(60), _t(5), _t(20), None, [(_t(5), _t(15))])
    assert got == {"lead": 3600, "queued": 300, "agents": 600, "idle": 300, "ready_wait": 2400}


@pytest.mark.portable
@pytest.mark.parametrize(
    "marks, kept",
    [
        ((None, _t(20), None), {"lead", "ready_wait"}),  # no first: no queued, agents or idle
        ((_t(5), None, _t(50)), {"lead", "landing"}),  # no ready
        ((_t(30), _t(20), None), {"lead"}),  # ready before first
        ((_t(5), _t(20), _t(70)), {"lead"}),  # landing after closed
        ((_t(5), _t(70), None), {"lead"}),  # ready after closed
        ((_t(5), _t(40), _t(30)), {"lead"}),  # landing before ready
    ],
)
def test_lead_time_leaves_out_what_it_cant_know(marks, kept) -> None:
    """162 R5: a part it can't know is absent, never 0."""
    first, ready, landing = marks
    got = metrics.lead_time(_t(0), _t(60), first, ready, landing, [(_t(5), _t(10))])
    assert set(got) == kept and got["lead"] == 3600


@pytest.mark.portable
def test_lead_time_with_opened_after_closed_is_nothing() -> None:
    assert metrics.lead_time(_t(10), _t(5), None, None, None, []) == {}


@pytest.mark.portable
def test_agents_before_opened_are_clipped_to_it() -> None:
    """A first event before `new` (the session that ran it) starts the clock at `opened`."""
    got = metrics.lead_time(_t(10), _t(60), _t(0), _t(30), None, [(_t(0), _t(20))])
    assert got == {"lead": 3000, "queued": 0, "agents": 600, "idle": 600, "ready_wait": 1800}


@pytest.mark.portable
def test_the_lead_line_round_trips_with_minutes_and_a_source_word() -> None:
    """162 R6: whole minutes and a source word, read back as `metrics["lead"]`."""
    parts = {"lead": 9000, "queued": 600, "agents": 3610, "idle": 1790,
             "ready_wait": 1800, "landing": 1200}  # fmt: skip
    line = metrics.lead_trailer(parts, "runs")
    assert line == (
        "Sdlc-Lead: lead=150 queued=10 agents=60 idle=30 ready_wait=30 landing=20 source=runs"
    )
    assert metrics.parse_trailers(line)["lead"] == {
        "lead": 150, "queued": 10, "agents": 60, "idle": 30, "ready_wait": 30, "landing": 20,
        "source": "runs",
    }  # fmt: skip
    short = metrics.lead_trailer({"lead": 600, "ready_wait": 120}, "git")
    assert short == "Sdlc-Lead: lead=10 ready_wait=2 source=git"
    assert "Sdlc-Lead" in metrics.__doc__ and "lead_time(" in metrics.__doc__


# ---------------------------------------------------------------- what ran underneath (170)


def _ran(entry: dict, version: str | None, model: str | None = None) -> dict:
    """An entry as Claude Code writes it: `version` on every entry, `message.model` on an
    assistant's. The values are made up; the shape is a real transcript's."""
    if version is not None:
        entry["version"] = version
    if model is not None:
        entry["message"]["model"] = model
    return entry


def test_runtime_is_read_from_each_entrys_version_and_model(tmp_path: Path) -> None:
    """170 R1: each distinct version and model the change's entries carry, from the main session,
    a factory agent's session and a sub-agent's transcript; never an empty value, the harness's
    `<synthetic>`, or another branch's session."""
    folder = tmp_path / "projects" / WORKTREE
    _write(folder, "main", [
        _ran(cmd(0, "sdlc-factory:build", "12"), "9.1.10"),
        _ran(asst(1, "m1", [tool("Agent", "a1")]), "9.1.10", "model-main"),
        _ran(asst(2, "m2"), "9.1.11", "<synthetic>"),
        _ran(asst(3, "m3"), "", ""),
        _ran(asst(4, "m4", branch=OTHER), "9.9.9", "model-other"),
    ])  # fmt: skip
    sub = folder / "main" / "subagents"
    _write(sub, "agent-a1", [_ran(asst(5, "s1"), "9.1.11", "model-sub")])
    (sub / "agent-a1.meta.json").write_text(json.dumps({"agentType": "Explore", "toolUseId": "a1"}))
    _write(folder, "sess-b", [_ran(user(6, "Build it."), "9.1.12"),
                              _ran(asst(7, "b1"), "9.1.12", "model-builder")])  # fmt: skip
    _write(folder, "other", [_ran(asst(8, "o1", branch=OTHER), "9.9.8", "model-leak")])
    events = metrics.read_events([folder], BRANCH, "012", None, {"sess-b": "builder"})
    ran = [e for e in events if e["kind"] == "runtime"]
    claude = sorted({e["claude"] for e in ran if "claude" in e})
    models = sorted({e["model"] for e in ran if "model" in e})
    assert claude == ["9.1.10", "9.1.11", "9.1.12"]
    assert models == ["model-builder", "model-main", "model-sub"]
    assert all(set(e) <= {"ts", "kind", "claude", "model"} for e in ran)
    # One event a value a run: the main session's 9.1.10 is on two entries.
    assert sum(e.get("claude") == "9.1.10" for e in ran) == 1
    # The kind moves no clock: the summary is the same with and without it.
    plain = [e for e in events if e["kind"] != "runtime"]
    assert metrics.trailers(_summary(events, way="factory")) == metrics.trailers(
        _summary(plain, way="factory")
    )


@pytest.mark.portable
def test_runtime_values_are_capped() -> None:
    """174 R11: an odd transcript value makes no very long trailer line: each value is at most 64
    characters, and the line still reads back."""
    long = "v" * 200
    line = metrics.runtime_trailer([{"ts": T0, "kind": "runtime", "claude": long}], [long], "1.0")
    back = metrics.parse_trailers(line)["runtime"]
    assert back["claude"] == "v" * 64 and back["models"] == "v" * 64, back
    assert back["plugin"] == "1.0"


def test_runtime_trailer_round_trips() -> None:
    """170 R2: one line, every value sorted, deduplicated and a word; read back as text."""
    at = T0
    events = [
        {"ts": at, "kind": "runtime", "claude": "2.1.10"},
        {"ts": at, "kind": "runtime", "claude": "2.1.9 made/x"},
        {"ts": at, "kind": "runtime", "claude": "2.1.10"},
        {"ts": at, "kind": "runtime", "model": "model~b"},
        {"ts": at, "kind": "tokens", "in": 1},
    ]
    line = metrics.runtime_trailer(events, ["model-a", "model-a", "provider:model/x"], "1.9.0")
    assert line == (
        "Sdlc-Runtime: claude=2.1.10,2.1.9-made-x models=model-a,model-b,provider-model-x "
        "plugin=1.9.0"
    )
    back = metrics.parse_trailers(line)["runtime"]
    assert back == {"claude": "2.1.10,2.1.9-made-x", "models": "model-a,model-b,provider-model-x",
                    "plugin": "1.9.0"}  # fmt: skip
    one = metrics.parse_trailers(metrics.runtime_trailer([], [], "2.1.10"))["runtime"]
    assert one == {"plugin": "2.1.10"} and isinstance(one["plugin"], str)
    rest = line.removeprefix("Sdlc-Runtime: ")
    assert not any(c in rest for c in "/~") and rest.count(" ") == 2
    assert metrics.runtime_trailer([], [], None) is None
    assert metrics.runtime_trailer([], ["", "  "], "") is None
    assert "runtime_trailer(" in metrics.__doc__ and "runtime{" in metrics.__doc__
