"""216: autopilot, the factory running from seed to landing while the person is away. Its calls
are recorded as its own (`by=autopilot`, `→ decided by autopilot:`), never as the person's, and
`--by autopilot` is refused to anything but its run's children, which the run lock tells.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Nothing here runs an agent: the
loop's steps go through `autopilot.run_step()`, which a test stands in for, as the train's own
tests drive it in process.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
from pathlib import Path

import pytest
from factory_helpers import (
    NAME,
    _build_report,
    _change,
    _files,
    _gate_config,
    _git,
    _run,
    factory,
    needs_uv,
    sdlc,
)
from train_driver import fake_claude

ROOT = Path(__file__).resolve().parents[1]
ap = factory.autopilot


def _common(root: Path) -> Path:
    return Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))


@pytest.fixture
def no_env(monkeypatch):
    monkeypatch.delenv(factory.AUTOPILOT_RUN_ENV, raising=False)


def _under_lock(root: Path, monkeypatch):
    """The run lock held by this process, as the loop holds it, and the env its children get."""
    monkeypatch.setenv(factory.AUTOPILOT_RUN_ENV, str(_common(root) / factory.AUTOPILOT_RUN_LOCK))
    return ap.autopilot_lock(root)


# ---------------------------------------------------------------- A. who decided (R1–R5)


def test_a_second_autopilot_run_is_refused_while_one_holds_the_lock(
    tmp_path, capsys, no_env
) -> None:
    """R1: a second `--run` while the lock is held is refused, and writes nothing."""
    root = _change(tmp_path)
    with ap.autopilot_lock(root) as held:
        assert held
        code, out = _run(capsys, ap.cmd_autopilot, root, "run")
        assert code == 1 and out["refusals"] == ["an autopilot --run is under way"], out
        with ap.autopilot_lock(root) as again:
            assert not again, "two loops can't hold it"
    with ap.autopilot_lock(root) as held:
        assert held, "let go when its holder ended"


def _ledger(folder: Path, *lines: str) -> Path:
    path = folder / "decisions.md"
    path.write_text("# Decisions\n\n" + "".join(f"{x}\n" for x in lines), encoding="utf-8")
    return path


DEFAULT_LINE = "- [ ] D1 (builder round 1, default): Page the list at 50? Going ahead with 50."


def _by_autopilot_calls(root: Path) -> list:
    folder = root / ".sdlc" / "work" / NAME
    return [
        ("land", lambda: factory.landing.cmd_land(root, "008", "autopilot")),
        ("train", lambda: factory.landing.cmd_train(root, begin=["008"], by="autopilot")),
        ("answer", lambda: factory.cmd_answer(root, "008", "D1", "autopilot")),
        ("write-spec", lambda: factory.cmd_write_spec(root, "008", by="autopilot")),
        folder,
    ]


@pytest.mark.parametrize("case", ["unset", "free", "other repo"])
def test_by_autopilot_is_refused_without_the_run_lock(tmp_path, capsys, monkeypatch, case) -> None:
    """R2: each of the four commands, with the env unset, set with the lock free, or naming
    another repo's held lock, is refused in the same words and writes nothing."""
    root = _change(tmp_path / "one", stage="plan")
    folder = root / ".sdlc" / "work" / NAME
    _ledger(folder, DEFAULT_LINE)
    (folder / "runs").mkdir()
    (folder / "runs" / "spec-draft.md").write_text("---\nid: 008\n---\n# spec\n", encoding="utf-8")
    (folder / "spec.md").write_text("<prompt>\n<prompt>\n", encoding="utf-8")
    other = _change(tmp_path / "two")
    monkeypatch.delenv(factory.AUTOPILOT_RUN_ENV, raising=False)
    if case == "free":
        monkeypatch.setenv(
            factory.AUTOPILOT_RUN_ENV, str(_common(root) / factory.AUTOPILOT_RUN_LOCK)
        )
    common = _common(root)
    before = (_files(folder), sorted(p.name for p in common.iterdir()))
    with ap.autopilot_lock(other) as held:
        assert held
        if case == "other repo":
            monkeypatch.setenv(
                factory.AUTOPILOT_RUN_ENV, str(_common(other) / factory.AUTOPILOT_RUN_LOCK)
            )
        *calls, _ = _by_autopilot_calls(root)
        for name, call in calls:
            code, out = _run(capsys, call)
            assert code == 1, (name, out)
            assert factory.BY_AUTOPILOT_REFUSED in out["refusals"], (name, out)
    after = (_files(folder), sorted(p.name for p in common.iterdir() if p.name != "index.lock"))
    assert after[0] == before[0], "nothing written in the folder"
    assert not (common / factory.landing.TRAIN_STATE).exists(), "no train begun"


def test_autopilot_decision_is_ticked_but_never_the_persons(tmp_path, capsys, monkeypatch) -> None:
    """R5: `answer --by autopilot` ticks an open default with the kept answer, a look as seen and
    a blocking with its first option; `read_ledger()` reads each as decided by autopilot, never as
    the person's, and never as open. An upgrade, or a blocking with no option, is refused."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    path = _ledger(
        folder,
        DEFAULT_LINE,
        "- [ ] D2 (builder round 1, blocking): Keep drafts 30 days or forever?",
        "  - OPTION: 30 days — within the limit",
        "  - OPTION: forever — nothing lost",
        "  - WHY: the limit",
        "- [ ] D3 (approver round 1, look): The board's colours changed",
        "- [ ] D4 (builder round 1, blocking): Upgrade to Tier 2?",
        "  - OPTION: upgrade to Tier 2 — needs a spec",
        "  - OPTION: stay Tier 1 — narrower",
        "- [ ] D5 (builder round 1, blocking): No options here?",
        "- [x] D6 (builder round 1, default): Log it? → decided: no",
    )
    monkeypatch.setattr(factory, "autopilot_running", lambda root: True)
    (folder / "build").mkdir()
    (folder / "build" / "round-1.md").write_text("Built.\n", encoding="utf-8")
    (folder / "decision.md").write_text(
        "DECISION: ESCALATE\n\n- ESCALATED: look: The board's colours changed\n", encoding="utf-8"
    )
    for ident in ("D1", "D2", "D3"):
        code, out = _run(capsys, factory.cmd_answer, root, "008", ident, "autopilot")
        assert code == 0, out
    code, out = _run(capsys, factory.cmd_answer, root, "008", "D4", "autopilot")
    assert code == 1 and "upgrade" in out["refusals"][0], out
    code, out = _run(capsys, factory.cmd_answer, root, "008", "D5", "autopilot")
    assert code == 1 and "no option" in out["refusals"][0], out
    code, out = _run(capsys, factory.cmd_answer, root, "008", "D6", "autopilot")
    assert code == 1 and "isn't open" in out["refusals"][0], out
    text = path.read_text(encoding="utf-8")
    assert f"{DEFAULT_LINE.replace('[ ]', '[x]')}{factory.DECIDED_AUTOPILOT}" in text
    assert " → decided: " not in text.replace("D6 (builder round 1, default): Log it? →", "")
    ledger = {d["id"]: d for d in factory.read_ledger(folder)}
    assert ledger["D1"]["answer"] == factory.KEPT_ANSWER
    assert ledger["D2"]["answer"] == "30 days"
    assert ledger["D3"]["answer"] == "seen"
    for ident in ("D1", "D2", "D3"):
        assert ledger[ident]["decided_by"] == "autopilot" and not ledger[ident]["open"], ident
        assert ledger[ident]["decided"], ident
    assert ledger["D6"]["decided_by"] == "person"
    assert ledger["D4"]["open"] and ledger["D5"]["open"]


TWO_VALUES_RE = re.compile(r"""\(\s*["']auto["']\s*,\s*["']person["']\s*\)""")


def test_landed_values_are_three() -> None:
    """R4: no reader in the scripts branches on `("auto", "person")` alone; each names
    `autopilot` too, and the factory's own list is the three."""
    found = []
    for path in [*(ROOT / "scripts").rglob("*.py"), *(ROOT / "plugins" / "factory").rglob("*.py")]:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if TWO_VALUES_RE.search(line):
                found.append(f"{path.relative_to(ROOT).as_posix()}:{n}")
    assert not found, found
    assert factory.BY_VALUES == ("auto", "person", "autopilot")


def test_land_message_says_by_autopilot(tmp_path) -> None:
    """R3: a change landed under autopilot carries `Sdlc-Landed: by=autopilot` on its commit."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    text = factory.landing.land_message(root, folder, "autopilot", False)
    assert text.rstrip().splitlines()[-1] == "Sdlc-Landed: by=autopilot"
    assert sdlc.metrics.parse_trailers(text)["landed"]["by"] == "autopilot"


def test_autopilot_records_are_never_the_persons() -> None:
    """R23: what autopilot writes in a change's folder is never a person's record: a ledger line it
    answered is no kept, changed or answered call in the records' counts, and `findings.md` gains
    no `By:` value for it."""
    fr = sdlc.factory_records
    ledger = (
        "# Decisions\n\n"
        "- [x] D1 (builder round 1, default): Page at 50? → decided by autopilot: "
        f"{factory.KEPT_ANSWER}\n"
        "- [x] D2 (approver round 1, look): Colours → decided by autopilot: seen\n"
    )
    files = {"decision.md": "DECISION: READY\n", "decisions.md": ledger}

    def show(rel: str) -> str | None:
        return files.get(rel)

    def listing(rel: str) -> str:
        return "\n".join(files)

    counts = fr.autonomy_counts(show, listing)
    assert counts["defaults"]["autopilot"] == 1 and counts["looks"]["autopilot"] == 1
    assert counts["defaults"]["kept"] == counts["defaults"]["changed"] == 0
    assert counts["looks"]["seen"] == 0
    assert fr.DECIDED_AUTOPILOT == factory.DECIDED_AUTOPILOT
    assert "autopilot" not in sdlc.SHIP_PASSES


# ---------------------------------------------------------------- D. the risk budgets (R24–R26)


def _config(**over) -> dict:
    cfg = dict(ap.CONFIG)
    cfg["debt_weights"] = dict(ap.DEBT_WEIGHTS)
    base = {k: ap.RISK_OTHER for k in factory.landing.SIGNAL_KINDS}
    cfg["risk_weights"] = {**base, **ap.RISK_WEIGHTS, **ap.RISK_FACTORS}
    cfg["guards"] = []
    return {**cfg, **over}


def test_review_debt_is_counted_by_kind() -> None:
    """R24: each kind at its weight, a call named twice counted once, a kind with no weight
    counted at none."""
    calls = [
        {"kind": "default", "change": "008-a", "id": "D1"},
        {"kind": "default", "change": "008-a", "id": "D1"},
        {"kind": "look", "change": "008-a", "id": "D2"},
        {"kind": "blocking", "change": "009-b", "id": "D1"},
        {"kind": "spec", "change": "009-b", "id": "spec"},
        {"kind": "intent", "change": "009-b", "id": "2026-11-21-3"},
        {"kind": "other", "change": "009-b", "id": "x"},
    ]
    state = {"config": _config(), "calls": calls}
    debt = ap.review_debt(state)
    assert debt["spent"] == 1 + 2 + 3 + 2 + 1 and debt["limit"] == 40
    assert debt["by_kind"] == {"default": 1, "look": 2, "blocking": 3, "spec": 2, "intent": 1}
    heavy = {"config": _config(debt_weights={**ap.DEBT_WEIGHTS, "look": 10}), "calls": calls}
    assert ap.review_debt(heavy)["spent"] == 1 + 10 + 3 + 2 + 1, "a weight is read"


def test_every_signal_has_a_kind(tmp_path, capsys, monkeypatch) -> None:
    """R25: every string `land_signals()` gives comes with its kind, in order, each one of
    `SIGNAL_KINDS`; and `land-check` prints them as `signal_kinds`."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    L = factory.landing
    cases = {"failed": [{"case": "c1", "graders": []}], "skipped": "over budget"}
    parts = {"undone": [], "nits": ["2026-11-01-1"], "cases": cases}
    monkeypatch.setattr(L, "land_parts", lambda folder, pre, root=None, cfg=None: parts)
    monkeypatch.setattr(L, "resolution_signals", lambda root, folder, cfg: ["one", "two"])
    monkeypatch.setattr(L, "nit_findings", lambda root, folder, cfg: [])
    monkeypatch.setattr(L, "read_impact", lambda folder: "major")
    _ledger(
        folder,
        DEFAULT_LINE,
        "- [x] D2 (code round 1, default): Log it? → settled by the approver: the spec says",
    )
    (folder / "build").mkdir()
    (folder / "build" / "land-1.ask.md").write_text("Rename it.\n", encoding="utf-8")
    pre = {"risk": {"sensitive": ["src/a.py"], "irreversible": ["db/1.sql"]},
           "closes": {"closes": "12"}, "undone": {"items": [{"text": "x"}]},
           "checks": {"checks": [{"name": "c"}]}, "cases": {"scope": ["skills/x"]},
           "ci": {"state": "red", "branch": "main", "sha": "abcdef1234567890",
                  "url": "https://ci/1"}}  # fmt: skip
    kinds: list[str] = []
    signals, _ = L.land_signals(
        folder, root, "ESCALATE", {"land": {"auto": False}}, pre, unreviewed=None, kinds=kinds
    )
    assert len(kinds) == len(signals), list(zip(kinds, signals, strict=False))
    assert set(kinds) <= set(L.SIGNAL_KINDS)
    assert set(kinds) == set(L.SIGNAL_KINDS) - {"unread"}, "every kind reached"
    assert kinds[signals.index("impact: major")] == "impact"
    assert kinds[signals.index(L.LANDING_FIXED)] == "fixed"
    monkeypatch.setattr(L, "_preflight", lambda folder, tree: (None, "boom"))
    kinds = []
    signals, _ = L.land_signals(folder, root, "READY", {"land": {"auto": True}}, kinds=kinds)
    assert kinds == ["unread"] and len(signals) == 1
    # `land-check` prints each change's kinds beside its signals.
    monkeypatch.setattr(L, "_preflight", lambda folder, tree: (pre, ""))
    monkeypatch.setattr(
        factory,
        "ready",
        lambda root: [{"change": NAME, "worktree": str(root), "decision": "READY", "overlaps": []}],
    )
    monkeypatch.setattr(L, "_unreviewed_at_test", lambda root, folder, cfg: [])
    monkeypatch.setattr(L, "unrecovered", lambda paths, recover: [])
    monkeypatch.setattr(L, "land_question", lambda *a, **k: "the question")
    monkeypatch.setattr(L, "land_shown", lambda batch: "shown")
    code, out = _run(capsys, L.cmd_land_check, root, [])
    entry = out["batch"][0]
    assert (
        len(entry["signal_kinds"]) == len(entry["signals"]) and "sensitive" in entry["signal_kinds"]
    )


def test_change_risk_weighs_pushed_and_stacked() -> None:
    """R26: each landed change's kinds at their weights, each kind once, `impact` at 3 only for a
    major, times `pushed` when pushed and `stacked` when stacked; a change not landed adds none."""
    signals = [["sensitive", "touches sensitive paths: a"], ["cases", "c1"], ["cases", "c2"],
               ["impact", "decision.md proposes no `- IMPACT:`"]]  # fmt: skip
    changes = {
        "008-a": {"place": "landed", "signals": signals},
        "009-b": {"place": "landed", "signals": signals, "pushed": True},
        "010-c": {"place": "landed", "signals": signals, "stacked": True},
        "011-d": {"place": "landed", "signals": [["impact", "impact: major"]], "pushed": True,
                  "stacked": True},
        "012-e": {"place": "ready", "signals": signals},
    }  # fmt: skip
    risk = ap.change_risk({"config": _config(), "changes": changes})
    one = 3 + 1 + 1  # sensitive, cases once, impact not major
    assert risk["by_change"] == {"008-a": one, "009-b": one * 2, "010-c": one * 1.5,
                                 "011-d": 3 * 2 * 1.5}  # fmt: skip
    assert risk["spent"] == one + one * 2 + one * 1.5 + 9 and risk["limit"] == 30


# ---------------------------------------------------------------- B. bounds, preview, begin


ITEMS = [
    {"id": "2026-11-21-1", "title": "Fix the drafts crash", "group": "ready", "rule": "bug",
     "label": "bug high", "theme": "drafts", "kind": "bug"},
    {"id": "2026-11-21-2", "title": "Keep tabs", "group": "ready", "rule": "priority",
     "label": "priority high · idea", "theme": "tabs", "kind": "idea"},
    {"id": "2026-11-21-3", "title": "Maybe export", "group": "decide", "rule": "idea",
     "label": "idea", "theme": "drafts", "kind": "idea"},
    {"id": None, "title": "[drafts] 3 open, cost S", "group": "ready", "rule": "nits",
     "label": "nits", "theme": "drafts", "kind": "nit"},
]  # fmt: skip
DOCS = {"docs": {"policy": {"path": ".sdlc/SDLC.md"}, "review": {"path": ".sdlc/REVIEW.md"}}}


@pytest.fixture
def fake_sdlc(monkeypatch):
    """`sdlc.py` as the factory runs it, stood in for: `config` and `status --json` answered, every
    other call recorded and refused."""
    calls = []

    def run(args, cwd):
        calls.append(list(args))
        if args[0] == "config":
            return 0, DOCS, json.dumps(DOCS)
        if args[:2] == ["status", "--json"]:
            data = {"next_up": {"items": ITEMS}}
            return 0, data, json.dumps(data)
        return 1, None, "not stood in for"

    monkeypatch.setattr(factory, "_sdlc", run)
    return calls


def _on_main(root: Path, text: str, name: str = "factory.toml") -> None:
    _git(root, "checkout", "-q", "main")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / name).write_text(text, encoding="utf-8")
    _git(root, "add", f".sdlc/{name}")
    _git(root, "commit", "-q", "-m", name)
    _git(root, "checkout", "-q", NAME)


