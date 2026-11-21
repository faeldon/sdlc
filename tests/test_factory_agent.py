"""The supervisor and `agent`: where a change is found, each role's model, a run's stream and
figures, mends, the spec draft and `write-spec`, and what each run was for.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Each test builds a scratch repo
on a change branch with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest
from factory_helpers import (
    FACTORY_PY,
    FULL,
    NAME,
    _build_report,
    _change,
    _files,
    _from_main,
    _git,
    _on_main,
    _report,
    _review,
    _round,
    _run,
    _verdicts,
    factory,
    sdlc,
)

# ---------------------------------------------------------------- the supervisor


def test_a_change_is_found_in_its_worktree_from_the_main_checkout(tmp_path, capsys) -> None:
    root, tree = _from_main(tmp_path)
    assert factory.change_root(root, "8").resolve() == tree.resolve()
    assert factory.change_root(tree, "008") == tree, "already in it"
    assert factory.change_root(root, "9") == root, "no worktree: left for find_change to refuse"
    code, out = _run(capsys, factory.cmd_start, factory.change_root(root, "008"), "008", "build")
    assert code == 0 and Path(out["worktree"]).resolve() == tree.resolve()


def test_the_worktree_lister_is_sdlc_s_own(tmp_path) -> None:
    root, _ = _from_main(tmp_path)
    assert factory.worktrees(root) == sdlc.worktrees(root)


def test_a_tier_two_at_plan_starts_with_a_spec_draft_and_shows_its_models(tmp_path, capsys):
    root = _change(tmp_path, tier=2, stage="plan")
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 0 and out["spec"] is True
    light = out["models_at"]["light"]
    assert light["code"] == "sonnet", "a Tier 2's reviewers are sonnet at either depth"
    assert (light["security"], light["builder"], light["approver"]) == ("opus",) * 3
    code, out = _run(capsys, factory.cmd_start, _change(tmp_path / "b", tier=2), "008", "build")
    assert out["spec"] is False, "a spec is already approved at stage: design"


@pytest.mark.parametrize(
    "role, tier, level, model",
    [("code", 1, "light", "sonnet"), ("test", 1, "full", "sonnet"),
     ("behaviour", 2, "light", "sonnet"), ("security", 1, "light", "opus"),
     ("builder", 1, "light", "opus"), ("approver", 1, "light", "opus"),
     ("arbiter", 1, "light", "sonnet"), ("spec-writer", 2, "full", "opus")],
)  # fmt: skip
def test_each_role_runs_on_its_model(role, tier, level, model) -> None:
    """136 R2: the scaled reviewers run on sonnet at either depth and tier, haiku nowhere unless
    `[models]` names it; what builds, decides or hunts exploits is opus."""
    cfg, _ = factory.load_config(Path("/nonexistent"))
    assert factory.model_for(role, cfg, tier, level) == model
    assert "haiku" not in {factory.model_for(role, cfg, t, d) for t in (1, 2, None)
                           for d in ("light", "full")}  # fmt: skip
    cfg["models"] = {role: "fable"}
    assert factory.model_for(role, cfg, tier, level) == "fable", "factory.models wins"


def test_the_resolver_has_a_model_of_its_own(tmp_path, capsys) -> None:
    """149 R7: the resolver runs on sonnet at either depth and tier unless `[models] resolver`
    names another, which `start`'s `models_at` shows and no warning calls unknown; the builder's
    model never reaches it."""
    cfg, _ = factory.load_config(Path("/nonexistent"))
    assert {factory.model_for("resolver", cfg, t, d) for t in (1, 2, None)
            for d in ("light", "full")} == {"sonnet"}  # fmt: skip
    cfg["models"] = {"builder": "haiku"}
    assert factory.model_for("resolver", cfg, 1, "full") == "sonnet", "never the builder's"
    root, tree = _from_main(tmp_path)
    _, out = _run(capsys, factory.cmd_start, tree, "008", "build")
    assert {out["models_at"][d]["resolver"] for d in ("light", "full")} == {"sonnet"}
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text(
        '[models]\nresolver = "opus"\nbuilder = "haiku"\n', encoding="utf-8"
    )
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "models")
    cfg, warnings = factory.load_config(tree)
    assert not any("unknown role" in w for w in warnings), warnings
    assert factory.model_for("resolver", cfg, 1, "light") == "opus"
    _, out = _run(capsys, factory.cmd_start, tree, "008", "build")
    assert {out["models_at"][d]["resolver"] for d in ("light", "full")} == {"opus"}


def test_the_agents_mode_is_the_base_branchs(tmp_path) -> None:
    root = _change(tmp_path)
    _git(root, "checkout", "-q", "main")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text('mode = "acceptEdits"\n', encoding="utf-8")
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "mode")
    _git(root, "checkout", "-q", NAME)
    (root / ".sdlc" / "factory.toml").write_text('mode = "bypassPermissions"\n', encoding="utf-8")
    cfg, warnings = factory.load_config(root)
    assert cfg["mode"] == "acceptEdits", "a change can't widen what its own agents may do"
    assert any("read from the base branch" in w for w in warnings)
    (root / ".sdlc" / "factory.toml").write_text('mode = "acceptEdits"\n', encoding="utf-8")
    assert factory.load_config(root)[1] == []


def test_models_are_the_base_branch_s_even_for_an_older_worktree(tmp_path, capsys, claude) -> None:
    """Bug 2026-11-18-41: a `[models]` entry committed on the base branch after a change's
    worktree was made reaches that change's `start` and its agents; one in the change's own
    checkout changes nothing, and says so."""
    root, tree = _from_main(tmp_path)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text(
        '[models]\nbuilder = "fable"\ndesigner = "opus"\n', encoding="utf-8"
    )
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "models")
    cfg, warnings = factory.load_config(tree)
    assert any("unknown role 'designer'" in w for w in warnings), "the base's entries are checked"
    assert not (tree / ".sdlc" / "factory.toml").exists(), "the worktree predates it"
    _, out = _run(capsys, factory.cmd_start, tree, "008", "build")
    assert {out["models_at"][d]["builder"] for d in ("light", "full")} == {"fable"}
    code, out = _run(capsys, factory.cmd_agent, tree, "008", "build", None, None)
    assert code == 0 and out["model"] == "fable", out
    argv = claude()[-1]["argv"]
    assert argv[argv.index("--model") + 1] == "fable"

    (tree / ".sdlc" / "factory.toml").write_text(
        '[models]\nbuilder = "haiku"\ncode = "haiku"\n', encoding="utf-8"
    )
    cfg, warnings = factory.load_config(tree)
    assert cfg["models"] == {"builder": "fable"}, "a change can't pick its own agents' models"
    assert any("models is read from the base branch" in w for w in warnings), warnings
    (tree / ".sdlc" / "factory.toml").write_text(
        '[models]\nbuilder = "fable"\ndesigner = "opus"\n', encoding="utf-8"
    )
    assert not [w for w in factory.load_config(tree)[1] if "read from the base branch" in w]


@pytest.mark.parametrize("bad", ["0", "true", '"two"', "1.5"])
def test_gate_jobs_is_read_from_the_base_branch_and_checked(tmp_path, capsys, bad) -> None:
    """101 R7: how many gates run at once is the base branch's to set, never the change's own,
    and a value that isn't a whole number of 1 or more is a warning that leaves 1."""
    root = _change(tmp_path)
    _on_main(root, "gate_jobs = 3\n")
    (root / ".sdlc" / "factory.toml").write_text("gate_jobs = 8\n", encoding="utf-8")
    cfg, warnings = factory.load_config(root)
    assert cfg["gate_jobs"] == 3, "a change can't give itself more gates"
    assert any("gate_jobs is read from the base branch" in w for w in warnings), warnings
    _, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert out["gate_jobs"] == 3
    (root / ".sdlc" / "factory.toml").write_text("gate_jobs = 3\n", encoding="utf-8")
    assert factory.load_config(root)[1] == []
    (root / ".sdlc" / "factory.toml").unlink()
    _on_main(root, f"gate_jobs = {bad}\n")
    cfg, warnings = factory.load_config(root)
    assert cfg["gate_jobs"] == 1 and any("gate_jobs must be" in w for w in warnings), warnings


