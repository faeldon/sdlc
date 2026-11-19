"""The skill evals' own mechanism, checked without running a model.

`evals/` holds the `claude plugin eval` suite for the core skills: each case builds its host repo
with `evals/scaffold.sh` from a fixture, and only a person runs the suite. What these tests can
prove without a model is that every fixture is a repo the script accepts, so a script change that
breaks one fails the gate here rather than in a paid run.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import frontmatter
import pytest

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
SCRIPT = ROOT / "scripts" / "sdlc.py"
_spec = importlib.util.spec_from_file_location("sdlc_evals_test", SCRIPT)
sdlc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sdlc)
_fspec = importlib.util.spec_from_file_location(
    "factory_evals_test", ROOT / "plugins" / "factory" / "scripts" / "factory.py"
)
factory = importlib.util.module_from_spec(_fspec)
_fspec.loader.exec_module(factory)
# `fresh` is the base alone; every other fixture names the branch its change is on, or `main`.
FIXTURES = [
    "fresh",
    *sorted(
        p.name
        for p in (EVALS / "fixtures").iterdir()
        if (p / "branch").is_file() or (p / "main").is_file()
    ),
]

pytestmark = pytest.mark.portable
SCAFFOLDS = [
    pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do"),
    pytest.mark.skipif(shutil.which("sh") is None, reason="the scaffold is sh, as _sh() is"),
]
# The cases that stop at their skill's WAIT, and the commands each must never have run before it.
STOP_CASES = {
    "intent": ["new"], "intent-product": ["new"], "spec": [], "ship": ["ship"],
    "ship-open-finding": ["ship"], "ship-behaviour": ["ship"], "close": ["close"],
    "idea": ["inbox-commit"],
}  # fmt: skip


def _scaffold(fixture: str, where: Path) -> None:
    """The case's scaffold, run as `plugin eval --scaffold` runs it: in the empty workspace."""
    where.mkdir()
    subprocess.run(
        ["sh", str(EVALS / "scaffold.sh"), fixture],
        cwd=where, check=True, capture_output=True, encoding="utf-8",
    )  # fmt: skip


@pytest.mark.parametrize("fixture", FIXTURES)
@SCAFFOLDS[0]
@SCAFFOLDS[1]
def test_every_fixture_passes_check(fixture: str, tmp_path: Path) -> None:
    """R4: each fixture builds, and the script finds nothing wrong with the repo it makes."""
    repo = tmp_path / fixture
    _scaffold(fixture, repo)
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    checked = subprocess.run(
        ["uv", "run", "--quiet", "--script", str(SCRIPT), "check", "--strict"],
        cwd=repo, capture_output=True, encoding="utf-8", env=env,
    )  # fmt: skip
    assert checked.returncode == 0, checked.stdout + checked.stderr


@SCAFFOLDS[0]
@SCAFFOLDS[1]
def test_the_set_up_fixture_is_complete(tmp_path: Path) -> None:
    """The setup case runs on a repo `readiness` calls complete, or the run it grades is a first
    setup: checked here for free, not found out in a paid run."""
    repo = tmp_path / "set-up"
    _scaffold("set-up", repo)
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    ran = subprocess.run(
        ["uv", "run", "--quiet", "--script", str(SCRIPT), "readiness"],
        cwd=repo, capture_output=True, encoding="utf-8", env=env, check=True,
    )  # fmt: skip
    out = json.loads(ran.stdout)
    assert out["complete"], [i for i in out["items"] if i["status"] not in ("ok", "n/a")]
    assert out["unset"] == ["commands.build", "commands.scan"]


def test_a_fixture_never_names_a_missing_one() -> None:
    """An `extends` that names no fixture would scaffold a half-built change: refused."""
    for fixture in FIXTURES[1:]:
        extends = EVALS / "fixtures" / fixture / "extends"
        if extends.is_file():
            parent = extends.read_text(encoding="utf-8").strip()
            assert (EVALS / "fixtures" / parent / "change").is_dir(), fixture


def _graders(case: str) -> dict[str, frontmatter.Post]:
    return {p.stem: frontmatter.load(p) for p in (EVALS / case / "graders").glob("*.md")}


