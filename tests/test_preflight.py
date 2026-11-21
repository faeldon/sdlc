"""`preflight`, everything ship's Step 0 looks up about a change in one read-only call, and its
`--question`, ship's WAIT question with each clause decided by code, not the skill's prose."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_preflight", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

NITS = """\
# Inbox

> The note.

## [2026-10-04-1] [nit] A registry that isn't UTF-8 crashes status

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: med
Raised by: 003-test-lifetimes (correctness)

## [2026-10-20-1] [nit] An idiom

Theme: style
Paths: docs/
Cost: M
Value: low
Raised by: 009-drift-message (cost)
"""

INTENT = """\
---
id: 001
slug: reopen-drafts
tier: 2
impact:
stage: build
created: 2026-10-01
updated: 2026-10-01
idea:
depends_on:
closes: [12, 15]
---

# 001 — Reopen drafts
"""

CHECKS = """\
# Acceptance checks

> The note.

## The list reopens a draft

```sh
true
```
"""

FULL = (
    "Fix F2 and F4, then commit this, touching sensitive paths <a> and <b>, "
    "without the fresh review (<why>), with how to recover it shown, "
    "with the context update shown, the nits shown recorded in .sdlc/work/inbox.md, "
    "the bugs shown filed in .sdlc/work/inbox.md, "
    "closing #N and #M when it lands and splitting #K off as a seed, and "
    ".sdlc/work/NNN-<slug>/ stamped shipped, then update its issue? "
    "(yes / fix all 5 first / commit without fixing, recording F2 and F4 as nits / "
    "edit the message)"
)


def _finding(n: int, rank: str = "nit", disposition: str = "recorded") -> dict:
    return {"id": f"F{n}", "rank": rank, "disposition": disposition}


# F2 and F4 recommended, five that could be fixed (F2, F3, F4, F5, F10), and four that can't: one
# already fixed, one dismissed `wrong`, one `intentional`, one pre-existing.
FIVE = [
    _finding(1, "important", "fixed"),
    _finding(2, "nit", "fix"),
    _finding(3, "nit", "recorded"),
    _finding(4, "nit", "fix"),
    _finding(5, "nit", "minor"),
    _finding(6, "nit", "wrong"),
    _finding(7, "preexisting", "recorded"),
    _finding(9, "nit", "intentional"),
    _finding(10, "nit", "recorded"),
]


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


@pytest.fixture
def change(tmp_path: Path) -> tuple[Path, Path]:
    """A repo on a change's branch: notes with an undone item, a nit its diff touches, two issues
    on `closes:`, an acceptance check and a context doc above a changed path."""
    root = tmp_path / "repo"
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    (root / ".sdlc" / "work" / "inbox.md").write_text(NITS, encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "AGENTS.md").write_text("the scripts\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "checkout", "-q", "-b", "001-reopen-drafts")
    folder = root / ".sdlc" / "work" / "001-reopen-drafts"
    folder.mkdir()
    (folder / "intent.md").write_text(INTENT, encoding="utf-8")
    (folder / "notes.md").write_text("# Notes\n\n- [ ] the empty list\n", encoding="utf-8")
    (folder / "checks.md").write_text(CHECKS, encoding="utf-8")
    (root / "scripts" / "sdlc.py").write_text("x = 1\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "work")
    return root, folder


def _json(capsys, run) -> tuple[int, dict]:
    code = run()
    return code, json.loads(capsys.readouterr().out)


def test_preflight_parts_equal_the_single_commands(change, capsys) -> None:
    root, _ = change
    code, out = _json(capsys, lambda: sdlc.cmd_preflight(root, "001"))
    assert code == 0, out["problems"]
    assert (out["change"], out["tier"], out["stage"]) == ("001-reopen-drafts", 2, "build")
    assert out["folder"] == ".sdlc/work/001-reopen-drafts"
    singles = {
        "undone": lambda: sdlc.cmd_undone(root, "001"),
        "nits": lambda: sdlc.cmd_nits(root, None, "001"),
        "closes": lambda: sdlc.cmd_closes(root, "001"),
        "checks": lambda: sdlc.cmd_checks(root, "001"),
        "context": lambda: sdlc.cmd_context(root),
    }
    for part, run in singles.items():
        assert out[part] == _json(capsys, run)[1], part
    # The fixture puts something in every part, so equal is never equally empty.
    assert [i["text"] for i in out["undone"]["items"]] == ["the empty list"]
    assert [n["id"] for n in out["nits"]["nits"]] == ["2026-10-04-1"]
    assert [c["number"] for c in out["closes"]["closes"]] == [12, 15]
    assert [c["name"] for c in out["checks"]["checks"]] == ["The list reopens a draft"]
    assert "scripts/AGENTS.md" in [d["path"] for d in out["context"]["docs"]]


def test_preflight_writes_nothing(change, capsys) -> None:
    root, folder = change
    before = (_git(root, "status", "--porcelain"), sorted(p.name for p in folder.iterdir()))
    sdlc.cmd_preflight(root, "001")
    capsys.readouterr()
    after = (_git(root, "status", "--porcelain"), sorted(p.name for p in folder.iterdir()))
    assert before == after


def test_preflight_exits_1_on_a_part_s_problems_and_prints_every_part(change, capsys) -> None:
    root, folder = change
    (folder / "checks.md").write_text("# Acceptance checks\n\n```sh\ntrue\n```\n")
    code, out = _json(capsys, lambda: sdlc.cmd_preflight(root, "001"))
    assert code == 1
    assert out["problems"] and all(p.startswith("checks: ") for p in out["problems"])
    assert {"undone", "nits", "closes", "checks", "context"} <= out.keys()


def test_preflight_names_the_branches_that_apply(change, capsys) -> None:
    """The fixture has an undone item and two issues on `closes:`; a factory run's decision puts
    its file first."""
    root, folder = change
    _, out = _json(capsys, lambda: sdlc.cmd_preflight(root, "001"))
    assert out["branches"] == ["undone.md", "closes.md"]
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    _, out = _json(capsys, lambda: sdlc.cmd_preflight(root, "001"))
    assert out["branches"] == ["factory.md", "undone.md", "closes.md"]


# A plain change's parts: nothing undone, nothing to close, no risk, no cases.
PLAIN = {
    "undone": {"items": []},
    "closes": {"closes": []},
    "risk": {"sensitive": [], "irreversible": [], "deep": False},
    "cases": {"available": False},
    "passes": {name: {"applies": False, "why": "x"} for name in ("security", "behaviour", "ui")},
}


def _passes(*names: str) -> dict:
    """The `passes` part with `names` applying."""
    return {n: {"applies": n in names, "why": None} for n in ("security", "behaviour", "ui")}


@pytest.mark.parametrize(
    "part, value, expected",
    [
        (None, None, []),
        ("undone", {"items": [{"line": 3, "text": "x"}]}, ["undone.md"]),
        ("closes", {"closes": [{"number": 12}]}, ["closes.md"]),
        ("risk", {"sensitive": [], "irreversible": ["defaults/x.md"], "deep": False},
         ["recover.md"]),
        ("risk", {"sensitive": ["check.sh"], "irreversible": [], "deep": True}, ["fresh.md"]),
        ("risk", None, []),
        ("cases", {"available": True, "cases": {}, "scope": ["ship"]}, ["cases.md"]),
        ("cases", {"available": True, "cases": {}, "scope": []}, []),
        ("passes", _passes("security"), ["security.md"]),
        ("passes", _passes("behaviour"), ["behaviour.md"]),
        ("passes", _passes("ui"), ["ui.md"]),
        ("passes", _passes("ui", "security", "behaviour"),
         ["security.md", "behaviour.md", "ui.md"]),
    ],
)  # fmt: skip
def test_ship_branches_condition(tmp_path: Path, part, value, expected) -> None:
    parts = {**PLAIN, **({part: value} if part else {})}
    assert sdlc.ship_branches(parts, tmp_path) == expected


def test_preflight_refuses_an_unknown_id(change, capsys) -> None:
    root, _ = change
    assert sdlc.cmd_preflight(root, "009") == 1
    assert capsys.readouterr().out == ""


def _ask(**kw) -> tuple[str | None, str | None]:
    args = {"folder": ".sdlc/work/001-reopen-drafts", "closes": [], "target": "github",
            "context": False, "nits": False, "closing": [], "split": [],
            "register": ".sdlc/work/inbox.md"}  # fmt: skip
    return sdlc.ship_question(**(args | kw))


def test_question_with_every_clause_matches_ship_s_example() -> None:
    """The skill's example sentence, every clause in, is what the script renders: N, M and K
    stand in for the numbers, and the folder for the change's."""
    question, why = _ask(folder=".sdlc/work/NNN-<slug>", closes=[1, 2, 3], context=True,
                         nits=True, bugs=True, closing=[1, 2], split=[3],
                         sensitive=["<a>", "<b>"], irreversible=True,
                         fresh={"ran": False, "why": "<why>"}, findings=FIVE)  # fmt: skip
    assert why is None
    assert question == FULL.replace("#N", "#1").replace("#M", "#2").replace("#K", "#3")
    skill = (ROOT / "skills" / "ship" / "SKILL.md").read_text(encoding="utf-8")
    assert FULL in " ".join(skill.split()), "the skill shows the same sentence"


