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
import sys
from pathlib import Path

import pytest
from train_driver import drive_train

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


factory = _load("factory_landing", ROOT / "plugins" / "factory" / "scripts" / "factory.py")
sdlc = _load("sdlc_for_landing", ROOT / "scripts" / "sdlc.py")

needs_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do")


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _run(capsys, fn, *args, **kwargs) -> tuple[int, dict]:
    code = fn(*args, **kwargs)
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
    message = factory.landing.land_message(tmp_path, folder, "auto", True)
    assert message.splitlines()[0] == "Reopen saved drafts"
    assert "A saved draft can't be reopened. See .sdlc/work/008-reopen-drafts/." in message
    assert "Nothing reads it back" not in message, "the Problem's first sentence only"
    assert message.rstrip().endswith("Refs #8\nSdlc-Landed: by=auto")
    assert "Sdlc-Findings" not in message, "a missing line reads as unanswered, never as clean"
    assert "Refs" not in factory.landing.land_message(tmp_path, folder, "person", False)
    assert "Carried forward" not in message and "Dropped" not in message, "empty, left out"
    assert "How to recover" not in message

    # 103 R9: ship's paragraphs, read back from notes.md's ticks and decision.md's RECOVER lines,
    # after the body and before the trailers.
    (folder / "notes.md").write_text(
        "# Notes\n\n- [x] Page the list → seed: 2026-11-17-4\n- [x] plain, done\n"
        "- [x] Rename the flag → dropped: the flag went away\n",
        encoding="utf-8",
    )
    (folder / "decision.md").write_text(
        "DECISION: READY\n\n- IMPACT: minor — x\n- RECOVER: deploy/: fix forward: drop it\n",
        encoding="utf-8",
    )
    message = factory.landing.land_message(tmp_path, folder, "person", True)
    assert message.split("\n\n", 2)[2] == (
        "Carried forward:\n- Page the list → 2026-11-17-4\n\n"
        "Dropped:\n- Rename the flag: the flag went away\n\n"
        "How to recover:\n- deploy/: fix forward: drop it\n\n"
        "Refs #8\nSdlc-Landed: by=person\n"
    )
    assert "Sdlc-Findings" not in message


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


def _ready(
    root: Path, slug: str, first_line: str, impact: str = "minor", reviewed: bool = True
) -> Path:
    """A change made by `sdlc.py new`, built (its README's first line), at `stage: test` with the
    approver's READY and its proposed impact, as a factory run leaves one: with `reviewed`, one
    build round, snapshotted, that every reviewer at the full depth passed."""
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
    if reviewed:
        (folder / "build").mkdir()
        (folder / "build" / "round-1.md").write_text("Built.\n", encoding="utf-8")
        hashes = factory._tree_hashes(tree, "main")
        factory.snapshot_path(folder, 1).write_text(
            "".join(f"{digest}  {p}\n" for p, digest in hashes.items()), encoding="utf-8"
        )
        (folder / "reviews" / "round-1").mkdir(parents=True)
        for role in factory.DEFAULTS["reviewers"]:
            (folder / "reviews" / "round-1" / f"{role}.md").write_text(
                _verdict(role), encoding="utf-8"
            )
    return tree


@needs_uv
def test_a_batch_lands_in_order_and_a_conflict_is_resolved_reviewed_and_closed(
    tmp_path, capsys
) -> None:
    """Two ready changes edit one line: the train commits both, stacks the second on the first,
    which conflicts; the rebase is left for the landing agent, its resolution is reviewed again at
    the run's depth, and both close in order. Each commit says who passed the gate, and nothing is
    left behind."""
    root = _repo(tmp_path)
    first, second = _ready(root, "first", "first's one"), _ready(root, "second", "second's one")
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    assert code == 0 and [c["change"] for c in batch["batch"]] == [first.name, second.name]
    assert batch["clear"] is True, batch
    assert [c["impact"] for c in batch["batch"]] == ["minor", "minor"]

    _train(root, capsys, [first, second])
    for tree in (first, second):
        code, out = _run(capsys, factory.landing.cmd_train, root)
        assert (out["next"], out["change"]) == ("commit", tree.name), out
        code, out = _run(capsys, factory.landing.cmd_land, tree, tree.name[:3], "auto")
        assert (code, out["state"]) == (0, "committed"), out
        assert "Sdlc-Landed: by=auto" in _git(tree, "log", "-1", "--format=%B")
    code, out = _run(capsys, factory.landing.cmd_train, root)
    assert (out["next"], out["change"]) == ("stack", second.name), "the first never moved"
    assert out["onto"] == _git(first, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.landing.cmd_resolve, second, "002", False, onto=out["onto"])
    assert (code, out["state"], out["conflicted"], out["round"]) == (
        0,
        "conflict",
        ["README.md"],
        1,
    )
    code, out = _run(capsys, factory.landing.cmd_train, root)
    assert (out["next"], out["files"]) == ("resolve", ["README.md"]), out
    resolved = "first's one, and second's, quoting " + "<" * 7 + " mid-line\ntwo\nthree\n"
    (second / "README.md").write_text(resolved, encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_resolve, second, "002", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert _git(second, "rev-parse", "HEAD^") == _git(first, "rev-parse", "HEAD"), "stacked"
    folder = second / ".sdlc" / "work" / second.name
    marker = (folder / "runs" / "land-resolved").read_text(encoding="utf-8").splitlines()
    assert marker == ["land-1", "README.md"], "the round under way, then the files"
    signals, _ = factory.landing.land_signals(
        folder, second, "READY", factory.load_config(second)[0]
    )
    assert "a conflict was resolved while landing" in signals, "the next gate is the person's"

    code, out = _run(capsys, factory.landing.cmd_train, root)
    assert (out["next"], out["change"]) == ("review", second.name), "no gate: the base names none"
    assert set(out["verdict"]["missing"]) == set(factory.DEFAULTS["reviewers"])
    code, out = _run(capsys, factory.landing.cmd_land_close, second, "002")
    assert code == 1 and "no landing review has passed it" in out["refusals"][0], out
    reviews = folder / "reviews" / "land-1"
    for role in factory.DEFAULTS["reviewers"]:
        evidence = "\n\n## Evidence\n$ true\nexit: 0\n" if role == "behaviour" else "\n"
        (reviews / f"{role}.md").write_text(f"VERDICT: PASS{evidence}", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, second, "002")
    assert out["next"] == "pass", out
    signals, _ = factory.landing.land_signals(
        folder, second, "READY", factory.load_config(second)[0]
    )
    assert "a conflict was resolved while landing" not in signals, "every reviewer saw it"

    for tree in (first, second):
        code, out = _run(capsys, factory.landing.cmd_train, root)
        assert (out["next"], out["change"]) == ("close", tree.name), out
        code, out = _run(capsys, factory.landing.cmd_land_close, tree, tree.name[:3])
        assert code == 0 and "merge" in out["done"], out
        assert not tree.exists(), "its worktree is gone"
    assert _run(capsys, factory.landing.cmd_train, root)[1]["next"] == "done"
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
    """073 R12: the behaviour check no longer runs the gate, so after a stack the landing runs the
    base branch's check itself, into `build/land-<n>.gate.md`, before any reviewer; a red gate on
    the change as stacked is a stop, for the person to ship by hand."""
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

    out = _stack(root, tree, capsys)
    assert (out["state"], out["round"]) == ("stacked", 1), out
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "gate" and out["gate"]["command"] == "test ! -f broken.txt", out
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert (code, out["verdict"]) == (0, "PASS") and out["to"].endswith("build/land-1.gate.md")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert (out["next"], out["missing"]) == ("review", ["behaviour"]), out

    (tree / "broken.txt").write_text("", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert (code, out["verdict"], out["attempt"]) == (1, "FAIL", 2)
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "stop" and "ship it by hand" in out["problems"][0], out


@needs_uv
def test_a_refused_step_lands_nothing_of_that_change(tmp_path, capsys) -> None:
    """A change the approver proposed no impact for can't be shipped by land: it is refused before
    anything is written, and its folder and worktree stay as they were."""
    root = _repo(tmp_path)
    tree = _ready(root, "lone", "lone's one")
    folder = tree / ".sdlc" / "work" / tree.name
    (folder / "decision.md").write_text("DECISION: READY\n\nNo impact here.\n", encoding="utf-8")
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    assert batch["clear"] is False and "proposes no `- IMPACT:`" in batch["batch"][0]["signals"][0]
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
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
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert code == 1 and "sdlc.py ship refused" in out["refusals"][0], out
    assert register.read_bytes() == REGISTER.encode("utf-8"), "the register as it was"


@needs_uv
def test_a_landing_commits_the_agents_findings_and_no_trailer(tmp_path, capsys) -> None:
    """114 R10: the agents' findings.md, written by `carry`, lands with the folder, and the
    commit still carries no `Sdlc-Findings`: a factory review is never counted as the person's."""
    root = _repo(tmp_path)
    tree = _ready(root, "noted", "noted's one")
    folder = _folder(tree)
    code_md = folder / "reviews" / "round-1" / "code.md"
    code_md.write_text(code_md.read_text() + "\n## Notes\n\n- NIT: README.md:1: terse\n")
    assert _run(capsys, factory.cmd_carry, tree, "001")[1]["findings"] == 1
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    body = _git(tree, "log", "-1", "--format=%B")
    assert "Sdlc-Findings" not in body and "Sdlc-Landed: by=person" in body
    shown = _git(tree, "show", "--name-only", "--format=")
    assert f".sdlc/work/{tree.name}/findings.md" in shown.splitlines()
    landed = _git(tree, "show", f"HEAD:.sdlc/work/{tree.name}/findings.md")
    assert "By: code" in landed and "Fresh review: skipped" in landed


CHECKS = "# Checks\n\n> Acceptance checks.\n\n## It runs\n\n```sh\ntrue\n```\n"


def _folder(tree: Path) -> Path:
    return tree / ".sdlc" / "work" / tree.name


def _held(tree: Path) -> Path:
    """134: a root whose register is the change's `entries.md`, so `sdlc.py`'s own readers read
    what the landing holds for close to file."""
    held = tree.parent / f"{tree.name}-held"
    (held / ".sdlc" / "work").mkdir(parents=True, exist_ok=True)
    source = _folder(tree) / factory.landing.ENTRIES
    text = source.read_text(encoding="utf-8") if source.is_file() else ""
    (held / ".sdlc" / "work" / "inbox.md").write_text(text, encoding="utf-8")
    return held


def _config(root: Path, text: str) -> None:
    """The base branch's `.sdlc/config.toml`, committed on main before any change is made."""
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "config")


def _with_cases(monkeypatch, scope: list[str]) -> None:
    """`sdlc.py` as it is, but for `preflight`, which says the diff reaches skills' cases: a
    scratch repo has none (`_cases_report()` is `available: false` outside this plugin's repo)."""
    real = factory._sdlc

    def fake(args: list[str], cwd: Path):
        code, data, out = real(args, cwd)
        if args[0] == "preflight" and data is not None:
            data["cases"] = {"available": True, "scope": scope}
        return code, data, out

    monkeypatch.setattr(factory, "_sdlc", fake)


@needs_uv
def test_a_change_with_acceptance_checks_or_undone_items_is_in_the_batch_behind_the_persons_yes(
    tmp_path, capsys
) -> None:
    """103 R1: checks, undone notes and assumed decisions are signals, never an exclusion: the
    change is in the batch, and the batch is never clear."""
    root = _repo(tmp_path)
    tree = _ready(root, "checked", "checked's one")
    folder = _folder(tree)
    (folder / "checks.md").write_text(CHECKS, encoding="utf-8")
    (folder / "notes.md").write_text("# Notes\n\n- [ ] a thing left\n", encoding="utf-8")
    (folder / "decisions.md").write_text(
        "# Decisions\n\n- [ ] D1 (builder round 1, default): Page at 50? Going with 50.\n",
        encoding="utf-8",
    )
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    assert batch["excluded"] == [] and [c["change"] for c in batch["batch"]] == [tree.name]
    assert batch["clear"] is False
    signals = " | ".join(batch["batch"][0]["signals"])
    for said in ("acceptance checks to run: 1", "undone notes to dispose of: 1",
                 "assumed decisions to confirm: D1"):  # fmt: skip
        assert said in signals, signals
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert code == 1 and "the gate is the person's" in out["refusals"][0]


@needs_uv
def test_land_check_shows_each_changes_checks_cases_notes_decisions_and_recovery(
    tmp_path, capsys, monkeypatch
) -> None:
    """103 R2: each change carries what the yes approves, and a change with none of it, empty
    parts."""
    root = _repo(tmp_path)
    _config(root, '[review]\nirreversible = ["deploy/"]\n')
    plain = _ready(root, "plain", "plain's one")
    full = _ready(root, "full", "full's one")
    folder = _folder(full)
    (full / "deploy").mkdir()
    (full / "deploy" / "run.sh").write_text("echo hi\n", encoding="utf-8")
    (folder / "checks.md").write_text(CHECKS, encoding="utf-8")
    (folder / "notes.md").write_text(
        "# Notes\n\n- [ ] Page the list\n- [x] done already\n- [ ] Rename the flag\n",
        encoding="utf-8",
    )
    (folder / "decisions.md").write_text(
        "# Decisions\n\n- [ ] D1 (builder round 1, default): Page at 50? Going with 50.\n"
        "- [x] D2 (builder round 1, blocking): Keep drafts? → decided: 30 days\n",
        encoding="utf-8",
    )
    (folder / "decision.md").write_text(
        "DECISION: READY\n\nFine.\n\n- IMPACT: minor — a test change\n"
        "- UNDONE: Rename the flag → dropped: the flag went away in round 2\n"
        "- RECOVER: deploy/: fix forward: a release without deploy/run.sh\n",
        encoding="utf-8",
    )
    _with_cases(monkeypatch, ["ship-basic"])
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    by = {c["change"]: c for c in batch["batch"]}
    assert by[full.name]["checks"] == [{"name": "It runs", "command": "true"}]
    assert by[full.name]["cases"] == {"scope": ["ship-basic"], "cap_usd": 5, "noted": False,
                                      "failed": [], "environment": [], "skipped": None,
                                      "run": None}  # fmt: skip
    assert by[full.name]["undone"] == [
        {"line": 3, "text": "Page the list", "seed": "Page the list"},
        {"line": 5, "text": "Rename the flag", "dropped": "the flag went away in round 2"},
    ]
    assert by[full.name]["assumed"] == [{"id": "D1", "text": "Page at 50? Going with 50."}]
    assert by[full.name]["recover"] == ["deploy/: fix forward: a release without deploy/run.sh"]
    assert "skills' cases in scope: 1" in by[full.name]["signals"]
    intent = factory.landing.intent_parts(folder)
    assert by[full.name]["intent"] == intent and intent["title"], "131: what the change is"
    for said in (f"{full.name} — {intent['title']}", "- Page the list → seed: Page the list",
                 "- Rename the flag → dropped: the flag went away in round 2",
                 "- D1: Page at 50? Going with 50.", f"{plain.name} — "):  # fmt: skip
        assert said in batch["shown"], batch["shown"]
    # The stand-in gives every change a scope; the plain one's other parts are empty.
    assert [by[plain.name][k] for k in ("checks", "undone", "assumed", "recover")] == [[]] * 4
    assert "(at most $10)" in batch["question"], "two changes with cases, $5 each"


SETTLED_LEDGER = (
    "# Decisions\n\n- [ ] D1 (builder round 1, default): Page at 50? Going with 50.\n"
    "  - OPTION: 50 — one screen; a second page past it\n"
    "  - OPTION: 100 — fewer pages; a slower first paint\n"
    "- [x] D2 (code round 1, default): Log the draft id? → settled by the approver: "
    "spec R4 forbids it\n"
)


@needs_uv
def test_the_landing_shows_settled_defaults_apart_and_never_confirms_them(tmp_path, capsys):
    """137 R8: the approver's settled default is shown under its own heading, never as one to
    confirm, and a landing by the person confirms the open default alone."""
    root = _repo(tmp_path)
    tree = _ready(root, "weighed", "weighed's one")
    folder = _folder(tree)
    (folder / "decisions.md").write_text(SETTLED_LEDGER, encoding="utf-8")
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    [c] = batch["batch"]
    assert c["assumed"] == [{"id": "D1", "text": "Page at 50? Going with 50."}], c
    assert c["settled"] == [
        {"id": "D2", "text": "Log the draft id?", "reason": "spec R4 forbids it"}
    ], c
    shown = batch["shown"]
    assert "  Settled by the approver:\n  - D2: Log the draft id? (spec R4 forbids it)" in shown
    assert shown.index("Assumed decisions to confirm") < shown.index("Settled by the approver")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    ledger = (folder / "decisions.md").read_text(encoding="utf-8")
    assert "D2 (code round 1, default): Log the draft id? → settled by the approver: " in ledger
    assert ledger.count("→ decided:") == 1 and "50. → decided: " in ledger, ledger
    assert "  - OPTION: 50 — one screen; a second page past it\n" in ledger, "sub-lines kept"


@needs_uv
def test_a_settled_default_keeps_the_batch_from_passing_itself(tmp_path, capsys) -> None:
    """137 R9: a settled default is a landing signal of its own, so the batch isn't clear; the
    open-or-assumed signals don't fire for it."""
    root = _repo(tmp_path)
    tree = _ready(root, "weighed", "weighed's one")
    (_folder(tree) / "decisions.md").write_text(
        SETTLED_LEDGER.replace("- [ ] D1", "- [x] D1").replace(
            "Going with 50.\n", "Going with 50. → decided: 50\n"
        ),
        encoding="utf-8",
    )
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    assert batch["clear"] is False
    signals = batch["batch"][0]["signals"]
    assert "defaults settled by the approver: D2" in signals, signals
    assert not any("assumed" in s or "still open" in s for s in signals), signals


def _entry(name: str, **parts) -> dict:
    empty = {"checks": [], "cases": {}, "undone": [], "assumed": [], "recover": [], "nits": []}
    return {"change": name, **empty, **parts}


def test_the_landing_question_names_only_what_the_batch_holds() -> None:
    """103 R3: the script words the question, a clause for each thing some change holds."""
    plain = factory.landing.land_question([_entry("001-a"), _entry("002-b")], "main")
    assert plain == (
        "Land 2 changes in this order, 001-a, 002-b, each shipped with its approver's impact, "
        "committed, stacked in this order on main, gated once at the tip (a red tip bisected, "
        "the change at fault left out with why and the rest landed; a conflict resolved by one "
        "landing agent and reviewed again), brought up to date as often as main moves while "
        "landing, up to 3 times, and closed in order, pushed as git.push says? "
        "(yes / yes, with a fix / leave one out / no)"
    )
    moving = factory.landing.land_question([_entry("001-a")], "main", 5)
    assert "as often as main moves while landing, up to 5 times" in moving, "the base's land.moves"
    check = {"name": "x", "command": "true"}
    cases = {"scope": ["ship-basic"], "cap_usd": 5}
    full = factory.landing.land_question(
        [
            _entry("001-a", checks=[check], cases=cases, recover=["a/: b"]),
            _entry(
                "002-b",
                cases=cases,
                assumed=[{"id": "D1", "text": "t"}],
                undone=[{"line": 1, "text": "t", "seed": "t"}],
            ),
        ],  # fmt: skip
        "trunk",
    )
    assert full == (
        "Land 2 changes in this order, 001-a, 002-b, each shipped with its approver's impact, its "
        "acceptance checks and skills' cases run as shown (at most $10), its undone notes carried "
        "or dropped and its assumed decisions confirmed as shown, with how to recover shown, "
        "committed, stacked in this order on trunk, gated once at the tip (a red tip bisected, "
        "the change at fault left out with why and the rest landed; a conflict resolved by one "
        "landing agent and reviewed again), brought up to date as often as trunk moves while "
        "landing, up to 3 times, and closed in order, pushed as git.push says? "
        "(yes / yes, with a fix / leave one out / no)"
    )
    only = factory.landing.land_question([_entry("001-a", checks=[check])], "main")
    assert "its acceptance checks run as shown, committed" in only and "$" not in only
    assert only.startswith("Land 1 change in this order, 001-a,")
    cases_only = factory.landing.land_question([_entry("001-a", cases=cases)], "main")
    assert "its skills' cases run as shown (at most $5)," in cases_only
    assert "accepted" not in cases_only
    # 156 R15: a failed or skipped case, seen in the question, is accepted by its yes.
    for seen in ({"failed": [{"case": "ship-basic", "graders": []}]}, {"skipped": "declined"}):
        accepted = factory.landing.land_question([_entry("001-a", cases={**cases, **seen})], "main")
        assert ("its skills' cases run as shown (at most $5), its failed or skipped skills' cases "
                "accepted as shown, committed") in accepted, accepted  # fmt: skip
    notes = factory.landing.land_question(
        [_entry("001-a", undone=[{"line": 1, "text": "t", "seed": "t"}])], "main")  # fmt: skip
    assert "its undone notes carried or dropped as shown," in notes and "assumed" not in notes
    decided = factory.landing.land_question(
        [_entry("001-a", assumed=[{"id": "D1", "text": "t"}])], "main"
    )
    assert "its assumed decisions confirmed as shown," in decided and "undone" not in decided
    assert "recover" not in decided


INTENT = """---
id: 007
slug: page-drafts
tier: 1
stage: test
---

# 007 — Drafts are paged

> Stage 1: why this change is worth making.

## Problem

The drafts list loads every draft.
It is slow past a hundred.

## Outcome

- The list shows 50 at a time.

## Affected

- **Area:** drafts.
"""


def test_intent_parts_quote_the_title_problem_and_outcome(tmp_path) -> None:
    """131: the landing quotes what each change is from its intent, never a summary of it."""
    folder = tmp_path / "007-page-drafts"
    folder.mkdir()
    (folder / "intent.md").write_text(INTENT, encoding="utf-8")
    assert factory.landing.intent_parts(folder) == {
        "title": "Drafts are paged",
        "problem": "The drafts list loads every draft.\nIt is slow past a hundred.",
        "outcome": "- The list shows 50 at a time.",
    }
    assert factory.landing.intent_parts(tmp_path) == {"title": "", "problem": "", "outcome": ""}


def test_the_dialog_shows_each_failed_or_skipped_case() -> None:
    """156 R15: under a change's cases, each failed case with its failing graders and the run's
    traces, each the sandbox spoiled, and a skip with why: what the yes accepts."""
    cases = {
        "scope": ["ship-basic", "ship-risky"],
        "cap_usd": 5,
        "noted": True,
        "failed": [{"case": "ship-basic", "graders": ["asks-the-question"]}],
        "environment": ["ship-risky"],
        "skipped": None,
        "run": ".sdlc/reports/cases-1",
    }
    assert factory.landing.land_shown([_entry("007-a", cases=cases)]) == (
        "007-a\n"
        "  Skills' cases (at most $5): ship-basic, ship-risky\n"
        "  - failed: ship-basic (asks-the-question), trace in .sdlc/reports/cases-1/traces\n"
        "  - hit the environment: ship-risky"
    )
    skipped = {**cases, "failed": [], "environment": [], "skipped": "declined", "run": None}
    assert factory.landing.land_shown([_entry("007-a", cases=skipped)]).endswith(
        "\n  - skipped: declined"
    )


def test_the_dialog_shows_each_disposition_and_assumed_decision() -> None:
    """131: what the question calls `as shown` is in the text the dialog shows: each change by its
    title, each undone note with its disposition, each assumed decision, check, case, recovery and
    agent nit to file, and a change with none of them by its title alone."""
    title = {"title": "Drafts are paged", "problem": "p", "outcome": "o"}
    bug = "filed as a bug, med: The second line is never read (README.md, docs/a.md)"
    shown = factory.landing.land_shown([
        _entry(
            "007-page-drafts", intent=title,
            checks=[{"name": "It runs", "command": "true"}],
            cases={"scope": ["ship-basic"], "cap_usd": 5},
            undone=[
                {"line": 3, "text": "Page the list", "seed": "Page the list"},
                {"line": 4, "text": "pre-existing: README.md:2: two", "bug": {}, "shown": bug},
                {"line": 5, "text": "Rename the flag", "dropped": "the flag went away"},
            ],
            assumed=[{"id": "D1", "text": "Page at 50? Going with 50."}],
            recover=["deploy/: fix forward"],
            nits=[{"shown": "[nit] Rename x (naming, S, low; a.py)"}],
        ),
        _entry("008-plain", intent={"title": "Plain", "problem": "", "outcome": ""}),
    ])  # fmt: skip
    assert shown == (
        "007-page-drafts — Drafts are paged\n"
        "  Acceptance checks:\n"
        "  - It runs: true\n"
        "  Skills' cases (at most $5): ship-basic\n"
        "  Undone notes:\n"
        "  - Page the list → seed: Page the list\n"
        "  - pre-existing: README.md:2: two → " + bug + "\n"
        "  - Rename the flag → dropped: the flag went away\n"
        "  Assumed decisions to confirm:\n"
        "  - D1: Page at 50? Going with 50.\n"
        "  How to recover:\n"
        "  - deploy/: fix forward\n"
        "  Agents' nits to file:\n"
        "  - [nit] Rename x (naming, S, low; a.py)\n"
        "\n"
        "008-plain — Plain"
    )


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
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert code == 1 and "the approver escalated" in out["refusals"][0]
    assert _git(tree, "log", "-1", "--format=%s") == "init", "nothing committed"
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
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
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "committed"), out
    with costs.open("a", encoding="utf-8") as f:
        f.write('{"role": "reviewer"}\n')
    assert _git(tree, "status", "--porcelain").startswith("M "), "stripped, as the bug read it"
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out
    assert '"reviewer"' in _git(root, "show", f"main~1:.sdlc/work/{tree.name}/runs/costs.jsonl")


