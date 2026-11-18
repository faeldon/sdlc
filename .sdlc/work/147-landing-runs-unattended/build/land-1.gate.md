GATE: FAIL

## Attempt 1

Verdict: FAIL
Command: ./check.sh
Build: 81e3c68c627efa52
Exit: 1
Seconds: 117.8
Tree: unchanged

Last 80 lines of its output:

    ........................................................................ [ 10%]
    ........................................................................ [ 12%]
    ........................................................................ [ 15%]
    ........................................................................ [ 17%]
    ................ss...................................................... [ 20%]
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
    ........................................................................ [ 47%]
    ........................................................................ [ 50%]
    .....................................................................F.. [ 52%]
    ........................................................................ [ 55%]
    ........................................................................ [ 57%]
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
    ...........................................F....                         [100%]
    =================================== FAILURES ===================================
    ____________________ test_nothing_in_the_repo_is_forbidden _____________________
    [gw5] darwin -- Python 3.12.12 <path-to-clone>/.claude/worktrees/147-landing-runs-unattended/.venv/bin/python
    
        def test_nothing_in_the_repo_is_forbidden() -> None:
    >       assert forbidden(ROOT, main_checkout() / LOCAL) == []
    E       AssertionError: assert ['.sdlc/work/...x/build', ...] == []
    E         
    E         Left contains 15 more items, first extra item: '.sdlc/work/144-factory-records-and-models/entries.md:9: ## [2026-11-18-62] [nit] `work/<008>*x` is rewritten to `work/008-slug*x`, because the regex backtracks off the `*` and the lookahead then passes on `*`.'
    E         Use -v to get more diff
    
    tests/test_nothing_local.py:112: AssertionError
    _________________ test_a_resolution_leaves_the_worktree_clean __________________
    [gw14] darwin -- Python 3.12.12 <path-to-clone>/.claude/worktrees/147-landing-runs-unattended/.venv/bin/python
    
    tmp_path = PosixPath('<tmp>/pytest-of-<user>/pytest-3931/popen-gw14/test_a_resolution_leaves_the_w0')
    capsys = <_pytest.capture.CaptureFixture object at 0x10b93e8a0>
    
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
    FAILED tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden - A...
    FAILED tests/test_train.py::test_a_resolution_leaves_the_worktree_clean - Ass...
    2 failed, 2826 passed, 28 skipped in 117.57s (0:01:57)