def _tree_state(root: Path) -> dict:
    found = {}
    for base in (root, _common(root)):
        for p in sorted(base.rglob("*")):
            # A lock's file is made by trying it (`O_CREAT`), as the train's are: never state.
            if (p.is_file() and ".git/objects" not in p.as_posix() and p.name != "index"
                    and p.suffix != ".lock"):  # fmt: skip
                found[p.as_posix()] = p.read_bytes()
    return found


ENABLED = "[autopilot]\nenabled = true\ndebt = 12\n"


def test_candidates_are_the_ready_group_within_bounds() -> None:
    """R10: the ready group's seeds in rank order, within the seeds or themes asked for: never the
    decide group, a nit line with no seed, nor a seed the run already took."""
    every = ap.bounds_of(None, None, 5, 1, None)
    assert [i["id"] for i in ap.candidates(ITEMS, every)] == ["2026-11-21-1", "2026-11-21-2"]
    themed = ap.bounds_of(None, ["drafts"], 5, 1, None)
    assert [i["id"] for i in ap.candidates(ITEMS, themed)] == ["2026-11-21-1"]
    named = ap.bounds_of(["2026-11-21-2", "2026-11-21-3"], None, 5, 1, None)
    assert [i["id"] for i in ap.candidates(ITEMS, named)] == ["2026-11-21-2"], "never decide"
    state = {"seeds": {"2026-11-21-1": {"change": "009-x"}}}
    assert [i["id"] for i in ap.candidates(ITEMS, every, state)] == ["2026-11-21-2"]


def test_a_seed_with_an_issue_is_a_candidate_only_when_named() -> None:
    """D9: a seed whose `Issue:` line names a public issue (or can't be read) is a candidate only
    when `--seeds` names it: text an outsider wrote is built unseen only by the person's choice."""
    items = [
        {"id": S1, "group": "ready", "theme": None, "issues": [12]},
        {"id": S2, "group": "ready", "theme": None, "issues": None},
        {"id": S3, "group": "ready", "theme": None, "issues": []},
    ]
    every = ap.bounds_of(None, None, 5, 1, None)
    assert [i["id"] for i in ap.candidates(items, every)] == [S3]
    named = ap.bounds_of([S1, S2], None, 5, 1, None)
    assert [i["id"] for i in ap.candidates(items, named)] == [S1, S2]


def test_autopilot_preview_writes_nothing(tmp_path, capsys, fake_sdlc, no_env) -> None:
    """R8: `--preview` gives the question and what its yes option shows (the bounds, the base
    branch's limits, the first candidates, that every call is autopilot's) and writes nothing."""
    root = _change(tmp_path)
    _on_main(root, ENABLED)
    before = _tree_state(root)
    code, out = _run(capsys, ap.cmd_autopilot, root, "preview", None, ["drafts"], 20.0, 6.0, 1)
    assert code == 0, out
    assert _tree_state(root) == before, "nothing written anywhere"
    assert out["question"].endswith("(yes / no)") and "$20.0" in out["question"]
    assert "review debt reaches 12" in out["question"]
    shown = out["shown"]
    for said in ("themes: drafts", "$20.0", "hours: 6.0", "Tier 1 at most", "parallel: 3",
                 "review debt limit 12", "2026-11-21-1", "never as yours"):  # fmt: skip
        assert said in shown, said
    assert "2026-11-21-2" not in shown, "outside the themes"
    assert out["config"]["guards"] == [".sdlc/SDLC.md", ".sdlc/REVIEW.md"]
    # 231 R5: with no doc, the theme the bounds hold is proposed, and the yes approves it.
    assert out["goal"]["arg"] == "theme:drafts" and out["goal"]["source"] == "register", out
    assert out["question"].startswith(
        'Run autopilot toward theme:drafts "the drafts theme" (register) until $20.0'
    ), out["question"]
    assert shown.startswith("Goal:\n") and "theme:drafts" in shown.split("Bounds:")[0]
    code, out = _run(capsys, ap.cmd_autopilot, root, "preview", None, None, 20.0, 6.0, 1,
                     "Make drafts fast")  # fmt: skip
    assert code == 0 and out["goal"]["source"] == "stated", out
    assert 'toward Make drafts fast "Make drafts fast" (stated)' in out["question"]
    assert "theme:drafts" in out["shown"].split("Bounds:")[0], "an alternative"
    assert _tree_state(root) == before, "nothing written by either"


@pytest.mark.parametrize(
    "case, why",
    [
        ("no table", "no [autopilot] enabled = true"),
        ("off", "no [autopilot] enabled = true"),
        ("land.auto off", "land.auto is off"),
        ("a train runs", "a train --run is under way"),
        ("an autopilot runs", "an autopilot --run is under way"),
        ("no dollars", "a dollar cap"),
        ("no hours", "need hours"),
        ("a run is begun", "an autopilot run is under way"),
        ("no goal", "the bounds need a goal (--goal), the one --preview named"),
        ("a closed milestone", "M2 isn't an open goal or milestone in the direction doc"),
    ],
)
def test_autopilot_begin_refusals(tmp_path, capsys, fake_sdlc, no_env, case, why) -> None:
    """R9: each refusal writes nothing; with none, the state is written in the git common dir."""
    root = _change(tmp_path)
    toml = {"no table": "", "off": "[autopilot]\nenabled = false\n",
            "land.auto off": ENABLED + "\n[land]\nauto = false\n"}.get(case, ENABLED)  # fmt: skip
    if toml:
        _on_main(root, toml)
    usd = None if case == "no dollars" else 10.0
    hours = None if case == "no hours" else 2.0
    state = _common(root) / factory.AUTOPILOT_STATE
    if case == "a run is begun":
        state.write_text(json.dumps({"id": "x", "started": "2026-11-21T00:00:00Z"}), "utf-8")
    before = _tree_state(root)
    lock = {"a train runs": factory.landing.run_lock, "an autopilot runs": ap.autopilot_lock}
    goal = {"no goal": None, "a closed milestone": "M2"}.get(case, "Keep drafts")
    args = (ap.cmd_autopilot, root, "begin", None, None, usd, hours, None, goal)
    if case in lock:
        with lock[case](root) as held:
            assert held
            code, out = _run(capsys, *args)
    else:
        code, out = _run(capsys, *args)
    assert code == 1 and any(why in r for r in out["refusals"]), out
    assert _tree_state(root) == before, "nothing written"


def test_autopilot_begin_writes_the_state_once(tmp_path, capsys, fake_sdlc, no_env) -> None:
    root = _change(tmp_path)
    _on_main(root, ENABLED)
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        f"# Inbox\n\n> The register.\n\n```\n## [2026-01-01-1] [idea] An example\n```\n\n"
        f"## [{S1}] [idea] Keep drafts\n\nKeep them.\n\n### [2026-11-21-8] not an entry\n",
        encoding="utf-8",
    )
    code, out = _run(capsys, ap.cmd_autopilot, root, "begin", None, ["drafts"], 10.0, 2.0, None,
                     "theme:drafts")  # fmt: skip
    assert code == 0 and out["state"] == "begun", out
    state = ap.read_state(root)
    # 231 R6, R11: the goal the preview named, resolved again, and the register's ids at the start.
    assert state["goal"] == {"source": "register", "arg": "theme:drafts",
                             "title": "the drafts theme", "serves": [],
                             "scope": ["2026-11-21-1"]}, state["goal"]  # fmt: skip
    assert state["register"] == {"start": [S1]}, "a fenced example is no entry"
    assert state["bounds"] == {"seeds": [], "themes": ["drafts"], "usd": 10.0, "hours": 2.0,
                               "level": 2}  # fmt: skip
    assert state["config"]["debt"] == 12 and state["config"]["enabled"] is True
    assert state["config"]["land_batch"] == 5, "land.batch fixed at --begin"
    assert not list(root.glob(".sdlc/reports/**/*")), "nothing in a tree"


def test_autopilot_config_is_read_from_the_base_branch(tmp_path, capsys, fake_sdlc, no_env) -> None:
    """R28: the change's own `factory.toml` raising a limit changes nothing: every value is the
    base branch's, fixed in the state at `--begin`."""
    root = _change(tmp_path)
    _on_main(
        root,
        ENABLED + 'risk = 9\nparallel = 2\nguards = ["src/**"]\n'
        "[autopilot.debt_weights]\nlook = 7\n[autopilot.risk_weights]\nsensitive = 5\n"
        "pushed = 3\n",
    )
    (root / ".sdlc" / "factory.toml").write_text(
        "[autopilot]\nenabled = true\ndebt = 999\nrisk = 999\nparallel = 9\nguards = []\n",
        encoding="utf-8",
    )
    cfg, warnings = ap.autopilot_config(root)
    assert (cfg["debt"], cfg["risk"], cfg["parallel"], cfg["guards"]) == (12, 9, 2, ["src/**"])
    assert cfg["debt_weights"]["look"] == 7 and cfg["risk_weights"]["sensitive"] == 5
    assert cfg["risk_weights"]["pushed"] == 3 and not warnings
    code, out = _run(capsys, ap.cmd_autopilot, root, "begin", None, None, 10.0, 2.0, None, "Go")
    assert code == 0, out
    assert ap.read_state(root)["config"]["debt"] == 12


def test_default_guards_hold_the_sensitive_paths(tmp_path, fake_sdlc, no_env) -> None:
    """D8: `guards` unset is the base branch's policy and review docs, its `[review] irreversible`
    and its `[review] sensitive`, so autopilot never lands a change to the code that runs it; the
    change's own `[review]` adds nothing."""
    root = _change(tmp_path)
    _on_main(root, ENABLED)
    _on_main(root, '[review]\nsensitive = ["scripts/closing.py"]\nirreversible = ["db/*.sql"]\n',
             "config.toml")  # fmt: skip
    (root / ".sdlc" / "config.toml").write_text('[review]\nsensitive = ["mine/**"]\n', "utf-8")
    cfg, _ = ap.autopilot_config(root)
    assert cfg["guards"] == [".sdlc/SDLC.md", ".sdlc/REVIEW.md", "db/*.sql", "scripts/closing.py"]


