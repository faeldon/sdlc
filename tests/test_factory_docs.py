"""The docs reviewer (227): its place in the roster, the docs it reads from the base branch, the
rule that calls it into a round, and the prompt that names its docs and stale lines.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Each test builds a scratch repo
on a change branch with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from factory_helpers import (
    FULL,
    LISTED,
    NAME,
    ROOT,
    _build_report,
    _change,
    _git,
    _review,
    _touch,
    _verdicts,
    _verified,
    factory,
    sdlc,
)


def _docs_on_main(root: Path, docs: str, *files: tuple[str, str]) -> None:
    """Commit a `[docs]` table on the base branch's `.sdlc/config.toml`, and `files`, then bring the
    change's branch up to it."""
    _git(root, "checkout", "-q", "main")
    config = root / ".sdlc" / "config.toml"
    config.parent.mkdir(exist_ok=True)
    before = config.read_text(encoding="utf-8") if config.is_file() else ""
    config.write_text(before + docs, encoding="utf-8")
    for path, text in files:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "docs")
    _git(root, "checkout", "-q", NAME)
    _git(root, "merge", "-q", "--ff-only", "main")


def _joins(root: Path) -> bool:
    base = factory._base(root)
    docs = factory.reviewed_docs(root, base)
    return factory.docs_review(docs, [], factory._changed_paths(root, base), root)


# ---------------------------------------------------------------- R1–R3: the roster


def test_docs_is_a_reviewer_on_sonnet() -> None:
    """R1: in every copy of the roster, on sonnet unless `models` says otherwise."""
    assert "docs" in factory.REVIEWERS and "docs" in factory.ROLES and "docs" in factory.SCALED
    assert sdlc.AGENT_ROLES == factory.REVIEWERS
    assert sdlc.factory_records.REVIEWERS == factory.REVIEWERS
    cfg = factory.load_config(Path("/nonexistent"))[0]
    assert factory.model_for("docs", cfg, 2, "full") == "sonnet"
    assert factory.model_for("docs", {**cfg, "models": {"docs": "opus"}}, 2, "full") == "opus"
    agent = (ROOT / "plugins" / "factory" / "agents" / "reviewer-docs.md").read_text("utf-8")
    assert "model: sonnet" in agent and "tools: Read, Grep, Glob, Bash\n" in agent


def test_an_untagged_docs_finding_is_context() -> None:
    """R2."""
    assert factory.finding_pass("docs", "docs/a.md:3: x") == ("context", "docs/a.md:3: x")


def test_docs_is_never_chosen_in_a_reviewers_list(tmp_path) -> None:
    """R3: named in either list, it warns and is dropped."""
    root = _change(tmp_path)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text(
        'reviewers = ["code", "docs"]\n[light]\nreviewers = ["docs", "code"]\n', encoding="utf-8"
    )
    cfg, warnings = factory.load_config(root)
    assert cfg["reviewers"] == ["code"] and cfg["light"]["reviewers"] == ["code"]
    assert "'docs' joins on its own, never in reviewers" in warnings
    assert "'docs' joins on its own, never in light.reviewers" in warnings


def test_a_light_run_that_ran_docs_stays_light(tmp_path, capsys) -> None:
    """R3: `docs` never makes a run's depth full."""
    root = _change(tmp_path, 1, config=LISTED)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    light = ["code", "behaviour", "docs"]
    out = _verdicts(root, capsys)
    assert (out["depth"], out["missing"]) == ("light", light)
    for role in light:
        _review(root, 1, role, "VERDICT: CHANGES", f"src/a.py:1: {role} fix")
    _verified(root, 1, kept=[f"{r}: src/a.py:1: {r} fix" for r in light])
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert out["depth"] == "light", "the docs review never makes a run full"
    assert out["missing"] == light


# ---------------------------------------------------------------- R5: the list


def test_with_nothing_set_the_list_is_today_s_context_default(tmp_path) -> None:
    """R5: the copy is pinned to `sdlc.py`'s default, and a host with no `[docs]` gets it."""
    assert tuple(sdlc.CONFIG_KEYS["docs"]["context"]) == factory.CONTEXT_DEFAULT
    root = _change(tmp_path)
    assert factory._docs_at(root, "main") == (list(factory.CONTEXT_DEFAULT), [])


def test_a_reviewed_folder_names_every_file_under_it(tmp_path) -> None:
    """R5: an entry ending in `/` is a folder; any other a glob."""
    root = _change(tmp_path)
    _docs_on_main(
        root,
        '[docs]\ncontext = ["AGENTS.md"]\nreviewed = ["site/", "docs/*.md"]\n',
        ("AGENTS.md", "agents\n"),
        ("site/a.md", "a\n"),
        ("site/deep/b.md", "b\n"),
        ("docs/c.md", "c\n"),
        ("docs/c.txt", "c\n"),
    )
    assert factory._docs_at(root, "main") == (["AGENTS.md"], ["site/", "docs/*.md"])
    assert factory.reviewed_docs(root, "main") == [
        "AGENTS.md",
        "docs/c.md",
        "site/a.md",
        "site/deep/b.md",
    ]


