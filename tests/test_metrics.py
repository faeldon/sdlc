"""What a change cost, read from fixture transcripts: which entries are the change's, its stages,
the four clocks, stops against the gates, tokens, and the trailers close writes.

Every fixture is a transcript built here under a made-up path, the shape Claude Code writes (an
entry per line, `gitBranch` and `timestamp` on each); nothing reads this machine's own.
"""

from __future__ import annotations

import importlib.util
import json
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


def asst(t: float, mid: str, tools: list[dict] = (), branch: str = BRANCH, tokens: int = 10):
    usage = {"input_tokens": 1, "cache_creation_input_tokens": tokens,
             "cache_read_input_tokens": tokens * 100, "output_tokens": tokens}  # fmt: skip
    content = [{"type": "text", "text": SENTINEL}, *tools]
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


@pytest.mark.parametrize(
    "path, kind",
    [(f"work/{BRANCH}/spec.md", "spec"), (f"/abs/work/{BRANCH}/notes.md", "notes"),
     (f"work/{BRANCH}/build/round-1.md", "artifact"), ("tests/test_x.py", "test"),
     ("src/x.test.ts", "test"), ("README.md", "doc"), ("work/ideas.md", "doc"),
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


def test_the_factorys_build_gate_comes_first_and_its_decisions_are_questions(tmp_path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc-factory:build", "12"),
        turn(1, 1), user(2, "yes"),  # the run's approval
        turn(30, 28), user(31, "option b"),  # a blocking decision
    ])  # fmt: skip
    s = _summary(events, way="factory")
    build = s["stages"]["build"]
    assert (build["gate"], build["question"], build["extra"]) == (1, 1, 0)
    assert s["totals"]["required"] == 5


@pytest.mark.parametrize(
    "text, reply",
    [("yes", "approve"), ("Yes, go ahead", "approve"), ("lgtm", "approve"),
     ("revise R3 first", "revise"), ("no, change the tier", "revise"),
     ("what does this do?", "other")],
)  # fmt: skip
def test_a_reply_is_kept_as_its_class_only(text: str, reply: str) -> None:
    assert metrics._reply(text) == reply


def test_permission_prompts_and_gate_runs_are_counted(tmp_path: Path) -> None:
    events = _events(tmp_path, [
        cmd(0, "sdlc:ship"),
        asst(1, "m1", [tool("Bash", "c1", command="./check.sh 2>&1 | tail -3")]),
        result(2, "c1", error=True, permissionDecision={"source": "user_temporary"}),
        asst(3, "m2", [tool("Bash", "c2", command="./check.sh")]),
        result(4, "c2"),
        asst(5, "m3", [tool("Bash", "c3", command="git status")]),
        result(6, "c3", permissionDecision={"source": "config"}),
    ])  # fmt: skip
    ship = _summary(events)["stages"]["ship"]
    assert (ship["checks"], ship["checks_failed"], ship["permission"]) == (2, 1, 1)


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
    "way, tier, plan, required",
    [("manual", 2, False, 5), ("manual", 1, False, 3), ("manual", 1, True, 4),
     ("factory", 2, False, 5)],
)  # fmt: skip
def test_the_gates_each_way_of_running_requires(tmp_path, way, tier, plan, required) -> None:
    entries = [cmd(0, "sdlc:intent")]
    if plan:
        entries.append(asst(1, "m1", [tool("ExitPlanMode", "x1")]))
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
    assert back["totals"] == {"elapsed": 180, "required": 5, "target": 6, "allowance": 1}
    assert back["mode"] == "factory"


def test_a_commit_without_trailers_reads_as_none() -> None:
    assert metrics.parse_trailers("Close 001-x\n\nIts artifacts are in abc.") is None
    assert metrics.parse_trailers(None) is None


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
    for name in ("VERDICT_RE", "DECISION_RE", "CHANGE_RE", "LEDGER_RE"):
        assert getattr(sdlc, f"FACTORY_{name}").pattern == getattr(factory, name).pattern, name