# ---------------------------------------------------------------- B. the judges (R11)


WRITES = {"Write", "Edit", "Bash", "NotebookEdit", "MultiEdit"}


def test_new_agents_have_no_write() -> None:
    """R11: the planner and the intent-writer read and reply; neither lists a tool that writes or
    runs, and each says it never commits."""
    import frontmatter as fm

    for name in ("autopilot-planner", "intent-writer"):
        post = fm.load(ROOT / "plugins" / "factory" / "agents" / f"{name}.md")
        tools = {t.strip() for t in str(post["tools"]).split(",")}
        assert tools == {"Read", "Grep", "Glob"} and not tools & WRITES, name
        assert "never" in post.content and "commit" in post.content, name
        assert factory.AUTOPILOT_TASKS[{"autopilot-planner": "wave"}.get(name, "intent")] == name


# ---------------------------------------------------------------- B and C. the loop, in process
#
# A main checkout with a register, its changes made by `sdlc.py new` in process. Every step the loop
# takes goes through `ap.run_step`, stood in for by `Steps`: the agents' replies are files it
# writes, `verdicts` reads from a script per change, `answer` is the real command, and a train's
# `--run` lands each change by a `Close` commit on main.

import contextlib  # noqa: E402
import io  # noqa: E402
import threading  # noqa: E402

S1, S2, S3 = "2026-11-21-1", "2026-11-21-2", "2026-11-21-3"
REGISTER = (
    "# Inbox\n\n> The register.\n\n"
    f"## [{S1}] [idea] Keep drafts\n\nKeep them.\n\n"
    f"## [{S2}] [idea] Show kept drafts\n\nList them, after keeping them.\n\n"
    f"## [{S3}] [idea] Trim logs\n\nTrim.\n"
)
SEEDS = [
    {"id": S1, "title": "Keep drafts", "group": "ready", "label": "idea", "theme": None},
    {"id": S2, "title": "Show kept drafts", "group": "ready", "label": "idea", "theme": None},
    {"id": S3, "title": "Trim logs", "group": "ready", "label": "idea", "theme": None},
]
HAPPY = ["build", "gate", "review", "approve", "done"]
READY_DECISION = "DECISION: READY\n\nGood.\n\n- IMPACT: patch\n"
OUT_LOCK = threading.Lock()


def _draft(slug: str, tier: int = 1, depends: str = "") -> str:
    return (f"---\nslug: {slug}\ntier: {tier}\ndepends_on: {depends}\n---\n\n# {slug}\n\n"
            "## Problem\n\nIt's missing.\n\n## Outcome\n\n- It's there.\n\n"
            "## Approach\n\nAdd it.\n")  # fmt: skip


def _quiet(fn, *args, **kwargs) -> tuple[int, dict | None, str]:
    """An in-process command, its stdout caught: its exit, its JSON and its text."""
    buf = io.StringIO()
    with OUT_LOCK, contextlib.redirect_stdout(buf):
        code = fn(*args, **kwargs)
    text = buf.getvalue()
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    return code, data if isinstance(data, dict) else None, text


def _repo(tmp_path: Path, toml: str = ENABLED) -> Path:
    root = tmp_path / "main"
    root.mkdir(parents=True)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(REGISTER, encoding="utf-8")
    (root / ".sdlc" / "factory.toml").write_text(toml, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


class Steps:
    """The stand-in for `run_step` and `_sdlc`, and the log of every argv the loop ran."""

    def __init__(self, main: Path, monkeypatch, drafts: dict, wave: list[str] | str,
                 readings: dict | None = None) -> None:  # fmt: skip
        self.main, self.drafts, self.wave = main, drafts, wave
        self.readings = {k: list(v) for k, v in (readings or {}).items()}
        self.log: list[tuple[str, list[str]]] = []
        self.hooks: dict = {}
        self.briefs: list[str] = []
        self.items = SEEDS
        monkeypatch.setattr(ap, "run_step", self)
        monkeypatch.setattr(factory, "_sdlc", self.sdlc)
        monkeypatch.setattr(factory.landing, "_checks_now", lambda folder, tree: ([], None))
        monkeypatch.setenv(factory.AUTOPILOT_RUN_ENV,
                           str(_common(main) / factory.AUTOPILOT_RUN_LOCK))  # fmt: skip

    def sdlc(self, args, cwd):
        if args[0] == "config":
            return 0, DOCS, ""
        if args[:2] == ["status", "--json"]:
            return 0, {"next_up": {"items": self.items}}, ""
        if args[0] == "preflight":
            return 0, {"checks": {"checks": []}}, ""
        if args[0] == "new":
            code, _, text = _quiet(sdlc.cmd_new, self.main, args[1], int(args[3]), None,
                                   worktree=True)  # fmt: skip
            return code, None, text
        raise AssertionError(args)

    def slug(self, cwd: Path) -> str:
        return cwd.name.split("-", 1)[1] if cwd.name[:1].isdigit() else ""

    def __call__(self, main: Path, argv: list[str], cwd: Path) -> dict:
        self.log.append((cwd.name, list(argv)))
        if hook := self.hooks.get(argv[0]):
            hook(argv, cwd)
        out = self.reply(argv, cwd)
        code = 1 if out.get("refusals") or out.get("problem") else 0
        return {"argv": list(argv), "code": code, "out": out, "said": ""}

    def reply(self, argv: list[str], cwd: Path) -> dict:
        run = next((self.main / factory.REPORTS / "autopilot").iterdir())
        if argv[:3] == ["agent", "--task", "wave"]:
            wave = self.wave if isinstance(self.wave, str) else self.wave.pop(0)
            if isinstance(wave, list | dict):
                brief = (run / "briefs" / "wave.md").read_text("utf-8")
                self.briefs.append(brief)
                plan = wave if isinstance(wave, dict) else {"wave": wave}
                wave = _plan_reply(brief, plan["wave"], plan.get("leave"))
            return self.file(run / "waves" / f"wave-{len(self.log)}.md", wave)
        if argv[:3] == ["agent", "--task", "intent"]:
            return self.file(run / "intents" / f"{argv[4]}.md", self.drafts[argv[4]])
        folder = cwd / ".sdlc" / "work" / cwd.name
        num = argv[1] if len(argv) > 1 else ""
        if argv[0] == "verdicts":
            queue = self.readings.setdefault(self.slug(cwd), list(HAPPY))
            nxt = queue.pop(0) if len(queue) > 1 else queue[0]
            reading = nxt if isinstance(nxt, dict) else {"next": nxt}
            return {"round": 1, "limit": 3, "built": 1, "missing": ["code"], **reading}
        if argv[0] == "agent":
            task = argv[argv.index("--task") + 1]
            if task == "approve":
                (folder / "decision.md").write_text(READY_DECISION, encoding="utf-8")
            return {"to": f".sdlc/work/{cwd.name}/build/round-1.md"}
        if argv[0] == "answer":
            return _quiet(factory.cmd_answer, cwd, num, argv[2], "autopilot")[1]
        if argv[0] == "land-check":
            names = [n for n in self.names() if n.split("-")[0] in argv[1:]]
            return {"batch": [{"change": n, "signals": [], "signal_kinds": []} for n in names],
                    "excluded": []}  # fmt: skip
        if argv[:2] == ["train", "--begin"]:
            self.batch = [n for n in self.names() if n.split("-")[0] in argv[2:-2]]
            return {"state": "begun"}
        if argv[:2] == ["train", "--run"]:
            for name in self.batch:
                _git(self.main, "commit", "-q", "--allow-empty", "-m", f"Close {name}")
            return {"landed": list(self.batch), "ejected": [], "done": True}
        return {}

    def names(self) -> list[str]:
        return [b for _, b in factory.worktrees(self.main)[1:]]

    def file(self, path: Path, text: str) -> dict:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return {"to": path.relative_to(self.main).as_posix()}

    def ran(self, *head: str) -> list[tuple[str, list[str]]]:
        return [(c, a) for c, a in self.log if a[: len(head)] == list(head)]


BRIEF_SEED_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}-\d+) \[", re.M)


def _plan_reply(brief: str, wave: list[str], leave: dict | None = None) -> str:
    """A planner's plan (231 R8) placing every candidate the brief lists: `wave`'s in WAVE lines,
    in its order, `leave`'s (seed to its LEAVE line's kind and reason) left, the rest waiting."""
    found = BRIEF_SEED_RE.findall(brief.partition("## In flight")[0])
    leave = leave or {}
    lines = ["## Drafts get lost", ""]
    lines += [f"- WAVE: {s} — tier 1 — it shares no file with the rest" for s in wave]
    lines += [f"- WAITS: {s} — after the wave before it" for s in found
              if s not in wave and s not in leave]  # fmt: skip
    lines += [f"- LEAVE: {s} — {why}" for s, why in leave.items()]
    return "\n".join(lines) + "\n"


def _begin(root: Path, capsys, usd: float = 50.0, **kw) -> dict:
    code, out = _run(capsys, ap.cmd_autopilot, root, "begin", kw.get("seeds"), None, usd, 4.0,
                     kw.get("level"), kw.get("goal", "Keep drafts working"))  # fmt: skip
    assert code == 0, out
    return out


def _loop(root: Path, capsys) -> tuple[int, dict]:
    return _run(capsys, ap.cmd_autopilot, root, "run")


def test_autopilot_end_to_end(tmp_path, capsys, monkeypatch) -> None:
    """The spec's dry run: two seeds, the second depending on the first, both opened; the second
    built only after the first's `Close` commit (R13); both landed by=autopilot; a summary naming
    both and every call."""
    root = _repo(tmp_path)
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts"),
                                      S2: _draft("show-drafts", depends=f"[{S1}]")},
                  [[S1, S2], []])  # fmt: skip
    steps.items = SEEDS[:2]
    (root / ".sdlc" / "DIRECTION.md").write_text(DIRECTION, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "direction")
    kept = {p: (root / p).read_bytes() for p in (".sdlc/work/inbox.md", ".sdlc/DIRECTION.md")}
    _begin(root, capsys)
    code, out = _loop(root, capsys)
    assert code == 0, out
    assert {p: (root / p).read_bytes() for p in kept} == kept, "231 R9: never written"
    state = ap.read_state(root)
    names = sorted(state["changes"])
    first, second = names
    assert [state["changes"][n]["place"] for n in names] == ["landed", "landed"], state["changes"]
    order = [(c, a[:2]) for c, a in steps.log]
    close_first = next(i for i, (c, a) in enumerate(steps.log) if a[:2] == ["train", "--run"])
    second_starts = next(i for i, (c, a) in enumerate(steps.log) if c == second)
    assert second_starts > close_first, order
    begins = steps.ran("train", "--begin")
    assert all(a[-2:] == ["--by", "autopilot"] for _, a in begins)
    intent = root / ".claude" / "worktrees" / second / ".sdlc" / "work" / second / "intent.md"
    text = intent.read_text(encoding="utf-8")
    assert f"depends_on: [{first.split('-')[0]}]" in text and "opened_by: autopilot" in text
    summary = (root / out["summary"]).read_text(encoding="utf-8")
    assert first in summary and second in summary and "2 hours" not in summary
    assert summary.count("(intent)") == 2
    assert not steps.ran("cases") and not steps.ran("run-cases") and not steps.ran("upgrade")


def test_a_change_waits_for_what_it_depends_on(tmp_path, capsys, monkeypatch) -> None:
    """R13: a change waits at `stage: plan` while what it depends on has no `Close` commit, and
    the summary says on what: here its dependency is held, so it never builds."""
    root = _repo(tmp_path)
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts"),
                                      S2: _draft("show-drafts", depends=f"[{S1}]")},
                  [[S1, S2], []],
                  {"keep-drafts": ["stop"]})  # fmt: skip
    steps.items = SEEDS[:2]
    _begin(root, capsys)
    code, out = _loop(root, capsys)
    state = ap.read_state(root)
    first, second = sorted(state["changes"])
    assert state["changes"][first]["place"] == "held"
    assert state["changes"][second]["place"] == "waiting"
    assert "waits on" in state["changes"][second]["why"]
    assert not [a for c, a in steps.log if c == second], "it never took a step"
    assert out["in_flight"] == {second: "waiting"}


def test_planner_reply_is_checked_by_the_script(tmp_path, capsys, monkeypatch) -> None:
    """R11, 231 R8: a plan naming a seed that isn't a candidate, or more WAVE lines than the
    room, or leaving a candidate unplaced, is refused and asked once more with the refusal (the
    planner's mend); a second refusal opens nothing."""
    root = _repo(tmp_path, ENABLED + "parallel = 1\n")
    group = "## Drafts get lost\n\n"
    rest = f"- WAITS: {S3} — later\n"
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts")},
                  [group + "- WAVE: 2026-01-01-9 — tier 1 — first\n",
                   group + f"- WAVE: {S1} — tier 1 — first\n- WAVE: {S2} — tier 1 — next\n"
                   + rest])  # fmt: skip
    _begin(root, capsys)
    code, out = _loop(root, capsys)
    assert len(steps.ran("agent", "--task", "wave")) == 2
    assert not steps.ran("agent", "--task", "intent"), "nothing opened"
    state = ap.read_state(root)
    assert "refused twice" in state["planned_out"] and "past the room for 1" in state["planned_out"]
    assert state["changes"] == {}
    run = next((root / ".sdlc" / "reports" / "autopilot").iterdir())
    brief = (run / "briefs" / "wave.md").read_text(encoding="utf-8")
    refusal = brief.split("## Your last reply was refused")[1]
    for said in ("not candidates: 2026-01-01-9", f"placed in no line: {S1}"):
        assert said in refusal, (said, refusal)


