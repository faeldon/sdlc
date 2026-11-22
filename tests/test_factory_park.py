"""A change parked on a host resource (222): a host's check answers busy with `[park] exit`, the
gate parks the change in `runs/parked.md` with a deadline the host can't move, `verdicts` reads
the park against an injected clock, and every waiting state has a bound.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Each test builds a scratch repo on
a change branch with its folder, so nothing here runs an agent.
"""

from __future__ import annotations

import ast
import json
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from factory_helpers import (
    NAME,
    ROOT,
    _build_report,
    _change,
    _gate_config,
    _git,
    _on_main,
    _run,
    factory,
)

T0 = datetime(2026, 11, 21, 15, 0, 0, tzinfo=UTC)
BUSY = 'printf "SDLC-BUSY-RESOURCE: staging db\\nSDLC-BUSY-HOLDER: 219-other\\n"; exit 75'
PARK = "[park]\nexit = 75\n"


def _stamp(when: datetime) -> str:
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def _at(monkeypatch, when: datetime) -> None:
    monkeypatch.setattr(factory, "_clock", lambda: when)


def _parked(root: Path) -> Path:
    return root / ".sdlc" / "work" / NAME / factory.PARKED


def _gate_file(root: Path, n: int = 1) -> Path:
    return root / ".sdlc" / "work" / NAME / "build" / f"round-{n}.gate.md"


def _busy_change(tmp_path: Path, command: str = BUSY, park: str = PARK) -> Path:
    root = _change(tmp_path)
    _gate_config(root, command)
    if park:
        _on_main(root, park)
    _build_report(root, 1)
    return root


def _gate(root, capsys) -> tuple[int, dict]:
    return _run(capsys, factory.cmd_gate, root, "008")


def _verdicts(root, capsys, now: datetime, head=None, record=False) -> dict:
    return _run(capsys, factory.cmd_verdicts, root, "008", head, record, now)[1]


# ---------------------------------------------------------------- the signal (R1, R3)


def test_a_busy_code_without_park_exit_is_a_red_gate(tmp_path, capsys) -> None:
    """R1: with no `[park]` on the base branch, exit 75 is a red gate like any other."""
    root = _busy_change(tmp_path, park="")
    code, out = _gate(root, capsys)
    assert code == 1 and out["verdict"] == "FAIL" and out["exit"] == "75", out
    assert _gate_file(root).read_text(encoding="utf-8").startswith("GATE: FAIL\n")
    assert not _parked(root).exists()


def test_a_busy_code_in_the_checkouts_own_factory_toml_is_not_read(tmp_path, capsys) -> None:
    """R1: `[park]` is the base branch's alone, and the checkout's own copy is warned about."""
    root = _busy_change(tmp_path, park="")
    (root / ".sdlc" / "factory.toml").write_text(PARK, encoding="utf-8")
    cfg, warnings = factory.load_config(root)
    assert cfg["park"]["exit"] is None
    assert any("park is read from the base branch" in w for w in warnings), warnings
    assert _gate(root, capsys)[1]["verdict"] == "FAIL"


def test_busy_of_is_none_unless_the_exit_is_the_configured_one() -> None:
    cfg = {"park": {"exit": 75, "deadline": 60, "retry": 5}}
    assert factory.busy_of(1, "SDLC-BUSY-RESOURCE: x\n", cfg) is None
    assert factory.busy_of(75, "", {"park": {"exit": None}}) is None
    assert factory.busy_of(75, "", cfg) == {"resource": "unknown", "holder": "unknown",
                                           "until": None}  # fmt: skip


def test_busy_payload_is_read_defused_and_cut(tmp_path) -> None:
    """R3: the last line of each counts, each made to one line, marked (a home path, a term), and
    cut to 200 characters."""
    root = _change(tmp_path)
    main = Path(_git(root, "rev-parse", "--show-toplevel"))
    (main / ".sdlc" / "terms.local").write_text("secret-project\n", encoding="utf-8")
    home = Path.home()
    output = (
        "SDLC-BUSY-RESOURCE: first\n"
        f"SDLC-BUSY-RESOURCE:   db at {home}/stuff for secret-project  \r\n"
        f"SDLC-BUSY-HOLDER: {'h' * 300}\n"
        "noise SDLC-BUSY-UNTIL: not at a line start\n"
        "SDLC-BUSY-UNTIL: 10\n"
    )
    cfg = {"park": {"exit": 75, "deadline": 60, "retry": 5}}
    busy = factory.busy_of(75, output, cfg, root)
    assert busy["resource"] == "db at <home>/stuff for <term>", busy
    assert busy["holder"] == "h" * 200
    assert busy["until"] == "10"