SHIPPED = ".sdlc/work/001-reopen-drafts/ stamped shipped"


@pytest.mark.parametrize(
    "kw, expected",
    [
        ({}, f"Commit this, with {SHIPPED}, then update its issue?"),
        ({"target": "none"}, f"Commit this, with {SHIPPED}? (yes"),
        ({"context": True}, f"Commit this, with the context update shown, and {SHIPPED}, then"),
        ({"nits": True}, "Commit this, the nits shown recorded in .sdlc/work/inbox.md, and .sdlc"),
        ({"bugs": True}, "Commit this, the bugs shown filed in .sdlc/work/inbox.md, and .sdlc"),
        ({"closes": [4], "closing": [4]}, "Commit this, closing #4 when it lands, and .sdlc"),
        ({"closes": [4, 5], "closing": [5, 4]}, "closing #4 and #5 when it lands, and"),
        ({"closes": [4, 5, 6], "closing": [4, 5, 6]}, "closing #4, #5 and #6 when it lands, and"),
        ({"closes": [4], "split": [4]}, "Commit this, splitting #4 off as a seed, and"),
        ({"closes": [4, 5], "split": [4, 5]}, "splitting #4 and #5 off as seeds, and"),
        (
            {"closes": [4, 5], "closing": [4], "split": [5]},
            "closing #4 when it lands and splitting #5 off as a seed, and",
        ),
    ],
)
def test_question_clause(kw, expected) -> None:
    question, why = _ask(**kw)
    assert why is None and question.startswith("Commit this") and expected in question
    if "context" not in kw:
        assert "context update" not in question
    if "nits" not in kw:
        assert "nits shown" not in question
    if "bugs" not in kw:
        assert "bugs shown" not in question
    if not kw.get("closing"):
        assert "closing" not in question
    if not kw.get("split"):
        assert "splitting" not in question
    assert question.endswith("? (yes / edit the message)")


