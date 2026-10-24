"""`sdlc.py readiness`: what /sdlc:setup works from.

It reports, item by item, whether a repo is set up for the plugin, and reads the repo's own task
files for the commands setup should propose. It must write nothing, and a repo with nothing at all
must still get an answer rather than a traceback.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_readiness", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _readiness(root: Path, capsys) -> dict:
    capsys.readouterr()
    assert sdlc.cmd_readiness(root) == 0
    return json.loads(capsys.readouterr().out)


def _items(out: dict) -> dict[str, str]:
    return {i["name"]: i["status"] for i in out["items"]}


def test_an_ignored_work_is_not_ready(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    out = _readiness(root, capsys)
    assert out["ready"] is True and _items(out)["work"] == "ok"
    assert _items(out)["docs.process"] == "missing" and _items(out)["context"] == "missing"
    (root / ".gitignore").write_text("work/\n", encoding="utf-8")
    out = _readiness(root, capsys)
    assert out["ready"] is False and _items(out)["work"] == "missing"


def test_outside_git_it_still_answers(tmp_path: Path, capsys) -> None:
    out = _readiness(tmp_path, capsys)
    assert _items(out)["work"] == "n/a" and out["ready"] is True


def test_it_writes_nothing(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    (root / "Makefile").write_text("check:\n\ttrue\n", encoding="utf-8")
    before = sorted(p.relative_to(root) for p in root.rglob("*") if ".git" not in p.parts)
    _readiness(root, capsys)
    after = sorted(p.relative_to(root) for p in root.rglob("*") if ".git" not in p.parts)
    assert before == after


def test_candidates_come_from_the_repos_own_task_files(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    (root / "Makefile").write_text(
        ".PHONY: check\ncheck: lint\n\ttrue\nintegration:\n\ttrue\nVAR := 1\n", encoding="utf-8"
    )
    (root / "package.json").write_text('{"scripts": {"test": "jest", "start": "node ."}}')
    (root / "pnpm-lock.yaml").write_text("")
    (root / "justfile").write_text("scan target='x':\n    echo\n", encoding="utf-8")
    (root / "mise.toml").write_text('[tasks.bootstrap]\nrun = "true"\n', encoding="utf-8")
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    (root / "uv.lock").write_text("")
    (root / "scripts").mkdir()
    (root / "scripts" / "ci.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    got = {k: {c["command"] for c in v} for k, v in _readiness(root, capsys)["candidates"].items()}
    assert got["check"] == {"make check", "pnpm test", "uv run pytest", "./scripts/ci.sh"}
    assert got["build"] == {"make integration"}
    assert got["scan"] == {"just scan"}
    assert got["worktree_setup"] == {"mise run bootstrap"}


def test_a_process_doc_still_holding_the_template_is_a_warning(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir()
    shutil.copy(sdlc.DEFAULTS_DIR / "SDLC.md", root / ".sdlc" / "SDLC.md")
    assert _items(_readiness(root, capsys))["docs.process"] == "warn"


def test_the_review_falling_back_to_the_plugins_counts_as_missing(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    assert _items(_readiness(root, capsys))["docs.review"] == "missing"


def test_permissions_are_read_from_the_shared_settings(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"permissions": {"allow": sdlc.ALLOW_RULES[:2]}}))
    out = _readiness(root, capsys)
    assert _items(out)["permissions"] == "missing"
    assert out["permissions"]["missing"] == sdlc.ALLOW_RULES[2:]
    settings.write_text(json.dumps({"permissions": {"allow": ["Bash(ls *)", *sdlc.ALLOW_RULES]}}))
    assert _items(_readiness(root, capsys))["permissions"] == "ok"
    settings.write_text("{not json")
    assert _items(_readiness(root, capsys))["permissions"] == "warn"


def test_the_allowlist_covers_only_subcommands_that_read() -> None:
    for writer in ("new", "ship", "close", "release", "publish", "retro-commit"):
        assert not any(f"sdlc.py {writer} " in r for r in sdlc.ALLOW_RULES)
    # `retro` writes nothing, but it runs the host's `retro.evidence`: outside the skill, it asks.
    assert not any("sdlc.py retro" in r for r in sdlc.ALLOW_RULES)


def test_the_defaults_setup_copies_from_exist(tmp_path: Path, capsys) -> None:
    out = _readiness(_repo(tmp_path), capsys)
    assert Path(out["defaults"]["process"]).is_file() and Path(out["defaults"]["review"]).is_file()


def test_the_project_doc_is_off_until_it_exists_and_warned_when_it_wont_read(
    tmp_path: Path, capsys
) -> None:
    root = _repo(tmp_path)
    item = next(i for i in _readiness(root, capsys)["items"] if i["name"] == "docs.project")
    assert item["status"] == "ok" and item["detail"].startswith("off:")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "PROJECT.md").write_text("---\nmilestone: tracker\n---\n", encoding="utf-8")
    item = next(i for i in _readiness(root, capsys)["items"] if i["name"] == "docs.project")
    assert item == {**item, "status": "ok", "detail": ".sdlc/PROJECT.md: milestone"}
    (root / ".sdlc" / "PROJECT.md").write_text("no frontmatter\n", encoding="utf-8")
    item = next(i for i in _readiness(root, capsys)["items"] if i["name"] == "docs.project")
    assert item["status"] == "warn" and "no frontmatter" in item["detail"]


def _by_name(root: Path, capsys) -> dict[str, dict]:
    return {i["name"]: i for i in _readiness(root, capsys)["items"]}


def test_the_product_doc_is_off_until_it_exists_and_evidence_waits_for_it(
    tmp_path: Path, capsys
) -> None:
    root = _repo(tmp_path)
    items = _by_name(root, capsys)
    assert items["docs.product"]["status"] == "ok"
    assert items["docs.product"]["detail"].startswith("off:")
    assert items["retro.evidence"]["status"] == "n/a"
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[retro]\nevidence = ["echo 3"]\n', "utf-8")
    assert _by_name(root, capsys)["retro.evidence"]["status"] == "warn"
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "PRODUCT.md").write_text(
        "- O1. **Setup.** Setup unaided\n- ~~O2. X~~ Done: 001\n"
    )
    items = _by_name(root, capsys)
    detail = ".sdlc/PRODUCT.md: 1 open outcome(s) (O1)"
    assert items["docs.product"] == {**items["docs.product"], "status": "ok", "detail": detail}
    assert items["retro.evidence"] == {**items["retro.evidence"], "status": "ok"}
    (root / ".sdlc" / "PRODUCT.md").write_text("- G1. A goal in the wrong doc\n")
    item = _by_name(root, capsys)["docs.product"]
    assert item["status"] == "warn" and "wrong doc" in item["detail"]


def test_the_default_product_doc_is_listed(tmp_path: Path, capsys) -> None:
    assert Path(_readiness(_repo(tmp_path), capsys)["defaults"]["product"]).is_file()


def test_the_default_project_doc_exists_and_turns_nothing_on(tmp_path: Path, capsys) -> None:
    path = Path(_readiness(_repo(tmp_path), capsys)["defaults"]["project"])
    text = path.read_text(encoding="utf-8")
    fields = {f: sdlc.frontmatter_list(text, f) for f in sdlc.PROJECT_FIELDS}
    assert fields == {f: None for f in sdlc.PROJECT_FIELDS}, "every field starts commented out"


def test_no_claude_md_or_agents_md_is_missing_context(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    item = next(i for i in _readiness(root, capsys)["items"] if i["name"] == "context")
    assert item["status"] == "missing" and "no CLAUDE.md or AGENTS.md" in item["detail"]
    (root / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
    items = _items(_readiness(root, capsys))
    assert items["context"] == "ok" and items["docs.policy"] == "ok"


def test_the_health_doc_is_off_without_a_scan_and_drafted_once_there_is_one(
    tmp_path: Path, capsys
) -> None:
    root = _repo(tmp_path)
    assert _items(_readiness(root, capsys))["docs.health"] == "n/a"
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "config.toml").write_text('[commands]\nscan = "make scan"\n', "utf-8")
    assert _items(_readiness(root, capsys))["docs.health"] == "missing"
    out = _readiness(root, capsys)
    assert not next(i for i in out["items"] if i["name"] == "docs.health")["required"]
    shutil.copy(out["defaults"]["health"], root / ".sdlc" / "HEALTH.md")
    assert _items(_readiness(root, capsys))["docs.health"] == "warn", "still the template"
    (root / ".sdlc" / "HEALTH.md").write_text("# Health\n\n## Findings\n\n| a | b |\n", "utf-8")
    assert _items(_readiness(root, capsys))["docs.health"] == "ok"
