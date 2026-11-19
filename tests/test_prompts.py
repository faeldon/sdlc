"""The factory's agent prompts: every task's prompt, on fixtures, is the text the script sent before
its prompts moved into `plugins/factory/prompts/` (164), and a prompt file that doesn't match what
the script fills is refused before any session starts.

The recorded copies in `tests/prompts/` were written by the script as it was before the move
(`SDLC_RECORD_PROMPTS=1`), and the golden test runs against any copy of the script named by
`SDLC_FACTORY_UNDER_TEST`, so it can be rerun against the base branch's own: a copy recorded from
the refactored code that differed from the old output would fail there. Each case calls `_task()`
or `_land_task()` on a change folder with a crafted loop state, the git and train boundaries fixed,
so the only values that vary by run are the temp root and the script's own path, each replaced by
a mark before comparing.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shlex
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UNDER_TEST = os.environ.get("SDLC_FACTORY_UNDER_TEST")
SCRIPT = Path(UNDER_TEST) if UNDER_TEST else ROOT / "plugins" / "factory" / "scripts" / "factory.py"
RECORDED = Path(__file__).resolve().parent / "prompts"
PROMPTS = ROOT / "plugins" / "factory" / "prompts"
NAME = "008-reopen-drafts"
# The tests of the files themselves: the script before the move has none to test.
needs_files = pytest.mark.skipif(bool(UNDER_TEST), reason="a script under test has no prompt files")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


factory = _load("factory_prompts_under_test", SCRIPT)

INTENT = """\
---
id: 008
slug: reopen-drafts
tier: 2
stage: build
idea: 2026-11-01-3
fixes: [2026-11-02-1]
---