def test_park_config_out_of_range_warns(tmp_path) -> None:
    """R4: `deadline` 1–1440 minutes, else 60 with a warning; `retry` likewise, else 5."""
    root = _change(tmp_path)
    _on_main(root, "[park]\nexit = 75\ndeadline = 2000\nretry = 0\nbogus = 1\n")
    cfg, warnings = factory.load_config(root)
    assert cfg["park"] == {"exit": 75, "deadline": 60, "retry": 5}
    assert sum("park." in w for w in warnings) == 3, warnings


@pytest.mark.parametrize("code", [0, 1])
def test_park_exit_of_0_or_1_is_refused(tmp_path, code) -> None:
    """229: exit 0 is a pass and 1 every ordinary red check, so neither may mean busy: each warns,
    naming 75, and nothing parks."""
    root = _change(tmp_path)
    _on_main(root, f"[park]\nexit = {code}\n")
    cfg, warnings = factory.load_config(root)
    assert cfg["park"]["exit"] is None
    assert any("park.exit" in w and "2 to 255" in w and "75" in w for w in warnings), warnings


def test_busy_payload_drops_control_characters() -> None:
    """229: a busy line is a host command's output, shown in a terminal: C0 and C1 control
    characters (ESC, BEL, DEL, CSI) are dropped before it is stored or shown."""
    cfg = {"park": {"exit": 75, "deadline": 60, "retry": 5}}
    output = (
        "SDLC-BUSY-RESOURCE: \x1b[31mstaging\x1b[0m db\x07\nSDLC-BUSY-HOLDER: a\x7fb\x9bc\x00d\tz\n"
    )
    busy = factory.busy_of(75, output, cfg)
    assert busy["resource"] == "[31mstaging[0m db", busy
    assert busy["holder"] == "abcd z", busy


# ---------------------------------------------------------------- the record (R2, R4, R5)