@pytest.mark.parametrize("case", sorted(STOP_CASES))
def test_a_stop_case_keeps_every_never_write_grader(case: str) -> None:
    """R2: a stop case asks config, ends at its question, and grades every write its WAIT
    approves as never run, with Write, Edit and Bash granted so those graders can fail."""
    graders = _graders(case)
    prompt = frontmatter.load(EVALS / case / "prompt.md")
    assert {"Bash", "Write", "Edit"} <= set(prompt["allowed_tools"]), case
    assert graders["asks-config"]["input_match"].endswith(" config"), case
    assert graders["asks-the-question"]["target"] == "last_message", case
    # No dialog in a run nobody answers: the skill asks its text fallback, which last_message reads.
    assert "AskUserQuestion" not in prompt["allowed_tools"], case
    for never in ["commits", "pushes", "writes", "edits", *STOP_CASES[case]]:
        g = graders[f"never-{never}"]
        assert (g["min"], g["max"]) == (0, 0), f"{case}: never-{never}"
    *_, fixture, flag = (EVALS / case / "scaffold.sh").read_text(encoding="utf-8").split()
    assert fixture in FIXTURES and flag == "--sandbox", case


@pytest.mark.parametrize("case", sorted(STOP_CASES))
def test_a_judgment_grader_reads_the_whole_reply(case: str) -> None:
    """A stop case's `llm` grader judges what came before its question, which a skill may ask in
    a message of its own: so it reads the run's trace, never only the last message (the default)."""
    for name, g in _graders(case).items():
        if g["type"] == "llm":
            assert g.get("focus") == "trace", f"{case}: {name}"
            assert "before its final question" in g.content, f"{case}: {name}"


def test_the_setup_case_stops_before_its_drafts() -> None:
    """R10: on a set-up repo, setup asks config, reads none of its drafts, writes, commits or
    pushes nothing, and ends saying so: it has no question to end at, so no `asks-the-question`."""
    graders = _graders("setup")
    prompt = frontmatter.load(EVALS / "setup" / "prompt.md")
    assert {"Bash", "Write", "Edit"} <= set(prompt["allowed_tools"])
    assert "AskUserQuestion" not in prompt["allowed_tools"]
    assert graders["asks-config"]["input_match"].endswith(" config")
    for never in ("commits", "pushes", "writes", "edits", "reads-drafts"):
        g = graders[f"never-{never}"]
        assert (g["min"], g["max"]) == (0, 0), f"never-{never}"
    assert graders["says-set-up"]["target"] == "last_message"
    *_, fixture, flag = (EVALS / "setup" / "scaffold.sh").read_text(encoding="utf-8").split()
    assert (fixture, flag) == ("set-up", "--sandbox") and fixture in FIXTURES
    assert sdlc.case_tags(EVALS)["setup"] == ["setup"]
    assert sdlc.cases_scope(["skills/setup/drafts.md"], sdlc.case_tags(EVALS)) == ["setup"]


def test_the_never_graders_match_what_they_forbid() -> None:
    """Each never-grader's pattern, read as the eval reads it (a regex over the tool call's JSON
    input), catches the call it forbids and lets the read-only one through."""

    def hits(case: str, grader: str, inp: dict) -> bool:
        # No `input_match` counts every call of the tool; both JSON spacings are read alike.
        pattern = _graders(case)[grader].get("input_match", "")
        return any(re.search(pattern, json.dumps(inp, separators=s)) for s in ((",", ":"), None))

    sdlc_py = 'uv run --quiet --script "/p"/scripts/sdlc.py'
    assert hits("ship", "never-ship", {"command": f"{sdlc_py} ship 001 --fixed F1"})
    assert not hits("ship", "never-ship", {"command": f"{sdlc_py} preflight 001"})
    assert hits("close", "never-close", {"command": f"{sdlc_py} close 001"})
    assert not hits("close", "never-close", {"command": f"{sdlc_py} close 001 --check"})
    assert hits("ship", "never-commits", {"command": 'git commit -m "x"'})
    assert hits("ship", "never-commits", {"command": "git -C /r commit -q -m x"})
    assert hits("ship", "never-pushes", {"command": "git push origin main"})
    assert hits("ship", "never-writes", {"file_path": "/w/drafts.py", "content": "x"})
    assert not hits("ship", "never-writes", {"file_path": "/w/.sdlc/work/001-x/findings.md"})
    assert hits("intent", "never-writes", {"file_path": "/w/findings.md", "content": "x"})
    assert hits("ship", "asks-script", {"command": f"{sdlc_py} preflight 001 --question"})
    # The script held in a variable, as a run did: `S=…/sdlc.py; uv run --script "$S" …`.
    held = 'S="/p/scripts/sdlc.py"; uv run --quiet --script "$S"'
    assert hits("ship", "asks-script", {"command": f"{held} preflight 001 --question"})
    assert hits("ship", "never-ship", {"command": f"{held} ship 001"})
    assert hits("close", "never-close", {"command": "uv run --script ${S} close 001"})
    assert not hits("close", "never-close", {"command": f"{held} close 001 --check"})
    assert hits("intent", "asks-config", {"command": f"{held} config"})
    assert hits("setup", "never-reads-drafts", {"file_path": "/plug/skills/setup/drafts.md"})
    assert not hits("setup", "never-reads-drafts", {"file_path": "/plug/skills/setup/SKILL.md"})