def test_opened_intent_says_autopilot_opened_it(tmp_path, capsys, monkeypatch) -> None:
    """R12: the intent `new` scaffolded keeps its `id:` as written, gains `idea:` and
    `opened_by: autopilot` by line, and holds the draft's body; `vet` reads the key; the change's
    `runs/autopilot.md` records the call."""
    root = _repo(tmp_path)
    Steps(root, monkeypatch, {S1: _draft("keep-drafts")}, [[S1], []],
          {"keep-drafts": ["stop"]})  # fmt: skip
    _begin(root, capsys)
    _loop(root, capsys)
    (name,) = ap.read_state(root)["changes"]
    folder = root / ".claude" / "worktrees" / name / ".sdlc" / "work" / name
    text = (folder / "intent.md").read_text(encoding="utf-8")
    head = text.split("---")[1]
    assert re.search(r"^id: 001$", head, re.M), head
    assert re.search(rf"^idea: {S1}$", head, re.M) and re.search(
        r"^opened_by: autopilot$", head, re.M
    )
    assert (
        "## Problem\n\nIt's missing." in text and "slug: keep-drafts" not in text.split("---", 2)[2]
    )
    rec = sdlc.load_change(folder, folder.parents[2])
    assert rec["opened_by"] == "autopilot" and not rec["errors"], rec["errors"]
    line = sdlc._change_lines({**rec, "age_days": 0, "unfilled": [], "artifacts": []}, {})[0]
    assert "opened by autopilot" in line
    bad = folder.parent / "009-odd"
    bad.mkdir()
    (bad / "intent.md").write_text(text.replace("opened_by: autopilot", "opened_by: me"), "utf-8")
    assert any("opened_by:" in e for e in sdlc.load_change(bad, folder.parents[2])["errors"])
    record = (folder / "runs" / "autopilot.md").read_text(encoding="utf-8")
    assert f"opened from seed {S1}" in record and "held:" in record


def test_a_seed_with_an_issue_is_opened_with_closes(tmp_path, capsys, monkeypatch) -> None:
    """D9: a seed named in `--seeds` whose `Issue:` line names issues is opened with the `closes:`
    line `/sdlc:intent` writes, so the landing's `issue` signal and the issue's close still work;
    one whose line can't be read is held, never opened without it."""
    root = _repo(tmp_path)
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts"), S2: _draft("show-drafts")},
                  [[S1, S2], []],
                  {"keep-drafts": ["stop"]})  # fmt: skip
    steps.items = [{**SEEDS[0], "issues": [12, 15]}, {**SEEDS[1], "issues": None}]
    _begin(root, capsys, seeds=[S1, S2])
    _loop(root, capsys)
    state = ap.read_state(root)
    (name,) = state["changes"]
    folder = root / ".claude" / "worktrees" / name / ".sdlc" / "work" / name
    head = (folder / "intent.md").read_text(encoding="utf-8").split("---")[1]
    assert re.search(r"^closes: \[12, 15\]$", head, re.M), head
    assert factory.intent_closes(folder) == "[12, 15]"
    assert "Issue:" in state["seeds"][S2]["why"], state["seeds"][S2]
    assert not steps.ran("agent", "--task", "intent", "--seed", S2), "never drafted"


ALLOWED = {tuple(t) for ts in ap.AUTOPILOT_STEPS.values() for t in ts}


def _named(argv: list[str]) -> bool:
    """Whether `argv` is one of `AUTOPILOT_STEPS`' templates, filled, or a landing's step."""
    for template in ALLOWED | {tuple(t) for t in ap.TRAIN_COMMANDS.values()}:
        if template[0] == "land-check" and argv[0] == "land-check":
            return True
        if template[:2] == ("train", "--begin") and argv[:2] == ["train", "--begin"]:
            return argv[-2:] == ["--by", "autopilot"]
        if len(template) == len(argv) and all(
            t.startswith("{") or t == a for t, a in zip(template, argv, strict=True)
        ):
            return True
    return False


def test_build_step_runs_only_the_named_commands(tmp_path, capsys, monkeypatch) -> None:
    """R14: every step `verdicts` can name is taken by the commands `AUTOPILOT_STEPS` holds, and
    none other; reviewers and mends are started together, one a role."""
    root = _repo(tmp_path)
    readings = {"keep-drafts": [
        "build", "gate", "fix", {"next": "review", "missing": ["code", "test"]}, "arbitrate",
        "rework", {"next": "stop", "way": "mend", "mend": ["builder"]}, "approve", "done",
    ]}  # fmt: skip
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts")}, [[S1], []],
                  readings)  # fmt: skip
    _begin(root, capsys)
    _loop(root, capsys)
    assert all(_named(a) for _, a in steps.log), [a for _, a in steps.log if not _named(a)]
    roles = [a[-1] for _, a in steps.ran("agent") if "--role" in a]
    assert roles == ["code", "test", "builder"]
    snaps = [a for _, a in steps.ran("snapshot")]
    assert snaps and all(a[-1] == "1" for a in snaps), snaps
    assert (
        ap.read_state(root)["changes"][next(iter(ap.read_state(root)["changes"]))]["place"]
        == "landed"
    )


def _landing_state(near_for: float | None, ready: int = 1, wait: int = 30) -> dict:
    changes = {f"00{i}-r": {"place": "ready"} for i in range(1, ready + 1)}
    if near_for is not None:
        since = ap._stamp(ap._now() - __import__("datetime").timedelta(seconds=near_for))
        changes["009-b"] = {"place": "building", "reading": {"next": "approve"},
                            "near_since": since}  # fmt: skip
    return {"changes": changes, "config": {**ap.CONFIG, "wait": wait}}


def test_landing_waits_for_a_nearly_ready_change() -> None:
    """R15: a batch doesn't begin while a change still building sits at `approve` inside the
    wait, unless the ready ones already fill `land.batch`; with nothing nearly ready it begins."""
    assert ap.landing_due(_landing_state(60), 5) == [], "waits for 009"
    assert ap.landing_due(_landing_state(None), 5) == ["001-r"]
    assert ap.landing_due(_landing_state(60, ready=2), 2) == ["001-r", "002-r"], "a full batch"
    far = _landing_state(None)
    far["changes"]["009-b"] = {"place": "building", "reading": {"next": "build", "round": 1,
                                                                "limit": 3}}  # fmt: skip
    assert ap.landing_due(far, 5) == ["001-r"], "a change far from ready isn't waited for"


def test_landing_does_not_wait_past_the_wait() -> None:
    """R15: once the nearly ready change has been so for longer than `[autopilot] wait`, the
    batch begins without it."""
    assert ap.landing_due(_landing_state(31 * 60), 5) == ["001-r"]
    assert ap.landing_due(_landing_state(29 * 60), 5) == []


def test_cancel_stops_between_steps_and_a_rerun_resumes(tmp_path, capsys, monkeypatch) -> None:
    """R16: `--cancel` with no run refuses; a cancel written while a step runs lets the step end,
    starts nothing more and ends the run with its summary; a rerun resumes from the state and
    never opens a seed twice."""
    root = _repo(tmp_path)
    code, out = _run(capsys, ap.cmd_autopilot, root, "cancel")
    assert code == 1 and "no autopilot --run" in out["refusals"][0]
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts")}, [[S1], []])
    steps.items = SEEDS[:1]
    cancel = _common(root) / ap.AUTOPILOT_CANCEL
    steps.hooks["gate"] = lambda argv, cwd: cancel.write_text("cancel\n", encoding="utf-8")
    _begin(root, capsys)
    code, out = _loop(root, capsys)
    assert code == 0 and out["reason"].startswith("cancelled"), out
    gate = next(i for i, (_, a) in enumerate(steps.log) if a[0] == "gate")
    assert len(steps.log) == gate + 1, "nothing started after the step in flight"
    assert not cancel.exists()
    del steps.hooks["gate"]
    code, out = _loop(root, capsys)
    assert code == 0 and out["landed"], out
    assert len(steps.ran("agent", "--task", "intent")) == 1, "the seed opened once"


def _one_change(tmp_path, capsys, monkeypatch, readings, toml: str = ENABLED, draft=None) -> tuple:
    root = _repo(tmp_path, toml)
    steps = Steps(root, monkeypatch, {S1: draft or _draft("keep-drafts")},
                  [[S1], []], {"keep-drafts": readings})  # fmt: skip
    steps.items = SEEDS[:1]
    _begin(root, capsys)
    return root, steps


def _only(root: Path) -> tuple[str, dict, Path]:
    state = ap.read_state(root)
    (name,) = state["changes"]
    tree = root / ".claude" / "worktrees" / name
    return name, state["changes"][name], tree / ".sdlc" / "work" / name


LEDGER_DEFAULT = "- [ ] D1 (builder round 1, default): Page at 50? Going ahead with 50.\n"
LEDGER_BLOCKING = (
    "- [ ] D2 (builder round 1, blocking): Keep drafts 30 days or forever?\n"
    "  - OPTION: 30 days — within the limit\n  - OPTION: forever — nothing lost\n"
    "  - WHY: the limit\n"
)

# 216's gap (218): a reviewer's default, which no builder made unless a later report says so.
LEDGER_REVIEWER = (
    "- [ ] D1 (security reviewer round 1, default): Guard `[review] sensitive`? Assuming yes.\n"
)


def _writes_ledger(text: str):
    def hook(argv, cwd):
        path = cwd / ".sdlc" / "work" / cwd.name / "decisions.md"
        if not path.is_file():
            path.write_text("# Decisions\n\n" + text, encoding="utf-8")

    return hook


def test_escalations_are_answered_as_defaults_and_recorded(tmp_path, capsys, monkeypatch) -> None:
    """R17: a blocking line is answered with its first option and the builder told; an open
    default at the decision is answered with the kept answer; each `→ decided by autopilot:`,
    never ` → decided: `, and each in the run's `escalations.md` with its options and why."""
    root, steps = _one_change(
        tmp_path,
        capsys,
        monkeypatch,
        ["build", {"next": "decide", "pending": ["D2"]}, "gate", "review", "approve", "done"],
    )
    steps.hooks["decisions"] = _writes_ledger(LEDGER_BLOCKING + LEDGER_DEFAULT)
    _loop(root, capsys)
    name, mine, folder = _only(root)
    assert mine["place"] == "landed", mine
    ledger = (folder / "decisions.md").read_text(encoding="utf-8")
    assert "D2 (builder round 1, blocking): Keep drafts 30 days or forever? → decided by " \
           "autopilot: 30 days" in ledger  # fmt: skip
    assert f"→ decided by autopilot: {factory.KEPT_ANSWER}" in ledger
    assert " → decided: " not in ledger
    decided = [a for _, a in steps.ran("agent") if "decided" in a]
    assert decided == [["agent", name[:3], "--task", "decided", "--decision", "D2"]]
    run = next((root / ".sdlc" / "reports" / "autopilot").iterdir())
    escalations = (run / "escalations.md").read_text(encoding="utf-8")
    assert f"## {name} D2 (blocking)" in escalations and "- OPTION: forever" in escalations
    assert "- WHY: the limit" in escalations and "- ANSWER: 30 days" in escalations
    assert f"## {name} D1 (default)" in escalations
    assert "decided by autopilot: D2" in (folder / "runs" / "autopilot.md").read_text("utf-8")


class InFlight(Steps):
    """`Steps`, also keeping which commands of each change are running, each held a moment to
    widen the window, and every time a ledger writer (`answer`, `decisions`) ran beside another
    command of its change."""

    WRITERS = ("answer", "decisions")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.guard, self.flight, self.overlaps = threading.Lock(), [], []

    def __call__(self, main: Path, argv: list[str], cwd: Path) -> dict:
        entry = (cwd.name, argv[0], object())
        with self.guard:
            beside = [e[1] for e in self.flight if e[0] == cwd.name]
            if beside and (argv[0] in self.WRITERS or set(beside) & set(self.WRITERS)):
                self.overlaps.append((cwd.name, argv[0], beside))
            self.flight.append(entry)
        try:
            __import__("time").sleep(0.05)
            return super().__call__(main, argv, cwd)
        finally:
            with self.guard:
                self.flight.remove(entry)


def test_no_ledger_writer_runs_beside_another_step_of_its_change(
    tmp_path, capsys, monkeypatch
) -> None:
    """228 R5: `cmd_answer()` and `cmd_decisions()` rewrite `decisions.md` with no lock, safe
    because the loop never runs either beside another command of the same change: two changes
    built at once, one with a blocking line answered and a review of three roles started
    together, and no ledger writer ever overlaps its own change's other steps."""
    root = _repo(tmp_path)
    roles = {"next": "review", "missing": ["code", "test", "security"]}
    readings = {
        "keep-drafts": ["build", {"next": "decide", "pending": ["D2"]}, "gate", roles,
                        "approve", "done"],
        "trim-logs": ["build", "gate", roles, "approve", "done"],
    }  # fmt: skip
    steps = InFlight(root, monkeypatch, {S1: _draft("keep-drafts"), S3: _draft("trim-logs")},
                     [[S1, S3], []], readings)  # fmt: skip
    steps.hooks["decisions"] = _writes_ledger(LEDGER_BLOCKING + LEDGER_DEFAULT)
    _begin(root, capsys)
    code, out = _loop(root, capsys)
    assert code == 0, out
    places = {n: c["place"] for n, c in ap.read_state(root)["changes"].items()}
    assert sorted(places.values()) == ["landed", "landed"], places
    assert len(steps.ran("answer")) >= 3, "the blocking line and the defaults were answered"
    roles_run = [a for _, a in steps.ran("agent") if "--role" in a]
    assert len(roles_run) == 6, "each change's three roles were started"
    assert steps.overlaps == [], steps.overlaps