def test_a_busy_gate_parks_and_records_no_attempt(tmp_path, capsys, monkeypatch) -> None:
    """R2: no attempt, a vouched `runs/parked.md` with every field, `BUSY` and exit 1."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    code, out = _gate(root, capsys)
    assert code == 1 and out["verdict"] == "BUSY", out
    assert out["parked"]["resource"] == "staging db" and out["parked"]["holder"] == "219-other"
    assert not _gate_file(root).exists(), "a busy run is no attempt"
    text = _parked(root).read_text(encoding="utf-8")
    for key in ("PARKED: gate", "ROUND: 1", "RESOURCE: staging db", "HOLDER: 219-other",
                f"SINCE: {_stamp(T0)}", f"RETRY: {_stamp(T0 + timedelta(minutes=5))}",
                f"DEADLINE: {_stamp(T0 + timedelta(minutes=60))}", "ATTEMPTS: 1"):  # fmt: skip
        assert key in text.splitlines(), (key, text)
    folder = root / ".sdlc" / "work" / NAME
    assert factory.vouched(root, folder, _parked(root))
    assert factory.read_park(text)["attempts"] == 1


def test_a_busy_answer_that_changed_the_tree_is_a_failed_attempt(tmp_path, capsys, monkeypatch):
    """R2: a busy answer parks only a check that left the tree as it found it. One that edited
    the change and exited with the park code is a FAIL attempt naming what it changed, and
    parks nothing, so the next attempt's snapshot can't take the edit in unseen."""
    root = _busy_change(tmp_path, f"printf more >> README.md; {BUSY}")
    _at(monkeypatch, T0)
    code, out = _gate(root, capsys)
    assert code == 1 and out["verdict"] == "FAIL", out
    assert out["exit"] == "75" and out["tree"] == "changed: README.md", out
    text = _gate_file(root).read_text(encoding="utf-8")
    assert text.startswith("GATE: FAIL\n") and "Tree: changed: README.md" in text, text
    assert not _parked(root).exists(), "a run that changed the tree parks nothing"


def test_a_repark_keeps_its_deadline(tmp_path, capsys, monkeypatch) -> None:
    """R4: a second busy attempt keeps SINCE and DEADLINE, counts the attempt, and an UNTIL past
    the deadline is cut to it; an UNTIL in the past is never less than a minute away."""
    late = _stamp(T0 + timedelta(hours=5))
    root = _busy_change(tmp_path, BUSY.replace("; exit", f"; echo SDLC-BUSY-UNTIL: {late}; exit"))
    _at(monkeypatch, T0)
    _gate(root, capsys)
    first = factory.read_park(_parked(root).read_text(encoding="utf-8"))
    assert first["retry"] == first["deadline"] == _stamp(T0 + timedelta(minutes=60))
    _at(monkeypatch, T0 + timedelta(minutes=20))
    _gate(root, capsys)
    second = factory.read_park(_parked(root).read_text(encoding="utf-8"))
    assert (second["since"], second["deadline"]) == (first["since"], first["deadline"])
    assert second["attempts"] == 2 and second["retry"] == second["deadline"]
    fields, _ = factory.park_fields(
        second, {"resource": "x", "holder": "y", "until": _stamp(T0)},
        {"park": {"exit": 75, "deadline": 60, "retry": 5}}, T0 + timedelta(minutes=30), "gate", 1,
    )  # fmt: skip
    assert fields["retry"] == _stamp(T0 + timedelta(minutes=31))


def test_an_until_that_wont_parse_is_noted(tmp_path, capsys, monkeypatch) -> None:
    """R3: an UNTIL that won't parse is ignored, and the record says so in a `- NOTE:` line; one
    in whole minutes is that many minutes from now."""
    root = _busy_change(tmp_path, BUSY.replace("; exit", "; echo SDLC-BUSY-UNTIL: soon; exit"))
    _at(monkeypatch, T0)
    _gate(root, capsys)
    park = factory.read_park(_parked(root).read_text(encoding="utf-8"))
    assert park["retry"] == _stamp(T0 + timedelta(minutes=5))
    assert any("soon" in n for n in park["notes"]), park
    fields, notes = factory.park_fields(
        None, {"resource": "x", "holder": "y", "until": "12"},
        {"park": {"exit": 75, "deadline": 60, "retry": 5}}, T0, "gate", 1,
    )  # fmt: skip
    assert fields["retry"] == _stamp(T0 + timedelta(minutes=12)) and not notes


def test_a_run_that_isnt_busy_ends_the_park(tmp_path, capsys, monkeypatch) -> None:
    """R5: a green or a red attempt removes the park after writing its attempt."""
    for verdict, command in (("PASS", "true"), ("FAIL", "exit 3")):
        root = _busy_change(tmp_path / verdict)
        _at(monkeypatch, T0)
        _gate(root, capsys)
        assert _parked(root).exists()
        _gate_config(root, command)
        code, out = _gate(root, capsys)
        assert out["verdict"] == verdict, out
        assert _gate_file(root).is_file() and not _parked(root).exists(), verdict


# ---------------------------------------------------------------- the reading (R6–R9)


def test_verdicts_parks_then_retries_then_stops(tmp_path, capsys, monkeypatch) -> None:
    """R6: before RETRY `parked`, from RETRY `gate`, at DEADLINE a stop whose way is `parked`."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    _gate(root, capsys)
    out = _verdicts(root, capsys, T0 + timedelta(minutes=1))
    assert (out["next"], out["round"]) == ("parked", 1), out
    assert out["parked"]["resource"] == "staging db" and out["parked"]["attempts"] == 1
    assert set(out["parked"]) >= {"resource", "holder", "since", "retry", "deadline", "attempts"}
    out = _verdicts(root, capsys, T0 + timedelta(minutes=5))
    assert (out["next"], out["round"]) == ("gate", 1), out
    out = _verdicts(root, capsys, T0 + timedelta(minutes=60))
    assert (out["next"], out["way"]) == ("stop", "parked"), out
    assert any("219-other" in p and "staging db" in p for p in out["problems"]), out


