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
# `fresh` is the base alone; every other fixture names the branch its change is on.
FIXTURES = [
    "fresh",
    *sorted(p.name for p in (EVALS / "fixtures").iterdir() if (p / "branch").is_file()),
]

pytestmark = pytest.mark.portable
SCAFFOLDS = [
    pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do"),
    pytest.mark.skipif(shutil.which("sh") is None, reason="the scaffold is sh, as _sh() is"),
]
# The cases that stop at their skill's WAIT, and the commands each must never have run before it.
STOP_CASES = {
    "intent": ["new"], "spec": [], "ship": ["ship"], "ship-open-finding": ["ship"],
    "close": ["close"], "idea": ["inbox-commit"],
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
    for never in ["commits", "pushes", "writes", "edits", *STOP_CASES[case]]:
        g = graders[f"never-{never}"]
        assert (g["min"], g["max"]) == (0, 0), f"{case}: never-{never}"
    *_, fixture, flag = (EVALS / case / "scaffold.sh").read_text(encoding="utf-8").split()
    assert fixture in FIXTURES and flag == "--sandbox", case


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
    argv = sdlc.cases_argv(tmp_path / "evals", tmp_path / "run", "change", ["intent", "ship"],
                           keep=False)  # fmt: skip
    assert argv[:4] == ["claude", "plugin", "eval", str(tmp_path / "evals")]
    tagged = argv[argv.index("--tag") + 1 : argv.index("--scaffold")]
    assert tagged == ["intent", "ship"] and "--case" not in argv, "--case takes one glob a run"
    assert argv[argv.index("--max-cost-usd") + 1] == "5" and argv[argv.index("--runs") + 1] == "1"
    assert argv[argv.index("--ablation") + 1] == "none" and "--scaffold" in argv
    granted = argv[argv.index("--allow-tools") + 1 : argv.index("--allow-tools") + 4]
    assert granted == ["Bash", "Write", "Edit"] and "--keep-temp" not in argv
    full = sdlc.cases_argv(tmp_path / "evals", tmp_path / "run", "full", ["a", "b"], keep=True)
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