GRADED_BY_OUTCOME = ("Read", "Write", "Edit", "Glob", "Grep")


def test_no_grader_insists_on_a_tool() -> None:
    """156 R1: a grader that requires a call (`min` ≥ 1) names only `Bash`, for a command only a
    shell runs (the plugin's script, or git): a file read or written by any tool is the same
    outcome, so a `cat` never fails a case that asked for a Read. A never-grader may name any."""
    insisting = []
    for path in sorted(EVALS.glob("*/graders/*.md")):
        g = frontmatter.load(path)
        if g.get("type") == "tool_used" and int(g.get("min", 0) or 0) >= 1:
            if g.get("tool") in GRADED_BY_OUTCOME:
                insisting.append(f"{path.parent.parent.name}/{path.stem}")
            else:
                assert g.get("tool") == "Bash", path
                assert re.search(r"sdlc|git", g.get("input_match", "")), path
    assert insisting == []


def test_a_diff_calls_for_the_cases_of_the_skills_it_touches() -> None:
    tags = {"ship": ["ship"], "ship-open-finding": ["ship"], "intent": ["intent"]}
    assert sdlc.cases_scope(["skills/ship/SKILL.md"], tags) == ["ship", "ship-open-finding"]
    assert sdlc.cases_scope(["scripts/sdlc.py", "README.md"], tags) == []
    assert sdlc.cases_scope(["plugins/factory/skills/build/SKILL.md"], tags) == []


def test_the_cases_are_read_with_their_tags() -> None:
    tags = sdlc.case_tags(EVALS)
    assert set(STOP_CASES) <= set(tags)
    assert all(tags[c] for c in STOP_CASES), "a case with no tag is never in a change's scope"


def test_runs_compare_case_by_case() -> None:
    def run(**scores: float) -> dict:
        return {"cases": [{"name": n.replace("_", "-"), "aggregates": {"score": s}}
                          for n, s in scores.items()]}  # fmt: skip

    found = sdlc.compare_runs(run(ship=1, intent=1), run(ship=0.5, intent=1, close=0))
    assert found["failed"] == ["close", "ship"] and found["fell"] == ["ship"]
    assert found["rerun"] == [["--case", "close"], ["--case", "ship"]] and not found["passed"]
    ship = next(r for r in found["cases"] if r["case"] == "ship")
    assert (ship["before"], ship["delta"]) == (1.0, -0.5)
    assert sdlc.compare_runs(None, run(ship=1))["passed"]
    assert sdlc.compare_runs(None, {"cases": "nonsense"}) == {
        "cases": [], "failed": [], "fell": [], "rerun": [], "passed": False,
    }  # fmt: skip


def test_a_run_grants_its_tools_and_caps_its_cost(tmp_path: Path) -> None:
    """R9: the target first, every grant, one arm, and the scope's ceiling; never a shell."""
    argv = sdlc.cases_argv(tmp_path / "evals", tmp_path / "run", "change", ["intent", "ship"])
    assert argv[:4] == ["claude", "plugin", "eval", str(tmp_path / "evals")]
    tagged = argv[argv.index("--tag") + 1 : argv.index("--scaffold")]
    assert tagged == ["intent", "ship"] and "--case" not in argv, "--case takes one glob a run"
    assert argv[argv.index("--max-cost-usd") + 1] == "5" and argv[argv.index("--runs") + 1] == "1"
    assert argv[argv.index("--ablation") + 1] == "none" and "--scaffold" in argv
    granted = argv[argv.index("--allow-tools") + 1 : argv.index("--allow-tools") + 4]
    assert granted == ["Bash", "Write", "Edit"]
    assert "--keep-temp" in argv, "156 R9: every run keeps its workspace until its trace is kept"
    full = sdlc.cases_argv(tmp_path / "evals", tmp_path / "run", "full", ["a", "b"])
    assert "--tag" not in full and full[full.index("--max-cost-usd") + 1] == "20"
    assert "--keep-temp" in full and full[-2:] == ["--json", str(tmp_path / "run" / "result.json")]


