"""The gate: `gate` and its records, a build starting current (`fresh`), gates sharing the
machine's slots, and `check`.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Each test builds a scratch repo
on a change branch with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from factory_helpers import (
    EVIDENCE,
    FACTORY_PY,
    FULL,
    INTENT,
    NAME,
    ROOT,
    _build_report,
    _change,
    _commit_on_main,
    _escalated,
    _files,
    _fixed,
    _from_main,
    _gate,
    _gate_config,
    _git,
    _load,
    _main_moves,
    _on_main,
    _round,
    _run,
    _verdicts,
    _verified,
    factory,
    needs_uv,
    sdlc,
)

# ---------------------------------------------------------------- the gate


def test_the_gate_runs_the_base_branchs_check_and_records_each_attempt(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """R1–R4: the base branch's command, never the checkout's; each attempt appended, the first
    line the latest; a red gate is a fix for the same builder, appended to the round's report,
    and the fixed build is gated again before any review."""
    root = _change(tmp_path)
    _gate_config(root, 'echo base-ran; test -z "$FAKE_GATE_FAIL"')
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "echo mine"\n')
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"]) == ("gate", 1) and out["gate"]["current"] is None

    monkeypatch.setenv("FAKE_GATE_FAIL", "1")
    code, out = _gate(root, capsys)
    assert code == 1 and (out["verdict"], out["attempt"], out["exit"]) == ("FAIL", 1, "1")
    record = (folder / "build" / "round-1.gate.md").read_text(encoding="utf-8")
    assert record.startswith("GATE: FAIL\n") and "    base-ran" in record and "mine" not in record
    out = _verdicts(root, capsys)
    assert (out["next"], out["gate"]["fails"]) == ("fix", 1), "no reviewer on a red build"

    (folder / "runs").mkdir()
    (folder / "runs" / "builder.sessions").write_text("builder-1\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "fix", None, None)
    assert code == 0 and out["to"].endswith("build/round-1.md"), out
    argv = claude()[-1]["argv"]
    assert "The gate failed on round 1" in argv[1] and argv[-2:] == ["--resume", "builder-1"]
    report = (folder / "build" / "round-1.md").read_text(encoding="utf-8")
    assert report.startswith("Built slice 1.") and "the report" in report, "added, not replaced"
    assert _verdicts(root, capsys)["next"] == "gate", "a fixed build is gated again"

    monkeypatch.delenv("FAKE_GATE_FAIL")
    code, out = _gate(root, capsys)
    assert code == 0 and (out["verdict"], out["attempt"]) == ("PASS", 2)
    record = (folder / "build" / "round-1.gate.md").read_text(encoding="utf-8")
    assert record.startswith("GATE: PASS\n") and record.count("## Attempt ") == 2
    assert [a["verdict"] for a in factory.run_state.read_gate(folder, 1)["attempts"]] == [
        "FAIL",
        "PASS",
    ]
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["missing"]) == ("review", 1, FULL)


def test_every_gate_attempt_records_its_slot_wait(tmp_path, capsys) -> None:
    """175 R3: each attempt carries `Waited:` right after `Seconds:`, the wait `gate_slot()`
    yielded (0.0 for none), read back by the core's copy; a landing gate's record too."""
    root = _change(tmp_path)
    _gate_config(root, "echo ok")
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1)
    assert _gate(root, capsys)[0] == 0
    assert _gate(root, capsys)[0] == 0
    lines = (folder / "build" / "round-1.gate.md").read_text(encoding="utf-8").splitlines()
    seconds = [i for i, line in enumerate(lines) if factory.SECONDS_RE.match(line)]
    assert len(seconds) == 2, lines
    assert all(factory.WAITED_RE.match(lines[i + 1]) for i in seconds), lines
    assert sum(bool(factory.WAITED_RE.match(line)) for line in lines) == 2
    assert lines[seconds[0] + 1] == "Waited: 0.0"


def test_the_gate_records_no_path_of_this_machine(tmp_path, capsys, monkeypatch) -> None:
    """087: `claude plugin validate` prints its manifests' absolute paths and `pytest -n auto` a
    failing worker's venv, and the record is committed with the change, so the checkout reads
    `<path-to-clone>` and the home directory `<home>`. Home holds the checkout here: the checkout
    is written first, so it never reads `<home>/…`."""
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _change(tmp_path)
    _gate_config(
        root,
        'echo "Validating marketplace manifest: $PWD/.claude-plugin/marketplace.json"; '
        'echo "[gw0] crashed under $HOME/.cache/uv/venv"; exit 1',
    )
    _build_report(root, 1)
    code, out = _gate(root, capsys)
    assert code == 1 and (out["verdict"], out["exit"]) == ("FAIL", "1")
    folder = root / ".sdlc" / "work" / NAME
    record = (folder / "build" / "round-1.gate.md").read_text(encoding="utf-8")
    for path in {str(root), str(root.resolve()), str(tmp_path), str(tmp_path.resolve())}:
        assert path not in record, path
    assert "    Validating marketplace manifest: <path-to-clone>/.claude-plugin/" in record
    assert "    [gw0] crashed under <home>/.cache/uv/venv" in record
    assert [
        (a["verdict"], a["exit"]) for a in factory.run_state.read_gate(folder, 1)["attempts"]
    ] == [("FAIL", "1")]


def test_the_gate_records_no_temp_path_or_user_name(tmp_path, capsys, monkeypatch) -> None:
    """A failing test's `tmp_path` sits under the temp directory, in pytest's `pytest-of-<login>`:
    the record reads `<tmp>`, and the login name `<user>` inside a marked path, while the same
    word in prose stays as it was printed."""
    temp = tmp_path / "T"
    temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
        monkeypatch.setenv(name, "drafter")
    monkeypatch.setenv("FAKE_TMP_PATH", f"{temp}/pytest-of-drafter/popen-gw4/test_x0")
    root = _change(tmp_path)
    _gate_config(
        root,
        'echo "tmp_path = PosixPath(\'$FAKE_TMP_PATH\')"; echo "drafter said hi"; exit 1',
    )
    _build_report(root, 1)
    code, out = _gate(root, capsys)
    assert code == 1 and out["verdict"] == "FAIL"
    record = (root / ".sdlc" / "work" / NAME / "build" / "round-1.gate.md").read_text("utf-8")
    assert "    tmp_path = PosixPath('<tmp>/pytest-of-<user>/popen-gw4/test_x0')" in record
    assert "    drafter said hi" in record
    for path in {str(temp), str(temp.resolve()), "pytest-of-drafter"}:
        assert path not in record, path
    assert factory.is_read("ls <tmp>/pytest-of-<user>/x")


def _forbidden_shapes() -> re.Pattern:
    """`tests/test_nothing_local.py`'s `PATTERNS`, the shapes the gate refuses in any record."""
    scan = _load("nothing_local_for_factory", ROOT / "tests" / "test_nothing_local.py")
    return re.compile("|".join(scan.PATTERNS), re.IGNORECASE)


