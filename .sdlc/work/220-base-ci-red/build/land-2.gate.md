GATE: FAIL

## Attempt 1

Verdict: FAIL
Command: ./check.sh
Build: 57c0b6ed11ada38f
Exit: 1
Seconds: 240.0
Waited: 0.0
Tree: unchanged

Last 80 lines of its output:

    ........................................................................ [ 44%]
    ........................................................................ [ 46%]
    ........................................................................ [ 48%]
    ........................................................................ [ 50%]
    ........................................................................ [ 51%]
    ........................................................................ [ 53%]
    ........................................................................ [ 55%]
    ........................................................................ [ 57%]
    ........................................................................ [ 59%]
    ........................................................................ [ 60%]
    ........................................................................ [ 62%]
    ........................................................................ [ 64%]
    ........................................................................ [ 66%]
    ........................................................................ [ 67%]
    ........................................................................ [ 69%]
    ........................................................................ [ 71%]
    ........................................................................ [ 73%]
    ........................................................................ [ 75%]
    ........................................................................ [ 76%]
    ........................................................................ [ 78%]
    ........................................................................ [ 80%]
    ........................................................................ [ 82%]
    ........................................................................ [ 84%]
    ........................................................................ [ 85%]
    ........................................................................ [ 87%]
    ........................................................................ [ 89%]
    ........................................................................ [ 91%]
    ........................................................................ [ 93%]
    ........................................................................ [ 94%]
    ........................................................................ [ 96%]
    ........................................................................ [ 98%]
    ......................................................s..........        [100%]
    =================================== FAILURES ===================================
    _________________________ test_every_signal_has_a_kind _________________________
    [gw4] darwin -- Python 3.12.12 <path-to-clone>/.claude/worktrees/220-base-ci-red/.venv/bin/python
    
    tmp_path = PosixPath('<tmp>/pytest-of-<user>/pytest-5531/popen-gw4/test_every_signal_has_a_kind0')
    capsys = <_pytest.capture.CaptureFixture object at 0x106c05fd0>
    monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x106c05640>
    
        def test_every_signal_has_a_kind(tmp_path, capsys, monkeypatch) -> None:
            """R25: every string `land_signals()` gives comes with its kind, in order, each one of
            `SIGNAL_KINDS`; and `land-check` prints them as `signal_kinds`."""
            root = _change(tmp_path)
            folder = root / ".sdlc" / "work" / NAME
            L = factory.landing
            cases = {"failed": [{"case": "c1", "graders": []}], "skipped": "over budget"}
            parts = {"undone": [], "nits": ["2026-11-01-1"], "cases": cases}
            monkeypatch.setattr(L, "land_parts", lambda folder, pre, root=None, cfg=None: parts)
            monkeypatch.setattr(L, "resolution_signals", lambda root, folder, cfg: ["one", "two"])
            monkeypatch.setattr(L, "nit_findings", lambda root, folder, cfg: [])
            monkeypatch.setattr(L, "read_impact", lambda folder: "major")
            _ledger(
                folder,
                DEFAULT_LINE,
                "- [x] D2 (code round 1, default): Log it? → settled by the approver: the spec says",
            )
            (folder / "build").mkdir()
            (folder / "build" / "land-1.ask.md").write_text("Rename it.\n", encoding="utf-8")
            pre = {"risk": {"sensitive": ["src/a.py"], "irreversible": ["db/1.sql"]},
                   "closes": {"closes": "12"}, "undone": {"items": [{"text": "x"}]},
                   "checks": {"checks": [{"name": "c"}]}, "cases": {"scope": ["skills/x"]}}  # fmt: skip
            kinds: list[str] = []
            signals, _ = L.land_signals(
                folder, root, "ESCALATE", {"land": {"auto": False}}, pre, unreviewed=None, kinds=kinds
            )
            assert len(kinds) == len(signals), list(zip(kinds, signals, strict=False))
            assert set(kinds) <= set(L.SIGNAL_KINDS)
    >       assert set(kinds) == set(L.SIGNAL_KINDS) - {"unread"}, "every kind reached"
    E       AssertionError: every kind reached
    E       assert {'assumed', '... 'fixed', ...} == {'assumed', '...calated', ...}
    E         
    E         Extra items in the right set:
    E         'ci'
    E         Use -v to get more diff
    
    tests/test_autopilot.py:282: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_autopilot.py::test_every_signal_has_a_kind - AssertionError...
    1 failed, 3995 passed, 29 skipped in 239.67s (0:03:59)