# ---------------------------------------------------------------- an agent's run and its figures


def _figures(cost: float | None, tokens_in: int = 10, tokens_out: int = 5) -> str:
    """A result's figures as Claude Code reports them: on a resume, `total_cost_usd` is the
    session's total so far, and `usage` the run's own."""
    usage = {"input_tokens": tokens_in, "output_tokens": tokens_out,
             "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000}  # fmt: skip
    figures = {"duration_ms": 1200, "num_turns": 3, "usage": usage}
    return json.dumps(figures if cost is None else {**figures, "total_cost_usd": cost})


def test_each_agent_run_records_its_figures_and_a_resume_is_not_counted_twice(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    root, tree = _from_main(tmp_path)
    worktree = factory.change_root(root, "008")
    folder = tree / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(0.5))
    code, out = _run(capsys, factory.cmd_agent, worktree, "008", "build", None, None)
    assert code == 0, out
    session = out["session"]
    rows = [json.loads(x) for x in (folder / "runs" / "costs.jsonl").read_text().splitlines()]
    # 162 R9: when the run began and ended, around the `claude` call, for close's lead time.
    started, ended = rows[0].pop("started"), rows[0].pop("ended")
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    assert datetime.strptime(started, fmt) <= datetime.strptime(ended, fmt)
    assert rows == [{
        "session": session, "role": "builder", "model": "opus", "cost_usd": 0.5,
        "duration_ms": 1200, "turns": 3, "in": 10, "out": 5, "cache_create": 100,
        "cache_read": 1000, "purpose": "build", "task": "build", "round": 1,
    }]  # fmt: skip
    sessions = (folder / "runs" / "builder.sessions").read_text()
    assert sessions == session + "\n", "one id a line, as measuring reads it"

    # The mend resumes the builder, whose total so far is 0.75: 0.25 more, never 1.25. It mends
    # only a report `verdicts` names: here one without its evidence.
    (folder / "build" / "round-1.md").write_text("Built, no evidence.\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(0.75, tokens_in=20))
    code, out = _run(capsys, factory.cmd_agent, worktree, "008", "mend", "builder", None)
    assert code == 0 and out["session"] == session
    cost = factory.run_cost(folder)
    assert cost["usd"] == 0.75 and cost["by_role"] == {"builder": 0.75}
    assert cost["by_model"] == {"opus": 0.75} and cost["runs"] == 2 and cost["unknown"] == 0
    assert cost["tokens"] == {"in": 30, "out": 10, "cache_create": 200, "cache_read": 2000}


def test_a_run_reporting_no_cost_or_failing_still_counts(tmp_path, capsys, claude, monkeypatch):
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(None))
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0 and (folder / "build" / "round-1.md").exists(), "a missing cost stops nothing"
    cost = factory.run_cost(folder)
    assert cost["usd"] == 0.0 and cost["unknown"] == 1 and cost["tokens"]["in"] == 10

    # A failed session files no reply, but what it spent is still recorded.
    (folder / "build" / "round-1.md").unlink()
    monkeypatch.setenv("FAKE_CLAUDE_EXIT", "1")
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(0.2))
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 1 and not (folder / "build" / "round-1.md").exists()
    assert factory.run_cost(folder)["usd"] == 0.2

    # A line that doesn't parse is skipped and counted, never raised.
    with (folder / "runs" / "costs.jsonl").open("a", encoding="utf-8") as f:
        f.write("not json\n")
    assert factory.run_cost(folder)["unknown"] == 2


class _Done:
    """What `subprocess.run` returns, for `_claude()` read without a process."""

    def __init__(self, stdout: str, returncode: int = 0, stderr: str = "") -> None:
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr


def _stream(monkeypatch, stdout: str, returncode: int = 0) -> None:
    monkeypatch.setattr(factory.subprocess, "run", lambda *a, **k: _Done(stdout, returncode))


def _event(kind: str, text: str | None = None, **fields) -> str:
    if kind == "assistant":
        message = {"role": "assistant", "content": [{"type": "text", "text": text}]}
        return json.dumps({"type": "assistant", "message": message})
    return json.dumps({"type": "result", "is_error": False, "result": text, **fields})


@pytest.mark.portable
def test_claude_returns_every_reply_in_order(tmp_path, monkeypatch) -> None:
    """140 R1: each assistant event's text and each result's, a result that repeats the reply
    before it counted once, in the order the session gave them."""
    lines = [
        json.dumps({"type": "system", "subtype": "init"}),
        _event("assistant", "VERDICT: PASS\n\nFine."),
        _event("result", "VERDICT: PASS\n\nFine."),
        "not json",
        "[1, 2]",
        _event("assistant", "My verdict stands."),
        _event("result", "My verdict stands."),
    ]
    _stream(monkeypatch, "\n".join(lines) + "\n")
    code, replies, problem, _ = factory._claude(["claude"], tmp_path)
    assert (code, problem) == (0, None)
    assert replies == ["VERDICT: PASS\n\nFine.", "My verdict stands."]
    # A result that differs from its assistant text is a reply of its own, after it.
    _stream(monkeypatch, "\n".join([_event("assistant", "one"), _event("result", "one\ntwo")]))
    assert factory._claude(["claude"], tmp_path)[1] == ["one", "one\ntwo"]