def test_verdicts_reads_only_files_and_its_clock(tmp_path, capsys, monkeypatch) -> None:
    """R7: the same files and the same `now` give the same reading, whatever the real clock."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    _gate(root, capsys)
    first = _verdicts(root, capsys, T0 + timedelta(minutes=2))
    _at(monkeypatch, T0 + timedelta(days=3))
    assert _verdicts(root, capsys, T0 + timedelta(minutes=2)) == first
    assert _verdicts(root, capsys, T0 + timedelta(minutes=2))["next"] == "parked"


def test_a_forged_park_never_waits(tmp_path, capsys, monkeypatch) -> None:
    """R8: a hand-written record with a far deadline is a stop to rerun, never a wait; a vouched
    record's deadline is capped by the base branch's `[park] deadline`."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    _gate(root, capsys)
    path = _parked(root)
    text = path.read_text(encoding="utf-8")
    far = _stamp(T0 + timedelta(days=30))
    path.write_text(re.sub(r"DEADLINE: .*", f"DEADLINE: {far}", text), encoding="utf-8")
    out = _verdicts(root, capsys, T0 + timedelta(minutes=1))
    assert (out["next"], out["way"]) == ("stop", "rerun"), out
    path.write_text("PARKED: gate\nnonsense\n", encoding="utf-8")
    assert _verdicts(root, capsys, T0 + timedelta(minutes=1))["way"] == "rerun"
    # A vouched record whose deadline runs past the cap is read at the cap.
    path.unlink()
    _on_main(root, PARK + "deadline = 10\n")
    _at(monkeypatch, T0)
    _gate(root, capsys)
    _on_main(root, PARK + "deadline = 3\n")
    out = _verdicts(root, capsys, T0 + timedelta(minutes=4))
    assert (out["next"], out["way"]) == ("stop", "parked"), out


def test_a_stale_park_is_passed_over_and_removed(tmp_path, capsys, monkeypatch) -> None:
    """R8: a record for another round is stale: `verdicts` passes over it, `--record` removes it."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    _gate(root, capsys)
    path = _parked(root)
    folder = root / ".sdlc" / "work" / NAME
    stale = path.read_text(encoding="utf-8").replace("ROUND: 1", "ROUND: 7")
    factory._vouch(root, folder, path, stale)
    path.write_text(stale, encoding="utf-8")
    out = _verdicts(root, capsys, T0 + timedelta(minutes=1))
    assert out["next"] == "gate" and out["parked"] is None, out
    head = _git(root, "rev-parse", "--short", "HEAD")
    _verdicts(root, capsys, T0 + timedelta(minutes=1), head=head, record=True)
    assert not path.exists()


def test_a_stop_at_the_deadline_reads_back_as_parked(tmp_path, capsys, monkeypatch) -> None:
    """R9: `--record` writes `STEP: parked` while parked, and at the deadline `STOPPED: parked`
    naming the resource and holder, which the core's reader reads back with its way."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    _gate(root, capsys)
    folder = root / ".sdlc" / "work" / NAME
    head = _git(root, "rev-parse", "--short", "HEAD")
    _verdicts(root, capsys, T0 + timedelta(minutes=1), head=head, record=True)
    step = factory.read_step((folder / factory.STEP).read_text(encoding="utf-8"))
    assert step["step"] == "parked"
    _verdicts(root, capsys, T0 + timedelta(minutes=61), head=head, record=True)
    text = (folder / factory.STOPPED).read_text(encoding="utf-8")
    assert text.startswith("STOPPED: parked\n")
    assert "NEXT: free staging db (held by 219-other), then /sdlc-factory:build 008" in text
    records = factory_records()
    stop = records.read_stop(folder)
    assert stop["way"] == "parked" and "219-other" in stop["next"], stop


def factory_records():
    from factory_helpers import _load

    return _load("factory_records_for_park", ROOT / "scripts" / "factory_records.py")


# ---------------------------------------------------------------- the transition table (R17)