def test_a_change_can_t_take_its_own_docs_out_of_review(tmp_path) -> None:
    """R5: the checkout's `[docs]` is never read."""
    root = _change(tmp_path)
    _docs_on_main(root, '[docs]\nreviewed = ["site/"]\n', ("site/a.md", "a\n"))
    (root / ".sdlc" / "config.toml").write_text("[docs]\nreviewed = []\n", encoding="utf-8")
    assert factory._docs_at(root, "main")[1] == ["site/"]
    assert "site/a.md" in factory.reviewed_docs(root, "main")


# ---------------------------------------------------------------- R4, R11: the join


def test_a_changed_reviewed_doc_calls_it_in(tmp_path) -> None:
    """R4 (a): even under `tests/`, a reviewed doc that changed."""
    root = _change(tmp_path)
    _docs_on_main(root, '[docs]\nreviewed = ["tests/docs/"]\n', ("tests/docs/a.md", "a\n"))
    _touch(root, "tests/docs/a.md")
    assert _joins(root)


def test_a_doc_naming_a_changed_path_calls_it_in(tmp_path) -> None:
    """R4 (b): by its path, or by its file name alone."""
    root = _change(tmp_path)
    _docs_on_main(root, "", ("AGENTS.md", "Run tests/test_a.py first.\n"))
    _touch(root, "tests/test_a.py")
    assert _joins(root)
    root = _change(tmp_path / "two")
    _docs_on_main(root, "", ("AGENTS.md", "Run test_b.py first.\n"))
    _touch(root, "tests/unit/test_b.py")
    assert _joins(root)


def test_a_claude_md_above_a_changed_path_calls_it_in(tmp_path) -> None:
    """R4 (c)."""
    root = _change(tmp_path)
    _docs_on_main(root, "", ("tests/CLAUDE.md", "how the tests run\n"))
    _touch(root, "tests/test_a.py")
    assert _joins(root)


def test_a_run_that_ran_docs_keeps_running_it(tmp_path) -> None:
    """R4 (d): a rework that touches only `tests/` keeps the review."""
    root = _change(tmp_path)
    _touch(root, "tests/test_a.py")
    base = factory._base(root)
    changed = factory._changed_paths(root, base)
    docs = factory.reviewed_docs(root, base)
    assert not factory.docs_review(docs, [], changed, root)
    rounds = [{"round": 1, "reviews": {"code": {}, "docs": {}}}]
    assert factory.docs_review(docs, rounds, changed, root)


@pytest.mark.parametrize(
    ("docs", "files", "touched", "joins"),
    [
        ("", (), "src/a.py", True),
        ("", (), "tests/test_a.py", False),
        ("", (("AGENTS.md", "Run tests/test_a.py.\n"),), "tests/test_a.py", True),
        ("", (("AGENTS.md", "Run test_a.py.\n"),), "tests/unit/test_a.py", True),
        ("", (("tests/CLAUDE.md", "the tests\n"),), "tests/test_a.py", True),
        ('[docs]\nreviewed = ["tests/docs/"]\n', (("tests/docs/a.md", "a\n"),), "tests/docs/a.md",
         True),
        ('[docs]\nreviewed = ["site/*.md"]\n', (("site/a.md", "see tests/test_b.py\n"),),
         "tests/test_b.py", True),
    ],
)  # fmt: skip
def test_ship_and_the_factory_join_by_the_same_rule(tmp_path, docs, files, touched, joins) -> None:
    """R4, R9: `factory.py`'s `docs_review()` and `sdlc.py`'s `_docs_applies()` are copies of one
    rule, clauses (a), (b), (c) and (e), each over its own reading of the base branch's list; this
    pins them in step."""
    root = _change(tmp_path)
    _docs_on_main(root, docs, *files)
    _touch(root, touched)
    base = factory._base(root)
    changed = factory._changed_paths(root, base)
    in_factory = factory.docs_review(factory.reviewed_docs(root, base), [], changed, root)
    at_ship = sdlc._docs_applies(root, sdlc._docs_list_at(root, base), changed) is None
    assert (in_factory, at_ship) == (joins, joins)


def test_a_path_outside_tests_calls_it_in(tmp_path) -> None:
    """R4 (e): `src/a.py`, which no doc names, joins; `tests/test_a.py` alone, or the change
    folder alone, doesn't."""
    root = _change(tmp_path)
    assert not _joins(root), "the change folder alone"
    _touch(root, "tests/test_a.py")
    assert not _joins(root), "only a test no doc names, with no CLAUDE.md above it"
    _touch(root, "src/a.py")
    assert _joins(root)