def test_ship_runs_the_cases_through_the_changes_own_script() -> None:
    """Ship runs `run-cases` from a change's worktree: a change that adds or edits it must reach
    its own script, not main's copy, which may not have the command at all."""
    assert "run-cases" in sdlc.OWN_SCRIPT_CMDS


def test_a_run_that_writes_no_result_is_skipped(tmp_path: Path, monkeypatch, capsys) -> None:
    """R14: a run that ends with no result.json (a case that failed to load) didn't happen: it is
    `skipped` with why and exits 0, never a failure of ship."""
    monkeypatch.setattr(sdlc, "_one_change", lambda root, ident: tmp_path / "053-x")
    monkeypatch.setattr(sdlc, "main_root", lambda root: tmp_path)
    monkeypatch.setattr(
        sdlc, "_cases_report", lambda r, p: {"available": True, "cases": {"ship": ["ship"]},
                                             "scope": ["ship"]}
    )  # fmt: skip

    def eval_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, "", "case ship failed to load\n")

    monkeypatch.setattr(sdlc.subprocess, "run", eval_run)
    assert sdlc.cmd_run_cases(tmp_path, "053") == 0
    out = json.loads(capsys.readouterr().out)
    assert out["skipped"] == "plugin eval wrote no result: case ship failed to load"


def test_the_report_folder_matches_the_factorys(tmp_path: Path, capsys) -> None:
    """The runs share `.sdlc/reports/`, which ignores itself, with the factory's eval and review:
    both scripts make it the same way, at the same path."""
    assert Path(sdlc.REPORTS) == Path(factory.REPORTS)
    run = sdlc._case_run_dir(tmp_path)
    factory.cmd_report_dir(tmp_path, "eval")
    capsys.readouterr()
    assert (tmp_path / sdlc.REPORTS / ".gitignore").read_text(encoding="utf-8") == "*\n"
    assert run.parent == tmp_path / sdlc.REPORTS and run.name.endswith("-1")


def test_status_nudges_only_when_claude_code_moved_since_the_last_full_run() -> None:
    """R12: a nudge, never a problem, and only with a full run on record to compare."""
    full = {"available": True, "last_full": {"claude": "2.1.300"}}
    assert "2.1.300; now 2.1.311" in sdlc.cases_nudge(full, "2.1.311")
    assert sdlc.cases_nudge(full, "2.1.300") is None
    assert sdlc.cases_nudge({"available": True, "last_full": None}, "2.1.311") is None
    assert sdlc.cases_nudge({"available": False}, "2.1.311") is None


def test_a_host_has_no_cases(tmp_path: Path) -> None:
    """In a host, even one whose checkout holds an `evals/`, nothing is read or run."""
    (tmp_path / "evals" / "x").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    assert sdlc._cases_report(tmp_path, None) == {"available": False}


def test_the_behaviour_case_reads_its_branch_and_says_it_ran() -> None:
    """143 R23, 156 R2: a Tier 2 change with a filled spec says in its findings.md's note whether
    the behaviour check ran, graded on what the run left, never on the tool that wrote it or on
    which tool read `behaviour.md`; the plain ship case still reads no branch file."""
    graders = _graders("ship-behaviour")
    assert "reads-behaviour" not in graders, "a read is graded by what follows it, not its tool"
    says = graders["says-the-behaviour-check"]
    assert (says["type"], says.get("focus")) == ("llm", "trace")
    flat = " ".join(says.content.split())
    assert "before its final question" in flat
    assert "Behaviour check: ran" in flat and "Behaviour check: skipped, <why>" in flat
    assert "a `Write`, an `Edit` and a shell command count the same" in flat
    assert "never the skill's own text" in flat
    assert "never-reads-a-branch" in _graders("ship")
    spec = EVALS / "fixtures" / "built-tier2" / "change" / ".sdlc" / "work" / "002-rename-drafts"
    assert not sdlc.is_unfilled(spec / "spec.md")
    assert sdlc.load_change(spec, ROOT)["tier"] == 2