# 008 — Reopen saved drafts
"""

UPGRADE = {
    "round": 2,
    "decision": "D3",
    "question": "Upgrade to Tier 2?",
    "answer": "upgrade to Tier 2: drafts need a retention policy",
}
REVIEWS = {
    "code": {"verdict": "CHANGES", "changes": ["src/a.py:1: rename a", "src/b.py:2: split b"]},
    "test": {"verdict": "PASS", "changes": []},
    "behaviour": {"verdict": "CHANGES", "changes": ["the drafts list is empty after a reload"]},
}
KEPT = {"kept": [{"role": "code", "change": "src/a.py:1: rename a"}]}
HANDED = [
    {"role": "code", "text": "src/c.py:3: a clearer name {key S high}"},
    {"role": "test", "text": "tests/t.py:9: one assert a line"},
]
LEDGER = [
    {"id": "D1", "kind": "default", "open": True, "decided": False, "answer": None,
     "source": "builder round 1", "options": [{"option": "50"}, {"option": "100"}]},
    {"id": "D2", "kind": "default", "open": True, "decided": False, "answer": None,
     "source": "code round 1", "options": []},
]  # fmt: skip
TRAIN_INTENT = "---\nid: {n}\ntier: {tier}\n---\n\n# {n} — {title}\n"
SHAS = {"007-keep-tabs": "7777777", NAME: "8888888", "009-trim-logs": "9999999"}


class Case:
    """One fixture: a change folder under `tmp_path` and the boundaries a prompt reads, fixed."""

    def __init__(self, tmp_path: Path, monkeypatch) -> None:
        self.root = tmp_path / "repo"
        self.folder = self.root / ".sdlc" / "work" / NAME
        self.folder.mkdir(parents=True)
        (self.folder / "intent.md").write_text(INTENT, encoding="utf-8", newline="\n")
        self.mp = monkeypatch
        self.ledger: list[dict] = []
        self.preamble = False
        self.verdict = {"next": "mend", "mend": [], "problems": []}
        mp = monkeypatch
        mp.setattr(factory, "_base", lambda root: "main")
        mp.setattr(factory, "_changed_paths", lambda root, base: ["db/migrate/1.sql", "src/a.py"])
        mp.setattr(factory, "_irreversible", lambda root, base: [])
        mp.setattr(factory, "_conflicted", lambda root: ["src/a.py", "src/b.py"])
        mp.setattr(factory, "_git", self._git)
        mp.setattr(factory, "read_train", lambda root: None)
        mp.setattr(factory, "current_branch", lambda root: NAME)
        mp.setattr(factory, "load_config", lambda root: ({}, []))
        mp.setattr(factory, "named_nits", lambda root, folder, text=None: ["2026-11-03-2"])
        mp.setattr(factory, "read_ledger", lambda folder: self.ledger)
        mp.setattr(factory, "preamble", lambda path: self.preamble)
        mp.setattr(factory.landing, "train_names", self._train_names)
        mp.setattr(factory.landing, "land_verdict", lambda root, folder, cfg, n: self.verdict)

    def _git(self, root: Path, *args: str) -> str:
        if args[0] == "merge-base":
            return "f0f0f0f"
        if args[0] == "show":
            pre, _, path = args[1].partition(":")
            name = next(n for n, sha in SHAS.items() if sha == pre)
            tier = "1" if name.startswith("009") else "2"
            title = {"007-keep-tabs": "Keep tabs", NAME: "Reopen saved drafts"}.get(name, "Trim")
            return TRAIN_INTENT.format(n=name[:3], tier=tier, title=title)
        raise AssertionError(args)

    def _train_names(self, root: Path, folder: Path):
        changes = {n: {"pre": sha} for n, sha in SHAS.items()}
        changes["010-gone"] = {"pre": "1010101", "ejected": True}
        return {"order": [*SHAS, "010-gone"], "changes": changes}, changes[folder.name]

    def write(self, rel: str, text: str) -> None:
        path = self.folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def task(self, state: dict, task: str, role: str, decided: str | None = None, **kw) -> str:
        planned = factory._task(self.root, self.folder, state, task, role, decided, **kw)
        assert not isinstance(planned, str), planned
        return planned[0]

    def land(self, task: str, role: str) -> str:
        self.write("reviews/land-1/.keep", "")
        planned = factory._land_task(self.root, self.folder, task, role)
        assert not isinstance(planned, str), planned
        return planned[0]


def _state(**over) -> dict:
    state = {
        "next": "build", "round": 1, "missing": [], "rounds": [], "reworked": None,
        "settled": [], "untouched": [], "repeats": [], "handed": [], "exhausted": False,
        "built": 1, "problems": [], "upgraded": None, "restart": None, "stuck": [],
        "untestable": [], "mend": [],
    }  # fmt: skip
    return {**state, **over}


def _reviewed(rnd: int, **over) -> dict:
    """A state at round `rnd`, every round before it reviewed by every reviewer in `REVIEWS`."""
    rounds = [{"round": r, "reviews": REVIEWS, "verified": KEPT} for r in range(1, rnd + 1)]
    return _state(round=rnd, rounds=rounds, **over)


def _spec_revise(c: Case) -> str:
    c.write(
        "decisions.md", "# Decisions\n\n- [x] R1 (person, revise): drop R3, it's out of scope\n"
    )
    return c.task(_state(next="spec"), "spec", "spec-writer", revise="R1")


def _restart(c: Case, reconsider: bool, words: bool) -> str:
    tail = (
        "\n## Reconsider the approach\n\nTry a queue.\n\n## Notes\n\nOld.\n" if reconsider else ""
    )
    c.write("decision-1.md", f"DECISION: ESCALATE\n- LOOK: the queue\n{tail}")
    c.write("decisions.md", "# Decisions\n\n- [x] R2 (person, restart): keep the old table\n")
    restart = {"round": 3, "archive": "decision-1.md", "words": "R2" if words else None}
    return c.task(_state(round=3, restart=restart), "build", "builder")


def _review_reworked(c: Case, kept: bool) -> str:
    rounds = [{"round": 1, "reviews": REVIEWS, "verified": KEPT if kept else {"kept": []}}]
    state = _state(next="review", round=2, rounds=rounds, missing=["code"])
    state.update(reworked=["src/a.py"], settled=["D1: 50"])
    return c.task(state, "review", "code")


def _approve(c: Case, **over) -> str:
    return c.task(_reviewed(2, next="approve", **over), "approve", "approver")


def _approve_irreversible(c: Case) -> str:
    c.mp.setattr(factory, "_irreversible", lambda root, base: ["db/migrate/**"])
    return _approve(c)


def _approve_defaults(c: Case, bare: bool) -> str:
    c.ledger = LEDGER if bare else LEDGER[:1]
    return _approve(c)


def _decided(c: Case, source: str) -> str:
    c.ledger = [{**LEDGER[0], "decided": True, "open": False, "answer": "50", "source": source}]
    return c.task(_reviewed(1, next="rework"), "decided", "builder", "D1")


def _mend(c: Case, role: str) -> str:
    problems = ["reviews/round-1/verified.md: C2 answered twice", "build/round-1.md: no evidence"]
    c.preamble = role == "code"
    state = _reviewed(1, next="stop", problems=problems, mend=[role])
    return c.task(state, "mend", role)


def _resolve(c: Case, gone: bool) -> str:
    files = ["src/a.py", factory.INBOX.as_posix()] if gone else ["src/a.py"]
    c.mp.setattr(factory, "_conflicted", lambda root: files)
    return c.land("resolve", "builder")


def _land_fix(c: Case) -> str:
    c.write("build/land-1.ask.md", "Name the flag `keep_drafts`.\n")
    assert factory.land_ask_path(c.folder, 1) == c.folder / "build" / "land-1.ask.md"
    return c.land("land-fix", "builder")


def _land_review(c: Case, how: str) -> str:
    if how == "resolved":
        c.write("runs/land-resolved", "")
    if how == "asked":
        c.write("build/land-1.ask.md", "Name the flag `keep_drafts`.\n")
    return c.land("land-review", "code")


def _land_verify(c: Case) -> str:
    c.write("reviews/land-1/code.md", "VERDICT: CHANGES\n- CHANGE: src/a.py:1: rename a\n")
    c.write("reviews/land-1/test.md", "VERDICT: PASS\n")
    return c.land("land-verify", "verifier")


def _land_mend(c: Case, role: str) -> str:
    c.preamble = role == "code"
    problems = ["reviews/land-1/verified.md: C1 answered twice", "reviews/round-1/verified.md: x"]
    c.verdict = {"next": "mend", "mend": [role], "problems": problems}
    return c.land("land-mend", role)


CASES: dict[str, Callable[[Case], str]] = {
    "spec": lambda c: c.task(_state(next="spec"), "spec", "spec-writer"),
    "spec-upgraded": lambda c: c.task(_state(next="spec", upgraded=UPGRADE), "spec", "spec-writer"),
    "spec-revise": _spec_revise,
    "spec-recheck": lambda c: c.task(_state(next="spec"), "spec", "spec-writer", recheck=True),
    "build": lambda c: c.task(_state(), "build", "builder"),
    "build-restart": lambda c: _restart(c, reconsider=False, words=False),
    "build-restart-reconsider": lambda c: _restart(c, reconsider=True, words=False),
    "build-restart-words": lambda c: _restart(c, reconsider=False, words=True),
    "build-restart-reconsider-words": lambda c: _restart(c, reconsider=True, words=True),
    "build-upgraded": lambda c: c.task(_state(round=2, upgraded=UPGRADE), "build", "builder"),
    "fix": lambda c: c.task(_state(next="fix", round=2), "fix", "builder"),
    "review": lambda c: c.task(_state(next="review", missing=["code"]), "review", "code"),
    "review-upgraded": lambda c: c.task(
        _state(next="review", round=2, missing=["code"], upgraded=UPGRADE), "review", "code"
    ),
    "review-reworked": lambda c: _review_reworked(c, kept=False),
    "review-reworked-kept": lambda c: _review_reworked(c, kept=True),
    "review-handed": lambda c: c.task(
        _state(next="review", round=2, missing=["code"], handed=HANDED), "review", "code"
    ),
    "verify": lambda c: c.task(
        _reviewed(1, next="verify", untouched=["src/z.py"], repeats=["code: x"]),
        "verify",
        "verifier",
    ),
    "rework": lambda c: c.task(_reviewed(1, next="rework"), "rework", "builder"),
    "rework-handed": lambda c: c.task(
        _reviewed(1, next="rework", handed=HANDED), "rework", "builder"
    ),
    "approve": lambda c: _approve(c),
    "approve-upgraded": lambda c: _approve(c, upgraded=UPGRADE),
    "approve-stuck": lambda c: _approve(c, stuck=["code: src/a.py:1: rename a"]),
    "approve-untestable": lambda c: _approve(c, untestable=["R4: judged by eye"]),
    "approve-exhausted": lambda c: _approve(c, exhausted=True),
    "approve-defaults": lambda c: _approve_defaults(c, bare=False),
    "approve-defaults-bare": lambda c: _approve_defaults(c, bare=True),
    "approve-irreversible": _approve_irreversible,
    "decided-builder": lambda c: _decided(c, "builder round 1"),
    "decided-other": lambda c: _decided(c, "code round 1"),
    "mend-approver": lambda c: _mend(c, "approver"),
    "mend-verifier": lambda c: _mend(c, "verifier"),
    "mend-verdict": lambda c: _mend(c, "code"),
    "mend-builder": lambda c: _mend(c, "builder"),
    "mend-behaviour": lambda c: _mend(c, "behaviour"),
    "resolve": lambda c: _resolve(c, gone=False),
    "resolve-inbox": lambda c: _resolve(c, gone=True),
    "train-resolve": lambda c: c.land("train-resolve", "resolver"),
    "land-fix": _land_fix,
    "land-review": lambda c: _land_review(c, "clean"),
    "land-review-resolved": lambda c: _land_review(c, "resolved"),
    "land-review-asked": lambda c: _land_review(c, "asked"),
    "land-verify": _land_verify,
    "land-mend-verifier": lambda c: _land_mend(c, "verifier"),
    "land-mend-verdict": lambda c: _land_mend(c, "code"),
    "land-mend-evidence": lambda c: _land_mend(c, "behaviour"),
}


def _marked(text: str, root: Path) -> str:
    """`text` with what varies by run marked: the script's own path, then the temp root."""
    script = factory.FACTORY_SCRIPT.as_posix()
    text = text.replace(shlex.quote(script), "<factory-script>").replace(script, "<factory-script>")
    return text.replace(str(root), "<root>").replace(root.as_posix(), "<root>")


