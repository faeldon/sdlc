"""The factory's landing: a batch of ready changes shipped, committed, brought up to date and
closed through `sdlc.py`'s own commands, which `factory.py` runs from its own version beside it.

Each test builds a bare scratch repo and makes its changes with `sdlc.py new`, as a host does, so
the landing runs the real ship, base and close, never a copy. Nothing here runs an agent: a
review or a resolution is written as the agent would reply.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


factory = _load("factory_landing", ROOT / "plugins" / "factory" / "scripts" / "factory.py")

needs_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do")


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _run(capsys, fn, *args) -> tuple[int, dict]:
    code = fn(*args)
    return code, json.loads(capsys.readouterr().out)


# ---------------------------------------------------------------- finding its own sdlc


def _plugin(root: Path, name: str, version: str) -> None:
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": name, "version": version}), encoding="utf-8"
    )


def test_the_landing_runs_the_sdlc_of_its_own_version_from_the_clone_or_the_cache(tmp_path):
    """Read in place, the factory sits at `plugins/factory/` in the clone, whose `scripts/sdlc.py`
    is sdlc's; installed, the marketplace cache holds each plugin by name and version side by
    side. Another version's sdlc is refused: landing runs the code the factory was released with."""
    found, why = factory.sdlc_path()
    assert why is None and found == ROOT / "scripts" / "sdlc.py", "this repo is a clone"
    cache = tmp_path / "cache" / "sdlc"
    mine = cache / "sdlc-factory" / "1.9.0"
    _plugin(mine, "sdlc-factory", "1.9.0")
    theirs = cache / "sdlc" / "1.9.0"
    _plugin(theirs, "sdlc", "1.9.0")
    (theirs / "scripts").mkdir()
    (theirs / "scripts" / "sdlc.py").write_text("", encoding="utf-8")
    assert factory.sdlc_path(mine) == (theirs / "scripts" / "sdlc.py", None)
    older = cache / "sdlc-factory" / "1.8.0"
    _plugin(older, "sdlc-factory", "1.8.0")
    found, why = factory.sdlc_path(older)
    assert found is None and "no sdlc 1.8.0" in why, "never another version's"
    clone = tmp_path / "clone"
    _plugin(clone, "sdlc", "1.7.0")
    (clone / "scripts").mkdir()
    (clone / "scripts" / "sdlc.py").write_text("", encoding="utf-8")
    _plugin(clone / "plugins" / "factory", "sdlc-factory", "1.8.0")
    found, why = factory.sdlc_path(clone / "plugins" / "factory")
    assert found is None and "version 1.7.0" in why and "one version" in why


# ---------------------------------------------------------------- the message


def test_a_landed_commit_says_who_passed_its_gate_and_carries_no_review_count(tmp_path) -> None:
    folder = tmp_path / ".sdlc" / "work" / "008-reopen-drafts"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(
        "---\nid: 008\n---\n\n# 008 — Reopen saved drafts\n\n## Problem\n\nA saved draft can't be\n"
        "reopened. Nothing reads it back.\n\n## Outcome\n\nIt can.\n",
        encoding="utf-8",
    )
    message = factory.land_message(tmp_path, folder, "auto", True)
    assert message.splitlines()[0] == "Reopen saved drafts"
    assert "A saved draft can't be reopened. See .sdlc/work/008-reopen-drafts/." in message
    assert "Nothing reads it back" not in message, "the Problem's first sentence only"
    assert message.rstrip().endswith("Refs #8\nSdlc-Landed: by=auto")
    assert "Sdlc-Findings" not in message, "a missing line reads as unanswered, never as clean"
    assert "Refs" not in factory.land_message(tmp_path, folder, "person", False)