# ---------------------------------------------------------------- 156: runs that tell

NO_GIT = Path(__file__).parent / "fixtures" / "eval-trace-no-git.jsonl"


def _trace(where: Path, lines: list[dict] | None = None) -> Path:
    """A trace in an eval's own workspace layout, `<where>/out/trace.jsonl`."""
    path = where / "out" / "trace.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if lines is None:
        shutil.copyfile(NO_GIT, path)
    else:
        path.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8",
                        newline="\n")  # fmt: skip
    return path


def _a_run(score: float, trace: Path | None = None, failing: tuple[str, ...] = ()) -> dict:
    graders = [{"name": g, "passed": False, "weight": 1, "explanation": f"{g} said no"}
               for g in failing]  # fmt: skip
    graders.append({"name": "asks-config", "passed": True, "weight": 1, "explanation": "ok"})
    return {"score": score, "passed": score >= 1, "error": None, "costUsd": 0.5,
            "tracePath": str(trace) if trace else None, "graders": graders}  # fmt: skip


def _a_result(cost: float = 1.0, **cases: list[dict]) -> dict:
    return {"claudeVersion": "2.1.311", "costUsd": cost,
            "cases": [{"name": n.replace("_", "-"), "arms": {"with": runs},
                       "aggregates": {"score": sum(r["score"] for r in runs) / len(runs)}}
                      for n, runs in cases.items()]}  # fmt: skip


def test_a_trace_that_could_not_start_git_is_environment(tmp_path: Path) -> None:
    """156 R8: a failed run whose trace shows, in a tool's result, that git couldn't start is the
    sandbox's, never the skill's; the marker in the agent's own words, or a passing run, isn't."""
    assert sdlc._environment_run(NO_GIT)
    assert not sdlc._environment_run(tmp_path / "missing.jsonl")
    entries = [json.loads(x) for x in NO_GIT.read_text(encoding="utf-8").splitlines()]
    said = "xcode-select: Failed to locate 'git' is what I'd expect here"
    own = [e for e in entries if e["type"] != "user"] + [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": said}]}}
    ]
    assert not sdlc._environment_run(_trace(tmp_path / "own", own))
    # A tool result given as text blocks, as some tools return it.
    blocks = [
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "content": [
                            {
                                "type": "text",
                                "text": "xcode-select: Failed to locate 'git', and no install",
                            }
                        ],
                    }
                ]
            },
        }
    ]
    assert sdlc._environment_run(_trace(tmp_path / "blocks", blocks))
    runs = sdlc.case_runs(_a_result(ship=[_a_run(1.0, NO_GIT), _a_run(0.5, NO_GIT, ("x",))]))
    sdlc.classify_runs(runs)
    assert [r["environment"] for r in runs["ship"]] == [False, True], "a pass never is"


def _verdicts(scope: str, first: dict, reruns: dict | None = None) -> dict:
    runs = sdlc.case_runs(first)
    sdlc.classify_runs(runs)
    return sdlc.case_verdicts(scope, runs, reruns or {})


def test_a_case_fails_only_twice() -> None:
    """156 R5: in a change's scope a case fails only when its rerun fails too; failed then passed
    is `passed on rerun`, counted as passed."""
    first = _a_result(ship=[_a_run(0.5, failing=("asks-the-question",))], close=[_a_run(1.0)])
    passed = sdlc.case_runs(_a_result(ship=[_a_run(1.0)]))["ship"]
    v = _verdicts("change", first, {"ship": passed})
    assert v["ship"]["result"] == "passed on rerun" and v["close"]["result"] == "passed"
    assert sdlc.verdict_lists(v) == {"failed": [], "environment": [], "passed_on_rerun": ["ship"]}
    assert v["ship"]["runs"][0]["graders"] == [
        {"name": "asks-the-question", "explanation": "asks-the-question said no"}
    ]
    assert v["ship"]["runs"][1]["rerun"] is True
    failed = sdlc.case_runs(_a_result(ship=[_a_run(0.0, failing=("never-writes",))]))["ship"]
    v = _verdicts("change", first, {"ship": failed})
    assert v["ship"]["result"] == "failed"
    assert sdlc.verdict_lists(v)["failed"] == ["ship"]


