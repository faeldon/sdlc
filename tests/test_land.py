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
sdlc = _load("sdlc_for_landing", ROOT / "scripts" / "sdlc.py")

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
    message = factory.land_message(tmp_path, folder, "person", True)
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


CHECKS = "# Checks\n\n> Acceptance checks.\n\n## It runs\n\n```sh\ntrue\n```\n"


def _folder(tree: Path) -> Path:
    return tree / ".sdlc" / "work" / tree.name


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
    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    assert batch["excluded"] == [] and [c["change"] for c in batch["batch"]] == [tree.name]
    assert batch["clear"] is False
    signals = " | ".join(batch["batch"][0]["signals"])
    for said in ("acceptance checks to run: 1", "undone notes to dispose of: 1",
                 "assumed decisions to confirm: D1"):  # fmt: skip
        assert said in signals, signals
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
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
    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    by = {c["change"]: c for c in batch["batch"]}
    assert by[full.name]["checks"] == [{"name": "It runs", "command": "true"}]
    assert by[full.name]["cases"] == {"scope": ["ship-basic"], "cap_usd": 5}
    assert by[full.name]["undone"] == [
        {"line": 3, "text": "Page the list", "seed": "Page the list"},
        {"line": 5, "text": "Rename the flag", "dropped": "the flag went away in round 2"},
    ]
    assert by[full.name]["assumed"] == [{"id": "D1", "text": "Page at 50? Going with 50."}]
    assert by[full.name]["recover"] == ["deploy/: fix forward: a release without deploy/run.sh"]
    assert "skills' cases in scope: 1" in by[full.name]["signals"]
    # The stand-in gives every change a scope; the plain one's other parts are empty.
    assert [by[plain.name][k] for k in ("checks", "undone", "assumed", "recover")] == [[]] * 4
    assert "(at most $10)" in batch["question"], "two changes with cases, $5 each"


def _entry(name: str, **parts) -> dict:
    empty = {"checks": [], "cases": {}, "undone": [], "assumed": [], "recover": []}
    return {"change": name, **empty, **parts}


def test_the_landing_question_names_only_what_the_batch_holds() -> None:
    """103 R3: the script words the question, a clause for each thing some change holds."""
    plain = factory.land_question([_entry("001-a"), _entry("002-b")], "main")
    assert plain == (
        "Land 2 changes in this order, 001-a, 002-b, each shipped with its approver's impact, "
        "committed, brought up to date with main as often as it moves while landing, up to 3 "
        "times (a conflict resolved by its builder and reviewed again), and closed, pushed as "
        "git.push says? (yes / yes, with a fix / leave one out / no)"
    )
    moving = factory.land_question([_entry("001-a")], "main", 5)
    assert "as often as it moves while landing, up to 5 times" in moving, "the base's land.moves"
    check = {"name": "x", "command": "true"}
    cases = {"scope": ["ship-basic"], "cap_usd": 5}
    full = factory.land_question(
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
        "committed, brought up to date with trunk as often as it moves while landing, up to 3 "
        "times (a conflict resolved by its builder and reviewed again), and closed, pushed as "
        "git.push says? (yes / yes, with a fix / leave one out / no)"
    )
    only = factory.land_question([_entry("001-a", checks=[check])], "main")
    assert "its acceptance checks run as shown, committed" in only and "$" not in only
    assert only.startswith("Land 1 change in this order, 001-a,")
    cases_only = factory.land_question([_entry("001-a", cases=cases)], "main")
    assert "its skills' cases run as shown (at most $5)," in cases_only
    notes = factory.land_question([_entry("001-a", undone=[{"line": 1, "text": "t", "seed": "t"}])],
                                  "main")  # fmt: skip
    assert "its undone notes carried or dropped as shown," in notes and "assumed" not in notes
    decided = factory.land_question([_entry("001-a", assumed=[{"id": "D1", "text": "t"}])], "main")
    assert "its assumed decisions confirmed as shown," in decided and "undone" not in decided
    assert "recover" not in decided


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
    assert factory._accept_state(tree, folder) == "FAIL"
    (tree / "README.md").write_text("changed again\n", encoding="utf-8")
    assert factory._accept_state(tree, folder) is None, "a new build needs a new run"