def _render(name: str, tmp_path: Path, monkeypatch) -> str:
    case = Case(tmp_path / name, monkeypatch)
    return _marked(CASES[name](case), case.root)


@pytest.mark.parametrize("name", sorted(CASES))
def test_every_prompt_matches_its_recorded_copy(name, tmp_path, monkeypatch) -> None:
    """164 R2, R3: each task's prompt, and each branch of it, byte for byte the recorded copy."""
    told = _render(name, tmp_path, monkeypatch)
    path = RECORDED / f"{name}.txt"
    if os.environ.get("SDLC_RECORD_PROMPTS"):
        path.parent.mkdir(exist_ok=True)
        path.write_text(told, encoding="utf-8", newline="\n")
    assert told == path.read_text(encoding="utf-8")


def test_every_recorded_copy_is_a_case() -> None:
    """A recorded copy no case renders is a branch the golden test no longer covers."""
    assert sorted(p.stem for p in RECORDED.glob("*.txt")) == sorted(CASES)


# ---------------------------------------------------------------- the files themselves


# Sentences only a prompt says: one from each file, found in the script's source only if a prompt
# was left in code.
PROSE = (
    "Address every KEPT line",
    "keeping what both sides meant",
    "it waits for a gate slot",
    "Draft spec.md for this change",
    "Build it: plan.md first",
    "fix what it shows, then report",
    "Raise again, word for word",
    "Untouched: ",
    "propose its disposition at landing",
    "is decided in decisions.md",
    "Your reply has no ## Evidence",
    "can't read your verdict",
    "can't read your decision",
    "The script couldn't read your answers",
    "Your draft is missing one of these",
    "A landing train stacks",
    "The person asked for a fix while landing",
    "Review landing round",
    "Verify landing round",
    "from the commit this round rebased the change onto",
    "Weigh each open default",
    "These have no options yet",
    "Change folder: ",
)