def test_a_full_run_fails_a_case_on_two_runs(tmp_path: Path) -> None:
    """156 R7: three runs a case, no rerun; two failures of the skill's fail it, one is shown but
    doesn't, and runs the sandbox spoiled never count."""
    ok, bad = _a_run(1.0), _a_run(0.5, failing=("asks-script",))
    env = _a_run(0.0, NO_GIT, ("asks-script",))
    v = _verdicts("full", _a_result(a=[ok, ok, ok], b=[ok, bad, ok], c=[bad, ok, bad],
                                    d=[env, env, bad], e=[env, env, env]))  # fmt: skip
    assert {c: v[c]["result"] for c in v} == {
        "a": "passed", "b": "passed", "c": "failed", "d": "passed", "e": "environment",
    }  # fmt: skip
    assert [r["score"] for r in v["b"]["runs"]] == [1.0, 0.5, 1.0], "the one failure is shown"
    assert sdlc.verdict_lists(v) == {"failed": ["c"], "environment": ["e"], "passed_on_rerun": []}


def test_the_runs_note_is_composed_once() -> None:
    """156 R10: the findings line, each list only when it has a case; still `CASES_RE`'s."""
    v = {"a": {"result": "passed"}, "b": {"result": "failed"}, "c": {"result": "environment"},
         "d": {"result": "passed on rerun"}}  # fmt: skip
    note = sdlc.cases_note(v, ".sdlc/reports/cases-2026-11-18-1")
    assert note == ("Skill evals: ran, 2 of 4; failed: b; environment: c; passed on rerun: d; "
                    "run: .sdlc/reports/cases-2026-11-18-1")  # fmt: skip
    assert sdlc.CASES_RE.match(note) and factory.CASES_RE.match(note)
    assert sdlc.cases_note({"a": {"result": "passed"}}, "r") == "Skill evals: ran, 1 of 1; run: r"


def _run_cases(tmp_path: Path, monkeypatch, replies: list) -> list[list[str]]:
    """`cmd_run_cases` for change 053 with `plugin eval` faked: each call takes the next reply,
    `(exit, result or None)`, writing the result where `--json` says."""
    monkeypatch.setattr(sdlc, "_one_change", lambda root, ident: tmp_path / "053-x")
    monkeypatch.setattr(sdlc, "main_root", lambda root: tmp_path)
    monkeypatch.setattr(
        sdlc, "_cases_report", lambda r, p: {"available": True, "scope": ["close", "ship"],
                                             "cases": {"ship": ["ship"], "close": ["close"]}}
    )  # fmt: skip
    calls = []

    def eval_run(argv, **kw):
        calls.append(argv)
        code, result = replies[len(calls) - 1]
        if result is not None:
            Path(argv[argv.index("--json") + 1]).write_text(json.dumps(result), encoding="utf-8")
        return subprocess.CompletedProcess(argv, code, "", "")

    monkeypatch.setattr(sdlc.subprocess, "run", eval_run)
    return calls


def test_a_failed_case_reruns_once_alone(tmp_path: Path, monkeypatch, capsys) -> None:
    """156 R4, R9: a case that fails its run reruns alone (`--case`, no `--tag`), once, under
    what's left of the cap, into its own folder; a failed run's trace is kept in the run."""
    trace = _trace(tmp_path / "ws", [{"type": "result"}])
    fail = _a_result(1.25, ship=[_a_run(0.5, trace, ("asks-the-question",))], close=[_a_run(1.0)])
    again = _a_result(0.75, ship=[_a_run(0.5, trace, ("asks-the-question",))])
    calls = _run_cases(tmp_path, monkeypatch, [(1, fail), (1, again), (0, None)])
    assert sdlc.cmd_run_cases(tmp_path, "053") == 1
    assert len(calls) == 2, "one rerun, never a third run"
    rerun = calls[1]
    assert rerun[rerun.index("--case") + 1] == "ship" and "--tag" not in rerun
    assert rerun[rerun.index("--max-cost-usd") + 1] == "3.75", "5 less what the first run cost"
    assert rerun[rerun.index("--runs") + 1] == "1" and "--keep-temp" in rerun
    out = json.loads(capsys.readouterr().out)
    run = tmp_path / out["run"]
    assert Path(rerun[rerun.index("--output-dir") + 1]) == run / "rerun-ship"
    assert out["failed"] == ["ship"] and out["passed"] is False
    traces = [r["trace"] for r in out["verdicts"]["ship"]["runs"]]
    assert traces == [f"{out['run']}/traces/ship-1.jsonl", f"{out['run']}/traces/ship-rerun.jsonl"]
    assert (tmp_path / traces[0]).is_file() and (tmp_path / traces[1]).is_file()
    assert out["verdicts"]["close"]["runs"][0]["trace"] is None, "a pass keeps no trace"
    assert out["cost_usd"] == 2.0
    assert json.loads((run / "scope.json").read_text(encoding="utf-8"))["note"] == out["note"]