@pytest.mark.parametrize(
    "findings, lead, options",
    [
        ([], "Commit this, with", "(yes / edit the message)"),
        ([_finding(1, "nit", "fixed")], "Commit this, with", "(yes / edit the message)"),
        (
            [_finding(1, "nit", "recorded"), _finding(2, "nit", "minor")],
            "Commit this, with",
            "(yes / fix all 2 first / edit the message)",
        ),
        (
            [_finding(1, "nit", "fix")],
            "Fix F1, then commit this, with",
            "(yes / commit without fixing, recording F1 as a nit / edit the message)",
        ),
        (
            [_finding(1, "important", "fix"), _finding(2, "nit", "fix")],
            "Fix F1 and F2, then commit this, with",
            "(yes / edit the message)",
        ),
        (
            [_finding(1, "important", "fix"), _finding(2, "nit", "recorded")],
            "Fix F1, then commit this, with",
            "(yes / fix all 2 first / edit the message)",
        ),
        (FIVE, "Fix F2 and F4, then commit this, with", "(yes / fix all 5 first / commit"),
    ],
    ids=[
        "none",
        "all-fixed",
        "fixable-only",
        "one-nit",
        "important-in-fix",
        "more-fixable",
        "five",
    ],  # fmt: skip
)
def test_question_leads_with_what_ship_recommends(findings, lead, options) -> None:
    question, why = _ask(findings=findings)
    assert why is None and question.startswith(lead) and options in question


def test_an_open_finding_asks_to_fix_and_review_again_never_to_commit() -> None:
    findings = [
        _finding(1, "important", "open"),
        _finding(2, "nit", "fix"),
        _finding(3, "nit", "recorded"),
    ]
    question, why = _ask(findings=findings, context=True, closes=[4], closing=[4])
    assert why is None
    assert (
        question == "Fix F1 and F2, then review again? (yes / fix all 3 first / edit the findings)"
    )
    question, why = _ask(findings=findings, closes=[4])
    assert question is None and "#4 on closes: but given to neither" in why