@needs_uv
def test_factory_cases_writes_the_note_ship_reads_or_stops(tmp_path, capsys, monkeypatch) -> None:
    """103 R5: `factory.py cases` runs `sdlc.py run-cases` for one change; a pass or a skip writes
    the `Skill evals:` line ship reads, once, and a failed case writes nothing."""
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
                               "passed": True})  # fmt: skip
    code, out = _run(capsys, factory.cmd_cases, tree, "001")
    assert code == 0 and calls == [["run-cases", tree.name]]
    findings = folder / "findings.md"
    assert findings.read_text(encoding="utf-8") == "# Findings\n\nSkill evals: ran, 2 of 2\n"
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

    reply.update(code=1, data={"run": "r", "cases": rows, "failed": ["ship-risky"],
                               "passed": False})  # fmt: skip
    code, out = _run(capsys, factory.cmd_cases, tree, "001")
    assert code == 1 and out["failed"] == ["ship-risky"]
    assert findings.read_text(encoding="utf-8") == text, "a failed case writes no note"


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
        code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
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
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "current"), out
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
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert code == 1 and "sdlc.py ship refused" in out["refusals"][0], out

    def written() -> tuple[str, str, list[dict]]:
        notes = (folder / "notes.md").read_text(encoding="utf-8")
        decisions = (folder / "decisions.md").read_text(encoding="utf-8")
        return notes, decisions, sdlc.inbox_entries(tree)

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
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "current"), out
    assert written() == (notes, decisions, entries), "the rerun wrote nothing twice"
    body = _git(tree, "log", "-1", "--format=%B")
    assert f"Carried forward:\n- Page the list → {seed}\n" in body
    assert "Dropped:\n- Rename the flag: the flag went away in round 2\n" in body
    assert ".sdlc/work/inbox.md" in _git(tree, "show", "--name-only", "--format="), "committed"


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
    assert factory.land_parts(folder, pre)["undone"] == [
        {"line": 3, "text": "Page the list", "seed": "Page the list"}
    ], "nothing proposed: carried as a seed titled by itself"

    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    assert batch["batch"] == [] and "no How to recover for deploy/run.sh" in " ".join(
        batch["excluded"][0]["excluded"]
    )
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert code == 1 and out["refusals"][0].startswith("ship it by hand"), out
    assert _git(tree, "log", "-1", "--format=%s") == "config", "nothing committed"


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

    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "rebased"), out
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert out["next"] == "gate", out
    assert _run(capsys, factory.cmd_gate, tree, "001", True)[0] == 0
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert out["next"] == "accept" and out["missing"] == ["behaviour"], out
    assert _run(capsys, factory.cmd_accept, tree, "001")[0] == 0
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert out["next"] == "review", out

    (tree / "broken.txt").write_text("", encoding="utf-8")
    assert _run(capsys, factory.cmd_accept, tree, "001")[0] == 1
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert out["next"] == "stop" and "build/land-accept.md" in out["problems"][0], out