def test_a_path_under_home_is_filed_in_a_form_the_scan_accepts(tmp_path, monkeypatch) -> None:
    """135: a path under the home directory but outside the clone, or a clone path that output
    cut short, keeps the directory after home: written `~/…`, it reads as a home path to the scan
    and the gate fails on a record whose change is fine."""
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _change(tmp_path)
    text = (
        f"node at {tmp_path}/.nvm/versions/node/bin/node\n"
        f"cut short: {tmp_path}/repo-but-cut/s...\n"
        f"elsewhere: {tmp_path.resolve().as_posix()}/projects/other/x.py\n"
    )
    filed = factory._placeholders(text, root)
    assert str(tmp_path) not in filed and str(tmp_path.resolve()) not in filed
    assert f"{factory.HOME_MARK}/projects/other/x.py" in filed
    assert _forbidden_shapes().search(filed) is None, filed


def test_a_path_is_marked_only_as_a_whole_path(tmp_path, monkeypatch) -> None:
    """A temp directory as short as Linux's `/tmp` is a substring of `/var/tmp` and `/tmpfoo`:
    each is left as printed, and only the temp directory itself, whole, reads `<tmp>`."""
    temp = tmp_path / "t"
    temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    root = _change(tmp_path)
    text = f"{temp}/x and {temp}, then /var{temp}/y and {temp}foo/z\n"
    filed = factory._placeholders(text, root)
    assert filed == f"<tmp>/x and <tmp>, then /var{temp}/y and {temp}foo/z\n", filed


def test_every_reply_is_filed_without_this_machine_s_paths(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """135: an agent quoting `git worktree list` names the main checkout and the change's own
    worktree, and a reply is committed with the change: the builder's report and the spec draft
    read `<path-to-clone>` and the home mark, never the path, and what the agent concluded
    stays as it said it."""
    monkeypatch.setenv("HOME", str(tmp_path))
    root, tree = _from_main(tmp_path)
    folder = tree / ".sdlc" / "work" / NAME
    quoted = (
        f"- CHANGE: scripts/x.py: keep it\n\n## Evidence\n\n$ git worktree list\n"
        f"{root.resolve()}  abc123 [main]\n{tree}  def456 [{NAME}]\n"
        f"$ which node\n{tmp_path}/.nvm/bin/node\nexit: 0\n"
    )
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "Built it.\n" + quoted)
    code, out = _run(capsys, factory.cmd_agent, tree, "008", "build", None, None)
    assert code == 0, out
    report = (tree / out["to"]).read_text(encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "---\nid: 008\n---\n\n# 008 — spec\n\n" + quoted)
    code, out = _run(capsys, factory.cmd_agent, tree, "008", "spec", None, None)
    assert code == 0, out
    draft = (folder / "runs" / "spec-draft.md").read_text(encoding="utf-8")
    for filed in (report, draft):
        for path in {str(root), str(root.resolve()), str(tree), str(tmp_path)}:
            assert path not in filed, path
        assert "<path-to-clone>  abc123 [main]\n" in filed
        assert f"<path-to-clone>  def456 [{NAME}]\n" in filed
        assert f"{factory.HOME_MARK}/.nvm/bin/node\n" in filed
        assert "- CHANGE: scripts/x.py: keep it\n" in filed
        assert _forbidden_shapes().search(filed) is None, filed


