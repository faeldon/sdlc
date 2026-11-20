"""196 (nit 2026-11-20-8): a raise matches an earlier one by its alternatives only when they are
a real choice, two options or more: two decisions that share one option are two decisions."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "factory_decision_alternatives", ROOT / "plugins" / "factory" / "scripts" / "factory.py"
)
factory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(factory)

NAME = "008-reopen-drafts"
INTENT = "---\nid: 008\nslug: reopen-drafts\ntier: 2\nstage: build\n---\n\n# 008 — Reopen drafts\n"
EVIDENCE = "\n## Evidence\n\n$ ./check.sh\n12 passed\nexit: 0\n"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)


def _change(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
    _git(root, "checkout", "-q", "-b", NAME)
    folder = root / ".sdlc" / "work" / NAME
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT, encoding="utf-8")
    return root


def _report(root: Path, n: int, text: str) -> None:
    build = root / ".sdlc" / "work" / NAME / "build"
    build.mkdir(parents=True, exist_ok=True)
    (build / f"round-{n}.md").write_text("Built.\n" + text + EVIDENCE, encoding="utf-8")


def _added(root: Path, capsys) -> list[str]:
    capsys.readouterr()
    assert factory.cmd_decisions(root, "008") == 0
    return json.loads(capsys.readouterr().out)["added"]


ONE = "  - OPTION: keep it — nothing lost\n  - WHY: the spec\n"


def test_two_decisions_sharing_one_option_are_filed_apart(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _report(root, 1, "- DECISION: [default] Keep the drafts list?\n" + ONE)
    assert _added(root, capsys) == ["D1"]
    _report(root, 1, "- DECISION: [default] Keep the old export?\n" + ONE)
    assert _added(root, capsys) == ["D2"]