def _assigned_steps(tree: ast.AST) -> set[str]:
    """Every value `run_state.py` assigns to `out["next"]`, alone or in a tuple assignment."""
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            pairs = []
            if isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple):
                pairs = list(zip(target.elts, node.value.elts, strict=False))
            else:
                pairs = [(target, node.value)]
            for t, v in pairs:
                is_next = (
                    isinstance(t, ast.Subscript)
                    and isinstance(t.slice, ast.Constant)
                    and t.slice.value == "next"
                )
                if is_next and isinstance(v, ast.Constant):
                    found.add(v.value)
    return found


def test_every_step_has_a_row_and_a_bound() -> None:
    """R17: every `next` the reading names is in `STEPS`, and the README's table has a row for
    each step with a bound."""
    run_state = ROOT / "plugins" / "factory" / "scripts" / "run_state.py"
    assigned = _assigned_steps(ast.parse(run_state.read_text(encoding="utf-8")))
    assert {"gate", "parked", "stop", "done"} <= assigned, assigned
    assert assigned <= set(factory.STEPS), assigned - set(factory.STEPS)
    readme = (ROOT / "plugins" / "factory" / "README.md").read_text(encoding="utf-8")
    section = readme.split("### The loop's states", 1)[1].split("\n#", 1)[0]
    rows = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and (m := re.fullmatch(r"`([a-z]+)`", cells[0])):
            rows[m.group(1)] = cells
    assert set(rows) == set(factory.STEPS), set(factory.STEPS) ^ set(rows)
    assert all(row[3] for row in rows.values()), rows


# ---------------------------------------------------------------- slots and check (R12, R14)


def test_a_gate_slot_wait_ends(tmp_path, monkeypatch) -> None:
    """R12: with every slot held, `gate_slot()` gives up at `SLOT_WAIT`, holding nothing."""
    root = _change(tmp_path)
    monkeypatch.setattr(factory, "SLOT_WAIT", 0.3)
    start = time.monotonic()
    with factory.gate_slot(root, 1, "009-other") as (slot, _):
        assert slot == 0
        with pytest.raises(factory.SlotWaitExpired) as e, factory.gate_slot(root, 1, NAME):
            raise AssertionError("no slot was free")
    assert e.value.waited >= 0.3 and time.monotonic() - start < 5
    with factory.gate_slot(root, 1, NAME) as (slot, _):
        assert slot == 0, "the slot it gave up on is free once its holder is done"


def test_a_gate_past_the_slot_wait_parks_and_a_check_exits_1(tmp_path, capfd, monkeypatch) -> None:
    """R12: a gate past `SLOT_WAIT` records no attempt and parks on `gate slot`, with no `[park]`
    set at all; a check past it exits 1 and says so."""
    root = _busy_change(tmp_path, "true", park="")
    monkeypatch.setattr(factory, "SLOT_WAIT", 0.2)
    _at(monkeypatch, T0)
    with factory.gate_slot(root, 1, "009-other"):
        capfd.readouterr()
        code = factory.cmd_gate(root, "008")
        out = json.loads(capfd.readouterr().out)
        assert code == 1 and out["verdict"] == "BUSY", out
        assert (out["parked"]["resource"], out["parked"]["holder"]) == ("gate slot", "another gate")
        assert not _gate_file(root).exists() and _parked(root).is_file()
        capfd.readouterr()
        assert factory.cmd_check(root, "008") == 1
        err = capfd.readouterr().err
        assert "no gate slot came free" in err and "didn't run" in err, err


def test_check_passes_busy_through_and_writes_nothing(tmp_path, capfd) -> None:
    """R14: `check` returns the host's busy code, says what is held on stderr, writes nothing;
    without `[park]`, its output is the command's own, uncaught."""
    root = _busy_change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    before = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*"))
    capfd.readouterr()
    assert factory.cmd_check(root, "008") == 75
    seen = capfd.readouterr()
    assert "SDLC-BUSY-RESOURCE: staging db" in seen.out
    assert "busy: staging db held by 219-other until unknown" in seen.err
    assert sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")) == before
    plain = _busy_change(tmp_path / "plain", park="")
    capfd.readouterr()
    assert factory.cmd_check(plain, "008") == 75
    seen = capfd.readouterr()
    assert "SDLC-BUSY-RESOURCE" in seen.out and "busy:" not in seen.err