def test_a_reply_citing_its_own_change_by_number_is_filed_by_its_full_name(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """Bug 2026-11-18-42: an agent that cites its own change's folder by bare number or glob
    has it filed as the full folder name, which the gate's scan accepts; another change's number,
    a longer number, a path already named in full and a `*` followed by more of a name (nit
    2026-11-18-62) are left as the agent wrote them, but for the scan's placeholder."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    # Built from parts: written whole, each citation is the shape the scan refuses in this file.
    w, n = "work/", "008"
    reply = (
        "Built it.\n\n## Evidence\n\n"
        f"$ ls .sdlc/{w}{n}*/build\nround-1.md\nexit: 0\n"
        f"$ cat .sdlc/{w}{n}/intent.md\nid: 008\nexit: 0\n"
        f"Seen in {w}{n}, and in {w}{n}* too.\n"
        f"Already whole: {w}{NAME}/plan.md, {w}{n}9, {w}009 and {w}{n}-*.\n"
        f"Not a glob: {w}{n}*x.\n"
    )
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", reply)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    filed = (root / out["to"]).read_text(encoding="utf-8")
    assert f"$ ls .sdlc/{w}{NAME}/build\n" in filed
    assert f"$ cat .sdlc/{w}{NAME}/intent.md\n" in filed
    assert f"Seen in {w}{NAME}, and in {w}{NAME} too.\n" in filed
    assert f"Already whole: {w}{NAME}/plan.md, {w}<{n}9>, {w}<009> and {w}{n}-*.\n" in filed
    assert f"Not a glob: {w}<{n}>*x.\n" in filed, "never backtracked off its `*`"
    assert "Built it.\n\n## Evidence\n" in filed and "round-1.md\nexit: 0\n" in filed
    assert _forbidden_shapes().search(filed) is None, filed
    assert (folder / "build" / "round-1.md").is_file()


def test_the_shapes_the_factory_defuses_are_the_scan_s() -> None:
    """`DEFUSE` holds `tests/test_nothing_local.py`'s `PATTERNS`, in order: a shape the scan
    gains is one the factory writes as a placeholder too."""
    scan = _load("nothing_local_for_defuse", ROOT / "tests" / "test_nothing_local.py")
    assert [shape for shape, _ in factory.DEFUSE] == scan.PATTERNS


def test_a_record_quoting_the_tests_fixtures_is_filed_in_a_form_the_scan_accepts(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """A reply quoting a test's output names the fixtures' changes and homes, which the scan
    refuses in any committed record: each is filed as its placeholder, and the gate's own copy of
    a failing test's output too, so a red gate never makes the next one red."""
    root = _change(tmp_path)
    w = "work/"
    quoted = (
        f"E  assert '$ ls .sdlc/{w}046*/build' in report\n"
        "Cloned to /Users/"
        "someone/code/x, /home/"
        "someone/code/x and ~/"
        "code/x.\n"
        "Kept: ~/.claude/plugins/ and /Users/<name>/.\n"
    )
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "Built it.\n\n" + quoted)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    filed = (root / out["to"]).read_text(encoding="utf-8")
    assert f"$ ls .sdlc/{w}<046>*/build" in filed
    assert "/Users/<name>/code/x, /home/<name>/code/x and ~/<dir>/x" in filed
    assert "Kept: ~/.claude/plugins/ and /Users/<name>/." in filed
    assert _forbidden_shapes().search(filed) is None, filed
    (root / "quoted.txt").write_text(quoted, encoding="utf-8")
    _gate_config(root, "cat quoted.txt; exit 1")
    _gate(root, capsys)
    record = factory.gate_path(root / ".sdlc" / "work" / NAME, 1).read_text(encoding="utf-8")
    assert f"{w}<046>*" in record and _forbidden_shapes().search(record) is None, record


def test_a_reply_quoting_a_local_term_is_filed_as_a_placeholder(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """Nit 2026-11-18-72: the scan also refuses each regex in the main checkout's gitignored
    `.sdlc/terms.local`, so a reply quoting one is filed with it as `<term>`, from the change's
    own worktree, where the file has no copy. A line written by hand is named by `defuse` and
    the approver by its path and line, never the term, and `defuse` rewrites it."""
    root, tree = _from_main(tmp_path)
    folder = tree / ".sdlc" / "work" / NAME
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "terms.local").write_text("# kept out\n\n\\bstale widgets\\b\n")
    reply = "Built it for Stale Widgets.\n\n## Evidence\n\n$ grep x\nstale widgets\nexit: 0\n"
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", reply)
    code, out = _run(capsys, factory.cmd_agent, tree, "008", "build", None, None)
    assert code == 0, out
    filed = (tree / out["to"]).read_text(encoding="utf-8")
    assert "Built it for <term>.\n" in filed and "\n<term>\nexit: 0\n" in filed, filed
    assert "widgets" not in filed.lower()
    (folder / "notes.md").write_text("Seen in stale widgets first.\n", encoding="utf-8")
    assert factory.forbidden_lines(folder, tree) == ["notes.md:1"]
    code, out = _run(capsys, factory.cmd_defuse, tree, "008")
    assert code == 0 and out["changed"] == ["notes.md"] and out["left"] == [], out
    assert (folder / "notes.md").read_text(encoding="utf-8") == "Seen in <term> first.\n"
    assert "widgets" not in json.dumps(out)