@needs_files
def test_no_prompt_prose_in_the_script() -> None:
    """164 R1: no sentence a prompt sends is left in `factory.py`."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert [p for p in PROSE if p in source] == []


@needs_files
def test_every_prompt_part_is_rendered(tmp_path, monkeypatch) -> None:
    """164 R4: every part of every file is sent by some golden case, and every file and part on
    disk is one the script declares."""
    seen = set()
    real = factory.prompt_part

    def spy(name: str, key: str, /, **values) -> str:
        seen.add((name, key))
        return real(name, key, **values)

    monkeypatch.setattr(factory, "prompt_part", spy)
    for name in CASES:
        _render(name, tmp_path, monkeypatch)
    declared = {(f, p) for f, parts in factory.PROMPT_PARTS.items() for p in parts}
    assert declared - seen == set()
    assert sorted(p.stem for p in PROMPTS.glob("*.md")) == sorted(factory.PROMPT_PARTS)
    for name in factory.PROMPT_PARTS:
        assert not isinstance(factory._prompt_file(name), str), name


def _doctored(tmp_path: Path, monkeypatch, name: str, old: str, new: str) -> None:
    """A copy of the prompts folder with `old` in `name`'s file replaced by `new`, read in place
    of the plugin's own."""
    copy = tmp_path / "prompts"
    shutil.copytree(PROMPTS, copy)
    path = copy / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    monkeypatch.setattr(factory, "PROMPTS_DIR", copy)