@pytest.mark.portable
def test_a_recorded_stream_with_two_replies_reads_both(tmp_path, monkeypatch) -> None:
    """140 R3: a real session's stream (`tests/fixtures/stream-two-replies.jsonl`): a reviewer
    that started a background task, replied with its verdict, and was woken by the task's notice
    to reply again. The verdict is among the replies, and it is the one a reviewer's holds."""
    text = (Path(__file__).parent / "fixtures" / "stream-two-replies.jsonl").read_text("utf-8")
    _stream(monkeypatch, text)
    code, replies, problem, figures = factory._claude(["claude"], tmp_path)
    assert (code, problem) == (0, None)
    assert replies[0] == "VERDICT: PASS\nThe draft reopens.", replies
    assert len(replies) == 2 and replies[1].startswith("The background command finished")
    assert [r for r in replies if factory.holds("code", r)] == [replies[0]]
    assert figures["cost_usd"] == 0.00477998, "the session's total, the last result's"
    assert figures["turns"] == 3 and figures["duration_ms"] == 2322 + 954


@pytest.mark.portable
def test_a_stream_without_a_result_or_with_an_error_fails(tmp_path, monkeypatch) -> None:
    """140 R4: no result event, an error on the last one, no reply's text, or a non-zero exit is
    a failed session: no reply, only its figures."""
    figures = {"total_cost_usd": 0.1, "num_turns": 1}
    cases = {
        "no result": ([_event("assistant", "VERDICT: PASS")], 0),
        "last result errs": (
            [
                _event("result", "VERDICT: PASS"),
                json.dumps({"type": "result", "is_error": True, "result": "", **figures}),
            ],
            0,
        ),
        "no text": ([_event("result", "  ", **figures)], 0),
        "exit": ([_event("result", "VERDICT: PASS", **figures)], 2),
        "nothing": (["garbage"], 0),
    }
    for name, (lines, exit_code) in cases.items():
        _stream(monkeypatch, "\n".join(lines) + "\n", exit_code)
        code, replies, problem, got = factory._claude(["claude"], tmp_path)
        assert code != 0 and replies == [] and problem, name
        if name in ("last result errs", "exit"):
            assert got and got["cost_usd"] == 0.1, name


@pytest.mark.portable
def test_figures_sum_a_session_s_turns_and_take_its_last_cost() -> None:
    """140 R5: `total_cost_usd` is the session's total so far, so the last result's; each
    result's usage, duration and turns are its own turn's, so they are summed."""
    usage = {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 100,
             "cache_read_input_tokens": 1000}  # fmt: skip
    first = {"total_cost_usd": 0.4, "duration_ms": 100, "num_turns": 2, "usage": usage}
    second = {"total_cost_usd": 0.5, "duration_ms": 50, "num_turns": 1, "usage": usage}
    figures = factory._figures([first, second])
    assert figures == {"cost_usd": 0.5, "duration_ms": 150, "turns": 3, "in": 20, "out": 10,
                       "cache_create": 200, "cache_read": 2000}  # fmt: skip
    assert factory._figures([{"result": "x"}]) is None
    one = factory._figures([{"usage": {"input_tokens": 3}}])
    assert one["in"] == 3 and one["cost_usd"] is None and one["out"] is None


def test_a_second_reply_never_replaces_the_verdict(tmp_path, capsys, claude, monkeypatch):
    """140 R2, bug 2026-11-18-26: a reviewer that replies with its verdict, then is woken by a
    background task's notice and replies again, has its verdict filed, never the note."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1)
    for role in FULL[1:]:
        _review(root, 1, role, "VERDICT: PASS")
    verdict = "VERDICT: PASS\n\n## Notes\n\nEach requirement has its code."
    monkeypatch.setenv("FAKE_CLAUDE_REPLIES", json.dumps([verdict, "My verdict stands."]))
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
    assert code == 0, out
    filed = (folder / "reviews" / "round-1" / "code.md").read_text(encoding="utf-8")
    assert filed == verdict + "\n"
    assert _verdicts(root, capsys)["next"] == "approve"

    # The last reply that holds one wins: a verdict the reviewer changed on waking is its latest.
    changed = "VERDICT: CHANGES\n- CHANGE: src/drafts.py:3: the check I waited on failed"
    monkeypatch.setenv("FAKE_CLAUDE_REPLIES", json.dumps([verdict, changed, "Done."]))
    (folder / "reviews" / "round-1" / "code.md").unlink()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
    assert code == 0, out
    assert (
        (folder / "reviews" / "round-1" / "code.md")
        .read_text(encoding="utf-8")
        .startswith("VERDICT: CHANGES")
    )

    # No reply holds a verdict: the last is filed, and it stops the run as it would have.
    monkeypatch.setenv("FAKE_CLAUDE_REPLIES", json.dumps(["Reading the diff.", "I ran out."]))
    (folder / "reviews" / "round-1" / "code.md").unlink()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
    assert code == 0, out
    filed = (folder / "reviews" / "round-1" / "code.md").read_text(encoding="utf-8")
    assert filed == "I ran out.\n"
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"]) == ("stop", "rerun"), out


@pytest.mark.portable
def test_holds_picks_each_role_s_answer() -> None:
    """140 R2: what each role's reply must hold for `agent` to file it over a later one."""
    assert factory.holds("behaviour", "Ran it.\nVERDICT: PASS")
    assert not factory.holds("code", "My verdict stands: PASS.")
    assert factory.holds("approver", "DECISION: READY") and not factory.holds("approver", "Ready.")
    assert factory.holds("arbiter", "- KEPT: code: C1: real")
    assert factory.holds("arbiter", "- DROPPED: code: C1: x — not there")
    assert not factory.holds("arbiter", "Nothing to keep.")
    assert factory.holds("builder", "Built.\n\n## Evidence\n$ ./check.sh\nexit: 0")
    assert not factory.holds("builder", "Built.")
    assert factory.holds("spec-writer", "---\nid: 008\n---\n# 008")
    assert not factory.holds("spec-writer", "Here is my thinking.")


@pytest.mark.portable
def test_no_reviewer_runs_the_gate_or_waits_in_the_background() -> None:
    """140 R9: every reviewer and the arbiter is told the gate is the script's, where its record
    is, and to start nothing in the background, whose notice wakes the session after its reply;
    none is told to run the gate."""
    agents = Path(__file__).parents[1] / "plugins" / "factory" / "agents"
    files = [*sorted(agents.glob("reviewer-*.md")), agents / "arbiter.md"]
    assert len(files) == len(factory.REVIEWERS) + 1
    runs_gate = re.compile(r"(?<!never )\brun (?:the repo's )?(?:tests or )?(?:the )?gate\b", re.I)
    for path in files:
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "`[commands] check`" in text and "gate.md" in text, path.name
        assert "background" in text, path.name
        assert not runs_gate.search(text), (path.name, runs_gate.search(text))
        assert "Run the repo's tests" not in text, path.name