def test_a_reviewer_s_default_a_later_build_made_lands(tmp_path, capsys, monkeypatch) -> None:
    """218: a reviewer's open default is answered and lands once a builder report of a later
    round says `- BUILT:` for it; a builder's own default needs no such line (the test above)."""
    root, steps = _one_change(tmp_path, capsys, monkeypatch, list(HAPPY))
    steps.hooks["decisions"] = _writes_ledger(LEDGER_REVIEWER)

    def built(argv, cwd):
        folder = cwd / ".sdlc" / "work" / cwd.name
        (folder / "build").mkdir(exist_ok=True)
        (folder / "build" / "round-2.md").write_text("- BUILT: D1: guarded\n", "utf-8")

    steps.hooks["carry"] = built
    _loop(root, capsys)
    _, mine, folder = _only(root)
    assert mine["place"] == "landed", mine
    assert f"D1 (security reviewer round 1, default): Guard `[review] sensitive`? Assuming " \
           f"yes. → decided by autopilot: {factory.KEPT_ANSWER}" in \
           (folder / "decisions.md").read_text(encoding="utf-8")  # fmt: skip


def test_a_fenced_built_line_still_holds_autopilot(tmp_path) -> None:
    """228 R8: a later builder report quoting `- BUILT: D1` inside a code fence never made the
    reviewer's default, so `hold_causes()` still holds the change on it; the same line outside
    the fence clears it."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _ledger(folder, LEDGER_REVIEWER.rstrip("\n"))
    _build_report(root, 2, "```text\n- BUILT: D1: guarded\n```\n")
    mine = {"guards": []}
    causes = ap.hold_causes(root, root, folder, mine)
    assert any("no build made: D1" in c for c in causes), causes
    _build_report(root, 2, "- BUILT: D1: guarded\n")
    assert not any("no build made" in c for c in ap.hold_causes(root, root, folder, mine))


def test_autopilot_never_upgrades(tmp_path, capsys, monkeypatch) -> None:
    """R18: a blocking decision whose recommendation is `upgrade to Tier 2` is held, and a
    reading that names `upgrade` is held: `factory.py upgrade` never runs under the lock."""
    upgrade = (
        "- [ ] D1 (builder round 1, blocking): Upgrade to Tier 2?\n"
        "  - OPTION: upgrade to Tier 2 — needs a spec\n  - OPTION: stay Tier 1 — narrow\n"
    )
    root, steps = _one_change(tmp_path, capsys, monkeypatch,
                              ["build", {"next": "decide", "pending": ["D1"]}])  # fmt: skip
    steps.hooks["decisions"] = _writes_ledger(upgrade)
    _loop(root, capsys)
    _, mine, folder = _only(root)
    assert mine["place"] == "held" and "never upgrades" in mine["why"], mine
    assert "- [ ] D1" in (folder / "decisions.md").read_text(encoding="utf-8")
    assert not steps.ran("upgrade") and not [a for _, a in steps.log if "upgrade" in a]
    root2, steps2 = _one_change(tmp_path / "two", capsys, monkeypatch, ["build", "upgrade"])
    _loop(root2, capsys)
    assert _only(root2)[1]["place"] == "held" and not steps2.ran("upgrade")


HOLDS = {
    "guards": ('[autopilot]\nenabled = true\nguards = ["src/**"]\n', "touches guarded paths"),
    "contract": (ENABLED, "CONTRACT: the one WAIT"),
    "relax": (ENABLED, "RELAX: narrow allowed-tools"),
    "reconsider": (ENABLED, "reconsider the approach"),
    "gate reason": (ENABLED, "escalated on the gate"),
    "stop": (ENABLED, "verdicts stopped"),
    "checks": (ENABLED, "isn't read-only"),
    "excluded": (ENABLED, "land-check excludes it"),
    "cases": (ENABLED, "skills' cases are in its scope"),
    "unbuilt": (ENABLED, "a reviewer's or the approver's default no build made: D1"),
}


@pytest.mark.parametrize("cause", sorted(HOLDS))
def test_held_change_and_its_dependents_never_land(tmp_path, capsys, monkeypatch, cause) -> None:
    """R19: each cause holds the change: it never lands, the cause is in its `runs/autopilot.md`
    and the summary, and a change depending on it never builds."""
    toml, why = HOLDS[cause]
    root = _repo(tmp_path, toml)
    readings = {"keep-drafts": ["stop"] if cause == "stop" else list(HAPPY)}
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts"),
                                      S2: _draft("show-drafts", depends=f"[{S1}]")},
                  [[S1, S2], []], readings)  # fmt: skip
    steps.items = SEEDS[:2]
    decision = READY_DECISION

    def approve(argv, cwd):
        folder = cwd / ".sdlc" / "work" / cwd.name
        if cause == "contract":
            (folder / "build").mkdir(exist_ok=True)
            (folder / "build" / "round-1.md").write_text(
                "Built.\n- CONTRACT: the one WAIT: it needs two\n", encoding="utf-8"
            )
        if cause == "relax":
            (folder / "build").mkdir(exist_ok=True)
            (folder / "build" / "round-1.md").write_text(
                "Built.\n- RELAX: narrow allowed-tools: simpler with Bash\n", encoding="utf-8"
            )
        if cause == "unbuilt":
            (folder / "decisions.md").write_text("# Decisions\n\n" + LEDGER_REVIEWER, "utf-8")
        if cause == "guards":
            (cwd / "src").mkdir(exist_ok=True)
            (cwd / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")

    steps.hooks["carry"] = approve
    real_reply = steps.reply

    def reply(argv, cwd):
        out = real_reply(argv, cwd)
        folder = cwd / ".sdlc" / "work" / cwd.name
        if argv[0] == "agent" and "approve" in argv and cause in ("reconsider", "gate reason"):
            tail = ("\n## Reconsider the approach\n\nSplit it.\n" if cause == "reconsider"
                    else "\n- ESCALATED: gate: the suite fails on main\n")  # fmt: skip
            (folder / "decision.md").write_text(
                decision.replace("READY", "ESCALATE") + tail, encoding="utf-8"
            )
        if argv[0] == "land-check" and cause in ("excluded", "cases"):
            name = out["batch"][0]["change"]
            if cause == "excluded":
                return {"batch": [], "excluded": [{"change": name, "excluded": ["no recover"]}]}
            out["batch"][0].update(signals=["skills' cases in scope: 1"], signal_kinds=["cases"])
        return out

    steps.reply = reply
    if cause == "checks":
        monkeypatch.setattr(
            factory.landing,
            "_checks_now",
            lambda folder, tree: ([{"name": "writes", "command": "rm -rf build"}], None),
        )
    _begin(root, capsys)
    code, out = _loop(root, capsys)
    state = ap.read_state(root)
    first, second = sorted(state["changes"])
    assert state["changes"][first]["place"] == "held", state["changes"][first]
    assert why in state["changes"][first]["why"], state["changes"][first]["why"]
    assert state["changes"][second]["place"] == "waiting", "its dependent never builds"
    assert not [a for c, a in steps.log if c == second]
    assert not steps.ran("train", "--run") or first not in (out["landed"] or [])
    tree = root / ".claude" / "worktrees" / first
    record = (tree / ".sdlc" / "work" / first / "runs" / "autopilot.md").read_text("utf-8")
    assert "held: " in record and why in record
    summary = (root / out["summary"]).read_text(encoding="utf-8")
    assert f"- {first}: " in summary.split("## Held")[1]


def test_autopilot_runs_no_paid_or_unlisted_command(tmp_path, capsys, monkeypatch) -> None:
    """R21: acceptance checks every one of which `read_only_command()` passes run through
    `accept` before the train; one it refuses holds the change; `cases` and `run-cases` never
    run."""
    root, steps = _one_change(tmp_path, capsys, monkeypatch, list(HAPPY))
    monkeypatch.setattr(
        factory.landing,
        "_checks_now",
        lambda folder, tree: ([{"name": "has it", "command": "grep -q keep README.md"}], None),
    )
    _loop(root, capsys)
    assert _only(root)[1]["place"] == "landed"
    accepts = steps.ran("accept")
    assert len(accepts) == 1 and steps.log.index(accepts[0]) < steps.log.index(
        steps.ran("train", "--begin")[0]
    )
    assert not [a for _, a in steps.log if a[0] in ("cases", "run-cases")]


def test_summary_names_every_call_and_no_machine(tmp_path, capsys, monkeypatch) -> None:
    """R22: the summary holds the run's time and cost, what landed, every call autopilot made and
    each budget; every path in it is repo-relative, and a home path in a call's text is a mark."""
    root, steps = _one_change(
        tmp_path,
        capsys,
        monkeypatch,
        ["build", {"next": "decide", "pending": ["D2"]}, "gate", "review", "approve", "done"],
    )
    home = Path.home().as_posix()
    steps.hooks["decisions"] = _writes_ledger(
        LEDGER_BLOCKING.replace("Keep drafts 30 days", f"Keep {home}/drafts 30 days")
        + LEDGER_DEFAULT
    )
    code, out = _loop(root, capsys)
    summary = (root / out["summary"]).read_text(encoding="utf-8")
    name, _, _ = _only(root)
    for said in ("## The run", "cost $", "## Landed", f"- {name}:", "## Calls autopilot made",
                 f"{name} D2 (blocking)", f"{name} D1 (default)", f"{name} {S1} (intent)",
                 "## Budgets", "Review debt: 5 of 12", "Change risk:", "## Risks to weigh",
                 "fixed forward"):  # fmt: skip
        assert said in summary, (said, summary)
    assert home not in summary and str(root) not in summary and "<home>" in summary
    escalations = (root / out["summary"]).with_name("escalations.md").read_text("utf-8")
    assert home not in escalations


def test_a_spent_budget_starts_nothing_and_lands_nothing_more(
    tmp_path, capsys, monkeypatch
) -> None:
    """R27 and the spec's dry run: with `debt = 1` the first intent spends the budget, so one
    seed is opened, taken on to `stage: test`, and left there unlanded; no other wave, intent or
    train starts."""
    root = _repo(tmp_path, "[autopilot]\nenabled = true\ndebt = 1\n")
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts"), S2: _draft("show-drafts")},
                  [[S1, S2], []])  # fmt: skip
    _begin(root, capsys)
    code, out = _loop(root, capsys)
    assert code == 0 and "review debt 1 reached its limit 1" in out["reason"], out
    assert len(steps.ran("agent", "--task", "intent")) == 1
    assert len(steps.ran("agent", "--task", "wave")) == 1
    assert not steps.ran("train") and not steps.ran("land-check")
    name, mine, _ = _only(root)
    assert mine["place"] == "ready" and steps.ran("stage", name[:3], "test")


def test_autopilot_prompt_parts_sent_only_under_the_lock(tmp_path, capsys, monkeypatch) -> None:
    """R20: the builder's prompt asks for `- CONTRACT:` and `- RELAX:` lines, naming the policy
    doc, only in autopilot's run; outside it the prompt is as it was."""
    root = _change(tmp_path)
    sent = []

    def claude(argv, cwd):
        sent.append(argv[argv.index("-p") + 1])
        return 0, ["Built.\n\n## Evidence\n\n$ true\nexit: 0\n"], None, None

    monkeypatch.setattr(factory, "_claude", claude)
    monkeypatch.setattr(factory, "policy_doc", lambda root: ".sdlc/SDLC.md")
    monkeypatch.delenv(factory.AUTOPILOT_RUN_ENV, raising=False)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    assert "- CONTRACT:" not in sent[-1] and "This run is autopilot's" not in sent[-1]
    (root / ".sdlc" / "work" / NAME / "build" / "round-1.md").unlink()
    with _under_lock(root, monkeypatch) as held:
        assert held
        code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    assert "- CONTRACT: <invariant>: <why>" in sent[-1] and "- RELAX:" in sent[-1]
    assert ".sdlc/SDLC.md" in sent[-1]


# ---------------------------------------------------------------- round 1: the env an agent gets


def test_an_agent_session_never_carries_the_loops_markers(tmp_path, capsys, monkeypatch) -> None:
    """R2: an agent `factory.py agent` starts under autopilot's run runs without
    `AUTOPILOT_RUN_ENV` or the train's `TRAIN_RUN_ENV`, so nothing the builder runs with its Bash
    can pass `--by autopilot`; every other variable is passed on."""
    root = _change(tmp_path)
    real, seen = factory.subprocess.run, []

    def run(argv, *a, **k):
        if argv and argv[0] == "claude":
            seen.append(k.get("env"))
            return real(["true"], capture_output=True, encoding="utf-8")
        return real(argv, *a, **k)

    monkeypatch.setattr(factory.subprocess, "run", run)
    monkeypatch.setattr(factory, "policy_doc", lambda root: ".sdlc/SDLC.md")
    monkeypatch.setenv(factory.landing.TRAIN_RUN_ENV, "held")
    monkeypatch.setenv("SDLC_SOMETHING_ELSE", "kept")
    with _under_lock(root, monkeypatch) as held:
        assert held and factory.autopilot_running(root)
        _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert seen, "the session was started"
    env = seen[-1]
    assert env is not None and factory.AUTOPILOT_RUN_ENV not in env
    assert factory.landing.TRAIN_RUN_ENV not in env and env["SDLC_SOMETHING_ELSE"] == "kept"


MARKERS = (factory.AUTOPILOT_RUN_ENV, factory.landing.TRAIN_RUN_ENV)


@pytest.mark.portable
@pytest.mark.parametrize("given", [True, False], ids=["both-set", "neither-set"])
def test_take_markers_moves_both_markers_out_of_the_env(monkeypatch, given) -> None:
    """228 R3: `take_markers()`, `main()`'s first step, moves each loop's marker out of
    `os.environ` into `LOOP_MARKERS`, where `loop_marker()` and `loop_env()` still find it and
    `agent_env()` never does; with neither set it changes nothing."""
    monkeypatch.setattr(factory, "LOOP_MARKERS", {})
    for name in MARKERS:
        if given:
            monkeypatch.setenv(name, f"{name}-value")
        else:
            monkeypatch.delenv(name, raising=False)
    before = dict(factory.os.environ)
    factory.take_markers()
    assert not [n for n in MARKERS if n in factory.os.environ]
    if not given:
        assert factory.LOOP_MARKERS == {} and dict(factory.os.environ) == before
        return
    assert {n: f"{n}-value" for n in MARKERS} == factory.LOOP_MARKERS
    for name in MARKERS:
        assert factory.loop_marker(name) == f"{name}-value"
        assert factory.loop_env()[name] == f"{name}-value"
        assert name not in factory.agent_env()


