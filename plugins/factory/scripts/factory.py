#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""factory — the mechanical half of the optional sdlc-factory layer.

The factory's skills hand a change's spec, plan, build and review to agents, inside the change
loop the `sdlc` plugin runs. This script does what must not be left to a model's reading: which
change a session is in and whether its stage lets a step start, where `HEAD` was when a run began,
what each review file's first line says, which step the loop takes next, and the one frontmatter
line a step moves.

It never imports `sdlc.py`. Installed from the marketplace, each plugin is cached on its own, so
it reads the change folder itself, the same way: frontmatter by line, edited by line, never
round-tripped (`sdlc.py`'s `stamp_shipped` rule). For landing alone it runs the `sdlc.py` of its
own version, beside it (`sdlc_path()`), so ship, base and close keep one implementation.

    uv run --script factory.py config
    uv run --script factory.py start 008 --for build
    uv run --script factory.py decisions 008
    uv run --script factory.py verdicts 008 --head 1a2b3c4 --record
    uv run --script factory.py gate 008
    uv run --script factory.py carry 008
    uv run --script factory.py stage 008 test
    uv run --script factory.py agent 008 --task review --role code
    uv run --script factory.py ready
    uv run --script factory.py land-check
    uv run --script factory.py land 008 --by auto

Every command prints JSON and writes only where its name says: `decisions` to `decisions.md`,
`carry` to `notes.md`, `stage` to `intent.md`, `gate` its attempt to `build/round-<N>.gate.md`,
`verdicts --record` a stop to `runs/stopped.md` (or removes it once the run is clear) and the
step it read, with since when, to `runs/step.md`,
`agent` the reply an agent session returned, and its id and figures under `runs/`. Nothing is
written outside the change's folder, and nothing under `.git/`, but by the landing: `land` and
`resolve` commit and rebase the change's own branch, and `sdlc.py close` lands it. A command about
one change runs in its worktree, found from the main checkout when the supervisor runs there
(`change_root()`).

**Decisions that are a person's.** An agent that reaches a call it shouldn't make (a trade-off, a
policy, scope) raises a `- DECISION: [blocking] ...` or `- DECISION: [default] ...` line in its
reply. `decisions` gathers them into `decisions.md`; `verdicts` says `decide` while a blocking one
is unanswered, and the session running the build, the only one that can talk to the person, asks
them. A default one lets the run go on, recorded as assumed until the person confirms it.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import tomllib
import uuid
from contextlib import suppress
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlparse

# The change-folder names `sdlc.py` gives: three digits at least, then the slug.
DIR_RE = re.compile(r"^(\d{3,})-([a-z0-9][a-z0-9-]*)$")
# Every role a model can be set for, and the reviewers a repo can choose among.
ROLES = (
    "spec-writer", "builder", "code", "security", "test", "behaviour", "ui", "ux", "verifier",
    "approver",
)  # fmt: skip
REVIEWERS = ("code", "security", "test", "behaviour", "ui", "ux")
# The reviewers that look at the page a change shows, from `factory.py shots`: never chosen in
# `reviewers`, they join a round once the base branch's `[ui]` is complete and the diff touches its
# `paths`, at either depth, and never make a run's depth full.
UI_REVIEWERS = ("ui", "ux")
# `reviewers` and `rounds` are the full depth; `light` the one a diff touching no path in the
# base branch's `[review] sensitive` gets, once a host lists any.
DEFAULTS: dict = {
    "reviewers": ["code", "security", "test", "behaviour"],
    "rounds": 3,
    "light": {"reviewers": ["code"], "rounds": 2},
    "models": {},
    "mode": "auto",
    "land": {"auto": True, "batch": 5},
    # A repo's front end: the dev server to start (`{port}`), where it answers, the pages to shoot,
    # the paths that count as UI, the screenshot command (`{url}`, `{width}`, `{height}`, `{out}`),
    # the window sizes, and how long the server gets to answer. Unset, no UI review runs.
    "ui": {
        "serve": None, "url": "http://127.0.0.1:{port}", "pages": ["/"], "paths": [],
        "shoot": None, "widths": [[1280, 800], [390, 844]], "timeout": 60,
    },
}  # fmt: skip
MAX_ROUNDS = 5
# The permission modes `claude -p` takes, for the agent sessions the supervisor starts: none of
# them can answer a prompt, so the mode is chosen before the run, and named at its gate.
MODES = ("acceptEdits", "auto", "bypassPermissions", "manual", "dontAsk", "plan")
# The model each role runs on unless `factory.models` sets one: what builds, decides or looks for
# exploits on the strongest; the other reviewers on `sonnet` for a Tier 2 change or a run at the
# full depth, `haiku` otherwise. The supervisor is the person's own session, never set here.
FIXED_MODELS = {
    "spec-writer": "opus", "builder": "opus", "security": "opus", "verifier": "sonnet",
    "approver": "opus",
}  # fmt: skip
SCALED = ("code", "test", "behaviour", "ui", "ux")
# The stages a factory step moves a change between. `shipped` stays `sdlc ship`'s alone.
STAGES = ("plan", "design", "build", "test")
# What each step may start from. A build left at `stage: build` by a run that stopped resumes; a
# Tier 2 at `plan` starts with the spec-writer's draft, shown before the run's one gate.
STARTS = {
    "spec": {(2, "plan")},
    "build": {(2, "plan"), (2, "design"), (2, "build"), (1, "plan"), (1, "build")},
}
# First lines the loop reads, and each required change a reviewer lists below its verdict.
VERDICT_RE = re.compile(r"^VERDICT: (PASS|CHANGES)\s*$")
DECISION_RE = re.compile(r"^DECISION: (READY|ESCALATE)\s*$")
CHANGE_RE = re.compile(r"^\s*- CHANGE:\s*(.+?)\s*$")
# A problem in code the change didn't touch: filed for later, never reworked.
PREEXISTING_RE = re.compile(r"^\s*- PREEXISTING:\s*(.+?)\s*$")
# The verifier's answer to each `CHANGE:` of a round, in `reviews/round-<N>/verified.md`: kept for
# the builder, or dropped with why (after the last ` — `).
VERIFIED = "verified.md"
KEPT_RE = re.compile(r"^\s*- KEPT:\s*([a-z]+):\s*(.+?)\s*$")
DROPPED_RE = re.compile(r"^\s*- DROPPED:\s*([a-z]+):\s*(.+?)\s*$")
DROP_WHY = " — "
# An answer may open with its change's id, `C<n>`, as the verify prompt numbers them
# (`asked_changes()`), then say the change in its own words.
ID_RE = re.compile(r"^C(\d+):\s*(.*)$")
# What an approver must write when the rounds ran out with changes still kept.
RECONSIDER = "## Reconsider the approach"
# An escalated change sent back to the factory: its `decision.md` kept as `decision-<n>.md`, and
# `build/round-<R>.restart.md`, written by `restart` beside the gate files, marking round R as the
# new run's first. Its first line names the archive; `WORDS:` the person's own words, when they gave
# any, as a ticked `R<k> (person, restart)` line in `decisions.md`, which the ledger reads past.
RESTART_RE = re.compile(r"^RESTART: (decision-(\d+)\.md)\s*$")
WORDS_RE = re.compile(r"^WORDS: (R\d+)\s*$")
RESTART_WORDS_RE = re.compile(r"^- \[x\] (R\d+) \(person, restart\): (.+?)\s*$")
ARCHIVE_RE = re.compile(r"^decision-(\d+)\.md$")
# What a builder report and a behaviour check end with: each command run (`$ <command>`), the tail
# of its output, and `exit: <n>`. A result claimed without one is a stop, never taken on trust.
EVIDENCE = "## Evidence"
EXIT_RE = re.compile(r"^\s*exit:\s*\d+\s*$")
# The reviewers whose replies owe evidence too: the ones that run the change.
RUNS_THE_CHANGE = ("behaviour",)
# The gate, the base branch's `[commands] check`, which this script runs on each build before any
# reviewer, into `build/round-<N>.gate.md`: its first line the latest attempt's verdict, then one
# `## Attempt <k>` section each. A red gate sends the builder back at most `GATE_FIXES` times a
# round; one more red is a stop. A fix never counts as a round, which stays a reviewed one.
GATE_TIMEOUT = 30 * 60
GATE_FIXES = 2
GATE_TAIL = 80
# What the recorded output says in place of the main checkout's root and the home directory: the
# record is committed with the change, and a machine's layout never reaches its history.
CLONE_MARK = "<path-to-clone>"
HOME_MARK = "~"
ATTEMPT_VERDICT_RE = re.compile(r"^Verdict: (PASS|FAIL)\s*$")
BUILD_RE = re.compile(r"^Build: ([0-9a-f]+)\s*$")
# How long an attempt ran, which the board reads from a closed change's history for its estimates.
SECONDS_RE = re.compile(r"^Seconds: (\d+(?:\.\d+)?)\s*$")
# A decision an agent can't make: a person's call. `blocking` stops the run until they answer;
# `default` goes ahead on the agent's stated default, recorded as assumed until they confirm it.
RAISED_RE = re.compile(r"^\s*- DECISION:\s*\[(blocking|default)\]\s*(.+?)\s*$")
# The ledger, `decisions.md`: one line each, ticked once a person has decided it.
LEDGER_RE = re.compile(r"^- \[( |x)\] (D\d+) \(([^,)]+), (blocking|default)\): (.+?)\s*$")
DECIDED = " → decided: "
# How `carry` starts a `notes.md` the change doesn't have yet: a copy of `sdlc`'s
# `templates/notes.md`, which this plugin's cached copy can't read. A test keeps the two the same.
NOTES_HEAD = """\
# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.
"""
CONFIG_FILE = Path(".sdlc") / "factory.toml"


def _git(root: Path, *args: str) -> str | None:
    """stdout of a git command run in `root`, or None if git is absent or the command fails."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip()


def _utf8_streams() -> None:
    """Write UTF-8 to stdout and stderr whatever the console's code page, which on Windows has no
    `■` or `→`. A stream that can't be reconfigured (a test's capture) is left as it is."""
    for stream in (sys.stdout, sys.stderr):
        with suppress(AttributeError, ValueError, OSError):
            stream.reconfigure(encoding="utf-8")


def _sh(command: str) -> list[str]:
    """The argv that runs the host's gate, and `[ui]`'s server and screenshots, through `sh -c`
    on every platform, as `sdlc.py` runs a host's commands: `/bin/sh`, and on Windows the `sh` on
    PATH, Git for Windows', never `cmd.exe`. Raises OSError when Windows has none. Copied from
    `sdlc.py`, pinned by a test."""
    if os.name != "nt":
        return ["/bin/sh", "-c", command]
    found = shutil.which("sh")
    if found is None:
        raise OSError("no sh on PATH: install Git for Windows, whose sh runs a host's commands")
    return [found, "-c", command]


def repo_root() -> Path:
    out = _git(Path.cwd(), "rev-parse", "--show-toplevel")
    return Path(out) if out else Path.cwd()


def names_change(name: str, ident: str) -> bool:
    """Whether `ident`, as a person types it (`8`, `008`, `008-slug`), names `name`. Copied from
    `sdlc.py`: never a string prefix, since ids run past three digits."""
    m = DIR_RE.match(name)
    if not m:
        return False
    if ident.isdigit():
        return int(m.group(1)) == int(ident)
    return name == ident or name.startswith(f"{ident}-")


def worktrees(root: Path) -> list[tuple[Path, str]]:
    """(path, branch) for every checkout of this repo with a branch out, the main one included.
    Copied from `sdlc.py`, and pinned to it by a test."""
    out = _git(root, "worktree", "list", "--porcelain") or ""
    found: list[tuple[Path, str]] = []
    path: Path | None = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree ") :])
        elif line.startswith("branch refs/heads/") and path is not None:
            found.append((path, line[len("branch refs/heads/") :]))
    return found


def change_root(root: Path, ident: str) -> Path:
    """The checkout a command about change `ident` works in: this one when it is on the change's
    branch, else the change's own worktree, so the supervisor, a session in the main checkout,
    runs every step there. Unchanged when the change has no worktree: `find_change` refuses it."""
    if names_change(current_branch(root), ident):
        return root
    trees = [p for p in _all_checkouts(root) if names_change(current_branch(p), ident)]
    return trees[0] if trees else root


def current_branch(root: Path) -> str:
    """The branch `root` has out, or, mid-rebase, the one being rebased, which git keeps in
    `rebase-merge/head-name` while HEAD is detached: a landing's conflict is still its change's."""
    branch = _git(root, "branch", "--show-current") or ""
    if branch:
        return branch
    for name in ("rebase-merge", "rebase-apply"):
        where = _git(root, "rev-parse", "--git-path", f"{name}/head-name")
        path = Path(where) if where else None
        if path is not None and not path.is_absolute():
            path = root / path
        if path is not None and path.is_file():
            return path.read_text(encoding="utf-8").strip().removeprefix("refs/heads/")
    return ""


def _all_checkouts(root: Path) -> list[Path]:
    """Every checkout of this repo, a detached one (a rebase under way) included."""
    out = _git(root, "worktree", "list", "--porcelain") or ""
    return [
        Path(line[len("worktree ") :]) for line in out.splitlines() if line.startswith("worktree ")
    ]


def load_config(root: Path) -> tuple[dict, list[str]]:
    """`.sdlc/factory.toml` over the defaults, and what was wrong with it. A bad key is a warning,
    never quietly ignored: a reviewer spelled `secruity` would otherwise never run."""
    light = DEFAULTS["light"]
    cfg = {
        "reviewers": list(DEFAULTS["reviewers"]),
        "rounds": DEFAULTS["rounds"],
        "light": {"reviewers": list(light["reviewers"]), "rounds": light["rounds"]},
        "models": {},
    }
    cfg["mode"], warnings = _mode(root)
    cfg["land"], land_warnings = _land(root)
    warnings += land_warnings
    cfg["ui"], ui_warnings = _ui(root)
    warnings += ui_warnings
    path = root / CONFIG_FILE
    if not path.is_file():
        return cfg, warnings
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        return cfg, [*warnings, f"{CONFIG_FILE} won't parse: {e}"]
    warnings += [f"unknown key {key}" for key in data if key not in DEFAULTS]
    _depth_keys(data, cfg, "", warnings)
    table = data.get("light", {})
    if not isinstance(table, dict):
        warnings.append("light must be a table of reviewers and rounds")
    else:
        warnings += [f"unknown key light.{key}" for key in table if key not in light]
        _depth_keys(table, cfg["light"], "light.", warnings)
    models = data.get("models", {})
    if not isinstance(models, dict):
        warnings.append("models must be a table of role = model")
    else:
        for role, model in models.items():
            if role not in ROLES:
                warnings.append(f"unknown role {role!r} in models: one of {', '.join(ROLES)}")
            elif not isinstance(model, str):
                warnings.append(f"models.{role} must be a model name")
            else:
                cfg["models"][role] = model
    if "mode" in data and data.get("mode") != cfg["mode"]:
        warnings.append(
            f"mode is read from the base branch's {CONFIG_FILE.as_posix()}: this checkout's "
            f"{data.get('mode')!r} applies once it lands"
        )
    if "ui" in data and _ui_table(data.get("ui"))[0] != cfg["ui"]:
        warnings.append(
            f"ui is read from the base branch's {CONFIG_FILE.as_posix()}: this checkout's [ui] "
            "applies once it lands"
        )
    return cfg, warnings


def _base_factory(root: Path) -> dict:
    """The base branch's `factory.toml`, never this checkout's: what a change may do unasked is
    set where the change can't edit it. Empty when there is none, or it won't parse."""
    base = _base(root)
    if not base:
        return {}
    try:
        return tomllib.loads(_git(root, "show", f"{base}:{CONFIG_FILE.as_posix()}") or "")
    except tomllib.TOMLDecodeError:
        return {}


def _mode(root: Path) -> tuple[str, list[str]]:
    """`mode`, the permission mode agent sessions run in, as the base branch's `factory.toml`
    holds it: a change can't widen what its own agents may do unasked."""
    mode = _base_factory(root).get("mode", DEFAULTS["mode"])
    if mode not in MODES:
        return DEFAULTS["mode"], [
            f"mode must be one of {', '.join(MODES)}, so {DEFAULTS['mode']} runs"
        ]
    return mode, []


def _land(root: Path) -> tuple[dict, list[str]]:
    """`[land]` as the base branch holds it: `auto`, whether a batch with no risk signal lands
    without asking, and `batch`, the most changes one landing takes. A change can't turn either up
    for itself."""
    table = _base_factory(root).get("land", {})
    out, warnings = dict(DEFAULTS["land"]), []
    if not isinstance(table, dict):
        return out, ["land must be a table of auto and batch"]
    for key, value in table.items():
        if key == "auto" and isinstance(value, bool):
            out["auto"] = value
        elif (
            key == "batch" and isinstance(value, int) and not isinstance(value, bool) and value > 0
        ):
            out["batch"] = value
        else:
            warnings.append(f"land.{key} must be auto = true|false or batch = a whole number")
    return out, warnings


def _ui(root: Path) -> tuple[dict, list[str]]:
    """`[ui]` as the base branch holds it: the dev server a UI review starts runs unasked once the
    run is approved, so a change can't name its own."""
    return _ui_table(_base_factory(root).get("ui", {}))