def test_the_round_expects_docs_whatever_the_lists_say(tmp_path, capsys) -> None:
    """R4, R11: a host whose `reviewers` is `code` alone still has its docs checked, and a round
    is complete only with the docs review."""
    root = _change(tmp_path)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text('reviewers = ["code"]\n', encoding="utf-8")
    _touch(root, "src/a.py")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert out["missing"] == ["code", "docs"]
    _review(root, 1, "code", "VERDICT: PASS")
    assert _verdicts(root, capsys)["missing"] == ["docs"], "incomplete without it"


def test_the_full_depth_counts_docs_in_every_round() -> None:
    """R8."""
    cfg = factory.load_config(Path("/nonexistent"))[0]
    assert factory.max_runs(cfg) == 2 + 3 * (len(FULL) + 1 + 2 + 2)


# ---------------------------------------------------------------- R6, R7: the prompt


def test_the_prompt_names_the_docs_and_their_stale_lines(tmp_path) -> None:
    """R6: the listed docs that exist, and each doc line naming a path the diff deletes or
    renames."""
    root = _change(tmp_path)
    _docs_on_main(
        root,
        '[docs]\ncontext = ["AGENTS.md", "CLAUDE.md"]\nreviewed = ["site/"]\n',
        ("AGENTS.md", "intro\nsee src/old.py for it\n"),
        ("site/a.md", "src/gone.py\n"),
        ("src/old.py", "def old():\n    return 1\n"),
        ("src/gone.py", "GONE = 'a different file'\n"),
    )
    _git(root, "mv", "src/old.py", "src/new.py")
    _git(root, "rm", "-q", "src/gone.py")
    text = factory.docs_prompt(root, "main")
    assert text.startswith(" Docs: AGENTS.md, site/a.md.")
    assert "AGENTS.md:2 names src/old.py, renamed to src/new.py" in text
    assert "site/a.md:1 names src/gone.py, deleted" in text
    assert "CLAUDE.md" not in text, "a listed doc that doesn't exist isn't named"
    root = _change(tmp_path / "two")
    assert factory.docs_prompt(root, "main").endswith("Stale lines: none.")


def test_the_code_reviewer_has_no_context_pass() -> None:
    """R7: the two never raise the same line."""
    agent = (ROOT / "plugins" / "factory" / "agents" / "reviewer-code.md").read_text("utf-8")
    assert "**Context.**" not in agent and "[docs] context" not in agent
    assert "`[context]`" not in agent


# ---------------------------------------------------------------- R12: the docs that say so


def _read(rel: str) -> str:
    return " ".join((ROOT / rel).read_text(encoding="utf-8").split())


def test_reference_names_every_docs_key() -> None:
    """R12.2: every `[docs]` key `config` knows is named, as `docs.<key>` or in the `[docs]`
    example, and `docs.reviewed` both ways."""
    text = (ROOT / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    example = text.split("\n[docs]\n", 1)[1].split("\n\n", 1)[0]
    named = [k for k in sdlc.CONFIG_KEYS["docs"] if f"docs.{k}" in text or f"\n{k} = " in example]
    assert named == list(sdlc.CONFIG_KEYS["docs"])
    assert "`docs.reviewed`" in text and "\nreviewed = [" in example


def test_the_factory_readme_has_a_row_for_every_reviewer() -> None:
    """R12.3."""
    rows = {
        line.split("|")[1].strip(): line
        for line in (ROOT / "plugins" / "factory" / "README.md").read_text("utf-8").splitlines()
        if line.startswith("| `")
    }
    assert [r for r in factory.REVIEWERS if f"`reviewer-{r}`" not in rows] == []
    docs = rows["`reviewer-docs`"]
    assert "sonnet" in docs and "joins on its own" in docs, docs
    assert "context docs" not in rows["`reviewer-code`"], "the code reviewer reads no docs now"


def test_the_build_skill_says_docs_joins_on_its_own() -> None:
    """R12.5."""
    assert "`docs`, which joins on its own" in _read("plugins/factory/skills/build/SKILL.md")


def test_agents_md_names_every_core_agent() -> None:
    """R12.6: each `agents/*.md` as `sdlc:<stem>`."""
    text = _read("AGENTS.md")
    stems = [p.stem for p in sorted((ROOT / "agents").glob("*.md"))]
    assert "docs" in stems and [s for s in stems if f"sdlc:{s}" not in text] == []
    assert "four more core agents, `sdlc:security`, `sdlc:docs`, `sdlc:ui` and `sdlc:ux`" in text