def test_an_agent_run_reads_the_closes_once(tmp_path, capsys, monkeypatch) -> None:
    """228 R7: one `agent` run reads the ledger's `closes:` rows twice (`recorded_closes()`): once
    for its reading (`loop_state()`'s `intent_closes()`), once to record them (`record_closes()`),
    a small file read twice a session, which a cache would hardly save; never once a line."""
    root = _change(tmp_path)
    intent = root / ".sdlc" / "work" / NAME / "intent.md"
    text = intent.read_text(encoding="utf-8")
    intent.write_text(text.replace("\nidea:", "\ncloses: [12]\nidea:"), encoding="utf-8")
    real, reads = factory.recorded_closes, []
    monkeypatch.setattr(factory, "recorded_closes", lambda f: reads.append(f) or real(f))
    monkeypatch.setattr(factory, "_claude", lambda argv, cwd: (0, ["Done.\n"], None, None))
    monkeypatch.setattr(factory, "policy_doc", lambda root: ".sdlc/SDLC.md")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    assert len(reads) == 2, reads
    assert factory.recorded_closes(root / ".sdlc" / "work" / NAME) == ["[12]"], "it was recorded"


def test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does(
    tmp_path, monkeypatch
) -> None:
    """R2 through the real subprocess path: `run_step` runs `factory.py answer --by autopilot` as a
    child under the loop's env and it is accepted while the lock is held; the same command run
    by an agent session, the stand-in `claude` `_claude()` starts (228 R4), is refused, as it is
    with the lock free."""
    root = _change(tmp_path / "host")
    said = tmp_path / "agent-answer.out"
    script = shlex.join([factory.sys.executable, str(factory.FACTORY_SCRIPT), "answer", "008", "D2",
                         "--by", "autopilot"])  # fmt: skip
    fake_claude(
        tmp_path,
        monkeypatch,
        {"builder": {"run": ["sh", "-c", f"{script} > {shlex.quote(str(said))} 2>&1"]}},
    )
    folder = root / ".sdlc" / "work" / NAME
    _ledger(folder, DEFAULT_LINE, DEFAULT_LINE.replace("D1", "D2").replace("50", "60"))
    argv = ["answer", "008", "D1", "--by", "autopilot"]
    monkeypatch.delenv(factory.AUTOPILOT_RUN_ENV, raising=False)
    free = ap.run_step(root, argv, root)
    assert free["code"] == 1 and factory.BY_AUTOPILOT_REFUSED in free["out"]["refusals"], free
    with ap.autopilot_lock(root) as held:
        assert held
        monkeypatch.setenv(
            factory.AUTOPILOT_RUN_ENV, str(_common(root) / factory.AUTOPILOT_RUN_LOCK)
        )
        code, replies, problem, _ = factory._claude(
            ["claude", "-p", "answer D2", "--agent", "sdlc-factory:builder"], root
        )
        assert code == 0 and problem is None, problem
        agent = json.loads(said.read_text(encoding="utf-8"))
        assert factory.BY_AUTOPILOT_REFUSED in agent["refusals"], agent
        ok = ap.run_step(root, argv, root)
    assert ok["code"] == 0 and ok["out"]["answer"] == factory.KEPT_ANSWER, ok
    ledger = {d["id"]: d for d in factory.read_ledger(folder)}
    assert ledger["D1"]["decided_by"] == "autopilot" and ledger["D2"]["open"]


@needs_uv
def test_candidates_come_from_the_real_status_json(tmp_path) -> None:
    """R10 through the real `sdlc.py` (no stand-in for `_sdlc`): `status --json` gives `next_up`'s
    items, and the candidates are its ready group: a high bug is one, a plain idea isn't."""
    root = _repo(tmp_path)
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Inbox\n\n> The register.\n\n"
        f"## [{S1}] [bug] The drafts list crashes\n\nSeverity: high\n\nIt crashes.\n\n"
        f"## [{S2}] [idea] Show kept drafts\n\nList them.\n\n"
        f"## [{S3}] [bug] The export drops a column\n\nSeverity: high\nIssue: #7\n\nIt drops.\n",
        encoding="utf-8",
    )  # fmt: skip
    _git(root, "commit", "-qam", "register")
    items, why = ap.status_items(root)
    assert why is None and {i["id"] for i in items} == {S1, S2, S3}, (why, items)
    assert {i["id"]: i["issues"] for i in items} == {S1: [], S2: [], S3: [7]}
    found = ap.candidates(items, ap.bounds_of(None, None, 5, 1, None))
    assert [i["id"] for i in found] == [S1], "a seed with an issue only when named"
    found = ap.candidates(items, ap.bounds_of([S3], None, 5, 1, None))
    assert [i["id"] for i in found] == [S3]


# ---------------------------------------------------------------- round 2: the change's own code


CHECKS = """# Checks

> The change's acceptance checks.

## It reads its env

The command writes the env it ran with outside the tree.

```sh
env > {out}
```
"""


@needs_uv
def test_the_changes_own_code_never_runs_as_a_loops_child(tmp_path, monkeypatch) -> None:
    """R2: a step the loop runs as its own child (`run_step`) holds the marker, but the host's
    check its `gate` runs, and the acceptance checks its `accept` runs through `sdlc.py`, never
    do: `factory.py` takes the markers out of its own env as it starts, so the change's tests, its
    checks and any git hook it wrote can't pass `--by autopilot`."""
    root = _change(tmp_path / "repo")
    seen = tmp_path / "seen"
    seen.mkdir()
    gate_env, check_env = seen / "gate.env", seen / "check.env"
    _gate_config(root, f"env > {gate_env.as_posix()}")
    _build_report(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "checks.md").write_text(CHECKS.format(out=check_env.as_posix()), encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "the change")
    monkeypatch.setenv(factory.landing.TRAIN_RUN_ENV, "held")
    with ap.autopilot_lock(root) as held:
        assert held
        gate = ap.run_step(root, ["gate", "008"], root)
        accept = ap.run_step(root, ["accept", "008"], root)
    assert gate["out"] and gate["out"]["verdict"] == "PASS", gate
    assert accept["out"] and accept["out"].get("verdict") == "PASS", accept
    for path in (gate_env, check_env):
        text = path.read_text(encoding="utf-8")
        assert "PATH=" in text, path.name
        assert factory.AUTOPILOT_RUN_ENV not in text, path.name
        assert factory.landing.TRAIN_RUN_ENV not in text, path.name


# ---------------------------------------------------------------- a parked change (222)


class ParkClock:
    """A stand-in clock for the loop, moving only when it pauses, and each pause's length."""

    def __init__(self, monkeypatch) -> None:
        from datetime import UTC, datetime

        self.when = datetime.now(UTC).replace(microsecond=0)
        self.pauses: list[float] = []
        monkeypatch.setattr(ap, "_now", lambda: self.when)
        monkeypatch.setattr(ap, "_pause", self.pause)

    def pause(self, seconds: float) -> None:
        from datetime import timedelta

        self.pauses.append(seconds)
        self.when += timedelta(seconds=seconds)

    def at(self, minutes: float) -> str:
        from datetime import timedelta

        return (self.when + timedelta(minutes=minutes)).strftime(ap.TIME_FORMAT)


def test_autopilot_waits_out_a_park_and_holds_past_its_deadline(
    tmp_path, capsys, monkeypatch
) -> None:
    """222 R15: a parked reading runs no command and keeps `retry` and `deadline` on the change;
    the loop neither ends nor reads again before the retry, sleeping in slices of at most 30 s,
    then gates and lands it. Past the deadline, the stop holds it with the holder named."""
    clock = ParkClock(monkeypatch)
    retry, deadline = clock.at(5), clock.at(60)
    park = {"resource": "staging db", "holder": "219-other", "since": clock.at(0),
            "retry": retry, "deadline": deadline, "attempts": 1}  # fmt: skip
    root, steps = _one_change(
        tmp_path, capsys, monkeypatch,
        ["build", {"next": "parked", "parked": park}, "gate", "review", "approve", "done"],
    )  # fmt: skip
    reads, kept = [], []
    steps.hooks["verdicts"] = lambda argv, cwd: reads.append(clock.when.strftime(ap.TIME_FORMAT))

    def gated(argv, cwd):
        kept.append({k: v for k, v in ap.read_state(root)["changes"].items()})

    steps.hooks["gate"] = gated
    code, out = _loop(root, capsys)
    assert code == 0, out
    name, mine, _ = _only(root)
    assert mine["place"] == "landed", mine
    assert len([r for r in reads if r < retry]) == 2, ("build, then parked: no more", reads)
    assert reads[2] >= retry, reads
    assert clock.pauses and max(clock.pauses) <= ap.PARK_SLICE, clock.pauses
    assert kept and kept[0][name]["retry"] == retry and kept[0][name]["deadline"] == deadline
    assert "retry" not in mine, "a reading that isn't parked clears it"

    clock2 = ParkClock(monkeypatch)
    soon = {**park, "retry": clock2.at(1), "deadline": clock2.at(2)}
    problem = "parked past its deadline: staging db is still held by 219-other after 3 attempts"
    root2, steps2 = _one_change(
        tmp_path / "two", capsys, monkeypatch,
        ["build", {"next": "parked", "parked": soon},
         {"next": "stop", "way": "parked", "problems": [problem]}],
    )  # fmt: skip
    _loop(root2, capsys)
    _, mine2, _ = _only(root2)
    assert mine2["place"] == "held" and "219-other" in mine2["why"], mine2
    assert not steps2.ran("train", "--run") and not steps2.ran("gate")


# ---------------------------------------------------------------- the whole loop, as it runs
#
# 228 R1, R2: `autopilot --begin` and `--run` as subprocesses of the test, nothing monkeypatched
# in them: every step a real `factory.py` child, `sdlc.py` run through `uv`, the stand-in `claude`
# first on PATH answering each agent, and the landing's real `ship` and `close` on a scratch host.

SEED = "2026-11-22-1"
ONE_SEED = (
    "# Inbox\n\n> The register.\n\n"
    f"## [{SEED}] [bug] The drafts list crashes\n\nSeverity: high\n\nIt crashes.\n"
)
PLAN = f"## Drafts crash\n\n- WAVE: {SEED} — tier 1 — it shares no file with the rest\n"
# The option the builder recommends, which autopilot answers on its own.
RECOMMENDED = "keep it"
BUILDER_RAISES = (
    "Built it.\n\n"
    f"- DECISION: [blocking] Keep a crashed draft, or drop it? Recommend {RECOMMENDED}.\n"
    f"  - OPTION: {RECOMMENDED} — nothing lost; the list holds a broken entry\n"
    "  - OPTION: drop it — a clean list; the draft is gone\n"
    "  - WHY: the intent says nothing is lost\n\n"
    "## Evidence\n\n$ true\nexit: 0\n"
)