def test_a_repeated_issue_number_reads_once() -> None:
    question, _ = _ask(closes=[4], closing=[4, 4])
    assert "closing #4 when it lands" in question and "#4 and #4" not in question


def test_the_old_option_is_gone_everywhere() -> None:
    for folder in ("scripts", "skills"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and path.suffix in (".py", ".md"):
                assert "fix a finding first" not in path.read_text(encoding="utf-8"), path


@pytest.mark.parametrize(
    "kw, why",
    [
        ({"closes": [4], "closing": [4, 9]}, "#9 not on the change's closes: line"),
        ({"closes": [4], "closing": [4], "split": [4]}, "#4 given to both"),
        ({"closes": [4, 5], "closing": [4]}, "#5 on closes: but given to neither"),
    ],
    ids=["not-on-closes", "given-to-both", "left-out"],
)
def test_question_refuses_issues_that_don_t_partition_closes(kw, why) -> None:
    question, said = _ask(**kw)
    assert question is None and why in said


def test_the_question_s_flags_without_question_are_refused_not_dropped(
    change, capsys, monkeypatch
) -> None:
    root, _ = change
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "preflight", "001", "--closing", "12", "--nits"])
    assert sdlc.main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "--nits, --closing only word ship's question; add --question" in captured.err


def test_question_through_the_command(change, capsys) -> None:
    root, _ = change
    assert sdlc.cmd_ship_question(root, "001", True, False, [12], [15]) == 0
    printed = capsys.readouterr().out.strip()
    assert printed == (
        "Commit this, with the context update shown, closing #12 when it lands and splitting "
        "#15 off as a seed, and .sdlc/work/001-reopen-drafts/ stamped shipped? "
        "(yes / edit the message)"
    ), "no tracker configured, so no issue update"
    assert sdlc.cmd_ship_question(root, "001", False, False, [12], []) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and "#15 on closes: but given to neither" in captured.err


def test_the_command_reads_findings_md_for_the_recommendation_and_the_fresh_review(
    change, capsys
) -> None:
    root, folder = change
    (folder / "findings.md").write_text(
        "# Findings\n\n> The note.\n> Fresh review: skipped, no Agent tool here\n\n"
        "## F1. [nit] [cost] A helper with one caller\n\nEvidence: a.py:1\nClass: c\n"
        "Disposition: fix\nFix: inline it\n",
        encoding="utf-8",
    )
    assert sdlc.cmd_ship_question(root, "001", False, False, [12], [15]) == 0
    printed = capsys.readouterr().out.strip()
    assert printed.startswith("Fix F1, then commit this, without the fresh review (no Agent tool")
    assert printed.endswith(
        "(yes / commit without fixing, recording F1 as a nit / edit the message)"
    )
    (folder / "findings.md").write_text(
        "# Findings\n\n## F1. [nit] [cost] A helper\n\n"
        "Evidence: a.py:1\nClass: c\nDisposition: fix\n",
        encoding="utf-8",
    )
    assert sdlc.cmd_ship_question(root, "001", False, False, [12], [15]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and "`fix` with no `Fix:`" in captured.err


def test_preflight_and_nits_are_allowed_without_a_prompt() -> None:
    assert {"preflight", "nits", "findings"} <= set(sdlc.READ_ONLY)


# ---------------------------------------------------------------- ship's passes (143)

SPEC = """\
---
id: 001
slug: reopen-drafts
kind: spec
created: 2026-10-01
updated: 2026-10-01
---

# 001 — Reopen drafts · spec

## Requirements

R1. A saved draft reopens with its text, and `test_reopen` fails if it doesn't.

## Verification

```bash
python -c "import drafts"
```
"""

UI = """\
[ui]
serve = "python -m http.server {port}"
shoot = "shoot {url} {out}"
paths = ["web/"]
pages = ["/", "/drafts"]
widths = [[1280, 800]]
"""


def _on_main(root: Path, files: dict[str, str | None]) -> None:
    """Commit `files` (None: remove one) on `main`, then rebase the change's branch onto it, as
    `sdlc.py base` would: `[review]` is read from the checkout's copy of the base branch."""
    _git(root, "checkout", "-q", "main")
    for rel, text in files.items():
        if text is None:
            _git(root, "rm", "-q", "--ignore-unmatch", rel)
            continue
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
        _git(root, "add", rel)
    _git(root, "commit", "-q", "--allow-empty", "-m", "base")
    _git(root, "checkout", "-q", "001-reopen-drafts")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "rebase", "-q", "main")


