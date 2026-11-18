GATE: FAIL

## Attempt 1

Verdict: FAIL
Command: ./check.sh
Build: a1e8a83cef9bcc1d
Exit: 1
Seconds: 113.7
Tree: unchanged

Last 80 lines of its output:

    ........................................................................ [ 10%]
    ........................................................................ [ 12%]
    ........................................................................ [ 15%]
    ........................................................................ [ 17%]
    ...........................................ss........................... [ 20%]
    ........................................................................ [ 22%]
    ........................................................................ [ 25%]
    ........................................................................ [ 27%]
    ........................................................................ [ 30%]
    ........................................................................ [ 32%]
    ........................................................................ [ 35%]
    ........................................................................ [ 37%]
    ........................................................................ [ 40%]
    ........................................................................ [ 42%]
    ........................................................................ [ 45%]
    ......................................F................................. [ 47%]
    ........................................................................ [ 50%]
    ........................................................................ [ 52%]
    ........................................................................ [ 55%]
    ........................................................................ [ 58%]
    ........................................................................ [ 60%]
    ........................................................................ [ 63%]
    ........................................................................ [ 65%]
    ........................................................................ [ 68%]
    ........................................................................ [ 70%]
    ........................................................................ [ 73%]
    ........................................................................ [ 75%]
    ........................................................................ [ 78%]
    ........................................................................ [ 80%]
    ........................................................................ [ 83%]
    ........................................................................ [ 85%]
    ........................................................................ [ 88%]
    ........................................................................ [ 90%]
    ........................................................................ [ 93%]
    ........................................................................ [ 95%]
    ........................................................................ [ 98%]
    ............................................F.                           [100%]
    =================================== FAILURES ===================================
    ____________________ test_nothing_in_the_repo_is_forbidden _____________________
    [gw16] darwin -- Python 3.12.12 <path-to-clone>/.claude/worktrees/147-landing-runs-unattended/.venv/bin/python
    
        def test_nothing_in_the_repo_is_forbidden() -> None:
    >       assert forbidden(ROOT, main_checkout() / LOCAL) == []
    E       assert [".sdlc/work/...l slug.', ...] == []
    E         
    E         Left contains 7 more items, first extra item: ".sdlc/work/145-escalations-that-clear/build/land-1.gate.md:66: E         Left contains 12 more items, first extra ite...*x` is rewritten to `work/008-slug*x`, because the regex backtracks off the `*` and the lookahead then passes on `*`.'"
    E         Use -v to get more diff
    
    tests/test_nothing_local.py:112: AssertionError
    _________________ test_a_resolution_leaves_the_worktree_clean __________________
    [gw2] darwin -- Python 3.12.12 <path-to-clone>/.claude/worktrees/147-landing-runs-unattended/.venv/bin/python
    
    tmp_path = PosixPath('<tmp>/pytest-of-<user>/pytest-3934/popen-gw2/test_a_resolution_leaves_the_w0')
    capsys = <_pytest.capture.CaptureFixture object at 0x10b07a120>
    
        @needs_uv
        def test_a_resolution_leaves_the_worktree_clean(tmp_path, capsys) -> None:
            """147 R14: after `resolve --continue`, the landing agent's reply and `runs/land-resolved`
            are in the rebased commit, and the worktree is clean."""
            root, trees = _conflicting(tmp_path)
            _begin(root, capsys)
            out = drive_train(factory, root, capsys, until=lambda o: o.get("next") == "resolve")[-1]
            tree, folder = trees[1], _folder(trees[1])
            reply = folder / "build" / f"land-{out['round']}.md"
            reply.parent.mkdir(exist_ok=True)
            reply.write_text("Kept both lines.\n\n## Evidence\n\n$ true\nexit: 0\n", encoding="utf-8")
            _resolving(tree, out["files"])
            code, done = _run(capsys, factory.cmd_resolve, tree, "002", True)
            assert (code, done["state"]) == (0, "resolved"), done
    >       assert _git(tree, "status", "--porcelain") == "", "nothing left uncommitted"
    E       AssertionError: nothing left uncommitted
    E       assert '?? .sdlc/wor...d-times.jsonl' == ''
    E         
    E         + ?? .sdlc/work/002-second/runs/land-times.jsonl
    
    tests/test_train.py:1106: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden - a...
    FAILED tests/test_train.py::test_a_resolution_leaves_the_worktree_clean - Ass...
    2 failed, 2824 passed, 28 skipped in 113.48s (0:01:53)