def _whole_host(tmp_path: Path) -> tuple[Path, Path]:
    """A scratch host on `main` with one seed, `[autopilot]` on and a check that writes its env
    under the returned directory, outside the tree, one file a run (its shell's pid); no remote.
    The check is plain `sh`, so the gate's record holds no interpreter's path under a home
    directory, which the scan refuses in a change's folder."""
    root, seen = tmp_path / "host", tmp_path / "check-envs"
    root.mkdir()
    seen.mkdir()
    (root / "README.md").write_text("one\ntwo\nthree\n", encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(ONE_SEED, encoding="utf-8")
    (root / ".sdlc" / "factory.toml").write_text(ENABLED, encoding="utf-8")
    check = f"env > {shlex.quote(seen.as_posix())}/check-$$.env"
    (root / ".sdlc" / "config.toml").write_text(
        f"[commands]\ncheck = {json.dumps(check)}\n", encoding="utf-8"
    )
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root, seen


def _autopilot(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in factory.os.environ.items() if k not in ("VIRTUAL_ENV", *MARKERS)}
    return subprocess.run(
        [factory.sys.executable, str(factory.FACTORY_SCRIPT), "autopilot", *args],
        cwd=root, env=env, capture_output=True, encoding="utf-8", timeout=600,
    )  # fmt: skip


def test_fake_claudes_marker_names_are_the_factorys() -> None:
    """228 R2: the stand-in `claude` names the loops' markers in full, since it can't import the
    factory; a rename of either fails here, never silently in the end-to-end test."""
    from train_driver import FAKE_CLAUDE

    assert f'("{factory.AUTOPILOT_RUN_ENV}", "{factory.landing.TRAIN_RUN_ENV}")' in FAKE_CLAUDE


@needs_uv
@pytest.mark.skipif(factory.os.name == "nt", reason="the stand-in claude is a shebang file")
def test_autopilot_run_lands_a_seed_through_real_subprocesses(tmp_path, monkeypatch) -> None:
    """228 R1: one seed, opened, built, its blocking line answered by a real `answer --by
    autopilot`, gated, reviewed, approved and landed by `autopilot --run`, every step its own
    child: `Close` on main, `Sdlc-Landed: by=autopilot`, `opened_by: autopilot`, and only
    `→ decided by autopilot:` in the ledger. R2: the host's check, run by the loop's gate and the
    train's, and every agent session, saw neither loop's marker."""
    for name in MARKERS:
        monkeypatch.delenv(name, raising=False)
    root, seen = _whole_host(tmp_path)
    calls = fake_claude(tmp_path, monkeypatch, {
        "autopilot-planner": {"reply": PLAN, "once": True, "then_reply": "NONE\n"},
        "intent-writer": {"reply": _draft("drafts-crash")},
        "builder": {"once": True, "write": {"keep.txt": "kept\n"}, "reply": BUILDER_RAISES},
        "approver": {"reply": READY_DECISION},
    })  # fmt: skip
    begun = _autopilot(
        root, "--begin", "--usd", "5", "--hours", "1", "--goal", "Keep drafts working"
    )
    assert begun.returncode == 0, begun.stdout + begun.stderr
    ran = _autopilot(root, "--run")
    state = ap.read_state(root)
    changes = (state or {}).get("changes") or {}
    assert ran.returncode == 0 and len(changes) == 1, (ran.stdout, ran.stderr[-3000:], state)
    ((name, mine),) = changes.items()
    record = root / ".claude" / "worktrees" / name / ".sdlc" / "work" / name / "runs"
    held = (record / "autopilot.md").read_text("utf-8") if record.is_dir() else ""
    assert mine["place"] == "landed", (mine, held, ran.stderr[-3000:])

    line = _git(root, "log", "--first-parent", "--format=%s", "main").splitlines()
    assert f"Close {name}" in line, line
    bodies = _git(root, "log", "--format=%B", "main")
    assert "Sdlc-Landed: by=autopilot" in bodies, bodies
    last = _git(root, "log", "--format=%H", "-1", "main", "--", f".sdlc/work/{name}/intent.md")
    intent = _git(root, "show", f"{last}^:.sdlc/work/{name}/intent.md")
    ledger = _git(root, "show", f"{last}^:.sdlc/work/{name}/decisions.md")
    assert re.search(r"^opened_by: autopilot$", intent, re.M), intent
    assert f"{factory.DECIDED_AUTOPILOT}{RECOMMENDED}" in ledger, ledger
    assert factory.DECIDED not in ledger, ledger
    agents = {c["agent"] for c in calls()}
    assert {"autopilot-planner", "intent-writer", "builder", "approver"} <= agents, agents

    envs = sorted(seen.iterdir())
    assert len(envs) >= 2, "the loop's gate and the train's tip gate each ran the check"
    for path in envs:
        text = path.read_text(encoding="utf-8")
        assert "PATH=" in text, path.name
        assert not [m for m in MARKERS if f"{m}=" in text], path.name
    assert [c for c in calls() if c["markers"]] == [], "no agent session held a marker"


# ---------------------------------------------------------------- 231: a run toward a goal

DIRECTION = """# Direction

> The doc.

## Goals

- G1. No one loses a draft (O1)
- ~~G2. Drafts shared between accounts~~ Dropped: nobody asked
- G3. Logs stay small

## Milestones

### M1. Drafts reopen where they were left

Groups: "Keep drafts", 2026-11-21-2, 2026-01-01-9, 006

Serves: G1, O1

### ~~M2. Drafts sync every hour~~ Dropped: not wanted

Groups: 2026-11-21-3

### M3. Logs are trimmed

Groups: 2026-11-21-3

Serves: G3
"""


@needs_uv
def test_goals_come_from_the_real_status_json(tmp_path) -> None:
    """R1 through the real `sdlc.py`: `status --json` gives `direction`, its open goals and
    milestones, a milestone's grouped seeds resolved to the register's open ids (a quoted title
    to its id, a seed no longer in the register left out), never a struck item; with no doc,
    every list is empty."""
    root = _repo(tmp_path)
    code, data, said = factory._sdlc(["status", "--json"], root)
    assert code == 0, said
    assert data["direction"] == {"goals": [], "milestones": [], "problems": []}
    (root / ".sdlc" / "DIRECTION.md").write_text(DIRECTION, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "direction")
    code, data, said = factory._sdlc(["status", "--json"], root)
    assert code == 0, said
    direction = data["direction"]
    assert [g["id"] for g in direction["goals"]] == ["G1", "G3"], "never a struck goal"
    assert direction["goals"][0]["serves"] == ["O1"]
    assert {"id", "name", "title", "serves"} <= set(direction["goals"][0])
    assert [m["id"] for m in direction["milestones"]] == ["M1", "M3"], "never a struck milestone"
    m1, m3 = direction["milestones"]
    assert m1["seeds"] == [S1, S2], "a title resolved to its id; a gone seed left out"
    assert m1["serves"] == ["G1", "O1"] and m3["seeds"] == [S3]
    assert m1["title"] == "Drafts reopen where they were left"
    assert direction["problems"] == []
    items, why = ap.status_items(root)
    assert why is None and items, "next_up is still read"


GOAL_ITEMS = [
    {"id": S1, "title": "Keep drafts", "group": "ready", "label": "idea", "theme": "drafts"},
    {"id": S2, "title": "Show kept drafts", "group": "ready", "label": "idea", "theme": "drafts"},
    {"id": S3, "title": "Trim logs", "group": "ready", "label": "idea", "theme": "logs"},
    {"id": "2026-11-21-4", "title": "Rotate logs", "group": "ready", "label": "idea",
     "theme": "logs"},
    {"id": "2026-11-21-5", "title": "Colour tabs", "group": "decide", "label": "idea",
     "theme": "tabs"},
]  # fmt: skip
GOAL_DIRECTION = {
    "goals": [{"id": "G1", "name": "", "title": "No one loses a draft (O1)", "serves": ["O1"]},
              {"id": "G3", "name": "", "title": "Logs stay small", "serves": []},
              {"id": "G4", "name": "Fast", "title": "Pages are fast", "serves": []}],
    "milestones": [{"id": "M1", "name": "", "title": "Drafts reopen", "serves": ["G1", "O1"],
                    "seeds": [S2, S1]},
                   {"id": "M3", "name": "", "title": "Logs are trimmed", "serves": ["G3"],
                    "seeds": [S3]}],
    "problems": [],
}  # fmt: skip


def test_a_goal_is_read_by_its_form() -> None:
    """R2: `G<n>`/`M<n>` an open item of the direction doc, `theme:<name>` a register theme, any
    other text the person's own; an id the doc doesn't hold open is refused."""
    goal, why = ap.resolve_goal("M1", GOAL_DIRECTION, GOAL_ITEMS)
    assert why is None and goal["source"] == "direction" and goal["arg"] == "M1"
    assert goal["title"] == "Drafts reopen" and goal["serves"] == ["G1", "O1"]
    goal, why = ap.resolve_goal("G1", GOAL_DIRECTION, GOAL_ITEMS)
    assert goal["source"] == "direction" and goal["title"] == "No one loses a draft", goal
    assert ap.resolve_goal("G4", GOAL_DIRECTION, GOAL_ITEMS)[0]["title"] == "Fast", "its name"
    goal, why = ap.resolve_goal("theme:logs", GOAL_DIRECTION, GOAL_ITEMS)
    assert goal["source"] == "register" and goal["arg"] == "theme:logs", goal
    goal, why = ap.resolve_goal("Make drafts fast", GOAL_DIRECTION, GOAL_ITEMS)
    assert goal["source"] == "stated" and goal["title"] == "Make drafts fast", goal
    goal, why = ap.resolve_goal("m1 and more", GOAL_DIRECTION, GOAL_ITEMS)
    assert goal["source"] == "stated", "only the bare id is an id"
    for struck in ("M2", "G2", "M999"):
        goal, why = ap.resolve_goal(struck, GOAL_DIRECTION, GOAL_ITEMS)
        assert goal is None and "isn't an open goal or milestone in the direction doc" in why
    assert ap.resolve_goal("  ", GOAL_DIRECTION, GOAL_ITEMS) == (None, None), "no goal"
    assert ap.resolve_goal("theme:", GOAL_DIRECTION, GOAL_ITEMS)[1], "a theme needs a name"


def test_a_goal_only_narrows_the_candidates() -> None:
    """R3: each goal's scope; the candidates with a goal are a subset of those without it, in
    the same order, and the config's guards and the holds never read a goal."""
    import inspect

    bounds = ap.bounds_of(None, None, 5, 1, None)
    every = [i["id"] for i in ap.candidates(GOAL_ITEMS, bounds)]
    scopes = {
        "M1": [S2, S1],
        "M3": [S3],
        "G1": [S2, S1],
        "G3": [S3],
        "G4": None,
        "theme:logs": [S3, "2026-11-21-4"],
        "theme:tabs": [],
        "Make it fast": None,
    }
    for arg, scope in scopes.items():
        goal, why = ap.resolve_goal(arg, GOAL_DIRECTION, GOAL_ITEMS)
        assert why is None, (arg, why)
        assert goal["scope"] == scope, (arg, goal["scope"])
        got = [i["id"] for i in ap.candidates(GOAL_ITEMS, bounds, None, goal)]
        assert set(got) <= set(every) and got == [i for i in every if i in got], arg
        if scope is not None:
            assert set(got) == set(scope) & set(every), arg
    themed = ap.bounds_of(None, ["drafts"], 5, 1, None)
    goal = ap.resolve_goal("theme:logs", GOAL_DIRECTION, GOAL_ITEMS)[0]
    assert ap.candidates(GOAL_ITEMS, themed, None, goal) == [], "the bounds still apply"
    for fn in (ap.autopilot_config, ap.hold_causes, ap._default_guards):
        assert "goal" not in inspect.signature(fn).parameters, fn.__name__


def test_the_preview_proposes_a_goal_when_none_is_stated() -> None:
    """R4: the first open milestone, in the doc's order, with a candidate within the bounds; else
    the theme with the most candidates (a tie to the best-ranked); else none. Up to three
    alternatives, each with its count."""
    every = ap.bounds_of(None, None, 5, 1, None)
    goal, alts = ap.propose_goal(GOAL_DIRECTION, GOAL_ITEMS, every)
    assert goal["arg"] == "M1" and goal["source"] == "direction", goal
    assert [a["arg"] for a in alts] == ["M3", "G1", "G3"], alts
    assert [a["count"] for a in alts] == [1, 2, 1]
    # M1's seeds outside the bounds: a milestone with no candidate is never proposed.
    logs = ap.bounds_of(None, ["logs"], 5, 1, None)
    goal, alts = ap.propose_goal(GOAL_DIRECTION, GOAL_ITEMS, logs)
    assert goal["arg"] == "M3", "the first milestone with a candidate"
    assert "M1" not in [a["arg"] for a in alts]
    # No milestone qualifies: the theme with the most candidates.
    no_milestones = {**GOAL_DIRECTION, "milestones": [], "goals": []}
    more = [*GOAL_ITEMS, {"id": "2026-11-21-6", "title": "Cap logs", "group": "ready",
                          "theme": "logs"}]  # fmt: skip
    goal, alts = ap.propose_goal(no_milestones, more, every)
    assert goal["arg"] == "theme:logs" and goal["source"] == "register", goal
    assert [a["arg"] for a in alts] == ["theme:drafts"]
    goal, alts = ap.propose_goal({**GOAL_DIRECTION, "milestones": []}, more, every)
    assert goal["arg"] == "theme:logs" and [a["arg"] for a in alts] == ["G1", "G3", "G4"], (
        "goals before themes; a goal no milestone serves has every candidate in scope"
    )
    # A tie goes to the theme whose best candidate ranks highest: drafts holds the first item.
    goal, _ = ap.propose_goal(no_milestones, GOAL_ITEMS, every)
    assert goal["arg"] == "theme:drafts", goal
    assert len(ap.propose_goal(GOAL_DIRECTION, more, every)[1]) <= 3
    # No candidate anywhere: no goal.
    assert ap.propose_goal(GOAL_DIRECTION, GOAL_ITEMS[-1:], every) == (None, [])


def test_the_preview_names_a_goal_from_the_direction_doc(
    tmp_path, capsys, monkeypatch, no_env
) -> None:
    """R5: the question and `shown` name the proposed milestone, its source and the
    alternatives; `--goal` with an id the doc doesn't hold open refuses; a doc's problem and a
    goal with no candidate are warnings, never refusals; no goal to propose is a warning."""
    root = _change(tmp_path)
    _on_main(root, ENABLED)
    direction = {**GOAL_DIRECTION, "problems": ["G5 is used twice"]}
    items = GOAL_ITEMS

    def run(args, cwd):
        if args[0] == "config":
            return 0, DOCS, ""
        return 0, {"next_up": {"items": items}, "direction": direction}, ""

    monkeypatch.setattr(factory, "_sdlc", run)
    code, out = _run(capsys, ap.cmd_autopilot, root, "preview", None, None, 9.0, 2.0, None)
    assert code == 0, out
    assert out["question"].startswith('Run autopilot toward M1 "Drafts reopen" (direction) until')
    assert out["goal"] == {"source": "direction", "arg": "M1", "title": "Drafts reopen",
                           "serves": ["G1", "O1"], "count": 2}  # fmt: skip
    shown = out["shown"]
    assert shown.startswith("Goal:\n"), shown
    for said in ("M1", "the direction doc", "M3", "a new --preview"):
        assert said in shown.split("Bounds:")[0], said
    assert any("G5 is used twice" in w for w in out["warnings"])
    assert [i["id"] for i in out["candidates"]] == [S1, S2], "the goal's own"
    code, out = _run(
        capsys, ap.cmd_autopilot, root, "preview", None, None, 9.0, 2.0, None, "theme:tabs"
    )
    assert code == 0 and out["goal"]["count"] == 0, out
    assert any("no candidate" in w for w in out["warnings"]), out["warnings"]
    code, out = _run(capsys, ap.cmd_autopilot, root, "preview", None, None, 9.0, 2.0, None, "M999")
    assert code == 1 and "isn't an open goal or milestone" in out["refusals"][0], out
    items = GOAL_ITEMS[-1:]
    code, out = _run(capsys, ap.cmd_autopilot, root, "preview", None, None, 9.0, 2.0, None)
    assert code == 0 and out["goal"] is None and ap.NO_GOAL in out["warnings"], out
    assert out["question"] is None, "no question to ask without a goal"


def _goal_state(goal: dict | None, level: int = 2) -> dict:
    state = {"bounds": ap.bounds_of(None, None, 5, 1, level), "changes": {}}
    return {**state, "goal": goal} if goal is not None else state


def test_the_wave_brief_names_the_goal() -> None:
    """R7, R12: the brief holds `## Goal` (its source, id, title and what it serves) and
    `Level:` before the candidates; a run begun before goals says it has none."""
    goal = ap.resolve_goal("M1", GOAL_DIRECTION, GOAL_ITEMS)[0]
    brief = ap.wave_brief(_goal_state(goal, 1), GOAL_ITEMS[:2], 2, None)
    head, _, tail = brief.partition("## Candidates")
    assert tail and "## Goal" in head and "Level: 1" in head, brief
    for said in ("direction", "M1", "Drafts reopen", "G1, O1"):
        assert said in head.split("## Goal")[1], said
    old = ap.wave_brief(_goal_state(None), GOAL_ITEMS[:2], 2, None)
    assert "Goal: none (begun before goals)" in old.partition("## Candidates")[0]


def _reply(tmp_path: Path, text: str) -> dict:
    to = Path(".sdlc") / "reports" / "reply.md"
    (tmp_path / to).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / to).write_text(text, encoding="utf-8")
    return {"out": {"to": to.as_posix()}}