# ---------------------------------------------------------------- a batch, end to end


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "host"
    root.mkdir()
    (root / "README.md").write_text("one\ntwo\nthree\n", encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _ready(root: Path, slug: str, first_line: str, impact: str = "minor") -> Path:
    """A change made by `sdlc.py new`, built (its README's first line), at `stage: test` with the
    approver's READY and its proposed impact, as a factory run leaves one."""
    code, _, said = factory._sdlc(["new", slug, "--tier", "1", "--worktree"], root)
    assert code == 0, said
    tree = next(p for p in (root / ".claude" / "worktrees").iterdir() if p.name.endswith(slug))
    folder = tree / ".sdlc" / "work" / tree.name
    intent = folder / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8").replace("stage: plan", "stage: test"), encoding="utf-8"
    )
    (folder / "decision.md").write_text(
        f"DECISION: READY\n\nIt does what it says.\n\n- IMPACT: {impact} — a test change\n",
        encoding="utf-8",
    )
    (tree / "README.md").write_text(f"{first_line}\ntwo\nthree\n", encoding="utf-8")
    return tree


@needs_uv
def test_a_batch_lands_in_order_and_a_conflict_is_resolved_reviewed_and_closed(
    tmp_path, capsys
) -> None:
    """Two ready changes edit one line: the first lands as it is; the second's rebase conflicts,
    the rebase is left for the builder, its resolution is reviewed again at the run's depth, and
    it lands too. Each commit says who passed the gate, and nothing is left behind."""
    root = _repo(tmp_path)
    first, second = _ready(root, "first", "first's one"), _ready(root, "second", "second's one")
    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    assert code == 0 and [c["change"] for c in batch["batch"]] == [first.name, second.name]
    assert batch["clear"] is True, batch
    assert [c["impact"] for c in batch["batch"]] == ["minor", "minor"]

    code, out = _run(capsys, factory.cmd_land, first, "001", "auto")
    assert (code, out["state"]) == (0, "current"), out
    assert "Sdlc-Landed: by=auto" in _git(first, "log", "-1", "--format=%B")
    code, out = _run(capsys, factory.cmd_land_close, first, "001")
    assert code == 0 and "merge" in out["done"], out
    assert not first.exists(), "its worktree is gone"

    code, out = _run(capsys, factory.cmd_land, second, "002", "auto")
    assert (code, out["state"], out["round"]) == (0, "conflict", 1), out
    code, out = _run(capsys, factory.cmd_resolve, second, "002", False)
    assert out["conflicted"] == ["README.md"]
    code, out = _run(capsys, factory.cmd_resolve, second, "002", True)
    assert code == 1 and "conflict markers left" in out["refusals"][0], "not resolved yet"
    (second / "README.md").write_text("first's one, and second's\ntwo\nthree\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_resolve, second, "002", True)
    assert (code, out["state"]) == (0, "resolved"), out
    folder = second / ".sdlc" / "work" / second.name
    marker = (folder / "runs" / "land-resolved").read_text(encoding="utf-8").splitlines()
    assert marker == ["land-1", "README.md"], "the round under way, then the files"
    signals, _ = factory.land_signals(folder, second, "READY", factory.load_config(second)[0])
    assert "a conflict was resolved while landing" in signals, "the next gate is the person's"

    code, out = _run(capsys, factory.cmd_land_verdicts, second, "002")
    assert out["next"] == "review" and set(out["missing"]) == set(factory.DEFAULTS["reviewers"])
    reviews = folder / "reviews" / "land-1"
    for role in factory.DEFAULTS["reviewers"]:
        evidence = "\n\n## Evidence\n$ true\nexit: 0\n" if role == "behaviour" else "\n"
        (reviews / f"{role}.md").write_text(f"VERDICT: PASS{evidence}", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_land_verdicts, second, "002")
    assert out["next"] == "pass", out
    signals, _ = factory.land_signals(folder, second, "READY", factory.load_config(second)[0])
    assert "a conflict was resolved while landing" not in signals, "every reviewer saw it"

    code, out = _run(capsys, factory.cmd_land_close, second, "002")
    assert code == 0 and "merge" in out["done"], out
    log = _git(root, "log", "--format=%s", "main").splitlines()
    assert log[0] == f"Close {second.name}" and f"Close {first.name}" in log
    assert (root / "README.md").read_text(encoding="utf-8").startswith("first's one, and second's")
    landed = _git(root, "log", "-1", "--format=%B", "main~1")
    assert "Sdlc-Landed: by=auto" in landed, "the resolution and its review amended in"
    assert ".sdlc/work/002-second/reviews/land-1/behaviour.md" in _git(
        root, "show", "--name-only", "--format=", "main~1"
    )


@needs_uv
def test_a_rebased_change_is_gated_by_the_script_before_its_review(tmp_path, capsys) -> None:
    """073 R12: the behaviour check no longer runs the gate, so after a rebase the landing runs the
    base branch's check itself, into `build/land-<n>.gate.md`, before any reviewer; a red gate on
    the change as rebased is a stop, for the person to ship by hand."""
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "config.toml").write_text(
        '[commands]\ncheck = "test ! -f broken.txt"\n', encoding="utf-8"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a gate")
    tree = _ready(root, "gated", "gated's one")
    # The base branch moves under it, touching nothing the change does: a clean rebase.
    (root / "elsewhere.txt").write_text("moved on\n", encoding="utf-8")
    _git(root, "add", "elsewhere.txt")
    _git(root, "commit", "-q", "-m", "main moves on")

    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["round"]) == (0, "rebased", 1), out
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert out["next"] == "gate" and out["gate"]["command"] == "test ! -f broken.txt", out
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert (code, out["verdict"]) == (0, "PASS") and out["to"].endswith("build/land-1.gate.md")
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert (out["next"], out["missing"]) == ("review", ["behaviour"]), out

    (tree / "broken.txt").write_text("", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert (code, out["verdict"], out["attempt"]) == (1, "FAIL", 2)
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert out["next"] == "stop" and "ship it by hand" in out["problems"][0], out


@needs_uv
def test_a_refused_step_lands_nothing_of_that_change(tmp_path, capsys) -> None:
    """A change the approver proposed no impact for can't be shipped by land: it is refused before
    anything is written, and its folder and worktree stay as they were."""
    root = _repo(tmp_path)
    tree = _ready(root, "lone", "lone's one")
    folder = tree / ".sdlc" / "work" / tree.name
    (folder / "decision.md").write_text("DECISION: READY\n\nNo impact here.\n", encoding="utf-8")
    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    assert batch["clear"] is False and "proposes no `- IMPACT:`" in batch["batch"][0]["signals"][0]
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert code == 1 and "no impact" in out["refusals"][0]
    assert "stage: test" in (folder / "intent.md").read_text(encoding="utf-8")
    assert _git(tree, "log", "-1", "--format=%s") == "init", "nothing committed"
    # R7: a nit the change names leaves the register only once ship succeeds, so ship's own
    # refusal (here an open finding) leaves the register as it was, byte for byte.
    (folder / "decision.md").write_text("DECISION: READY\n\n- IMPACT: minor\n", encoding="utf-8")
    intent = folder / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8") + "\nTakes in nit 2026-11-17-11.\n", encoding="utf-8"
    )
    (folder / "findings.md").write_text(
        "# Findings\n\n> The review.\n\n## F1. [important] [correctness] Still open\n\n"
        "Evidence: README.md:1\nClass: a class\nDisposition: open\n",
        encoding="utf-8",
    )
    register = tree / ".sdlc" / "work" / "inbox.md"
    register.write_bytes(REGISTER.encode("utf-8"))
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert code == 1 and "sdlc.py ship refused" in out["refusals"][0], out
    assert register.read_bytes() == REGISTER.encode("utf-8"), "the register as it was"