FAKE_CLAUDE = """\
#!/usr/bin/env python3
import json, os, sys
with open(os.environ["FAKE_CLAUDE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
print(json.dumps({"type": "result", "is_error": False, "result": "ok"}))
"""


def _repo(tmp_path: Path) -> Path:
    """A change at the start of its build, on its branch, as `cmd_agent` reads one."""
    import subprocess

    root = tmp_path / "repo"
    folder = root / ".sdlc" / "work" / NAME
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT.replace("stage: build", "stage: design"), "utf-8")
    for artifact in ("spec.md", "plan.md"):
        (folder / artifact).write_text(f"# 008 — {artifact}\n\nWritten.\n", encoding="utf-8")
    for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "init"],
                 ["checkout", "-q", "-b", NAME]):  # fmt: skip
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    return root


@needs_files
@pytest.mark.parametrize(
    "name, old, new, why",
    [
        ("build", "## upgraded\n", "## upgrade\n", "part upgrade"),
        ("build", "## first\n", "## first\n\nx\n\n## extra\n", "part extra"),
        ("build", "build round ${round} to the spec", "build round ${rounds} to", "${rounds}"),
        ("common", "check ${ident}`", "check`", "${ident}"),
        ("build", "Build it: plan.md", "Build it: $5 plan.md", "$"),
    ],
    ids=["missing-part", "extra-part", "unfilled-placeholder", "unnamed-placeholder", "stray-$"],
)
def test_a_prompt_file_that_doesnt_match_is_refused(
    tmp_path, monkeypatch, capsys, name, old, new, why
) -> None:
    """164 R5: a prompt file whose parts or placeholders don't match what the script fills is
    refused by `agent` with exit 1, naming the file and the part, and no session starts."""
    root = _repo(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "claude").write_text(FAKE_CLAUDE, encoding="utf-8")
    (bin_dir / "claude").chmod(0o755)
    log = tmp_path / "claude.jsonl"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(log))
    _doctored(tmp_path, monkeypatch, name, old, new)
    code = factory.cmd_agent(root, "008", "build", None, None)
    refusal = json.loads(capsys.readouterr().out)["refusals"][0]
    assert code == 1 and f"prompts/{name}.md" in refusal and why in refusal, refusal
    assert not log.exists(), "no session starts on a prompt file that doesn't match"