def _review_passes(capsys, tree: Path) -> None:
    """A rebased change's landing round, run as the agents would reply: its behaviour check
    passes, and `land-verdicts` says `pass`."""
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, tree.name.split("-")[0])
    if out["next"] == "pass":
        return
    assert out["next"] == "review", out
    for role in out["missing"]:
        (_folder(tree) / "reviews" / f"land-{out['round']}" / f"{role}.md").write_text(
            "VERDICT: PASS\n\n## Evidence\n$ true\nexit: 0\n", encoding="utf-8"
        )
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, tree.name.split("-")[0])
    assert out["next"] == "pass", out


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

    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    assert [c["change"] for c in batch["batch"]] == [checked.name, noted.name, deployed.name]
    assert batch["excluded"] == [] and batch["clear"] is False
    question = batch["question"]
    for clause in ("its acceptance checks run as shown", "undone notes carried or dropped",
                   "with how to recover shown"):  # fmt: skip
        assert clause in question, question

    # The person's yes; then each change in order, as the skill's Step 3 runs it.
    assert _run(capsys, factory.cmd_accept, checked, "001")[0] == 0
    for tree in (checked, noted, deployed):
        num = tree.name.split("-")[0]
        code, out = _run(capsys, factory.cmd_land, tree, num, "person")
        if out["state"] == "conflict":
            # Each change numbered locally conflicts on `.sdlc/last-id` alone, once the one
            # before it has landed: it settles itself, and the rebase goes on with nothing for
            # the builder.
            code, out = _run(capsys, factory.cmd_resolve, tree, num, False)
            assert (code, out["conflicted"], out["state"]) == (0, [], "clean"), out
            assert not _git(tree, "status", "--porcelain", "--untracked-files=no"), "rebased"
        assert code == 0 and out["state"] in ("current", "rebased", "clean"), out
        if out["state"] != "current":
            _review_passes(capsys, tree)
        code, out = _run(capsys, factory.cmd_land_close, tree, num)
        assert code == 0 and "merge" in out["done"], out

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


@needs_uv
def test_main_moving_before_close_sends_the_landing_back_to_its_rebase(tmp_path, capsys) -> None:
    """R1–R3: the base branch moves between a passing landing review and the close. `land --close`
    runs no close: it amends the record in, round 1's review and `runs/land-moves` with it, and
    says `moved`. `land` again rebases into round 2, which is gated and reviewed before the close
    merges."""
    root = _gated(tmp_path)
    tree = _ready(root, "follow", "follow's one")
    folder = tree / ".sdlc" / "work" / tree.name
    _move(root, 1)
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["round"]) == (0, "rebased", 1), out
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert out["verdict"] == "PASS", out
    _pass_behaviour(folder, 1)
    assert _run(capsys, factory.cmd_land_verdicts, tree, "001")[1]["next"] == "pass"

    _move(root, 2)
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert (code, out.get("state"), out.get("moves")) == (0, "moved", 1), out
    assert tree.exists() and _git(root, "log", "-1", "--format=%s", "main") == "main moves on, 2"
    committed = _git(tree, "show", "--name-only", "--format=", "HEAD").splitlines()
    rel = f".sdlc/work/{tree.name}"
    assert (
        f"{rel}/reviews/land-1/behaviour.md" in committed and f"{rel}/runs/land-moves" in committed
    )
    assert _git(tree, "status", "--porcelain") == "", "the record is in the commit"

    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["round"]) == (0, "rebased", 2), out
    assert _run(capsys, factory.cmd_land_verdicts, tree, "001")[1]["next"] == "gate"
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert out["verdict"] == "PASS", out
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert (out["next"], out["missing"]) == ("review", ["behaviour"]), out
    _pass_behaviour(folder, 2)
    assert _run(capsys, factory.cmd_land_verdicts, tree, "001")[1]["next"] == "pass"
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out
    assert _git(root, "log", "-1", "--format=%s", "main") == f"Close {tree.name}"
    assert "Sdlc-Landed: by=auto" in _git(root, "log", "-1", "--format=%B", "main~1")


@needs_uv
def test_a_move_racing_close_reads_as_moved(tmp_path, capsys, monkeypatch) -> None:
    """R4: the base moves after the check and before close's merge, so close refuses. The landing
    counts the base again and says `moved`, never matching close's words."""
    root = _repo(tmp_path)
    tree = _ready(root, "raced", "raced's one")
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "current"), out
    real = factory._sdlc

    def racing(args: list[str], cwd: Path):
        if args[0] == "close":
            _move(root, 1)
            return 1, {"refusals": ["anything at all"], "done": []}, "anything at all"
        return real(args, cwd)

    monkeypatch.setattr(factory, "_sdlc", racing)
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert (code, out.get("state"), out.get("moves")) == (0, "moved", 1), out
    rel = f".sdlc/work/{tree.name}/runs/land-moves"
    assert rel in _git(tree, "show", "--name-only", "--format=", "HEAD").splitlines()