def _passes_of(capsys, root: Path) -> dict:
    sdlc.cmd_preflight(root, "001")
    return json.loads(capsys.readouterr().out)


def test_preflight_passes_security(change, capsys) -> None:
    """R2: a deep diff with no decision.md gets the security pass; shallow, or a factory run,
    doesn't."""
    root, folder = change
    out = _passes_of(capsys, root)
    assert out["passes"]["security"]["applies"] is False and "security.md" not in out["branches"]
    _on_main(root, {".sdlc/config.toml": '[review]\nsensitive = ["scripts/"]\n'})
    out = _passes_of(capsys, root)
    assert out["risk"]["deep"] and out["passes"]["security"] == {"applies": True, "why": None}
    assert "security.md" in out["branches"]
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    out = _passes_of(capsys, root)
    assert out["passes"]["security"]["applies"] is False
    assert "factory" in out["passes"]["security"]["why"]


def test_preflight_passes_behaviour(change, capsys) -> None:
    """R3: Tier 2 with a filled spec and no decision.md; never Tier 1, an unfilled spec or a
    factory run."""
    root, folder = change
    out = _passes_of(capsys, root)
    assert out["passes"]["behaviour"]["applies"] is False, "no spec.md"
    (folder / "spec.md").write_text(
        "# Spec\n\n## Requirements\n\n<one>\n\n<two>\n\n<three>\n\n<four>\n", encoding="utf-8"
    )
    assert sdlc.is_unfilled(folder / "spec.md")
    assert _passes_of(capsys, root)["passes"]["behaviour"]["applies"] is False, "unfilled"
    (folder / "spec.md").write_text(SPEC, encoding="utf-8")
    out = _passes_of(capsys, root)
    assert out["passes"]["behaviour"] == {"applies": True, "why": None}
    assert "behaviour.md" in out["branches"]
    intent = folder / "intent.md"
    intent.write_text(INTENT.replace("tier: 2", "tier: 1"), encoding="utf-8")
    assert _passes_of(capsys, root)["passes"]["behaviour"]["applies"] is False, "Tier 1"
    intent.write_text(INTENT, encoding="utf-8")
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    assert _passes_of(capsys, root)["passes"]["behaviour"]["applies"] is False, "factory"


def test_preflight_names_none_of_the_passes_on_a_factory_run(change, capsys) -> None:
    """R19: a deep, Tier 2, [ui]-touching factory run reads factory.md, never a new branch."""
    root, folder = change
    _on_main(root, {".sdlc/config.toml": '[review]\nsensitive = ["web/"]\n',
                    ".sdlc/factory.toml": UI})  # fmt: skip
    (root / "web").mkdir()
    (root / "web" / "drafts.css").write_text("a {}\n", encoding="utf-8")
    (folder / "spec.md").write_text(SPEC, encoding="utf-8")
    out = _passes_of(capsys, root)
    assert {"security.md", "behaviour.md", "ui.md"} <= set(out["branches"])
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    out = _passes_of(capsys, root)
    assert not {"security.md", "behaviour.md", "ui.md"} & set(out["branches"])
    assert not any(p["applies"] for p in out["passes"].values())


def _web(root: Path) -> Path:
    (root / "web").mkdir(exist_ok=True)
    css = root / "web" / "drafts.css"
    css.write_text("a {}\n", encoding="utf-8")
    return css