# ---------------------------------------------------------------- park --wait, --clear, start


class Clock:
    """A stand-in clock that moves only when `park --wait` pauses."""

    def __init__(self, when: datetime) -> None:
        self.when, self.pauses = when, []

    def __call__(self) -> datetime:
        return self.when

    def pause(self, seconds: float) -> None:
        self.pauses.append(seconds)
        self.when += timedelta(seconds=seconds)


def test_park_wait_returns_by_its_bound(tmp_path, capsys, monkeypatch) -> None:
    """R10: `--wait` checks every few seconds until RETRY, writes nothing, and prints the reading
    `verdicts` gives then; with the record gone it returns at once."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    _gate(root, capsys)
    clock = Clock(T0 + timedelta(minutes=1))
    monkeypatch.setattr(factory, "_clock", clock)
    monkeypatch.setattr(factory, "_pause", clock.pause)
    before = _parked(root).read_bytes()
    code, out = _run(capsys, factory.cmd_park, root, "008", True, False)
    assert code == 0 and out["next"] == "gate", out
    assert clock.when == T0 + timedelta(minutes=5), "until RETRY, no later"
    assert max(clock.pauses) <= factory.PARK_POLL and len(clock.pauses) >= 4 * 60 / 5
    assert _parked(root).read_bytes() == before
    _parked(root).unlink()
    clock.pauses.clear()
    code, out = _run(capsys, factory.cmd_park, root, "008", True, False)
    assert code == 0 and not clock.pauses and out["next"] == "gate"


def test_park_clear_refuses_a_live_park(tmp_path, capsys, monkeypatch) -> None:
    """R10: `--clear` refuses a park before its deadline and removes one past it."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    _gate(root, capsys)
    _at(monkeypatch, T0 + timedelta(minutes=59))
    code, out = _run(capsys, factory.cmd_park, root, "008", False, True)
    assert code == 1 and out["refusals"] and _parked(root).exists(), out
    _at(monkeypatch, T0 + timedelta(minutes=60))
    code, out = _run(capsys, factory.cmd_park, root, "008", False, True)
    assert code == 0 and out["cleared"] and not _parked(root).exists(), out
    code, out = _run(capsys, factory.cmd_park, root, "008", False, True)
    assert code == 0 and not out["cleared"], out


def test_park_clear_removes_an_unvouched_record(tmp_path, capsys, monkeypatch) -> None:
    """229: a record the ledger never vouched for is no park, so `--clear` removes it before its
    deadline rather than refusing with no way out but an `rm`."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    _gate(root, capsys)
    path = _parked(root)
    path.write_text(path.read_text(encoding="utf-8").replace("ATTEMPTS: 1", "ATTEMPTS: 9"),
                    encoding="utf-8")  # fmt: skip
    _at(monkeypatch, T0 + timedelta(minutes=1))
    code, out = _run(capsys, factory.cmd_park, root, "008", False, True)
    assert code == 0 and out["cleared"] and not path.exists(), out
    assert out["parked"]["vouched"] is False


def test_start_reports_the_park(tmp_path, capsys, monkeypatch) -> None:
    """R11: `start --for build` reports the park and whether it is past its deadline, and
    writes nothing."""
    root = _busy_change(tmp_path)
    _at(monkeypatch, T0)
    _gate(root, capsys)
    intent = root / ".sdlc" / "work" / NAME / "intent.md"
    intent.write_text(intent.read_text(encoding="utf-8").replace("stage: design", "stage: build"))
    before = _parked(root).read_bytes()
    _at(monkeypatch, T0 + timedelta(minutes=1))
    out = _run(capsys, factory.cmd_start, root, "008", "build")[1]
    assert out["parked"]["resource"] == "staging db" and out["parked"]["expired"] is False, out
    _at(monkeypatch, T0 + timedelta(hours=2))
    out = _run(capsys, factory.cmd_start, root, "008", "build")[1]
    assert out["parked"]["expired"] is True
    assert _parked(root).read_bytes() == before