OPENING_CASES = json.loads(
    (Path(__file__).parent / "fixtures" / "opening-cases.json").read_text(encoding="utf-8")
)


@pytest.mark.portable
@pytest.mark.parametrize("case", OPENING_CASES, ids=[c["name"] for c in OPENING_CASES])
def test_opening_reads_the_answer_line(case) -> None:
    """140 R6: the first line when it matches; else the first matching line when every matching
    line names the same answer; else none. `board.py` and `sdlc.py` pin their copies to this
    same table."""
    regex = {"verdict": factory.VERDICT_RE, "decision": factory.DECISION_RE}[case["kind"]]
    found = factory.opening(case["lines"], regex)
    got = [found[0], found[1].group(1)] if found else None
    assert got == case["answer"]


def test_a_verdict_after_prose_is_read(tmp_path, capsys) -> None:
    """140 R6: `preamble()`'s cases as they stood, each read as its answer where it stands, the
    prose kept in the file, with no mend; a reply with no verdict is still a stop."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    reply = folder / "reviews" / "round-1" / "code.md"
    text = "Both kept changes are in the code.\n\nVERDICT: PASS\n"
    reply.write_text(text, encoding="utf-8")
    out = _verdicts(root, capsys)
    assert out["next"] == "approve" and not out["problems"], out
    assert reply.read_text(encoding="utf-8") == text, "read in place, never rewritten"
    reply.write_text("Status: reviewed\nVERDICT: CHANGES\n- CHANGE: code fix 1\n", "utf-8")
    out = _verdicts(root, capsys)
    assert out["next"] == "arbitrate" and out["rounds"][0]["reviews"]["code"]["changes"] == [
        "code fix 1"
    ], out
    reply.write_text("VERDICT: PASS\n", encoding="utf-8")
    decision = folder / "decision.md"
    decision.write_text("I read every round.\n\nDECISION: READY\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["decision"]) == ("done", "READY"), out
    decision.unlink()
    reply.write_text("I couldn't review it.\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"]) == ("stop", "rerun"), out


def test_a_cost_line_written_mid_rebase_goes_into_the_resolved_commit(tmp_path, capsys) -> None:
    """The builder's resolve run appends to the change's committed `runs/costs.jsonl` while the
    landing's rebase is stopped: `resolve --continue` stages it, or git refuses to continue."""
    root, tree = _from_main(tmp_path)
    costs = tree / ".sdlc" / "work" / NAME / "runs" / "costs.jsonl"
    costs.parent.mkdir()
    costs.write_text('{"session": "s-1", "cost_usd": 0.5}\n', encoding="utf-8")
    (tree / "README.md").write_text("the change's line\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "the change")
    (root / "README.md").write_text("main's line\n", encoding="utf-8")
    _git(root, "commit", "-q", "-am", "main moves")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "008", False, "main")
    assert out["conflicted"] == ["README.md"], out
    with costs.open("a", encoding="utf-8", newline="\n") as f:
        f.write('{"session": "s-2", "role": "builder", "cost_usd": 0.25}\n')
    (tree / "README.md").write_text("main's line, and the change's\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "008", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert "s-2" in _git(tree, "show", f"HEAD:.sdlc/work/{NAME}/runs/costs.jsonl")


def test_the_hand_back_says_what_the_run_cost(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "runs").mkdir()
    rows = [
        {"session": "s-1", "role": "builder", "model": "opus", "cost_usd": 1.0},
        {"session": "s-2", "role": "code", "model": "sonnet", "cost_usd": 0.25},
        {"session": "s-3", "role": "arbiter", "model": "sonnet", "cost_usd": 0.125},
    ]
    text = "".join(json.dumps(r) + "\n" for r in rows)
    (folder / "runs" / "costs.jsonl").write_text(text, encoding="utf-8")
    code, out = _run(capsys, factory.cmd_stage, root, "008", "test")
    assert code == 0 and out["cost"]["usd"] == 1.375
    assert out["cost"]["by_role"] == {"builder": 1.0, "code": 0.25, "arbiter": 0.125}
    assert out["cost"]["by_model"] == {"opus": 1.0, "sonnet": 0.375}
    code, out = _run(capsys, factory.cmd_stage, root, "008", "build")
    assert "cost" not in out, "only the hand-back reports it"


def test_an_agent_runs_as_its_own_session_in_the_worktree_and_files_its_reply(
    tmp_path, capsys, claude
) -> None:
    root, tree = _from_main(tmp_path)
    worktree = factory.change_root(root, "008")
    code, out = _run(capsys, factory.cmd_agent, worktree, "008", "build", None, None)
    assert code == 0, out
    folder = tree / ".sdlc" / "work" / NAME
    assert (folder / "build" / "round-1.md").read_text().startswith("the report")
    session = (folder / "runs" / "builder.sessions").read_text().split()
    call = claude()[-1]
    assert Path(call["cwd"]).resolve() == tree.resolve()
    argv = call["argv"]
    assert argv[0] == "-p" and argv[1].startswith("Change folder: .sdlc/work/")
    assert argv.count("--verbose") == 1, "stream-json needs it in print mode"
    flags = [a for a in argv[2:] if a != "--verbose"]
    pairs = dict(zip(flags[::2], flags[1::2], strict=True))
    assert pairs["--agent"] == "sdlc-factory:builder" and pairs["--model"] == "opus"
    assert pairs["--permission-mode"] == "auto" and pairs["--output-format"] == "stream-json"
    assert pairs["--session-id"] == session[0] == out["session"]

    # A mend resumes the same builder, with its context, and writes over the report it mends:
    # one `verdicts` names, here a report without its evidence.
    (folder / "build" / "round-1.md").write_text("Built, no evidence.\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_agent, worktree, "008", "mend", "builder", None)
    assert code == 0 and claude()[-1]["argv"][-2:] == ["--resume", session[0]]
    assert (folder / "runs" / "builder.sessions").read_text().split() == session


DISAGREEING = "Both kept changes are in the code.\n\nVERDICT: CHANGES\n\nVERDICT: PASS\n"


def test_a_reviewer_s_disagreeing_verdicts_are_mended_by_the_same_reviewer(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """Bug 2026-11-17-18, 140 R7: a reply whose verdict lines disagree, none of them first, is a
    stop the run mends, asking the reviewer that wrote it, in its own session, to reply again
    with one verdict first, written over the old reply. It is never read as either verdict."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    reply = folder / "reviews" / "round-1" / "code.md"
    reply.write_text(DISAGREEING, encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "mend", ["code"]), out
    assert out["problems"] == [factory._no_verdict(1, "code")]

    (folder / "runs").mkdir()
    (folder / "runs" / "reviewer-code.sessions").write_text("s-code\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "VERDICT: PASS\n\n## Notes\n\nFine.")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "code", None)
    assert code == 0 and out["to"] == f".sdlc/work/{NAME}/reviews/round-1/code.md", out
    argv = claude()[-1]["argv"]
    assert argv[-2:] == ["--resume", "s-code"] and "sdlc-factory:reviewer-code" in argv
    assert "VERDICT:" in argv[1] and "first line" in argv[1]
    assert reply.read_text(encoding="utf-8").startswith("VERDICT: PASS\n"), "written over"
    assert (folder / "runs" / "reviewer-code.sessions").read_text() == "s-code\n"
    assert _verdicts(root, capsys)["next"] == "approve"

    # A reviewer whose reply opens with its verdict has nothing to mend.
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "security", None)
    assert code == 1 and "not a mend for security" in out["refusals"][0]

    # Once: a second such reply from the same reviewer in the same round is a stop like any other.
    reply.write_text("Still.\n\nVERDICT: PASS\nVERDICT: CHANGES\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "rerun", []), out
    calls = len(claude())
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "code", None)
    assert code == 1 and "mended once" in out["refusals"][0] and len(claude()) == calls


def test_an_approver_s_disagreeing_decisions_are_mended_by_the_approver(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """109 R10, 140 R7: a decision.md whose DECISION: lines disagree, none of them first, is a
    stop the run mends once, resuming the approver's own session and writing its whole new reply
    over the old."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    decision = folder / "decision.md"
    decision.write_text("So:\n\nDECISION: ESCALATE\nDECISION: READY\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "mend", ["approver"]), out
    (folder / "runs").mkdir()
    (folder / "runs" / "approver.sessions").write_text("s-a\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "DECISION: READY\n\nFine.")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "approver", None)
    assert code == 0 and out["to"] == f".sdlc/work/{NAME}/decision.md", out
    argv = claude()[-1]["argv"]
    assert argv[-2:] == ["--resume", "s-a"] and "sdlc-factory:approver" in argv
    assert "DECISION:" in argv[1] and "first line" in argv[1]
    assert decision.read_text(encoding="utf-8") == "DECISION: READY\n\nFine.\n"
    assert _verdicts(root, capsys)["next"] == "done"
    decision.write_text("Again.\n\nDECISION: READY\nDECISION: ESCALATE\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"]) == ("stop", "rerun"), "once a round"
    # No DECISION: line at all is nothing to mend: there is no answer to put first.
    decision.write_text("I couldn't decide.\n", encoding="utf-8")
    (folder / "runs" / "mended").unlink()
    assert _verdicts(root, capsys)["way"] == "rerun"


def test_a_verifier_s_unread_answers_are_mended_once(tmp_path, capsys, claude, monkeypatch):
    """109 R10: a verified.md whose answers the script can't read (here in another shape) is a
    stop the run mends once, resuming the arbiter, told what the script found; a second is a
    stop like any other."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1, code="CHANGES")
    verified = folder / "reviews" / "round-1" / "verified.md"
    verified.write_text("- **KEPT:** code: C1: code fix 1\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "mend", ["arbiter"]), out
    (folder / "runs").mkdir()
    (folder / "runs" / "arbiter.sessions").write_text("s-v\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "- KEPT: code: C1: code fix 1")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "arbiter", None)
    assert code == 0 and out["to"] == f".sdlc/work/{NAME}/reviews/round-1/verified.md", out
    argv = claude()[-1]["argv"]
    assert argv[-2:] == ["--resume", "s-v"] and "sdlc-factory:arbiter" in argv
    assert "code fix 1 0 times, not once" in argv[1] and "- KEPT: <role>: C<n>:" in argv[1]
    assert verified.read_text(encoding="utf-8") == "- KEPT: code: C1: code fix 1\n"
    assert _verdicts(root, capsys)["next"] == "rework"
    verified.write_text("- **KEPT:** code: C1: code fix 1\n", encoding="utf-8")
    assert _verdicts(root, capsys)["way"] == "rerun"
    calls = len(claude())
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "arbiter", None)
    assert code == 1 and "mended once" in out["refusals"][0] and len(claude()) == calls


def test_a_build_mend_is_refused_when_verdicts_names_none(tmp_path, capsys, claude) -> None:
    """109 R5, the 103 case: a change at `stage: test`, its landing round's behaviour check missing
    an exit. The build loop's `mend` runs only for a role `verdicts` names in a `mend` stop, so
    nothing runs and nothing appears under `reviews/round-1/`."""
    root = _change(tmp_path, stage="test")
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    (folder / "decision.md").write_text("DECISION: READY\n\nFine.\n", encoding="utf-8")
    land = folder / "reviews" / "land-1"
    land.mkdir(parents=True)
    (land / "behaviour.md").write_text(
        "VERDICT: PASS\n\n## Evidence\n\n$ uv run pytest -q\n3 passed\n", encoding="utf-8"
    )
    before = _files(folder / "reviews" / "round-1")
    assert _verdicts(root, capsys)["next"] == "done"
    for role in ("behaviour", "builder", "code"):
        code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", role, None)
        assert code == 1 and out["refusals"] == [f"verdicts says 'done', not a mend for {role}"]
    assert not claude() and _files(folder / "reviews" / "round-1") == before


@pytest.mark.portable
def test_the_builder_s_evidence_is_mended_once_a_round(tmp_path, capsys, claude, monkeypatch):
    """The same marker holds the evidence mend to once: a second report without it stops."""
    root = _change(tmp_path)
    _report(root, 1, "Built it. The gate passed.\n")
    (root / ".sdlc" / "work" / NAME / "runs").mkdir()
    (root / ".sdlc" / "work" / NAME / "runs" / "builder.sessions").write_text("s-b\n")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "Built it again, no evidence.")
    assert _verdicts(root, capsys)["mend"] == ["builder"]
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "builder", None)
    assert code == 0, out
    assert _verdicts(root, capsys)["way"] == "rerun"
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "builder", None)
    assert code == 1 and "mended once" in out["refusals"][0]


def test_an_agent_out_of_turn_or_failing_files_nothing(tmp_path, capsys, claude, monkeypatch):
    root = _change(tmp_path)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "approve", None, None)
    assert code == 1 and "verdicts says 'build'" in out["refusals"][0] and not claude()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "rework", None, None)
    assert code == 1, "no step out of turn"
    monkeypatch.setenv("FAKE_CLAUDE_EXIT", "1")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    folder = root / ".sdlc" / "work" / NAME
    assert code == 1 and out["exit"] == 1 and "failed" in out["problem"]
    assert not (folder / "build" / "round-1.md").exists()


# A spec-writer's reply as it comes: a sentence before the draft, the draft's frontmatter, a body
# holding a fenced block with its own `---` line and a longer fence nesting a shorter one, then the
# separator and the questions.
FENCED_DRAFT = """\
---
id: 008
kind: spec
---

# 008 — Reopen saved drafts · spec

## Requirements

R1. The config reads as:

```yaml
---
drafts: 30
---
```

````markdown
```sh
echo inside
```
---
````

~~~
---
~~~

R2. Nothing else.

"""
FENCED_REPLY = "Here is the draft.\n\n" + FENCED_DRAFT + "---\n\n- Resolved: none.\n- Left: none.\n"


@pytest.mark.portable
def test_split_draft_cuts_at_the_last_separator_outside_a_fence() -> None:
    """105 R2: the draft runs from the frontmatter to the last bare `---` outside a fence, whole."""
    preamble, draft, questions = factory.split_draft(FENCED_REPLY)
    assert draft == FENCED_DRAFT, "cut at a fence, or a line lost"
    assert questions == "\n- Resolved: none.\n- Left: none.\n"
    assert preamble == "Here is the draft."


@pytest.mark.portable
@pytest.mark.parametrize(
    "reply, expected",
    [
        (FENCED_DRAFT, (None, FENCED_DRAFT, None)),
        ("no frontmatter at all\n", (None, "no frontmatter at all\n", None)),
        ("---\nid: 008\n---\n\nbody\n", (None, "---\nid: 008\n---\n\nbody\n", None)),
        ("---\nid: 008\n", (None, "---\nid: 008\n", None)),
        ("Hi.\n---\nid: 008\n---\nbody\n---\nq\n", ("Hi.", "---\nid: 008\n---\nbody\n", "q\n")),
        ("---\nid: 1\n---\n```\n---\n", (None, "---\nid: 1\n---\n```\n---\n", None)),
    ],
    ids=["no-separator", "no-frontmatter", "body-only", "unclosed", "preamble", "open-fence"],
)
def test_split_draft_without_a_separator_keeps_the_whole_draft(reply, expected) -> None:
    assert factory.split_draft(reply) == expected


def test_the_spec_draft_is_written_whole_to_runs(tmp_path, capsys, claude, monkeypatch) -> None:
    """105 R1: the draft and its questions go to `runs/`, byte for byte; spec.md is untouched and
    the JSON names the files, never carrying the draft itself."""
    root = _change(tmp_path, tier=2, stage="plan")
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", FENCED_REPLY)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None)
    assert code == 0, out
    assert claude()[-1]["argv"][3] == "sdlc-factory:spec-writer"
    assert out["to"] == f".sdlc/work/{NAME}/runs/spec-draft.md"
    assert out["questions"] == f".sdlc/work/{NAME}/runs/spec-questions.md"
    assert out["preamble"] == "Here is the draft." and "reply" not in out
    assert (folder / "runs" / "spec-draft.md").read_bytes() == FENCED_DRAFT.encode()
    questions = (folder / "runs" / "spec-questions.md").read_text(encoding="utf-8")
    assert questions == "\n- Resolved: none.\n- Left: none.\n"
    assert (folder / "spec.md").read_text() == "# 008 — spec.md\n\nWritten.\n", "untouched"

    # A recheck writes over both; one with no separator leaves no stale questions behind.
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "---\nid: 008\n---\n\nSecond draft.\n")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None, None, True)
    assert code == 0 and out["questions"] is None and out["preamble"] is None, out
    draft = (folder / "runs" / "spec-draft.md").read_text(encoding="utf-8")
    assert draft == "---\nid: 008\n---\n\nSecond draft.\n"
    assert not (folder / "runs" / "spec-questions.md").exists()


def test_spec_agent_reply_previews_requirements(tmp_path, capsys, claude, monkeypatch) -> None:
    """210 R5, R12: the filed reply carries the draft's `## Requirements` as the WAIT's preview,
    nothing outside it, and writes nothing beyond the draft's own files."""
    root = _change(tmp_path, tier=2, stage="plan")
    design = "## Design\n\nOne table.\n"
    monkeypatch.setenv(
        "FAKE_CLAUDE_REPLY",
        FENCED_REPLY.replace("\nR2. Nothing else.\n", "\nR2. Nothing else.\n\n" + design),
    )
    before = _git(root, "status", "--porcelain", "--untracked-files=all")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None)
    assert code == 0, out
    preview = out["preview"]
    assert preview.startswith("## Requirements\n\nR1. The config reads as:")
    assert preview.rstrip().endswith("R2. Nothing else.")
    assert "One table" not in preview and "# 008" not in preview and "Resolved" not in preview
    after = _git(root, "status", "--porcelain", "--untracked-files=all").splitlines()
    runs = f".sdlc/work/{NAME}/runs/"
    assert [ln for ln in after if ln not in before.splitlines() and runs not in ln] == []


def test_a_long_spec_preview_is_cut(tmp_path, capsys, claude, monkeypatch) -> None:
    """210 R4, R5: Requirements past 40 lines keep the first 40, naming the draft for the rest; a
    recheck previews its own new draft."""
    root = _change(tmp_path, tier=2, stage="plan")
    reqs = "\n".join(f"R{n}. Requirement {n}." for n in range(1, 46))
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", f"---\nid: 008\n---\n\n## Requirements\n\n{reqs}\n")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None)
    assert code == 0, out
    lines = out["preview"].splitlines()
    assert len(lines) == factory.PREVIEW_LINES + 1
    assert lines[-1] == f"… 7 more lines in .sdlc/work/{NAME}/runs/spec-draft.md"
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "---\nid: 008\n---\n\n## Requirements\n\nR1. One.\n")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None, None, True)
    assert code == 0 and out["preview"] == "## Requirements\n\nR1. One.", out


SCAFFOLD = "---\nid: 008\nkind: spec\n---\n\n# 008 — spec\n\n<requirements>\n\n<design>\n"


def _drafted(tmp_path: Path, tier: int = 2, stage: str = "plan") -> Path:
    """A change whose spec.md is the scaffold and whose spec-writer left a fenced draft."""
    root = _change(tmp_path, tier=tier, stage=stage)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "spec.md").write_text(SCAFFOLD, encoding="utf-8", newline="\n")
    (folder / "runs").mkdir()
    (folder / "runs" / "spec-draft.md").write_bytes(FENCED_DRAFT.encode())
    return root


