"""199: the records ledger, `sdlc-factory-records.jsonl` in the git common dir, where the script
vouches for each gate, build and accept record it writes, so a record an agent wrote in the
change's folder is never read as a verdict.

The landing's and the train's refusals are tested beside them, in `test_land.py` and
`test_train.py`; the hand gate's in `test_hand_gate.py`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from factory_helpers import (
    NAME,
    _build_report,
    _change,
    _gate,
    _gate_config,
    _git,
    factory,
    sdlc,
)


def _ledger(root: Path) -> Path:
    return Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")) / (
        factory.RECORDS_LEDGER
    )


def _rows(root: Path) -> list[dict]:
    path = _ledger(root)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _digest(path: Path) -> str:
    return factory._record_digest(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- R1: the script vouches


def test_gate_vouches_for_its_record(tmp_path, capsys) -> None:
    """R1: `factory.py gate` appends the hash of each version it writes, before it writes it."""
    root = _change(tmp_path)
    _gate_config(root, "echo ok")
    _build_report(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    record = folder / "build" / "round-1.gate.md"
    assert _gate(root, capsys)[0] == 0
    first = _digest(record)
    assert _gate(root, capsys)[0] == 0
    rows = _rows(root)
    assert rows == [
        {"change": NAME, "record": "build/round-1.gate.md", "sha256": first},
        {"change": NAME, "record": "build/round-1.gate.md", "sha256": _digest(record)},
    ]
    assert factory.vouched(root, folder, record)
    assert factory.landing.forged_records(root, folder) == []


# ---------------------------------------------------------------- R2: the ledger alone decides


def test_vouched_reads_the_ledger_alone(tmp_path, capsys) -> None:
    """R2: a byte changed unvouches a record and restoring it vouches it again; the same bytes in
    another change's folder, or at another record path, are unvouched; a missing ledger, or one
    with a garbled line, vouches nothing more than its whole lines say."""
    root = _change(tmp_path)
    _gate_config(root, "echo ok")
    _build_report(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    record = folder / "build" / "round-1.gate.md"
    assert _gate(root, capsys)[0] == 0
    text = record.read_text(encoding="utf-8")
    assert factory.vouched(root, folder, record)

    record.write_text(text.replace("PASS", "PASs", 1), encoding="utf-8", newline="\n")
    assert not factory.vouched(root, folder, record)
    assert factory.landing.forged_records(root, folder) == ["build/round-1.gate.md"]
    record.write_text(text, encoding="utf-8", newline="\n")
    assert factory.vouched(root, folder, record)

    other = root / ".sdlc" / "work" / "009-other" / "build" / "round-1.gate.md"
    other.parent.mkdir(parents=True)
    other.write_text(text, encoding="utf-8", newline="\n")
    assert not factory.vouched(root, other.parent.parent, other), "another change's"
    moved = folder / "build" / "round-2.gate.md"
    moved.write_text(text, encoding="utf-8", newline="\n")
    assert not factory.vouched(root, folder, moved), "another record path"
    accept = folder / "build" / "land-accept.md"
    accept.write_text(text, encoding="utf-8", newline="\n")
    assert factory.landing.forged_records(root, folder) == [
        "build/land-accept.md",
        "build/round-2.gate.md",
    ]

    ledger = _ledger(root)
    lines = ledger.read_text(encoding="utf-8")
    ledger.write_text("{not json\n" + lines + '{"change": "x"\n', encoding="utf-8", newline="\n")
    assert factory.vouched(root, folder, record), "a garbled line is skipped"
    ledger.unlink()
    assert not factory.vouched(root, folder, record), "no ledger vouches nothing"


@pytest.mark.portable
def test_a_crlf_record_stays_vouched(tmp_path, capsys) -> None:
    """R2: a CRLF copy of a vouched record (a checkout with `core.autocrlf`) reads alike."""
    root = _change(tmp_path)
    _gate_config(root, "echo ok")
    _build_report(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    record = folder / "build" / "round-1.gate.md"
    assert _gate(root, capsys)[0] == 0
    record.write_bytes(record.read_bytes().replace(b"\n", b"\r\n"))
    assert b"\r\n" in record.read_bytes()
    assert factory.vouched(root, folder, record)
    assert factory._record_digest("a\r\nb\n") == factory._record_digest("a\nb\n")


# ---------------------------------------------------------------- R7: no append to a forgery


FORGED = "GATE: PASS\n\n## Attempt 1\n\nVerdict: PASS\nBuild: {build}\nExit: 0\n"


def test_no_writer_appends_to_an_unvouched_record(tmp_path, capsys) -> None:
    """R7: `factory.py gate` refuses to append to a round's or a landing's record it didn't write:
    nothing runs (the marker is never left), the record is unchanged and the ledger holds no line
    for it."""
    root = _change(tmp_path)
    marker = tmp_path / "ran"
    _gate_config(root, f"touch {marker}")
    _build_report(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    record = folder / "build" / "round-1.gate.md"
    record.parent.mkdir(exist_ok=True)
    forged = FORGED.format(build=factory.build_hash(folder, 1))
    record.write_text(forged, encoding="utf-8", newline="\n")
    code, out = _gate(root, capsys)
    assert (
        code == 1
        and "build/round-1.gate.md isn't a record the script wrote" in (out["refusals"][0])
    ), out
    assert "remove it" in out["refusals"][0]
    assert not marker.exists(), "nothing ran"
    assert record.read_text(encoding="utf-8") == forged
    assert _rows(root) == []
    record.unlink()
    assert _gate(root, capsys)[0] == 0 and marker.exists(), "once removed, it runs"


def test_a_record_forged_while_the_gate_ran_is_never_appended_to(tmp_path, capsys) -> None:
    """R7: the earlier record is checked again after the slot wait, before it is read: one
    rewritten by hand while the gate waited or ran is refused, left as it is, and gets no line."""
    root = _change(tmp_path)
    _gate_config(root, "echo ok")
    _build_report(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    record = folder / "build" / "round-1.gate.md"
    assert _gate(root, capsys)[0] == 0
    rows = _rows(root)
    forged = tmp_path / "forged.md"
    forged.write_text(FORGED.format(build="abc"), encoding="utf-8", newline="\n")
    _gate_config(root, f"cp {forged} {record}")
    code, out = _gate(root, capsys)
    assert (
        code == 1
        and "build/round-1.gate.md isn't a record the script wrote" in (out["refusals"][0])
    ), out
    assert record.read_text(encoding="utf-8") == FORGED.format(build="abc"), "never appended to"
    assert _rows(root) == rows, "nothing vouched"


# ---------------------------------------------------------------- R9: across worktrees


WRITER = """
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("f", sys.argv[1])
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
root, folder = Path(sys.argv[2]), Path(sys.argv[3])
for i in range(int(sys.argv[5])):
    f._vouch(root, folder, folder / "build" / "round-1.gate.md", sys.argv[4] * 200 + str(i))