def _ui_table(table: object) -> tuple[dict, list[str]]:
    """A `[ui]` table over the defaults, each bad value a warning that leaves its default."""
    out = {k: list(v) if isinstance(v, list) else v for k, v in DEFAULTS["ui"].items()}
    if not isinstance(table, dict):
        return out, ["ui must be a table of serve, url, pages, paths, shoot, widths and timeout"]
    warnings = []
    for key, value in table.items():
        texts = isinstance(value, list) and all(isinstance(v, str) for v in value)
        sizes = isinstance(value, list) and value and all(
            isinstance(v, list) and len(v) == 2
            and all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in v)
            for v in value
        )  # fmt: skip
        if key in ("serve", "url", "shoot") and isinstance(value, str) and value.strip():
            out[key] = value
        elif key in ("pages", "paths") and texts:
            out[key] = list(value)
        elif key == "widths" and sizes:
            out[key] = [list(v) for v in value]
        elif (
            key == "timeout"
            and isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
        ):
            out[key] = value
        elif key in DEFAULTS["ui"]:
            warnings.append(f"ui.{key} has the wrong shape, so its default stands")
        else:
            warnings.append(f"unknown key ui.{key}")
    return out, warnings


def ui_complete(ui: dict) -> bool:
    """Whether `[ui]` says enough for a UI review: a server, a screenshot command and its paths."""
    return bool(ui.get("serve") and ui.get("shoot") and ui.get("paths"))


def model_for(role: str, cfg: dict, tier: int | None, level: str) -> str:
    """The model `role` runs on: `factory.models`' entry, else `FIXED_MODELS`, the scaled
    reviewers on `sonnet` for a Tier 2 change or a full-depth run and `haiku` otherwise."""
    if role in cfg["models"]:
        return cfg["models"][role]
    if role in SCALED:
        return "sonnet" if tier == 2 or level == "full" else "haiku"
    return FIXED_MODELS[role]


def _depth_keys(data: dict, into: dict, prefix: str, warnings: list[str]) -> None:
    """A depth's `reviewers` and `rounds` from `data` into `into`, the top level's or `[light]`'s,
    each bad value a warning that leaves the default in place."""
    reviewers = data.get("reviewers", into["reviewers"])
    if not isinstance(reviewers, list) or not all(isinstance(r, str) for r in reviewers):
        warnings.append(f"{prefix}reviewers must be a list of names")
    else:
        chosen = [r for r in REVIEWERS if r not in UI_REVIEWERS]
        unknown = [r for r in reviewers if r not in chosen]
        warnings += [
            f"{r!r} joins on its own when [ui] is set, never in {prefix}reviewers"
            if r in UI_REVIEWERS
            else f"unknown reviewer {r!r} in {prefix}reviewers: one of {', '.join(chosen)}"
            if prefix
            else f"unknown reviewer {r!r}: one of {', '.join(chosen)}"
            for r in unknown
        ]
        known = [r for r in dict.fromkeys(reviewers) if r in chosen]
        if known:
            into["reviewers"] = known
        else:
            warnings.append(f"no known reviewer is configured in {prefix or 'the top level'}, so "
                            "the defaults run")  # fmt: skip
    rounds = data.get("rounds", into["rounds"])
    if isinstance(rounds, int) and not isinstance(rounds, bool) and 1 <= rounds <= MAX_ROUNDS:
        into["rounds"] = rounds
    else:
        warnings.append(f"{prefix}rounds must be a whole number from 1 to {MAX_ROUNDS}")


def frontmatter(text: str) -> dict[str, str]:
    """The `key: value` lines of a `---` block, as text. Enough for `tier` and `stage`."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep:
            out[key.strip()] = value.strip()
    return out


def find_change(root: Path, ident: str) -> tuple[Path | None, str | None]:
    """The change folder this checkout's branch holds, or why not. A factory step works in the
    change's own worktree (`change_root()` finds it from the main checkout), so its agents do."""
    branch = current_branch(root)
    if not names_change(branch, ident):
        return None, (
            f"run it from change {ident}'s own worktree, or from the main checkout once "
            f"/sdlc:intent has made one: this checkout is on {branch or '?'!r}, and no worktree "
            "has that change's NNN-slug branch"
        )
    rel = work_rel(root)
    folder = root / rel / branch
    if not (folder / "intent.md").is_file():
        return None, f"{rel}/{branch}/intent.md doesn't exist on this branch"
    return folder, None


def work_rel(root: Path) -> str:
    """The change folder, relative to the checkout: `.sdlc/work`, as `sdlc.py`'s `work_rel()` says,
    kept here because this script never imports that one."""
    return ".sdlc/work"


def max_runs(cfg: dict) -> int:
    """The most agent runs one build can take, at the full depth: the builder, the approver, and
    each round's reviewers, verifier, builder resume and the builder's fixes of a red gate. An
    upper bound to show before a person approves the cost, whatever depth the diff turns out to
    need. With `[ui]` complete, the UI reviewers are counted in every round, since any round's
    diff can touch its paths."""
    ui = len(UI_REVIEWERS) if ui_complete(cfg.get("ui", {})) else 0
    return 2 + cfg["rounds"] * (len(cfg["reviewers"]) + ui + 2 + GATE_FIXES)


# The base branch's review lists, read here because the factory's cached copy has no `sdlc.py`.
SDLC_CONFIG = Path(".sdlc") / "config.toml"