GOOD_PLAN = f"""# Plan

## The drafts list crashing loses work

- WAVE: {S1} — tier 1 — first: `src/drafts.py` is shared with {S2}
- WAITS: {S2} — touches `src/drafts.py` too, after {S1}

- LEAVE: {S3} — fixed — `src/logs.py` trims already
"""


def test_the_planner_places_every_candidate(tmp_path) -> None:
    """R8: a reply is groups of WAVE and WAITS lines, LEAVE lines anywhere; the script refuses a
    candidate placed nowhere or twice, a line outside a group, a WAVE with no tier or one past the
    level, an empty reason, a fixed or wrong LEAVE citing no path in the main checkout, a seed that
    isn't a candidate, and more WAVE lines than the room."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "logs.py").write_text("x = 1\n", encoding="utf-8")
    found = [{"id": S1}, {"id": S2}, {"id": S3}]
    plan, why = ap.read_plan(tmp_path, _reply(tmp_path, GOOD_PLAN), found, 2, 2)
    assert why is None, why
    assert plan["wave"] == [
        {
            "seed": S1,
            "tier": 1,
            "why": f"first: `src/drafts.py` is shared with {S2}",
            "group": "The drafts list crashing loses work",
        }
    ]
    assert plan["waits"] == [
        {
            "seed": S2,
            "why": f"touches `src/drafts.py` too, after {S1}",
            "group": "The drafts list crashing loses work",
        }
    ]
    assert plan["leave"] == [{"seed": S3, "kind": "fixed", "why": "`src/logs.py` trims already"}]
    assert [g["risk"] for g in plan["groups"]] == ["The drafts list crashing loses work"]
    # 235 R29: a LEAVE line before any group is read as any other.
    first = f"- LEAVE: {S3} — fixed — `src/logs.py` trims already\n\n" + GOOD_PLAN.replace(
        f"- LEAVE: {S3} — fixed — `src/logs.py` trims already\n", ""
    )
    assert first.index("- LEAVE:") < first.index("## ")
    plan, why = ap.read_plan(tmp_path, _reply(tmp_path, first), found, 2, 2)
    assert why is None, why
    assert [e["seed"] for e in plan["leave"]] == [S3]
    empty = GOOD_PLAN.replace(f"- WAVE: {S1} — tier 1 —", f"- WAITS: {S1} —")
    plan, why = ap.read_plan(tmp_path, _reply(tmp_path, empty), found, 2, 2)
    assert why is None and plan["wave"] == [], "an empty wave is no WAVE line"
    bad = {
        "placed nowhere": GOOD_PLAN.replace(f"- WAITS: {S2} — touches `src/drafts.py` too, after "
                                            f"{S1}\n", ""),
        "placed twice": GOOD_PLAN + f"- LEAVE: {S2} — off-goal — not drafts\n",
        "outside a group": f"- WAVE: {S1} — tier 1 — first\n" + GOOD_PLAN.replace(
            f"- WAVE: {S1} — tier 1 — first: `src/drafts.py` is shared with {S2}\n", ""),
        "no tier": GOOD_PLAN.replace("— tier 1 ", ""),
        "past the level": GOOD_PLAN.replace("tier 1", "tier 2"),
        "empty reason": GOOD_PLAN.replace("after " + S1, "").replace("too, ", "").replace(
            "touches `src/drafts.py`", ""),
        "no path": GOOD_PLAN.replace("`src/logs.py`", "the code"),
        "a path not there": GOOD_PLAN.replace("src/logs.py", "src/gone.py"),
        "a path outside": GOOD_PLAN.replace("`src/logs.py`", "../src/logs.py"),
        "no kind": GOOD_PLAN.replace("— fixed —", "— done —"),
        "not a candidate": GOOD_PLAN + "- LEAVE: 2026-01-01-9 — off-goal — not ours\n",
        "past the room": GOOD_PLAN.replace(f"- WAITS: {S2} —", f"- WAVE: {S2} — tier 1 —"),
        "NONE": "NONE\n",
        "empty WAVE reason": GOOD_PLAN.replace(
            f"tier 1 — first: `src/drafts.py` is shared with {S2}", "tier 1 —"),
        "empty LEAVE reason": GOOD_PLAN.replace("— fixed — `src/logs.py` trims already",
                                                "— fixed —"),
    }  # fmt: skip
    said = {"placed nowhere": f"placed in no line: {S2}", "placed twice": f"placed twice: {S2}",
            "outside a group": "outside a `## <risk>` group", "no tier": "has no `tier <1|2>`",
            "past the level": "tier 2, past the level 1", "empty reason": "gives no reason",
            "no path": "names no repo path", "a path not there": "names no repo path",
            "a path outside": "names no repo path", "no kind": "needs a kind",
            "not a candidate": "not candidates: 2026-01-01-9",
            "past the room": "past the room for 1", "NONE": f"placed in no line: {S1}",
            "empty WAVE reason": "gives no reason",
            "empty LEAVE reason": "gives no reason"}  # fmt: skip
    for case, text in bad.items():
        level, room = (
            (1, 2) if case == "past the level" else (2, 1 if case == "past the room" else 2)
        )
        plan, why = ap.read_plan(tmp_path, _reply(tmp_path, text), found, room, level)
        assert plan is None and why and said[case] in why, (case, why)


def test_a_seed_the_planner_leaves_is_left_for_the_person(tmp_path, capsys, monkeypatch) -> None:
    """R9: a seed the planner leaves as fixed is kept in the state with its kind and reason, never
    opened, never offered to a later wave, and the register and the direction doc are byte for
    byte as they were; the summary lists it as the person's, retired by none."""
    root = _repo(tmp_path)
    (root / ".sdlc" / "DIRECTION.md").write_text(DIRECTION, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "direction")
    kept = {p: (root / p).read_bytes() for p in (".sdlc/work/inbox.md", ".sdlc/DIRECTION.md")}
    leave = {S3: "fixed — `.gitignore` already keeps it out"}
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts")},
                  [{"wave": [S1], "leave": leave}, []], {"keep-drafts": ["stop"]})  # fmt: skip
    _begin(root, capsys)
    code, out = _loop(root, capsys)
    assert code == 0, out
    state = ap.read_state(root)
    assert state["seeds"][S3] == {"change": None, "why": "fixed: `.gitignore` already keeps it out",
                                  "left": "fixed"}, state["seeds"]  # fmt: skip
    assert not steps.ran("agent", "--task", "intent", "--seed", S3), "never opened"
    assert len(steps.briefs) == 2 and S3 not in steps.briefs[1], "never offered again"
    assert S2 in steps.briefs[1], "a seed that waits is offered again"
    assert {p: (root / p).read_bytes() for p in kept} == kept, "neither file changes"
    assert out["left"] == {S3: {"kind": "fixed", "why": "`.gitignore` already keeps it out"}}
    assert S3 not in out["seeds_held"], "left, not held"
    summary = (root / out["summary"]).read_text(encoding="utf-8")
    left = summary.split("## Left for you")[1].split("\n## ")[0]
    assert S3 in left and ".gitignore" in left and "retired none" in left, left


def test_the_intent_brief_carries_the_plan(tmp_path, capsys, monkeypatch) -> None:
    """R10: the intent brief gets the WAVE line's tier, group and reason after the register
    entry; the intent-writer's own tier still decides (2 here, against the planner's 1)."""
    root = _repo(tmp_path)
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts", tier=2)}, [[S1], []],
                  {"keep-drafts": ["stop"]})  # fmt: skip
    steps.items = SEEDS[:1]
    _begin(root, capsys)
    _loop(root, capsys)
    run = next((root / ".sdlc" / "reports" / "autopilot").iterdir())
    brief = (run / "briefs" / f"intent-{S1}.md").read_text(encoding="utf-8")
    entry, _, planned = brief.partition("Planned: ")
    assert f"[{S1}] [idea] Keep drafts" in entry, brief
    assert planned.strip() == "tier 1, Drafts get lost: it shares no file with the rest", brief
    (name,) = ap.read_state(root)["changes"]
    assert ap.read_state(root)["changes"][name]["tier"] == 2, "the draft's tier decides"


def _register(root: Path, *ids: str) -> None:
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Inbox\n\n> The register.\n\n"
        + "".join(f"## [{i}] [idea] Seed {i}\n\nIt.\n\n" for i in ids),
        encoding="utf-8",
    )


def test_the_summary_says_whether_the_register_grew(tmp_path) -> None:
    """R11: the summary counts the register's ids at the start and the end, `filed` (new at the
    end) and `drained` (gone), says the register grew faster than the run drained it only when
    more were filed, and gives the goal and each plan as data and in its sections."""
    root = _repo(tmp_path)
    a, b, c, d, e = (f"2026-11-21-{n}" for n in range(11, 16))
    goal = ap.resolve_goal("M1", GOAL_DIRECTION, GOAL_ITEMS)[0]
    plan = {"groups": [{"risk": "Drafts get lost", "wave": [{"seed": a, "tier": 1, "why": "first",
                                                           "group": "Drafts get lost"}],
                        "waits": [{"seed": b, "why": "after a", "group": "Drafts get lost"}]}],
            "wave": [], "waits": [{"seed": b, "why": "after a", "group": "Drafts get lost"}],
            "leave": [{"seed": c, "kind": "off-goal", "why": "about logs"}]}  # fmt: skip
    state = {"id": "20261122T000000Z", "started": "2026-11-22T00:00:00Z", "bounds": {},
             "config": _config(), "goal": goal, "register": {"start": [a, b, c]},
             "plans": [plan], "seeds": {}, "changes": {}, "calls": []}  # fmt: skip
    cases = {"grew": ([b, c, d, e], 2, 1, True), "even": ([b, c, d], 1, 1, False),
             "drained": ([c], 0, 2, False)}  # fmt: skip
    for case, (end, filed, drained, grew) in cases.items():
        _register(root, *end)
        data = ap.summary(root, state)
        reg = data["register"]
        assert (reg["start"], reg["end"]) == (3, len(end)), case
        assert (len(reg["filed"]), len(reg["drained"]), reg["grew"]) == (filed, drained, grew), case
        assert data["goal"]["arg"] == "M1" and data["plans"] == [plan]
        text = ap.write_summary(root, state).read_text(encoding="utf-8")
        line = "The register grew faster than this run drained it"
        assert (line in text.split("## The run")[1].split("\n## ")[0]) is grew, (case, text)
        assert f"{filed} filed" in text and f"{drained} drained" in text, case
    for said in ("## Goal", 'M1 "Drafts reopen"', "from the direction doc", "## The plan",
                 f"{a} at tier 1 (first)", f"Waits: {b}: after a", f"{c}: about logs",
                 "## Left for you"):  # fmt: skip
        assert said in text, (said, text)
    state["register"]["end"] = [a]
    _register(root, a, b, c, d, e)
    assert ap.summary(root, state)["register"]["end"] == 1, "an ended run's count is kept"


def test_a_run_begun_without_a_goal_resumes(tmp_path, capsys, monkeypatch) -> None:
    """R12: a state written before goals (no `goal`, `register` or `plans`) runs as before: the
    brief says it has no goal, every candidate is offered, and the summary says the register
    wasn't counted."""
    root = _repo(tmp_path)
    steps = Steps(root, monkeypatch, {S1: _draft("keep-drafts")}, [[S1], []],
                  {"keep-drafts": ["stop"]})  # fmt: skip
    _begin(root, capsys)
    path = _common(root) / factory.AUTOPILOT_STATE
    old = json.loads(path.read_text(encoding="utf-8"))
    for key in ("goal", "register", "plans"):
        old.pop(key)
    path.write_text(json.dumps(old), encoding="utf-8")
    code, out = _loop(root, capsys)
    assert code == 0, out
    first = steps.briefs[0]
    assert "Goal: none (begun before goals)" in first
    assert all(s in first for s in (S1, S2, S3)), "nothing narrowed"
    assert out["register"] is None and out["goal"] is None
    summary = (root / out["summary"]).read_text(encoding="utf-8")
    assert "The register wasn't counted" in summary and "Goal: none" in summary


SKILL = ROOT / "plugins" / "factory" / "skills" / "autopilot" / "SKILL.md"


def test_the_skill_quotes_the_preview_question() -> None:
    """R13: the question Step 2 quotes is `preview()`'s, its values as `<…>` marks, and Steps 1
    and 3 pass the goal."""
    marks = {"arg": "<goal.arg>", "title": "<goal.title>", "source": "<goal.source>"}
    asked = ap.preview_question(marks, {"usd": "<usd>", "hours": "<hours>"},
                                {"debt": "<debt>", "risk": "<risk>"})  # fmt: skip
    text = SKILL.read_text(encoding="utf-8")
    quoted = re.findall(r"^> `(Run autopilot .+)`$", text, re.M)
    assert quoted == [asked], (quoted, asked)
    step1 = text.split("## Step 1")[1].split("## Step 2")[0]
    step3 = text.split("## Step 3")[1].split("## Out of scope")[0]
    assert "--goal" in step1 and "alternatives" in step1
    assert "--goal <goal.arg>" in step3