"""


def test_two_writers_at_once_leave_whole_lines(tmp_path) -> None:
    """R9: two processes appending at once each leave whole lines, every one of them read. 235
    R11: one is `factory.py`'s writer and the other core's copy, under the same lock."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    script = tmp_path / "writer.py"
    script.write_text(WRITER, encoding="utf-8", newline="\n")
    argv = [sys.executable, str(script)]
    places = [str(root), str(folder)]
    writers = [(factory.__file__, "a"), (sdlc.__file__, "b")]
    kids = [subprocess.Popen([*argv, str(path), *places, mark, "50"]) for path, mark in writers]
    assert [k.wait(timeout=120) for k in kids] == [0, 0]
    rows = _rows(root)
    assert len(rows) == 100
    want = {factory._record_digest(mark * 200 + str(i)) for mark in ("a", "b") for i in range(50)}
    assert {r["sha256"] for r in rows} == want


# ---------------------------------------------------------------- R8: core's copy is pinned


@pytest.mark.portable
def test_the_ledger_writer_is_pinned_to_core(tmp_path) -> None:
    """R8: `sdlc.py`'s `_vouch()` and `factory.py`'s write the same line for the same record, and
    each reads the other's as vouched."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    record = folder / "build" / "gate.md"
    record.parent.mkdir(exist_ok=True)
    text = "GATE: PASS\r\n\n## Attempt 1\n\nVerdict: PASS\nBuild: abc\n"
    assert sdlc.factory_records.RECORDS_LEDGER == factory.RECORDS_LEDGER
    assert sdlc.factory_records.RECORDS_LOCK == factory.RECORDS_LOCK
    assert sdlc.LEDGER_LOCK_WAIT == factory.RECORDS_LOCK_WAIT
    assert sdlc.factory_records.record_digest(text) == factory._record_digest(text)
    assert sdlc.factory_records.ledger_line(NAME, "build/gate.md", text) == factory._ledger_line(
        NAME, "build/gate.md", text
    )
    sdlc._vouch(root, folder, record, text)
    factory._vouch(root, folder, record, text)
    lines = _ledger(root).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and lines[0] == lines[1], lines
    record.write_text(text, encoding="utf-8", newline="\n")
    assert factory.vouched(root, folder, record)
    assert sdlc._hand_vouched(root, folder, record)
    record.write_text(text + "x", encoding="utf-8", newline="\n")
    assert not sdlc._hand_vouched(root, folder, record)