def test_preflight_passes_ui(change, capsys) -> None:
    """R4: only a complete [ui] on the base branch, a diff touching its paths, and no
    decision.md."""
    root, folder = change
    _web(root)
    assert _passes_of(capsys, root)["passes"]["ui"]["applies"] is False, "no factory.toml"
    _on_main(root, {".sdlc/factory.toml": UI.replace('shoot = "shoot {url} {out}"\n', "")})
    assert _passes_of(capsys, root)["passes"]["ui"]["applies"] is False, "no shoot"
    _on_main(root, {".sdlc/factory.toml": UI.replace('["web/"]', '["app/"]')})
    out = _passes_of(capsys, root)["passes"]["ui"]
    assert out["applies"] is False and "no [ui] path" in out["why"], "untouched"
    _on_main(root, {".sdlc/factory.toml": UI})
    out = _passes_of(capsys, root)
    assert out["passes"]["ui"]["applies"] is True and "ui.md" in out["branches"]
    assert out["passes"]["ui"]["shots"] == []
    assert out["passes"]["ui"]["why"].startswith("no screenshots of this change")
    # With the factory enabled, the why points at the command that takes them (seed
    # 2026-11-18-57); ship never runs it.
    settings = root / ".claude" / "settings.local.json"
    settings.parent.mkdir(exist_ok=True)
    for on, why in ((False, "sdlc-factory isn't enabled, so none can be taken"),
                    (True, "take them with factory.py shots 001 --round 1 --role ui")):  # fmt: skip
        enabled = {"enabledPlugins": {"sdlc-factory@sdlc": on}}
        settings.write_text(json.dumps(enabled), encoding="utf-8")
        out = _passes_of(capsys, root)["passes"]["ui"]
        assert out["why"] == f"no screenshots of this change: {why}", out
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    assert _passes_of(capsys, root)["passes"]["ui"]["applies"] is False, "factory"


def test_ui_is_read_from_the_base_branch(change, capsys) -> None:
    """R4: a change that removes or narrows [ui] in its own checkout keeps its UI review."""
    root, _ = change
    _on_main(root, {".sdlc/factory.toml": UI})
    _web(root)
    toml = root / ".sdlc" / "factory.toml"
    toml.write_text(UI.replace('["web/"]', '["app/"]'), encoding="utf-8")
    assert _passes_of(capsys, root)["passes"]["ui"]["applies"] is True, "narrowed"
    toml.unlink()
    assert _passes_of(capsys, root)["passes"]["ui"]["applies"] is True, "removed"


def _shoot(root: Path, label: str, role: str = "ui", problem: str | None = None,
           skip: str | None = None, when: float = 2_000_000_000.0) -> Path:  # fmt: skip
    """A screenshot set as `factory.py shots` leaves one, its record stamped `when`."""
    import os

    where = root / ".sdlc" / "reports" / "shots" / "001-reopen-drafts" / label / role
    where.mkdir(parents=True)
    for name in ("index-1280x800.png", "drafts-1280x800.png"):
        if name != skip:
            (where / name).write_bytes(b"\x89PNG\r\n\x1a\n")
    record = where / "shots.json"
    record.write_text(json.dumps({"problem": problem, "shots": []}), encoding="utf-8")
    os.utime(record, (when, when))
    return record


def test_current_shots_are_listed_newest_first(change, capsys) -> None:
    """R6: the newest set that finished, with every PNG, newer than every changed [ui] path."""
    import os

    root, _ = change
    _on_main(root, {".sdlc/factory.toml": UI})
    css = _web(root)
    os.utime(css, (1_000_000_000, 1_000_000_000))
    _shoot(root, "round-1", when=1_500_000_000)
    _shoot(root, "round-2", "ux", when=1_600_000_000)
    out = _passes_of(capsys, root)["passes"]["ui"]
    shots = ".sdlc/reports/shots/001-reopen-drafts/round-2/ux"
    assert out["shots"] == [f"{shots}/index-1280x800.png", f"{shots}/drafts-1280x800.png"]
    assert out["why"] is None


@pytest.mark.parametrize(
    "kw, why",
    [
        ({"problem": "the dev server came up on none of 3 ports"}, "didn't finish: the dev server"),
        ({"skip": "drafts-1280x800.png"}, "screenshots missing drafts-1280x800.png"),
    ],
    ids=["problem", "missing-png"],
)
def test_a_set_that_didn_t_finish_is_never_listed(change, capsys, kw, why) -> None:
    import os

    root, _ = change
    _on_main(root, {".sdlc/factory.toml": UI})
    os.utime(_web(root), (1_000_000_000, 1_000_000_000))
    _shoot(root, "round-1", **kw)
    out = _passes_of(capsys, root)["passes"]["ui"]
    assert out["shots"] == [] and why in out["why"]