@needs_uv
def test_a_landing_stops_after_land_moves_moves(tmp_path, capsys) -> None:
    """R5: with `moves = 1` on the base branch, the first move is followed and the second is a
    refusal that names the bound, with nothing closed."""
    root = _repo(tmp_path)
    _bound(root, 1)
    tree = _ready(root, "bounded", "bounded's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "current"), out
    _move(root, 1)
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert (code, out.get("state")) == (0, "moved"), out
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["round"]) == (0, "rebased", 1), out
    _pass_behaviour(folder, 1)
    _move(root, 2)
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert code == 1 and f"main moved 1 times while {tree.name} landed" in out["refusals"][0], out
    assert tree.exists() and _git(root, "log", "-1", "--format=%s", "main") == "main moves on, 2"


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
    assert factory.land_unreviewed(tree, folder, cfg) == [], "as its reviewers read it"
    (folder / "decision.md").write_text(
        (folder / "decision.md").read_text(encoding="utf-8") + "\nA note.\n", encoding="utf-8"
    )
    assert factory.land_unreviewed(tree, folder, cfg) == [], "the change's own folder never counts"
    (tree / "README.md").write_text("edited's one, by hand\ntwo\nthree\n", encoding="utf-8")
    (tree / "added.txt").write_text("by hand\n", encoding="utf-8")
    assert factory.land_unreviewed(tree, folder, cfg) == ["README.md", "added.txt"]
    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    said = "changed since its last review: README.md, added.txt"
    assert said in batch["batch"][0]["signals"] and batch["clear"] is False, batch
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert code == 1 and said in out["refusals"][0], out
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "current"), out
    body = _git(tree, "log", "-1", "--format=%B")
    assert "Changed since its last review: README.md, added.txt\n" in body, body
    assert metrics.parse_trailers(body)["landed"] == {"by": "person", "unreviewed": 2}

    factory.snapshot_path(folder, 1).unlink()
    assert factory.land_unreviewed(tree, folder, cfg) is None
    message = factory.land_message(tree, folder, "person", False, unreviewed=None)
    assert message.rstrip().endswith("Sdlc-Landed: by=person unreviewed=unknown"), message
    assert "No snapshot of its last review." in message
    signals = factory.land_signals(folder, tree, "READY", cfg, unreviewed=None)[0]
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
        return 0, "Kept TWO.\n\n## Evidence\n$ true\nexit: 0\n", None, None

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
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "current"), out
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", _asked(folder), False)
    assert (code, out["round"]) == (0, 1), out
    assert FIX_WORDS in (folder / "build" / "land-1.ask.md").read_text(encoding="utf-8")
    assert list((folder / "reviews" / "land-1").iterdir()) == [], "never read as a review"

    (folder / "runs").mkdir(exist_ok=True)
    (folder / "runs" / "builder.sessions").write_text("a-builder-session\n", encoding="utf-8")
    captured: dict = {}
    monkeypatch.setattr(factory, "_claude", _builder_edits(tree, captured))
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-fix", None, None)
    assert (code, out["to"]) == (0, f".sdlc/work/{tree.name}/build/land-1.md"), out
    argv = captured["argv"]
    prompt = argv[argv.index("-p") + 1]
    assert FIX_WORDS in prompt and "run no git command" in prompt and "## Evidence" in prompt
    assert argv[argv.index("--resume") + 1] == "a-builder-session", "the change's own builder"

    before = _git(tree, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", None, True)
    assert (code, out["fixed"]) == (0, ["README.md"]), out
    assert _git(tree, "rev-parse", "HEAD") != before and _git(tree, "status", "--porcelain") == ""
    assert _git(tree, "show", "HEAD:README.md").startswith("fixed's one\nTWO")
    assert "Sdlc-Landed: by=person" in _git(tree, "log", "-1", "--format=%B"), "one commit"
    assert _git(tree, "rev-list", "--count", "main..HEAD") == "1"

    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert out["next"] == "gate" and out["fixed"] is True, out
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert out["verdict"] == "PASS", out
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    roles = factory._rounds_at_depth(tree, folder, factory.load_config(tree)[0])[2]["reviewers"]
    assert out["next"] == "review" and out["missing"] == roles and len(roles) > 1, out
    review = factory._land_task(tree, folder, "land-review", "code")
    assert FIX_WORDS in review[0] and "the person asked for" in review[0], review
    for role in roles:
        (folder / "reviews" / "land-1" / f"{role}.md").write_text(_verdict(role), encoding="utf-8")
    assert _run(capsys, factory.cmd_land_verdicts, tree, "001")[1]["next"] == "pass"
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert code == 0 and "merge" in out["done"], out
    assert (root / "README.md").read_text(encoding="utf-8").startswith("fixed's one\nTWO")


@needs_uv
def test_a_fix_commit_needs_an_ask(tmp_path, capsys, monkeypatch) -> None:
    """R8, R10: a fix is asked only of a shipped change whose landing round passed or none is
    open; `--commit` amends nothing in a round with no ask, or with nothing the builder edited.
    The builder's task refuses with no ask."""
    root = _repo(tmp_path)
    tree = _ready(root, "asked", "asked's one")
    folder = tree / ".sdlc" / "work" / tree.name
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", _asked(folder), False)
    assert code == 1 and "isn't shipped" in out["refusals"][0], out
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "current"), out
    head = _git(tree, "rev-parse", "HEAD")
    (tree / "README.md").write_text("by hand\ntwo\nthree\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", None, True)
    assert code == 1 and "no fix was asked" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head, "nothing amended"
    _git(tree, "checkout", "--", "README.md")
    (folder / "reviews" / "land-1").mkdir(parents=True)
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-fix", None, None)
    assert code == 1 and "no fix was asked" in out["refusals"][0], out
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", None, True)
    assert code == 1 and "no fix was asked" in out["refusals"][0], "a round, but no ask"
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", _asked(folder), False)
    assert code == 1 and "landing round 1 hasn't passed" in out["refusals"][0], out
    (folder / "reviews" / "land-1").rmdir()
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", _asked(folder), False)
    assert (code, out["round"]) == (0, 1), out
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", None, True)
    assert code == 1 and "changed nothing" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head, "nothing amended"


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
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "current"), out
    words = """keep "TWO" as it's written, and never run $(rm -rf ~) or `id`"""
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", "R1", False)
    assert code == 1 and "(person, fix)" in out["refusals"][0], "no decisions.md line"
    (folder / "decisions.md").write_text(
        f"# Decisions\n\n- [ ] R1 (person, fix): {words}\n", encoding="utf-8", newline="\n"
    )
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", "R1", False)
    assert code == 1 and "(person, fix)" in out["refusals"][0], "an unticked line"
    _asked(folder, words, "R2", kind="revise")
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", "R2", False)
    assert code == 1 and "(person, fix)" in out["refusals"][0], "another kind's line"
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", words, False)
    assert code == 1 and "(person, fix)" in out["refusals"][0], "words, not an id"
    assert not (folder / "reviews" / "land-1").exists(), "no round opened by a refusal"
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", _asked(folder, words, "R3"), False)
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
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "current"), out
    code, out = _run(capsys, factory.cmd_land_fix, tree, "001", _asked(folder), False)
    assert code == 0, out
    said = "a fix was made while landing"
    assert said in factory.land_signals(folder, tree, "READY", factory.load_config(tree)[0])[0]
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert code == 1 and said in out["refusals"][0], out
    code, out = _run(capsys, factory.cmd_land_close, tree, "001")
    assert code == 1 and said in out["refusals"][0], out
    assert tree.exists() and _git(root, "log", "-1", "--format=%s", "main") == "init"