@needs_uv
def test_a_change_with_acceptance_checks_or_undone_items_is_shipped_by_hand(
    tmp_path, capsys
) -> None:
    root = _repo(tmp_path)
    tree = _ready(root, "checked", "checked's one")
    folder = tree / ".sdlc" / "work" / tree.name
    (folder / "checks.md").write_text(
        "# Checks\n\n> Acceptance checks.\n\n## It runs\n\n```sh\ntrue\n```\n", encoding="utf-8"
    )
    (folder / "notes.md").write_text("# Notes\n\n- [ ] a thing left\n", encoding="utf-8")
    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    assert batch["batch"] == [] and batch["clear"] is False
    why = batch["excluded"][0]["excluded"]
    assert any("undone" in w for w in why) and any("acceptance checks" in w for w in why)
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert code == 1 and out["refusals"][0].startswith("ship it by hand"), "whoever passed the gate"
    assert "stage: test" in (folder / "intent.md").read_text(encoding="utf-8")


@needs_uv
def test_a_risky_change_is_never_landed_by_auto_whatever_the_skill_says(tmp_path, capsys) -> None:
    """The gate's rule is the script's: `land --by auto` on a change with a risk signal (here the
    approver escalated) is refused before anything is written, and the person's yes lands it."""
    root = _repo(tmp_path)
    tree = _ready(root, "risky", "risky's one")
    folder = tree / ".sdlc" / "work" / tree.name
    (folder / "decision.md").write_text(
        "DECISION: ESCALATE\n\nA call for the person.\n\n- IMPACT: minor — a test change\n",
        encoding="utf-8",
    )
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert code == 1 and "the approver escalated" in out["refusals"][0]
    assert _git(tree, "log", "-1", "--format=%s") == "init", "nothing committed"
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "current"), out
    assert "Sdlc-Landed: by=person" in _git(tree, "log", "-1", "--format=%B")