@pytest.mark.portable
def test_write_spec_copies_the_draft_byte_for_byte(tmp_path, capsys) -> None:
    """105 R3: spec.md becomes the draft exactly, and nothing else is written."""
    root = _drafted(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    before = {p: p.read_bytes() for p in folder.rglob("*") if p.is_file() and p.name != "spec.md"}
    code, out = _run(capsys, factory.cmd_write_spec, root, "008")
    assert code == 0 and out["to"] == f".sdlc/work/{NAME}/spec.md", out
    assert (folder / "spec.md").read_bytes() == FENCED_DRAFT.encode()
    after = {p: p.read_bytes() for p in folder.rglob("*") if p.is_file() and p.name != "spec.md"}
    assert after == before, "writes nothing else"
    # A rerun is refused: spec.md is no longer the scaffold.
    code, out = _run(capsys, factory.cmd_write_spec, root, "008")
    assert code == 1 and "scaffold" in out["refusals"][0]


@pytest.mark.portable
@pytest.mark.parametrize(
    "case, why",
    [
        ("no-draft", "no runs/spec-draft.md"),
        ("tier-1", "Tier 2"),
        ("past-plan", "stage: plan"),
        ("written", "scaffold"),
    ],
)
def test_write_spec_refuses_and_writes_nothing(tmp_path, capsys, case, why) -> None:
    root = _drafted(tmp_path, tier=1 if case == "tier-1" else 2,
                    stage="design" if case == "past-plan" else "plan")  # fmt: skip
    folder = root / ".sdlc" / "work" / NAME
    if case == "no-draft":
        (folder / "runs" / "spec-draft.md").unlink()
    if case == "written":
        (folder / "spec.md").write_text("# 008 — spec\n\nA person's words.\n", encoding="utf-8")
    before = (folder / "spec.md").read_bytes()
    code, out = _run(capsys, factory.cmd_write_spec, root, "008")
    assert code == 1 and why in out["refusals"][0], out
    assert (folder / "spec.md").read_bytes() == before


@pytest.mark.portable
def test_the_scaffold_rule_is_sdlc_s_own() -> None:
    """`write-spec` never writes over a person's text: its copy of `is_unfilled()`'s rule."""
    assert factory.PROMPT_RE.pattern == sdlc.PROMPT_RE.pattern
    assert factory.UNFILLED_THRESHOLD == sdlc.UNFILLED_THRESHOLD
    for text in (SCAFFOLD, "<one>\n", "plain\n", "<a>\n<b>\n<c>\n"):
        assert factory._scaffold(text) == (len(sdlc.PROMPT_RE.findall(text)) >= 2), text


def test_a_revision_reaches_the_same_spec_writer_through_the_ledger(tmp_path, capsys, claude):
    """A person's words never go in a command line: a revision is a ticked `R<n>` line in
    `decisions.md`, read by `agent`, and the spec-writer that drafted is resumed with them; a
    recheck resumes it with fixed text. Neither is a decision the loop waits on."""
    root = _change(tmp_path, tier=2, stage="plan")
    folder = root / ".sdlc" / "work" / NAME
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None, "R1")
    assert code == 1 and "R1" in out["refusals"][0], "no spec-writer yet, and no R1 line"
    _run(capsys, factory.cmd_agent, root, "008", "spec", None, None)
    session = (folder / "runs" / "spec-writer.sessions").read_text().split()
    words = 'drop R3; it\'s "out of scope" & $(nothing) runs'
    (folder / "decisions.md").write_text(
        f"# Decisions\n\n- [x] R1 (person, revise): {words}\n", encoding="utf-8"
    )
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None, "R1")
    argv = claude()[-1]["argv"]
    assert code == 0 and argv[1].endswith(words) and argv[-2:] == ["--resume", session[0]]
    draft = (folder / "runs" / "spec-draft.md").read_text(encoding="utf-8")
    assert draft.startswith("the report"), "a revision writes over the draft"
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None, None, True)
    assert code == 0 and claude()[-1]["argv"][1] == factory.prompt_part("spec", "recheck")
    assert factory.read_ledger(folder) == [], "a revision is no decision the loop waits on"
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None, None, True)
    assert code == 1 and "for --task spec" in out["refusals"][0]