def _base(root: Path) -> str | None:
    """The branch a change lands on: `[git] base` in `.sdlc/config.toml`, else `main` when it
    exists. None when neither is a branch here."""
    try:
        data = tomllib.loads((root / SDLC_CONFIG).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        data = {}
    git = data.get("git")
    named = git.get("base") if isinstance(git, dict) else None
    for ref in (named, "main"):
        if isinstance(ref, str) and ref and _git(root, "rev-parse", "--verify", "-q", ref):
            return ref
    return None


def _sensitive(root: Path, base: str) -> list[str]:
    """`[review] sensitive` as the base branch holds it, never this checkout's: a change can't
    lighten its own review by editing the list."""
    try:
        data = tomllib.loads(_git(root, "show", f"{base}:{SDLC_CONFIG.as_posix()}") or "")
    except tomllib.TOMLDecodeError:
        return []
    review = data.get("review")
    listed = review.get("sensitive") if isinstance(review, dict) else None
    return [p for p in listed if isinstance(p, str)] if isinstance(listed, list) else []


def _base_check(root: Path, base: str) -> str | None:
    """`[commands] check` as the base branch holds it, never this checkout's: a change can't edit
    the gate it is judged by. None when the base branch names none."""
    try:
        data = tomllib.loads(_git(root, "show", f"{base}:{SDLC_CONFIG.as_posix()}") or "")
    except tomllib.TOMLDecodeError:
        return None
    commands = data.get("commands")
    check = commands.get("check") if isinstance(commands, dict) else None
    return check if isinstance(check, str) and check.strip() else None


def _changed_paths(root: Path, base: str) -> list[str]:
    """Every path the change touches against where it left the base branch, uncommitted and
    untracked included, both sides of a rename, leaving out the change folders."""
    fork = _git(root, "merge-base", base, "HEAD")
    tracked = _git(root, "diff", "--name-only", "--no-renames", fork) if fork else None
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    paths = (tracked or "").splitlines() + (untracked or "").splitlines()
    return sorted({p for p in paths if p and not p.startswith(work_rel(root) + "/")})


def risk_paths(paths: list[str], patterns: list[str]) -> list[str]:
    """The `paths` any of `patterns` names, in order: an entry ending in `/` names every path under
    it, any other is an fnmatch glob over the repo-relative path, its `*` crossing `/`. Copied
    from `sdlc.py`, and pinned to it by a test."""

    def named(p: str) -> bool:
        return any(
            p.startswith(pat) if pat.endswith("/") else fnmatch.fnmatchcase(p, pat)
            for pat in patterns
        )

    return [p for p in paths if named(p)]


def depth(root: Path, cfg: dict, rounds: list[dict], starts: list[int] = ()) -> dict:
    """The depth this run reviews at, from the diff as it stands: `full` with no sensitive list
    (every run, as before there was a choice), when the diff touches a listed path, or once any
    round ran beyond `[light]` (a run never lightens); `light` otherwise. A round's place against
    `[light]`'s rounds is its place in its own run, counted from the newest restart at or before
    it (`starts`, the restarts' rounds), so a restart never deepens a light run. Writes nothing."""

    def place(n: int) -> int:
        return n - max((s for s in starts if s <= n), default=1) + 1

    base = _base(root)
    listed = _sensitive(root, base) if base else []
    changed = _changed_paths(root, base) if base else []
    hit = risk_paths(changed, listed)
    light = cfg["light"]
    beyond = any(
        place(r["round"]) > light["rounds"]
        or set(r["reviews"]) - set(light["reviewers"]) - set(UI_REVIEWERS)
        for r in rounds
    )
    if not listed:
        level, why = "full", "the base branch lists no [review] sensitive paths"
    elif hit:
        shown = ", ".join(hit[:5]) + (f" and {len(hit) - 5} more" if len(hit) > 5 else "")
        level, why = "full", f"the diff touches sensitive path(s) {shown}"
    elif beyond:
        level, why = "full", "an earlier round ran at the full depth, and a run never lightens"
    else:
        level, why = "light", "the diff touches no sensitive path"
    chosen = cfg if level == "full" else light
    return {"depth": level, "sensitive": hit, "why": why, "changed": changed,
            "reviewers": list(chosen["reviewers"]), "rounds": chosen["rounds"]}  # fmt: skip


def snapshot_path(folder: Path, n: int) -> Path:
    return folder / "build" / f"round-{n}.files"


def read_snapshot(folder: Path, n: int) -> dict[str, str] | None:
    """`build/round-<N>.files` as path → hash, or None when there is none."""
    path = snapshot_path(folder, n)
    if not path.is_file():
        return None
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, sep, name = line.partition("  ")
        if sep and name:
            found[name] = digest
    return found


def reworked(folder: Path, n: int) -> list[str] | None:
    """The paths round `n`'s build changed since round `n - 1`'s, by their snapshots: every
    changed path in round 1. None when a snapshot is missing, so the reviewers read it all."""
    now = read_snapshot(folder, n)
    if now is None:
        return None
    if n == 1:
        return sorted(now)
    before = read_snapshot(folder, n - 1)
    if before is None:
        return None
    return sorted(p for p in set(now) | set(before) if now.get(p) != before.get(p))


def emit(out: dict, code: int = 0) -> int:
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return code


def cmd_config(root: Path) -> int:
    cfg, warnings = load_config(root)
    return emit({"config_file": str(CONFIG_FILE), **cfg, "warnings": warnings})


def cmd_start(root: Path, ident: str, purpose: str) -> int:
    """Whether a factory step may start on this change now, and what it will run with."""
    cfg, warnings = load_config(root)
    out: dict = {"change": None, "folder": None, "for": purpose, "tier": None, "stage": None}
    out.update(head=_git(root, "rev-parse", "--short", "HEAD"), **cfg, max_runs=max_runs(cfg))
    out.update(warnings=warnings, refusals=[])
    folder, refusal = find_change(root, ident)
    if refusal:
        out["refusals"].append(refusal)
        return emit(out, 1)
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    tier = int(meta["tier"]) if meta.get("tier", "").isdigit() else None
    stage = meta.get("stage") or None
    out.update(change=folder.name, folder=str(folder), worktree=str(root), tier=tier, stage=stage)
    # A Tier 2 at `plan` has no spec yet: the spec-writer drafts it before the run's gate.
    out["spec"] = purpose == "build" and (tier, stage) == (2, "plan")
    # Each role's model, at either depth, so the gate shows the run's cost before it starts.
    out["models_at"] = {
        level: {role: model_for(role, cfg, tier, level) for role in ROLES}
        for level in ("light", "full")
    }
    if purpose == "build" and stage == "test" and tier in (1, 2):
        # An escalated change, sent back: reported here, written only by `restart`, after the yes.
        restart, why = restart_state(folder)
        if restart:
            out["restart"] = restart
        else:
            out["refusals"].append(why)
    elif (tier, stage) not in STARTS[purpose]:
        allowed = " or ".join(f"tier {t} at stage: {s}" for t, s in sorted(STARTS[purpose]))
        out["refusals"].append(
            f"{purpose} starts from {allowed}; {folder.name} is tier {tier} at stage: {stage}"
        )
        if purpose == "spec" and tier == 1:
            out["refusals"].append("a Tier 1 change has no spec: its intent's Approach is the spec")
    return emit(out, 1 if out["refusals"] else 0)


def read_rounds(folder: Path, reviewers: list[str]) -> tuple[list[dict], list[str]]:
    """Every `reviews/round-<N>/`, in order: each reviewer's verdict, the changes it asks for and
    the pre-existing problems it found, the verifier's answer when there is one, and whether the
    round is complete for `reviewers`, the ones the run's depth expects. A file whose first line
    isn't a verdict is a problem, never a guess."""
    base = folder / "reviews"
    found = []
    problems = []
    dirs = [p for p in base.glob("round-*") if p.is_dir() and p.name[6:].isdigit()]
    for path in sorted(dirs, key=lambda p: int(p.name[6:])):
        n = int(path.name[6:])
        reviews = {}
        for role in REVIEWERS:
            file = path / f"{role}.md"
            if not file.is_file():
                continue
            lines = file.read_text(encoding="utf-8").splitlines()
            m = VERDICT_RE.match(lines[0]) if lines else None
            if not m:
                problems.append(_no_verdict(n, role))
                continue
            changes = [c.group(1) for c in map(CHANGE_RE.match, lines[1:]) if c]
            if m.group(1) == "CHANGES" and not changes:
                # Nothing to verify or rework: a malformed reply, refused like one with no verdict.
                problems.append(
                    f"reviews/round-{n}/{role}.md says VERDICT: CHANGES but lists no - CHANGE: line"
                )
                continue
            preexisting = [c.group(1) for c in map(PREEXISTING_RE.match, lines[1:]) if c]
            reviews[role] = {"verdict": m.group(1), "changes": changes, "preexisting": preexisting}
        verified, wrong = read_verified(path / VERIFIED, n, reviews)
        problems += wrong
        complete = set(reviewers) <= set(reviews)
        found.append({"round": n, "reviews": reviews, "complete": complete, "verified": verified})
    return found, problems


def _no_verdict(n: int, role: str) -> str:
    """The problem a round's reply that doesn't open with its verdict is, word for word as the
    board and status show it."""
    return f"reviews/round-{n}/{role}.md doesn't open with VERDICT: PASS or VERDICT: CHANGES"


def preamble(path: Path) -> bool:
    """Whether a reply holds its verdict, but not on its first line: something written before it,
    which the run may mend once by asking again. Never read as a verdict where it stands."""
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    return bool(lines) and not VERDICT_RE.match(lines[0]) and any(map(VERDICT_RE.match, lines))


def asked_changes(reviews: dict) -> list[tuple[str, str, str]]:
    """The changes a round's `CHANGES` verdicts ask for, as `(id, role, text)`: each `(role,
    text)` once, numbered `C1`… in `REVIEWERS` order (any other role after, by name), then each
    file's line order. The verify prompt and `read_verified()` both number from here, so an id
    means the same change to the verifier and to the script."""
    roles = [r for r in REVIEWERS if r in reviews] + sorted(set(reviews) - set(REVIEWERS))
    asked = dict.fromkeys(
        (role, c)
        for role in roles
        if reviews[role]["verdict"] == "CHANGES"
        for c in reviews[role]["changes"]
    )
    return [(f"C{i}", role, c) for i, (role, c) in enumerate(asked, 1)]


def _change_lead(change: str) -> str | None:
    """A `CHANGE:`'s `path:line` lead, `src/a.py:42: what` → `src/a.py:42`, or None without one."""
    parts = change.split(":", 2)
    if len(parts) < 3 or not parts[1].strip().isdigit():
        return None
    return f"{_change_path(change)}:{parts[1].strip()}"


def _resolve(role: str, text: str, asked: list, n: int) -> tuple[str | None, str]:
    """The asked change an answer in round `n` names, by its id, else its exact text, else a
    `path:line` lead only one of its role's changes has: the reviewer's text, or None and why it
    names none."""
    if m := ID_RE.match(text):
        ident = f"C{m.group(1)}"
        match = next((a for a in asked if a[0] == ident), None)
        if not match:
            return None, f"{ident}, which no change of round {n} is"
        if match[1] != role:
            return None, f"{ident}, which is {match[1]}'s change, not {role}'s"
        return match[2], ""
    if any(a[1:] == (role, text) for a in asked):
        return text, ""
    lead = _change_lead(text)
    leads = [a[2] for a in asked if a[1] == role and lead and _change_lead(a[2]) == lead]
    if len(leads) == 1:
        return leads[0], ""
    if len(leads) > 1:
        return None, f"{text}, whose lead {lead} {len(leads)} of {role}'s changes open with"
    return None, f"{text}, which no review of round {n} asks for"


def read_verified(path: Path, n: int, reviews: dict) -> tuple[dict | None, list[str]]:
    """The verifier's `KEPT` and `DROPPED` lines for round `n`, or None before it answered. Each
    answer is resolved to the change it names (`_resolve()`) and carries the reviewer's text, so
    every reader sees the change as it was asked. Every `CHANGE:` the round's `CHANGES` verdicts
    ask for is answered exactly once, and every answer names one: anything else is a problem, so
    no change is reworked or dropped unread."""
    if not path.is_file():
        return None, []
    asked = asked_changes(reviews)
    where = f"reviews/round-{n}/{VERIFIED}"
    kept, dropped, problems = [], [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if m := KEPT_RE.match(line):
            role, text, why = m.group(1), m.group(2), None
        elif m := DROPPED_RE.match(line):
            change, sep, why = m.group(2).rpartition(DROP_WHY)
            role, text, why = m.group(1), (change if sep else m.group(2)).strip(), why.strip()
        else:
            continue
        change, wrong = _resolve(role, text, asked, n)
        if change is None:
            problems.append(f"{where} answers {role}: {wrong}")
            continue
        if why is None:
            kept.append({"role": role, "change": change})
        else:
            dropped.append({"role": role, "change": change, "why": why})
    answered = [(a["role"], a["change"]) for a in kept + dropped]
    problems = [
        f"{where} answers {role}: {c} {answered.count((role, c))} times, not once"
        for _, role, c in asked
        if answered.count((role, c)) != 1
    ] + problems
    return {"kept": kept, "dropped": dropped}, problems


def ui_review(cfg: dict, rounds: list[dict], changed: list[str]) -> bool:
    """Whether the UI reviewers join: `[ui]` is complete and the diff touches one of its `paths`,
    or an earlier round already ran them, so a run that looked at the page keeps looking."""
    ui = cfg.get("ui", {})
    if not ui_complete(ui):
        return False
    ran = any(set(r["reviews"]) & set(UI_REVIEWERS) for r in rounds)
    return ran or bool(risk_paths(changed, ui["paths"]))


def _rounds_at_depth(root: Path, folder: Path, cfg: dict) -> tuple[list[dict], list[str], dict]:
    """The rounds, their problems and the run's depth, each round's `complete` judged against the
    reviewers that depth expects, the UI reviewers among them when they join (`ui_review()`), and
    the newest restart (`restart`, or None), whose round starts the run."""
    rounds, problems = read_rounds(folder, cfg["reviewers"])
    restarts, wrong = read_restarts(folder)
    problems += wrong
    run = depth(root, cfg, rounds, [r["round"] for r in restarts])
    run["restart"] = restarts[-1] if restarts else None
    run["ui"] = ui_review(cfg, rounds, run["changed"])
    if run["ui"]:
        run["reviewers"] += [r for r in UI_REVIEWERS if r not in run["reviewers"]]
    for r in rounds:
        r["complete"] = set(run["reviewers"]) <= set(r["reviews"])
    return rounds, problems, run


def _change_path(change: str) -> str:
    """The path a `CHANGE:` names, `path/to/file.py:42: what` → `path/to/file.py`."""
    return change.split(":", 1)[0].strip().strip("`")


def _untouched(root: Path, change: str, changed: list[str]) -> bool:
    """Whether a `CHANGE:` is about code the change didn't touch: its path exists here and isn't
    among `changed`. A path that doesn't exist yet is one the change is asked to create, never
    pre-existing; with no changed paths known (no base branch), nothing is called untouched."""
    path = _change_path(change)
    return bool(changed) and path not in changed and (root / path).is_file()


def settled(rounds: list[dict], before: int) -> list[str]:
    """What the rounds before round `before` answered, as `role: change`: every dropped change,
    and every kept one the round after it no longer asks for. A reviewer never raises one again."""
    out = []
    for i, r in enumerate(rounds):
        if r["round"] >= before:
            break
        v = r["verified"] or {"kept": [], "dropped": []}
        out += [f"{d['role']}: {d['change']}" for d in v["dropped"]]
        later = rounds[i + 1] if i + 1 < len(rounds) else None
        if later:
            asked = {c for rv in later["reviews"].values() for c in rv["changes"]}
            out += [f"{k['role']}: {k['change']}" for k in v["kept"] if k["change"] not in asked]
    return list(dict.fromkeys(out))


def build_round(folder: Path) -> int:
    """The newest builder report's round, `build/round-<N>.md`; 0 before the first."""
    names = [p.stem[6:] for p in (folder / "build").glob("round-*.md")]
    return max((int(n) for n in names if n.isdigit()), default=0)


def read_evidence(text: str, where: str) -> list[str]:
    """What's wrong with a reply's `## Evidence` section: missing, no command in it, or a command
    whose `exit:` line never comes before the next command or the section's end."""
    lines = text.splitlines()
    if EVIDENCE not in [line.strip() for line in lines]:
        return [f"{where} has no `{EVIDENCE}` section: each command it ran, its output, its exit"]
    start = [line.strip() for line in lines].index(EVIDENCE) + 1
    commands, open_cmd, problems = 0, None, []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.lstrip().startswith("$ "):
            if open_cmd:
                problems.append(f"{where}: `{open_cmd}` has no `exit:` line")
            open_cmd, commands = line.strip()[2:], commands + 1
        elif EXIT_RE.match(line):
            open_cmd = None
    if open_cmd:
        problems.append(f"{where}: `{open_cmd}` has no `exit:` line")
    if not commands:
        problems.append(f"{where}'s `{EVIDENCE}` shows no command run (`$ <command>`)")
    return problems


def read_decision(folder: Path, exhausted: bool = False) -> tuple[str | None, str | None]:
    """The approver's decision, or what's wrong with it. After a run whose rounds ran out with
    changes still kept, only an ESCALATE that asks the person to reconsider the approach will do."""
    path = folder / "decision.md"
    if not path.is_file():
        return None, None
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    m = DECISION_RE.match(lines[0]) if lines else None
    if not m:
        return None, "decision.md doesn't open with DECISION: READY or DECISION: ESCALATE"
    if exhausted and (m.group(1) != "ESCALATE" or RECONSIDER not in lines):
        return None, (
            f"the rounds ran out with changes kept, so decision.md must be ESCALATE with a "
            f"`{RECONSIDER}` section"
        )
    return m.group(1), None


def restart_path(folder: Path, n: int) -> Path:
    return folder / "build" / f"round-{n}.restart.md"


def read_restart_words(folder: Path, ident: str) -> str | None:
    """The person's words for restart `ident` (`R2`) in `decisions.md`, or None."""
    path = folder / "decisions.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        m = RESTART_WORDS_RE.match(line)
        if m and m.group(1) == ident:
            return m.group(2)
    return None


def read_restarts(folder: Path) -> tuple[list[dict], list[str]]:
    """Every restart record, `build/round-<R>.restart.md`, oldest first, as its round, the archived
    decision it names, the id of the person's words (or None) and its own path in the folder; and
    what's wrong with any that won't read: a first line that isn't `RESTART: decision-<n>.md`, an
    archive that doesn't exist, or a `WORDS:` id no `(person, restart)` line holds."""
    found, problems = [], []
    suffix = ".restart.md"
    paths = [
        p for p in (folder / "build").glob(f"round-*{suffix}") if p.name[6 : -len(suffix)].isdigit()
    ]
    for path in sorted(paths, key=lambda p: int(p.name[6 : -len(suffix)])):
        where = f"build/{path.name}"
        lines = path.read_text(encoding="utf-8").splitlines()
        m = RESTART_RE.match(lines[0]) if lines else None
        if not m:
            problems.append(f"{where} doesn't open with RESTART: decision-<n>.md")
            continue
        archive = m.group(1)
        if not (folder / archive).is_file():
            problems.append(f"{where} names {archive}, which doesn't exist")
            continue
        words = next((w.group(1) for w in map(WORDS_RE.match, lines[1:]) if w), None)
        if words and read_restart_words(folder, words) is None:
            problems.append(
                f"{where} names {words}, which no `- [x] {words} (person, restart): …` line in "
                "decisions.md is"
            )
            continue
        n = int(path.name[6 : -len(suffix)])
        found.append({"round": n, "archive": archive, "words": words, "record": where})
    return found, problems


def next_archive(folder: Path) -> int:
    """The number the next archived decision takes: one past the highest `decision-<n>.md`."""
    names = [ARCHIVE_RE.match(p.name) for p in folder.glob("decision-*.md")]
    taken = [int(m.group(1)) for m in names if m]
    return max(taken, default=0) + 1


def reconsider_section(text: str) -> str | None:
    """A decision's `## Reconsider the approach` section, its heading and lines up to the next
    `## ` heading, word for word; None when it has none."""
    lines = text.splitlines()
    if RECONSIDER not in [line.strip() for line in lines]:
        return None
    start = [line.strip() for line in lines].index(RECONSIDER)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).rstrip()


def restart_state(folder: Path) -> tuple[dict | None, str | None]:
    """Whether a change at `stage: test` can go back to the factory, and how, or why not: the one
    reading `start` reports and `restart` acts on. An ESCALATE in `decision.md` goes back as
    `decision-<n>.md`, its new run starting at round R, one past the newest round built or
    reviewed. With no `decision.md`, a restart record for a round not yet built, whose archive
    exists, is a restart cut short, to finish. A READY, a decision that won't read, or neither,
    is refused. Writes nothing."""
    path = folder / "decision.md"
    reviewed = [
        int(p.name[6:]) for p in (folder / "reviews").glob("round-*")
        if p.is_dir() and p.name[6:].isdigit()
    ]  # fmt: skip
    newest = max([build_round(folder), *reviewed])
    if path.is_file():
        decision, problem = read_decision(folder)
        if problem:
            return None, problem
        if decision == "READY":
            return None, (
                f"{folder.name}'s decision is READY: ship it with /sdlc:ship, or land it with "
                "/sdlc-factory:land; only an ESCALATE goes back to the factory"
            )
        archive, rnd, under_way = f"decision-{next_archive(folder)}.md", newest + 1, False
    else:
        restarts, _ = read_restarts(folder)
        last = restarts[-1] if restarts else None
        if not last or last["round"] <= newest:
            return None, (
                f"{folder.name} is at stage: test with no decision.md: there is no ESCALATE to "
                "send back"
            )
        archive, rnd, under_way = last["archive"], last["round"], True
    text = (folder / ("decision.md" if not under_way else archive)).read_text(encoding="utf-8")
    record = restart_path(folder, rnd).relative_to(folder).as_posix()
    return {
        "archive": archive, "round": rnd, "reconsider": reconsider_section(text) is not None,
        "reasons": text, "record": record, "under_way": under_way,
    }, None  # fmt: skip


def read_ledger(folder: Path) -> list[dict]:
    """`decisions.md` as records: id, who raised it and when, blocking or default, the question,
    and the person's answer once the line is ticked."""
    path = folder / "decisions.md"
    if not path.is_file():
        return []
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = LEDGER_RE.match(line)
        if m:
            text, _, answer = m.group(5).partition(DECIDED)
            found.append(
                {"id": m.group(2), "source": m.group(3), "kind": m.group(4), "text": text.strip()}
                | {"decided": m.group(1) == "x", "answer": answer.strip() or None}
            )
    return found


def raised_decisions(folder: Path) -> list[tuple[str, str, str]]:
    """Every `- DECISION:` line an agent's reply holds, oldest first, as (source, kind, text): the
    builder's reports in `build/round-<N>.md`, and the reviews in `reviews/round-<N>/<role>.md`."""
    found = []

    def rounds(base: Path, pattern: str) -> list[Path]:
        hits = [p for p in base.glob(pattern) if p.stem.split("-")[-1].isdigit()]
        return sorted(hits, key=lambda p: int(p.stem.split("-")[-1]))

    sources = [(p, f"builder round {p.stem[6:]}") for p in rounds(folder / "build", "round-*.md")]
    for path in rounds(folder / "reviews", "round-*"):
        sources += [(f, f"{f.stem} round {path.name[6:]}") for f in sorted(path.glob("*.md"))]
    for path, source in sources:
        for line in path.read_text(encoding="utf-8").splitlines():
            m = RAISED_RE.match(line)
            if m:
                found.append((source, m.group(1), m.group(2)))
    return found


def cmd_decisions(root: Path, ident: str) -> int:
    """Bring every decision the agents raised into `decisions.md`, once each, with a stable id,
    and say which blocking ones are still waiting for the person. The ledger is the one place a
    person answers: ticking a line with ` → decided: <answer>` is the answer."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    ledger = read_ledger(folder)
    known = {d["text"] for d in ledger}
    added = []
    new_lines = []
    for source, kind, text in raised_decisions(folder):
        if text not in known:
            known.add(text)
            added.append(f"D{len(ledger) + 1}")
            ledger.append(
                {"id": added[-1], "source": source, "kind": kind, "text": text}
                | {"decided": False, "answer": None}
            )
            new_lines.append(f"- [ ] {added[-1]} ({source}, {kind}): {text}\n")
    if new_lines:
        path = folder / "decisions.md"
        body = path.read_text(encoding="utf-8") if path.is_file() else "# Decisions\n\n"
        body += "" if body.endswith("\n") else "\n"
        path.write_text(body + "".join(new_lines), encoding="utf-8", newline="\n")
    pending = [d["id"] for d in ledger if d["kind"] == "blocking" and not d["decided"]]
    assumed = [d["id"] for d in ledger if d["kind"] == "default" and not d["decided"]]
    return emit(
        {"change": folder.name, "decisions": ledger, "added": added}
        | {"pending": pending, "assumed": assumed}
    )


def stop_text(change: str, way: str, problems: list[str]) -> str:
    """`runs/stopped.md`'s text: the way on, its sentence, and each problem on a line of its own."""
    ident = change.split("-", 1)[0]
    lines = [f"STOPPED: {way}", f"NEXT: {WAYS[way].format(id=ident)}", ""]
    lines += [f"- PROBLEM: {' '.join(p.split())}" for p in problems]
    return "\n".join(lines) + "\n"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_step(text: str) -> dict | None:
    """`runs/step.md`'s fields, or None when it doesn't open with a `STEP:` line."""
    lines = text.splitlines()
    step = STEP_RE.match(lines[0]) if lines else None
    if not step:
        return None

    def field(regex: re.Pattern) -> str | None:
        found = [m.group(1) for m in map(regex.match, lines) if m]
        return found[0] if found else None

    rnd, limit, names = field(ROUND_RE), field(LIMIT_RE), field(REVIEWERS_RE)
    return {
        "step": step.group(1), "round": int(rnd) if rnd else None,
        "limit": int(limit) if limit else None,
        "reviewers": [n.strip() for n in (names or "").split(",") if n.strip()],
        "since": field(SINCE_RE), "after": field(AFTER_RE),
    }  # fmt: skip


def step_text(out: dict, since: str, after: str | None = None) -> str:
    """`runs/step.md`'s text for one `verdicts` reading: the step, its round, the run's round
    limit and expected reviewers, since when, and on a `decide` the step it paused at."""
    rnd = "" if out.get("round") is None else str(out["round"])
    lines = [
        f"STEP: {out['next']}", f"ROUND: {rnd}", f"LIMIT: {out.get('limit') or ''}",
        f"REVIEWERS: {', '.join(out.get('reviewers') or [])}", f"SINCE: {since}",
    ]  # fmt: skip
    if after:
        lines.append(f"AFTER: {after}")
    return "\n".join(line.rstrip() for line in lines) + "\n"


def _record_step(folder: Path, out: dict) -> None:
    """Write `runs/step.md` for this reading, keeping the record's `SINCE:` while its step and
    round hold, and on a `decide` the step it paused at."""
    path = folder / STEP
    try:
        old = read_step(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        old = None
    same = old and old["step"] == out["next"] and old["round"] == out.get("round")
    since = old["since"] if same and old["since"] else _utc_now()
    after = None
    if out["next"] == "decide" and old:
        after = old["after"] if old["step"] == "decide" else old["step"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(step_text(out, since, after), encoding="utf-8", newline="\n")


def cmd_verdicts(root: Path, ident: str, head: str | None, record: bool = False) -> int:
    """The review rounds and the decision so far, and the step the loop takes next:

    - `build`: no builder report yet: run the builder (`build/round-1.md`).
    - `gate`: run `gate` on `round`'s build, which no attempt has judged as it stands now.
    - `fix`: the gate is red on `round`'s build: resume the builder with
      `build/round-<round>.gate.md`; its report is added to `build/round-<round>.md`. A red gate
      more than `GATE_FIXES` times in a round is a `stop`.
    - `review`: run the reviewers for `round` (all of them, or the `missing` ones), once its
      gate is green or the base branch names none (`gate` null, `gate_why`).
    - `verify`: run the verifier on `round`'s changes, before any rework.
    - `rework`: resume the builder with `round`'s kept changes; its report is
      `build/round-<round+1>.md`.
    - `approve`: carry what's unresolved to notes.md and run the approver.
    - `decide`: a blocking decision in `decisions.md` is waiting for the person (`pending`).
    - `done`: the decision is in.
    - `stop`: a problem, or `HEAD` moved: an agent committed, which none may.

    What has been built and what has been reviewed are compared by round: a builder report newer
    than the last complete review round is always reviewed, whether it came from a rework or from
    an answer the person gave, so no build reaches the approver unreviewed.

    A stop names its `way` on (`WAYS`): `ship` when `HEAD` moved, `mend` when every problem is a
    missing `## Evidence` or a verdict after a preamble in the last round (`preamble()`), with the
    roles to mend in `mend`, `rerun` otherwise. A role is mended once a round: one `runs/mended`
    names for that round no longer counts as mendable.

    Run `decisions` first: this reads the ledger as it stands, and writes nothing, but with
    `--record`, which only the supervisor passes and only with `--head`: then a stop is written to
    `runs/stopped.md` (`stop_text()`) for the board and status, from this same reading, and any
    other step removes it; and every reading is written to `runs/step.md` (`step_text()`) for the
    board's step track, its `SINCE:` kept while the step and round hold. Nothing in the loop reads
    either back.

    Beside the step: the run's `depth` (`depth()`), `reworked` (the paths the round to review
    changed since the last, from the snapshots), `settled` (what earlier rounds answered, never
    raised again), and for the verifier, `repeats` (a change raised again) and `untouched` (one on
    a path the change doesn't touch: pre-existing, never reworked).
    """
    if record and not head:
        why = "--record needs --head: without it a stop for HEAD moving would be removed"
        return emit({"refusals": [why]}, 1)
    out, refusal = loop_state(root, ident, head)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    if record:
        folder, _ = find_change(root, ident)
        path = folder / STOPPED
        if out["next"] == "stop":
            path.parent.mkdir(parents=True, exist_ok=True)
            text = stop_text(folder.name, out["way"], out["problems"])
            path.write_text(text, encoding="utf-8", newline="\n")
        else:
            path.unlink(missing_ok=True)
        _record_step(folder, out)
    return emit(out)


def loop_state(root: Path, ident: str, head: str | None) -> tuple[dict, str | None]:
    """What `verdicts` prints, or why not: one reading of the loop, so the step `verdicts` names
    and the prompt `agent` sends for it are made from the same state."""
    cfg, warnings = load_config(root)
    folder, refusal = find_change(root, ident)
    if refusal:
        return {}, refusal
    rounds, problems, run = _rounds_at_depth(root, folder, cfg)
    last = rounds[-1] if rounds else None
    changes = last and any(v["verdict"] == "CHANGES" for v in last["reviews"].values())
    kept = bool(last and last["verified"] and last["verified"]["kept"])
    # A restarted run's rounds count from its restart: round R is its first.
    restart = run["restart"]
    first = restart["round"] if restart else 1
    exhausted = bool(last and last["complete"] and changes and kept)
    exhausted = exhausted and last["round"] - first + 1 >= run["rounds"]
    decision, problem = read_decision(folder, exhausted)
    problems += [problem] if problem else []
    now = _git(root, "rev-parse", "--short", "HEAD")
    moved = bool(head) and now is not None and not now.startswith(head) and not head.startswith(now)
    out: dict = {"change": folder.name, "rounds": rounds, "decision": decision, "head": now}
    out.update(head_moved=moved, problems=problems, warnings=warnings, round=None, missing=[])
    out["mend"] = []
    out["exhausted"] = False
    out.update({k: run[k] for k in ("depth", "sensitive", "why", "reviewers")})
    out["limit"] = first - 1 + run["rounds"]
    out["restart"] = restart
    ledger = read_ledger(folder)
    out["pending"] = [d["id"] for d in ledger if d["kind"] == "blocking" and not d["decided"]]
    out["assumed"] = [d["id"] for d in ledger if d["kind"] == "default" and not d["decided"]]
    built = build_round(folder)
    out["built"] = built
    # A build no review round has read yet is gated first; a reviewed one never is again.
    unreviewed = bool(built) and (last is None or last["round"] < built)
    gate, out["gate_why"] = _gate_state(root, folder, built) if built else (None, None)
    out["gate"] = gate
    if gate and unreviewed and gate["current"] == "FAIL" and gate["fails"] > GATE_FIXES:
        problems.append(
            f"the gate failed {gate['fails']} times in round {built}: exit {gate['exit']}"
        )
    out["reworked"] = reworked(folder, built) if built else None
    out["settled"] = settled(rounds, last["round"] if last else 0)
    asked = [
        f"{role}: {c}"
        for role, r in (last["reviews"].items() if last else ())
        if r["verdict"] == "CHANGES"
        for c in r["changes"]
    ]
    out["repeats"] = [a for a in asked if a in out["settled"]]
    # With no base branch nothing is known to be touched, so nothing is called untouched.
    out["untouched"] = [a for a in asked if _untouched(root, a.split(": ", 1)[1], run["changed"])]
    # Kept apart as they're added, so a stop knows whether a mend alone can move it on: a missing
    # `## Evidence`, or a verdict after a preamble in the last round, each by the role that mends.
    mendable: dict[str, list[str]] = {}
    if built:
        report = folder / "build" / f"round-{built}.md"
        found = read_evidence(report.read_text(encoding="utf-8"), f"build/round-{built}.md")
        mendable["builder"] = found
    for r in rounds:
        for role in RUNS_THE_CHANGE:
            reply = folder / "reviews" / f"round-{r['round']}" / f"{role}.md"
            if role in r["reviews"]:
                where = f"reviews/round-{r['round']}/{role}.md"
                found = read_evidence(reply.read_text(encoding="utf-8"), where)
                mendable.setdefault(role, []).extend(found)
    problems += [p for found in mendable.values() for p in found]
    for role in REVIEWERS if last else ():
        if preamble(folder / "reviews" / f"round-{last['round']}" / f"{role}.md"):
            mendable.setdefault(role, []).append(_no_verdict(last["round"], role))
    # Each role is mended once a round: one already mended (`runs/mended`) is a stop like any other.
    done = mended(folder)
    rnd = last["round"] if last else 0
    for role in [r for r in mendable if (r, built if r == "builder" else rnd) in done]:
        del mendable[role]
    every = {p for found in mendable.values() for p in found}
    if moved:
        problems.append(f"HEAD moved from {head} to {now}: no agent may commit")
    if last and last["round"] > built:
        problems.append(f"reviews/round-{last['round']}/ has no build/round-{last['round']}.md")
    if problems:
        out["next"] = "stop"
        out["way"] = "ship" if moved else "mend" if set(problems) <= every else "rerun"
        if out["way"] == "mend":
            out["mend"] = [role for role, found in mendable.items() if found]
    elif out["pending"]:
        out["next"] = "decide"
    elif decision:
        out["next"] = "done"
    elif restart and restart["round"] > built:
        out["next"], out["round"] = "build", restart["round"]
    elif built == 0:
        out["next"], out["round"] = "build", 1
    elif unreviewed and gate and gate["current"] is None:
        out["next"], out["round"] = "gate", built
    elif unreviewed and gate and gate["current"] == "FAIL":
        out["next"], out["round"] = "fix", built
    elif unreviewed:
        out["next"], out["round"], out["missing"] = "review", built, list(run["reviewers"])
    elif not last["complete"]:
        out["next"], out["round"] = "review", last["round"]
        out["missing"] = [r for r in run["reviewers"] if r not in last["reviews"]]
    elif changes and last["verified"] is None:
        out["next"], out["round"] = "verify", last["round"]
    elif kept and last["round"] - first + 1 < run["rounds"]:
        out["next"], out["round"] = "rework", last["round"]
    else:
        out["next"], out["round"], out["exhausted"] = "approve", last["round"], exhausted
    return out, None


def cmd_carry(root: Path, ident: str) -> int:
    """Each change the last complete round still asks for and the verifier kept (every one, in a
    round from before there was a verifier), and every pre-existing problem a reviewer found, as an
    unticked `- [ ]` line in notes.md, so `/sdlc:ship` must give each a disposition. Once only: a
    line already there, ticked or not, isn't added again."""
    cfg, _ = load_config(root)
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    rounds, _, _ = _rounds_at_depth(root, folder, cfg)
    done = [r for r in rounds if r["complete"]]
    wanted = []
    if done:
        last = done[-1]
        if last["verified"] is not None:
            wanted += [f"{k['role']}: {k['change']}" for k in last["verified"]["kept"]]
        else:
            for role, review in last["reviews"].items():
                if review["verdict"] == "CHANGES":
                    wanted += [f"{role}: {text}" for text in review["changes"]]
    for r in rounds:
        for review in r["reviews"].values():
            wanted += [f"pre-existing: {text}" for text in review["preexisting"]]
    wanted = list(dict.fromkeys(wanted))
    notes = folder / "notes.md"
    text = notes.read_text(encoding="utf-8") if notes.is_file() else ""
    added = [item for item in wanted if item not in text]
    if added:
        if not text:
            text = NOTES_HEAD
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + "".join(f"- [ ] {item}\n" for item in added)
        notes.write_text(text, encoding="utf-8", newline="\n")
    return emit({"change": folder.name, "notes": str(notes), "added": added})


def _tree_hashes(root: Path, base: str) -> dict[str, str]:
    """Every path the change touches, as path → its content's sha256, or `deleted`: what a
    snapshot records, and what the gate compares before and after it runs."""
    found = {}
    for p in _changed_paths(root, base):
        file = root / p
        found[p] = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else "deleted"
    return found


def cmd_snapshot(root: Path, ident: str, n: int) -> int:
    """Write `build/round-<N>.files`: a hash of every path the change touches as round `n`'s build
    left it, so the next round's reviewers read what the rework changed. A file in the change's
    folder, never a commit, a stash or anything under `.git/`."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    if n < 1:
        return emit({"refusals": ["a round is 1 or more"]}, 1)
    base = _base(root)
    if base is None:
        return emit({"refusals": ["no base branch: set [git] base in .sdlc/config.toml"]}, 1)
    lines = [f"{digest}  {p}\n" for p, digest in _tree_hashes(root, base).items()]
    path = snapshot_path(folder, n)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8", newline="\n")
    rel = path.relative_to(root).as_posix()
    return emit({"change": folder.name, "snapshot": rel, "paths": len(lines)})


def gate_path(folder: Path, n: int) -> Path:
    return folder / "build" / f"round-{n}.gate.md"


def build_hash(folder: Path, n: int) -> str:
    """Round `n`'s build as the gate judges it: its report and its snapshot together. A fix adds
    to the report and is snapshotted again, so it is always a new build, gated again."""
    digest = hashlib.sha256()
    for path in (folder / "build" / f"round-{n}.md", snapshot_path(folder, n)):
        digest.update(path.read_bytes() if path.is_file() else b"")
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def land_gate_path(folder: Path, n: int) -> Path:
    """The gate on a change rebased while landing, landing round `n`: beside the builder's
    reports, never under `reviews/land-<n>/`, whose every file the landing reads as a review."""
    return folder / "build" / f"land-{n}.gate.md"


def read_gate(folder: Path, n: int) -> dict | None:
    """`build/round-<N>.gate.md` as its attempts, oldest first, each its verdict and the build it
    ran on, or None when the gate never ran on round `n`."""
    return read_gate_file(gate_path(folder, n))


def read_gate_file(path: Path) -> dict | None:
    """A gate file's attempts, oldest first, or None when there is none."""
    if not path.is_file():
        return None
    attempts: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        # The gate's output is indented, so a line of it never reads as a record's.
        if line.startswith("## Attempt "):
            attempts.append({"verdict": None, "build": None, "exit": None})
        elif attempts and (m := ATTEMPT_VERDICT_RE.match(line)):
            attempts[-1]["verdict"] = m.group(1)
        elif attempts and (m := BUILD_RE.match(line)):
            attempts[-1]["build"] = m.group(1)
        elif attempts and line.startswith("Exit: "):
            attempts[-1]["exit"] = line[len("Exit: ") :].strip()
    fails = sum(a["verdict"] == "FAIL" for a in attempts)
    return {"attempts": attempts, "fails": fails}


def _gate_state(root: Path, folder: Path, built: int) -> tuple[dict | None, str | None]:
    """The gate as it stands for round `built`'s build, or None and why there is no gate: the
    command, its fails so far this round, and the last attempt's verdict when it ran on this
    build exactly (`current`), else None, which calls for a fresh attempt."""
    base = _base(root)
    command = _base_check(root, base) if base else None
    if command is None:
        return None, "the base branch's .sdlc/config.toml has no [commands] check"
    record = read_gate(folder, built) or {"attempts": [], "fails": 0}
    last = record["attempts"][-1] if record["attempts"] else None
    now = build_hash(folder, built)
    current = last["verdict"] if last and last["build"] == now else None
    out = {"command": command, "round": built, "fails": record["fails"], "current": current}
    return out | {"exit": last["exit"] if last else None}, None


def landed_build(root: Path) -> str:
    """The change as a landing gates it: its commit, rebased onto the base branch."""
    return (_git(root, "rev-parse", "HEAD") or "")[:16]


def _land_gate_state(root: Path, folder: Path, n: int) -> dict | None:
    """The gate on landing round `n`'s rebased change, as `_gate_state` reads a build's: None when
    the base branch names no check."""
    base = _base(root)
    command = _base_check(root, base) if base else None
    if command is None:
        return None
    record = read_gate_file(land_gate_path(folder, n)) or {"attempts": [], "fails": 0}
    last = record["attempts"][-1] if record["attempts"] else None
    current = last["verdict"] if last and last["build"] == landed_build(root) else None
    return {"command": command, "current": current, "exit": last["exit"] if last else None}


def _placeholders(text: str, root: Path) -> str:
    """`text` with the main checkout's root, then `root` when it lies elsewhere, written as
    `CLONE_MARK`, and then the home directory as `HOME_MARK`: in that order, so a checkout under
    the home directory reads `<path-to-clone>/…`, never `~/…`. Each path is matched as given and
    resolved (macOS prints `/private/var` for `/var`), and in its POSIX form too."""
    checkouts = _all_checkouts(root)
    for path, mark in (
        (checkouts[0] if checkouts else root, CLONE_MARK),
        (root, CLONE_MARK),
        (Path.home(), HOME_MARK),
    ):
        forms = {str(path), path.as_posix(), str(path.resolve()), path.resolve().as_posix()}
        for form in sorted(forms - {"", "/", "."}, key=len, reverse=True):
            text = text.replace(form, mark)
    return text


def cmd_gate(root: Path, ident: str, land: bool = False) -> int:
    """Run the base branch's `[commands] check` in the change's worktree on its newest build, and
    add the attempt to `build/round-<N>.gate.md`; with `land`, on the change as a landing rebased
    it, into `build/land-<n>.gate.md`. PASS only on exit 0, within `GATE_TIMEOUT`, with the tree as
    it found it. Writes only that file, its copy of the output holding no path of this machine's
    (`_placeholders()`): the record is committed with the change."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    base = _base(root)
    if base is None:
        return emit({"refusals": ["no base branch: set [git] base in .sdlc/config.toml"]}, 1)
    command = _base_check(root, base)
    if command is None:
        why = "the base branch's .sdlc/config.toml has no [commands] check"
        return emit({"refusals": [why]}, 1)
    if land:
        n = land_round(folder)
        if n == 0:
            return emit({"refusals": ["no landing round is under way: run land first"]}, 1)
        path, build = land_gate_path(folder, n), landed_build(root)
    else:
        n = build_round(folder)
        if n == 0:
            return emit({"refusals": ["no builder report yet: build/round-1.md comes first"]}, 1)
        path, build = gate_path(folder, n), build_hash(folder, n)
    before = _tree_hashes(root, base)
    start = time.monotonic()
    try:
        done = subprocess.run(
            _sh(command), cwd=root, capture_output=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=GATE_TIMEOUT,
        )  # fmt: skip
        code, output = done.returncode, done.stdout + done.stderr
        exit_text = str(code)
    except subprocess.TimeoutExpired as e:
        # A timeout's partial output is bytes even in text mode.
        partial = [o.decode("utf-8", "replace") if isinstance(o, bytes) else o or "" for o in
                   (e.stdout, e.stderr)]  # fmt: skip
        code, output = None, "".join(partial) + f"\ntimed out after {GATE_TIMEOUT}s"
        exit_text = "timeout"
    except OSError as e:
        code, output, exit_text = None, f"didn't run: {e}", "didn't run"
    seconds = round(time.monotonic() - start, 1)
    after = _tree_hashes(root, base)
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    verdict = "PASS" if code == 0 and not changed else "FAIL"
    attempt = len((read_gate_file(path) or {"attempts": []})["attempts"]) + 1
    output = _placeholders(output, root)
    tail = "".join(f"    {line}\n" for line in output.rstrip().splitlines()[-GATE_TAIL:])
    tail = tail or "    (no output)\n"
    tree = f"changed: {', '.join(changed)}" if changed else "unchanged"
    section = (
        f"## Attempt {attempt}\n\nVerdict: {verdict}\nCommand: {command}\n"
        f"Build: {build}\nExit: {exit_text}\nSeconds: {seconds}\nTree: {tree}\n\n"
        f"Last {GATE_TAIL} lines of its output:\n\n{tail}"
    )
    # The first line is the latest verdict; the attempts before it stay as they were.
    earlier = path.read_text(encoding="utf-8").partition("\n")[2] if path.is_file() else ""
    earlier = earlier.rstrip("\n") + "\n" if earlier.strip() else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"GATE: {verdict}\n{earlier}\n{section}", encoding="utf-8", newline="\n")
    out = {"change": folder.name, "round": n, "attempt": attempt, "verdict": verdict}
    out.update(exit=exit_text, seconds=seconds, tree=tree, to=path.relative_to(root).as_posix())
    return emit(out, 0 if verdict == "PASS" else 1)


def set_stage(text: str, stage: str, today: str) -> tuple[str, list[str]]:
    """`text` with its frontmatter's `stage:` and `updated:` lines set, every other line as it
    was, and the keys it couldn't find. Edited by line, never round-tripped through YAML, which
    would turn `id: 008` into 8 and reorder the keys."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text, ["a --- frontmatter block"]
    wanted = {"stage": stage, "updated": today}
    seen = set()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            break
        key = lines[i].split(":", 1)[0].strip()
        if key in wanted:
            end = "\n" if lines[i].endswith("\n") else ""
            lines[i] = f"{key}: {wanted[key]}{end}"
            seen.add(key)
    return "".join(lines), [k for k in wanted if k not in seen]


def cmd_stage(root: Path, ident: str, stage: str) -> int:
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    if stage not in STAGES:
        return emit({"refusals": [f"a factory step sets one of {', '.join(STAGES)}"]}, 1)
    intent = folder / "intent.md"
    text, unplaced = set_stage(intent.read_text(encoding="utf-8"), stage, date.today().isoformat())
    if unplaced:
        return emit({"refusals": [f"intent.md has no {', '.join(unplaced)} line"]}, 1)
    intent.write_text(text, encoding="utf-8", newline="\n")
    out = {"change": folder.name, "stage": stage}
    if stage == "test":
        out["cost"] = run_cost(folder)
    return emit(out)


def cmd_restart(root: Path, ident: str, words: str | None) -> int:
    """Send an escalated change back to the factory, once the person said yes: the checks `start`
    made (`restart_state()`), then `build/round-<R>.restart.md`, then `decision.md` renamed to
    `decision-<n>.md`, byte for byte, then `stage: build`. With `words`, the id of the person's
    `(person, restart)` line in `decisions.md`, named in the record. Writes only the change's
    folder, commits nothing, never writes over an archive; a rerun finishes a restart cut short."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    intent = folder / "intent.md"
    meta = frontmatter(intent.read_text(encoding="utf-8"))
    tier = int(meta["tier"]) if meta.get("tier", "").isdigit() else None
    stage = meta.get("stage") or None
    if stage != "test" or tier not in (1, 2):
        why = f"restart takes a tier 1 or 2 change at stage: test; {folder.name} is tier {tier} "
        return emit({"refusals": [why + f"at stage: {stage}"]}, 1)
    restart, why = restart_state(folder)
    if why:
        return emit({"refusals": [why]}, 1)
    if words and read_restart_words(folder, words) is None:
        why = f"{words} isn't a `- [x] {words} (person, restart): …` line in decisions.md"
        return emit({"refusals": [why]}, 1)
    today = date.today().isoformat()
    text, unplaced = set_stage(intent.read_text(encoding="utf-8"), "build", today)
    if unplaced:
        return emit({"refusals": [f"intent.md has no {', '.join(unplaced)} line"]}, 1)
    archive = folder / restart["archive"]
    if not restart["under_way"]:
        if archive.exists():
            why = f"{restart['archive']} exists already: an archived decision is never written over"
            return emit({"refusals": [why]}, 1)
        record = folder / restart["record"]
        record.parent.mkdir(parents=True, exist_ok=True)
        body = f"RESTART: {restart['archive']}\n" + (f"WORDS: {words}\n" if words else "")
        record.write_text(body, encoding="utf-8", newline="\n")
        (folder / "decision.md").rename(archive)
    intent.write_text(text, encoding="utf-8", newline="\n")
    out = {"change": folder.name, "archive": restart["archive"], "round": restart["round"]}
    return emit(out | {"record": restart["record"], "words": words, "stage": "build"})


# ---------------------------------------------------------------- the agents, as sessions
#
# The supervisor starts each agent as a headless session of its own in the change's worktree, in
# the background, so it stays free while one runs and can take another change. `agent` is the one
# place this script runs `claude`: it composes the prompt from the loop's state, picks the model
# and the session, files the reply where the build's rules say, and records the session's id in
# `runs/<agent>.sessions`, which is how measuring tells an agent's session from the person's.

AGENT_TIMEOUT = 3 * 3600
# Each agent run's figures, one JSON object a line, beside the `.sessions` files measuring reads.
COSTS = Path("runs") / "costs.jsonl"
# A stopped run's record, written and removed only by `verdicts --record`, read by the board and
# `sdlc.py status` (each with its own copies of these, pinned by tests), never by the loop.
STOPPED = Path("runs") / "stopped.md"
STOPPED_RE = re.compile(r"^STOPPED: (mend|rerun|ship)\s*$")
NEXT_RE = re.compile(r"^NEXT: (.+?)\s*$")
PROBLEM_RE = re.compile(r"^- PROBLEM: (.+?)\s*$")
# The step the supervisor's last reading named, and since when: written on every reading by
# `verdicts --record`, read by the board (with its own copies of these, pinned by a test), never by
# the loop. `SINCE:` holds while `STEP:` and `ROUND:` do; `AFTER:` is the step a `decide` paused.
STEP = Path("runs") / "step.md"
STEP_RE = re.compile(r"^STEP: ([a-z]+)\s*$")
ROUND_RE = re.compile(r"^ROUND: ?(\d*)\s*$")
LIMIT_RE = re.compile(r"^LIMIT: ?(\d*)\s*$")
REVIEWERS_RE = re.compile(r"^REVIEWERS: ?(.*?)\s*$")
SINCE_RE = re.compile(r"^SINCE: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$")
AFTER_RE = re.compile(r"^AFTER: ([a-z]+)\s*$")
# What moves a stopped run on, by its way: the record's `NEXT:` line.
WAYS = {
    "ship": "an agent committed: read the commit, then ship it by hand with /sdlc:ship {id}",
    "mend": (
        "rerun /sdlc-factory:build {id}, whose one mend asks again for the missing ## Evidence or"
        " a verdict on the reply's first line; if that reply still lacks it, ship it by hand with"
        " /sdlc:ship {id}"
    ),
    "rerun": (
        "fix its cause, then /sdlc-factory:build {id}, or ship it by hand with /sdlc:ship {id}"
    ),
}
# The run's own token counts, as `runs/costs.jsonl` names them, from the result's `usage`.
USAGE_FIELDS = {
    "in": "input_tokens", "out": "output_tokens",
    "cache_create": "cache_creation_input_tokens", "cache_read": "cache_read_input_tokens",
}  # fmt: skip
TASKS = ("spec", "build", "fix", "review", "verify", "rework", "decided", "mend", "approve",
         "resolve", "land-review", "land-verify")  # fmt: skip
# The role each task runs as; `review`, `mend` and `land-review` are told theirs.
TASK_ROLE = {
    "spec": "spec-writer", "build": "builder", "fix": "builder", "verify": "verifier",
    "rework": "builder", "decided": "builder", "approve": "approver", "resolve": "builder",
    "land-verify": "verifier",
}  # fmt: skip
# The landing's tasks: the builder resolving a rebase's conflicts, and the review of the change
# as it now stands on the base branch. Never steps of the build's loop, so `verdicts` names none.
LAND_TASKS = ("resolve", "land-review", "land-verify")
# The step `verdicts` must name for a task to run, so no step is taken out of turn.
TASK_STEP = {"build": "build", "fix": "fix", "review": "review", "verify": "verify",
             "rework": "rework", "approve": "approve"}  # fmt: skip
# What the builder resumes on when a task carries on its own session.
RESUMES = ("fix", "rework", "decided", "mend", "resolve")
MEND = (
    "Your reply has no ## Evidence, or a command without its exit: run what your claims rest on "
    "again and reply with it."
)
# The mends `agent` has filed, `<role> <round>` a line: the record that holds each to once a round.
MENDED = Path("runs") / "mended"
VERDICT_MEND = (
    "Your reply didn't open with its verdict. Reply again, the whole reply, with its VERDICT: line "
    "as the first line and nothing before it."
)
# What a spec draft must have before the person sees it; a draft missing one is sent back once.
RECHECK = (
    "Your draft is missing one of these: every <...> prompt replaced, the requirements numbered "
    "and each checkable, a Contracts touched line for each invariant the change comes near. Draft "
    "it again with all three."
)
# The person's words for a revised spec draft, written to `decisions.md` before the run's gate:
# the only way free text reaches an agent session, never through a shell argument.
REVISION_RE = re.compile(r"^- \[x\] (R\d+) \(person, revise\): (.+?)\s*$")


def read_revision(folder: Path, ident: str) -> str | None:
    """The person's words for revision `ident` (`R1`) in `decisions.md`, or None."""
    path = folder / "decisions.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        m = REVISION_RE.match(line)
        if m and m.group(1) == ident:
            return m.group(2)
    return None


def mend_round(state: dict, role: str) -> int:
    """The round a mend for `role` answers for: the builder's report's, or the last review's."""
    if role == "builder":
        return state["built"]
    return state["rounds"][-1]["round"] if state.get("rounds") else 0


def mended(folder: Path) -> set[tuple[str, int]]:
    """(role, round) for each mend `agent` has filed, from `runs/mended`: each role is mended once
    a round, and a second reply that still needs one is a stop like any other."""
    path = folder / MENDED
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        role, _, rnd = line.partition(" ")
        if rnd.strip().isdigit():
            found.add((role, int(rnd)))
    return found


def verdict_mend(folder: Path, state: dict, role: str | None) -> bool:
    """Whether `mend` for `role` is a reviewer's verdict to put first: its reply in the last round
    holds one after a preamble."""
    rnd = state["rounds"][-1]["round"] if state.get("rounds") else 0
    reply = folder / "reviews" / f"round-{rnd}" / f"{role}.md"
    return bool(rnd) and role in REVIEWERS and preamble(reply)


def agent_name(role: str) -> str:
    """The agent definition a role runs as: `reviewer-<role>` for a reviewer."""
    return f"reviewer-{role}" if role in REVIEWERS else role


def _figures(data: dict) -> dict | None:
    """A run's figures from its `--output-format json` result, numbers only, or None when it
    holds none. `usage` and `duration_ms` are the run's own; `total_cost_usd` is the session's
    total so far, which on a `--resume` includes the runs before it, so `run_cost()` takes a
    session's last one. A field missing or not a number is None."""

    def num(value: object) -> int | float | None:
        return value if isinstance(value, int | float) and not isinstance(value, bool) else None

    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    figures = {
        "cost_usd": num(data.get("total_cost_usd")),
        "duration_ms": num(data.get("duration_ms")),
        "turns": num(data.get("num_turns")),
        **{key: num(usage.get(field)) for key, field in USAGE_FIELDS.items()},
    }
    return figures if any(v is not None for v in figures.values()) else None


def _claude(argv: list[str], cwd: Path) -> tuple[int, str, str | None, dict | None]:
    """Run one headless agent session and return its exit, its reply (the JSON's `result`), what
    went wrong, and its figures (`_figures()`), a failed session's included. Text mode in UTF-8
    whatever the locale, no shell, nothing read from stdin."""
    try:
        done = subprocess.run(
            argv, cwd=cwd, capture_output=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=AGENT_TIMEOUT,
        )  # fmt: skip
    except subprocess.TimeoutExpired:
        return 124, "", f"the agent ran past {AGENT_TIMEOUT // 60} minutes", None
    except OSError as e:
        return 127, "", f"claude couldn't be run: {e}", None
    try:
        data = json.loads(done.stdout)
    except ValueError:
        data = {}
    data = data if isinstance(data, dict) else {}
    figures = _figures(data)
    reply = data.get("result") if isinstance(data.get("result"), str) else ""
    if done.returncode or data.get("is_error") or not reply.strip():
        tail = (done.stderr or done.stdout or "").strip()[-500:]
        return done.returncode or 1, "", f"the agent session failed: {tail or 'no reply'}", figures
    return 0, reply, None, figures


def record_cost(folder: Path, session: str, role: str, model: str, figures: dict) -> None:
    """Add one run's figures to the change's `runs/costs.jsonl`, with its session, role and
    model: numbers and names only, never a prompt or a reply."""
    path = folder / COSTS
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"session": session, "role": role, "model": model, **figures})
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def run_cost(folder: Path) -> dict:
    """What the change's agent runs cost so far, from `runs/costs.jsonl`: `usd`, each session's
    last reported total summed (Claude Code's API-equivalent figure, not a bill), split `by_role`
    and `by_model`; `tokens`, every run's own usage summed; `runs`, the lines read; and `unknown`,
    the sessions that reported no cost and the lines that don't parse, which are skipped."""
    path = folder / COSTS
    last: dict[str, dict] = {}
    tokens = dict.fromkeys(USAGE_FIELDS, 0)
    runs = unknown = 0
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        if not isinstance(row, dict) or not isinstance(row.get("session"), str):
            unknown += 1 if line.strip() else 0
            continue
        runs += 1
        for key in tokens:
            tokens[key] += row.get(key) if isinstance(row.get(key), int) else 0
        if isinstance(row.get("cost_usd"), int | float) or row["session"] not in last:
            last[row["session"]] = row
    usd, by_role, by_model = 0.0, {}, {}
    for row in last.values():
        cost = row.get("cost_usd")
        if not isinstance(cost, int | float):
            unknown += 1
            continue
        usd += cost
        for split, key in ((by_role, "role"), (by_model, "model")):
            name = str(row.get(key) or "unknown")
            split[name] = round(split.get(name, 0.0) + cost, 4)
    return {
        "usd": round(usd, 4), "by_role": by_role, "by_model": by_model,
        "runs": runs, "unknown": unknown, "tokens": tokens,
    }  # fmt: skip


def _task(
    root: Path,
    folder: Path,
    state: dict,
    task: str,
    role: str,
    decided: str | None,
    revise: str | None = None,
    recheck: bool = False,
) -> tuple[str, Path | None, bool] | str:
    """The prompt a task sends, the file its reply goes to (None for the spec draft, which waits
    for the person's yes), and whether the reply is added to that file: or why it can't run now.
    The wording is the build's own; every builder report goes to `build/round-<R+1>.md`, `<R>`
    the highest review round so far, unless it answers a decision before its round's review."""
    rel = folder.relative_to(root).as_posix()
    head = f"Change folder: {rel}. Worktree: {root}. "
    step = TASK_STEP.get(task)
    if step and state["next"] != step:
        return f"verdicts says {state['next']!r}, not {step!r}"
    rnd = state["round"]
    reviews_dir = folder / "reviews" / f"round-{rnd}"
    if task in LAND_TASKS:
        return _land_task(root, folder, task, role)
    if task == "spec" and revise:
        words = read_revision(folder, revise)
        if words is None:
            return f"{revise} isn't a `- [x] {revise} (person, revise): …` line in decisions.md"
        return f"Revise your draft, as the person asks: {words}", None, False
    if task == "spec" and recheck:
        return RECHECK, None, False
    if task == "spec":
        return head + "Draft spec.md for this change.", None, False
    restart = state.get("restart")
    if task == "build" and restart and rnd == restart["round"]:
        # A fresh builder, told why the approver escalated: never resumed on the old approach.
        text = (folder / restart["archive"]).read_text(encoding="utf-8")
        prompt = head + (
            f"The approver escalated this change after round {rnd - 1}, and the person sent it "
            f"back for another build: read {rel}/{restart['archive']} and build round {rnd} to "
            "answer it, plan.md first where the approach changes, then the code, test first."
        )
        section = reconsider_section(text)
        if section:
            prompt += "\n\n" + section
        if restart["words"]:
            prompt += f"\n\nThe person adds: {read_restart_words(folder, restart['words'])}"
        return prompt, folder / "build" / f"round-{rnd}.md", False
    if task == "build":
        return (
            head + "Build it: plan.md first (Tier 2), then the code, test first.",
            (folder / "build" / "round-1.md"),
            False,
        )
    if task == "fix":
        # Added to the round's report, as an answer before review is: the round isn't reviewed.
        return (
            f"The gate failed on round {rnd}: read {rel}/build/round-{rnd}.gate.md, fix what it "
            "shows, then report.",
            folder / "build" / f"round-{rnd}.md",
            True,
        )
    if task == "review":
        if role not in state["missing"]:
            return f"{role} isn't among round {rnd}'s missing reviewers: {state['missing']}"
        prompt = head + f"Review round {rnd}."
        before = [r for r in state["rounds"] if r["round"] < rnd and role in r["reviews"]]
        if before and state["reworked"] is not None:
            prev = next((r for r in state["rounds"] if r["round"] == rnd - 1), None)
            kept = (prev or {}).get("verified") or {"kept": []}
            prompt += (
                f" Reworked: {', '.join(state['reworked']) or 'nothing'}. Kept last round: "
                f"{'; '.join(k['role'] + ': ' + k['change'] for k in kept['kept']) or 'none'}. "
                f"Settled, never raise again: {'; '.join(state['settled']) or 'none'}."
            )
        return prompt, reviews_dir / f"{role}.md", False
    if task == "verify":
        current = next(r for r in state["rounds"] if r["round"] == rnd)
        asked = [f"- {i}: {name}: {c}" for i, name, c in asked_changes(current["reviews"])]
        return (
            head + f"Verify round {rnd}.\n" + "\n".join(asked) + "\n"
            f"Untouched: {'; '.join(state['untouched']) or 'none'}. "
            f"Repeats: {'; '.join(state['repeats']) or 'none'}. "
            f"Settled: {'; '.join(state['settled']) or 'none'}.",
            reviews_dir / VERIFIED,
            False,
        )
    if task == "rework":
        # Each kept change in the reviewer's own words, as `read_verified()` resolved it: the
        # verifier's line is its own summary, by id.
        current = next(r for r in state["rounds"] if r["round"] == rnd)
        kept = (current["verified"] or {"kept": []})["kept"]
        return (
            f"Round {rnd}'s changes are verified in {rel}/reviews/round-{rnd}/{VERIFIED}. Address "
            "every KEPT line, then report. The kept changes, in the reviewers' words:\n"
            + "\n".join(f"- {k['role']}: {k['change']}" for k in kept),
            folder / "build" / f"round-{rnd + 1}.md",
            False,
        )
    if task == "approve":
        prompt = head + "Decide."
        if state["exhausted"]:
            prompt += (
                " The rounds ran out with changes still kept: say whether the approach should "
                "be reconsidered."
            )
        return prompt, folder / "decision.md", False
    reviewed = state["rounds"][-1]["round"] if state["rounds"] else 0
    if task == "decided":
        entry = next((d for d in read_ledger(folder) if d["id"] == decided), None)
        if entry is None or not entry["decided"]:
            return f"{decided} isn't a decided line in decisions.md"
        prompt = f"{decided} is decided in decisions.md: {entry['answer']}. Continue."
        if not entry["source"].startswith("builder"):
            prompt += f" Round {reviewed}'s reviews are in {rel}/reviews/round-{reviewed}/."
        target = folder / "build" / f"round-{reviewed + 1}.md"
        return prompt, target, target.is_file() and state["built"] == reviewed + 1
    # mend: the stops a run mends itself, once each: a reviewer resumed to put its verdict first,
    # the builder resumed for its evidence, or a new behaviour check for its own.
    if verdict_mend(folder, state, role):
        return (
            VERDICT_MEND,
            folder / "reviews" / f"round-{reviewed}" / f"{role}.md",
            False,
        )
    if role == "builder":
        return MEND, folder / "build" / f"round-{state['built']}.md", False
    if role in RUNS_THE_CHANGE:
        return (
            head + f"Review round {reviewed}. " + MEND,
            (folder / "reviews" / f"round-{reviewed}" / f"{role}.md"),
            False,
        )
    return f"only the builder and {', '.join(RUNS_THE_CHANGE)} owe evidence"


def _land_task(root: Path, folder: Path, task: str, role: str) -> tuple[str, Path, bool] | str:
    """The landing's prompts: the builder, resumed, resolving the files a rebase left conflicted;
    a reviewer reading the change as it now stands on the base branch; the verifier on what they
    asked for. Each reply goes under `reviews/land-<n>/`, the builder's to `build/land-<n>.md`."""
    n = land_round(folder)
    if not n:
        return "no landing round is under way: run land first"
    rel = folder.relative_to(root).as_posix()
    head = f"Change folder: {rel}. Worktree: {root}. "
    where = folder / "reviews" / f"land-{n}"
    base = _base(root) or "the base branch"
    if task == "resolve":
        files = _conflicted(root)
        if not files:
            return "no conflicted file: run resolve first"
        return (
            f"The base branch moved under this change, and rebasing onto it conflicts in: "
            f"{', '.join(files)}. Resolve each, keeping what both sides meant; edit only those "
            "files, run no git command, then report what you kept from each side, ending with "
            "## Evidence.",
            folder / "build" / f"land-{n}.md",
            False,
        )
    if task == "land-review":
        if role not in REVIEWERS:
            return f"land-review needs --role, one of {', '.join(REVIEWERS)}"
        resolved = (folder / "runs" / "land-resolved").is_file()
        why = (
            f"its conflicts resolved by the builder, in build/land-{n}.md"
            if resolved
            else ("with no conflict")
        )
        return (
            head + f"Review landing round {n}: the change was rebased onto {base}, {why}. Review "
            f"its whole diff against {base} as it now stands.",
            where / f"{role}.md",
            False,
        )
    reviews = {}
    for file in where.glob("*.md"):
        lines = file.read_text(encoding="utf-8").splitlines()
        m = VERDICT_RE.match(lines[0]) if file.name != VERIFIED and lines else None
        if m:
            changes = [c.group(1) for c in map(CHANGE_RE.match, lines[1:]) if c]
            reviews[file.stem] = {"verdict": m.group(1), "changes": changes}
    asked = [f"- {i}: {name}: {c}" for i, name, c in asked_changes(reviews)]
    if not asked:
        return f"landing round {n} asks for no change: there is nothing to verify"
    return (head + f"Verify landing round {n}.\n" + "\n".join(asked), where / VERIFIED, False)


def cmd_agent(
    root: Path,
    ident: str,
    task: str,
    role: str | None,
    decided: str | None,
    revise: str | None = None,
    recheck: bool = False,
) -> int:
    """Run one agent for one step of the change's loop, as a session of its own in the change's
    worktree, and file its reply: the builder resumed with its context for a rework, an answer or
    a mend, the spec-writer for a revision or a recheck of its draft, every other agent a fresh
    session. Writes only in the change's folder: the reply, `runs/<agent>.sessions`, and the run's
    figures in `runs/costs.jsonl`. A failed session files no reply, only its figures when it
    reported any, and is reported, never retried."""
    state, refusal = loop_state(root, ident, None)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    cfg, _ = load_config(root)
    folder, _ = find_change(root, ident)
    role = role or TASK_ROLE.get(task)
    if task == "review" and role not in REVIEWERS:
        return emit({"refusals": [f"review needs --role, one of {', '.join(REVIEWERS)}"]}, 1)
    if task == "mend" and role is None:
        why = "mend needs --role: builder, behaviour, or the reviewer `verdicts` names in `mend`"
        return emit({"refusals": [why]}, 1)
    if task == "mend" and (role, mend_round(state, role)) in mended(folder):
        why = f"{role} was mended once in round {mend_round(state, role)}: a second is a stop"
        return emit({"refusals": [why]}, 1)
    if task == "decided" and not decided:
        return emit({"refusals": ["decided needs --decision D<n>"]}, 1)
    if (revise or recheck) and task != "spec":
        return emit({"refusals": ["--revise and --recheck are for --task spec"]}, 1)
    planned = _task(root, folder, state, task, role, decided, revise, recheck)
    if isinstance(planned, str):
        return emit({"refusals": [planned]}, 1)
    prompt, target, append = planned
    if role in UI_REVIEWERS and task in ("review", "land-review"):
        if not ui_complete(cfg["ui"]):
            return emit({"refusals": ["the base branch's [ui] needs serve, shoot and paths"]}, 1)
        label = f"round-{state['round']}" if task == "review" else f"land-{land_round(folder)}"
        paths, record = shots(root, folder, label, cfg["ui"])
        if record["problem"]:
            why = f"the screenshots failed, so the {role} review doesn't run blind: "
            return emit({"refusals": [why + record["problem"]], "shots": record}, 1)
        base = _base(root)
        changed = _changed_paths(root, base) if base else []
        prompt += (
            f" Screenshots: {', '.join(p.as_posix() for p in paths)}. "
            f"Changed: {', '.join(changed) or 'nothing'}."
        )
    sessions = folder / "runs" / f"{agent_name(role)}.sessions"
    resumed = (role == "builder" and task in RESUMES) or bool(
        task == "spec" and (revise or recheck)
    )
    resumed = resumed or (task == "mend" and verdict_mend(folder, state, role))
    if resumed:
        ids = sessions.read_text(encoding="utf-8").split() if sessions.is_file() else []
        if not ids:
            first = {"builder": "build", "spec-writer": "spec"}.get(role, "review")
            return emit({"refusals": [f"no {role} session to resume: run --task {first} first"]}, 1)
        session, how = ids[-1], "--resume"
    else:
        session, how = str(uuid.uuid4()), "--session-id"
        sessions.parent.mkdir(parents=True, exist_ok=True)
        with sessions.open("a", encoding="utf-8", newline="\n") as f:
            f.write(session + "\n")
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    tier = int(meta["tier"]) if meta.get("tier", "").isdigit() else None
    model = model_for(role, cfg, tier, state["depth"])
    argv = ["claude", "-p", prompt, "--agent", f"sdlc-factory:{agent_name(role)}"]
    argv += ["--model", model, "--permission-mode", cfg["mode"], "--output-format", "json"]
    argv += [how, session]
    code, reply, problem, figures = _claude(argv, root)
    if figures:
        record_cost(folder, session, role, model, figures)
    out = {"change": folder.name, "task": task, "role": role, "model": model, "session": session}
    out.update(to=target.relative_to(root).as_posix() if target else None, exit=code)
    if problem:
        return emit({**out, "problem": problem}, 1)
    if target is None:
        return emit({**out, "reply": reply})
    target.parent.mkdir(parents=True, exist_ok=True)
    text = reply if reply.endswith("\n") else reply + "\n"
    if append:
        before = target.read_text(encoding="utf-8")
        text = before + ("" if before.endswith("\n") else "\n") + "\n" + text
    target.write_text(text, encoding="utf-8", newline="\n")
    if task == "mend":
        with (folder / MENDED).open("a", encoding="utf-8", newline="\n") as f:
            f.write(f"{role} {mend_round(state, role)}\n")
    return emit(out)


def _waits(change: dict, names: list[str]) -> bool:
    """Whether a ready change depends on another of `names` that hasn't shipped yet."""
    others = [n for n in names if n != change["change"]]
    return any(names_change(n, d) for d in change["depends_on"] for n in others)


def cmd_ready(root: Path) -> int:
    """The changes ready to ship: each open worktree's change at `stage: test` with a decision,
    its `depends_on:`, what its agent runs cost (`run_cost()`), and the other ready changes its
    diff shares a path with, ordered so a change comes after what it depends on. Read-only: the
    person ships, each from its own worktree, or `/sdlc-factory:land` lands them as a batch, in
    this order."""
    return emit({"ready": [{k: v for k, v in r.items() if k != "paths"} for r in ready(root)]})


def ready(root: Path) -> list[dict]:
    """`cmd_ready`'s list, each change with its changed `paths` too."""
    base = _base(root)
    ready = []
    for path, branch in worktrees(root):
        folder = path / work_rel(path) / branch
        if not DIR_RE.match(branch) or not (folder / "intent.md").is_file():
            continue
        meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
        decision, _ = read_decision(folder)
        # `shipped` with its worktree still open: a landing stopped after its commit, to finish.
        if meta.get("stage") not in ("test", "shipped") or decision is None:
            continue
        ready.append({
            "change": branch, "worktree": str(path), "decision": decision,
            "depends_on": re.findall(r"\d{3,}", meta.get("depends_on", "")),
            "cost": run_cost(folder),
            "paths": set(_changed_paths(path, base)) if base else set(),
        })  # fmt: skip
    for r in ready:
        r["overlaps"] = sorted(o["change"] for o in ready if o is not r and r["paths"] & o["paths"])
    order, left = [], sorted(ready, key=lambda r: r["change"])
    while left:
        names = [o["change"] for o in left]
        free = [r for r in left if not _waits(r, names)]
        pick = free[0] if free else left[0]  # a cycle: by id, and the overlaps say why
        order.append(pick)
        left.remove(pick)
    return order


# ---------------------------------------------------------------- landing, through sdlc's own code
#
# `/sdlc-factory:land` lands a batch of ready changes: each one shipped, committed, brought up to
# date with the base branch and closed, by `sdlc.py`'s own `ship`, `base` and `close`, never a copy
# of them. The two plugins always release as one version, so the `sdlc.py` this runs is the one of
# its own version, beside it: the clone's, read in place, or the marketplace cache's. It is run,
# never imported, and only for landing. The batch's one gate passes itself when no change in it
# carries a risk signal (`land-check`), recorded on each change's commit as `Sdlc-Landed: by=auto`.

FACTORY_ROOT = Path(__file__).resolve().parents[1]
SDLC_TIMEOUT = 3600
# The environment a landing step runs `sdlc.py` in: without a flag that would stop close handing
# itself to the main checkout's script, or ship to the change's own, and without this session's
# virtualenv, so `uv` builds the script's own.
UNSET_FOR_SDLC = ("SDLC_CLOSE_RAN", "SDLC_OWN_SCRIPT", "VIRTUAL_ENV")
# What the approver proposes as the change's release impact, read by land.
IMPACT_RE = re.compile(r"^\s*- IMPACT:\s*(major|minor|patch|none)\b")
# Who passed the batch's gate, on each landed change's commit: the person, or no one (`auto`).
LANDED = "Sdlc-Landed"
FRESH_SKIPPED = "Fresh review: skipped, the factory's rounds stand in"


def _plugin(root: Path) -> dict:
    try:
        data = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def sdlc_path(factory: Path = FACTORY_ROOT) -> tuple[Path | None, str | None]:
    """The `sdlc` plugin's `scripts/sdlc.py` of this factory's own version, or why there is none:
    the clone's, when the factory is read in place from `plugins/factory/` inside it, else the
    marketplace cache's, `<cache>/<marketplace>/sdlc/<version>/` beside the factory's
    `<cache>/<marketplace>/sdlc-factory/<version>/`. A copy of another version is refused: landing
    runs the code this factory was released with."""
    mine = _plugin(factory).get("version")
    candidates = [factory.parents[1], factory.parents[1] / "sdlc" / str(mine)]
    for root in candidates:
        found = _plugin(root)
        if found.get("name") == "sdlc" and (root / "scripts" / "sdlc.py").is_file():
            if found.get("version") != mine:
                return None, (
                    f"sdlc at {root} is version {found.get('version')}, this factory {mine}: "
                    "update both to one version"
                )
            return root / "scripts" / "sdlc.py", None
    return None, f"no sdlc {mine} beside this factory: install sdlc, which the factory depends on"


def _sdlc(args: list[str], cwd: Path) -> tuple[int, dict | None, str]:
    """Run `sdlc.py <args>` of this factory's own version from `cwd`, and return its exit, its
    JSON when it printed one, and its output. Text mode in UTF-8, no shell, nothing on stdin."""
    path, why = sdlc_path()
    if path is None:
        return 1, None, why or ""
    uv = shutil.which("uv")
    argv = [uv, "run", "--quiet", "--script"] if uv else [sys.executable]
    env = {k: v for k, v in os.environ.items() if k not in UNSET_FOR_SDLC}
    try:
        done = subprocess.run(
            [*argv, str(path), *args], cwd=cwd, capture_output=True, encoding="utf-8",
            errors="replace", stdin=subprocess.DEVNULL, env=env, timeout=SDLC_TIMEOUT,
        )  # fmt: skip
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, None, f"sdlc.py {args[0]} couldn't run: {e}"
    try:
        data = json.loads(done.stdout)
    except ValueError:
        data = None
    return done.returncode, data if isinstance(data, dict) else None, done.stdout + done.stderr


def cmd_sdlc_path() -> int:
    path, why = sdlc_path()
    return emit(
        {"sdlc": str(path) if path else None, "refusals": [why] if why else []}, 0 if path else 1
    )


def read_impact(folder: Path) -> str | None:
    """The release impact the approver proposed in `decision.md`'s `- IMPACT:` line."""
    path = folder / "decision.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        if m := IMPACT_RE.match(line):
            return m.group(1)
    return None


def land_signals(folder: Path, worktree: Path, decision: str, cfg: dict) -> tuple[list, list]:
    """Why change `folder` needs the person at the batch's gate (`signals`), and why it can't land
    in a batch at all, only by hand (`excluded`): what `sdlc.py preflight` reads of its risk, its
    notes, its checks, its skills' cases and its issues, and what the run left in its folder."""
    signals, excluded = [], []
    code, pre, out = _sdlc(["preflight", folder.name], worktree)
    if pre is None:
        return [f"preflight couldn't be read: {out.strip()[-300:]}"], []
    risk = pre.get("risk") or {}
    if risk.get("sensitive"):
        signals.append(f"touches sensitive paths: {', '.join(risk['sensitive'][:5])}")
    if risk.get("irreversible"):
        signals.append(f"touches irreversible paths: {', '.join(risk['irreversible'][:5])}")
    if (pre.get("closes") or {}).get("closes"):
        signals.append("came from a public issue (closes:)")
    impact = read_impact(folder)
    if impact is None:
        signals.append("decision.md proposes no `- IMPACT:`")
    elif impact == "major":
        signals.append("impact: major")
    if decision == "ESCALATE":
        signals.append("the approver escalated")
    ledger = read_ledger(folder)
    if [d for d in ledger if not d["decided"]]:
        signals.append("decisions still open or assumed in decisions.md")
    if (folder / "runs" / "land-resolved").is_file():
        signals.append("a conflict was resolved while landing")
    if not cfg["land"]["auto"]:
        signals.append("land.auto is off on the base branch")
    if (pre.get("undone") or {}).get("items"):
        excluded.append("notes.md has undone items, which only a person gives a disposition")
    if (pre.get("checks") or {}).get("checks"):
        excluded.append("checks.md has acceptance checks, which run only under a prompt")
    if (pre.get("cases") or {}).get("scope"):
        excluded.append("its skills' cases are in scope, a paid run that is the person's call")
    return signals, excluded


def cmd_land_check(root: Path, idents: list[str]) -> int:
    """The batch: the ready changes in `ready`'s order (or those named), at most `land.batch`, each
    with its signals and why any is left out, and `clear`: true when no change in it has a signal,
    so the gate passes itself. Read-only."""
    cfg, warnings = load_config(root)
    picked = [
        r for r in ready(root) if not idents or any(names_change(r["change"], i) for i in idents)
    ]
    batch, left_out, over = [], [], []
    for r in picked:
        worktree = Path(r["worktree"])
        folder = worktree / work_rel(worktree) / r["change"]
        signals, excluded = land_signals(folder, worktree, r["decision"], cfg)
        entry = {
            "change": r["change"], "worktree": r["worktree"], "decision": r["decision"],
            "impact": read_impact(folder), "signals": signals, "overlaps": r["overlaps"],
        }  # fmt: skip
        if excluded:
            left_out.append({**entry, "excluded": excluded})
        elif len(batch) >= cfg["land"]["batch"]:
            over.append(r["change"])
        else:
            batch.append(entry)
    clear = bool(batch) and not any(c["signals"] for c in batch)
    return emit({
        "batch": batch, "excluded": left_out, "over_limit": over, "clear": clear,
        "auto": cfg["land"]["auto"], "limit": cfg["land"]["batch"], "warnings": warnings,
    })  # fmt: skip


def land_message(root: Path, folder: Path, by: str, refs: bool) -> str:
    """The landed change's commit message: its title, its Problem's first sentence and its folder,
    `Refs #N` when its number is its issue's, and who passed the gate. No `Sdlc-Findings`: the
    factory's rounds stood in for ship's review, and retro reads a missing line as unanswered."""
    text = (folder / "intent.md").read_text(encoding="utf-8")
    title = next((ln for ln in text.splitlines() if ln.startswith("# ")), f"# {folder.name}")
    title = re.sub(r"^#\s+\d{3,}\s+—\s+", "", title).lstrip("# ").strip()
    problem = text.split("## Problem", 1)[1] if "## Problem" in text else ""
    prose = " ".join(problem.split("\n## ", 1)[0].split())
    first = re.split(r"(?<=[.!?])\s", prose, maxsplit=1)[0] if prose else ""
    body = f"{first} See {folder.relative_to(root).as_posix()}/.".strip()
    tail = [f"Refs #{int(folder.name.split('-')[0])}"] if refs else []
    tail.append(f"{LANDED}: by={by}")
    return f"{title}\n\n{body}\n\n" + "\n".join(tail) + "\n"


def _set_impact(intent: Path, impact: str) -> bool:
    """`intent.md`'s `impact:` line set in place, by line, never through YAML."""
    lines = intent.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            break
        if line.split(":", 1)[0].strip() == "impact":
            lines[i] = f"impact: {impact}\n"
            intent.write_text("".join(lines), encoding="utf-8", newline="\n")
            return True
    return False


def land_round(folder: Path) -> int:
    """The landing review round under way: `reviews/land-<n>/`, the highest, 0 before any."""
    found = [p.name[5:] for p in (folder / "reviews").glob("land-*") if p.is_dir()]
    return max((int(n) for n in found if n.isdigit()), default=0)


def cmd_land(root: Path, ident: str, by: str) -> int:
    """Land change `ident`'s first half, in its worktree: the approver's impact on `intent.md`,
    `sdlc.py ship` (stamped, the seed dropped, every path staged), the commit with
    `land_message()`, then `sdlc.py base`. Its `state`: `current` (nothing to review again),
    `rebased` (the base moved: the gate and the spec's path run again before close), `conflict`
    (the rebase was aborted: `resolve` takes it), or `refused`, with why."""
    folder, refusal = find_change(root, ident)
    out: dict = {"change": None, "state": "refused", "refusals": []}
    if refusal:
        return emit({**out, "refusals": [refusal]}, 1)
    out["change"] = folder.name
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    impact = read_impact(folder)
    decision = read_decision(folder)[0]
    if meta.get("stage") not in ("test", "shipped") or decision is None:
        return emit(
            {**out, "refusals": [f"{folder.name} isn't ready: stage test with a decision"]}, 1
        )
    # The gate's rule is the script's, never only the skill's: a change only a person can ship is
    # refused whoever passed the gate, and `auto` is refused while any risk signal stands.
    cfg, _ = load_config(root)
    signals, excluded = land_signals(folder, root, decision, cfg)
    if excluded:
        return emit({**out, "refusals": [f"ship it by hand: {'; '.join(excluded)}"]}, 1)
    if by == "auto" and signals:
        return emit({**out, "refusals": [f"the gate is the person's: {'; '.join(signals)}"]}, 1)
    if meta.get("stage") == "test":
        if impact is None or not _set_impact(folder / "intent.md", impact):
            return emit({**out, "refusals": ["no impact to set: decision.md has no - IMPACT:"]}, 1)
        code, pre, _ = _sdlc(["preflight", folder.name], root)
        findings = folder / "findings.md"
        if pre and (pre.get("risk") or {}).get("deep") and not findings.is_file():
            findings.write_text(f"# Findings\n\n{FRESH_SKIPPED}\n", encoding="utf-8", newline="\n")
        code, _, said = _sdlc(["ship", folder.name], root)
        if code:
            return emit({**out, "refusals": [f"sdlc.py ship refused: {said.strip()[-500:]}"]}, 1)
        _, cfg_out, _ = _sdlc(["config"], root)
        refs = ((cfg_out or {}).get("archive") or {}).get("ids_from") == "github"
        message = land_message(root, folder, by, refs)
        try:
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-F", "-"], input=message,
                capture_output=True, encoding="utf-8", check=True,
            )  # fmt: skip
        except (subprocess.CalledProcessError, OSError) as e:
            return emit({**out, "refusals": [f"the commit failed: {e}"]}, 1)
    code, based, said = _sdlc(["base", folder.name], root)
    action = (based or {}).get("action")
    reason = str((based or {}).get("reason") or said)
    out.update(head=_git(root, "rev-parse", "--short", "HEAD"), base=based)
    if action in ("current", "fast-forwarded"):
        out["state"] = "current"
    elif action == "rebased":
        out["state"] = "rebased"
    elif action == "refused" and "conflict" in reason:
        out["state"] = "conflict"
    else:
        return emit({**out, "refusals": [f"sdlc.py base refused: {reason.strip()[-500:]}"]}, 1)
    if out["state"] != "current":
        (folder / "reviews" / f"land-{land_round(folder) + 1}").mkdir(parents=True, exist_ok=True)
    out["round"] = land_round(folder) or None
    return emit(out)