@needs_uv
def test_land_close_reads_a_modified_first_path_in_the_folder_as_the_folders(
    tmp_path, capsys
) -> None:
    """2026-11-17-31: the landing's record is a tracked file of the change's folder modified after
    its commit (` M`, the status's first line, whose leading space a stripped read loses): it is
    the folder's, so close amends it in and closes, never refusing it as a stray."""
    root = _repo(tmp_path)
    tree = _ready(root, "costed", "costed's one")
    costs = tree / ".sdlc" / "work" / tree.name / "runs" / "costs.jsonl"
    costs.parent.mkdir(parents=True, exist_ok=True)
    costs.write_text('{"role": "builder"}\n', encoding="utf-8")
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "current"), out
    with costs.open("a", encoding="utf-8") as f:
        f.write('{"role": "reviewer"}\n')
    assert _git(tree, "status", "--porcelain").startswith("M "), "stripped, as the bug read it"
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out
    assert '"reviewer"' in _git(root, "show", f"main~1:.sdlc/work/{tree.name}/runs/costs.jsonl")


@needs_uv
def test_a_second_land_after_main_moves_rebases_with_the_first_record_amended_in(
    tmp_path, capsys
) -> None:
    """2026-11-17-33: a landing's record (its review of a rebased change) is written after the
    change's commit; when the base branch moves again before the close, the second `land` amends
    that record into the commit first, so it rebases rather than refusing on uncommitted work."""
    root = _repo(tmp_path)
    tree = _ready(root, "twice", "twice's one")
    folder = tree / ".sdlc" / "work" / tree.name
    for n in (1, 2):
        (root / f"moved-{n}.txt").write_text("moved on\n", encoding="utf-8")
        _git(root, "add", f"moved-{n}.txt")
        _git(root, "commit", "-q", "-m", f"main moves on, {n}")
        code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
        assert (code, out["state"], out.get("round")) == (0, "rebased", n), out
        (folder / "reviews" / f"land-{n}" / "behaviour.md").write_text(
            "VERDICT: PASS\n\n## Evidence\n$ true\nexit: 0\n", encoding="utf-8"
        )
    committed = _git(tree, "show", "--name-only", "--format=", "HEAD")
    assert f".sdlc/work/{tree.name}/reviews/land-1/behaviour.md" in committed, "amended in"
    assert _git(tree, "rev-list", "--count", "main..HEAD") == "1", "one commit, on main as it is"
    assert _git(tree, "merge-base", "main", "HEAD") == _git(root, "rev-parse", "main")