# ---------------------------------------------------------------- what each run was for (174)


@pytest.mark.portable
def test_every_task_has_a_purpose() -> None:
    """174 R1: every task `agent` runs has a purpose, one of `PURPOSES`, in either round."""
    for task in factory.TASKS:
        for rnd, first in ((1, 1), (2, 1), (None, 1)):
            purpose = factory.purpose_of(task, "builder", rnd, first, None, [])
            assert purpose in factory.PURPOSES, (task, rnd, purpose)
    assert set(factory.WASTE) < set(factory.PURPOSES) | {"ejected", "dropped"}
    assert set(factory.RERUNNABLE) <= set(factory.TASKS)


@pytest.mark.portable
@pytest.mark.parametrize(
    "task, role, rnd, first, purpose",
    [
        ("spec", "spec-writer", None, 1, "spec"), ("spec", "spec-writer", 3, 1, "spec"),
        ("build", "builder", 1, 1, "build"), ("build", "builder", 2, 1, "rework"),
        ("build", "builder", 3, 3, "build"), ("build", "builder", 4, 3, "rework"),
        ("review", "code", 1, 1, "build"), ("review", "code", 2, 1, "rework"),
        ("arbitrate", "arbiter", 1, 1, "build"), ("arbitrate", "arbiter", 2, 1, "rework"),
        ("decided", "builder", 1, 1, "build"), ("decided", "builder", 2, 1, "rework"),
        ("approve", "approver", 1, 1, "build"), ("approve", "approver", 3, 1, "build"),
        ("rework", "builder", 1, 1, "rework"), ("fix", "builder", 1, 1, "gate-fix"),
        ("mend", "code", 1, 1, "mend"), ("land-mend", "arbiter", None, 1, "mend"),
        ("resolve", "builder", None, 1, "land"), ("train-resolve", "resolver", None, 1, "land"),
        ("land-fix", "builder", None, 1, "land"), ("land-review", "code", None, 1, "land"),
        ("land-arbitrate", "arbiter", None, 1, "land"),
    ],
)  # fmt: skip
def test_purpose_by_task_and_round(task, role, rnd, first, purpose) -> None:
    """174 R2: the purpose from the task and the round, against the run's first round."""
    land = 1 if task in factory.LAND_TASKS else None
    assert factory.purpose_of(task, role, rnd, first, land, []) == purpose


