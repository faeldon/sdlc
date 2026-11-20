"""The suite's own shape: what a test review kept raising as a nit, held by the gate instead
(201). A test that asks for a pytest fixture it never uses reads as though it writes a file,
prints or patches something, and a reviewer has to look to find it doesn't (nit 2026-11-20-34)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
# pytest's own fixtures, which a test asks for only to use: never for a side effect.
BUILT_IN = {"tmp_path", "tmp_path_factory", "capsys", "capfd", "caplog", "monkeypatch"}


def unused_fixtures(source: str) -> list[str]:
    """Each test function in `source` (a `test_` def, at any depth) with a `BUILT_IN` parameter
    its body, nested functions included, never names: `<name>: <fixture>`."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not node.name.startswith("test_"):
            continue
        named = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        found += [
            f"{node.name}: {a.arg}"
            for a in node.args.args
            if a.arg in BUILT_IN and a.arg not in named
        ]
    return found


@pytest.mark.portable
def test_the_check_finds_a_fixture_never_used() -> None:
    source = (
        "def test_one(tmp_path, capsys):\n    print(tmp_path)\n\n"
        "def test_two(monkeypatch):\n    def inner():\n        monkeypatch.setenv('A', '1')\n"
        "    inner()\n\n"
        "def helper(tmp_path):\n    pass\n"
    )
    assert unused_fixtures(source) == ["test_one: capsys"]


@pytest.mark.portable
def test_no_test_takes_a_fixture_it_never_uses() -> None:
    found = [
        f"{path.name}: {each}"
        for path in sorted(TESTS.glob("test_*.py"))
        for each in unused_fixtures(path.read_text(encoding="utf-8"))
    ]
    assert found == [], "drop the argument:\n" + "\n".join(found)