@pytest.mark.parametrize(
    "spent, ceiling",
    [(0.65, "4.35"), (0.30000000000000004, "4.7"), (0.305, "4.69")],
)
def test_the_rerun_ceiling_keeps_its_last_cent(
    tmp_path: Path, monkeypatch, capsys, spent: float, ceiling: str
) -> None:
    """172 R9 (nit 2026-11-18-100): the rerun's ceiling is the cap less what was spent, to the
    cent: float noise never costs a cent, and a real fraction of one still rounds down."""
    fail = _a_result(spent, ship=[_a_run(0.5, failing=("x",))], close=[_a_run(1.0)])
    calls = _run_cases(tmp_path, monkeypatch, [(1, fail), (1, _a_result(0.1, ship=[_a_run(1.0)]))])
    sdlc.cmd_run_cases(tmp_path, "053")
    rerun = calls[1]
    assert rerun[rerun.index("--max-cost-usd") + 1] == ceiling


def test_a_rerun_that_passes_passes_the_run(tmp_path: Path, monkeypatch, capsys) -> None:
    """156 R5: failed then passed exits 0, the case `passed on rerun` in the output and note."""
    fail = _a_result(1.0, ship=[_a_run(0.5, failing=("x",))], close=[_a_run(1.0)])
    _run_cases(tmp_path, monkeypatch, [(1, fail), (0, _a_result(0.5, ship=[_a_run(1.0)]))])
    assert sdlc.cmd_run_cases(tmp_path, "053") == 0
    out = json.loads(capsys.readouterr().out)
    assert (out["failed"], out["passed_on_rerun"], out["passed"]) == ([], ["ship"], True)
    assert out["note"].startswith("Skill evals: ran, 2 of 2; passed on rerun: ship; run: ")


@pytest.mark.parametrize("first_cost, reply", [(5.0, None), (1.0, (2, None))])
def test_a_rerun_the_cap_cant_cover_is_a_failure(
    tmp_path: Path, monkeypatch, capsys, first_cost: float, reply
) -> None:
    """156 R6: no ceiling left for the rerun, or a rerun stopped at it, fails the case, marked
    so; it is never quietly passed."""
    fail = _a_result(first_cost, ship=[_a_run(0.5, failing=("x",))], close=[_a_run(1.0)])
    calls = _run_cases(tmp_path, monkeypatch, [(1, fail), reply])
    assert sdlc.cmd_run_cases(tmp_path, "053") == 1
    assert len(calls) == (1 if reply is None else 2)
    out = json.loads(capsys.readouterr().out)
    assert out["failed"] == ["ship"]
    assert out["verdicts"]["ship"]["why"] == "not rerun: the cost cap"


def test_a_sandbox_failure_is_never_rerun_nor_counted(tmp_path: Path, monkeypatch, capsys) -> None:
    """156 R8: a run that couldn't start git is `environment`: no rerun, no failure, exit 0."""
    trace = _trace(tmp_path / "ws")
    first = _a_result(1.0, ship=[_a_run(0.0, trace, ("asks-script",))], close=[_a_run(1.0)])
    calls = _run_cases(tmp_path, monkeypatch, [(1, first)])
    assert sdlc.cmd_run_cases(tmp_path, "053") == 0 and len(calls) == 1
    out = json.loads(capsys.readouterr().out)
    assert (out["environment"], out["failed"]) == (["ship"], [])
    assert "; environment: ship; run: " in out["note"]