def cmd_land_close(root: Path, ident: str) -> int:
    """Land change `ident`'s second half: `sdlc.py close` run from the main checkout (from inside
    the change's worktree it would keep the worktree), which merges, archives, removes the folder,
    the worktree and the branch, and pushes as `git.push` says. Its JSON passes through."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    # The landing's own record (its review, a resolved conflict's marker) is written after the
    # change's commit: amended into it, so the change lands as one commit and close finds the
    # worktree clean. Anything dirty outside the change's folder is not the landing's: refused.
    dirty = (_git(root, "status", "--porcelain", "--untracked-files=all") or "").splitlines()
    rel = folder.relative_to(root).as_posix() + "/"
    stray = [line[3:] for line in dirty if not line[3:].strip('"').startswith(rel)]
    if stray:
        return emit(
            {"refusals": [f"uncommitted outside the change's folder: {', '.join(stray)}"]}, 1
        )
    if dirty:
        _git(root, "add", "--", rel)
        if _git(root, "commit", "-q", "--amend", "--no-edit") is None:
            return emit({"refusals": ["the landing's record couldn't be added to the commit"]}, 1)
    main = worktrees(root)[0][0] if worktrees(root) else root
    code, closed, said = _sdlc(["close", ident], main)
    return emit(closed or {"refusals": [said.strip()[-500:]]}, code)


def _conflicted(root: Path) -> list[str]:
    return (_git(root, "diff", "--name-only", "--diff-filter=U") or "").splitlines()


COUNTER = ".sdlc/last-id"


def _settle_counter(root: Path) -> None:
    """`.sdlc/last-id` conflicted, as it is whenever two locally numbered changes land one after
    the other: never the builder's, it keeps the higher of the two numbers, as `sdlc.py base` does
    on a fast-forward, so no number is handed out twice."""
    if COUNTER not in _conflicted(root):
        return
    sides = [_git(root, "show", f":{n}:{COUNTER}") or "" for n in (2, 3)]
    numbers = [int(s) for s in sides if s.strip().isdigit()]
    if not numbers:
        return
    (root / COUNTER).write_text(f"{max(numbers):03d}\n", encoding="utf-8", newline="\n")
    _git(root, "add", "--", COUNTER)


def cmd_resolve(root: Path, ident: str, cont: bool) -> int:
    """A rebase onto the base branch that conflicts, left for the builder: `resolve` starts it and
    lists the conflicted files (or finds none, and it is done); `--continue` checks no conflict
    marker is left in them, stages them and continues, aborting the rebase on a second conflict.
    Every git step is this script's: the builder only edits the files it is given."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    base = _base(root)
    if base is None:
        return emit({"refusals": ["no base branch: set [git] base in .sdlc/config.toml"]}, 1)
    env = {**os.environ, "GIT_EDITOR": "true"}
    if not cont:
        done = subprocess.run(["git", "-C", str(root), "rebase", "-q", base], capture_output=True,
                              encoding="utf-8", env=env)  # fmt: skip
        _settle_counter(root)
        files = _conflicted(root)
        if done.returncode and not files:
            return emit({"refusals": [f"git rebase failed: {done.stderr.strip()[-300:]}"]}, 1)
        return emit(
            {"change": folder.name, "conflicted": files, "state": "conflict" if files else "clean"}
        )
    files = _conflicted(root)
    marked = [
        f for f in files if "<<<<<<<" in (root / f).read_text(encoding="utf-8", errors="replace")
    ]
    if marked:
        return emit({"refusals": [f"conflict markers left in: {', '.join(marked)}"]}, 1)
    for f in files:
        _git(root, "add", "--", f)
    # The builder's resolve run added its cost line to this tracked file mid-rebase: the change's
    # own record, so it goes into the rebased commit, or `--continue` refuses on it.
    if (folder / COSTS).is_file():
        _git(root, "add", "--", (folder / COSTS).relative_to(root).as_posix())
    done = subprocess.run(["git", "-C", str(root), "rebase", "--continue"], capture_output=True,
                          encoding="utf-8", env=env)  # fmt: skip
    if done.returncode:
        _git(root, "rebase", "--abort")
        return emit({"refusals": ["a second conflict: the rebase was aborted, ship it by hand"]}, 1)
    marker = folder / "runs" / "land-resolved"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(", ".join(files) + "\n", encoding="utf-8", newline="\n")
    return emit({"change": folder.name, "resolved": files, "state": "resolved",
                 "head": _git(root, "rev-parse", "--short", "HEAD")})  # fmt: skip