def test_an_approver_s_decision_stops_on_a_folder_the_scan_would_refuse(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """The approver ends a build: a line the scan refuses anywhere in the folder, written by
    hand or filed before the rule, stops the change then, naming the file and line and the
    command that rewrites it, never at the landing's gate."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    (folder / "notes.md").write_text("Seen in work/" + "046 first.\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "DECISION: READY\n\n**Why.** Fine.\n")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "approve", None, None)
    assert code == 1 and "notes.md:1" in out["problem"], out
    assert "factory.py defuse 008" in out["problem"] and "046" not in out["problem"]
    assert (folder / "decision.md").is_file()
    code, out = _run(capsys, factory.cmd_defuse, root, "008")
    assert code == 0 and out["changed"] == ["notes.md"] and out["left"] == [], out
    assert (folder / "notes.md").read_text(encoding="utf-8") == "Seen in work/<046> first.\n"
    assert factory.forbidden_lines(folder) == []
    (folder / "decision.md").unlink()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "approve", None, None)
    assert code == 0 and "problem" not in out, out


def test_a_third_red_gate_in_a_round_is_a_stop(tmp_path, capsys) -> None:
    """R5: two fixes a round; the third red gate stops the change, never a review."""
    root = _change(tmp_path)
    _gate_config(root, "exit 3")
    _build_report(root, 1)
    for fix in range(factory.GATE_FIXES):
        _gate(root, capsys)
        assert _verdicts(root, capsys)["next"] == "fix", fix
        _fixed(root)
    _gate(root, capsys)
    out = _verdicts(root, capsys)
    assert out["next"] == "stop"
    assert any("the gate failed 3 times in round 1: exit 3" in p for p in out["problems"])


def test_a_gate_that_changes_the_tree_or_runs_too_long_fails(tmp_path, capsys, monkeypatch):
    """R2: PASS only on exit 0, within the timeout, with the tree as the gate found it."""
    root = _change(tmp_path)
    _gate_config(root, "printf more >> README.md")
    _build_report(root, 1)
    code, out = _gate(root, capsys)
    assert code == 1 and out["exit"] == "0" and out["tree"] == "changed: README.md"
    _gate_config(root, "exec sleep 5")
    monkeypatch.setattr(factory, "GATE_TIMEOUT", 0.5)
    code, out = _gate(root, capsys)
    assert code == 1 and out["exit"] == "timeout" and out["attempt"] == 2


def test_with_no_gate_the_build_goes_to_review(tmp_path, capsys) -> None:
    """R6: no `[commands] check` on the base branch, no step and no file, and why."""
    root = _change(tmp_path)
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert out["next"] == "review" and out["gate"] is None and "[commands] check" in out["gate_why"]
    code, out = _gate(root, capsys)
    assert code == 1 and "no [commands] check" in out["refusals"][0]
    assert not (root / ".sdlc" / "work" / NAME / "build" / "round-1.gate.md").exists()


def test_the_light_depth_is_gated_too(tmp_path, capsys) -> None:
    """R7: a diff touching no sensitive path runs light, and its build is gated all the same."""
    root = _change(tmp_path)
    _gate_config(root, "true", '[review]\nsensitive = ["secrets/"]\n')
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["next"]) == ("light", "gate")


def test_a_reviewed_round_is_never_gated_after_the_fact(tmp_path, capsys) -> None:
    """R14: a run from before the gate, its round reviewed with no gate file, reads as it did."""
    root = _change(tmp_path)
    _gate_config(root, "true")
    _round(root, 1, code="CHANGES")
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"]) == ("arbitrate", 1) and out["problems"] == []


def test_close_counts_the_red_gates_only_for_a_run_that_had_one(tmp_path, capsys) -> None:
    """R10: `gate_fail` from the committed gate files reaches `Sdlc-Rework`; a run with no gate
    file says nothing, never 0, so an old trailer reads as unknown."""
    metrics = sdlc.metrics
    root = _change(tmp_path)
    _gate_config(root, "test -f fixed.txt")
    _round(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "decision.md").write_text("DECISION: READY\n\nAll pass.\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "built, no gate yet")
    assert "gate_fail" not in sdlc.closing._factory_files(root, NAME)
    _gate(root, capsys)
    (root / "fixed.txt").write_text("ok\n", encoding="utf-8")
    _fixed(root)
    _gate(root, capsys)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "gated")
    found = sdlc.closing._factory_files(root, NAME)
    assert found["gate_fail"] == 1 and found["rounds"] == 1, "the gate file is no review round"
    done = metrics.rework([], {}, found, None, 2)
    assert done["gate_fail"] == 1
    assert any("gate_fail=1" in line for line in metrics.in_change_trailers(done, {}, None))
    old = {k: v for k, v in found.items() if k != "gate_fail"}
    assert "gate_fail" not in metrics.rework([], {}, old, None, 2)


def test_a_fix_is_refused_unless_the_gate_is_red(tmp_path, capsys, claude) -> None:
    root = _change(tmp_path)
    _gate_config(root, "true")
    _build_report(root, 1)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "fix", None, None)
    assert code == 1 and "verdicts says 'gate'" in out["refusals"][0] and not claude()


def test_measuring_reads_which_sessions_were_the_factorys_agents(tmp_path) -> None:
    root = _change(tmp_path)
    runs = root / ".sdlc" / "work" / NAME / "runs"
    runs.mkdir()
    (runs / "builder.sessions").write_text("s-1\ns-2\n", encoding="utf-8")
    (runs / "reviewer-code.sessions").write_text("s-3\n", encoding="utf-8")
    (runs / "reviewer-ui.sessions").write_text("s-4\n", encoding="utf-8")
    (runs / "reviewer-ux.sessions").write_text("s-5\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the run")
    found = sdlc.closing._agent_sessions(root, NAME, f".sdlc/work/{NAME}")
    assert found == {"s-1": "builder", "s-2": "builder", "s-3": "reviewer-code",
                     "s-4": "reviewer-ui", "s-5": "reviewer-ux"}  # fmt: skip


def test_a_resolver_session_is_its_own_role(tmp_path) -> None:
    """149 R12: a session in `runs/resolver.sessions` is named `resolver`, never `builder`."""
    root = _change(tmp_path)
    runs = root / ".sdlc" / "work" / NAME / "runs"
    runs.mkdir()
    (runs / "builder.sessions").write_text("s-1\n", encoding="utf-8")
    (runs / "resolver.sessions").write_text("s-2\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the run")
    found = sdlc.closing._agent_sessions(root, NAME, f".sdlc/work/{NAME}")
    assert found == {"s-1": "builder", "s-2": "resolver"}


def test_ready_lists_what_can_ship_in_the_order_to_ship_it(tmp_path, capsys) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    changes = (
        ("009-second", "[008]", "test"),
        ("008-first", "", "test"),
        ("010-busy", "", "build"),
    )
    for name, deps, stage in changes:
        tree = tmp_path / name
        _git(root, "worktree", "add", "-q", "-b", name, str(tree), "main")
        folder = tree / ".sdlc" / "work" / name
        folder.mkdir(parents=True)
        text = INTENT.format(tier=2, stage=stage).replace("idea:\n", f"idea:\ndepends_on: {deps}\n")
        (folder / "intent.md").write_text(text, encoding="utf-8")
        (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
        (tree / "README.md").write_text(f"{name} edits this\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_ready, root)
    assert code == 0
    assert [r["change"] for r in out["ready"]] == ["008-first", "009-second"], "010 isn't ready"
    first, second = out["ready"]
    assert second["depends_on"] == ["008"] and first["overlaps"] == ["009-second"]
    assert first["cost"]["usd"] == 0.0 and first["cost"]["runs"] == 0, "no runs recorded yet"


def test_ready_leaves_a_stopped_run_out(tmp_path, capsys) -> None:
    """R13: a stopped run sits at `stage: build`, its record or not, and is never ready."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    tree = tmp_path / NAME
    _git(root, "worktree", "add", "-q", "-b", NAME, str(tree), "main")
    folder = tree / ".sdlc" / "work" / NAME
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT.format(tier=2, stage="build"), encoding="utf-8")
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    (folder / "runs").mkdir()
    (folder / factory.STOPPED).write_text(
        factory.stop_text(NAME, "rerun", ["a problem"]), encoding="utf-8"
    )
    code, out = _run(capsys, factory.cmd_ready, root)
    assert code == 0 and out["ready"] == []