def test_only_the_evals_own_workspace_is_removed(tmp_path: Path) -> None:
    """156 R9: a run's `e-*` workspace directly in the system temp dir is removed, modes and all,
    once its trace is kept; one anywhere else is left and listed; `--keep` removes nothing."""
    import tempfile

    def workspace(parent: Path | None) -> tuple[Path, Path]:
        ws = Path(tempfile.mkdtemp(prefix="e-", dir=parent))
        trace = _trace(ws, [{"type": "result"}])
        (ws / "sealed").mkdir()
        if os.name != "nt":
            (ws / "sealed").chmod(0)
            ws.chmod(0o500)
        return ws, trace

    run = tmp_path / "run"
    run.mkdir()
    ws, trace = workspace(None)
    try:
        runs = sdlc.case_runs(_a_result(ship=[_a_run(0.5, trace, ("x",))]))
        assert sdlc._keep_traces(run, tmp_path, runs, "", keep=True) == []
        assert ws.is_dir(), "--keep removes nothing"
        assert sdlc._keep_traces(run, tmp_path, runs, "", keep=False) == []
        assert not ws.exists() and (run / "traces" / "ship-1.jsonl").is_file()
    finally:
        if ws.exists():
            for p in (ws, ws / "sealed"):
                p.chmod(0o700)
            shutil.rmtree(ws)
    outside, trace = workspace(tmp_path)
    runs = sdlc.case_runs(_a_result(ship=[_a_run(1.0, trace)]))
    assert sdlc._keep_traces(run, tmp_path, runs, "", keep=False) == [outside.as_posix()]
    assert outside.is_dir()
    outside.chmod(0o700)
    (outside / "sealed").chmod(0o700)


def test_a_runs_summary_reads_verdicts_or_its_result(tmp_path: Path) -> None:
    """156 R10: a run's summary takes its confirmed failures from its record's verdicts, and
    from `result.json` for a run made before there were any."""
    old = tmp_path / "cases-2026-11-01-1"
    old.mkdir()
    (old / "result.json").write_text(json.dumps(_a_result(ship=[_a_run(0.5)])), encoding="utf-8")
    (old / "scope.json").write_text(json.dumps({"scope": "change"}), encoding="utf-8")
    assert (sdlc._run_summary(old)["passed"], sdlc._run_summary(old)["failed"]) == (False, ["ship"])
    new = tmp_path / "cases-2026-11-18-1"
    new.mkdir()
    (new / "result.json").write_text(json.dumps(_a_result(ship=[_a_run(0.5)])), encoding="utf-8")
    record = {"scope": "change", "verdicts": {"ship": {"result": "passed on rerun"}},
              "failed": [], "environment": [], "passed_on_rerun": ["ship"]}  # fmt: skip
    (new / "scope.json").write_text(json.dumps(record), encoding="utf-8")
    assert (sdlc._run_summary(new)["passed"], sdlc._run_summary(new)["failed"]) == (True, [])


def test_full_runs_are_kept_in_order(tmp_path: Path, monkeypatch) -> None:
    """156 R18: every full run, oldest first, with its date, Claude Code version, cost and each
    case's score and verdict, for release to set the last beside the one before."""
    monkeypatch.setattr(sdlc, "_own_repo", lambda home: True)
    monkeypatch.setattr(sdlc, "main_root", lambda root: tmp_path)
    (tmp_path / "evals" / "ship").mkdir(parents=True)
    (tmp_path / "evals" / "ship" / "prompt.md").write_text("x", encoding="utf-8")
    reports = tmp_path / sdlc.REPORTS
    for name, scope, result, verdicts in [
        ("cases-2026-11-02-1", "full", _a_result(4.0, ship=[_a_run(0.5)] * 3), None),
        ("cases-2026-11-10-1", "change", _a_result(1.0, ship=[_a_run(1.0)]), None),
        (
            "cases-2026-11-10-2",
            "full",
            _a_result(6.0, ship=[_a_run(1.0)] * 3),
            {"ship": {"result": "passed"}},
        ),
    ]:
        (reports / name).mkdir(parents=True)
        (reports / name / "result.json").write_text(json.dumps(result), encoding="utf-8")
        record = {"scope": scope, **({"verdicts": verdicts, "failed": []} if verdicts else {})}
        (reports / name / "scope.json").write_text(json.dumps(record), encoding="utf-8")
    history = sdlc._cases_report(tmp_path, None)["full_history"]
    assert [h["run"] for h in history] == ["cases-2026-11-02-1", "cases-2026-11-10-2"]
    assert history[0] == {
        "run": "cases-2026-11-02-1", "date": "2026-11-02", "claude": "2.1.311", "cost_usd": 4.0,
        "cases": [{"case": "ship", "score": 0.5, "result": "failed"}],
    }  # fmt: skip
    assert history[1]["cases"] == [{"case": "ship", "score": 1.0, "result": "passed"}]