def cmd_land_verdicts(root: Path, ident: str) -> int:
    """The landing review of round `land-<n>`, and the step it takes next: `gate` (the script's
    gate on the change as rebased, before any reviewer, while the base branch names one),
    `review` for the `missing` reviewers (behaviour alone after a clean rebase, every reviewer at
    the run's depth after a resolved conflict), `verify` when one asks for changes, `pass` when
    none is kept, or `stop`, with why: a red gate, a kept change, a reply without a verdict, or
    one without its evidence."""
    cfg, _ = load_config(root)
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    n = land_round(folder)
    if not n:
        return emit({"change": folder.name, "round": None, "next": "pass", "missing": []})
    path = folder / "reviews" / f"land-{n}"
    resolved = (folder / "runs" / "land-resolved").is_file()
    rounds, _, run = _rounds_at_depth(root, folder, cfg)
    wanted = list(run["reviewers"]) if resolved else ["behaviour"]
    reviews, problems = {}, []
    for role in wanted:
        file = path / f"{role}.md"
        if not file.is_file():
            continue
        lines = file.read_text(encoding="utf-8").splitlines()
        m = VERDICT_RE.match(lines[0]) if lines else None
        if not m:
            problems.append(f"reviews/land-{n}/{role}.md doesn't open with a VERDICT")
            continue
        reviews[role] = {
            "verdict": m.group(1),
            "changes": [c.group(1) for c in map(CHANGE_RE.match, lines[1:]) if c],
        }
        if role in RUNS_THE_CHANGE:
            problems += read_evidence("\n".join(lines), f"reviews/land-{n}/{role}.md")
    missing = [r for r in wanted if r not in reviews]
    verified, wrong = read_verified(path / VERIFIED, n, reviews)
    problems += wrong
    # The rebased change is gated by the script before any reviewer reads it, as each build was.
    # Red is a stop, never a fix: the landing has no builder round, so the person ships it.
    gate = _land_gate_state(root, folder, n)
    if gate and gate["current"] == "FAIL":
        problems.append(
            f"the gate failed on the change as rebased (exit {gate['exit']}), in "
            f"build/land-{n}.gate.md: ship it by hand"
        )
    out = {"change": folder.name, "round": n, "reviews": reviews, "missing": missing,
           "resolved": resolved, "gate": gate, "problems": problems}  # fmt: skip
    asks = any(r["verdict"] == "CHANGES" for r in reviews.values())
    if problems:
        out["next"] = "stop"
    elif gate and gate["current"] is None:
        out["next"] = "gate"
    elif missing:
        out["next"] = "review"
    elif asks and verified is None:
        out["next"] = "verify"
    elif verified and verified["kept"]:
        out["next"], out["problems"] = (
            "stop",
            [f"the landing review kept {len(verified['kept'])} change(s): ship it by hand"],
        )
    else:
        out["next"] = "pass"
    return emit(out)