# ---------------------------------------------------------------- a build starts current (101)


def _behind(tmp_path: Path, slug: str = "fresh") -> tuple[Path, Path]:
    """A host repo and a change made by `sdlc.py new --worktree`, its folder uncommitted, as
    `/sdlc:intent` leaves one: (main checkout, the change's worktree)."""
    root = tmp_path / "host"
    root.mkdir(parents=True)
    (root / "README.md").write_text("one\ntwo\nthree\n", encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    code, _, said = factory._sdlc(["new", slug, "--tier", "2", "--worktree"], root)
    assert code == 0, said
    tree = next(p for p in (root / ".claude" / "worktrees").iterdir() if p.name.endswith(slug))
    return root, tree


def _no_stash_or_merge(root: Path) -> None:
    assert _git(root, "stash", "list") == "", "never a stash"
    assert _git(root, "rev-list", "--merges", "--all") == "", "never a merge"


@needs_uv
def test_fresh_fast_forwards_a_change_behind_the_base(tmp_path, capsys) -> None:
    """101 R2: a change with no commits of its own, two behind, moves onto `main`'s tip through
    `sdlc.py base`, its uncommitted folder carried across byte for byte, with the undo."""
    root, tree = _behind(tmp_path)
    folder = tree / ".sdlc" / "work" / tree.name
    _commit_on_main(root, "one.txt", "1\n")
    _commit_on_main(root, "two.txt", "2\n")
    before, files = _git(tree, "rev-parse", "HEAD"), _files(folder)
    code, out = _run(capsys, factory.cmd_fresh, tree, "001")
    assert (code, out["state"], out["behind"]) == (0, "fast-forwarded", 2), out
    assert _git(tree, "rev-parse", "HEAD") == _git(root, "rev-parse", "main")
    assert before.startswith(out["from"]) and out["head"] == _git(tree, "rev-parse", "--short",
                                                                  "HEAD")  # fmt: skip
    assert f"reset --keep {before}" in out["undo"] and out["refusals"] == []
    assert _files(folder) == files, "the change's folder, as it was"
    _no_stash_or_merge(root)
    code, out = _run(capsys, factory.cmd_fresh, tree, "001")
    assert (code, out["state"], out["behind"]) == (0, "current", 0), out


def test_fresh_holds_a_run_that_stopped_part_way(tmp_path, capsys, monkeypatch) -> None:
    """101 R3: at `stage: build` its rounds were gated and reviewed on the base they had, so
    nothing moves, and `sdlc.py` isn't run at all."""
    root = _change(tmp_path, 2, "build")
    _main_moves(root, "one.txt")
    monkeypatch.setattr(factory, "_sdlc", lambda *a: pytest.fail("held: nothing to run"))
    head = _git(root, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert (code, out["state"], out["behind"]) == (0, "held", 1), out
    assert "landing rebases and gates it again" in out["reason"]
    assert _git(root, "rev-parse", "HEAD") == head and out["head"] == out["from"]


def test_fresh_refuses_a_stage_no_fresh_run_starts_from(tmp_path, capsys, monkeypatch) -> None:
    root = _change(tmp_path, 2, "test")
    monkeypatch.setattr(factory, "_sdlc", lambda *a: pytest.fail("refused: nothing to run"))
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert (code, out["state"]) == (1, "refused") and "no decision.md" in out["refusals"][0]
    root = _change(tmp_path / "b", 1, "design")
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert code == 1 and "tier 1 at stage: design" in out["refusals"][0], out
    root = _change(tmp_path / "c", 2, "test")
    _escalated(root)
    ran = []
    monkeypatch.setattr(factory, "_sdlc", lambda args, cwd: ran.append(args) or (
        0, {"action": "current", "undo": None}, ""))  # fmt: skip
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert (code, out["state"], ran) == (0, "current", [["base", NAME]]), "a restart starts fresh"


@needs_uv
def test_fresh_resolves_what_git_can_and_stops_on_a_real_conflict(tmp_path, capsys) -> None:
    """101 R4: (a) uncommitted work `main` then changes differently: `resolve` meets a real
    conflict, `fresh` aborts it and refuses, the worktree as it found it; (b) a commit of its own
    and uncommitted work, `main` changing another file: resolved, the work still uncommitted."""
    root, tree = _behind(tmp_path / "a")
    folder = tree / ".sdlc" / "work" / tree.name
    (tree / "README.md").write_text("the change's one\ntwo\nthree\n", encoding="utf-8")
    _commit_on_main(root, "README.md", "main's one\ntwo\nthree\n")
    head, files, status = _git(tree, "rev-parse", "HEAD"), _files(folder), _git(tree, "status")
    code, out = _run(capsys, factory.cmd_fresh, tree, "001")
    assert (code, out["state"]) == (1, "refused"), out
    assert "README.md" in out["refusals"][0] and "/sdlc:ship" in out["refusals"][0]
    assert _git(tree, "rev-parse", "HEAD") == head and out["head"] == out["from"]
    assert (tree / "README.md").read_text(encoding="utf-8") == "the change's one\ntwo\nthree\n"
    assert _files(folder) == files and _git(tree, "status") == status
    _no_stash_or_merge(root)

    root, tree = _behind(tmp_path / "b")
    (tree / "mine.txt").write_text("a commit of its own\n", encoding="utf-8")
    _git(tree, "add", "mine.txt")
    _git(tree, "commit", "-q", "-m", "the change's own")
    (tree / "README.md").write_text("the change's one\ntwo\nthree\n", encoding="utf-8")
    _commit_on_main(root, "other.txt", "elsewhere\n")
    code, out = _run(capsys, factory.cmd_fresh, tree, "001")
    assert (code, out["state"]) == (0, "resolved"), out
    assert "--abort" in out["undo"]
    main = _git(root, "rev-parse", "main")
    assert _git(tree, "rev-parse", "HEAD^") == main, "its own commit, onto main's tip"
    assert (tree / "README.md").read_text(encoding="utf-8").startswith("the change's one")
    assert "README.md" in _git(tree, "status", "--porcelain"), "the work still uncommitted"
    _no_stash_or_merge(root)


def test_fresh_refuses_without_its_own_sdlc(tmp_path, capsys, monkeypatch) -> None:
    """101 R5: no `sdlc.py` of the factory's version, and nothing moves."""
    root = _change(tmp_path, 2, "design")
    _main_moves(root, "one.txt")
    monkeypatch.setattr(factory, "sdlc_path", lambda *a: (None, "no sdlc 9.9 beside this factory"))
    head = _git(root, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert (code, out["state"]) == (1, "refused") and "no sdlc 9.9" in out["refusals"][0], out
    assert _git(root, "rev-parse", "HEAD") == head


# ---------------------------------------------------------------- gates share the machine (101)
# A gate that stamps when it starts and ends, from the worktree it runs in, and takes a second.
STAMP = (
    "import os, sys, time\n"
    "with open(sys.argv[2], 'a', encoding='utf-8', newline='\\n') as f:\n"
    "    f.write(f'{os.path.basename(os.getcwd())} {sys.argv[1]} {time.time()}\\n')\n"
)


def _second_change(root: Path, tmp_path: Path) -> Path:
    """Another change, `009-other`, in its own worktree of `root`'s repo, with a build report."""
    tree = tmp_path / "other"
    _git(root, "worktree", "add", "-q", "-b", "009-other", str(tree), "main")
    folder = tree / ".sdlc" / "work" / "009-other"
    (folder / "build").mkdir(parents=True)
    text = INTENT.format(tier=2, stage="build").replace("008", "009")
    (folder / "intent.md").write_text(text.replace("reopen-drafts", "other"), encoding="utf-8")
    (folder / "build" / "round-1.md").write_text("Built.\n" + EVIDENCE, encoding="utf-8")
    return tree


@pytest.mark.parametrize("jobs", [1, 2])
def test_two_gates_with_a_limit_of_one_run_one_after_the_other(tmp_path, jobs) -> None:
    """101 R8, R9: two changes' gates started at once in two worktrees. With `gate_jobs = 1` the
    second waits for the first's slot, says so, and its wait isn't in its time; with 2 they run
    side by side, so the limit is what orders them."""
    root = _change(tmp_path)
    log, stamp = tmp_path / "stamps.log", tmp_path / "stamp.py"
    stamp.write_text(STAMP, encoding="utf-8")
    py = Path(sys.executable).as_posix()
    run = f'"{py}" "{stamp.as_posix()}" {{}} "{log.as_posix()}"'
    _gate_config(root, f"{run.format('start')} && sleep 1 && {run.format('end')}")
    _on_main(root, f"gate_jobs = {jobs}\n")
    _build_report(root, 1)
    other = _second_change(root, tmp_path)
    gates = [
        subprocess.Popen([sys.executable, str(FACTORY_PY), "gate", ident], cwd=tree,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        for tree, ident in ((root, "008"), (other, "009"))
    ]  # fmt: skip
    done = [g.communicate(timeout=60) for g in gates]
    assert [g.returncode for g in gates] == [0, 0], done
    outs = [json.loads(out) for out, _ in done]
    times: dict[str, dict[str, float]] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        where, what, when = line.split()
        times.setdefault(where, {})[what] = float(when)
    (a, b) = times.values()
    overlap = a["start"] < b["end"] and b["start"] < a["end"]
    waiting = [err for _, err in done if "waiting for a gate slot" in err]
    if jobs == 1:
        assert not overlap, times
        assert len(waiting) == 1 and "(1 of 1 in use)" in waiting[0], done
        waited = max(outs, key=lambda o: o["waited"])
        assert waited["waited"] >= 0.5 and waited["seconds"] < 1.8, outs
        assert min(o["waited"] for o in outs) == 0.0
    else:
        assert overlap, times
        assert not waiting and [o["waited"] for o in outs] == [0.0, 0.0], done


HOLD = """\
import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("factory_child", sys.argv[1])
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)
with factory.gate_slot(Path(sys.argv[2]), 1, "008-reopen-drafts") as (slot, waited):
    print(f"held {slot}", flush=True)
    time.sleep(60)
"""


@pytest.mark.portable
def test_a_killed_gate_frees_its_slot(tmp_path) -> None:
    """101 R10: a slot is a lock on an open descriptor, so the OS frees it however its gate ends,
    and the next gate takes it at once."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    child = subprocess.Popen(
        [sys.executable, "-c", HOLD, str(FACTORY_PY), str(root)],
        stdout=subprocess.PIPE, encoding="utf-8",
    )  # fmt: skip
    try:
        assert child.stdout.readline().strip() == "held 0"
        lock = Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        lock = lock / "sdlc-factory-gate-0.lock"
        fd = os.open(lock, os.O_RDWR)
        try:
            assert not factory._try_lock(fd), "held while its gate runs"
        finally:
            os.close(fd)
    finally:
        child.kill()
        child.wait()
    import time

    start = time.monotonic()
    with factory.gate_slot(root, 1, NAME) as (slot, waited):
        assert slot == 0
    assert time.monotonic() - start < 2, "the slot outlived its gate"
    assert lock.is_file(), "the file stays; only the lock goes"


# A child that holds slot 0 through `sdlc.py`'s `_hand_slot()`, the hand gate's, until killed.
HOLD_HAND = """\
import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("sdlc_child", sys.argv[1])
sdlc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdlc)
with sdlc._hand_slot(Path(sys.argv[2]), 1, "009-other", 60) as (slot, waited):
    print(f"held {slot}", flush=True)
    time.sleep(60)
"""


def test_a_factory_gate_waits_for_a_hand_gates_slot(tmp_path) -> None:
    """113 R2: a slot `sdlc.py gate` holds is one the factory's gate waits for, and takes once
    the hand gate ends."""
    import time

    root = _change(tmp_path)
    _gate_config(root, "true")
    _build_report(root, 1)
    child = subprocess.Popen(
        [sys.executable, "-c", HOLD_HAND, str(ROOT / "scripts" / "sdlc.py"), str(root)],
        stdout=subprocess.PIPE, encoding="utf-8",
    )  # fmt: skip
    try:
        assert child.stdout.readline().strip() == "held 0"
        gate = subprocess.Popen(
            [sys.executable, str(FACTORY_PY), "gate", "008"], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
        )  # fmt: skip
        line = gate.stderr.readline()
        assert f"{NAME}: waiting for a gate slot (1 of 1 in use)" in line, line
        time.sleep(0.6)
    finally:
        child.kill()
        child.wait()
    out, err = gate.communicate(timeout=60)
    assert gate.returncode == 0, (out, err)
    got = json.loads(out)
    assert got["waited"] >= 0.5 and got["slot"] == 0, got


# ---------------------------------------------------- agents' full runs take a slot too (155)


def test_check_runs_the_base_branchs_command_and_exits_with_its_code(tmp_path, capfd) -> None:
    """155 R1: the base branch's `[commands] check`, never the checkout's, its output straight
    through and its exit code the command's."""
    root = _change(tmp_path)
    _gate_config(root, "echo base-ran; exit 3")
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "echo mine"\n')
    code = factory.cmd_check(root, "008")
    out = capfd.readouterr().out
    assert code == 3 and "base-ran" in out and "mine" not in out, out


@pytest.mark.parametrize("case", ["no base", "no check", "no change"])
def test_check_refuses_and_runs_nothing(tmp_path, capfd, case) -> None:
    """155 R2: no base branch, no `[commands] check` on it, or no such change: a refusal, in
    `gate`'s words, and the command never runs."""
    root = _change(tmp_path)
    stamp = tmp_path / "ran"
    if case != "no check":
        _gate_config(root, f'touch "{stamp.as_posix()}"')
    if case == "no base":
        _git(root, "branch", "-q", "-m", "main", "trunk")
    ident = "099" if case == "no change" else "008"
    code = factory.cmd_check(root, ident)
    out = json.loads(capfd.readouterr().out)
    assert code == 1 and out["refusals"], out
    why = {"no base": "no base branch", "no check": "has no [commands] check", "no change": "099"}
    assert why[case] in out["refusals"][0], out
    assert not stamp.exists()


@pytest.mark.portable
def test_two_checks_with_one_slot_run_one_after_the_other(tmp_path) -> None:
    """155 R3: two `check` runs at once in two worktrees, with `gate_jobs = 1`: the second waits
    for the first's slot and says so."""
    root = _change(tmp_path)
    log, stamp = tmp_path / "stamps.log", tmp_path / "stamp.py"
    stamp.write_text(STAMP, encoding="utf-8")
    py = Path(sys.executable).as_posix()
    run = f'"{py}" "{stamp.as_posix()}" {{}} "{log.as_posix()}"'
    _gate_config(root, f"{run.format('start')} && sleep 1 && {run.format('end')}")
    _on_main(root, "gate_jobs = 1\n")
    other = _second_change(root, tmp_path)
    checks = [
        subprocess.Popen([sys.executable, str(FACTORY_PY), "check", ident], cwd=tree,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        for tree, ident in ((root, "008"), (other, "009"))
    ]  # fmt: skip
    done = [c.communicate(timeout=60) for c in checks]
    assert [c.returncode for c in checks] == [0, 0], done
    times: dict[str, dict[str, float]] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        where, what, when = line.split()
        times.setdefault(where, {})[what] = float(when)
    (a, b) = times.values()
    assert not (a["start"] < b["end"] and b["start"] < a["end"]), times
    waiting = [err for _, err in done if "waiting for a gate slot (1 of 1 in use)" in err]
    assert len(waiting) == 1, done


@pytest.mark.portable
def test_a_check_waits_for_a_gates_slot(tmp_path) -> None:
    """155 R3: a slot a gate holds is one `check` waits for: gates and checks share the slots."""
    import time

    root = _change(tmp_path)
    _gate_config(root, "echo checked")
    child = subprocess.Popen(
        [sys.executable, "-c", HOLD, str(FACTORY_PY), str(root)],
        stdout=subprocess.PIPE, encoding="utf-8",
    )  # fmt: skip
    try:
        assert child.stdout.readline().strip() == "held 0"
        check = subprocess.Popen(
            [sys.executable, str(FACTORY_PY), "check", "008"], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
        )  # fmt: skip
        line = check.stderr.readline()
        assert f"{NAME}: waiting for a gate slot (1 of 1 in use)" in line, line
        time.sleep(0.5)
        assert check.poll() is None, "it ran while the gate held the slot"
    finally:
        child.kill()
        child.wait()
    out, err = check.communicate(timeout=60)
    assert check.returncode == 0 and "checked" in out, (out, err)


def test_a_killed_check_frees_its_slot(tmp_path) -> None:
    """155 R4: the slot is a lock on `check`'s own descriptor, never inherited by the command it
    runs, so killing `check` frees it even while the command lives on. Not portable: it starts
    `check` with `start_new_session` and cleans up with `killpg`, which Windows has neither of."""
    import time

    root = _change(tmp_path)
    started = tmp_path / "started"
    _gate_config(root, f'touch "{started.as_posix()}"; sleep 30')
    check = subprocess.Popen(
        [sys.executable, str(FACTORY_PY), "check", "008"], cwd=root, start_new_session=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )  # fmt: skip
    try:
        deadline = time.monotonic() + 30
        while not started.exists():
            assert time.monotonic() < deadline, "the command never started"
            time.sleep(0.05)
        check.kill()
        check.wait()
        start = time.monotonic()
        with factory.gate_slot(root, 1, NAME) as (slot, _):
            assert slot == 0
        assert time.monotonic() - start < 2, "the slot outlived its check"
    finally:
        import contextlib
        import signal

        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(check.pid, signal.SIGKILL)


def test_a_check_past_the_timeout_is_killed(tmp_path, capfd, monkeypatch) -> None:
    """155 R4: past `GATE_TIMEOUT` the command is killed, said on stderr, and `check` fails. Not
    portable: what is killed is an `sh` that `exec`s `sleep`, whose kill CI's Windows job, where
    Git for Windows' `sh` starts `sleep` as a process of its own, can't show."""
    root = _change(tmp_path)
    _gate_config(root, "exec sleep 5")
    monkeypatch.setattr(factory, "GATE_TIMEOUT", 0.5)
    code = factory.cmd_check(root, "008")
    assert code != 0 and "timed out after 0.5s" in capfd.readouterr().err


@pytest.mark.portable
def test_a_green_check_writes_nothing_and_never_clears_the_gate(tmp_path, capfd) -> None:
    """155 R5: a green `check` writes no record, leaves the folder as it was, and `verdicts`
    still asks for the gate: the script's gate stays the one proof of the suite."""
    root = _change(tmp_path)
    _gate_config(root, "true")
    _build_report(root, 1)
    rel = ".sdlc/work/" + NAME
    assert _verdicts(root, capfd)["next"] == "gate"
    before = _git(root, "status", "--porcelain", "--untracked-files=all", "--", rel)
    capfd.readouterr()
    assert factory.cmd_check(root, "008") == 0
    assert _git(root, "status", "--porcelain", "--untracked-files=all", "--", rel) == before
    assert not list((root / rel / "build").glob("*.gate.md"))
    capfd.readouterr()
    assert _verdicts(root, capfd)["next"] == "gate"


def test_the_builders_prompts_name_the_check_command(tmp_path, capsys) -> None:
    """155 R6: every prompt the builder is sent names the full `check` command, this factory's
    own script by its absolute path; no reviewer's, arbiter's or approver's does."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    line = f"uv run --quiet --script {factory.FACTORY_SCRIPT.as_posix()} check 008"
    assert factory.FACTORY_SCRIPT.is_absolute()

    def prompt(state: dict, task: str, role: str, decided: str | None = None) -> str:
        planned = factory._task(root, folder, state, task, role, decided)
        assert not isinstance(planned, str), planned
        return planned[0]

    state, _ = factory.run_state.loop_state(root, "008", None)
    assert state["next"] == "build"
    assert line in prompt(state, "build", "builder")
    assert line in prompt({**state, "next": "fix", "round": 1}, "fix", "builder")
    _build_report(root, 1, "- DECISION: [default] Page at 50.\n")
    _run(capsys, factory.cmd_decisions, root, "008")
    path = folder / "decisions.md"
    path.write_text(path.read_text().replace("- [ ] D1", "- [x] D1").replace(
        "50.", "50. → decided: 50"))  # fmt: skip
    _round(root, 1, code="CHANGES")
    _verified(root, 1, kept=["code: code fix 1"])
    state, _ = factory.run_state.loop_state(root, "008", None)
    assert state["next"] == "rework", state
    assert line in prompt(state, "rework", "builder")
    assert line in prompt(state, "decided", "builder", "D1")
    assert line in prompt(state, "mend", "builder")
    for task, role, step in (("review", "code", "review"), ("arbitrate", "arbiter", "arbitrate"),
                             ("approve", "approver", "approve")):  # fmt: skip
        told = prompt({**state, "next": step, "missing": ["code"]}, task, role)
        assert "check 008" not in told, (task, told)


def test_a_landing_verifiers_answer_names_its_landing_round(tmp_path) -> None:
    """111: a problem in a landing round's `verified.md` names the round `land-<n>`, as its file
    does, and a build round's names it `round <n>`."""
    reviews = {"code": {"verdict": "CHANGES", "changes": ["src/a.py:2: name it"]}}
    for kind, label in (("land", "land-1"), ("round", "round 1")):
        where = tmp_path / kind / "reviews" / f"{kind}-1"
        where.mkdir(parents=True)
        (where / "verified.md").write_text(
            "- KEPT: code: C9: made up\n- KEPT: code: src/b.py:1: reworded\n", encoding="utf-8"
        )
        _, problems = factory.read_verified(where / "verified.md", 1, reviews)
        assert f"C9, which no change of {label} is" in problems[1], problems
        assert f"reworded, which no review of {label} asks for" in problems[2], problems