@needs_uv
def test_a_record_is_never_amended_into_a_commit_the_landing_didnt_make(tmp_path, capsys) -> None:
    """A change at `stage: shipped` whose commit a person made, not the landing: its uncommitted
    folder is refused, never amended into a commit that isn't the landing's."""
    root = _repo(tmp_path)
    tree = _ready(root, "handmade", "handmade's one")
    folder = tree / ".sdlc" / "work" / tree.name
    intent = folder / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8").replace("stage: test", "stage: shipped"),
        encoding="utf-8",
    )
    _git(tree, "add", "README.md", ".sdlc/last-id")
    _git(tree, "commit", "-q", "-m", "by hand")
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert code == 1 and "isn't the landing's commit" in out["refusals"][0], out
    assert _git(tree, "show", "--name-only", "--format=", "HEAD").splitlines() == [
        ".sdlc/last-id",
        "README.md",
    ], "nothing amended"


REGISTER = """# Ideas

> The register.

## [2026-11-17-1] [nit] A nit no change names

Paths: README.md

## [2026-11-17-11] [nit] A nit the change takes in

Paths: README.md

## [2026-11-17-2] [nit] A nit the Problem only cites

Paths: README.md

## [2026-11-17-12] [idea] An idea that stays
"""


@needs_uv
def test_a_landing_retires_the_nits_its_intent_names(tmp_path, capsys) -> None:
    """2026-11-17-32: a change whose intent names an open nit by id lands with that nit gone from
    the register, in its own commit, and a `Retired nits:` paragraph, as `/sdlc:ship` does. An id
    is matched whole: `2026-11-17-1` is not named by `2026-11-17-11`, and stays."""
    root = _repo(tmp_path)
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(REGISTER, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a register")
    tree = _ready(root, "tidy", "tidy's one")
    intent = tree / ".sdlc" / "work" / tree.name / "intent.md"
    text = intent.read_text(encoding="utf-8").replace(
        "## Problem\n", "## Problem\n\nAs 2026-11-17-2 was, by an earlier change.\n"
    )
    headings = [ln for ln in text.splitlines() if ln.startswith("## ")]
    assert headings[-1] == "## Approach", "what's appended below is in the Approach"
    intent.write_text(text + "\nTakes in nit 2026-11-17-11.\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["retired_nits"]) == (0, "current", ["2026-11-17-11"]), out
    message = _git(tree, "log", "-1", "--format=%B")
    assert f"Retired nits:\n- 2026-11-17-11: taken in by {tree.name}" in message, message
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out
    register = (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    assert "2026-11-17-11" not in register and "A nit the change takes in" not in register
    assert "## [2026-11-17-1] [nit] A nit no change names" in register, "matched whole"
    assert "## [2026-11-17-2] [nit] A nit the Problem only cites" in register, "the Approach only"
    assert "## [2026-11-17-12] [idea] An idea that stays\n" in register
    assert "Paths: README.md\n\n## [2026-11-17-12]" in register, "heading to the next heading"


def test_the_landings_nits_are_the_ones_sdlc_reads(tmp_path) -> None:
    """`named_nits()` reads the register with a copy of `sdlc.py`'s parsing: the same `[nit]`
    entries, a fenced example never one."""
    sdlc = _load("sdlc_for_landing", ROOT / "scripts" / "sdlc.py")
    text = (
        REGISTER
        + "\n```\n## [2026-11-17-13] [nit] An example\n```\n\n##  [2026-11-17-14]  [nit] Spaced\n"
    )
    (tmp_path / ".sdlc" / "work").mkdir(parents=True)
    (tmp_path / ".sdlc" / "work" / "inbox.md").write_text(text, encoding="utf-8")
    folder = tmp_path / ".sdlc" / "work" / "001-tidy"
    folder.mkdir()
    ids = [e["id"] for e in sdlc.parse_entries(text)]
    approach = "## Approach\n\n" + " ".join([*ids, "2026-11-17-13"]) + "\n"
    (folder / "intent.md").write_text(approach, encoding="utf-8")
    theirs = [e["id"] for e in sdlc.parse_entries(text) if e["status"] == "nit"]
    assert (
        factory.named_nits(tmp_path, folder)
        == theirs
        == ["2026-11-17-1", "2026-11-17-11", "2026-11-17-2", "2026-11-17-14"]
    )


@needs_uv
def test_a_landings_record_never_takes_in_a_path_outside_its_folder(tmp_path, capsys) -> None:
    """R2: anything uncommitted outside the change's folder is not the landing's record. The
    second `land` and `land --close` each refuse, naming it, and amend nothing."""
    root = _repo(tmp_path)
    tree = _ready(root, "strayed", "strayed's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["retired_nits"]) == (0, "current", []), out
    (folder / "runs").mkdir(exist_ok=True)
    (folder / "runs" / "costs.jsonl").write_text("{}\n", encoding="utf-8")
    (tree / "stray.txt").write_text("not the landing's\n", encoding="utf-8")
    head = _git(tree, "rev-parse", "HEAD")
    (root / "moved.txt").write_text("moved on\n", encoding="utf-8")
    _git(root, "add", "moved.txt")
    _git(root, "commit", "-q", "-m", "main moves on")
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert code == 1 and "stray.txt" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head, "nothing amended"
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert code == 1 and "stray.txt" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head and tree.exists(), "nothing amended or closed"


def test_the_landings_resolutions_are_the_ones_sdlc_reads(tmp_path) -> None:
    """R14: `resolved_files()` reads `conflicts.md` with a copy of `sdlc.py`'s
    `conflicts_resolved()`: each `- ` line's path, once, in order."""
    sdlc = _load("sdlc_for_resolutions", ROOT / "scripts" / "sdlc.py")
    (tmp_path / "conflicts.md").write_text(
        "# Conflicts\n\n## 2026-11-17 onto main abc1234\n\n- README.md\n-  src/a b.py \n\n"
        "## 2026-11-18 onto main def5678\n\n- README.md\n- docs/x.md\nnot a path\n",
        encoding="utf-8",
    )
    theirs = sdlc.conflicts_resolved(tmp_path)
    assert factory.resolved_files(tmp_path) == theirs == ["README.md", "src/a b.py", "docs/x.md"]
    assert factory.resolved_files(tmp_path / "none") == sdlc.conflicts_resolved(tmp_path / "none")


def _gated(tmp_path: Path) -> Path:
    """A scratch repo whose base branch names a check, `true`."""
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "true"\n', encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a gate")
    return root


def _verdict(role: str, verdict: str = "PASS", changes: tuple[str, ...] = ()) -> str:
    lines = [f"VERDICT: {verdict}", *(f"- CHANGE: {c}" for c in changes)]
    evidence = "\n## Evidence\n$ true\nexit: 0\n" if role in factory.RUNS_THE_CHANGE else ""
    return "\n".join(lines) + "\n" + evidence


@needs_uv
def test_a_landing_resolution_counts_until_its_review_passes(tmp_path, capsys) -> None:
    """R11: a resolution made while landing is a signal until `land-verdicts` for its round says
    `pass`: missing a reviewer, or with a change the verifier kept, it still asks. Once passed it
    stays passed when the landing's own record moves `HEAD`. A marker with no round, written
    before the round was recorded, always asks."""
    root = _gated(tmp_path)
    tree = _ready(root, "resolved", "resolved's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "current"), out
    reviews = folder / "reviews" / "land-1"
    reviews.mkdir(parents=True)
    marker = folder / "runs" / "land-resolved"
    marker.parent.mkdir(exist_ok=True)
    marker.write_text("land-1\nREADME.md\n", encoding="utf-8")
    cfg = factory.load_config(tree)[0]
    said = "a conflict was resolved while landing"

    def asks() -> bool:
        return said in factory.land_signals(folder, tree, "READY", cfg)[0]

    assert asks(), "before any review"
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert (code, out["verdict"]) == (0, "PASS"), out
    roles = factory.land_verdict(tree, folder, cfg, 1)["missing"]
    assert len(roles) > 1, roles
    for role in roles[1:]:
        (reviews / f"{role}.md").write_text(_verdict(role), encoding="utf-8")
    assert asks(), f"while {roles[0]} is missing"
    (reviews / f"{roles[0]}.md").write_text(
        _verdict(roles[0], "CHANGES", ("README.md:1: keep both",)), encoding="utf-8"
    )
    (reviews / "verified.md").write_text(
        f"- KEPT: {roles[0]}: README.md:1: keep both\n", encoding="utf-8"
    )
    assert asks(), "with a change the verifier kept"
    (reviews / "verified.md").unlink()
    (reviews / f"{roles[0]}.md").write_text(_verdict(roles[0]), encoding="utf-8")
    assert not asks(), "every reviewer at the run's depth passed it"
    assert factory._amend_record(tree, folder) is None
    assert not asks(), "the landing's own record moved HEAD: the pass still stands"
    marker.write_text("README.md\n", encoding="utf-8")
    assert asks(), "a marker without a round"


@needs_uv
def test_a_resolution_the_build_reviewed_is_no_signal_and_one_after_it_is(tmp_path, capsys) -> None:
    """R13: a resolution `sdlc.py resolve` recorded in `conflicts.md` was seen when every file it
    names hashes now as the newest complete build round's snapshot does. With no complete round it
    asks; resolved before the round's snapshot it doesn't; edited after it, it asks. A file it
    names that neither the snapshot nor the change touches counts as unchanged."""
    root = _gated(tmp_path)
    tree = _ready(root, "rebuilt", "rebuilt's one")
    folder = tree / ".sdlc" / "work" / tree.name
    (folder / "conflicts.md").write_text(
        "# Conflicts\n\n## 2026-11-17 onto main abc1234\n\n- README.md\n- untouched.txt\n",
        encoding="utf-8",
    )
    cfg = factory.load_config(tree)[0]
    said = "a conflict resolved by sdlc.py resolve after the last review round"

    def asked() -> list[str]:
        return [
            s for s in factory.land_signals(folder, tree, "READY", cfg)[0] if s.startswith(said)
        ]

    assert asked() == [f"{said}: README.md, untouched.txt"], "no complete round saw it"
    (folder / "build").mkdir()
    (folder / "build" / "round-1.md").write_text("Built.\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_snapshot, tree, "001", 1)
    assert code == 0, out
    roles = factory._rounds_at_depth(tree, folder, cfg)[2]["reviewers"]
    (folder / "reviews" / "round-1").mkdir(parents=True)
    for role in roles:
        (folder / "reviews" / "round-1" / f"{role}.md").write_text(_verdict(role), encoding="utf-8")
    assert asked() == [], "the round's reviewers read the resolution as it stands"
    (tree / "README.md").write_text("rebuilt's one, edited after\ntwo\nthree\n", encoding="utf-8")
    assert asked() == [f"{said}: README.md"], "edited after the round's snapshot"


@needs_uv
def test_an_auto_landing_never_closes_over_a_resolution_no_review_passed(tmp_path, capsys) -> None:
    """R15: the gate's rule is the script's at the close too. A change committed `by=auto` whose
    landing resolution no review has passed is refused, naming it; once every reviewer at the
    run's depth passes it, the close merges."""
    root = _repo(tmp_path)
    tree = _ready(root, "hasty", "hasty's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "current"), out
    reviews = folder / "reviews" / "land-1"
    reviews.mkdir(parents=True)
    (folder / "runs").mkdir(exist_ok=True)
    (folder / "runs" / "land-resolved").write_text("land-1\nREADME.md\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert code == 1 and "a conflict was resolved while landing" in out["refusals"][0], out
    assert tree.exists() and _git(root, "log", "-1", "--format=%s", "main") == "init"
    cfg = factory.load_config(tree)[0]
    for role in factory.land_verdict(tree, folder, cfg, 1)["missing"]:
        (reviews / f"{role}.md").write_text(_verdict(role), encoding="utf-8")
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out