# ---------------------------------------------------------------- what escaped, and old code
#
# The eval replays the reviewers on the diffs that let real bugs through, and the review looks at
# code no change touches. Both read what `sdlc.py` writes (the register's `[bug]` entries, the
# `Close` commits' `Sdlc-Fixes` and `Sdlc-Base` lines) with copies of its parsing, pinned to it by
# tests, since this plugin's cached copy has no `sdlc.py`. Neither writes the register: a review's
# bugs reach it only through `/sdlc:bug`.

INBOX = Path(".sdlc") / "work" / "inbox.md"
BUG_RE = re.compile(r"^##\s*\[(\d{4}-\d{2}-\d{2})-(\d+)\]\s*\[bug\]\s*(.+)$")
FIELD_RE = re.compile(r"^(Severity|Paths|Introduced by):\s*(.+)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
TRAILER_RE = re.compile(r"^Sdlc-(Fixes|Base):\s*(.*)$")
CLOSE_PREFIX = "Close "
# Where the eval and the review write, uncommitted: a folder that ignores itself, so a run never
# dirties a checkout and needs nothing of setup.
REPORTS = Path(".sdlc") / "reports"
REPORT_KINDS = ("eval", "review")
SCORE_RE = re.compile(r"^- ([a-z]+): (\d+) of (\d+) caught")


def _words(rest: str) -> tuple[str | None, dict[str, str]]:
    """An `Sdlc-*` line's value: its leading name, when the first word isn't `key=value`, and its
    `key=value` words. Copied from `metrics.parse_trailers`, values kept as text."""
    words = rest.split()
    name = words[0] if words and "=" not in words[0] else None
    fields = {}
    for word in words[1:] if name else words:
        k, _, v = word.partition("=")
        fields[k] = v
    return name, fields


def bug_paths(raw: object) -> list[str] | None:
    """A bug's paths, from the register (a list) or an `Sdlc-Fixes` line's `paths=` (text, or
    `unknown`); None when nobody recorded them. Copied from `sdlc.py`'s `_bug_paths()`."""
    if isinstance(raw, list):
        return raw or None
    if not isinstance(raw, str) or raw in ("", "unknown"):
        return None
    return [p for p in raw.split(",") if p]


def on_paths(evidence: str, paths: list[str] | None) -> bool | None:
    """Whether a finding's path is one of a bug's paths, under one, or holds one; None when the
    bug's paths are unknown. Copied from `sdlc.py`'s `_on_paths()`."""
    if paths is None:
        return None
    where = (evidence.split() or [""])[0].split(":", 1)[0].strip("`").rstrip("/")
    for p in paths:
        p = p.strip("`").rstrip("/")
        if where and p and (where == p or where.startswith(p + "/") or p.startswith(where + "/")):
            return True
    return False


def open_bugs(root: Path) -> list[dict]:
    """The register's `[bug]` entries: id, title, reported date, severity, paths and the change
    they were introduced by, read as `sdlc.py`'s `bug_entries()` reads them."""
    path = root / INBOX
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    found: list[dict] = []
    current: dict | None = None
    fenced = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if m := BUG_RE.match(line):
            current = {"id": f"{m.group(1)}-{m.group(2)}", "title": m.group(3).strip(),
                       "reported": m.group(1), "fields": {}}  # fmt: skip
            found.append(current)
        elif line.startswith("#"):
            current = None
        elif current is not None and (f := FIELD_RE.match(line.strip())):
            current["fields"].setdefault(f.group(1), f.group(2).strip())
    out = []
    for b in found:
        fields = b.pop("fields")
        paths = fields.get("Paths", "")
        by = (fields.get("Introduced by") or "").strip() or None
        out.append({**b, "severity": fields.get("Severity", "").strip(),
                    "paths": [p.strip().strip("`") for p in paths.split(",") if p.strip()],
                    "introduced_by": by})  # fmt: skip
    return out


def closes(root: Path, base: str) -> tuple[dict[str, dict], list[dict]]:
    """Every `Close <name>` on the base branch's first-parent line: the change's own commit (the
    close's parent) and the `Sdlc-Base:` it recorded, by name; and every `Sdlc-Fixes:` line on
    them, as the bugs those changes fixed."""
    log = _git(root, "log", "--first-parent", "--format=%x1e%H%x00%P%x00%B", base) or ""
    by_name: dict[str, dict] = {}
    fixed: list[dict] = []
    for record in log.split("\x1e"):
        sha, _, rest = record.partition("\x00")
        parents, _, body = rest.partition("\x00")
        subject = body.strip().splitlines()[0] if body.strip() else ""
        if not subject.startswith(CLOSE_PREFIX) or not parents.split():
            continue
        name = subject[len(CLOSE_PREFIX) :].strip()
        rec = {"commit": parents.split()[0], "base": None}
        for line in body.splitlines():
            if m := TRAILER_RE.match(line.strip()):
                if m.group(1) == "Base":
                    rec["base"] = m.group(2).strip() or None
                else:
                    bug, fields = _words(m.group(2))
                    if bug:
                        fixed.append({"id": bug, **fields})
        by_name.setdefault(name, rec)
    return by_name, fixed


def cmd_escapes(root: Path, limit: int) -> int:
    """The bugs that escaped a review and the change each came in with, newest reported first: the
    fixed ones from `Sdlc-Fixes`, the open ones from the register. Each with the diff to replay:
    from the close's `Sdlc-Base:` to the change's commit, or its last commit alone (`partial`)
    when the close recorded no base. Read-only."""
    base = _base(root)
    if base is None:
        return emit({"refusals": ["no base branch: set [git] base in .sdlc/config.toml"]}, 1)
    by_name, fixed = closes(root, base)
    bugs = [
        {"id": f["id"], "title": None, "reported": f.get("reported"), "severity": f.get("severity"),
         "paths": bug_paths(f.get("paths")), "introduced_by": f.get("introduced_by")}
        for f in fixed
    ] + [{**b, "paths": b["paths"] or None} for b in open_bugs(root)]  # fmt: skip
    found, unattributed, unknown = [], 0, 0
    for b in bugs:
        by = b["introduced_by"]
        if not by or by == "unknown":
            unattributed += 1
            continue
        name = next((n for n in by_name if names_change(n, by)), None)
        if name is None:
            unknown += 1
            continue
        rec = by_name[name]
        start = rec["base"] or f"{rec['commit']}^"
        found.append({**b, "change": name, "commit": rec["commit"], "base": start,
                      "partial": rec["base"] is None})  # fmt: skip
    found.sort(key=lambda e: str(e.get("reported") or ""), reverse=True)
    return emit({"escapes": found[:limit], "listed": len(found), "limit": limit,
                 "unattributed": unattributed, "unknown_change": unknown})  # fmt: skip


def _reports(root: Path) -> Path:
    """`.sdlc/reports/`, made with the `.gitignore` that keeps everything in it out of git."""
    reports = root / REPORTS
    reports.mkdir(parents=True, exist_ok=True)
    ignore = reports / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("*\n", encoding="utf-8", newline="\n")
    return reports


# ---------------------------------------------------------------- the page a change shows
#
# The UI reviewers judge screenshots, never a browser of their own: `shots` starts the dev server
# the base branch's `[ui]` names, takes each page at each width with its `shoot` command, and stops
# the server it started, so no agent starts, drives or kills a process. The images go under
# `.sdlc/reports/shots/`, which ignores itself, so none reaches a commit.

SHOT_TIMEOUT = 120
STOP_GRACE = 5


def _free_port() -> int:
    """A port nothing on this machine listens on, for one dev server."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _answers(host: str, port: int) -> bool:
    """Whether something accepts on `host`:`port`, `host` resolved to every address it has, so a
    server bound to `localhost` on IPv6 alone answers too."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _fill(command: str, **values: object) -> str:
    """`command` with each `{key}` named in `values` replaced, and nothing else: a host's shell
    braces (`${HOME}`) stay as written."""
    for key, value in values.items():
        command = command.replace("{" + key + "}", str(value))
    return command


def _page_name(page: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", page.strip("/")).strip("-") or "index"


def _stop(proc: subprocess.Popen) -> None:
    """Stop the process group `shots` started, and only it: its children with it, whatever they
    are, and never anything found by name or port."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            capture_output=True, encoding="utf-8", errors="replace",
        )  # fmt: skip
        with suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=STOP_GRACE)
        return
    import signal

    with suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGTERM)
    with suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=STOP_GRACE)
    with suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


def shots(root: Path, folder: Path, label: str, ui: dict) -> tuple[list[Path], dict]:
    """Each page of `[ui]` at each width, as PNGs under `.sdlc/reports/shots/<change>/<label>/`,
    with `shots.json` saying what ran and how it ended: `problem` is None only when every shot was
    written. A label already shot without a problem is reused, not shot again."""
    where = _reports(root) / "shots" / folder.name / label
    record_path = where / "shots.json"
    want = [
        (page, w, h, where / f"{_page_name(page)}-{w}x{h}.png")
        for page in ui["pages"]
        for w, h in ui["widths"]
    ]
    paths = [p for *_, p in want]
    with suppress(OSError, ValueError):
        before = json.loads(record_path.read_text(encoding="utf-8"))
        if before.get("problem") is None and all(p.is_file() for p in paths):
            return paths, before
    where.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    record: dict = {
        "serve": _fill(ui["serve"], port=port),
        "port": port,
        "shots": [],
        "problem": None,
    }
    log = where / "serve.log"
    group = (
        {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    with log.open("wb") as sink:
        try:
            proc = subprocess.Popen(
                _sh(record["serve"]), cwd=root, stdin=subprocess.DEVNULL, stdout=sink,
                stderr=subprocess.STDOUT, **group,
            )  # fmt: skip
        except OSError as e:
            proc, record["problem"] = None, f"the dev server couldn't be started: {e}"
        try:
            deadline = time.monotonic() + ui["timeout"]
            # Wait where the shots will go: `[ui] url`'s host, not one assumed.
            host = urlparse(_fill(ui["url"], port=port)).hostname or "127.0.0.1"
            while proc and record["problem"] is None and not _answers(host, port):
                if proc.poll() is not None:
                    record["problem"] = f"the dev server exited {proc.returncode} before answering"
                elif time.monotonic() > deadline:
                    record["problem"] = (
                        f"the dev server didn't answer on {port} in {ui['timeout']}s"
                    )
                else:
                    time.sleep(0.2)
            for page, w, h, path in want if record["problem"] is None else []:
                url = _fill(ui["url"], port=port).rstrip("/") + "/" + page.lstrip("/")
                # Relative to the checkout, where the command runs: the record names no machine.
                out = path.relative_to(root).as_posix()
                command = _fill(ui["shoot"], url=url, width=w, height=h, out=out)
                try:
                    done = subprocess.run(
                        _sh(command), cwd=root, capture_output=True, encoding="utf-8",
                        errors="replace", stdin=subprocess.DEVNULL, timeout=SHOT_TIMEOUT,
                    )  # fmt: skip
                    code, tail = done.returncode, (done.stderr or done.stdout or "").strip()[-500:]
                except subprocess.TimeoutExpired:
                    code, tail = 124, f"ran past {SHOT_TIMEOUT}s"
                except OSError as e:
                    code, tail = 127, str(e)
                record["shots"].append({"command": command, "exit": code, "tail": tail})
                if code or not path.is_file():
                    record["problem"] = (
                        f"`{command}` exited {code} and wrote no {path.name}: {tail}"
                    )
                    break
        finally:
            if proc:
                _stop(proc)
    if record["problem"]:
        served = log.read_text(encoding="utf-8", errors="replace").strip()[-500:]
        record["server_tail"] = served
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    return paths, record


def cmd_shots(root: Path, ident: str, n: int) -> int:
    """Round `n`'s screenshots of the change's pages, for its UI reviewers (`shots()`)."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    ui = load_config(root)[0]["ui"]
    if not ui_complete(ui):
        return emit({"refusals": ["the base branch's [ui] needs serve, shoot and paths"]}, 1)
    paths, record = shots(root, folder, f"round-{n}", ui)
    out = {"change": folder.name, "shots": [p.relative_to(root).as_posix() for p in paths]}
    return emit({**out, **record}, 1 if record["problem"] else 0)


def cmd_report_dir(root: Path, kind: str) -> int:
    """A fresh run folder under `.sdlc/reports/`, which ignores itself, for an eval or a review to
    write into: `<kind>-<date>-<n>/`."""
    reports = _reports(root)
    stamp = f"{kind}-{date.today().isoformat()}"
    n = 1 + sum(1 for p in reports.glob(f"{stamp}-*") if p.is_dir())
    run = reports / f"{stamp}-{n}"
    run.mkdir()
    return emit({"run": run.relative_to(root).as_posix()})


def _run_order(path: Path) -> tuple[str, int]:
    """A run's place among its kind: its date, then its number within the day."""
    stem = path.name.removesuffix(".md")
    day, _, n = stem.rpartition("-")
    return day, int(n) if n.isdigit() else 0


def cmd_score(root: Path, run_rel: str) -> int:
    """Score an eval's run: a reviewer caught a bug when one of its `CHANGE:` lines sits on the
    bug's paths, missed it when none does, and is `unknown` when the paths weren't recorded, never
    missed. Write `<run>.md` beside the run, with each reviewer's score against the last eval's."""
    run = root / run_rel
    data = json.loads((run / "escapes.json").read_text(encoding="utf-8"))
    escapes = data["escapes"] if isinstance(data, dict) else data
    scores: dict[str, dict] = {}
    bugs = []
    for b in escapes:
        results = {}
        for reply in sorted((run / b["id"]).glob("*.md")):
            role = reply.stem
            changes = [
                c.group(1)
                for c in map(CHANGE_RE.match, reply.read_text(encoding="utf-8").splitlines())
                if c
            ]
            hits = [c for c in changes if on_paths(c, b.get("paths"))]
            result = "unknown" if b.get("paths") is None else "caught" if hits else "missed"
            results[role] = {"result": result, "lines": hits}
            s = scores.setdefault(role, {"caught": 0, "scored": 0})
            if result != "unknown":
                s["scored"] += 1
                s["caught"] += result == "caught"
        bugs.append({"id": b["id"], "change": b.get("change"), "results": results})
    earlier = [p for p in (root / REPORTS).glob("eval-*.md") if _run_order(p) < _run_order(run)]
    previous: dict[str, tuple[int, int]] = {}
    if earlier:
        last = max(earlier, key=_run_order)
        for line in last.read_text(encoding="utf-8").splitlines():
            if m := SCORE_RE.match(line):
                previous[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    lines = [f"# Eval {run.name}", "", "## Reviewers", ""]
    for role, s in sorted(scores.items()):
        was = previous.get(role)
        then = f" (was {was[0]} of {was[1]})" if was else ""
        lines.append(f"- {role}: {s['caught']} of {s['scored']} caught{then}")
        s["previous"] = {"caught": was[0], "scored": was[1]} if was else None
    lines += ["", "## Bugs", ""]
    for b in bugs:
        lines.append(f"### {b['id']} ({b['change']})")
        for role, r in sorted(b["results"].items()):
            lines.append(f"- {role}: {r['result']}")
            lines += [f"  - `{text}`" for text in r["lines"]]
        lines.append("")
    report = run.parent / f"{run.name}.md"
    report.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    return emit({"report": report.relative_to(root).as_posix(), "reviewers": scores, "bugs": bugs})


def _open_change_paths(root: Path, base: str) -> set[str]:
    """Every path an open change's worktree touches: a review of old code leaves them alone."""
    listing = _git(root, "worktree", "list", "--porcelain") or ""
    touched: set[str] = set()
    tree = None
    for line in listing.splitlines():
        if line.startswith("worktree "):
            tree = Path(line[len("worktree ") :])
        elif line.startswith("branch refs/heads/") and tree is not None:
            branch = line[len("branch refs/heads/") :]
            if DIR_RE.match(branch) and tree.resolve() != root.resolve():
                touched |= set(_changed_paths(tree, base))
    return touched


def cmd_slice(root: Path, paths: list[str], limit: int) -> int:
    """The code a review looks at: the paths named; else the tracked files under the base
    branch's `[review] sensitive`; else the `limit` least recently changed tracked files. Paths an
    open change touches are always left out. Read-only."""
    base = _base(root)
    if base is None:
        return emit({"refusals": ["no base branch: set [git] base in .sdlc/config.toml"]}, 1)
    # The change folders and the register are the process's records, not code to review.
    tracked = [
        p
        for p in (_git(root, "ls-files") or "").splitlines()
        if not p.startswith(work_rel(root) + "/")
    ]
    if paths:
        chosen, why = list(paths), "the paths named"
    elif hit := risk_paths(tracked, _sensitive(root, base)):
        chosen, why = hit[:limit], "the base branch's [review] sensitive paths"
    else:
        # One walk, newest first: the first time a path shows up is when it last changed.
        last: dict[str, int] = {}
        stamp = 0
        log = _git(root, "log", "--format=%x00%ct", "--name-only", "HEAD") or ""
        for line in log.splitlines():
            if line.startswith("\x00"):
                stamp = int(line[1:] or 0)
            elif line and line not in last:
                last[line] = stamp
        oldest = sorted(tracked, key=lambda p: (last.get(p, 0), p))
        chosen, why = oldest[:limit], f"the {limit} least recently changed tracked files"
    busy = _open_change_paths(root, base)
    left_out = [p for p in chosen if p in busy]
    return emit({"paths": [p for p in chosen if p not in busy], "why": why,
                 "left_out": left_out, "limit": limit})  # fmt: skip


def main() -> int:
    _utf8_streams()
    ap = argparse.ArgumentParser(description="The sdlc-factory layer's mechanism.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("config", help=f"{CONFIG_FILE} over the defaults, as JSON")
    p_start = sub.add_parser("start", help="whether a factory step may start on the change")
    p_start.add_argument("id")
    p_start.add_argument("--for", dest="purpose", choices=sorted(STARTS), required=True)
    p_verdicts = sub.add_parser("verdicts", help="the review rounds, the decision, the next step")
    p_verdicts.add_argument("id")
    p_verdicts.add_argument("--head", help="HEAD as `start` printed it; a move is a stop")
    p_verdicts.add_argument(
        "--record", action="store_true", help=f"write a stop to {STOPPED.as_posix()}, or remove it"
    )
    p_decisions = sub.add_parser("decisions", help="the agents' decisions into decisions.md")
    p_decisions.add_argument("id")
    p_carry = sub.add_parser("carry", help="unresolved changes to notes.md as `- [ ]` items")
    p_carry.add_argument("id")
    p_snapshot = sub.add_parser("snapshot", help="hash what a round's build left, for the next")
    p_snapshot.add_argument("id")
    p_snapshot.add_argument("--round", dest="round", type=int, required=True)
    p_gate = sub.add_parser("gate", help="run the base branch's gate on the newest build")
    p_gate.add_argument("id")
    p_gate.add_argument("--land", action="store_true", help="on the change as a landing rebased it")
    p_shots = sub.add_parser("shots", help="screenshot the change's pages for its UI reviewers")
    p_shots.add_argument("id")
    p_shots.add_argument("--round", dest="round", type=int, required=True)
    p_stage = sub.add_parser("stage", help="set the intent's stage: line, in place")
    p_stage.add_argument("id")
    p_stage.add_argument("stage")
    p_restart = sub.add_parser("restart", help="send an escalated change back for another build")
    p_restart.add_argument("id")
    p_restart.add_argument("--words", help="the person's words in decisions.md (R1), if any")
    p_agent = sub.add_parser("agent", help="run one agent session for a step, and file its reply")
    p_agent.add_argument("id")
    p_agent.add_argument("--task", choices=TASKS, required=True)
    p_agent.add_argument("--role", choices=[*REVIEWERS, "builder"])
    sub.add_parser("sdlc-path", help="the sdlc.py of this factory's own version, which land runs")
    p_check = sub.add_parser("land-check", help="the batch to land, its signals, and whether clear")
    p_check.add_argument("ids", nargs="*")
    p_land = sub.add_parser("land", help="ship, commit and rebase a change; or close it")
    p_land.add_argument("id")
    p_land.add_argument("--by", choices=("auto", "person"))
    p_land.add_argument("--close", action="store_true", help="close it, from the main checkout")
    p_resolve = sub.add_parser("resolve", help="leave a conflicting rebase for the builder")
    p_resolve.add_argument("id")
    p_resolve.add_argument("--continue", dest="cont", action="store_true")
    p_lv = sub.add_parser("land-verdicts", help="the landing review, and its next step")
    p_lv.add_argument("id")
    p_agent.add_argument("--decision", help="the decided ledger id, for --task decided")
    p_agent.add_argument("--revise", help="the person's revision in decisions.md (R1), for spec")
    p_agent.add_argument("--recheck", action="store_true", help="send a spec draft back once")
    sub.add_parser("ready", help="the changes ready to ship, in the order to ship them")
    p_escapes = sub.add_parser("escapes", help="escaped bugs and the diffs that let them in")
    p_escapes.add_argument("--limit", type=int, default=10)
    p_report = sub.add_parser("report-dir", help="a fresh run folder under .sdlc/reports/")
    p_report.add_argument("--kind", choices=REPORT_KINDS, required=True)
    p_score = sub.add_parser("score", help="score an eval's run against the last one")
    p_score.add_argument("run")
    p_slice = sub.add_parser("slice", help="the code a review of old code looks at")
    p_slice.add_argument("--paths", nargs="*", default=[])
    p_slice.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()
    root = repo_root()
    if getattr(args, "id", None):
        root = change_root(root, args.id)
    if args.cmd == "sdlc-path":
        return cmd_sdlc_path()
    if args.cmd == "land-check":
        return cmd_land_check(root, args.ids)
    if args.cmd == "land" and args.close:
        return cmd_land_close(root, args.id)
    if args.cmd == "land":
        if not args.by:
            return emit({"refusals": ["land needs --by auto|person, or --close"]}, 1)
        return cmd_land(root, args.id, args.by)
    if args.cmd == "resolve":
        return cmd_resolve(root, args.id, args.cont)
    if args.cmd == "land-verdicts":
        return cmd_land_verdicts(root, args.id)
    if args.cmd == "agent":
        return cmd_agent(
            root, args.id, args.task, args.role, args.decision, args.revise, args.recheck
        )
    if args.cmd == "ready":
        return cmd_ready(root)
    if args.cmd == "config":
        return cmd_config(root)
    if args.cmd == "start":
        return cmd_start(root, args.id, args.purpose)
    if args.cmd == "verdicts":
        return cmd_verdicts(root, args.id, args.head, args.record)
    if args.cmd == "decisions":
        return cmd_decisions(root, args.id)
    if args.cmd == "carry":
        return cmd_carry(root, args.id)
    if args.cmd == "snapshot":
        return cmd_snapshot(root, args.id, args.round)
    if args.cmd == "gate":
        return cmd_gate(root, args.id, args.land)
    if args.cmd == "shots":
        return cmd_shots(root, args.id, args.round)
    if args.cmd == "restart":
        return cmd_restart(root, args.id, args.words)
    if args.cmd == "escapes":
        return cmd_escapes(root, args.limit)
    if args.cmd == "report-dir":
        return cmd_report_dir(root, args.kind)
    if args.cmd == "score":
        return cmd_score(root, args.run)
    if args.cmd == "slice":
        return cmd_slice(root, args.paths, args.limit)
    return cmd_stage(root, args.id, args.stage)


if __name__ == "__main__":
    sys.exit(main())