@needs_files
def test_a_missing_prompt_file_is_a_refusal(tmp_path, monkeypatch) -> None:
    """164 R5: a prompt file gone is a refusal, never a traceback."""
    monkeypatch.setattr(factory, "PROMPTS_DIR", tmp_path / "nowhere")
    case = Case(tmp_path, monkeypatch)
    refused = factory._task(case.root, case.folder, _state(), "build", "builder", None)
    assert isinstance(refused, str) and "prompts/build.md" in refused, refused


@needs_files
def test_filled_text_is_never_read_as_a_placeholder(tmp_path, monkeypatch) -> None:
    """164 R6: the person's words and the agents' text reach the prompt as they are, `$`, `${x}`,
    braces and backticks included."""
    words = "cost it at $5, not ${round} or $$ {x} `y`"
    case = Case(tmp_path, monkeypatch)
    case.write("decisions.md", f"# Decisions\n\n- [x] R1 (person, revise): {words}\n")
    told = case.task(_state(next="spec"), "spec", "spec-writer", revise="R1")
    assert told == f"Revise your draft, as the person asks: {words}"
    handed = [{"role": "code", "text": words}]
    told = case.task(_reviewed(1, next="rework", handed=handed), "rework", "builder")
    assert f"- code: {words}\n" in told
    case.write("build/land-1.ask.md", words)
    assert f"landing this change: {words} Make it" in case.land("land-fix", "builder")


@needs_files
def test_the_land_fix_prompt_tells_a_fix_already_made(tmp_path, monkeypatch) -> None:
    """181 R10: the builder asked for a fix at landing is told what to do when it already holds:
    edit nothing, answer `FIX: ALREADY MADE`, and prove it under `## Evidence`."""
    case = Case(tmp_path, monkeypatch)
    case.write("build/land-1.ask.md", "say it louder")
    told = case.land("land-fix", "builder")
    assert "already holds" in told and "edit nothing" in told, told
    assert "FIX: ALREADY MADE" in told and "## Evidence" in told, told


@needs_files
@pytest.mark.portable
def test_a_crlf_prompt_file_gives_the_same_prompt(tmp_path, monkeypatch) -> None:
    """164 R7: a prompt file checked out with CRLF line ends gives the prompt an LF one does."""
    copy = tmp_path / "prompts"
    shutil.copytree(PROMPTS, copy)
    for path in copy.glob("*.md"):
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    monkeypatch.setattr(factory, "PROMPTS_DIR", copy)
    for name in ("build-restart-reconsider-words", "verify", "train-resolve"):
        told = _render(name, tmp_path, monkeypatch)
        assert "\r" not in told
        assert told == (RECORDED / f"{name}.txt").read_text(encoding="utf-8")


@needs_files
def test_prompts_are_read_from_the_plugin_alone(tmp_path, monkeypatch) -> None:
    """164 R8: a host's `.sdlc/templates/prompts/` or a `prompts/` in the worktree is never read."""
    case = Case(tmp_path, monkeypatch)
    for where in (".sdlc/templates/prompts", "prompts"):
        (case.root / where).mkdir(parents=True)
        (case.root / where / "build.md").write_text("# build\n\n## first\n\nHijacked.\n", "utf-8")
    monkeypatch.chdir(case.root)
    told = _marked(case.task(_state(), "build", "builder"), case.root)
    assert told == (RECORDED / "build.txt").read_text(encoding="utf-8")
    assert factory.PROMPTS_DIR == factory.FACTORY_ROOT / "prompts"


@needs_files
def test_prompt_files_hold_no_path() -> None:
    """164 R9: no prompt file holds a machine path: each is filled in at run time."""
    import re

    script = factory.FACTORY_SCRIPT.as_posix()
    for path in PROMPTS.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"/Users/|/home/|\b[A-Za-z]:[\\/]", text), path.name
        assert script not in text and str(factory.FACTORY_ROOT) not in text, path.name


def test_the_factory_readme_names_the_prompts_folder() -> None:
    """164 R11: the factory's README says where its prompts live."""
    readme = (ROOT / "plugins" / "factory" / "README.md").read_text(encoding="utf-8")
    assert "plugins/factory/prompts/" in readme