def test_stale_shots_are_not_current(change, capsys) -> None:
    """R6: a changed [ui] path touched after the shots leaves them unlisted, saying which."""
    import os

    root, _ = change
    _on_main(root, {".sdlc/factory.toml": UI})
    css = _web(root)
    os.utime(css, (1_000_000_000, 1_000_000_000))
    _shoot(root, "round-1", when=1_500_000_000)
    assert _passes_of(capsys, root)["passes"]["ui"]["shots"], "current before the edit"
    os.utime(css, (1_700_000_000, 1_700_000_000))
    out = _passes_of(capsys, root)["passes"]["ui"]
    assert out["shots"] == [] and out["why"] == "screenshots older than web/drafts.css"


# ---------------------------------------------------------------- ship's preview (210)

TWO_FINDINGS = (
    "# Findings\n\n> The note.\n\n"
    "## F1. [nit] [cost] A helper with one caller\n\nEvidence: a.py:1\nClass: c\n"
    "Disposition: fix\nFix: inline it\n\n"
    "## F2. [important] [correctness] The empty list crashes\n\nEvidence: b.py:2\nClass: c\n"
    "Disposition: fixed\n"
)


def _preview(root: Path, capsys, *flags: str) -> tuple[int, str, str]:
    import os

    here = os.getcwd()
    os.chdir(root)
    try:
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("sys.argv", ["sdlc.py", "preflight", "001", *flags])
            code = sdlc.main()
    finally:
        os.chdir(here)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_preflight_preview_lists_findings_paths_and_stamp(change, capsys) -> None:
    """210 R7: what ship's yes commits, by the script: each finding with its id, rank and
    disposition, every path the diff touches against the merge base (a rename by both), and the
    stamp line, plain text, whatever clause flags `--question` was given."""
    root, folder = change
    (folder / "findings.md").write_text(TWO_FINDINGS, encoding="utf-8")
    _git(root, "mv", "README.md", "READ.md")
    code, out, err = _preview(root, capsys, "--preview", "--context", "--closing", "12")
    assert code == 0, err
    assert out.splitlines() == [
        "Findings:",
        "F1 nit → fix: A helper with one caller",
        "F2 important → fixed: The empty list crashes",
        "Paths:",
        "A .sdlc/work/001-reopen-drafts/checks.md",
        "A .sdlc/work/001-reopen-drafts/intent.md",
        "A .sdlc/work/001-reopen-drafts/notes.md",
        "R README.md → READ.md",
        "A scripts/sdlc.py",
        "A .sdlc/work/001-reopen-drafts/findings.md",
        ".sdlc/work/001-reopen-drafts/ stamped shipped",
    ]


def test_preflight_preview_without_findings_says_none(change, capsys) -> None:
    root, _ = change
    code, out, _ = _preview(root, capsys, "--preview")
    assert code == 0 and out.splitlines()[0] == "Findings: none"


def test_preflight_preview_is_cut_past_forty_lines(change, capsys) -> None:
    """210 R4, R7: a diff of many files keeps the first 40 lines; ship shows the rest above."""
    root, _ = change
    for n in range(50):
        (root / f"f{n:02}.txt").write_text("x\n", encoding="utf-8")
    code, out, _ = _preview(root, capsys, "--preview")
    lines = out.splitlines()
    assert code == 0 and len(lines) == sdlc.PREVIEW_LINES + 1
    assert lines[-1].startswith("… ") and lines[-1].endswith(" more lines, shown above")


def test_preflight_preview_writes_nothing(change, capsys) -> None:
    """210 R12."""
    root, folder = change
    (folder / "findings.md").write_text(TWO_FINDINGS, encoding="utf-8")
    before = _git(root, "status", "--porcelain")
    assert _preview(root, capsys, "--preview")[0] == 0
    assert _git(root, "status", "--porcelain") == before


def test_preflight_preview_refuses_a_bad_findings_md_as_the_question_does(change, capsys) -> None:
    root, folder = change
    (folder / "findings.md").write_text(
        "# Findings\n\n## F1. [nit] [cost] A helper\n\nEvidence: a.py:1\nClass: c\n"
        "Disposition: fix\n",
        encoding="utf-8",
    )
    code, out, err = _preview(root, capsys, "--preview")
    question = _preview(root, capsys, "--question", "--closing", "12", "--split", "15")
    assert (code, out) == (1, "") and err == question[2]
    assert "`fix` with no `Fix:`" in err


def test_preflight_preview_and_question_are_refused_together(change, capsys) -> None:
    root, _ = change
    code, out, err = _preview(root, capsys, "--preview", "--question")
    assert (code, out) == (1, "") and "--question and --preview" in err