@needs_uv
def test_a_hand_shipped_change_is_not_committed_again(tmp_path, capsys) -> None:
    """109 R9: a change whose commit a person made, `stage: shipped` in it, with no
    `Sdlc-Landed:` line: its uncommitted folder is refused, never amended into a commit that isn't
    the landing's, and no landing commit is made over it."""
    root = _repo(tmp_path)
    tree = _ready(root, "handmade", "handmade's one")
    folder = tree / ".sdlc" / "work" / tree.name
    intent = folder / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8").replace("stage: test", "stage: shipped"),
        encoding="utf-8",
    )
    rel = folder.relative_to(tree).as_posix()
    _git(tree, "add", "README.md", ".sdlc/last-id", f"{rel}/intent.md")
    _git(tree, "commit", "-q", "-m", "by hand")
    head = _git(tree, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert code == 1 and "isn't the landing's commit" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head, "nothing committed or amended"
    assert _git(tree, "show", "--name-only", "--format=", "HEAD").splitlines() == [
        ".sdlc/last-id",
        f"{rel}/intent.md",
        "README.md",
    ], "nothing amended"


def _hook(root: Path, says: str | None) -> None:
    """A `commit-msg` hook in the scratch repo, shared by its worktrees, that prints `says` and
    refuses every commit; None removes it."""
    hook = Path(_git(root, "rev-parse", "--git-common-dir"))
    hook = (hook if hook.is_absolute() else root / hook) / "hooks" / "commit-msg"
    if says is None:
        hook.unlink()
        return
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(f"#!/bin/sh\necho '{says}' >&2\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)


@needs_uv
def test_a_failed_landing_commit_carries_git_s_error(tmp_path, capsys) -> None:
    """109 R7: a commit git refuses is reported with git's own words, never only its exit."""
    root = _repo(tmp_path)
    tree = _ready(root, "hooked", "hooked's one")
    _hook(root, "hook says no")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert code == 1 and "the commit failed" in out["refusals"][0], out
    assert "hook says no" in out["refusals"][0], out


@needs_uv
def test_a_landing_whose_commit_failed_commits_on_rerun(tmp_path, capsys) -> None:
    """109 R8: a landing that failed after `sdlc.py ship` and before its commit makes the commit
    when it runs again with the same `--by`: one commit, the message the first run would have
    written, its retired nit included, and nothing left uncommitted."""
    root = _repo(tmp_path)
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(REGISTER, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a register")
    tree = _ready(root, "retried", "retried's one")
    intent = _folder(tree) / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8") + "\nTakes in nit 2026-11-17-11.\n", encoding="utf-8"
    )
    before = _git(tree, "rev-parse", "HEAD")
    _hook(root, "hook says no")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert code == 1 and "hook says no" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == before
    assert "stage: shipped" in intent.read_text(encoding="utf-8"), "ship ran before the commit"
    _hook(root, None)
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"], out["retired_nits"]) == (0, "committed", ["2026-11-17-11"]), out
    assert _git(tree, "rev-parse", "HEAD~1") == before, "one new commit"
    message = _git(tree, "log", "-1", "--format=%B")
    assert message.splitlines()[-1] == "Sdlc-Landed: by=person", message
    assert f"Retired nits:\n- 2026-11-17-11: taken in by {tree.name}" in message, message
    assert _git(tree, "status", "--porcelain") == "", "nothing left uncommitted"
    shipped = _git(tree, "show", f"HEAD:{intent.relative_to(tree).as_posix()}")
    assert "stage: shipped" in shipped
    assert _git(tree, "show", "HEAD:.sdlc/work/inbox.md") == REGISTER.rstrip("\n"), "134 R1"
    held = _git(tree, "show", f"HEAD:.sdlc/work/{tree.name}/entries.md")
    assert f"Retire 2026-11-17-11: taken in by {tree.name}" in held


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
    """2026-11-17-32, 134 R3: a change whose intent names an open nit by id lands with a `Retire`
    line for it in its `entries.md` and a `Retired nits:` paragraph, and close deletes it from the
    register, as for `/sdlc:ship`. An id is matched whole: `2026-11-17-1` is not named by
    `2026-11-17-11`, and stays."""
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
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["retired_nits"]) == (0, "committed", ["2026-11-17-11"]), out
    message = _git(tree, "log", "-1", "--format=%B")
    assert f"Retired nits:\n- 2026-11-17-11: taken in by {tree.name}" in message, message
    # 134 R3: the branch's register keeps the nit; its `entries.md` retires it at close.
    assert _git(tree, "show", "HEAD:.sdlc/work/inbox.md") == REGISTER.rstrip("\n")
    held = _git(tree, "show", f"HEAD:.sdlc/work/{tree.name}/entries.md").splitlines()
    assert held[0] == f"# {tree.name} — entries"
    assert f"Retire 2026-11-17-11: taken in by {tree.name}" in held
    assert factory.landing.retired_ids(_folder(tree)) == ["2026-11-17-11"]
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
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
    train's stack and `land --close` each refuse, naming it, and amend nothing."""
    root = _repo(tmp_path)
    tree = _ready(root, "strayed", "strayed's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["retired_nits"]) == (0, "committed", []), out
    (folder / "runs").mkdir(exist_ok=True)
    (folder / "runs" / "costs.jsonl").write_text("{}\n", encoding="utf-8")
    (tree / "stray.txt").write_text("not the landing's\n", encoding="utf-8")
    head = _git(tree, "rev-parse", "HEAD")
    (root / "moved.txt").write_text("moved on\n", encoding="utf-8")
    _git(root, "add", "moved.txt")
    _git(root, "commit", "-q", "-m", "main moves on")
    _train(root, capsys, [tree])
    code, reading = _run(capsys, factory.landing.cmd_train, root)
    assert reading["next"] == "stack", reading
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", False, onto=reading["onto"])
    assert code == 1 and "stray.txt" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head, "nothing amended"
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert code == 1 and "stray.txt" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head and tree.exists(), "nothing amended or closed"
    assert _run(capsys, factory.landing.cmd_train, root)[1]["next"] == "eject", (
        "a failure of its own"
    )


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
    assert (
        factory.landing.resolved_files(tmp_path)
        == theirs
        == ["README.md", "src/a b.py", "docs/x.md"]
    )
    assert factory.landing.resolved_files(tmp_path / "none") == sdlc.conflicts_resolved(
        tmp_path / "none"
    )


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
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    reviews = folder / "reviews" / "land-1"
    reviews.mkdir(parents=True)
    marker = folder / "runs" / "land-resolved"
    marker.parent.mkdir(exist_ok=True)
    marker.write_text("land-1\nREADME.md\n", encoding="utf-8")
    cfg = factory.load_config(tree)[0]
    said = "a conflict was resolved while landing"

    def asks() -> bool:
        return said in factory.landing.land_signals(folder, tree, "READY", cfg)[0]

    assert asks(), "before any review"
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert (code, out["verdict"]) == (0, "PASS"), out
    roles = factory.landing.land_verdict(tree, folder, cfg, 1)["missing"]
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
    assert factory.landing._amend_record(tree, folder) is None
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
    tree = _ready(root, "rebuilt", "rebuilt's one", reviewed=False)
    folder = tree / ".sdlc" / "work" / tree.name
    (folder / "conflicts.md").write_text(
        "# Conflicts\n\n## 2026-11-17 onto main abc1234\n\n- README.md\n- untouched.txt\n",
        encoding="utf-8",
    )
    cfg = factory.load_config(tree)[0]
    said = "a conflict resolved by sdlc.py resolve after the last review round"

    def asked() -> list[str]:
        return [
            s
            for s in factory.landing.land_signals(folder, tree, "READY", cfg)[0]
            if s.startswith(said)
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
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "committed"), out
    reviews = folder / "reviews" / "land-1"
    reviews.mkdir(parents=True)
    (folder / "runs").mkdir(exist_ok=True)
    (folder / "runs" / "land-resolved").write_text("land-1\nREADME.md\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert code == 1 and "a conflict was resolved while landing" in out["refusals"][0], out
    assert tree.exists() and _git(root, "log", "-1", "--format=%s", "main") == "init"
    cfg = factory.load_config(tree)[0]
    for role in factory.landing.land_verdict(tree, folder, cfg, 1)["missing"]:
        (reviews / f"{role}.md").write_text(_verdict(role), encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out


# ---------------------------------------------------------------- checks and cases, behind the yes


@needs_uv
def test_factory_accept_records_sdlc_accepts_verdict(tmp_path, capsys) -> None:
    """103 R4: `factory.py accept` runs `sdlc.py accept` and records its verdict on the build as it
    stands, in the gate file's shape; the record never changes the build it records."""
    root = _repo(tmp_path)
    tree = _ready(root, "checked", "checked's one")
    folder = _folder(tree)
    (folder / "checks.md").write_text(CHECKS, encoding="utf-8")
    build = factory.accept_build(tree, folder)
    code, out = _run(capsys, factory.cmd_accept, tree, "001")
    assert (code, out["verdict"]) == (0, "PASS") and out["to"].endswith("build/land-accept.md")
    assert out["passed"] is True, "accept's own JSON passes through"
    record = folder / "build" / "land-accept.md"
    assert record.read_text(encoding="utf-8").startswith("ACCEPT: PASS\n")
    assert factory.read_gate_file(record)["attempts"] == [
        {"verdict": "PASS", "build": build, "exit": None}
    ]
    assert factory.accept_build(tree, folder) == build, "the record is outside what it records"

    (folder / "checks.md").write_text(CHECKS.replace("true", "pwd; false"), encoding="utf-8")
    code, said, _ = factory._sdlc(["accept", tree.name], tree)
    assert code == 1 and said["passed"] is False
    code, out = _run(capsys, factory.cmd_accept, tree, "001")
    assert (code, out["verdict"]) == (1, "FAIL")
    text = record.read_text(encoding="utf-8")
    assert text.startswith("ACCEPT: FAIL\n") and "## Attempt 2" in text
    assert "- It runs: exit 1, failed" in text
    assert str(tree) not in text and "<path-to-clone>" in text, "no path of this machine's"
    attempts = factory.read_gate_file(record)["attempts"]
    assert [a["verdict"] for a in attempts] == ["PASS", "FAIL"]
    assert attempts[1]["build"] != build, "checks.md is part of the build"
    assert factory.landing._accept_state(tree, folder) == "FAIL"
    (tree / "README.md").write_text("changed again\n", encoding="utf-8")
    assert factory.landing._accept_state(tree, folder) is None, "a new build needs a new run"


@needs_uv
def test_factory_cases_writes_the_note_ship_reads_or_stops(tmp_path, capsys, monkeypatch) -> None:
    """103 R5, 156 R11: `factory.py cases` runs `sdlc.py run-cases` for one change and writes the
    `Skill evals:` line ship reads, as run-cases worded it, once: on a pass, a skip, and a failed
    case too, which exits 1, its note replaced by a rerun of the command."""
    root = _repo(tmp_path)
    tree = _ready(root, "cased", "cased's one")
    folder = _folder(tree)
    calls, reply = [], {}

    def fake(args: list[str], cwd: Path):
        calls.append(args)
        return reply["code"], reply["data"], json.dumps(reply["data"])

    monkeypatch.setattr(factory, "_sdlc", fake)
    rows = [{"case": "ship-basic", "score": 1.0}, {"case": "ship-risky", "score": 1.0}]
    reply.update(code=0, data={"run": ".sdlc/reports/cases-1", "cases": rows, "failed": [],
                               "passed": True, "note": "Skill evals: ran, 2 of 2"})  # fmt: skip
    code, out = _run(capsys, factory.cmd_cases, tree, "001")
    assert code == 0 and calls == [["run-cases", tree.name]]
    findings = folder / "findings.md"
    assert findings.read_text(encoding="utf-8") == (
        factory.FINDINGS_HEAD + "\nSkill evals: ran, 2 of 2\n"
    ), "a missing file starts from the template's note"
    assert sdlc.findings_entries(folder)["cases"] == {"ran": True, "said": "2 of 2"}

    # A rerun replaces the line, in a findings.md that has findings, inside its note.
    findings.write_text(
        "# Findings\n\nFresh review: ran\nSkill evals: ran, 2 of 2\n\n## F1. [nit] [cost] A nit\n\n"
        "Evidence: a.py:1\nClass: style\nDisposition: minor\n",
        encoding="utf-8",
    )
    reply.update(code=0, data={"skipped": "plugin eval is unavailable: early access"})
    code, out = _run(capsys, factory.cmd_cases, tree, "001")
    text = findings.read_text(encoding="utf-8")
    assert code == 0 and text.count("Skill evals:") == 1, text
    assert "Fresh review: ran\nSkill evals: skipped, plugin eval is unavailable" in text
    assert sdlc.findings_entries(folder)["cases"]["ran"] is False

    failed = "Skill evals: ran, 1 of 2; failed: ship-risky; run: .sdlc/reports/cases-2"
    reply.update(code=1, data={"run": ".sdlc/reports/cases-2", "cases": rows, "note": failed,
                               "failed": ["ship-risky"], "passed": False})  # fmt: skip
    code, out = _run(capsys, factory.cmd_cases, tree, "001")
    assert code == 1 and out["failed"] == ["ship-risky"] and out["note"] == failed
    text = findings.read_text(encoding="utf-8")
    assert text.count("Skill evals:") == 1 and f"Fresh review: ran\n{failed}\n" in text, text
    assert sdlc.findings_entries(folder)["cases"]["ran"] is True
    reply["data"] = {**reply["data"], "note": failed.replace("1 of 2", "0 of 2")}
    code, out = _run(capsys, factory.cmd_cases, tree, "001")
    text = findings.read_text(encoding="utf-8")
    assert code == 1 and text.count("Skill evals:") == 1 and "ran, 0 of 2" in text, text


@needs_uv
def test_factory_cases_skip_writes_why_and_runs_nothing(tmp_path, capsys, monkeypatch) -> None:
    """156 R12: `cases --skip <why>` writes `Skill evals: skipped, <why>` and runs nothing; it
    refuses an empty why, and a change whose cases already ran."""
    root = _repo(tmp_path)
    tree = _ready(root, "skipped", "skipped's one")
    folder = _folder(tree)
    calls = []
    monkeypatch.setattr(factory, "_sdlc", lambda args, cwd: calls.append(args) or (0, {}, ""))
    code, out = _run(capsys, factory.cmd_cases, tree, "001", skip="  ")
    assert code == 1 and "why" in out["refusals"][0] and not (folder / "findings.md").exists()
    code, out = _run(capsys, factory.cmd_cases, tree, "001", skip="declined at landing")
    assert (code, out["note"]) == (0, "Skill evals: skipped, declined at landing")
    assert sdlc.findings_entries(folder)["cases"] == {"ran": False, "why": "declined at landing"}
    assert calls == [], "a skip runs nothing"
    factory._note_line(folder, factory.CASES_RE, "Skill evals: ran, 1 of 1; run: r")
    code, out = _run(capsys, factory.cmd_cases, tree, "001", skip="declined at landing")
    assert code == 1 and "already ran" in out["refusals"][0], out
    assert "Skill evals: ran, 1 of 1" in (folder / "findings.md").read_text(encoding="utf-8")


def _a_failed_run(root: Path, name: str = "cases-2026-11-18-1") -> str:
    """A run of the skills' cases in the main checkout's reports, `ship-basic` failed twice."""
    run = root / ".sdlc" / "reports" / name
    run.mkdir(parents=True)
    graders = [{"name": "asks-the-question", "explanation": "pattern not found"}]
    record = {"scope": "change", "verdicts": {
        "ship-basic": {"result": "failed", "runs": [
            {"score": 0.5, "graders": graders, "trace": f"{run}/traces/ship-basic-1.jsonl"},
            {"score": 0.5, "graders": [*graders, {"name": "never-writes", "explanation": "1x"}],
             "trace": None}]},
        "ship-risky": {"result": "environment", "runs": []}}}  # fmt: skip
    (run / "scope.json").write_text(json.dumps(record), encoding="utf-8")
    return f".sdlc/reports/{name}"


@needs_uv
def test_a_failed_case_is_a_signal_not_a_refusal(tmp_path, capsys, monkeypatch) -> None:
    """156 R13, R14, R15: a failed, environment or skipped case is a signal, with its graders and
    run, so `--by auto` can't land the change; the person's yes, which saw it, does. `land` never
    refuses a change whose cases ran with failures, or were skipped: only one where they didn't."""
    root = _repo(tmp_path)
    tree = _ready(root, "failing", "failing's one")
    folder = _folder(tree)
    _with_cases(monkeypatch, ["ship-basic", "ship-risky"])
    run = _a_failed_run(root)
    note = f"Skill evals: ran, 0 of 2; failed: ship-basic; environment: ship-risky; run: {run}"
    factory._note_line(folder, factory.CASES_RE, note)
    cfg, _ = factory.load_config(tree)
    signals, excluded = factory.landing.land_signals(folder, tree, "READY", cfg)
    assert excluded == []
    assert (f"skills' cases failed: ship-basic (asks-the-question, never-writes), trace in {run}"
            in signals), signals  # fmt: skip
    assert "skills' cases hit the environment: ship-risky" in signals
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    part = batch["batch"][0]["cases"]
    assert part == {"scope": ["ship-basic", "ship-risky"], "cap_usd": 5, "noted": True,
                    "failed": [{"case": "ship-basic",
                                "graders": ["asks-the-question", "never-writes"]}],
                    "environment": ["ship-risky"], "skipped": None, "run": run}  # fmt: skip
    assert "its failed or skipped skills' cases accepted as shown" in batch["question"]
    assert (
        f"  - failed: ship-basic (asks-the-question, never-writes), trace in {run}/traces"
        in (batch["shown"])
    )
    assert factory.landing._land_readiness(tree, folder, "person")["before"] == []
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert code == 1 and "skills' cases failed: ship-basic" in out["refusals"][0], out
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out

    other = _ready(root, "skipping", "skipping's one")
    skipped = _folder(other)
    assert factory.landing._land_readiness(other, skipped, "person")["before"] == ["cases"]
    factory._note_line(skipped, factory.CASES_RE, "Skill evals: skipped, declined at landing")
    assert factory.landing._land_readiness(other, skipped, "person")["before"] == []
    signals, _ = factory.landing.land_signals(skipped, other, "READY", cfg)
    assert "skills' cases skipped: declined at landing" in signals
    # With no readable record, the note alone still names the failed case.
    factory._note_line(
        skipped,
        factory.CASES_RE,
        "Skill evals: ran, 1 of 2; failed: ship-basic; run: .sdlc/reports/gone",
    )
    signals, _ = factory.landing.land_signals(skipped, other, "READY", cfg)
    assert "skills' cases failed: ship-basic, trace in .sdlc/reports/gone" in signals, signals


@needs_uv
def test_accept_and_cases_record_their_landing_step(tmp_path, capsys, monkeypatch) -> None:
    """2026-11-18-39: before the landing's commit, `accept` records `checks` and `cases` records
    `cases` in `runs/land-step.md`, so the board's track shows them rather than the build's; after
    the commit (145 R26) it records `recheck`, its own step after the gate."""
    root = _repo(tmp_path)
    tree = _ready(root, "stepped", "stepped's one")
    folder = _folder(tree)
    (folder / "checks.md").write_text(CHECKS, encoding="utf-8")
    reply = {"code": 0, "data": {"passed": True, "checks": [], "problems": []}}
    monkeypatch.setattr(factory, "_sdlc", lambda args, cwd: (reply["code"], reply["data"], ""))
    assert _land_step(folder) is None
    code, out = _run(capsys, factory.cmd_accept, tree, "001")
    assert (code, out["verdict"]) == (0, "PASS"), out
    step = _land_step(folder)
    assert (step["step"], step["round"], step["moves"]) == ("checks", None, 0), step
    assert "checks" in factory.LAND_STEPS and "cases" in factory.LAND_STEPS
    reply["data"] = {"skipped": "plugin eval is unavailable: early access"}
    code, out = _run(capsys, factory.cmd_cases, tree, "001")
    assert code == 0 and _land_step(folder)["step"] == "cases"
    intent = folder / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8").replace("stage: test", "stage: shipped"),
        encoding="utf-8",
    )
    reply["data"] = {"passed": True, "checks": [], "problems": []}
    assert _run(capsys, factory.cmd_accept, tree, "001")[0] == 0
    assert _land_step(folder)["step"] == "recheck", "145 R26: its own step after the gate"
    assert "recheck" in factory.LAND_STEPS


@needs_uv
def test_land_refuses_a_change_whose_checks_or_cases_havent_run(
    tmp_path, capsys, monkeypatch
) -> None:
    """103 R7, R12: `land` itself refuses, before writing anything, a change whose checks haven't
    passed on the build as it stands, or whose skills' cases haven't run; once they have, the
    person's yes lands it, and the commit says so."""
    root = _repo(tmp_path)
    tree = _ready(root, "checked", "checked's one")
    folder = _folder(tree)
    (folder / "checks.md").write_text(CHECKS, encoding="utf-8")

    def refused(why: str) -> None:
        code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
        assert code == 1 and why in out["refusals"][0], out
        intent = (folder / "intent.md").read_text(encoding="utf-8")
        assert "stage: test" in intent and "impact: minor" not in intent, "nothing written"
        assert _git(tree, "log", "-1", "--format=%s") == "init", "nothing committed"

    refused("factory.py accept 001")
    assert _run(capsys, factory.cmd_accept, tree, "001")[0] == 0
    (tree / "README.md").write_text("checked's one, again\ntwo\nthree\n", encoding="utf-8")
    refused("factory.py accept 001")
    assert _run(capsys, factory.cmd_accept, tree, "001")[0] == 0

    _with_cases(monkeypatch, ["ship-basic"])
    refused("factory.py cases 001")
    factory._note_line(folder, factory.CASES_RE, "Skill evals: ran, 1 of 1")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    body = _git(tree, "log", "-1", "--format=%B")
    assert "Sdlc-Landed: by=person" in body
    shown = _git(tree, "show", "--name-only", "--format=")
    assert f".sdlc/work/{tree.name}/build/land-accept.md" in shown, "the record lands with it"


OPEN_FINDING = (
    "# Findings\n\n## F1. [important] [correctness] A wrong count\n\nEvidence: a.py:1\n"
    "Class: logic\nDisposition: open\n"
)


@needs_uv
def test_a_landing_carries_drops_and_confirms_once(tmp_path, capsys) -> None:
    """103 R8: on the person's yes, land carries an undone item as a seed in the register, drops
    one the approver proposed dropping, confirms each assumed decision, all by line, before ship;
    when ship refuses after them, a rerun writes nothing twice."""
    root = _repo(tmp_path)
    tree = _ready(root, "noted", "noted's one")
    folder = _folder(tree)
    (folder / "notes.md").write_text(
        "# Notes\n\n- [ ] Page the list\n- [ ] Rename the flag\n", encoding="utf-8"
    )
    (folder / "decisions.md").write_text(
        "# Decisions\n\n- [ ] D1 (builder round 1, default): Page at 50? Going with 50.\n",
        encoding="utf-8",
    )
    (folder / "decision.md").write_text(
        "DECISION: READY\n\nFine.\n\n- IMPACT: minor — a test change\n"
        "- UNDONE: Rename the flag → dropped: the flag went away in round 2\n",
        encoding="utf-8",
    )
    (folder / "findings.md").write_text(OPEN_FINDING, encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert code == 1 and "sdlc.py ship refused" in out["refusals"][0], out

    def written() -> tuple[str, str, list[dict]]:
        notes = (folder / "notes.md").read_text(encoding="utf-8")
        decisions = (folder / "decisions.md").read_text(encoding="utf-8")
        return notes, decisions, sdlc.inbox_entries(_held(tree))

    notes, decisions, entries = written()
    assert [(e["status"], e["title"]) for e in entries] == [("idea", "Page the list")]
    seed = entries[0]["id"]
    assert f"- [x] Page the list → seed: {seed}\n" in notes
    assert "- [x] Rename the flag → dropped: the flag went away in round 2\n" in notes
    assert "- [ ]" not in notes
    assert (
        "- [x] D1 (builder round 1, default): Page at 50? Going with 50. → decided: the assumed "
        "default, confirmed when landing\n"
    ) in decisions
    assert "notes.md" in " ".join(entries[0]["text"])

    (folder / "findings.md").write_text(
        OPEN_FINDING.replace("Disposition: open", "Disposition: fixed"), encoding="utf-8"
    )
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    assert written() == (notes, decisions, entries), "the rerun wrote nothing twice"
    body = _git(tree, "log", "-1", "--format=%B")
    assert f"Carried forward:\n- Page the list → {seed}\n" in body
    assert "Dropped:\n- Rename the flag: the flag went away in round 2\n" in body
    names = _git(tree, "show", "--name-only", "--format=").splitlines()
    assert f".sdlc/work/{tree.name}/entries.md" in names, "committed, held for close"
    assert ".sdlc/work/inbox.md" not in names, "134 R1: the register never rides the branch"


NOTES = (
    "# Notes\n\n- [ ] Page the drafts list. Fifty a page would match the\n"
    "  search results, which page at fifty.\n"
    "  Nobody asked yet.\n\nAfter the list.\n"
    "- [ ] Rename the flag\n  to what the docs call it\n"
    "```\n- [ ] an example, never an item\n```\n"
)
CARRIED = (
    "Page the drafts list. Fifty a page would match the search results, which page at fifty. "
    "Nobody asked yet."
)


@needs_uv
def test_a_carried_note_keeps_its_continuation_lines(tmp_path, capsys) -> None:
    """109 R11: a note's text runs on through its indented lines, joined with single spaces, in
    what land-check shows and in the seed it is carried as; the tick goes on its `- [ ]` line."""
    root = _repo(tmp_path)
    tree = _ready(root, "noted", "noted's one")
    folder = _folder(tree)
    (folder / "notes.md").write_text(NOTES, encoding="utf-8")
    (folder / "decision.md").write_text(
        "DECISION: READY\n\nFine.\n\n- IMPACT: minor — a test change\n"
        "- UNDONE: Rename the flag → dropped: the docs moved on\n",
        encoding="utf-8",
    )
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    undone = batch["batch"][0]["undone"]
    assert [u["text"] for u in undone] == [CARRIED, "Rename the flag to what the docs call it"]
    assert "dropped" in undone[1], "a proposal on the note's first line still matches"
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    entry = next(e for e in sdlc.inbox_entries(_held(tree)) if e["status"] == "idea")
    assert CARRIED in " ".join(entry["text"]), entry
    notes = (folder / "notes.md").read_text(encoding="utf-8")
    assert f"- [x] Page the drafts list. Fifty a page would match the → seed: {entry['id']}\n" in (
        notes
    )
    assert "  search results, which page at fifty.\n  Nobody asked yet.\n" in notes
    assert "- [x] Rename the flag → dropped: the docs moved on\n  to what" in notes


def test_an_unproposed_seed_is_titled_from_its_first_sentence(tmp_path) -> None:
    """109 R12: with no proposal, a carried note's seed is titled by its first sentence, split as
    the landing commit splits a Problem; a note with no sentence end is its own title. A proposal
    matches a note by its first line or its full text."""
    assert factory.OPEN_NOTE_RE.pattern == sdlc.OPEN_ITEM_RE.pattern, "read as preflight reads"
    folder = tmp_path / "001-noted"
    folder.mkdir()
    (folder / "notes.md").write_text(NOTES, encoding="utf-8")
    pre = {"undone": {"items": [
        {"line": 3, "text": "Page the drafts list. Fifty a page would match the"},
        {"line": 8, "text": "Rename the flag"},
    ]}}  # fmt: skip
    parts = factory.landing.land_parts(folder, pre)["undone"]
    assert [p.get("seed") for p in parts] == [
        "Page the drafts list.",
        "Rename the flag to what the docs call it",
    ]
    assert [p["line"] for p in parts] == [3, 8], "ticked on its `- [ ]` line"
    (folder / "decision.md").write_text(
        f"DECISION: READY\n\n- UNDONE: {CARRIED} → seed: Page the drafts\n", encoding="utf-8"
    )
    assert factory.landing.land_parts(folder, pre)["undone"][0]["seed"] == "Page the drafts"


@needs_uv
def test_the_approver_proposes_dispositions_and_recovery(tmp_path, capsys) -> None:
    """103 R10: the approver is told the irreversible paths the diff touches, from the base
    branch's list, and asked for the RECOVER and UNDONE lines; an item it proposed nothing for is
    carried, never dropped; and a change with an irreversible path but no RECOVER stays out."""
    root = _repo(tmp_path)
    _config(root, '[review]\nirreversible = ["deploy/"]\n')
    tree = _ready(root, "deployed", "deployed's one")
    folder = _folder(tree)
    (tree / "deploy").mkdir()
    (tree / "deploy" / "run.sh").write_text("echo hi\n", encoding="utf-8")
    state = {"next": "approve", "round": 1, "exhausted": False}
    prompt, to, _ = factory._task(tree, folder, state, "approve", "builder", None)
    assert to == folder / "decision.md"
    assert "deploy/run.sh" in prompt and "- RECOVER:" in prompt and "- UNDONE:" in prompt
    approver = (ROOT / "plugins" / "factory" / "agents" / "approver.md").read_text(encoding="utf-8")
    assert "- UNDONE: <item text> → seed: <title>" in approver and "- RECOVER: <path" in approver

    pre = {"undone": {"items": [{"line": 3, "text": "Page the list"}]}}
    assert factory.landing.land_parts(folder, pre)["undone"] == [
        {"line": 3, "text": "Page the list", "seed": "Page the list"}
    ], "nothing proposed: carried as a seed titled by itself"

    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    assert batch["batch"] == [] and "no How to recover for deploy/run.sh" in " ".join(
        batch["excluded"][0]["excluded"]
    )
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert code == 1 and out["refusals"][0].startswith("ship it by hand"), out
    assert _git(tree, "log", "-1", "--format=%s") == "config", "nothing committed"


PRE = "pre-existing: README.md:2: the second line says two, and nothing reads it"
BUG = f"- UNDONE: {PRE} → bug: med: README.md, docs/a.md: The second line is never read\n"


def test_the_approver_may_propose_a_preexisting_item_as_a_bug(tmp_path) -> None:
    """114 R17: a `pre-existing:` item may be proposed as a bug, its severity, paths and title
    read from the line; the prompt and the agent file both give the format."""
    folder = tmp_path / "001-noted"
    folder.mkdir()
    (folder / "notes.md").write_text(f"# Notes\n\n- [ ] {PRE}\n- [ ] Page the list\n")
    (folder / "decision.md").write_text(f"DECISION: READY\n\n{BUG}")
    undone, _ = factory.landing.read_proposals(folder)
    title = "The second line is never read"
    assert undone[PRE] == ("bug", "med", ["README.md", "docs/a.md"], title)
    pre = {"undone": {"items": [{"line": 3, "text": PRE}, {"line": 4, "text": "Page the list"}]}}
    parts = factory.landing.land_parts(folder, pre)["undone"]
    assert parts[0]["bug"] == {"severity": "med", "paths": ["README.md", "docs/a.md"],
                               "title": "The second line is never read"}  # fmt: skip
    assert parts[0]["shown"] == (
        "filed as a bug, med: The second line is never read (README.md, docs/a.md)"
    )
    assert parts[1] == {"line": 4, "text": "Page the list", "seed": "Page the list"}
    assert factory.TICKED_RE.match(f"- [x] {PRE} → bug: 2026-11-18-3").group(2) == "bug"
    state = {"next": "approve", "round": 1, "exhausted": False}
    prompt, _, _ = factory._task(folder.parent, folder, state, "approve", "builder", None)
    assert "→ bug: <severity>: <path>[, <path>…]: <title>" in prompt
    approver = (ROOT / "plugins" / "factory" / "agents" / "approver.md").read_text(encoding="utf-8")
    assert "- UNDONE: <item text> → bug: <severity>: <path>[, <path>…]: <title>" in approver


@needs_uv
def test_a_landing_files_each_approved_bug_once(tmp_path, capsys) -> None:
    """114 R18: land-check checks a bug's severity against the process doc's words, its paths and
    its item, leaving a bad one for ship; the person's yes files each approved bug once, with its
    `Severity:` and `Paths:`, ticks it `→ bug: <id>`, and the commit names it in no paragraph."""
    root = _repo(tmp_path)
    tree = _ready(root, "noted", "noted's one")
    folder = _folder(tree)
    (folder / "notes.md").write_text(f"# Notes\n\n- [ ] {PRE}\n- [ ] Page the list\n")
    decision = folder / "decision.md"
    head = "DECISION: READY\n\nFine.\n\n- IMPACT: minor — a test change\n"
    for bad, why in (
        (BUG.replace("bug: med:", "bug: urgent:"), "urgent, not one of high, med, low"),
        (BUG.replace("med: README.md, docs/a.md:", "med: :"), "names no paths"),
        ("- UNDONE: Page the list → bug: med: README.md: Paging\n", "isn't a pre-existing: item"),
    ):  # fmt: skip
        decision.write_text(head + bad)
        code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
        assert batch["batch"] == [], batch
        said = " ".join(batch["excluded"][0]["excluded"])
        assert why in said and "ship it by hand" in said, said
    decision.write_text(head + BUG)
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    [entry] = batch["batch"]
    assert entry["undone"][0]["shown"].startswith("filed as a bug, med: The second line")
    assert "filed as bugs" in batch["question"]
    assert f"- {PRE} → filed as a bug, med: The second line" in batch["shown"], batch["shown"]

    (folder / "findings.md").write_text(OPEN_FINDING, encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert code == 1 and "sdlc.py ship refused" in out["refusals"][0], out
    bugs, problems = sdlc.bug_entries(_held(tree))
    assert problems == [] and len(bugs) == 1
    [bug] = bugs
    assert (bug["title"], bug["severity"], bug["paths"]) == (
        "The second line is never read",
        "med",
        ["README.md", "docs/a.md"],
    )
    assert bug["introduced_by"] is None, "an escape is confirmed, never assumed here"
    assert bug["text"].startswith(f"Found by the review of {tree.name}. {PRE}")
    notes = (folder / "notes.md").read_text(encoding="utf-8")
    assert f"- [x] {PRE} → bug: {bug['id']}\n" in notes
    register = (folder / factory.landing.ENTRIES).read_text(encoding="utf-8")

    (folder / "findings.md").write_text(
        OPEN_FINDING.replace("Disposition: open", "Disposition: fixed"), encoding="utf-8"
    )
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    assert (folder / factory.landing.ENTRIES).read_text(encoding="utf-8") == register, (
        "a rerun files nothing twice"
    )
    body = _git(tree, "log", "-1", "--format=%B")
    assert "Carried forward:\n- Page the list →" in body
    assert "second line" not in body, "a bug is in neither Carried forward nor Dropped"


# ---------------------------------------------------------------- the agents' nits (129)

TERSE = "README.md:1: terse wording. Say what it is {docs S low}"
TERSE_FILED = {
    "title": "terse wording.", "text": "README.md:1: terse wording. Say what it is",
    "theme": "docs", "paths": ["README.md"], "cost": "S", "value": "low",
    "pass": "correctness", "role": "code", "round": 1,
    "shown": "[nit] terse wording. (docs, S, low; README.md)",
}  # fmt: skip


def _nit(folder: Path, role: str, *nits: str) -> None:
    """Add `- NIT:` lines to the build round's `role` review."""
    path = folder / "reviews" / "round-1" / f"{role}.md"
    path.write_text(path.read_text() + "".join(f"- NIT: {n}\n" for n in nits))


@needs_uv
def test_land_check_shows_the_nits_it_would_file(tmp_path, capsys) -> None:
    """129 R8: each change carries the nits `carry` records to file, from the same reading, and the
    question says they are filed as shown."""
    root = _repo(tmp_path)
    tree = _ready(root, "noted", "noted's one")
    folder = _folder(tree)
    _nit(folder, "code", TERSE, "the names are long {style M low}")
    _nit(folder, "test", "README.md:3: a third line {tests L med}")
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    [entry] = batch["batch"]
    assert entry["nits"] == [TERSE_FILED]
    assert "nits to file: 1" in entry["signals"]
    assert "its agents' nits filed as shown" in batch["question"]
    rounds = factory._rounds_at_depth(tree, folder, factory.load_config(tree)[0])[0]
    carried = [i["file"] for i in factory.agent_findings(rounds) if i["file"]]
    assert [{k: v for k, v in n.items() if k != "shown"} for n in entry["nits"]] == carried


def test_land_question_names_the_nits() -> None:
    """129 R8: the clause is there when some change in the batch files a nit, and only then."""
    plain = factory.landing.land_question([_entry("001-a"), _entry("002-b")], "main")
    assert "nits" not in plain
    one = factory.landing.land_question(
        [_entry("001-a"), _entry("002-b", nits=[TERSE_FILED])], "main"
    )
    assert one == plain.replace(
        "each shipped with its approver's impact, ",
        "each shipped with its approver's impact, its agents' nits filed as shown, ",
    )
    notes = factory.landing.land_question(
        [_entry("001-a", nits=[TERSE_FILED], undone=[{"line": 1, "text": "t", "seed": "t"}],
                recover=["a/: b"])], "main",
    )  # fmt: skip
    assert (
        "its undone notes carried or dropped as shown, its agents' nits filed as shown, " in notes
    )
    assert notes.index("nits filed") < notes.index("with how to recover shown")


@needs_uv
def test_nits_to_file_keep_the_gate_the_persons(tmp_path, capsys) -> None:
    """129 R9: a nit to file is a signal, saying how many fell past the cap: the batch isn't clear,
    and `land --by auto` refuses it before writing anything."""
    root = _repo(tmp_path)
    tree = _ready(root, "noted", "noted's one")
    folder = _folder(tree)
    assert _run(capsys, factory.landing.cmd_land_check, root, [])[1]["clear"] is True
    _nit(folder, "code", *(f"README.md:{i}: wording {i} {{docs M low}}" for i in range(1, 8)))
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    assert batch["clear"] is False
    assert batch["batch"][0]["signals"] == ["nits to file: 5, 2 past the cap of 5"]
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert code == 1 and "the gate is the person's: nits to file: 5" in out["refusals"][0]
    assert _git(tree, "log", "-1", "--format=%s") == "init", "nothing committed"
    assert not (tree / ".sdlc" / "work" / "inbox.md").exists(), "nothing filed"


@needs_uv
def test_a_landing_files_the_nits_sdlc_reads(tmp_path, capsys) -> None:
    """129 R10: the person's yes files each nit as a `[nit]` entry `sdlc.py` reads with no
    problem, its id from the one `next-entry` call the seeds and bugs take theirs from, in the
    change's own commit, and `land` reports the ids."""
    root = _repo(tmp_path)
    tree = _ready(root, "noted", "noted's one")
    folder = _folder(tree)
    (folder / "notes.md").write_text(f"# Notes\n\n- [ ] {PRE}\n- [ ] Page the list\n")
    (folder / "decision.md").write_text(
        "DECISION: READY\n\nFine.\n\n- IMPACT: minor — a test change\n" + BUG
    )
    _nit(folder, "code", TERSE)
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    nits, problems = sdlc.nit_entries(_held(tree))
    assert problems == [] and len(nits) == 1
    [nit] = nits
    assert out["filed_nits"] == [nit["id"]]
    assert (nit["title"], nit["theme"], nit["paths"], nit["cost"], nit["value"]) == (
        "terse wording.", "docs", ["README.md"], "S", "low",
    )  # fmt: skip
    assert (nit["by"], nit["pass"]) == (tree.name, "correctness")
    assert nit["text"].startswith(
        f"Raised by the code review of {tree.name}, round 1: README.md:1: terse wording. Say what"
    )
    [bug] = sdlc.bug_entries(_held(tree))[0]
    seeds = [e["id"] for e in sdlc.inbox_entries(_held(tree)) if e["status"] == "idea"]
    assert len({nit["id"], bug["id"], *seeds}) == 3, "one next-entry call, three ids"
    names = _git(tree, "show", "--name-only", "--format=").splitlines()
    assert f".sdlc/work/{tree.name}/entries.md" in names and ".sdlc/work/inbox.md" not in names


@needs_uv
def test_a_landing_rerun_files_each_nit_once(tmp_path, capsys) -> None:
    """129 R11: a rerun of the yes's writes skips a nit the register already holds for this change,
    matched by its `Raised by:` and its text, never by its title alone."""
    root = _repo(tmp_path)
    tree = _ready(root, "noted", "noted's one")
    folder = _folder(tree)
    _nit(folder, "code", TERSE, "README.md:2: terse wording. Another one {docs M low}")
    pre, _ = factory.landing._preflight(folder, tree)
    filed, refused = factory.landing._dispose(tree, folder, pre)
    assert refused is None and len(filed) == 2
    register = folder / factory.landing.ENTRIES
    once = register.read_text(encoding="utf-8")
    assert once.count("] [nit] terse wording.") == 2, "one title, two nits: both filed"
    assert factory.landing._dispose(tree, folder, pre) == ([], None)
    assert register.read_text(encoding="utf-8") == once
    assert len(sdlc.nit_entries(_held(tree))[0]) == 2


@needs_uv
def test_a_rebased_change_runs_its_checks_again_before_its_review(tmp_path, capsys) -> None:
    """103 R11: after a rebase, a change with acceptance checks runs them again on its commit as
    rebased, after a green gate and before any review; a red check is a stop."""
    root = _repo(tmp_path)
    _config(root, '[commands]\ncheck = "true"\n')
    tree = _ready(root, "checked", "checked's one")
    folder = _folder(tree)
    (folder / "checks.md").write_text(
        CHECKS.replace("```sh\ntrue", "```sh\ntest ! -f broken.txt"), encoding="utf-8"
    )
    assert _run(capsys, factory.cmd_accept, tree, "001")[0] == 0
    (root / "elsewhere.txt").write_text("moved on\n", encoding="utf-8")
    _git(root, "add", "elsewhere.txt")
    _git(root, "commit", "-q", "-m", "main moves on")

    assert _stack(root, tree, capsys, "person")["state"] == "stacked"
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "gate", out
    assert _run(capsys, factory.cmd_gate, tree, "001", True)[0] == 0
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "accept" and out["missing"] == ["behaviour"], out
    assert _run(capsys, factory.cmd_accept, tree, "001")[0] == 0
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "review", out

    (tree / "broken.txt").write_text("", encoding="utf-8")
    assert _run(capsys, factory.cmd_accept, tree, "001")[0] == 1
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "stop" and "build/land-accept.md" in out["problems"][0], out


def _train(root: Path, capsys, trees: list[Path], by: str = "auto") -> None:
    """Begin a train over `trees`' changes, unless one is under way."""
    if factory.read_train(root) is not None:
        return
    code, out = _run(capsys, factory.landing.cmd_train, root, begin=[t.name for t in trees], by=by)
    assert code == 0 and out["state"] == "begun", out


def _stack(root: Path, tree: Path, capsys, by: str = "auto") -> dict:
    """The change landed and stacked on the base through a train of one, as the skill does it:
    `land --by` (committed), then the stack the reading names. Returns the stack's output, state
    `stacked` with its round when the base moved, else the reading, `next: close`."""
    num = tree.name.split("-")[0]
    code, out = _run(capsys, factory.landing.cmd_land, tree, num, by)
    assert (code, out["state"]) == (0, "committed"), out
    _train(root, capsys, [tree], by)
    code, reading = _run(capsys, factory.landing.cmd_train, root)
    if reading["next"] != "stack":
        return reading
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, num, False, onto=reading["onto"])
    assert code == 0, out
    return out


@needs_uv
def test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone(
    tmp_path, capsys
) -> None:
    """103 R13: a batch of three, one with acceptance checks, one with an undone note, one touching
    an irreversible path, lands behind the person's one yes through `factory.py` alone: every
    change closed on main, the carried seed in the register, `How to recover:` in the commit."""
    root = _repo(tmp_path)
    _config(root, '[review]\nirreversible = ["deploy/"]\n')
    checked = _ready(root, "checked", "one")
    noted = _ready(root, "noted", "one")
    deployed = _ready(root, "deployed", "one")
    for tree in (checked, noted, deployed):
        (tree / "README.md").write_text("one\ntwo\nthree\n", encoding="utf-8")
        (tree / f"{tree.name}.txt").write_text("built\n", encoding="utf-8")
    (_folder(checked) / "checks.md").write_text(
        CHECKS.replace("```sh\ntrue", f"```sh\ntest -f {checked.name}.txt"), encoding="utf-8"
    )
    (_folder(noted) / "notes.md").write_text("# Notes\n\n- [ ] Page the list\n", encoding="utf-8")
    (deployed / "deploy").mkdir()
    (deployed / "deploy" / "run.sh").write_text("echo hi\n", encoding="utf-8")
    with (_folder(deployed) / "decision.md").open("a", encoding="utf-8") as f:
        f.write("- RECOVER: deploy/: fix forward: a release without deploy/run.sh\n")

    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    assert [c["change"] for c in batch["batch"]] == [checked.name, noted.name, deployed.name]
    assert batch["excluded"] == [] and batch["clear"] is False
    question = batch["question"]
    for clause in ("its acceptance checks run as shown", "undone notes carried or dropped",
                   "with how to recover shown"):  # fmt: skip
        assert clause in question, question

    # The person's yes; then the train, as the skill's Step 3 runs it: the checks first, each
    # change committed, stacked (each numbered locally conflicts on `.sdlc/last-id` alone, which
    # settles itself), reviewed as stacked, and closed in order.
    readings = drive_train(factory, root, capsys, [checked, noted, deployed], "person", strict=True)
    assert readings[0]["next"] == "commit" and readings[0]["before"] == ["accept"], readings[0]

    log = _git(root, "log", "--format=%s", "--first-parent", "main").splitlines()
    for tree in (checked, noted, deployed):
        assert f"Close {tree.name}" in log
    entries = sdlc.inbox_entries(root)
    assert [(e["status"], e["title"]) for e in entries] == [("idea", "Page the list")]
    bodies = _git(root, "log", "--format=%B", "main")
    assert "How to recover:\n- deploy/: fix forward: a release without deploy/run.sh" in bodies
    assert f"Carried forward:\n- Page the list → {entries[0]['id']}" in bodies
    assert bodies.count("Sdlc-Landed: by=person") == 3


# ---------------------------------------------------------------- following main (104)


OWN = """# Ideas

> The register.

## [2026-11-17-5] [nit] A nit the change takes in

Paths: README.md

## [2026-11-17-6] [idea] The change's own seed

Raised 2026-11-17.

## [2026-11-17-7] [bug] A bug the change fixes

Severity: minor

## [2026-11-17-8] [nit] A nit no change names

Paths: README.md
"""


def _resolving(tmp_path: Path, capsys, edit: tuple[str, str]) -> tuple[Path, Path]:
    """A change landed before 134 over a register that names its seed, the bug it fixes and a nit
    it takes in, its commit deleting them, its rebase left conflicted in the register by the base
    branch's `edit` to it, and the builder's resolution: the base branch's register, everything
    the landing deleted kept."""
    root = _repo(tmp_path)
    (root / ".sdlc" / "work").mkdir(parents=True)
    register = root / ".sdlc" / "work" / "inbox.md"
    register.write_text(OWN, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a register")
    tree = _ready(root, "own", "own's one")
    intent = _folder(tree) / "intent.md"
    text = intent.read_text(encoding="utf-8").replace("idea:", "idea: 2026-11-17-6", 1)
    text = text.replace("---\n", "---\nfixes: [2026-11-17-7]\n", 1)
    intent.write_text(text + "\nTakes in nit 2026-11-17-5.\n", encoding="utf-8")
    assert factory.frontmatter(text).get("idea") == "2026-11-17-6", text
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "committed"), out
    # A branch landed before 134, whose commit deleted what it took from the register itself.
    factory.landing.drop_entries(tree, ["2026-11-17-5", "2026-11-17-6", "2026-11-17-7"])
    _git(tree, "commit", "-q", "--amend", "-a", "--no-edit")
    landed = _git(tree, "show", "HEAD:.sdlc/work/inbox.md")
    assert "2026-11-17-6" not in landed and "2026-11-17-5" not in landed, landed
    register.write_text(OWN.replace(*edit), encoding="utf-8")
    _git(root, "commit", "-q", "-am", "main edits the register")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "committed"), out
    (_folder(tree) / "reviews" / "land-1").mkdir(parents=True)
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", False, onto="main")
    assert out["state"] == "conflict" and ".sdlc/work/inbox.md" in out["conflicted"], out
    (tree / ".sdlc" / "work" / "inbox.md").write_text(OWN.replace(*edit), encoding="utf-8")
    return root, tree


@needs_uv
def test_a_landing_resolution_never_keeps_the_change_s_own_seeds(tmp_path, capsys) -> None:
    """109 R13, the 104 case: the base branch tagged the change's seed `[building]` while its ship
    deleted it, and the builder's resolution kept it. `resolve --continue` deletes every entry the
    change's `idea:` and `fixes:` name, by id, and leaves the rest byte for byte."""
    edit = ("[2026-11-17-6] [idea]", "[2026-11-17-6] [building]")
    root, tree = _resolving(tmp_path, capsys, edit)
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert out["dropped"] == ["2026-11-17-5", "2026-11-17-6", "2026-11-17-7"], out
    landed = _git(tree, "show", "HEAD:.sdlc/work/inbox.md") + "\n"
    assert (
        landed == "# Ideas\n\n> The register.\n\n## [2026-11-17-8] [nit] A nit no change "
        "names\n\nPaths: README.md\n"
    ), landed


@needs_uv
def test_a_landing_resolution_never_keeps_the_nits_it_retired(tmp_path, capsys) -> None:
    """109 R13: the base branch edited a nit the landing retired, and the builder kept it; the
    landed commit doesn't have it, and an open nit the change doesn't name stays."""
    edit = ("Paths: README.md\n\n## [2026-11-17-6]", "Paths: README.md, docs/\n\n## [2026-11-17-6]")
    root, tree = _resolving(tmp_path, capsys, edit)
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert "2026-11-17-5" in out["dropped"], out
    landed = _git(tree, "show", "HEAD:.sdlc/work/inbox.md")
    assert "2026-11-17-5" not in landed and "docs/" not in landed, landed
    assert "## [2026-11-17-8] [nit] A nit no change names\n\nPaths: README.md" in landed


def test_a_resolution_drops_entries_by_id_alone(tmp_path) -> None:
    """109 R13: an `idea:` naming its seed by title is skipped, never matched; a fenced example of
    an id is never an entry."""
    assert factory.frontmatter_ids("---\nidea: Reopen drafts\n---\n", "idea") == []
    text = "---\nfixes: [2026-11-17-7, Some bug]\nidea: 2026-11-17-6\n---\n"
    assert factory.frontmatter_ids(text, "fixes") == ["2026-11-17-7"]
    assert factory.frontmatter_ids(text, "idea") == ["2026-11-17-6"]
    (tmp_path / ".sdlc" / "work").mkdir(parents=True)
    register = tmp_path / ".sdlc" / "work" / "inbox.md"
    fenced = OWN + "\n```\n## [2026-11-17-6] [idea] an example\n```\n"
    register.write_text(fenced, encoding="utf-8")
    assert factory.landing.drop_entries(tmp_path, ["2026-11-17-6"]) == ["2026-11-17-6"]
    after = register.read_text(encoding="utf-8")
    assert "## [2026-11-17-6] [idea] an example" in after and "own seed" not in after


def test_resolve_needs_onto_or_continue(tmp_path, capsys) -> None:
    """147 R13: the bare `resolve <NNN>` is gone: it takes exactly one of `--onto` and
    `--continue`, from the command line and from the function alike."""
    root = _repo(tmp_path)
    tree = _ready(root, "lone", "lone's one")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", False)
    assert code == 1 and "--onto" in out["refusals"][0] and "--continue" in out["refusals"][0]
    script = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
    for args in (["resolve", "001"], ["resolve", "001", "--onto", "main", "--continue"]):
        done = subprocess.run([sys.executable, str(script), *args], cwd=tree,
                              capture_output=True, encoding="utf-8")  # fmt: skip
        assert done.returncode == 2, (args, done.stdout, done.stderr)


@needs_uv
def test_resolve_onto_the_base_outside_a_train(tmp_path, capsys) -> None:
    """147 R13: outside a train, `--onto` takes the base branch alone, by name or by its tip, and
    rebases the change's own commits from their merge base: `stacked`, then `current`; it writes
    no train state and opens no landing round; any other commit is refused."""
    root = _repo(tmp_path)
    tree = _ready(root, "lone", "lone's one")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "committed"), out
    (root / "elsewhere.txt").write_text("moved on\n", encoding="utf-8")
    _git(root, "add", "elsewhere.txt")
    _git(root, "commit", "-q", "-m", "main moves on")
    tip = _git(root, "rev-parse", "main")
    old = _git(tree, "rev-parse", "HEAD^")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", False, onto=old)
    assert code == 1 and "only the base branch" in out["refusals"][0], out
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", False, onto="main")
    assert (code, out["state"]) == (0, "stacked"), out
    assert _git(tree, "rev-parse", "HEAD^") == tip
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", False, onto=tip)
    assert (code, out["state"]) == (0, "current"), out
    assert factory.read_train(root) is None, "no train state written"
    assert not list((_folder(tree) / "reviews").glob("land-*")), "no landing round opened"


# A command that is not a read, with its output and no exit: 123 moved it off `head`, which a
# read showing its output now passes, so 109's tests still test a real missing exit.
NO_EXIT = "VERDICT: PASS\n\nIt reopens.\n\n## Evidence\n\n$ uv run pytest -q\n3 passed\n"
PASSED = "VERDICT: PASS\n\nIt reopens.\n\n## Evidence\n\n$ head -5 intent.md\n---\nexit: 0\n"


@pytest.mark.portable
def test_no_exit_is_not_a_read() -> None:
    """123 R7: `NO_EXIT` keeps 109's landing tests on a real missing exit; were it a read again,
    they would pass for the wrong reason."""
    assert factory.read_evidence(NO_EXIT, "r") == ["r: `uv run pytest -q` has no `exit:` line"]


# 119-ui-review-folders' two landing behaviour replies, as bug 2026-11-17-90 quotes their commands,
# rebuilt with the elided arguments filled in: every command a read, its output shown, no exit.
W119 = ".sdlc/work/119-ui-review-folders"
CHAIN_119 = (
    f'grep -n "^VERDICT" {W119}/build/round-1.gate.md ; '
    f'grep -n "^VERDICT" {W119}/build/land-1.gate.md ; '
    f"cmp {W119}/build/round-1.gate.md {W119}/build/land-1.gate.md"
)
REPLY_119 = f"""VERDICT: PASS

The landing gate's verdict matches the build's; nothing the rebase touched changed the result.

## Evidence

$ {CHAIN_119}
1:VERDICT: PASS
1:VERDICT: PASS
"""
MENDED_119 = f"""VERDICT: PASS

The plan still says what was built.

## Evidence

$ cat {W119}/plan.md
# 119 — Review folders in the UI · plan

## Files to change
"""


@needs_uv
def test_119s_landing_replies_pass(tmp_path, capsys) -> None:
    """123 R5: 119's landing replies, a chain of reads and the mend's `cat`, each showing its output
    and no `exit:`, pass: the landing is neither mended nor stopped for the missing exits."""
    root, tree = _landing(tmp_path, capsys)
    reply = _folder(tree) / "reviews" / "land-1" / "behaviour.md"
    for text in (REPLY_119, MENDED_119):
        reply.write_text(text, encoding="utf-8")
        code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
        assert out["next"] not in ("mend", "stop"), out
        assert not any("exit:" in p for p in out.get("problems", [])), out


def _landing(tmp_path: Path, capsys, config: str | None = None) -> tuple[Path, Path]:
    """A ready change whose landing stacked it onto a base branch that moved, through a train of
    one: round `land-1` open, its behaviour check to run (and the gate first, when `config` names
    one)."""
    root = _repo(tmp_path)
    if config:
        _config(root, config)
    tree = _ready(root, "mended", "mended's one")
    (root / "elsewhere.txt").write_text("moved on\n", encoding="utf-8")
    _git(root, "add", "elsewhere.txt")
    _git(root, "commit", "-q", "-m", "main moves on")
    out = _stack(root, tree, capsys)
    assert (out["state"], out["round"]) == ("stacked", 1), out
    return root, tree


def _replies(monkeypatch, reply: str, figures: dict | None = None) -> list[list[str]]:
    """A stand-in for `claude -p` that replies `reply`, reporting `figures`; the argv of each
    call, in order."""
    calls: list[list[str]] = []

    def fake(argv: list[str], cwd: Path):
        calls.append(argv)
        return 0, [reply], None, figures

    monkeypatch.setattr(factory, "_claude", fake)
    return calls


@needs_uv
def test_a_landing_review_reads_the_change_from_its_rounds_own_base(tmp_path, capsys) -> None:
    """121: a commit that reaches the base branch after the landing rebased the change is never
    in the diff its reviewers and verifier are told to read, so it never reads as the change's."""
    root, tree = _landing(tmp_path, capsys)
    folder = _folder(tree)
    rebased_onto = _git(root, "rev-parse", "main")
    (root / "later.txt").write_text("filed after the rebase\n", encoding="utf-8")
    _git(root, "add", "later.txt")
    _git(root, "commit", "-q", "-m", "main moves again, under the landing")
    moved = _git(root, "rev-parse", "main")
    (folder / "reviews" / "land-1" / "code.md").write_text(
        "VERDICT: CHANGES\n- CHANGE: later.txt:1: put it back\n", encoding="utf-8"
    )
    for task, role in (("land-review", "code"), ("land-verify", "verifier")):
        prompt = factory._land_task(tree, folder, task, role)[0]
        assert f"git diff {rebased_onto}...HEAD" in prompt, prompt
        assert moved not in prompt and "may have moved" in prompt, prompt
    named = _git(tree, "diff", "--name-only", f"{rebased_onto}...HEAD").splitlines()
    assert "later.txt" not in named and "README.md" in named, named
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert (code, out["state"]) == (0, "moved"), "the script catches the move, never a review"


@needs_uv
def test_a_landing_review_with_no_fork_point_is_refused(tmp_path, capsys, monkeypatch) -> None:
    """121: with no merge base to read the round's diff from, the landing's review and verify
    are refused, never handed a diff against the base branch's tip."""
    root = _repo(tmp_path)
    tree = _ready(root, "forkless", "forkless's one")
    assert _run(capsys, factory.landing.cmd_land, tree, "001", "auto")[1]["state"] == "committed"
    _move(root, 1)
    _git(tree, "rebase", "-q", "main")  # by hand, outside a train
    folder = _folder(tree)
    (folder / "reviews" / "land-1").mkdir(parents=True)
    (folder / "reviews" / "land-1" / "code.md").write_text(
        "VERDICT: CHANGES\n- CHANGE: README.md:1: name it\n", encoding="utf-8"
    )
    real = factory._git
    monkeypatch.setattr(
        factory, "_git", lambda r, *a: None if a[:1] == ("merge-base",) else real(r, *a)
    )
    for task, role in (("land-review", "code"), ("land-verify", "verifier")):
        refused = factory._land_task(tree, folder, task, role)
        assert isinstance(refused, str) and "no fork point between main and HEAD" in refused


@needs_uv
def test_a_landing_review_missing_an_exit_is_mended_not_stopped(tmp_path, capsys) -> None:
    """109 R1: a landing behaviour check whose read has no `exit:` is a mend, not a stop."""
    root, tree = _landing(tmp_path, capsys)
    reviews = _folder(tree) / "reviews" / "land-1"
    (reviews / "behaviour.md").write_text(NO_EXIT, encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert (out["next"], out["mend"]) == ("mend", ["behaviour"]), out
    (reviews / "behaviour.md").write_text("VERDICT: PASS\n\nIt reopens.\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert (out["next"], out["mend"]) == ("mend", ["behaviour"]), "no section at all"


@needs_uv
def test_a_landing_verdict_that_disagrees_is_mended(tmp_path, capsys) -> None:
    """109 R2, 140 R6–R7: a landing reply whose verdict follows prose is read where it stands;
    one whose verdict lines disagree, none of them first, is a mend for its role."""
    root, tree = _landing(tmp_path, capsys)
    reviews = _folder(tree) / "reviews" / "land-1"
    (reviews / "behaviour.md").write_text("I ran it.\n\n" + PASSED, encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "pass" and not out["problems"], out
    (reviews / "behaviour.md").write_text("I ran it.\nVERDICT: CHANGES\n" + PASSED, "utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert (out["next"], out["mend"]) == ("mend", ["behaviour"]), out
    (reviews / "behaviour.md").write_text("I couldn't run it.\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "stop", "no verdict anywhere: nothing to put first"


@needs_uv
def test_a_landing_stops_for_cause_even_beside_a_mendable_problem(tmp_path, capsys) -> None:
    """109 R6: a red landing gate beside a missing exit stops the landing; a mend can't move it."""
    config = '[commands]\ncheck = "test ! -f broken.txt"\n'
    root, tree = _landing(tmp_path, capsys, config)
    (tree / "broken.txt").write_text("", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert (code, out["verdict"]) == (1, "FAIL"), out
    (_folder(tree) / "reviews" / "land-1" / "behaviour.md").write_text(NO_EXIT, encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "stop" and not out.get("mend"), out
    assert any("ship it by hand" in p for p in out["problems"]), out


@needs_uv
def test_a_landing_mend_writes_into_its_landing_round(tmp_path, capsys, monkeypatch) -> None:
    """109 R4: `land-mend` runs a new behaviour check, told to run what its claims rest on again,
    and writes its reply over `reviews/land-1/behaviour.md`, never under `reviews/round-*`."""
    root, tree = _landing(tmp_path, capsys)
    folder = _folder(tree)
    reply = folder / "reviews" / "land-1" / "behaviour.md"
    reply.write_text(NO_EXIT, encoding="utf-8")
    before = {p.name: p.read_bytes() for p in (folder / "reviews" / "round-1").iterdir()}
    calls = _replies(monkeypatch, PASSED)
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-mend", "behaviour", None)
    assert (code, out["to"]) == (0, f".sdlc/work/{tree.name}/reviews/land-1/behaviour.md"), out
    prompt = calls[0][calls[0].index("-p") + 1]
    assert "Review landing round 1" in prompt and "## Evidence" in prompt, prompt
    assert "--session-id" in calls[0], "a new behaviour check"
    assert reply.read_text(encoding="utf-8") == PASSED
    after = {p.name: p.read_bytes() for p in (folder / "reviews" / "round-1").iterdir()}
    assert after == before, "the build round untouched"
    assert (folder / "runs" / "mended").read_text(encoding="utf-8") == "behaviour land-1\n"
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "pass", out


@needs_uv
def test_a_landing_mend_is_once_a_role_a_round(tmp_path, capsys, monkeypatch) -> None:
    """109 R3, R10: each role is mended once a landing round; a build round's mend and a
    landing's never use up each other's. A verifier whose answers can't be read is resumed."""
    root, tree = _landing(tmp_path, capsys)
    folder = _folder(tree)
    reviews = folder / "reviews" / "land-1"
    (reviews / "behaviour.md").write_text("Ran it.\nVERDICT: CHANGES\n" + PASSED, "utf-8")
    (folder / "runs").mkdir(exist_ok=True)
    (folder / "runs" / "mended").write_text("behaviour 1\n", encoding="utf-8")
    (folder / "runs" / "reviewer-behaviour.sessions").write_text("s-b\n", encoding="utf-8")
    calls = _replies(monkeypatch, "Ran it again.\nVERDICT: CHANGES\n" + PASSED)
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-mend", "behaviour", None)
    assert code == 0, "a build round's mend leaves the landing's"
    assert calls[0][-2:] == ["--resume", "s-b"], "the reviewer resumed to put its verdict first"
    assert factory.mended(folder) == {("behaviour", 1)}, "and the landing's leaves the build's"
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "stop", "still disagreeing after its one mend"
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-mend", "behaviour", None)
    assert code == 1 and "not a mend for behaviour" in out["refusals"][0], out
    assert len(calls) == 1, "refused before any session"

    (reviews / "behaviour.md").write_text(
        "VERDICT: CHANGES\n- CHANGE: README.md:1: keep both\n\n## Evidence\n$ true\nexit: 0\n",
        encoding="utf-8",
    )
    # 111: an answer naming no change of the landing round says which round: land-1, not round 1.
    (reviews / "verified.md").write_text("- KEPT: behaviour: C9: made up\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert any("C9, which no change of land-1 is" in p for p in out["problems"]), out
    assert not any("round 1" in p for p in out["problems"]), out
    (reviews / "verified.md").write_text("- **KEPT:** behaviour: C1: keep both\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert (out["next"], out["mend"]) == ("mend", ["verifier"]), out
    assert "reviews/land-1/verified.md" in out["problems"][0], out
    (folder / "runs" / "verifier.sessions").write_text("s-v\n", encoding="utf-8")
    calls = _replies(monkeypatch, "- DROPPED: behaviour: C1: README.md:1: keep both — it does\n")
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-mend", "verifier", None)
    assert (code, out["to"]) == (0, f".sdlc/work/{tree.name}/reviews/land-1/verified.md"), out
    assert calls[0][-2:] == ["--resume", "s-v"] and "- KEPT: <role>: C<n>:" in calls[0][2]
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "pass", out


def test_the_landing_loop_names_its_mend() -> None:
    """109 R14, 147: the landing's loop runs `land-mend` for each role `land-verdicts` names."""
    assert factory.landing.RUN_STEPS["mend"] == (
        ("agent", "{change}", "--task", "land-mend", "--role", "{role}"),
    )


def _move(root: Path, n: int) -> None:
    """The base branch moves on, touching nothing a change does: another session's landing."""
    (root / f"elsewhere-{n}.txt").write_text("moved on\n", encoding="utf-8")
    _git(root, "add", f"elsewhere-{n}.txt")
    _git(root, "commit", "-q", "-m", f"main moves on, {n}")


def _bound(root: Path, moves: int) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text(f"[land]\nmoves = {moves}\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"land.moves = {moves}")


def _pass_behaviour(folder: Path, n: int) -> None:
    (folder / "reviews" / f"land-{n}" / "behaviour.md").write_text(
        _verdict("behaviour"), encoding="utf-8"
    )


def _agents_sections(text: str) -> list[str]:
    """findings.md's sections a factory role raised, as written."""
    sections = ["## " + s for s in text.split("\n## ")[1:]]
    return [s for s in sections if any(f"\nBy: {r}" in s for r in factory.REVIEWERS)]


@needs_uv
def test_a_landing_writes_its_rounds_findings_into_its_commit(tmp_path, capsys) -> None:
    """127: `land --close` writes the landing rounds' findings into findings.md beside carry's,
    in the same shape, each `Class:` naming its landing round, before the record is amended in: a
    kept change `fixed`, a dropped one `wrong` with the verifier's why, a pre-existing problem
    `recorded`, each once, and one a build round raised too only once. A rerun (the base moved)
    changes none of the agents' sections, ship's own stays, and the commit has no
    `Sdlc-Findings`."""
    root = _gated(tmp_path)
    tree = _ready(root, "late", "late's one")
    folder = _folder(tree)
    old = "README.md:3: an old fault"
    (folder / "reviews" / "round-1" / "behaviour.md").write_text(
        _verdict("behaviour") + f"- PREEXISTING: {old}\n", encoding="utf-8"
    )
    assert _run(capsys, factory.cmd_carry, tree, "001")[1]["findings"] == 1
    ship = (
        "## F9. [important] [correctness] Ship's own\n\nEvidence: README.md:1\nClass: logic\n"
        "Disposition: fixed"
    )
    path = folder / "findings.md"
    path.write_text(path.read_text(encoding="utf-8").rstrip("\n") + "\n\n" + ship + "\n")
    _move(root, 1)
    out = _stack(root, tree, capsys, "person")
    assert (out["state"], out["round"]) == ("stacked", 1), out
    kept, dropped, pre = "README.md:1: says late", "README.md:2: two is wrong", "README.md:9: slow"
    land = folder / "reviews" / "land-1"
    (land / "behaviour.md").write_text(
        _verdict("behaviour", "CHANGES", (kept, dropped))
        + f"- PREEXISTING: {pre}\n- PREEXISTING: {old}\n",
        encoding="utf-8",
    )
    (land / "verified.md").write_text(
        f"- KEPT: behaviour: {kept}\n- DROPPED: behaviour: {dropped} — not in the code\n",
        encoding="utf-8",
    )

    _move(root, 2)
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert (code, out.get("state")) == (0, "moved"), out
    rel = f".sdlc/work/{tree.name}/findings.md"
    first = _git(tree, "show", f"HEAD:{rel}")
    assert _git(tree, "status", "--porcelain") == "", "the findings are in the commit"
    code, reading = _run(capsys, factory.landing.cmd_train, root)
    assert reading["next"] == "stack", reading
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", False, onto=reading["onto"])
    assert (code, out["state"], out["round"]) == (0, "stacked", 2), out
    _pass_behaviour(folder, 2)
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out

    landed = _git(root, "show", f"main~1:{rel}")
    # Kept in the last landing round, with none after it, it was never claimed fixed; once round
    # 2 passes, it is. Nothing else changes.
    before = [s.replace("Disposition: recorded", "Disposition: fixed") if kept in s else s
              for s in _agents_sections(first)]  # fmt: skip
    assert _agents_sections(landed) == before, "a rerun rewrites only what moved"
    assert (
        f"{kept}\n\nEvidence: README.md:1\nClass: behaviour review, landing round 1\n"
        "Disposition: recorded" in first
    )
    assert ship in landed, "ship's own section is kept as written"
    found = [
        (e["disposition"], e["class"], e["reason"])
        for e in sdlc._findings_from_text(landed)[0]
        if e["by"] == "behaviour"
    ]
    assert found == [
        ("recorded", "behaviour review, round 1", None),
        ("fixed", "behaviour review, landing round 1", None),
        ("wrong", "behaviour review, landing round 1", "not in the code"),
        ("recorded", "behaviour review, landing round 1", None),
    ], found
    for text in (kept, dropped, pre, old):
        assert landed.count(text.split(": ", 1)[1]) == 2, f"{text}: its heading and line, once"
    assert sdlc._findings_from_text(landed)[1] == [], "it reads as sdlc reads it"
    assert "Sdlc-Findings" not in _git(root, "log", "-1", "--format=%B", "main~1")


@needs_uv
def test_a_move_racing_close_reads_as_moved(tmp_path, capsys, monkeypatch) -> None:
    """R4: the base moves after the train's check and before close's merge, so close refuses. The
    landing reads the base's tip again and says `moved`, never matching close's words."""
    root = _repo(tmp_path)
    tree = _ready(root, "raced", "raced's one")
    reading = _stack(root, tree, capsys)
    assert reading["next"] == "close", reading
    real = factory._sdlc

    def racing(args: list[str], cwd: Path):
        if args[0] == "close":
            _move(root, 1)
            return 1, {"refusals": ["anything at all"], "done": []}, "anything at all"
        return real(args, cwd)

    monkeypatch.setattr(factory, "_sdlc", racing)
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert (code, out.get("state"), out.get("moves")) == (0, "moved", 1), out
    step = factory.read_land_step(
        _git(tree, "show", f"HEAD:.sdlc/work/{tree.name}/{factory.LAND_STEP.as_posix()}")
    )
    assert (step["step"], step["moves"]) == ("stack", 1), "back to its stack, the move counted"
    monkeypatch.setattr(factory, "_sdlc", real)
    assert _run(capsys, factory.landing.cmd_train, root)[1]["next"] == "stack", "onto the base anew"


def test_the_bound_on_following_main_is_the_base_branchs(tmp_path) -> None:
    """R5: `[land] moves` is read from the base branch's `factory.toml`: a change that sets its
    own gets the default, and a bad value is a warning and the default."""
    root = _repo(tmp_path)
    assert factory.load_config(root)[0]["land"]["moves"] == 3, "the default"
    _git(root, "checkout", "-q", "-b", "change")
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "factory.toml").write_text("[land]\nmoves = 10\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a change raises its own bound")
    assert factory.load_config(root)[0]["land"]["moves"] == 3, "never the change's own"
    _git(root, "checkout", "-q", "main")
    _bound(root, 0)
    cfg, warnings = factory.load_config(root)
    assert cfg["land"]["moves"] == 3 and any("land.moves" in w for w in warnings), warnings
    _bound(root, 2)
    assert factory.load_config(root)[0]["land"]["moves"] == 2


# ---------------------------------------------------------------- what no review read (104)


@needs_uv
def test_a_hand_edit_after_the_approver_is_a_signal_and_recorded(tmp_path, capsys) -> None:
    """R13, R14: a path that hashes otherwise than in the newest complete build round's snapshot
    was changed after its review. It is a signal, so `auto` is refused. The person's landing says
    so on its commit: `unreviewed=<n>` on `Sdlc-Landed`, and the paths in its body."""
    metrics = _load("metrics_for_landing", ROOT / "scripts" / "metrics.py")
    root = _repo(tmp_path)
    tree = _ready(root, "edited", "edited's one")
    folder = tree / ".sdlc" / "work" / tree.name
    cfg = factory.load_config(tree)[0]
    assert factory.landing.land_unreviewed(tree, folder, cfg) == [], "as its reviewers read it"
    (folder / "decision.md").write_text(
        (folder / "decision.md").read_text(encoding="utf-8") + "\nA note.\n", encoding="utf-8"
    )
    assert factory.landing.land_unreviewed(tree, folder, cfg) == [], (
        "the change's own folder never counts"
    )
    (tree / "README.md").write_text("edited's one, by hand\ntwo\nthree\n", encoding="utf-8")
    (tree / "added.txt").write_text("by hand\n", encoding="utf-8")
    assert factory.landing.land_unreviewed(tree, folder, cfg) == ["README.md", "added.txt"]
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    said = "changed since its last review: README.md, added.txt"
    assert said in batch["batch"][0]["signals"] and batch["clear"] is False, batch
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert code == 1 and said in out["refusals"][0], out
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    body = _git(tree, "log", "-1", "--format=%B")
    assert "Changed since its last review: README.md, added.txt\n" in body, body
    assert metrics.parse_trailers(body)["landed"] == {"by": "person", "unreviewed": 2}

    factory.snapshot_path(folder, 1).unlink()
    assert factory.landing.land_unreviewed(tree, folder, cfg) is None
    message = factory.landing.land_message(tree, folder, "person", False, unreviewed=None)
    assert message.rstrip().endswith("Sdlc-Landed: by=person unreviewed=unknown"), message
    assert "No snapshot of its last review." in message
    signals = factory.landing.land_signals(folder, tree, "READY", cfg, unreviewed=None)[0]
    assert "no snapshot of its last review" in signals


# ---------------------------------------------------------------- a fix asked at landing (104)

FIX_WORDS = "keep the second line as TWO"


def _asked(folder: Path, words: str = FIX_WORDS, ident: str = "R1", kind: str = "fix") -> str:
    """The person's words for a fix, as the land skill writes them: a ticked line at the end of
    the change's `decisions.md`, whose id, never the words, reaches the command line."""
    path = folder / "decisions.md"
    head = path.read_text(encoding="utf-8") if path.is_file() else "# Decisions\n\n"
    line = f"- [x] {ident} (person, {kind}): {words}\n"
    if line not in head:
        path.write_text(head + line, encoding="utf-8", newline="\n")
    return ident


def _builder_edits(tree: Path, captured: dict):
    """A stand-in for `claude -p`: the builder's session edits README.md and replies."""

    def fake(argv: list[str], cwd: Path):
        captured["argv"] = argv
        (tree / "README.md").write_text("fixed's one\nTWO\nthree\n", encoding="utf-8")
        return 0, ["Kept TWO.\n\n## Evidence\n$ true\nexit: 0\n"], None, None

    return fake


@needs_uv
def test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth(
    tmp_path, capsys, monkeypatch
) -> None:
    """R8–R11: the person's words open round `land-1` beside the builder's reports; the builder,
    resumed, gets them; the script amends its edits into the change's commit; the new `HEAD` is
    gated, then reviewed by every reviewer at the run's depth, before the close."""
    root = _gated(tmp_path)
    tree = _ready(root, "fixed", "fixed's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", _asked(folder), False)
    assert (code, out["round"]) == (0, 1), out
    assert FIX_WORDS in (folder / "build" / "land-1.ask.md").read_text(encoding="utf-8")
    assert list((folder / "reviews" / "land-1").iterdir()) == [], "never read as a review"

    (folder / "runs").mkdir(exist_ok=True)
    (folder / "runs" / "builder.sessions").write_text("a-builder-session\n", encoding="utf-8")
    captured: dict = {}
    monkeypatch.setattr(factory, "_claude", _builder_edits(tree, captured))
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-fix", None, None)
    assert (code, out["to"]) == (0, f".sdlc/work/{tree.name}/build/land-1.md"), out
    assert out["role"] == "builder", "149 R11: a fix stays the builder's, never the resolver's"
    argv = captured["argv"]
    prompt = argv[argv.index("-p") + 1]
    assert FIX_WORDS in prompt and "run no git command" in prompt and "## Evidence" in prompt
    assert argv[argv.index("--resume") + 1] == "a-builder-session", "the change's own builder"

    before = _git(tree, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", None, True)
    assert (code, out["fixed"]) == (0, ["README.md"]), out
    assert _git(tree, "rev-parse", "HEAD") != before and _git(tree, "status", "--porcelain") == ""
    assert _git(tree, "show", "HEAD:README.md").startswith("fixed's one\nTWO")
    assert "Sdlc-Landed: by=person" in _git(tree, "log", "-1", "--format=%B"), "one commit"
    assert _git(tree, "rev-list", "--count", "main..HEAD") == "1"

    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert out["next"] == "gate" and out["fixed"] is True, out
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert out["verdict"] == "PASS", out
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    roles = factory._rounds_at_depth(tree, folder, factory.load_config(tree)[0])[2]["reviewers"]
    assert out["next"] == "review" and out["missing"] == roles and len(roles) > 1, out
    review = factory._land_task(tree, folder, "land-review", "code")
    assert FIX_WORDS in review[0] and "the person asked for" in review[0], review
    for role in roles:
        (folder / "reviews" / "land-1" / f"{role}.md").write_text(_verdict(role), encoding="utf-8")
    assert _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")[1]["next"] == "pass"
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out
    assert (root / "README.md").read_text(encoding="utf-8").startswith("fixed's one\nTWO")


@needs_uv
def test_a_fix_commit_needs_an_ask(tmp_path, capsys, monkeypatch) -> None:
    """R8, R10: a fix is asked only of a shipped change whose landing round passed, no reviewer
    has answered yet (154), or none is open; `--commit` amends nothing in a round with no ask, or
    with nothing the builder edited. The builder's task refuses with no ask."""
    root = _repo(tmp_path)
    tree = _ready(root, "asked", "asked's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", _asked(folder), False)
    assert code == 1 and "isn't shipped" in out["refusals"][0], out
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    head = _git(tree, "rev-parse", "HEAD")
    (tree / "README.md").write_text("by hand\ntwo\nthree\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", None, True)
    assert code == 1 and "no fix was asked" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head, "nothing amended"
    _git(tree, "checkout", "--", "README.md")
    (folder / "reviews" / "land-1").mkdir(parents=True)
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-fix", None, None)
    assert code == 1 and "no fix was asked" in out["refusals"][0], out
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", None, True)
    assert code == 1 and "no fix was asked" in out["refusals"][0], "a round, but no ask"
    reply = folder / "reviews" / "land-1" / "behaviour.md"
    reply.write_text("VERDICT: CHANGES\n- CHANGE: README.md:1: say more\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", _asked(folder), False)
    assert code == 1 and "landing round 1 hasn't passed" in out["refusals"][0], out
    reply.unlink()
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", _asked(folder), False)
    assert (code, out["round"]) == (0, 1), "a round no reviewer has answered takes the fix (154)"
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", None, True)
    assert code == 1 and "changed nothing" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head, "nothing amended"


@needs_uv
def test_a_fix_asked_with_its_land_round_folder_gone_is_not_a_traceback(
    tmp_path, capsys, monkeypatch
) -> None:
    """171 R9 (nit 2026-11-18-80): a landing round counted with its `reviews/land-<n>/` folder
    gone by the time the ask reads it is one no reviewer has answered: the ask opens it, never a
    `FileNotFoundError`. `land_round()` counts only folders that exist, so it is stood in for."""
    root = _repo(tmp_path)
    tree = _ready(root, "gone", "gone's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    assert not (folder / "reviews" / "land-1").exists()
    monkeypatch.setattr(factory, "land_round", lambda folder: 1)
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", _asked(folder), False)
    assert (code, out["round"]) == (0, 1), out
    assert FIX_WORDS in (folder / "build" / "land-1.ask.md").read_text(encoding="utf-8")


@needs_uv
def test_a_fix_is_asked_by_its_line_in_decisions_md_never_on_a_command_line(
    tmp_path, capsys
) -> None:
    """R8: `--ask` takes the id of a ticked `(person, fix)` line in `decisions.md`, never the
    words, so a quote or `$(` in them never reaches a shell. An id with no such line, an unticked
    one, or another kind's, opens no round; the words reach the ask file byte for byte, and the
    ledger reads past the line."""
    root = _repo(tmp_path)
    tree = _ready(root, "quoted", "quoted's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    words = """keep "TWO" as it's written, and never run $(rm -rf ~) or `id`"""
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", "R1", False)
    assert code == 1 and "(person, fix)" in out["refusals"][0], "no decisions.md line"
    (folder / "decisions.md").write_text(
        f"# Decisions\n\n- [ ] R1 (person, fix): {words}\n", encoding="utf-8", newline="\n"
    )
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", "R1", False)
    assert code == 1 and "(person, fix)" in out["refusals"][0], "an unticked line"
    _asked(folder, words, "R2", kind="revise")
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", "R2", False)
    assert code == 1 and "(person, fix)" in out["refusals"][0], "another kind's line"
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", words, False)
    assert code == 1 and "(person, fix)" in out["refusals"][0], "words, not an id"
    assert not (folder / "reviews" / "land-1").exists(), "no round opened by a refusal"
    code, out = _run(
        capsys, factory.landing.cmd_land_fix, tree, "001", _asked(folder, words, "R3"), False
    )
    assert (code, out["round"]) == (0, 1), out
    assert factory.land_ask(folder, 1) == words
    assert factory.read_ledger(folder) == [], "the ledger reads past the person's lines"


@needs_uv
def test_a_fix_at_landing_is_never_landed_by_auto_later(tmp_path, capsys) -> None:
    """R12: a fix made while landing is a signal for the rest of the change's life: a later
    landing that passed itself is refused on it, at `land` and at `land --close`."""
    root = _repo(tmp_path)
    tree = _ready(root, "later", "later's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "committed"), out
    code, out = _run(capsys, factory.landing.cmd_land_fix, tree, "001", _asked(folder), False)
    assert code == 0, out
    said = "a fix was made while landing"
    assert (
        said in factory.landing.land_signals(folder, tree, "READY", factory.load_config(tree)[0])[0]
    )
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert code == 1 and said in out["refusals"][0], out
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert code == 1 and said in out["refusals"][0], out
    assert tree.exists() and _git(root, "log", "-1", "--format=%s", "main") == "init"


def test_a_conflict_marker_is_matched_only_as_a_whole_line() -> None:
    """108: both resolves refuse a file only for a marker git writes, a whole line. Each script's
    own source and a register quoting the run mid-line (bug 51's wording, and the check the
    scripts held) pass; a real marker of each kind is refused, and the factory's copy of the
    pattern is `sdlc.py`'s."""
    assert factory.CONFLICT_MARKER_RE.pattern == sdlc.CONFLICT_MARKER_RE.pattern
    run = "<" * 7
    quoted = f'## [2026-11-17-51] [bug] A resolve refuses "{run}"\n\nif "{run}" in text:\n'
    sources = [Path(sdlc.__file__), Path(factory.__file__)]
    sources += [Path(sdlc.__file__), Path(factory.__file__)]
    texts = [quoted, "a heading\n========\n", *(p.read_text(encoding="utf-8") for p in sources)]
    real = [f"{run} HEAD\nours\n", "ours\n=======\ntheirs\n", f"theirs\n{'>' * 7} abc1234\n"]
    for mod in (factory, sdlc):
        for text in texts:
            assert not mod.CONFLICT_MARKER_RE.search(text), (mod.__name__, text[:60])
        for text in real:
            assert mod.CONFLICT_MARKER_RE.search(text), (mod.__name__, text)


# ---------------------------------------------------------------- the landing's step record (133)


def _land_step(folder: Path) -> dict | None:
    path = folder / factory.LAND_STEP
    return factory.read_land_step(path.read_text(encoding="utf-8")) if path.is_file() else None


def _committed_step(tree: Path, folder: Path, rev: str = "HEAD") -> dict | None:
    rel = (folder / factory.LAND_STEP).relative_to(tree).as_posix()
    return factory.read_land_step(_git(tree, "show", f"{rev}:{rel}"))


@pytest.mark.portable
def test_every_landing_stop_has_a_plain_line_over_its_raw_text(tmp_path, capsys) -> None:
    """2026-11-18-20: a stop a tool's words caused is recorded with a plain line first, saying what
    failed and what to do, the raw text under it, and the output keeps the raw words. Each of
    `_amend_record()`'s whys has one, naming the way on and none of git's words; a stop at the
    landing's close the same; the bound on the base branch's moves names `/sdlc:close`, since the
    change is committed by then (`/sdlc:ship` only as what brings it up to date first)."""
    folder = tmp_path / ".sdlc" / "work" / "012-draft-land"
    (folder / "runs").mkdir(parents=True)
    why = "HEAD isn't the landing's commit, so its record has nothing to be amended into"
    plain = factory.landing._amend_plain(why, "012")
    code, out = _run(
        capsys, factory.landing._land_refused, tmp_path, folder, {"state": "x"}, why, plain
    )
    assert (code, out["state"], out["refusals"]) == (1, "refused", [why])
    stop = _land_step(folder)
    assert (stop["step"], stop["problems"]) == ("stop", [plain, why])
    code, out = _run(capsys, factory.landing._land_refused, tmp_path, folder, {}, why)
    assert out["refusals"] == [why] and _land_step(folder)["problems"] == [why], "no plain: as is"
    raws = (
        "git status couldn't be read",
        "uncommitted outside the change's folder: stray.txt, other.txt",
        why,
        "the landing's record couldn't be added to the commit",
        "something new",
    )
    for raw in raws:
        line = factory.landing._amend_plain(raw, "012")
        assert line and line != raw and "/sdlc" in line and "012" in line, (raw, line)
        assert "HEAD" not in line and "amend" not in line, line
    assert "stray.txt, other.txt" in factory.landing._amend_plain(raws[1], "012"), (
        "the paths, named"
    )
    code, out = _run(
        capsys, factory.landing._close_stopped, tmp_path, folder, "raw close words", "plain"
    )
    assert code == 1 and out["refusals"] == ["raw close words"]
    assert _land_step(folder)["problems"] == ["plain", "raw close words"]
    (folder / factory.LAND_MOVES).write_text("abc\n", encoding="utf-8")
    cfg = {"land": {"moves": 1}}
    bound = factory._record_move(tmp_path, folder, cfg)
    assert bound and "/sdlc:close 012" in bound and "ship it by hand" not in bound, bound


@needs_uv
def test_a_landing_records_each_step_it_takes(tmp_path, capsys, monkeypatch) -> None:
    """133: each landing command writes the step it runs to `runs/land-step.md` as it starts, its
    round, the moves so far and its place in the train beside it, and `land`'s and `close`'s own
    go into the change's commit, so the stack and `close` find the tree clean."""
    root = _gated(tmp_path)
    tree = _ready(root, "tracked", "tracked's one")
    folder = _folder(tree)
    _move(root, 1)
    assert _run(capsys, factory.landing.cmd_land, tree, "001", "auto")[1]["state"] == "committed"
    shipped = _committed_step(tree, folder)
    assert shipped["step"] == "ship" and shipped["since"], "the ship step, in the commit"
    assert _git(tree, "status", "--porcelain") == "", "the record left nothing uncommitted"
    out = _stack(root, tree, capsys)
    assert out["state"] == "stacked", out
    stack = _land_step(folder)
    assert (stack["step"], stack["train"]) == ("stack", {"k": 1, "n": 1}), stack
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert out["verdict"] == "PASS", out
    gate = _land_step(folder)
    assert (gate["step"], gate["round"], gate["moves"], gate["limit"]) == ("gate", 1, 0, 3)
    _replies(monkeypatch, _verdict("behaviour"), {"cost_usd": 0.1, "duration_ms": 60000})
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-review", "behaviour", None)
    assert code == 0, out
    assert _land_step(folder)["step"] == "review"
    # 174 R1: a landing task's row names its landing round, not a build round.
    row = json.loads((folder / "runs" / "costs.jsonl").read_text().splitlines()[-1])
    assert (row["task"], row["purpose"], row["land"]) == ("land-review", "land", 1), row
    assert "round" not in row
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001", True)
    assert out["next"] == "pass" and _land_step(folder)["step"] == "review", "pass writes nothing"

    _move(root, 2)
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert (code, out["state"]) == (0, "moved"), out
    moved = _committed_step(tree, folder)
    assert (moved["step"], moved["moves"]) == ("stack", 1), "back to its stack, the move counted"
    code, reading = _run(capsys, factory.landing.cmd_train, root)
    assert reading["next"] == "stack", reading
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", False, onto=reading["onto"])
    assert (code, out["state"], out["round"]) == (0, "stacked", 2), out
    again = _committed_step(tree, folder)
    assert (again["step"], again["round"], again["moves"]) == ("stack", 1, 1), again
    status = _git(tree, "status", "--porcelain").splitlines()
    assert sorted(line.split() for line in status) == [
        ["M", f".sdlc/work/{tree.name}/runs/land-step.md"],
        ["M", f".sdlc/work/{tree.name}/runs/land-times.jsonl"],
    ], "the stack's own step and the time of the one before it, for the close to amend in"
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    _pass_behaviour(folder, 2)
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out
    rel = f".sdlc/work/{tree.name}/{factory.LAND_STEP.as_posix()}"
    landed = factory.read_land_step(_git(root, "show", f"main~1:{rel}"))
    assert (landed["step"], landed["round"]) == ("close", 2), landed


@needs_uv
def test_a_resolving_landing_records_the_builder_in_the_rebased_commit(
    tmp_path, capsys, monkeypatch
) -> None:
    """133: the builder's resolve is recorded mid-rebase and goes into the rebased commit with its
    costs line, so `--continue` finds nothing unstaged; the gate records itself next."""
    root, tree = _resolving(tmp_path, capsys, ("A nit no change names", "A nit nobody names"))
    folder = _folder(tree)
    (folder / "runs").mkdir(exist_ok=True)
    (folder / "runs" / "builder.sessions").write_text("s-1\n", encoding="utf-8")
    _replies(monkeypatch, "Resolved.\n\n## Evidence\n\n$ true\nexit: 0\n")
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "resolve", None, None)
    assert code == 0, out
    assert _land_step(folder)["step"] == "resolve"
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert _committed_step(tree, folder)["step"] == "resolve", "staged with the resolution"


@needs_uv
def test_a_stopped_landing_records_why(tmp_path, capsys) -> None:
    """133: `land-verdicts --record` writes a stop with its problems and the step it stopped
    after; without `--record` it writes nothing. A refused close records its refusal."""
    root = _gated(tmp_path)
    (root / ".sdlc" / "config.toml").write_text(
        '[commands]\ncheck = "test ! -f broken.txt"\n', encoding="utf-8"
    )
    _git(root, "commit", "-q", "-am", "a gate that can fail")
    tree = _ready(root, "stops", "stops' one")
    folder = _folder(tree)
    _move(root, 1)
    assert _stack(root, tree, capsys)["state"] == "stacked"
    (tree / "broken.txt").write_text("", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert out["verdict"] == "FAIL", out
    before = (folder / factory.LAND_STEP).read_text(encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001")
    assert (
        out["next"] == "stop" and (folder / factory.LAND_STEP).read_text(encoding="utf-8") == before
    ), "a reading alone writes nothing"
    code, out = _run(capsys, factory.landing.cmd_land_verdicts, tree, "001", True)
    stop = _land_step(folder)
    assert (stop["step"], stop["after"], stop["round"]) == ("stop", "gate", 1), stop
    assert stop["problems"] == out["problems"] and "ship it by hand" in stop["problems"][0]


@pytest.mark.portable
def test_the_landing_step_record_reads_back_what_it_writes() -> None:
    out = {"step": "review", "round": 2, "moves": 1, "limit": 3}
    text = factory.land_step_text(out, "2026-11-18T10:00:00Z")
    assert factory.read_land_step(text) == {
        "step": "review", "round": 2, "moves": 1, "limit": 3,
        "since": "2026-11-18T10:00:00Z", "after": None, "problems": [], "train": None,
        "waits": None,
    }  # fmt: skip
    stop = {"step": "stop", "round": None, "moves": 0, "limit": 3}
    text = factory.land_step_text(stop, "2026-11-18T10:00:00Z", "ship", ["it broke\nbadly"])
    read = factory.read_land_step(text)
    assert (read["round"], read["after"], read["problems"]) == (None, "ship", ["it broke badly"])
    assert factory.read_land_step("STEP: review\n") is not None
    assert factory.read_land_step("landing, probably\n") is None


@needs_uv
def test_a_landing_stopped_by_a_tool_records_plain_words(tmp_path, capsys) -> None:
    """133 round 1: the record a person reads on the board says what failed and how to see why;
    the tool's own words stay in the landing's output, and (141) under the plain line in the
    record."""
    root = _repo(tmp_path)
    tree = _ready(root, "hooked", "hooked's one")
    _hook(root, "hook says no")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert code == 1 and "hook says no" in out["refusals"][0], out
    stop = _land_step(_folder(tree))
    assert (stop["step"], stop["after"]) == ("stop", "ship"), stop
    assert stop["problems"][0] == (
        "its commit failed: the landing's output gives git's words; rerun it once fixed"
    )
    assert len(stop["problems"]) == 2 and "hook says no" in stop["problems"][1], stop


# ---------------------------------------------------------------- the register never rides (134)


def _landed_holding(tmp_path: Path, capsys) -> tuple[Path, Path]:
    """A change landed by the person over a committed register: a carried seed, a filed bug, a
    nit its review raised and a nit its intent takes in, all held in its `entries.md`."""
    root = _repo(tmp_path)
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(REGISTER, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a register")
    tree = _ready(root, "noted", "noted's one")
    folder = _folder(tree)
    (folder / "notes.md").write_text(f"# Notes\n\n- [ ] {PRE}\n- [ ] Page the list\n")
    (folder / "decision.md").write_text(
        "DECISION: READY\n\nFine.\n\n- IMPACT: minor — a test change\n" + BUG
    )
    _nit(folder, "code", TERSE)
    intent = folder / "intent.md"
    intent.write_text(intent.read_text(encoding="utf-8") + "\nTakes in nit 2026-11-17-11.\n")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "committed"), out
    return root, tree


@needs_uv
def test_a_landing_leaves_the_register_as_the_base_has_it(tmp_path, capsys) -> None:
    """134 R1: the landing's commit names no register path."""
    root, tree = _landed_holding(tmp_path, capsys)
    assert ".sdlc/work/inbox.md" not in _git(tree, "show", "--name-only", "--format=").splitlines()
    assert _git(tree, "show", "HEAD:.sdlc/work/inbox.md") == REGISTER.rstrip("\n")
    assert _git(tree, "status", "--porcelain") == ""


@needs_uv
def test_a_landing_holds_its_carried_seeds_bugs_and_nits(tmp_path, capsys) -> None:
    """134 R2: every entry the yes filed is in the change's `entries.md`, whole, and committed;
    none in the branch's register."""
    root, tree = _landed_holding(tmp_path, capsys)
    held = _git(tree, "show", f"HEAD:.sdlc/work/{tree.name}/entries.md")
    tags = [e["status"] for e in sdlc.parse_entries(held)]
    assert sorted(tags) == ["bug", "idea", "nit"], held
    register = _git(tree, "show", "HEAD:.sdlc/work/inbox.md")
    for e in sdlc.parse_entries(held):
        assert e["id"] not in register and e["title"] not in register


@needs_uv
def test_the_entries_factory_holds_are_the_ones_close_files(tmp_path, capsys) -> None:
    """134 R13: `sdlc.py` reads what `_dispose()` and `retire_nits()` wrote, with its own parsing,
    which the factory's copies match; and close files every entry and retires the nit."""
    assert factory.landing.ENTRIES == sdlc.ENTRIES
    assert factory.landing.RETIRE_RE.pattern == sdlc.RETIRE_LINE_RE.pattern
    root, tree = _landed_holding(tmp_path, capsys)
    folder = _folder(tree)
    held = sdlc.held_entries((folder / factory.landing.ENTRIES).read_text(encoding="utf-8"))
    assert held["problems"] == [], held
    assert (
        [i for i, _ in held["retire"]] == factory.landing.retired_ids(folder) == ["2026-11-17-11"]
    )
    ids = held["ids"]
    assert len(ids) == 3
    code, out = _run(capsys, factory.landing.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out
    assert out["register"]["file"] == ids and "2026-11-17-11" in out["register"]["retire"], out
    register = (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    assert [e["id"] for e in sdlc.parse_entries(register)][-3:] == ids
    assert "2026-11-17-11" not in register
    said = " ".join(sdlc.nit_entries(root)[1] + sdlc.bug_entries(root)[1])
    assert not any(i in said for i in ids), "each filed entry reads clean"


@needs_uv
def test_two_factory_landings_never_conflict_on_the_register(tmp_path, capsys) -> None:
    """134 R5, the factory's way: two changes from one base, each taking a seed and carrying one
    forward, landed one after the other (two trains) with an idea filed between. The second's
    stack meets no register conflict, and every entry is there once."""
    root = _repo(tmp_path)
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(OWN, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a register")
    trees = []
    for slug, seed in (("first", "2026-11-17-6"), ("second", "2026-11-17-7")):
        tree = _ready(root, slug, f"{slug}'s one")
        if slug == "second":
            (tree / "README.md").write_text("one\ntwo\nsecond's three\n", encoding="utf-8")
        folder = _folder(tree)
        intent = folder / "intent.md"
        intent.write_text(intent.read_text("utf-8").replace("idea:", f"idea: {seed}", 1))
        (folder / "notes.md").write_text(f"# Notes\n\n- [ ] Carry {slug}'s rest\n")
        trees.append(tree)
    for n, tree in enumerate(trees, 1):
        drive_train(factory, root, capsys, [tree], "person", strict=True)
        if n == 1:
            register = root / ".sdlc" / "work" / "inbox.md"
            register.write_text(
                register.read_text("utf-8") + "\n## [2026-11-18-9] [idea] Filed between\n\nx\n"
            )
            assert sdlc.cmd_inbox_commit(root) == 0
            capsys.readouterr()
    entries = sdlc.inbox_entries(root)
    titles = [e["title"] for e in entries]
    for title in ("Carry first's rest", "Carry second's rest", "Filed between"):
        assert titles.count(title) == 1, titles
    assert "The change's own seed" not in titles and "A bug the change fixes" not in titles
    assert len({e["id"] for e in entries}) == len(entries), "no id twice"


# ---------------------------------------------------------------- escalations that clear (145)


@needs_uv
def test_land_check_shows_how_each_reason_was_cleared(tmp_path, capsys) -> None:
    """145 R13, R10: a cleared escalation still signals `the approver escalated`, so the gate
    never passes itself, and the question shows each reason with how it cleared; nothing the
    landing reads rewrites `decision.md`."""
    root = _repo(tmp_path)
    _config(root, '[commands]\ncheck = "true"\n')
    tree = _ready(root, "esc", "esc's one")
    folder = _folder(tree)
    (folder / "runs").mkdir(exist_ok=True)
    (folder / "decision.md").write_text(
        "DECISION: ESCALATE\n\nThree things.\n\n- IMPACT: minor — a test change\n"
        "- ESCALATED: gate: the gate was red on round 1\n"
        "- ESCALATED: look: the page reads oddly\n",
        encoding="utf-8",
    )
    (folder / "decisions.md").write_text(
        "# Decisions\n\n- [x] D1 (builder round 1, blocking): Keep drafts? → decided: 30 days\n",
        encoding="utf-8",
    )
    shown = (folder / "decision.md").read_bytes()
    _run(capsys, factory.cmd_decisions, tree, tree.name[:3])
    _run(capsys, factory.cmd_ask, tree, tree.name[:3], None)
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    [entry] = batch["batch"]
    assert entry["escalations"] == ["D1: decided: 30 days", "D2: not cleared", "gate: not cleared"]
    ledger = folder / "decisions.md"
    text = ledger.read_text(encoding="utf-8").replace("- [ ] D2", "- [x] D2")
    ledger.write_text(text.replace("oddly\n", "oddly → decided: seen\n"), encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "built")
    assert sdlc.cmd_gate(tree, tree.name[:3]) == 0
    capsys.readouterr()
    code, batch = _run(capsys, factory.landing.cmd_land_check, root, [])
    [entry] = batch["batch"]
    assert entry["escalations"] == [
        "D1: decided: 30 days",
        "D2: acknowledged: seen",
        "gate: green on the build as it stands (attempt 1)",
    ]
    assert batch["clear"] is False and "the approver escalated" in entry["signals"]
    assert "  Escalated:\n  - D1: decided: 30 days\n  - D2: acknowledged: seen\n" in batch["shown"]
    assert (folder / "decision.md").read_bytes() == shown


def test_each_landing_step_change_writes_a_times_row(tmp_path, monkeypatch) -> None:
    """145 R19: a step that replaces another adds the one it replaces to `runs/land-times.jsonl`,
    its round and its seconds since its `SINCE:`; the same step and round again adds nothing."""
    root = _repo(tmp_path)
    folder = root / ".sdlc" / "work" / "001-timed"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text("---\nid: 001\nstage: test\n---\n", encoding="utf-8")
    clock = iter(["2026-11-18T10:00:00Z", "2026-11-18T10:00:30Z", "2026-11-18T10:00:30Z",
                  "2026-11-18T10:02:00Z"])  # fmt: skip
    monkeypatch.setattr(factory, "_utc_now", lambda: next(clock))
    factory._record_land(root, folder, "checks")
    factory._record_land(root, folder, "ship")
    factory._record_land(root, folder, "ship")
    factory._record_land(root, folder, "gate")
    raw = (folder / factory.LAND_TIMES).read_bytes()
    assert b"\r" not in raw
    rows = factory.read_land_times(raw.decode("utf-8"))
    assert rows == [
        {"step": "checks", "round": None, "seconds": 30.0},
        {"step": "ship", "round": None, "seconds": 90.0},
    ], rows
    # 162 R9: each row says when its step began, for close's lead time; the readers above pass
    # over the key, so the board's figures don't move.
    raw_rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    assert [r["since"] for r in raw_rows] == ["2026-11-18T10:00:00Z", "2026-11-18T10:00:30Z"]


@needs_uv
def test_nothing_rewrites_decision_md(tmp_path, capsys) -> None:
    """145 R10: on an escalated change, `decisions`, `ask`, `sdlc.py gate`, `land-check` and the
    board's state each leave `decision.md` byte for byte as the approver wrote it."""
    root = _repo(tmp_path)
    _config(root, '[commands]\ncheck = "true"\n')
    tree = _ready(root, "kept", "kept's one")
    folder = _folder(tree)
    (folder / "runs").mkdir(exist_ok=True)
    (folder / "decision.md").write_text(
        "DECISION: ESCALATE\n\nTwo things.\n\n- IMPACT: minor — a test change\n"
        "- ESCALATED: gate: the gate was red on round 1\n"
        "- ESCALATED: look: the page reads oddly\n",
        encoding="utf-8",
    )
    shown = (folder / "decision.md").read_bytes()
    ident = tree.name[:3]
    steps = [
        ("decisions", lambda: factory.cmd_decisions(tree, ident)),
        ("ask", lambda: factory.cmd_ask(tree, ident, None)),
        ("sdlc.py gate", lambda: sdlc.cmd_gate(tree, ident)),
        ("land-check", lambda: factory.landing.cmd_land_check(root, [])),
        ("the board's state", lambda: sdlc._load_board().state(root)),
    ]
    for name, step in steps:
        step()
        capsys.readouterr()
        assert (folder / "decision.md").read_bytes() == shown, name
    card = {c["change"]: c for c in sdlc._load_board().state(root)["changes"]}[tree.name]
    assert card["decision"] == "ESCALATE" and "acknowledge D1" in card["needs"], card