@pytest.mark.portable
def test_a_second_run_of_a_step_is_a_rerun() -> None:
    """174 R3: the same step for the same role in the same round (or landing) again is a rerun,
    but a second gate fix, answer or conflict is work of its own; rows with no task never match."""
    review = {"task": "review", "role": "code", "round": 2, "purpose": "rework"}
    assert factory.purpose_of("review", "code", 2, 1, None, [review]) == "rerun"
    assert factory.purpose_of("review", "test", 2, 1, None, [review]) == "rework", "another role"
    assert factory.purpose_of("review", "code", 3, 1, None, [review]) == "rework", "another round"
    fix = {"task": "fix", "role": "builder", "round": 2}
    assert factory.purpose_of("fix", "builder", 2, 1, None, [fix]) == "gate-fix"
    land = {"task": "land-review", "role": "code", "land": 1}
    assert factory.purpose_of("land-review", "code", None, 1, 1, [land]) == "rerun"
    assert factory.purpose_of("land-review", "code", None, 1, 2, [land]) == "land"
    resolve = {"task": "resolve", "role": "builder", "land": 1}
    assert factory.purpose_of("resolve", "builder", None, 1, 1, [resolve]) == "land"
    old = {"role": "code", "session": "s"}
    assert factory.purpose_of("review", "code", 1, 1, None, [old]) == "build"


def test_a_row_names_its_purpose_task_and_round(tmp_path, capsys, claude, monkeypatch) -> None:
    """174 R1: every row `agent` writes names its purpose, its task and its round; a review run
    twice in a round is a rerun the second time. Still numbers and names only."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(0.5))
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    monkeypatch.setenv("FAKE_CLAUDE_REPLIES", json.dumps(["VERDICT: PASS"]))
    for _ in range(2):
        (folder / "reviews" / "round-1" / "code.md").unlink(missing_ok=True)
        code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
        assert code == 0, out
    rows = [json.loads(x) for x in (folder / "runs" / "costs.jsonl").read_text().splitlines()]
    said = [(r["task"], r["role"], r["round"], r["purpose"]) for r in rows]
    assert said == [
        ("build", "builder", 1, "build"), ("review", "code", 1, "build"),
        ("review", "code", 1, "rerun"),
    ], said  # fmt: skip
    assert all("land" not in r for r in rows), "a loop task's row names no landing"
    assert all(isinstance(v, int | float | str) for r in rows for v in r.values()), rows


def test_a_run_with_no_figures_leaves_the_next_try_its_own_purpose(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """185 R19 (nit 2026-11-19-36): a run whose `claude` reports no figures writes no row to
    `runs/costs.jsonl`, so the next try of the same task in the same round is not a `rerun`."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(0.5))
    assert _run(capsys, factory.cmd_agent, root, "008", "build", None, None)[0] == 0
    monkeypatch.setenv("FAKE_CLAUDE_REPLIES", json.dumps(["VERDICT: PASS"]))
    monkeypatch.delenv("FAKE_CLAUDE_FIGURES")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
    assert code == 0, out
    rows = [json.loads(x) for x in (folder / "runs" / "costs.jsonl").read_text().splitlines()]
    assert [r["task"] for r in rows] == ["build"], "no figures, no row"
    (folder / "reviews" / "round-1" / "code.md").unlink()
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(0.5))
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
    assert code == 0, out
    rows = [json.loads(x) for x in (folder / "runs" / "costs.jsonl").read_text().splitlines()]
    assert [(r["task"], r["purpose"]) for r in rows] == [("build", "build"), ("review", "build")]


@pytest.mark.parametrize(
    "argv", [["--task", "review", "--role", "verifier"], ["--task", "verify"],
             ["--task", "land-verify"]], ids=["role", "task", "land-task"],
)  # fmt: skip
def test_the_verifier_role_and_task_are_gone(tmp_path, argv) -> None:
    """187 R12: the verifier is the arbiter, with no alias: argparse refuses the old names."""
    run = subprocess.run(
        [sys.executable, str(FACTORY_PY), "agent", "008", *argv],
        cwd=tmp_path, capture_output=True, encoding="utf-8",
    )  # fmt: skip
    assert run.returncode == 2, run.stdout + run.stderr
    assert "invalid choice" in run.stderr
    assert "arbiter" in factory.ROLES and "verifier" not in factory.ROLES
    assert {"arbitrate", "land-arbitrate"} <= set(factory.TASKS)
    assert not {"verify", "land-verify"} & set(factory.TASKS)


def test_models_verifier_is_an_unknown_role() -> None:
    """187 R16: `[models] verifier` has no shim. It warns like any unknown role, and the arbiter
    runs on `[models] arbiter` or its default, `sonnet`."""
    models, warnings = factory._models({"verifier": "opus"})
    assert any("unknown role 'verifier'" in w for w in warnings), warnings
    cfg = factory.load_config(Path("/nonexistent"))[0]
    assert factory.model_for("arbiter", {**cfg, "models": models}, 2, "full") == "sonnet"
    models, warnings = factory._models({"verifier": "opus", "arbiter": "haiku"})
    assert factory.model_for("arbiter", {**cfg, "models": models}, 2, "full") == "haiku"
    assert len(warnings) == 1


def test_the_arbiter_writes_verified_md(tmp_path, capsys, claude, monkeypatch) -> None:
    """187 R13: the arbiter runs as `sdlc-factory:arbiter` on `--task arbitrate`, and its answers
    land in the round's `verified.md`, which keeps its name."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1, code="CHANGES")
    assert _verdicts(root, capsys)["next"] == "arbitrate"
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "- KEPT: code: C1: code fix 1")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "arbitrate", None, None)
    assert code == 0 and out["to"] == f".sdlc/work/{NAME}/reviews/round-1/verified.md", out
    argv = claude()[-1]["argv"]
    assert "sdlc-factory:arbiter" in argv
    assert (folder / "runs" / "arbiter.sessions").is_file()
    text = (folder / "reviews" / "round-1" / "verified.md").read_text(encoding="utf-8")
    assert text == "- KEPT: code: C1: code fix 1\n"
    assert _verdicts(root, capsys)["next"] == "rework"


def test_an_old_verifier_mend_counts_for_its_round(tmp_path, capsys) -> None:
    """187 R14: a `verifier <n>` line in `runs/mended`, written before the rename, is the
    arbiter's mend for round n, so the run doesn't mend it a second time."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1, code="CHANGES")
    verified = folder / "reviews" / "round-1" / "verified.md"
    verified.write_text("- **KEPT:** code: C1: code fix 1\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "mend", ["arbiter"]), out
    (folder / "runs").mkdir()
    (folder / "runs" / "mended").write_text("verifier 1\n", encoding="utf-8")
    assert factory.mended(folder) == {("arbiter", 1)}
    assert _verdicts(root, capsys)["way"] == "rerun", "mended once already, as the verifier"
    assert factory.RENAMED == {
        "verifier": "arbiter",
        "verify": "arbitrate",
        "land-verify": "land-arbitrate",
    }


def test_an_old_verifier_session_is_resumed_as_the_arbiter(tmp_path, capsys, claude, monkeypatch):
    """187 R14: a run in flight when the plugin updated holds `runs/verifier.sessions`; a mend of
    the arbiter resumes that session rather than refusing for want of `arbiter.sessions`."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1, code="CHANGES")
    verified = folder / "reviews" / "round-1" / "verified.md"
    verified.write_text("- **KEPT:** code: C1: code fix 1\n", encoding="utf-8")
    (folder / "runs").mkdir()
    (folder / "runs" / "verifier.sessions").write_text("s-v\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "- KEPT: code: C1: code fix 1")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "arbiter", None)
    assert code == 0, out
    argv = claude()[-1]["argv"]
    assert argv[-2:] == ["--resume", "s-v"] and "sdlc-factory:arbiter" in argv
