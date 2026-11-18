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
round-tripped (`sdlc.py`'s `stamp_shipped` rule). For `fresh`, `upgrade` and landing alone it runs
the `sdlc.py` of its own version, beside it (`sdlc_path()`), so ship, base, resolve, upgrade and
close keep one implementation.

    uv run --script factory.py config
    uv run --script factory.py start 008 --for build
    uv run --script factory.py fresh 008
    uv run --script factory.py decisions 008
    uv run --script factory.py verdicts 008 --head 1a2b3c4 --record
    uv run --script factory.py gate 008
    uv run --script factory.py carry 008
    uv run --script factory.py stage 008 test
    uv run --script factory.py write-spec 008
    uv run --script factory.py upgrade 008
    uv run --script factory.py agent 008 --task review --role code
    uv run --script factory.py ready
    uv run --script factory.py land-check
    uv run --script factory.py land 008 --by auto

Every command prints JSON and writes only where its name says: `decisions` to `decisions.md`,
`carry` to `notes.md`, `stage` to `intent.md`, `write-spec` the approved draft to `spec.md`,
`upgrade` its record to `build/round-<P>.upgraded.md` (and, through `sdlc.py upgrade`, the tier and
stage to `intent.md` and the scaffolds a Tier 2 owes),
`gate` its attempt to `build/round-<N>.gate.md`, `verdicts --record` a stop to `runs/stopped.md`
(or removes it once the run is clear) and the step it read, with since when, to `runs/step.md`,
`agent` the reply an agent session returned (a spec draft to `runs/spec-draft.md` and its
questions to `runs/spec-questions.md`, never to `spec.md`), and its id and figures under `runs/`.
Nothing is written outside the change's folder, and nothing under `.git/`, but by the landing and
`fresh`: `land` and `resolve` commit and rebase the change's own branch, and `sdlc.py close` lands
it; `fresh`, before a run, moves the change's own branch onto the base through `sdlc.py base` and
`resolve`, and commits nothing that stays. `gate` also holds a lock on a slot file,
`sdlc-factory-gate-<k>.lock` in the git common dir, made once and never written; `sdlc.py gate`,
the gate run by hand, takes the same lock files while this plugin is enabled. A command about
one change runs in its worktree, found from the main checkout when the supervisor runs there
(`change_root()`).

**Decisions that are a person's.** An agent that reaches a call it shouldn't make (a trade-off, a
policy, scope) raises a `- DECISION: [blocking] ...` or `- DECISION: [default] ...` line in its
reply. `decisions` gathers them into `decisions.md`; `verdicts` says `decide` while a blocking one
is unanswered, and the session running the build, the only one that can talk to the person, asks
them. A default one lets the run go on, recorded as assumed until the person confirms it.

**An upgrade to Tier 2.** A Tier 1 change found bigger than its Approach is upgraded only by the
person's answer to a blocking decision, one that starts `upgrade to Tier 2`: `verdicts` names
`upgrade`, then `spec` until the approved spec moves the change to `stage: build`, then `build` at
round P, the upgraded run's first, which resumes the builder. Once only, and never back.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import time
import tomllib
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, date, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import BinaryIO
from urllib.parse import urlparse

# The change-folder names `sdlc.py` gives: three digits at least, then the slug.
DIR_RE = re.compile(r"^(\d{3,})-([a-z0-9][a-z0-9-]*)$")
# A conflict marker as git writes it, a whole line: never a run of the signs quoted mid-line, as
# a check like this one, or a register naming it, holds. A copy of `sdlc.py`'s, pinned by a test.
CONFLICT_MARKER_RE = re.compile(r"^(?:<{7} |={7}$|>{7} )", re.M)
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
    "land": {"auto": True, "batch": 5, "moves": 3},
    # A repo's front end: the dev server to start (`{port}`), where it answers, the pages to shoot,
    # the paths that count as UI, the screenshot command (`{url}`, `{width}`, `{height}`, `{out}`),
    # the window sizes, how long the server gets to answer, and the data it serves: a path in the
    # checkout, copied afresh for each shot and passed as `{fixture}`. Unset, no UI review runs.
    "ui": {
        "serve": None, "url": "http://127.0.0.1:{port}", "pages": ["/"], "paths": [],
        "shoot": None, "widths": [[1280, 800], [390, 844]], "timeout": 60, "fixture": None,
    },
    # The most `factory.py gate` runs at once across every worktree of the repo: one by default,
    # so parallel runs' gates never fight each other for every core.
    "gate_jobs": 1,
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
# A reviewer's nit, under its `## Notes`: recorded in findings.md, never verified or reworked.
# (`NIT_RE` is the register's `[nit]` heading.)
FINDING_NIT_RE = re.compile(r"^\s*- NIT:\s*(.+?)\s*$")
# A nit's weights, which its reviewer writes at its end by the process doc's rubric: `{<theme>
# <cost> <value>}`, one word each. Read off the nit's text; a nit without them, or with a word the
# rubric doesn't have, keeps its text whole and is never weighed. `NIT_COSTS` and `NIT_VALUES` are
# what a filed `[nit]` may hold, copies of `sdlc.py`'s, pinned by a test: `L` cost is an idea and
# `high` value is never a nit, so neither is filed.
NIT_WEIGHT_RE = re.compile(r"^(.*?)\s*\{([a-z][a-z0-9-]*)\s+(S|M|L)\s+(high|med|low)\}$")
NIT_COSTS = ("S", "M")
NIT_VALUES = ("med", "low")
# The pass a finding opens with, `[context] docs/a.md:3: …`: one of the four `sdlc.py` counts
# (`FINDING_PASSES`). Without one, or with another word, its role's pass (`ROLE_PASS`, else
# correctness), and an unknown tag stays in the text.
PASSES = ("correctness", "contract", "cost", "context")
PASS_TAG_RE = re.compile(r"^\[([a-z]+)\]\s*(.*)$")
ROLE_PASS = {"security": "contract"}
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
# A Tier 1 change upgraded to Tier 2 during its run, on the person's answer to a blocking decision,
# which starts `upgrade to Tier 2` in any case: `upgrade` writes `build/round-<P>.upgraded.md`
# beside the gate files, naming that decision, then has `sdlc.py upgrade` set the tier. Round P is
# the upgraded run's first, as a restart's round is. `sdlc.py` keeps a copy of the file's pattern.
UPGRADED_RE = re.compile(r"^UPGRADED: (D\d+)\s*$")
UPGRADED_FILE_RE = re.compile(r"^round-(\d+)\.upgraded\.md$")
UPGRADE_ANSWER_RE = re.compile(r"^upgrade to tier 2\b", re.I)
# What a builder report and a behaviour check end with: each command run (`$ <command>`), the tail
# of its output, and `exit: <n>`. A result claimed without one is a stop, never taken on trust.
EVIDENCE = "## Evidence"
EXIT_RE = re.compile(r"^\s*exit:\s*\d+\s*$")
# The one judge of a read, a command the script can tell changes nothing (`is_read()`): a read
# that shows its output owes no `exit:`, since its output is its result. A closed allowlist, each
# program under its own condition; anything else, or anything it can't see into, is not a read.
READS = frozenset(
    {"cat", "head", "tail", "grep", "egrep", "fgrep", "ls", "wc", "cmp", "diff", "nl", "cut"}
    | {"tr", "stat", "pwd", "cd", "echo", "true", "test", "[", "jq"}
)
SEPARATORS = frozenset({"|", "||", "&&", ";"})
REDIRECTS = frozenset({"<", ">", ">>", ">&", "&>"})
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
AWK_PRINT_RE = re.compile(r"\bprintf?\b[^;}\n]*>")
# awk allows space between a builtin's name and its `(`: `system ("rm f")` runs as well.
AWK_RUNS_RE = re.compile(r"system\s*\(|@load|@include")
SED_ADDR = r"(?:\d+|\$|/(?:[^/\\]|\\.)*/)"
SED_PRINT_RE = re.compile(rf"^\s*(?:{SED_ADDR}(?:\s*,\s*{SED_ADDR})?)?\s*p\s*$")
GIT_READS = frozenset(
    {"show", "diff", "log", "status", "rev-parse", "ls-files", "ls-tree", "cat-file", "grep"}
    | {"blame", "merge-base", "shortlog", "describe"}
)
# git's options that run another program from a read, each with the length of its shortest
# abbreviation git takes: a diff driver (`--ext-diff`), a textconv filter (`--textc` is
# `--textconv`, `--text` a read), and gpg (`--show-signature`, which git takes whole). A pretty
# format with a `%G` placeholder (`--format=%G?`) runs gpg too (`GIT_FORMATS`). What git config
# turns on with no option, `log.showSignature` or a `diff.<driver>.textconv`, a command can't
# show, so it is not covered; `-c` before the subcommand is never a read.
GIT_RUNS = (
    ("--ext-diff", len("--ext")),
    ("--textconv", len("--textc")),
    ("--show-signature", len("--show-signature")),
)
GIT_FORMATS = ("--format", "--pretty")
FIND_REFUSED = ("-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fls")
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
# A later default naming the one it replaces, `- DECISION: [default] (supersedes D2) …`; `decisions`
# ticks the named line with SUPERSEDED, which every reader of an unticked line then passes over.
SUPERSEDES_RE = re.compile(r"^\(supersedes (D\d+)\)\s*(.+)$")
SUPERSEDED = " → superseded by "
# How `carry` starts a `notes.md` the change doesn't have yet: a copy of `sdlc`'s
# `templates/notes.md`, which this plugin's cached copy can't read. A test keeps the two the same.
NOTES_HEAD = """\
# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.
"""
# How `carry` and `_note_line()` start a `findings.md` the change doesn't have yet: a copy of
# `sdlc`'s `templates/findings.md` title and note, pinned by a test as `NOTES_HEAD` is.
FINDINGS_HEAD = """\
# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.
"""
# What `carry` writes for each agent finding: its `By:` is the role, its `Class:` names the round,
# and a nit's `Reason:` says no one weighed it.
FINDING_HEAD_RE = re.compile(r"^## F(\d+)\.")
NIT_REASON = "raised by an agent; not weighed or filed"
# What a weighed nit's `Reason:` says when it isn't filed as one (`agent_findings()`).
HANDED_REASON = "weighed S med: handed to the builder's rework, and not raised again"
HIGH_REASON = "weighed high value: never a nit; carried to notes.md"
IDEA_REASON = "weighed L cost: an idea, not a nit; carried to notes.md"
NIT_CAP = 5
CAP_REASON = f"past the cap of {NIT_CAP} nits a change files"
NO_PATH_REASON = "names no path, so it can't be filed as a nit"
LEAD_RE = re.compile(r"^`?([^\s:`]*[./][^\s:`]*?)(?::(\d+(?:[-–]\d+)?))?`?:\s+(.+)$")
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
        # `chosen`: whether `[light] reviewers` was set, so a Tier 2's default isn't applied over
        # a host's own list (`light_reviewers()`).
        "light": {
            "reviewers": list(light["reviewers"]),
            "rounds": light["rounds"],
            "chosen": False,
        },
        "models": {},
    }
    cfg["mode"], warnings = _mode(root)
    cfg["land"], land_warnings = _land(root)
    warnings += land_warnings
    cfg["ui"], ui_warnings = _ui(root)
    warnings += ui_warnings
    cfg["gate_jobs"], jobs_warnings = _gate_jobs(root)
    warnings += jobs_warnings
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
        cfg["light"]["chosen"] = _depth_keys(table, cfg["light"], "light.", warnings)
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
    if "gate_jobs" in data and data.get("gate_jobs") != cfg["gate_jobs"]:
        warnings.append(
            f"gate_jobs is read from the base branch's {CONFIG_FILE.as_posix()}: this checkout's "
            f"{data.get('gate_jobs')!r} applies once it lands"
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
    without asking, `batch`, the most changes one landing takes, and `moves`, the most times a
    landing follows the base branch moving under a change before it closes. A change can't turn
    any of them up for itself."""
    table = _base_factory(root).get("land", {})
    out, warnings = dict(DEFAULTS["land"]), []
    if not isinstance(table, dict):
        return out, ["land must be a table of auto, batch and moves"]
    for key, value in table.items():
        if key == "auto" and isinstance(value, bool):
            out["auto"] = value
        elif (
            key in ("batch", "moves")
            and isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
        ):
            out[key] = value
        else:
            warnings.append(
                f"land.{key} must be auto = true|false, batch or moves = a whole number"
            )
    return out, warnings


def _gate_jobs(root: Path) -> tuple[int, list[str]]:
    """`gate_jobs` as the base branch holds it: a change can't give its own gate more room."""
    jobs = _base_factory(root).get("gate_jobs", DEFAULTS["gate_jobs"])
    if not isinstance(jobs, int) or isinstance(jobs, bool) or jobs < 1:
        return DEFAULTS["gate_jobs"], [
            f"gate_jobs must be a whole number of 1 or more, so {DEFAULTS['gate_jobs']} runs"
        ]
    return jobs, []


def _ui(root: Path) -> tuple[dict, list[str]]:
    """`[ui]` as the base branch holds it: the dev server a UI review starts runs unasked once the
    run is approved, so a change can't name its own."""
    return _ui_table(_base_factory(root).get("ui", {}))


def _ui_table(table: object) -> tuple[dict, list[str]]:
    """A `[ui]` table over the defaults, each bad value a warning that leaves its default."""
    out = {k: list(v) if isinstance(v, list) else v for k, v in DEFAULTS["ui"].items()}
    if not isinstance(table, dict):
        return out, [
            "ui must be a table of serve, url, pages, paths, shoot, widths, timeout and fixture"
        ]
    warnings = []
    for key, value in table.items():
        texts = isinstance(value, list) and all(isinstance(v, str) for v in value)
        sizes = isinstance(value, list) and value and all(
            isinstance(v, list) and len(v) == 2
            and all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in v)
            for v in value
        )  # fmt: skip
        text = isinstance(value, str) and bool(value.strip())
        if key in ("serve", "url", "shoot") and text or key == "fixture" and _inside(value):
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
        elif key == "fixture":
            warnings.append("ui.fixture must be a path inside the checkout, so none is served")
        elif key in DEFAULTS["ui"]:
            warnings.append(f"ui.{key} has the wrong shape, so its default stands")
        else:
            warnings.append(f"unknown key ui.{key}")
    if "{fixture}" in (out["serve"] or "") and not out["fixture"]:
        warnings.append("ui.serve names {fixture}, but no ui.fixture is set")
    return out, warnings


def _inside(value: object) -> bool:
    """Whether `value` is a path that stays inside the checkout, on any platform: relative, with
    no drive and no `..`."""
    if not isinstance(value, str) or not value.strip():
        return False
    posix = PurePosixPath(value.replace("\\", "/"))
    return not (posix.is_absolute() or PureWindowsPath(value).anchor or ".." in posix.parts)


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


def _depth_keys(data: dict, into: dict, prefix: str, warnings: list[str]) -> bool:
    """A depth's `reviewers` and `rounds` from `data` into `into`, the top level's or `[light]`'s,
    each bad value a warning that leaves the default in place. Whether `data`'s own `reviewers`
    were taken."""
    taken = False
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
            taken = "reviewers" in data
        else:
            warnings.append(f"no known reviewer is configured in {prefix or 'the top level'}, so "
                            "the defaults run")  # fmt: skip
    rounds = data.get("rounds", into["rounds"])
    if isinstance(rounds, int) and not isinstance(rounds, bool) and 1 <= rounds <= MAX_ROUNDS:
        into["rounds"] = rounds
    else:
        warnings.append(f"{prefix}rounds must be a whole number from 1 to {MAX_ROUNDS}")
    return taken


def light_reviewers(cfg: dict, tier: int | None) -> list[str]:
    """The reviewers the light depth expects of a change at `tier`: `[light] reviewers` as a host
    set them, at either tier; unset, the default, with the test reviewer added for a Tier 2, whose
    spec numbers requirements for it to read the tests against, when the full depth runs it too."""
    light = cfg["light"]
    if light.get("chosen") or tier != 2 or "test" not in cfg["reviewers"]:
        return list(light["reviewers"])
    wanted = {*light["reviewers"], "test"}
    return [r for r in REVIEWERS if r in wanted]


def change_tier(folder: Path) -> int | None:
    """The tier `intent.md` gives, or None when there is none that reads as a number."""
    path = folder / "intent.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    tier = frontmatter(text).get("tier", "")
    return int(tier) if tier.isdigit() else None


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


def _review_list(root: Path, base: str, key: str) -> list[str]:
    """`[review] <key>` as the base branch holds it, never this checkout's: a change can't lighten
    its own review by editing the list."""
    try:
        data = tomllib.loads(_git(root, "show", f"{base}:{SDLC_CONFIG.as_posix()}") or "")
    except tomllib.TOMLDecodeError:
        return []
    review = data.get("review")
    listed = review.get(key) if isinstance(review, dict) else None
    return [p for p in listed if isinstance(p, str)] if isinstance(listed, list) else []


def _sensitive(root: Path, base: str) -> list[str]:
    return _review_list(root, base, "sensitive")


def _irreversible(root: Path, base: str) -> list[str]:
    return _review_list(root, base, "irreversible")


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


def depth(
    root: Path, cfg: dict, rounds: list[dict], starts: list[int] = (), tier: int | None = None
) -> dict:
    """The depth this run reviews at, from the diff as it stands: `full` with no sensitive list
    (every run, as before there was a choice), when the diff touches a listed path, or once any
    round ran beyond `[light]` (a run never lightens); `light` otherwise. A round's place against
    `[light]`'s rounds is its place in its own run, counted from the newest restart at or before
    it (`starts`, the restarts' rounds), so a restart never deepens a light run. The tier says only
    which reviewers the light depth expects (`light_reviewers()`), never which depth runs, so a
    Tier 2's own test reviewer never counts as beyond `[light]`. Writes nothing."""

    def place(n: int) -> int:
        return n - max((s for s in starts if s <= n), default=1) + 1

    base = _base(root)
    listed = _sensitive(root, base) if base else []
    changed = _changed_paths(root, base) if base else []
    hit = risk_paths(changed, listed)
    light = {"reviewers": light_reviewers(cfg, tier), "rounds": cfg["light"]["rounds"]}
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


def behind_base(root: Path) -> dict:
    """`base`, the branch the change lands on, and `behind`, how many of its commits `HEAD`
    lacks: both None when there is no base branch. Reads only."""
    base = _base(root)
    count = _git(root, "rev-list", "--count", f"HEAD..{base}") if base else None
    return {"base": base, "behind": int(count) if count and count.isdigit() else None}


def _listed(names: list[str]) -> str:
    """`a`, `a and b`, `a, b and c`; `no reviewer` for none, which the config allows."""
    if not names:
        return "no reviewer"
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def build_question(start: dict, check: str | None, sensitive: list[str]) -> str:
    """The build gate's question, worded here so the skill never words its own, from `start`'s
    output and the base branch's `[commands] check` and `[review] sensitive`: the restart form for
    a `restart`, the upgraded form for an `upgraded` run, the spec-draft form for a `spec`, the
    plain form otherwise. The gate clause reads `, with no gate configured` with no check; the
    light parenthesis appears only with a sensitive list, since every run is full without one; the
    UI clause only when `[ui]` has `serve`, `shoot` and `paths`, since no UI review runs without
    all three."""
    change, restart, upgraded = start["change"], start.get("restart"), start.get("upgraded")
    more = " more" if restart or upgraded else ""

    def rounds(n: int) -> str:
        return f"{n}{more} round{'s' if n != 1 else ''}"

    gate = (
        f", the base branch's gate {check} runs on each build before any reviewer "
        "(up to 2 fixes a round)"
        if check
        else ", with no gate configured"
    )
    review = f", {_listed(start['reviewers'])} review it in up to {rounds(start['rounds'])}"
    if sensitive:
        light = start["light"]
        n = light["rounds"]
        review += (
            f" (or {_listed(light['reviewers'])} in up to {n} round{'s' if n != 1 else ''} "
            "when the diff touches no sensitive path)"
        )
    ui = start["ui"]
    if ui.get("serve") and ui.get("shoot") and ui.get("paths"):
        review += (
            f", and, on a diff touching {', '.join(ui['paths'])}, the ui and ux reviewers, "
            f"which start {ui['serve']}"
        )
    again = " again" if restart else ""
    runs = f"at most {start['max_runs']}{' more' if upgraded else ''} agent runs"
    tail = (
        f", a verifier checks each round's changes, the approver decides{again}, {runs}, agents "
        f"in {start['mode']}, all left uncommitted at stage: test?"
    )
    if restart:
        archive = restart["archive"]
        opening = (
            f"Send {change} back to the factory: decision.md kept as {archive}, the builder "
            f"rebuilds from round {restart['round']} with the approver's reasons"
        )
    elif upgraded:
        opening = (
            f"Write this spec and carry on {change}'s factory run as Tier 2: the builder, "
            f"resumed, rewrites plan.md against it and builds round {upgraded['round']}"
        )
    elif start.get("spec"):
        opening = (
            f"Write this spec and run the factory on {change}: the builder plans and builds it"
        )
    else:
        opening = f"Run the factory on {change}: the builder plans and builds it"
    revise = "revise a requirement / " if upgraded or start.get("spec") else ""
    return f"{opening}{gate}{review}{tail} (yes / {revise}change the reviewers or rounds / no)"


def cmd_start(root: Path, ident: str, purpose: str) -> int:
    """Whether a factory step may start on this change now, and what it will run with."""
    cfg, warnings = load_config(root)
    out: dict = {"change": None, "folder": None, "for": purpose, "tier": None, "stage": None}
    out.update(head=_git(root, "rev-parse", "--short", "HEAD"), **cfg, max_runs=max_runs(cfg))
    out.update(behind_base(root), warnings=warnings, refusals=[], question=None)
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
    # A run upgraded to Tier 2 part way: the gate's question is asked in its upgraded form.
    upgrade, _ = read_upgrade(folder)
    keys = ("round", "decision", "answer")
    out["upgraded"] = {k: upgrade[k] for k in keys} if upgrade else None
    # Each role's model, at either depth, so the gate shows the run's cost before it starts.
    # The light depth's reviewers for this change's tier, as `depth()` will expect them.
    out["light"] = {**cfg["light"], "reviewers": light_reviewers(cfg, tier)}
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
    # The build gate's question, worded by the script; the spec skill asks its own. Its gate and
    # depth clauses are the base branch's, so with none it refuses rather than say there is no gate.
    if purpose == "build" and not out["refusals"] and out["base"] is None:
        out["refusals"].append("no base branch: set [git] base in .sdlc/config.toml")
    if purpose == "build" and not out["refusals"]:
        base = out["base"]
        out["question"] = build_question(out, _base_check(root, base), _sensitive(root, base))
    return emit(out, 1 if out["refusals"] else 0)


def read_rounds(
    folder: Path, reviewers: list[str], kind: str = "round"
) -> tuple[list[dict], list[str]]:
    """Every `reviews/round-<N>/`, in order (the landing's `reviews/land-<n>/` with `kind`
    `land`): each reviewer's verdict, the changes it asks for, the pre-existing problems it found
    and its nits, the verifier's answer when there is one, and whether the round is complete for
    `reviewers`, the ones the run's depth expects. A file whose first line isn't a verdict is a
    problem, never a guess."""
    base = folder / "reviews"
    found = []
    problems = []
    cut = len(kind) + 1
    dirs = [p for p in base.glob(f"{kind}-*") if p.is_dir() and p.name[cut:].isdigit()]
    for path in sorted(dirs, key=lambda p: int(p.name[cut:])):
        n = int(path.name[cut:])
        reviews = {}
        for role in REVIEWERS:
            file = path / f"{role}.md"
            if not file.is_file():
                continue
            lines = file.read_text(encoding="utf-8").splitlines()
            m = VERDICT_RE.match(lines[0]) if lines else None
            if not m:
                problems.append(_no_verdict(n, role, kind))
                continue
            changes = [c.group(1) for c in map(CHANGE_RE.match, lines[1:]) if c]
            if m.group(1) == "CHANGES" and not changes:
                # Nothing to verify or rework: a malformed reply, refused like one with no verdict.
                problems.append(
                    f"reviews/{kind}-{n}/{role}.md says VERDICT: CHANGES but lists no - CHANGE: "
                    "line"
                )
                continue
            preexisting = [c.group(1) for c in map(PREEXISTING_RE.match, lines[1:]) if c]
            nits = [read_nit(c.group(1)) for c in map(FINDING_NIT_RE.match, lines[1:]) if c]
            reviews[role] = {"verdict": m.group(1), "changes": changes, "preexisting": preexisting,
                             "nits": nits}  # fmt: skip
        verified, wrong = read_verified(
            path / VERIFIED, n, reviews, f"reviews/{kind}-{n}/{VERIFIED}"
        )
        problems += wrong
        complete = set(reviewers) <= set(reviews)
        found.append({"round": n, "kind": kind, "reviews": reviews, "complete": complete,
                      "verified": verified})  # fmt: skip
    return found, problems


def read_nit(line: str) -> dict:
    """A `- NIT:` line's text and its weights (`NIT_WEIGHT_RE`): `theme`, `cost` and `value`, each
    None when the line has none the rubric reads, its text then as written."""
    m = NIT_WEIGHT_RE.match(line)
    if not m:
        return {"text": line, "theme": None, "cost": None, "value": None}
    return {"text": m.group(1), "theme": m.group(2), "cost": m.group(3), "value": m.group(4)}


def _no_verdict(n: int, role: str, kind: str = "round") -> str:
    """The problem a round's reply that doesn't open with its verdict is, word for word as the
    board and status show it."""
    return f"reviews/{kind}-{n}/{role}.md doesn't open with VERDICT: PASS or VERDICT: CHANGES"


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
    parts = finding_pass("", change)[1].split(":", 2)
    if len(parts) < 3 or not parts[1].strip().isdigit():
        return None
    return f"{_change_path(change)}:{parts[1].strip()}"


def _resolve(role: str, text: str, asked: list, label: str) -> tuple[str | None, str]:
    """The asked change an answer in round `label` (`round 1`, `land-1`) names, by its id, else its
    exact text, else a `path:line` lead only one of its role's changes has: the reviewer's text, or
    None and why it names none."""
    if m := ID_RE.match(text):
        ident = f"C{m.group(1)}"
        match = next((a for a in asked if a[0] == ident), None)
        if not match:
            return None, f"{ident}, which no change of {label} is"
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
    return None, f"{text}, which no review of {label} asks for"


def read_verified(
    path: Path, n: int, reviews: dict, where: str | None = None
) -> tuple[dict | None, list[str]]:
    """The verifier's `KEPT` and `DROPPED` lines for round `n`, or None before it answered. Each
    answer is resolved to the change it names (`_resolve()`) and carries the reviewer's text, so
    every reader sees the change as it was asked. Every `CHANGE:` the round's `CHANGES` verdicts
    ask for is answered exactly once, and every answer names one: anything else is a problem, so
    no change is reworked or dropped unread. `where` names the file in a problem: a build round's
    unless a landing round's is given."""
    if not path.is_file():
        return None, []
    asked = asked_changes(reviews)
    where = where or f"reviews/round-{n}/{VERIFIED}"
    # The round's kind is its folder's: a landing round's is `land-<n>`, never a build round's.
    label = f"land-{n}" if path.parent.name == f"land-{n}" else f"round {n}"
    kept, dropped, problems = [], [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if m := KEPT_RE.match(line):
            role, text, why = m.group(1), m.group(2), None
        elif m := DROPPED_RE.match(line):
            change, sep, why = m.group(2).rpartition(DROP_WHY)
            role, text, why = m.group(1), (change if sep else m.group(2)).strip(), why.strip()
        else:
            continue
        change, wrong = _resolve(role, text, asked, label)
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
    its `start` whether a restart or the upgrade starts a run there; and the newest restart
    (`restart`, or None) and the upgrade (`upgrade`, or None), whose round starts the run, the
    newer of the two."""
    rounds, problems = read_rounds(folder, cfg["reviewers"])
    restarts, wrong = read_restarts(folder)
    problems += wrong
    upgrade, wrong = read_upgrade(folder)
    problems += wrong
    starts = [r["round"] for r in restarts] + ([upgrade["round"]] if upgrade else [])
    for r in rounds:
        r["start"] = r["round"] in starts
    run = depth(root, cfg, rounds, starts, change_tier(folder))
    run["restart"] = restarts[-1] if restarts else None
    run["upgrade"] = upgrade
    run["ui"] = ui_review(cfg, rounds, run["changed"])
    if run["ui"]:
        run["reviewers"] += [r for r in UI_REVIEWERS if r not in run["reviewers"]]
    for r in rounds:
        r["complete"] = set(run["reviewers"]) <= set(r["reviews"])
    return rounds, problems, run


def finding_pass(role: str, text: str) -> tuple[str, str]:
    """A reviewer's finding's pass and its text: the `[<pass>] ` it opens with, taken off, when
    the pass is one of the four, else its role's and the text as written."""
    m = PASS_TAG_RE.match(text)
    if m and m.group(1) in PASSES:
        return m.group(1), m.group(2)
    return ROLE_PASS.get(role, "correctness"), text


def _change_path(change: str) -> str:
    """The path a `CHANGE:` names, `path/to/file.py:42: what` → `path/to/file.py`, past a pass
    tag it opens with."""
    return finding_pass("", change)[1].split(":", 1)[0].strip().strip("`")


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


def _substitutes(command: str) -> bool:
    """Whether the shell would run something inside `command` before it runs: a backtick, `$(`,
    `<(` or `>(` anywhere but in single-quoted text, where the shell substitutes nothing."""
    quote, escaped = "", False
    for i, ch in enumerate(command):
        if quote == "'":
            quote = "" if ch == "'" else quote
        elif escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == "`" or command[i : i + 2] in ("$(", "<(", ">("):
            return True
        elif ch == "'" and not quote:
            quote = "'"
        elif ch == '"':
            quote = "" if quote else '"'
    return False


def _awk_reads(args: list[str]) -> bool:
    """awk changes nothing when its only options are `-F` and `-v` (so no `-f`, `-i`, `-l` or `-E`
    reads a program or loads an extension the script can't see), and its program holds no pipe, no
    `system(`, no `@load`/`@include`, and no print with a `>` in it."""
    program, i = None, 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            program = args[i + 1] if i + 1 < len(args) else None
            break
        if not arg.startswith("-") or arg == "-":
            program = arg
            break
        if arg in ("-F", "-v"):
            i += 2
            continue
        if arg[:2] in ("-F", "-v"):
            i += 1
            continue
        return False
    if program is None:
        return False
    if "|" in program or AWK_RUNS_RE.search(program):
        return False
    return not AWK_PRINT_RE.search(program)


def _sed_reads(args: list[str]) -> bool:
    """sed changes nothing when it edits nothing in place and every script only prints lines."""
    scripts, files, take = [], [], False
    for arg in args:
        if take:
            scripts.append(arg)
            take = False
        elif arg in ("-e", "--expression"):
            take = True
        elif arg.startswith("--expression="):
            scripts.append(arg.split("=", 1)[1])
        elif arg in ("-n", "-E", "-r", "--quiet", "--silent"):
            continue
        elif arg.startswith("-") and arg != "-":
            return False
        else:
            files.append(arg)
    if not scripts and files:
        scripts.append(files.pop(0))
    if take or not scripts:
        return False
    return all(SED_PRINT_RE.match(part) for s in scripts for part in s.split(";"))


def _git_reads(args: list[str]) -> bool:
    """git changes nothing in a subcommand that only shows, with no option that writes a file
    or runs another program (`GIT_RUNS`, `GIT_FORMATS`)."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            i += 2
        elif args[i] == "--no-pager":
            i += 1
        else:
            return False
    if i >= len(args) or args[i] not in GIT_READS:
        return False
    rest = args[i + 1 :]
    for k, arg in enumerate(rest):
        name = arg.split("=", 1)[0]
        if name in ("--output", "--open-files-in-pager") or arg.startswith("-O"):
            return False
        if any(len(name) >= n and option.startswith(name) for option, n in GIT_RUNS):
            return False
        # A format's value, after `=` or as the next word, holding a `%G` placeholder runs gpg.
        if name in GIT_FORMATS:
            value = arg.split("=", 1)[1] if "=" in arg else " ".join(rest[k + 1 : k + 2])
            if "%G" in value:
                return False
    return True


def _simple_read(words: list[str]) -> bool:
    """One simple command, its redirections already taken out, judged by its own program."""
    if not words or ASSIGNMENT_RE.match(words[0]):
        return False
    name, args = words[0], words[1:]
    if name in READS:
        return True
    if name == "awk":
        return _awk_reads(args)
    if name == "sed":
        return _sed_reads(args)
    if name == "git":
        return _git_reads(args)
    if name == "sort":
        return not any(
            a.startswith(("--o", "--compress"))
            or (a.startswith("-") and not a.startswith("--") and "o" in a)
            for a in args
        )
    if name == "file":  # `-C` (`--compile`) writes `<magic>.mgc`
        return not any(
            a.startswith("--co") or (a.startswith("-") and not a.startswith("--") and "C" in a)
            for a in args
        )
    if name == "rg":
        return not any(a.startswith("--pre") for a in args)  # `--pre <cmd>` runs a program
    if name == "find":
        return not any(a.startswith(FIND_REFUSED) for a in args)
    return False


def is_read(command: str) -> bool:
    """Whether the script can tell `command` changes nothing: every stage of it, split at `|`,
    `||`, `&&` and `;`, a program on the closed allowlist under that program's condition, with no
    substitution, no assignment, and no output redirected anywhere but `/dev/null` or a descriptor.
    Pure, and strict: a read judged a non-read costs one mend; the other way loses a result."""
    if _substitutes(command):
        return False
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split, lexer.commenters = True, ""
    try:
        tokens = list(lexer)
    except ValueError:
        return False
    stages: list[list[str]] = [[]]
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in SEPARATORS:
            stages.append([])
        elif token in REDIRECTS:
            if i + 1 >= len(tokens):
                return False
            target = tokens[i + 1]
            # Only `>&` takes a descriptor (`2>&1`, `>&2`): after `>`, `>>` or `&>` a digit is
            # a file's name (`cat a >2` writes `2`).
            descriptor = token == ">&" and target.isdigit()
            if token != "<" and target != "/dev/null" and not descriptor:
                return False
            i += 1
        elif token and all(ch in lexer.punctuation_chars for ch in token):
            return False
        else:
            stages[-1].append(token)
        i += 1
    return all(_simple_read(stage) for stage in stages)


def read_evidence(text: str, where: str) -> list[str]:
    """What's wrong with a reply's `## Evidence` section: missing, no command in it, or a command
    whose `exit:` line never comes before the next command or the section's end, unless it is a
    read (`is_read()`) that printed a line, neither blank nor a fence, which is its result."""
    lines = text.splitlines()
    if EVIDENCE not in [line.strip() for line in lines]:
        return [f"{where} has no `{EVIDENCE}` section: each command it ran, its output, its exit"]
    start = [line.strip() for line in lines].index(EVIDENCE) + 1
    commands, open_cmd, printed, problems = 0, None, False, []

    def close() -> None:
        if open_cmd and not (printed and is_read(open_cmd)):
            problems.append(f"{where}: `{open_cmd}` has no `exit:` line")

    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.lstrip().startswith("$ "):
            close()
            open_cmd, printed, commands = line.strip()[2:], False, commands + 1
        elif EXIT_RE.match(line):
            open_cmd = None
        elif line.strip() and not line.lstrip().startswith(("```", "~~~")):
            printed = True
    close()
    if not commands:
        problems.append(f"{where}'s `{EVIDENCE}` shows no command run (`$ <command>`)")
    return problems


NO_DECISION = "decision.md doesn't open with DECISION: READY or DECISION: ESCALATE"


def decision_preamble(folder: Path) -> bool:
    """Whether `decision.md` holds its `DECISION:` line, but not first: `preamble()`'s rule for the
    approver's reply, which the run may mend once by asking again."""
    path = folder / "decision.md"
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    return bool(lines) and not DECISION_RE.match(lines[0]) and any(map(DECISION_RE.match, lines))


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
        return None, NO_DECISION
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


def upgraded_path(folder: Path, n: int) -> Path:
    return folder / "build" / f"round-{n}.upgraded.md"


def upgrade_answer(ledger: list[dict]) -> dict | None:
    """The first ledger line that upgrades the change: blocking, ticked and decided by the person
    (never superseded), its answer starting `upgrade to Tier 2`. An open line, a default, or any
    other answer is None: an agent asking is never the person deciding."""
    for d in ledger:
        if d["kind"] == "blocking" and d["decided"] and UPGRADE_ANSWER_RE.match(d["answer"] or ""):
            return d
    return None


def read_upgrade(folder: Path) -> tuple[dict | None, list[str]]:
    """The upgrade record, `build/round-<P>.upgraded.md`, as its round, the decision it names, that
    decision's question and the person's answer, and its own path in the folder; and what's wrong
    with it: a second record (a change is upgraded once), a first line that isn't `UPGRADED:
    D<n>`, or a decision that isn't a decided upgrade answer. (None, []) with no record."""
    found = []
    for path in (folder / "build").glob("round-*.upgraded.md"):
        m = UPGRADED_FILE_RE.match(path.name)
        if m:
            found.append((int(m.group(1)), path))
    if not found:
        return None, []
    found.sort()
    problems = []
    if len(found) > 1:
        names = ", ".join(f"build/{p.name}" for _, p in found)
        problems.append(f"{names}: a change is upgraded once, and these are {len(found)} records")
    n, path = found[0]
    where = f"build/{path.name}"
    lines = path.read_text(encoding="utf-8").splitlines()
    m = UPGRADED_RE.match(lines[0]) if lines else None
    if not m:
        return None, [*problems, f"{where} doesn't open with UPGRADED: D<n>"]
    entry = next((d for d in read_ledger(folder) if d["id"] == m.group(1)), None)
    if entry is None or upgrade_answer([entry]) is None:
        return None, [*problems, (
            f"{where} names {m.group(1)}, which isn't a decided blocking line in decisions.md "
            "answered `upgrade to Tier 2`"
        )]  # fmt: skip
    return {
        "round": n, "decision": entry["id"], "question": entry["text"], "answer": entry["answer"],
        "record": where,
    }, problems  # fmt: skip


def newest_round(folder: Path) -> int:
    """The newest round built or reviewed: one past it is the round a restart or an upgrade
    starts."""
    reviewed = [
        int(p.name[6:]) for p in (folder / "reviews").glob("round-*")
        if p.is_dir() and p.name[6:].isdigit()
    ]  # fmt: skip
    return max([build_round(folder), *reviewed])


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
    newest = newest_round(folder)
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
    the person's answer once the line is ticked, and `superseded_by`, the default that replaced
    it. `decided` is a ticked line the person answered, `open` an unticked one: a superseded line
    is neither, so no reader counts it as assumed or as the person's word."""
    path = folder / "decisions.md"
    if not path.is_file():
        return []
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = LEDGER_RE.match(line)
        if m:
            text, _, answer = m.group(5).partition(DECIDED)
            text, _, by = text.partition(SUPERSEDED)
            ticked, by = m.group(1) == "x", by.strip() or None
            found.append(
                {"id": m.group(2), "source": m.group(3), "kind": m.group(4), "text": text.strip()}
                | {
                    "decided": ticked and not by,
                    "open": not ticked,
                    "answer": answer.strip() or None,
                }
                | {"superseded_by": by}
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


def _supersede_refusal(ledger: list[dict], target: str, new: str) -> str | None:
    """Why default `new` can't supersede `target`, or None when it can."""
    entry = next((d for d in ledger if d["id"] == target), None)
    if target == new:
        return f"{new} names itself"
    if entry is None:
        return f"there is no {target} in decisions.md"
    if entry["kind"] != "default":
        return f"{target} is not a default: a blocking decision is the person's to answer"
    if entry["superseded_by"]:
        return f"{target} is already superseded by {entry['superseded_by']}"
    if entry["decided"]:
        return f"{target} is decided by the person: raise a blocking decision instead"
    return None


def cmd_decisions(root: Path, ident: str) -> int:
    """Bring every decision the agents raised into `decisions.md`, once each, with a stable id,
    and say which blocking ones are still waiting for the person. The ledger is the one place a
    person answers: ticking a line with ` → decided: <answer>` is the answer. A default raised as
    `(supersedes D<n>)` ticks D<n>'s line with ` → superseded by D<m>`, that line alone, and only
    when D<n> is a default still open (`unmarked` says why not); the prefix stays out of the new
    line's text, which is what keeps it from being added twice."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    ledger = read_ledger(folder)
    known = {d["text"] for d in ledger}
    added, new_lines, marks, unmarked = [], [], {}, []
    for source, kind, raised in raised_decisions(folder):
        named = SUPERSEDES_RE.match(raised) if kind == "default" else None
        text = named.group(2) if named else raised
        if text in known:
            continue
        known.add(text)
        added.append(f"D{len(ledger) + 1}")
        ledger.append(
            {"id": added[-1], "source": source, "kind": kind, "text": text}
            | {"decided": False, "open": True, "answer": None, "superseded_by": None}
        )
        new_lines.append(f"- [ ] {added[-1]} ({source}, {kind}): {text}\n")
        if named:
            why = _supersede_refusal(ledger, named.group(1), added[-1])
            if why:
                unmarked.append({"id": added[-1], "supersedes": named.group(1), "why": why})
                continue
            entry = next(d for d in ledger if d["id"] == named.group(1))
            entry.update(superseded_by=added[-1], open=False)
            marks[entry["id"]] = added[-1]
    if new_lines:
        path = folder / "decisions.md"
        body = path.read_text(encoding="utf-8") if path.is_file() else "# Decisions\n\n"
        body += "" if body.endswith("\n") else "\n"
        lines = (body + "".join(new_lines)).splitlines(keepends=True)
        for i, line in enumerate(lines):
            m = LEDGER_RE.match(line)
            if m and m.group(1) == " " and m.group(2) in marks:
                end = "\n" if line.endswith("\n") else ""
                ticked = "- [x]" + line.rstrip("\r\n")[len("- [ ]") :]
                lines[i] = f"{ticked}{SUPERSEDED}{marks[m.group(2)]}{end}"
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    pending = [d["id"] for d in ledger if d["kind"] == "blocking" and d["open"]]
    assumed = [d["id"] for d in ledger if d["kind"] == "default" and d["open"]]
    return emit(
        {"change": folder.name, "decisions": ledger, "added": added}
        | {"pending": pending, "assumed": assumed, "superseded": list(marks), "unmarked": unmarked}
    )


def stop_text(change: str, way: str, problems: list[str]) -> str:
    """`runs/stopped.md`'s text: the way on, its short sentence, the longer one (`WAYS_WHY`), and
    each problem on a line of its own."""
    ident = change.split("-", 1)[0]
    lines = [f"STOPPED: {way}", f"NEXT: {WAYS[way].format(id=ident)}", ""]
    lines += [WAYS_WHY[way].format(id=ident), ""]
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
    limit and expected reviewers, since when, and on a pause (`PAUSES`) the step it paused at."""
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
    round hold, and on a pause (`PAUSES`) the step it paused at."""
    path = folder / STEP
    try:
        old = read_step(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        old = None
    same = old and old["step"] == out["next"] and old["round"] == out.get("round")
    since = old["since"] if same and old["since"] else _utc_now()
    after = None
    if out["next"] in PAUSES and old:
        after = old["after"] if old["step"] in PAUSES else old["step"]
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
    - `upgrade`: the person answered `upgrading`, a blocking decision, `upgrade to Tier 2`, on a
      Tier 1 change: run `upgrade`. A record left with the tier still 1 names it again, to finish.
    - `spec`: an upgraded change (`upgraded`) owes its spec before round `round` builds: draft it
      and ask for it, `written` true once `spec.md` is no longer its scaffold. At `stage: build`,
      `build` at that round, the builder resumed.
    - `done`: the decision is in.
    - `stop`: a problem, or `HEAD` moved: an agent committed, which none may.

    What has been built and what has been reviewed are compared by round: a builder report newer
    than the last complete review round is always reviewed, whether it came from a rework or from
    an answer the person gave, so no build reaches the approver unreviewed.

    A stop names its `way` on (`WAYS`): `ship` when `HEAD` moved, `mend` when every problem is a
    missing `## Evidence`, a verdict after a preamble in the last round (`preamble()`), the
    verifier's unread answers in the last round, or a decision after a preamble
    (`decision_preamble()`), with the roles to mend in `mend`, `rerun` otherwise. A role is mended
    once a round: one `runs/mended` names for that round no longer counts as mendable.

    Run `decisions` first: this reads the ledger as it stands, and writes nothing, but with
    `--record`, which only the supervisor passes and only with `--head`: then a stop is written to
    `runs/stopped.md` (`stop_text()`) for the board and status, from this same reading, and any
    other step removes it; and every reading is written to `runs/step.md` (`step_text()`) for the
    board's step track, its `SINCE:` kept while the step and round hold. Nothing in the loop reads
    either back.

    Beside the step: the run's `depth` (`depth()`), `reworked` (the paths the round to review
    changed since the last, from the snapshots), `settled` (what earlier rounds answered, never
    raised again), and for the verifier, `repeats` (a change raised again) and `untouched` (one on
    a path the change doesn't touch: pre-existing, never reworked); and `handed`, the cheap nits
    (`cheap_nits()`) a `rework` gives the builder beside its kept changes, or that the `review`
    after it names to the roles that raised them. Nits never make a step: a round with nits and no
    kept change goes to `approve`.
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
    # A restarted or upgraded run's rounds count from its restart or its upgrade, the newer: round
    # R or P is its first.
    restart, upgrade = run["restart"], run["upgrade"]
    first = max(restart["round"] if restart else 1, upgrade["round"] if upgrade else 1)
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
    out.update(upgraded=upgrade, upgrading=None, written=None)
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    tier, stage = change_tier(folder), meta.get("stage") or None
    ledger = read_ledger(folder)
    out["pending"] = [d["id"] for d in ledger if d["kind"] == "blocking" and d["open"]]
    out["assumed"] = [d["id"] for d in ledger if d["kind"] == "default" and d["open"]]
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
    # The verifier's answers in the last round the script couldn't read, and the approver's
    # decision after a preamble: each its own agent's to give again.
    if last:
        path = folder / "reviews" / f"round-{last['round']}" / VERIFIED
        _, wrong = read_verified(path, last["round"], last["reviews"])
        if wrong:
            mendable["verifier"] = wrong
    if decision_preamble(folder):
        mendable["approver"] = [NO_DECISION]
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
    elif tier == 1 and not decision and (upgrade or upgrade_answer(ledger)):
        # A record with the tier still 1 is an upgrade cut short: the same one, finished.
        out["next"] = "upgrade"
        out["upgrading"] = upgrade["decision"] if upgrade else upgrade_answer(ledger)["id"]
    elif upgrade and upgrade["round"] > built and stage != "build" and not decision:
        out["next"], out["round"] = "spec", upgrade["round"]
        spec = folder / "spec.md"
        out["written"] = spec.is_file() and not _scaffold(spec.read_text(encoding="utf-8"))
    elif decision:
        out["next"] = "done"
    elif restart and restart["round"] > built:
        out["next"], out["round"] = "build", restart["round"]
    elif upgrade and upgrade["round"] > built:
        out["next"], out["round"] = "build", upgrade["round"]
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
    # The cheap nits a rework is handed, the round's own (`cheap_nits()`), and the ones the round
    # after it reviews: none when it starts a restarted or upgraded run, which starts fresh.
    out["handed"] = []
    rnd = out["round"]
    prev = next((r for r in rounds if r["round"] == (rnd or 0) - 1), None)
    fresh = {(restart or {}).get("round"), (upgrade or {}).get("round")}
    if out["next"] == "rework":
        out["handed"] = [{"role": a, "text": b} for a, b in cheap_nits(last)]
    elif out["next"] == "review" and prev and prev["complete"] and rnd not in fresh:
        kept_before = (prev["verified"] or {}).get("kept")
        out["handed"] = [{"role": a, "text": b} for a, b in cheap_nits(prev)] if kept_before else []
    return out, None


def cmd_carry(root: Path, ident: str) -> int:
    """Each change the last complete round still asks for and the verifier kept (every one, in a
    round from before there was a verifier), every pre-existing problem a reviewer found, and each
    nit weighed `high` or `L` (`agent_findings()`'s `note`), as an unticked `- [ ]` line in
    notes.md, so `/sdlc:ship` must give each a disposition. Once only: a line already there,
    ticked or not, isn't added again. Then the record: every agent finding of every complete
    round, in `findings.md` beside notes.md (`write_findings()`)."""
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
    # A nit weighed `high` or `L` is no nit: left undone, for the approver to propose like any.
    wanted += [f"{i['role']}: {i['text']}" for i in agent_findings(rounds) if i["note"]]
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
    findings = write_findings(folder, rounds)
    return emit({"change": folder.name, "notes": str(notes), "added": added, "findings": findings})


def cheap_nits(r: dict) -> list[tuple[str, str]]:
    """Round `r`'s nits weighed `S` and `med`, worth fixing before the commit that found them, as
    `(role, text)`, each once, in `REVIEWERS` order: what a rework of the round is handed."""
    return list(dict.fromkeys(
        (role, n["text"])
        for role in REVIEWERS if role in r["reviews"]
        for n in r["reviews"][role].get("nits") or []
        if (n["cost"], n["value"]) == ("S", "med")
    ))  # fmt: skip


def reworked_round(rounds: list[dict], n: int) -> bool:
    """Whether round `n`'s rework ran, read from the rounds alone: its verifier kept a change, and
    round `n + 1` was built, but not as a restart's or an upgrade's first round, which starts
    fresh. Its cheap nits (`cheap_nits()`) were handed to the builder then."""
    this = next((r for r in rounds if r["round"] == n), None)
    after = next((r for r in rounds if r["round"] == n + 1), None)
    kept = this and (this["verified"] or {}).get("kept")
    return bool(kept and after and not after.get("start"))


def agent_findings(rounds: list[dict]) -> list[dict]:
    """Every distinct `(role, text)` the complete `rounds` raised, as the record's findings, in
    round order (the build's rounds, then the landing's), then `REVIEWERS` order, then each file's
    order (its changes, its pre-existing problems, its nits): a change the verifier kept is
    `fixed`, or `recorded` while the last complete build round still carries it to notes.md, or
    the last landing round kept it and no later one followed; one it dropped is `wrong` with its
    why; a pre-existing problem `recorded`. In a round from before there was a verifier, every
    change counts as kept. A change asked under a `PASS` verdict was never asked. The same
    `(role, text)` in a build round and a landing round is one finding, the first.

    A nit is keyed by its text without its weights, which the latest complete build round that
    raised it gives, and disposed of by them, never by a model: without weights it is `minor`;
    `high` value is never a nit but an `important` finding, and `L` cost an idea, each `recorded`
    and `note`d for notes.md; `S` with `med` is `fixed` when a rework was handed it
    (`reworked_round()`) and a later complete build round of its role doesn't raise it again;
    every other is `recorded`, to file as a `[nit]` entry (`file`), but one naming no path, and
    any past the first `NIT_CAP`, `minor`. Only the build's rounds are weighed, so what the
    landing filed is what the record says: a nit only a landing round raised, after the filing,
    is `minor`."""
    done = [r for r in rounds if r["complete"]]

    def kept_of(r: dict) -> list[tuple[str, str]]:
        if r["verified"] is not None:
            return [(k["role"], k["change"]) for k in r["verified"]["kept"]]
        return [(role, c) for _, role, c in asked_changes(r["reviews"])]

    carried = set()
    for kind in ("round", "land"):
        last = [r for r in done if r.get("kind", "round") == kind][-1:]
        carried |= set(kept_of(last[0])) if last else set()
    kept = {k for r in done for k in kept_of(r)}
    why = {(d["role"], d["change"]): d["why"] for r in done
           for d in (r["verified"] or {"dropped": []})["dropped"]}  # fmt: skip
    found: dict[tuple[str, str], dict] = {}
    latest: dict[tuple[str, str], tuple[int, dict]] = {}
    for r in done:
        for role in [x for x in REVIEWERS if x in r["reviews"]]:
            review = r["reviews"][role]
            asked = review["changes"] if review["verdict"] == "CHANGES" else []
            nits = review.get("nits") or []
            for nit in nits if r.get("kind", "round") == "round" else ():
                latest[(role, nit["text"])] = (r["round"], nit)
            for kind, texts in (("change", asked), ("pre-existing", review["preexisting"]),
                                ("nit", [n["text"] for n in nits])):  # fmt: skip
                for text in texts:
                    if (role, text) in found:
                        continue
                    item = {"role": role, "text": text, "round": r["round"], "reason": None,
                            "kind": r.get("kind", "round"), "file": None,
                            "note": False}  # fmt: skip
                    if kind == "pre-existing":
                        item.update(rank="pre-existing", disposition="recorded")
                    elif kind == "nit":
                        item.update(rank="nit")
                    elif (role, text) in carried:
                        item.update(rank="important", disposition="recorded")
                    elif (role, text) in kept:
                        item.update(rank="important", disposition="fixed")
                    elif (role, text) in why:
                        item.update(rank="important", disposition="wrong", reason=why[(role, text)])
                    else:
                        continue
                    found[(role, text)] = item
    built = [r for r in rounds if r.get("kind", "round") == "round"]
    filed = 0
    for (role, text), item in found.items():
        if item["rank"] != "nit":
            continue
        if (role, text) not in latest:
            item.update(disposition="minor", reason=NIT_REASON)
            continue
        last, nit = latest[(role, text)]
        later = [r for r in built if r["complete"] and r["round"] > last and role in r["reviews"]]
        if nit["cost"] is None:
            item.update(disposition="minor", reason=NIT_REASON)
            continue
        item.update(theme=nit["theme"], cost=nit["cost"], value=nit["value"])
        if nit["value"] == "high":
            item.update(rank="important", disposition="recorded", reason=HIGH_REASON, note=True)
        elif nit["cost"] == "L":
            item.update(disposition="recorded", reason=IDEA_REASON, note=True)
        elif (nit["cost"], nit["value"]) == ("S", "med") and reworked_round(built, last) and later:
            item.update(disposition="fixed", reason=HANDED_REASON)
        else:
            pass_, said = finding_pass(role, text)
            m = LEAD_RE.match(said)
            if not m:
                item.update(disposition="minor", reason=NO_PATH_REASON)
            elif filed >= NIT_CAP:
                item.update(disposition="minor", reason=CAP_REASON)
            else:
                filed += 1
                item.update(disposition="recorded")
                item["file"] = {
                    "title": first_sentence(m.group(3)).strip() or said, "text": said,
                    "theme": nit["theme"], "paths": [m.group(1)], "cost": nit["cost"],
                    "value": nit["value"], "pass": pass_, "role": role, "round": item["round"],
                }  # fmt: skip
    return list(found.values())


def finding_section(n: int, item: dict) -> str:
    """One agent finding as findings.md's `## F<n>. [rank] [pass] title` section: its title the
    text after its lead, to the first sentence's end; its whole line below; `Evidence:` its
    leading `path[:line]`, else the review file it is in."""
    pass_, text = finding_pass(item["role"], item["text"])
    kind = item.get("kind", "round")
    where = f"reviews/{kind}-{item['round']}/{item['role']}.md"
    m = LEAD_RE.match(text)
    evidence = (m.group(1) + (f":{m.group(2)}" if m.group(2) else "")) if m else where
    title = first_sentence(m.group(3) if m else text).strip() or text
    which = "landing round" if kind == "land" else "round"
    lines = [f"## F{n}. [{item['rank']}] [{pass_}] {title}", "", text, "",
             f"Evidence: {evidence}", f"Class: {item['role']} review, {which} {item['round']}",
             f"Disposition: {item['disposition']}"]  # fmt: skip
    if item.get("file"):
        lines += [f"Theme: {item['theme']}", f"Cost: {item['cost']}", f"Value: {item['value']}"]
    if item["reason"]:
        lines.append(f"Reason: {item['reason']}")
    lines.append(f"By: {item['role']}")
    return "\n".join(lines) + "\n"


def write_findings(folder: Path, rounds: list[dict]) -> int:
    """findings.md with the agents' findings (`agent_findings()`) in place of the ones a run of
    this wrote before, found by their `By:` naming a factory role: its title and note, a line
    `_note_line()` set in it included, and every other section, ship's own, kept as written, and
    the agents' numbered after the highest id kept. Started from `FINDINGS_HEAD` when missing.
    With no complete round, an existing file is left as it is. How many agent findings it holds."""
    path = folder / "findings.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else FINDINGS_HEAD
    if not any(r["complete"] for r in rounds):
        if not path.is_file():
            path.write_text(text, encoding="utf-8", newline="\n")
        return 0
    head, sections, fenced = [], [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            sections.append([line])
        elif sections:
            sections[-1].append(line)
        else:
            head.append(line)
    agents = {f"By: {r}" for r in REVIEWERS}
    kept = [sec for sec in sections if not agents & {ln.strip() for ln in sec}]
    top = max((int(m.group(1)) for sec in kept if (m := FINDING_HEAD_RE.match(sec[0]))), default=0)
    items = agent_findings(rounds)
    parts = ["\n".join(head).rstrip("\n") + "\n"]
    parts += ["\n".join(sec).rstrip("\n") + "\n" for sec in kept]
    parts += [finding_section(top + i, item) for i, item in enumerate(items, 1)]
    path.write_text("\n".join(parts), encoding="utf-8", newline="\n")
    return len(items)


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


def _land_gate_state(root: Path, folder: Path, n: int, settled: bool = False) -> dict | None:
    """The gate on landing round `n`'s rebased change, as `_gate_state` reads a build's: None when
    the base branch names no check. `settled` reads a round already reviewed: its last attempt's
    verdict stands whatever `HEAD` is now, which the landing's own record and later rebases move."""
    base = _base(root)
    command = _base_check(root, base) if base else None
    if command is None:
        return None
    record = read_gate_file(land_gate_path(folder, n)) or {"attempts": [], "fails": 0}
    last = record["attempts"][-1] if record["attempts"] else None
    ran_on = last and (settled or last["build"] == landed_build(root))
    current = last["verdict"] if ran_on else None
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


# Each of `gate_jobs` slots is a lock on a file of its own in the git common dir, which every
# worktree shares and no `git status` shows; never `sdlc.py`'s `sdlc.lock`, which `new` claims
# numbers under. A lock held on an open descriptor, never a file whose existence is the lock, so
# the OS frees it when its gate ends, however it ends. The files stay. `sdlc.py gate`, the gate
# run by hand, takes the same slots through copies of these, pinned by `tests/test_hand_gate.py`.
SLOT_NAME = "sdlc-factory-gate-{}.lock"
SLOT_POLL = 0.25


def _slot_dir(root: Path) -> Path | None:
    common = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common) if common else None


def _try_lock(fd: int) -> bool:
    """Take an exclusive lock on `fd` without waiting: True when taken, False when another holds
    it. Each platform's module is imported here only, never at the top: neither exists on both."""
    if os.name == "nt":
        import errno
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError as e:
            if e.errno in (errno.EACCES, getattr(errno, "EDEADLOCK", 36)):
                return False
            raise
        return True
    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    return True


def _unlock(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    # Elsewhere, closing the descriptor releases a flock.


@contextmanager
def gate_slot(root: Path, jobs: int, change: str) -> Iterator[tuple[int | None, float]]:
    """Hold one of `jobs` gate slots for the `with` block, waiting until one is free, and yield
    which (`k`) and how many seconds the wait took (0.0 for none). A wait says so once, on stderr.
    Outside a git repo there are no slots: `(None, 0.0)`, and the gate runs unlimited."""
    where = _slot_dir(root)
    if where is None:
        yield None, 0.0
        return
    start, fds, held = time.monotonic(), [], None
    try:
        for k in range(jobs):
            fds.append(os.open(where / SLOT_NAME.format(k), os.O_RDWR | os.O_CREAT, 0o644))
        said = False
        while held is None:
            held = next((k for k, fd in enumerate(fds) if _try_lock(fd)), None)
            if held is None:
                if not said:
                    print(f"{change}: waiting for a gate slot ({jobs} of {jobs} in use)",
                          file=sys.stderr, flush=True)  # fmt: skip
                    said = True
                time.sleep(SLOT_POLL)
        waited = round(time.monotonic() - start, 1) if said else 0.0
        try:
            yield held, waited
        finally:
            _unlock(fds[held])
    finally:
        for fd in fds:
            os.close(fd)


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
    jobs = load_config(root)[0]["gate_jobs"]
    with gate_slot(root, jobs, folder.name) as (slot, waited):
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
    out.update(exit=exit_text, seconds=seconds, waited=waited, slot=slot, tree=tree)
    out["to"] = path.relative_to(root).as_posix()
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


# `sdlc.py`'s scaffold rule, copied (never imported) and pinned by `tests/test_factory.py`: a file
# with this many lines opening a `<…>` prompt is still the template it was scaffolded from.
PROMPT_RE = re.compile(r"^<[^>]", re.M)
UNFILLED_THRESHOLD = 2


def _scaffold(text: str) -> bool:
    """Whether `text` is still a scaffold, as `sdlc.py`'s `is_unfilled()` reads one."""
    return len(PROMPT_RE.findall(text)) >= UNFILLED_THRESHOLD


def cmd_write_spec(root: Path, ident: str) -> int:
    """Copy `runs/spec-draft.md` into `spec.md`, byte for byte, once the person said yes. Refused,
    writing nothing, with no draft, for a change that isn't a Tier 2 at `stage: plan`, or once
    `spec.md` is no longer its scaffold, so a person's text is never written over."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    draft, spec = folder / SPEC_DRAFT, folder / "spec.md"
    refusals = []
    if not draft.is_file():
        refusals.append(f"no {SPEC_DRAFT.as_posix()}: run agent --task spec first")
    if meta.get("tier") != "2" or meta.get("stage") != "plan":
        refusals.append(
            f"write-spec is for a Tier 2 change at stage: plan, not tier {meta.get('tier')} at "
            f"stage: {meta.get('stage')}"
        )
    try:
        written = not _scaffold(spec.read_text(encoding="utf-8"))
    except OSError:
        written = True
    if written:
        refusals.append("spec.md is no longer the scaffold: a person's text is never written over")
    if refusals:
        return emit({"change": folder.name, "refusals": refusals}, 1)
    shutil.copyfile(draft, spec)
    return emit({"change": folder.name, "to": spec.relative_to(root).as_posix()})


def cmd_upgrade(root: Path, ident: str) -> int:
    """Upgrade a Tier 1 change to Tier 2 during its run, once the person's answer to a blocking
    decision said so: refused unless `verdicts` names `upgrade`. Writes
    `build/round-<P>.upgraded.md`, `P` one past the newest round built or reviewed, then runs
    `sdlc.py upgrade` of this factory's own version, which sets `tier: 2` and `stage: plan` and
    scaffolds what a Tier 2 owes. The record first, so a rerun after a stop between the two
    finishes the same upgrade, writing no second record. Commits nothing."""
    state, refusal = loop_state(root, ident, None)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    if state["next"] != "upgrade":
        why = f"verdicts says {state['next']!r}, not 'upgrade'"
        return emit({"change": state["change"], "refusals": [why]}, 1)
    folder, _ = find_change(root, ident)
    stage = frontmatter((folder / "intent.md").read_text(encoding="utf-8")).get("stage")
    if stage not in ("plan", "build"):
        why = f"upgrade takes a Tier 1 change at stage: plan or build, not stage: {stage}"
        return emit({"change": folder.name, "refusals": [why]}, 1)
    upgrade = state["upgraded"]
    rnd = upgrade["round"] if upgrade else newest_round(folder) + 1
    record = upgraded_path(folder, rnd)
    out = {"change": folder.name, "round": rnd, "decision": state["upgrading"]}
    out["record"] = record.relative_to(folder).as_posix()
    if not upgrade:
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(f"UPGRADED: {state['upgrading']}\n", encoding="utf-8", newline="\n")
    code, data, said = _sdlc(["upgrade", folder.name], root)
    if code or data is None:
        why = "; ".join((data or {}).get("refusals") or []) or said.strip()[-500:]
        return emit({**out, "refusals": [f"sdlc.py upgrade refused: {why}"]}, 1)
    out.update({k: data.get(k) for k in ("tier", "stage", "created", "kept")})
    return emit({**out, "refusals": []})


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
# the loop. `SINCE:` holds while `STEP:` and `ROUND:` do; `AFTER:` is the step a pause held.
STEP = Path("runs") / "step.md"
STEP_RE = re.compile(r"^STEP: ([a-z]+)\s*$")
ROUND_RE = re.compile(r"^ROUND: ?(\d*)\s*$")
LIMIT_RE = re.compile(r"^LIMIT: ?(\d*)\s*$")
REVIEWERS_RE = re.compile(r"^REVIEWERS: ?(.*?)\s*$")
SINCE_RE = re.compile(r"^SINCE: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$")
AFTER_RE = re.compile(r"^AFTER: ([a-z]+)\s*$")
# The steps that pause a run for the person, each recorded with `AFTER:`, the step it paused at: a
# decision to answer, and an upgrade with the spec it owes. The board keeps a copy, pinned.
PAUSES = ("decide", "upgrade", "spec")
# What moves a stopped run on, by its way: the record's `NEXT:` line, the command and a few words,
# so it reads in two lines of a card at phone width (the board's `next:`, `status`'s `→` line).
WAYS = {
    "ship": "read the commit, then /sdlc:ship {id}",
    "mend": "rerun /sdlc-factory:build {id}, or /sdlc:ship {id}",
    "rerun": "fix its cause, then /sdlc-factory:build {id}, or /sdlc:ship {id}",
}
# The longer sentence under it, in the record's body, which the board's drawer shows. No reader
# parses it: it matches none of `STOPPED_RE`, `NEXT_RE` or `PROBLEM_RE`.
WAYS_WHY = {
    "ship": "An agent committed, which no agent may: read the commit, then ship it by hand with"
    " /sdlc:ship {id}.",
    "mend": (
        "A reply lacked its ## Evidence, or held its answer after a preamble. Rerunning"
        " /sdlc-factory:build {id} asks an agent again, once, for the reply in its shape; if that"
        " reply still lacks it, ship it by hand with /sdlc:ship {id}."
    ),
    "rerun": (
        "Fix the cause the problems below name, then rerun /sdlc-factory:build {id}, or ship it by"
        " hand with /sdlc:ship {id}."
    ),
}
# The run's own token counts, as `runs/costs.jsonl` names them, from the result's `usage`.
USAGE_FIELDS = {
    "in": "input_tokens", "out": "output_tokens",
    "cache_create": "cache_creation_input_tokens", "cache_read": "cache_read_input_tokens",
}  # fmt: skip
TASKS = ("spec", "build", "fix", "review", "verify", "rework", "decided", "mend", "approve",
         "resolve", "land-fix", "land-review", "land-verify", "land-mend")  # fmt: skip
# The role each task runs as; `review`, `mend` and `land-review` are told theirs.
TASK_ROLE = {
    "spec": "spec-writer", "build": "builder", "fix": "builder", "verify": "verifier",
    "rework": "builder", "decided": "builder", "approve": "approver", "resolve": "builder",
    "land-fix": "builder", "land-verify": "verifier",
}  # fmt: skip
# The landing's tasks: the builder resolving a rebase's conflicts or making a fix the person asked
# for, the review of the change as it now stands on the base branch, and the mend of a landing
# reply `land-verdicts` names. Never steps of the build's loop, so `verdicts` names none.
LAND_TASKS = ("resolve", "land-fix", "land-review", "land-verify", "land-mend")
# The step `verdicts` must name for a task to run, so no step is taken out of turn.
TASK_STEP = {"build": "build", "fix": "fix", "review": "review", "verify": "verify",
             "rework": "rework", "approve": "approve"}  # fmt: skip
# What the builder resumes on when a task carries on its own session.
RESUMES = ("fix", "rework", "decided", "mend", "resolve", "land-fix")
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
DECISION_MEND = (
    "Your reply didn't open with its decision. Reply again, the whole reply, with its DECISION: "
    "line as the first line and nothing before it."
)
VERIFY_MEND = (
    "The script couldn't read your answers: {problems}. Reply again, the whole reply, answering "
    "each change exactly once as plain text with no emphasis, `- KEPT: <role>: C<n>: <why>` or "
    "`- DROPPED: <role>: C<n>: <the change> — <why>`."
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


# Where a spec-writer's reply is filed: the draft, cut from its questions, each whole.
SPEC_DRAFT = Path("runs") / "spec-draft.md"
SPEC_QUESTIONS = Path("runs") / "spec-questions.md"
# A fence's opening or closing line, as CommonMark reads one: its character and its length.
FENCE_MARK_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def split_draft(reply: str) -> tuple[str | None, str, str | None]:
    """A spec-writer's reply as (preamble, draft, questions). The draft runs from the first bare
    `---` line, its frontmatter's opening, up to the last bare `---` after the frontmatter's
    closing that sits outside a fenced block; the questions are what follows that line. A fence
    closes only on its own character, at least as long, so a `---` inside one is the draft's text.
    With no such line the draft runs to the end and there are no questions; with no frontmatter
    at all, the whole reply is the draft. Text before the frontmatter is the preamble, never the
    draft's. Nothing is re-joined: the draft is the reply's own characters."""
    lines = reply.splitlines(keepends=True)
    bare = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == "---"]
    if not bare:
        return None, reply, None
    start = bare[0]
    preamble = "".join(lines[:start]).strip() or None
    closing = next((i for i in bare if i > start), None)
    cut, fence = None, None
    for i in range(closing + 1 if closing is not None else len(lines), len(lines)):
        text = lines[i].rstrip("\r\n")
        m = FENCE_MARK_RE.match(text)
        if fence:
            if (
                m
                and m.group(1)[0] == fence[0]
                and len(m.group(1)) >= len(fence)
                and not m.group(2).strip()
            ):
                fence = None
        elif m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            fence = m.group(1)
        elif text == "---":
            cut = i
    if cut is None:
        return preamble, "".join(lines[start:]), None
    return preamble, "".join(lines[start:cut]), "".join(lines[cut + 1 :])


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


def land_mended(folder: Path, n: int) -> set[str]:
    """The roles `agent` has mended in landing round `n`, from the `<role> land-<n>` lines of
    `runs/mended`: a landing round's allowance, apart from every build round's (`mended()`)."""
    path = folder / MENDED
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    pairs = (line.partition(" ") for line in lines)
    return {role for role, _, rnd in pairs if rnd.strip() == f"land-{n}"}


def verdict_mend(folder: Path, state: dict, role: str | None) -> bool:
    """Whether `mend` for `role` resumes that agent's own session to answer in its shape: a
    reviewer whose reply in the last round holds its verdict after a preamble, the approver, or
    the verifier. A behaviour check owing evidence runs afresh instead."""
    if role in ("approver", "verifier"):
        return True
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
    """The prompt a task sends, the file its reply goes to (for the spec draft `runs/spec-draft.md`,
    never `spec.md`, which waits for the person's yes), and whether the reply is added to that
    file: or why it can't run now.
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
        return f"Revise your draft, as the person asks: {words}", folder / SPEC_DRAFT, False
    if task == "spec" and recheck:
        return RECHECK, folder / SPEC_DRAFT, False
    upgrade = state.get("upgraded")
    if task == "spec":
        prompt = head + "Draft spec.md for this change."
        if upgrade and state["next"] == "spec":
            prompt += (
                f" It was upgraded from Tier 1 to Tier 2 before round {upgrade['round']}, on the "
                f"person's answer to {upgrade['decision']} ({upgrade['question']}): "
                f"{upgrade['answer']}. The build so far, up to round {upgrade['round'] - 1}, is in "
                "the worktree: specify the whole change, what is built included."
            )
        return prompt, folder / SPEC_DRAFT, False
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
    if task == "build" and upgrade and rnd == upgrade["round"]:
        # The builder resumed, its context kept: told the answer, the spec, and to replan first.
        prompt = head + (
            f"{upgrade['decision']} is decided in decisions.md: {upgrade['answer']}. So this "
            f"change is now Tier 2, upgraded before round {rnd}, and {rel}/spec.md is its approved "
            f"spec. Rewrite {rel}/plan.md against it first, keeping what still holds of your plan "
            f"so far, then build round {rnd} to the spec, test first. Every other ticked line in "
            "decisions.md is settled: build on it."
        )
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
        if upgrade and rnd == upgrade["round"]:
            prompt += (
                f" This change was upgraded from Tier 1 to Tier 2 before this round "
                f"({upgrade['decision']}): review it against spec.md."
            )
        before = [r for r in state["rounds"] if r["round"] < rnd and role in r["reviews"]]
        if before and state["reworked"] is not None:
            prev = next((r for r in state["rounds"] if r["round"] == rnd - 1), None)
            kept = (prev or {}).get("verified") or {"kept": []}
            prompt += (
                f" Reworked: {', '.join(state['reworked']) or 'nothing'}. Kept last round: "
                f"{'; '.join(k['role'] + ': ' + k['change'] for k in kept['kept']) or 'none'}. "
                f"Settled, never raise again: {'; '.join(state['settled']) or 'none'}."
            )
        handed = [h["text"] for h in state.get("handed") or [] if h["role"] == role]
        if handed:
            prompt += (
                f" Nits handed to the builder last round: {'; '.join(handed)}; raise again, word "
                "for word with its weights, any the rework didn't make."
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
        prompt = (
            f"Round {rnd}'s changes are verified in {rel}/reviews/round-{rnd}/{VERIFIED}. Address "
            "every KEPT line, then report. The kept changes, in the reviewers' words:\n"
            + "\n".join(f"- {k['role']}: {k['change']}" for k in kept)
        )
        if state.get("handed"):
            prompt += "\nAlso make these nits, each weighed cheap and worth it:\n" + "\n".join(
                f"- {h['role']}: {h['text']}" for h in state["handed"]
            )
        return prompt, folder / "build" / f"round-{rnd + 1}.md", False
    if task == "approve":
        prompt = head + "Decide."
        if upgrade:
            prompt += (
                f" This change was upgraded from Tier 1 to Tier 2 before round {upgrade['round']}, "
                f"on the person's answer to {upgrade['decision']}: judge it against spec.md."
            )
        if state["exhausted"]:
            prompt += (
                " The rounds ran out with changes still kept: say whether the approach should "
                "be reconsidered."
            )
        prompt += (
            " For each unticked `- [ ]` item in notes.md, propose its disposition at landing: "
            "`- UNDONE: <the item's text, exactly> → seed: <a short title>` or `→ dropped: "
            "<why>`; an item starting `pre-existing:` may instead be filed as a bug, "
            "`→ bug: <severity>: <path>[, <path>…]: <title>`, its severity one of the words in "
            "the Bugs section of the repo's process doc (`[docs] process`, else the plugin's "
            "guide), never guessed: with no word that fits, carry it as a seed."
        )
        base = _base(root)
        touched = risk_paths(_changed_paths(root, base), _irreversible(root, base)) if base else []
        if touched:
            prompt += (
                f" The diff touches irreversible paths ([review] irreversible on {base}): "
                f"{', '.join(touched)}. A revert won't undo what they reach: for each, or each "
                "group, one `- RECOVER: <path or glob>: <the way back>` line, its command or "
                "`fix forward:` and what the follow-up would do."
            )
        return prompt, folder / "decision.md", False
    reviewed = state["rounds"][-1]["round"] if state["rounds"] else 0
    if task == "decided":
        upgrading = state.get("upgrading") or (upgrade or {}).get("decision")
        if decided == upgrading:
            return (
                f"{decided} upgraded the change: `upgrade`, the spec and the builder's round "
                f"{(upgrade or {}).get('round') or 'P'} answer it, never `decided`"
            )
        if state["next"] in ("upgrade", "spec") or (
            upgrade and state["next"] == "build" and rnd == upgrade["round"]
        ):
            return (
                f"verdicts says {state['next']!r}: the upgrade comes first, and the builder it "
                "resumes is told every decided line"
            )
        entry = next((d for d in read_ledger(folder) if d["id"] == decided), None)
        if entry is None or not entry["decided"]:
            return f"{decided} isn't a decided line in decisions.md"
        prompt = f"{decided} is decided in decisions.md: {entry['answer']}. Continue."
        if not entry["source"].startswith("builder"):
            prompt += f" Round {reviewed}'s reviews are in {rel}/reviews/round-{reviewed}/."
        target = folder / "build" / f"round-{reviewed + 1}.md"
        return prompt, target, target.is_file() and state["built"] == reviewed + 1
    # mend: the stops a run mends itself, once each: a reviewer resumed to put its verdict first,
    # the approver its decision, the verifier resumed to answer in its shape, the builder resumed
    # for its evidence, or a new behaviour check for its own.
    if role == "approver":
        return DECISION_MEND, folder / "decision.md", False
    if role == "verifier":
        where = f"reviews/round-{reviewed}/{VERIFIED}"
        found = [p for p in state["problems"] if p.startswith(where)]
        return (
            VERIFY_MEND.format(problems="; ".join(found)),
            folder / "reviews" / f"round-{reviewed}" / VERIFIED,
            False,
        )
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
    return (
        f"only the builder and {', '.join(RUNS_THE_CHANGE)} owe evidence; a reviewer, the approver "
        "and the verifier are mended to answer in their shape"
    )


def _land_task(root: Path, folder: Path, task: str, role: str) -> tuple[str, Path, bool] | str:
    """The landing's prompts: the builder, resumed, resolving the files a rebase left conflicted,
    or making the fix the person asked for at landing (`build/land-<n>.ask.md`); a reviewer
    reading the change's diff from the commit the round rebased it onto (`_land_diff()`); the
    verifier on what they asked for, against that diff. Each reply goes under
    `reviews/land-<n>/`, the builder's to `build/land-<n>.md`."""
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
        prompt = (
            f"The base branch moved under this change, and rebasing onto it conflicts in: "
            f"{', '.join(files)}. Resolve each, keeping what both sides meant; edit only those "
            "files, run no git command, then report what you kept from each side, ending with "
            "## Evidence."
        )
        if INBOX.as_posix() in files:
            text = (folder / "intent.md").read_text(encoding="utf-8")
            ids = [*frontmatter_ids(text, "idea"), *frontmatter_ids(text, "fixes")]
            gone = [*ids, *named_nits(root, folder)]
            if gone:
                prompt += (
                    f" The landing deleted {', '.join(dict.fromkeys(gone))} from "
                    f"{INBOX.as_posix()}, and they stay deleted: don't keep them."
                )
        return (
            prompt,
            folder / "build" / f"land-{n}.md",
            False,
        )
    ask = land_ask(folder, n)
    if task == "land-fix":
        if ask is None:
            return f"no fix was asked for in landing round {n}: run land-fix --ask first"
        return (
            head + f"The person asked for a fix while landing this change: {ask} Make it, editing "
            "only what the fix needs; run no git command, then report what you changed, ending "
            "with ## Evidence.",
            folder / "build" / f"land-{n}.md",
            False,
        )
    if task == "land-mend":
        cfg, _ = load_config(root)
        state = land_verdict(root, folder, cfg, n)
        if state["next"] != "mend" or role not in state.get("mend", []):
            return f"land-verdicts says {state['next']!r}, not a mend for {role}"
        if role == "verifier":
            gone = [p for p in state["problems"] if p.startswith(f"reviews/land-{n}/{VERIFIED}")]
            return VERIFY_MEND.format(problems="; ".join(gone)), where / VERIFIED, False
        if preamble(where / f"{role}.md"):
            return VERDICT_MEND, where / f"{role}.md", False
        planned = _land_task(root, folder, "land-review", role)
        if isinstance(planned, str):
            return planned
        return planned[0] + " " + MEND, planned[1], False
    if task == "land-review":
        if role not in REVIEWERS:
            return f"land-review needs --role, one of {', '.join(REVIEWERS)}"
        resolved = (folder / "runs" / "land-resolved").is_file()
        why = (
            f"its conflicts resolved by the builder, in build/land-{n}.md"
            if resolved
            else ("with no conflict")
        )
        what = f"the change was rebased onto {base}, {why}"
        if ask is not None:
            what = (
                f"the builder made a fix the person asked for while landing, in build/land-{n}.md. "
                f"The person asked: {ask}"
            )
        if (diff := _land_diff(root, base)) is None:
            return _NO_FORK.format(base=base)
        return (
            head + f"Review landing round {n}: {what}. Review its whole diff: " + diff,
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
    if (diff := _land_diff(root, base)) is None:
        return _NO_FORK.format(base=base)
    return (
        head + f"Verify landing round {n} against its diff: {diff}\n" + "\n".join(asked),
        where / VERIFIED,
        False,
    )


_NO_FORK = "no fork point between {base} and HEAD: the landing can't be reviewed"


def _land_diff(root: Path, base: str) -> str | None:
    """The diff a landing round's reviewers and verifier read: from the commit the round rebased
    the change onto, `HEAD`'s merge base with the base branch, which a later move of the branch
    leaves where it is (the amend that adds the landing's record keeps `HEAD`'s parent). Never
    the branch's tip, where a commit that landed since reads as one the change deleted: None when
    there is no merge base, for the caller to refuse (`_NO_FORK`)."""
    fork = _git(root, "merge-base", base, "HEAD")
    if not fork:
        return None
    return (
        f"`git diff {fork}...HEAD`, from the commit this round rebased the change onto. {base} "
        "may have moved since: a commit on it that isn't in that diff is not the change's, and a "
        "move is the script's to catch before the close, never a finding."
    )


def _file_draft(root: Path, folder: Path, reply: str) -> dict:
    """Write a spec-writer's reply as `runs/spec-draft.md` and `runs/spec-questions.md`, each over
    the last draft's, and say where: `questions` is None, and its old file gone, when the reply
    has no separator, so a revision never shows the questions of the draft before it."""
    preamble, draft, questions = split_draft(reply)
    path = folder / SPEC_QUESTIONS
    for text, to in ((draft, folder / SPEC_DRAFT), (questions, path)):
        if text is None:
            to.unlink(missing_ok=True)
        else:
            end = "" if text.endswith("\n") else "\n"
            to.write_text(text + end, encoding="utf-8", newline="\n")
    shown = path.relative_to(root).as_posix() if questions is not None else None
    return {"questions": shown, "preamble": preamble}


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
    if task == "land-mend" and role is None:
        why = "land-mend needs --role: one `land-verdicts` names in `mend`"
        return emit({"refusals": [why]}, 1)
    if task == "mend" and role is None:
        why = "mend needs --role: one `verdicts` names in `mend`"
        return emit({"refusals": [why]}, 1)
    if task == "mend" and (role, mend_round(state, role)) in mended(folder):
        why = f"{role} was mended once in round {mend_round(state, role)}: a second is a stop"
        return emit({"refusals": [why]}, 1)
    # A mend answers the stop `verdicts` names, for a role it names: never a landing round's
    # reply, which `land-mend` mends under `reviews/land-<n>/`.
    if task == "mend" and not (
        state["next"] == "stop" and state.get("way") == "mend" and role in state["mend"]
    ):
        return emit({"refusals": [f"verdicts says {state['next']!r}, not a mend for {role}"]}, 1)
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
        paths, record = shots(root, folder, label, cfg["ui"], role)
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
    # An upgraded run's first build carries on the builder that raised the upgrade.
    upgrade = state.get("upgraded")
    at_p = bool(upgrade) and state["next"] == "build" and state["round"] == upgrade["round"]
    resumed = resumed or (task == "build" and at_p)
    resumed = resumed or bool(task == "land-mend" and (role == "verifier" or preamble(target)))
    if resumed:
        ids = sessions.read_text(encoding="utf-8").split() if sessions.is_file() else []
        if not ids:
            first = {"builder": "build", "spec-writer": "spec", "approver": "approve",
                     "verifier": "verify"}.get(role, "review")  # fmt: skip
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
    target.parent.mkdir(parents=True, exist_ok=True)
    if task == "spec":
        return emit({**out, **_file_draft(root, folder, reply)})
    text = reply if reply.endswith("\n") else reply + "\n"
    if append:
        before = target.read_text(encoding="utf-8")
        text = before + ("" if before.endswith("\n") else "\n") + "\n" + text
    target.write_text(text, encoding="utf-8", newline="\n")
    if task in ("mend", "land-mend"):
        rnd = mend_round(state, role) if task == "mend" else f"land-{land_round(folder)}"
        with (folder / MENDED).open("a", encoding="utf-8", newline="\n") as f:
            f.write(f"{role} {rnd}\n")
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
# What the approver proposes for each undone notes.md item, and for each irreversible path the
# diff touches: read by land-check, which shows them, and by land, which writes them. A
# `pre-existing:` item may be proposed as a bug, `→ bug: <severity>: <path>[, <path>…]: <title>`.
UNDONE_RE = re.compile(r"^\s*- UNDONE:\s*(.+?)\s+→\s+(seed|dropped|bug):\s*(.+?)\s*$")
BUG_PROPOSAL_RE = re.compile(r"^([^\s:]+):\s*(.*?):\s+(.+)$")
PREEXISTING_ITEM = "pre-existing:"
RECOVER_RE = re.compile(r"^\s*- RECOVER:\s*(.+?):\s+(.+?)\s*$")
# A notes.md item a landing (or ship) gave its disposition, as `land_message()` reads it back.
# An unticked note, as `sdlc.py`'s `OPEN_ITEM_RE` reads one.
OPEN_NOTE_RE = re.compile(r"^\s*[-*] \[ \] (.+?)\s*$")
TICKED_RE = re.compile(r"^\s*[-*] \[x\] (.+?) → (seed|dropped|bug): (.+?)\s*$")
# findings.md's note lines ship reads, and the cost ceiling of a change's run of the skills'
# cases: copies of `sdlc.py`'s `FRESH_RE`, `CASES_RE` and `CASE_CAP["change"]`, pinned by a test.
FRESH_RE = re.compile(r"^>?\s*Fresh review:\s*(ran|skipped)\b,?\s*(.*)$")
CASES_RE = re.compile(r"^>?\s*Skill evals:\s*(ran|skipped)\b,?\s*(.*)$")
CASE_CAP_USD = 5
CONFIRMED = "the assumed default, confirmed when landing"


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


def cmd_fresh(root: Path, ident: str) -> int:
    """Bring change `ident`'s branch up to date with the base branch before a run starts, through
    `sdlc.py base` of this factory's own version, and `sdlc.py resolve` when `base` refuses on a
    conflict it can take on: so `base`'s and `resolve`'s rules (only the change's own branch
    moves; never a stash, a merge of the base or a force) stay in one implementation. Its `state`:
    `current`, `fast-forwarded`, `rebased` or `resolved`, each with the `undo`; `held` for a run
    that stopped part way, whose rounds were gated and reviewed on the base they had; or `refused`,
    with why, the worktree as `fresh` found it. A real conflict is aborted (`resolve --abort`),
    left for the person: no agent runs before the run's yes."""
    out: dict = {"change": None, "state": "refused", **behind_base(root), "from": None}
    out.update(head=None, undo=None, refusals=[])
    out["from"] = out["head"] = _git(root, "rev-parse", "--short", "HEAD")

    def refuse(why: str) -> int:
        out["refusals"].append(why)
        out["head"] = _git(root, "rev-parse", "--short", "HEAD")
        return emit(out, 1)

    folder, refusal = find_change(root, ident)
    if refusal:
        return refuse(refusal)
    out["change"] = folder.name
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    tier = int(meta["tier"]) if meta.get("tier", "").isdigit() else None
    stage = meta.get("stage") or None
    if any(UPGRADED_FILE_RE.match(p.name) for p in (folder / "build").glob("round-*.upgraded.md")):
        out.update(state="held", reason=(
            f"{folder.name} was upgraded to Tier 2 part way through its run: its rounds so far "
            "were gated and reviewed on the base they had, so it carries on there, and landing "
            "rebases and gates it again"
        ))  # fmt: skip
        return emit(out)
    if stage == "build":
        out.update(state="held", reason=(
            f"{folder.name} stopped part way at stage: build: its rounds were gated and reviewed "
            "on the base they had, so it resumes there, and landing rebases and gates it again"
        ))  # fmt: skip
        return emit(out)
    if stage == "test" and tier in (1, 2):
        restart, why = restart_state(folder)
        if restart is None:
            return refuse(why)
    elif (tier, stage) not in STARTS["build"]:
        allowed = " or ".join(f"tier {t} at stage: {s}" for t, s in sorted(STARTS["build"]))
        here = f"{folder.name} is tier {tier} at stage: {stage}"
        return refuse(f"build starts from {allowed}; {here}")
    _, based, said = _sdlc(["base", folder.name], root)
    action = (based or {}).get("action")
    if based is None:
        return refuse(f"sdlc.py base didn't run: {said.strip()[-500:]}")
    if action in ("current", "fast-forwarded", "rebased"):
        out.update(state=action, undo=based.get("undo"))
        out["head"] = _git(root, "rev-parse", "--short", "HEAD")
        return emit(out)
    reason = str(based.get("reason") or said).strip()
    if not based.get("resolvable"):
        return refuse(f"sdlc.py base refused: {reason[-500:]}")
    _, resolved, said = _sdlc(["resolve", folder.name], root)
    state = (resolved or {}).get("state")
    if state in ("clean", "current"):
        out.update(state="resolved", undo=resolved.get("undo"))
        out["head"] = _git(root, "rev-parse", "--short", "HEAD")
        return emit(out)
    if state != "conflict":
        why = (resolved or {}).get("reason") or said
        return refuse(f"sdlc.py resolve refused: {str(why).strip()[-500:]}")
    files = ", ".join(resolved.get("conflicted") or [])
    way = (
        f"{folder.name} conflicts with {out['base']} in {files}: left as it was, for the person to "
        "resolve with /sdlc:ship from its worktree, or sdlc.py resolve"
    )
    _, aborted, said = _sdlc(["resolve", folder.name, "--abort"], root)
    if (aborted or {}).get("state") != "aborted":
        why = (aborted or {}).get("reason") or said
        undo = resolved.get("undo")
        return refuse(f"{way}; resolve --abort refused ({str(why).strip()[-300:]}): undo: {undo}")
    return refuse(way)


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


def resolved_files(folder: Path) -> list[str]:
    """Every file the change's `conflicts.md` says `sdlc.py resolve` merged, each once, in order:
    a copy of `sdlc.py`'s `conflicts_resolved()`, pinned to it by `tests/test_land.py`."""
    record = folder / "conflicts.md"
    lines = record.read_text(encoding="utf-8").splitlines() if record.is_file() else []
    return list(dict.fromkeys(ln[2:].strip() for ln in lines if ln.startswith("- ")))


LANDED_ROUND_RE = re.compile(r"^land-(\d+)$")
LANDING_RESOLVED = "a conflict was resolved while landing"
# A fix the person asked for at landing: new behaviour, a signal for the rest of the change's life.
LANDING_FIXED = "a fix was made while landing"


# The person's words for a fix asked at landing: a ticked line the land skill writes at the end of
# `decisions.md`, after the yes, whose id alone `land-fix --ask` takes. Never a shell argument,
# where a quote or `$(` in the words breaks the command or runs. The ledger reads past it.
FIX_WORDS_RE = re.compile(r"^- \[x\] (R\d+) \(person, fix\): (.+?)\s*$")


def read_fix_words(folder: Path, ident: str) -> str | None:
    """The person's words for fix `ident` (`R3`) in `decisions.md`, or None."""
    path = folder / "decisions.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        m = FIX_WORDS_RE.match(line)
        if m and m.group(1) == ident:
            return m.group(2)
    return None


def land_ask_path(folder: Path, n: int) -> Path:
    """The person's words for a fix asked at landing, round `n`: beside the builder's reports,
    never under `reviews/land-<n>/`, whose every file the landing reads as a review."""
    return folder / "build" / f"land-{n}.ask.md"


def land_ask(folder: Path, n: int) -> str | None:
    """The fix the person asked for in landing round `n`, or None when the round has none."""
    path = land_ask_path(folder, n)
    return path.read_text(encoding="utf-8").strip() if n and path.is_file() else None


def resolution_signals(root: Path, folder: Path, cfg: dict) -> list[str]:
    """A resolved conflict no reviewer has seen, as a signal: one made while landing until
    `land_verdict()` for the round its marker names (`runs/land-resolved`'s first line) says
    `pass`, a pass that stands when the landing's own record or a later rebase moves `HEAD`
    (`settled`), and always for a marker naming no round, written before the round was. And one
    `sdlc.py resolve` recorded in `conflicts.md` while any file it names hashes otherwise than
    in the newest complete build round's snapshot, whose reviewers read exactly that content, or
    always with no such round or snapshot. Content, never file times, which a checkout resets."""
    signals = []
    files = resolved_files(folder)
    if files:
        rounds, _, _ = _rounds_at_depth(root, folder, cfg)
        done = [r["round"] for r in rounds if r["complete"]]
        snap = read_snapshot(folder, done[-1]) if done else None
        base = _base(root)
        if snap is None or base is None:
            unseen = files
        else:
            now = _tree_hashes(root, base)
            unseen = [f for f in files if now.get(f) != snap.get(f)]
        if unseen:
            signals.append(
                "a conflict resolved by sdlc.py resolve after the last review round: "
                + ", ".join(unseen)
            )
    marker = folder / "runs" / "land-resolved"
    if marker.is_file():
        lines = marker.read_text(encoding="utf-8").splitlines()
        m = LANDED_ROUND_RE.match(lines[0].strip()) if lines else None
        n = int(m.group(1)) if m else 0
        if not n or land_verdict(root, folder, cfg, n, settled=True)["next"] != "pass":
            signals.append(LANDING_RESOLVED)
    return signals


def _preflight(folder: Path, worktree: Path) -> tuple[dict | None, str]:
    """`sdlc.py preflight` on the change, from its worktree: its JSON, or None and what it said."""
    _, pre, out = _sdlc(["preflight", folder.name], worktree)
    return pre, out


def read_proposals(folder: Path) -> tuple[dict[str, tuple], list[tuple[str, str]]]:
    """What the approver proposed in `decision.md`: each undone item's disposition by its exact
    text, as (`seed`, title), (`dropped`, reason) or (`bug`, severity, paths, title), a bug line
    that doesn't read as one with no severity and no paths, and each `- RECOVER:` line as (the
    path or group it covers, the way back)."""
    path = folder / "decision.md"
    undone, recover = {}, []
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        if (m := UNDONE_RE.match(line)) and m.group(2) == "bug":
            b = BUG_PROPOSAL_RE.match(m.group(3))
            paths = [p.strip().strip("`") for p in b.group(2).split(",") if p.strip()] if b else []
            undone.setdefault(
                m.group(1), ("bug", b.group(1), paths, b.group(3)) if b else ("bug", "", [], "")
            )
        elif m:
            undone.setdefault(m.group(1), (m.group(2), m.group(3)))
        elif m := RECOVER_RE.match(line):
            recover.append((m.group(1), m.group(2)))
    return undone, recover


def bad_bugs(undone: list[dict], words: list[str]) -> list[str]:
    """Why each bug the approver proposed can't be filed as it stands: an item not starting
    `pre-existing:`, no paths, or a severity outside `words`, the process doc's (any word when it
    names none). The script never guesses one: such a change is left for `/sdlc:ship`."""
    out = []
    for u in undone:
        if "bug" not in u:
            continue
        bug, item = u["bug"], u["text"]
        if not item.startswith(PREEXISTING_ITEM):
            out.append(f"a bug proposed for {item!r}, which isn't a {PREEXISTING_ITEM} item")
        elif not bug["paths"]:
            out.append(f"a bug proposed for {item!r} names no paths")
        elif not bug["severity"] or (words and bug["severity"] not in words):
            out.append(f"a bug proposed for {item!r} is {bug['severity'] or 'without a severity'}"
                       + (f", not one of {', '.join(words)}" if words else ""))  # fmt: skip
    return out


def severity_words(worktree: Path) -> tuple[list[str] | None, str]:
    """The process doc's severity words, from `sdlc.py bugs`'s `severities`, or None and what it
    said when it can't be read."""
    _, data, said = _sdlc(["bugs"], worktree)
    words = (data or {}).get("severities")
    return (words, "") if isinstance(words, list) else (None, said)


def unrecovered(paths: list[str], recover: list[tuple[str, str]]) -> list[str]:
    """The irreversible `paths` no `- RECOVER:` line covers: one names it, or a pattern of it (a
    directory ending in `/`, or a glob), alone or in a comma-separated list."""
    named = [s.strip().strip("`") for subject, _ in recover for s in subject.split(",")]
    return [p for p in paths if p not in named and not risk_paths([p], named)]


def note_items(folder: Path) -> dict[int, str]:
    """Each `- [ ]` note of `notes.md` by its line number, as `sdlc.py preflight` numbers them, with
    its whole text: the line's own, then each indented, non-blank line after it, up to the first
    that isn't, joined with single spaces. A fenced example is never a note."""
    path = folder / "notes.md"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    found, fenced = {}, False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        m = None if fenced else OPEN_NOTE_RE.match(line)
        if not m:
            continue
        words = [m.group(1)]
        for more in lines[i + 1 :]:
            if not more.strip() or not more[:1].isspace() or OPEN_NOTE_RE.match(more):
                break
            words.append(more.strip())
        found[i + 1] = " ".join(" ".join(words).split())
    return found


def first_sentence(text: str) -> str:
    """`text`'s first sentence, up to a `.`, `!` or `?` and a space; all of it without one."""
    return re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0] if text else ""


def nit_findings(root: Path, folder: Path, cfg: dict) -> list[dict]:
    """The agents' findings of change `folder`, as `carry` writes them (`agent_findings()` of the
    rounds at the run's depth): the one reading the landing files nits from."""
    return agent_findings(_rounds_at_depth(root, folder, cfg)[0])


def land_parts(folder: Path, pre: dict, root: Path | None = None, cfg: dict | None = None) -> dict:
    """What the batch's yes approves for change `folder`, each part empty when it has none: its
    acceptance checks, its skills' cases with the cap, its undone notes, each with its whole text
    (`note_items()`) and the disposition the approver proposed for its first line or its whole
    text (a seed titled by the note's first sentence when none was; a bug with what the question
    shows of it), its assumed decisions, the `How to recover:` lines its commit will carry, and,
    read from its worktree `root` with `cfg`, the agents' nits to file as `[nit]` entries
    (`nit_findings()`'s `file`, with the line the question shows of each)."""
    proposed, recover = read_proposals(folder)
    notes = note_items(folder)
    undone = []
    for item in (pre.get("undone") or {}).get("items") or []:
        full = notes.get(item["line"], item["text"])
        kind, *said = (
            proposed.get(full) or proposed.get(item["text"]) or ("seed", first_sentence(full))
        )
        part = {"line": item["line"], "text": full}
        if kind == "bug":
            severity, paths, title = said
            part["bug"] = {"severity": severity, "paths": paths, "title": title}
            part["shown"] = f"filed as a bug, {severity}: {title} ({', '.join(paths)})"
        else:
            part["seed" if kind == "seed" else "dropped"] = said[0]
        undone.append(part)
    scope = (pre.get("cases") or {}).get("scope") or []
    found = nit_findings(root, folder, cfg) if root is not None and cfg is not None else []
    nits = [
        {**n, "shown": f"[nit] {n['title']} ({n['theme']}, {n['cost']}, {n['value']}; "
                       f"{', '.join(n['paths'])})"}
        for n in (i["file"] for i in found) if n
    ]  # fmt: skip
    return {
        "checks": [{"name": c["name"], "command": c["command"]}
                   for c in (pre.get("checks") or {}).get("checks") or []],
        "cases": {"scope": scope, "cap_usd": CASE_CAP_USD} if scope else {},
        "undone": undone,
        "assumed": [{"id": d["id"], "text": d["text"]} for d in read_ledger(folder)
                    if not d["decided"] and d["kind"] == "default"],
        "recover": [f"{subject}: {way}" for subject, way in recover],
        "nits": nits,
    }  # fmt: skip


def land_unreviewed(root: Path, folder: Path, cfg: dict) -> list[str] | None:
    """The paths the change touches that hash otherwise than in the newest complete build round's
    snapshot, whose reviewers read exactly that content: changed since its last review, by hand or
    by `sdlc.py resolve`. A path absent from both is unchanged, and the change folders never count
    (`_changed_paths()`). None with no complete round, no snapshot of it, or no base branch."""
    rounds, _, _ = _rounds_at_depth(root, folder, cfg)
    done = [r["round"] for r in rounds if r["complete"]]
    snap = read_snapshot(folder, done[-1]) if done else None
    base = _base(root)
    if snap is None or base is None:
        return None
    now = _tree_hashes(root, base)
    return sorted(p for p in set(now) | set(snap) if now.get(p) != snap.get(p))


UNREVIEWED_UNKNOWN = "no snapshot of its last review"


def land_signals(
    folder: Path,
    worktree: Path,
    decision: str,
    cfg: dict,
    pre: dict | None = None,
    unreviewed: list[str] | None = (),
) -> tuple[list, list]:
    """Why change `folder` needs the person at the batch's gate (`signals`), and why it can't land
    in a batch at all, only by hand (`excluded`): what `sdlc.py preflight` reads of its risk, its
    notes, its checks, its skills' cases and its issues, and what the run left in its folder,
    a resolved conflict no reviewer has seen among it (`resolution_signals()`). The exclusions
    are an irreversible path the approver proposed no way back for, and a bug it proposed that
    `bad_bugs()` refuses. A nit to file is a signal, so no agent's nit is filed without the
    person's yes. `unreviewed` is
    `land_unreviewed()` as the caller read it at `stage: test`: paths, or None for no snapshot."""
    signals, excluded = [], []
    if pre is None:
        pre, out = _preflight(folder, worktree)
        if pre is None:
            return [f"preflight couldn't be read: {out.strip()[-300:]}"], []
    risk = pre.get("risk") or {}
    if risk.get("sensitive"):
        signals.append(f"touches sensitive paths: {', '.join(risk['sensitive'][:5])}")
    if risk.get("irreversible"):
        signals.append(f"touches irreversible paths: {', '.join(risk['irreversible'][:5])}")
        missing = unrecovered(risk["irreversible"], read_proposals(folder)[1])
        if missing:
            excluded.append(
                f"decision.md proposes no How to recover for {', '.join(missing[:5])}: "
                "ship it by hand"
            )
    parts = land_parts(folder, pre, worktree, cfg)
    undone = parts["undone"]
    if any("bug" in u for u in undone):
        words, said = severity_words(worktree)
        if words is None:
            excluded.append(f"sdlc.py bugs couldn't be read: {said.strip()[-300:]}")
        else:
            excluded += [f"{why}: ship it by hand" for why in bad_bugs(undone, words)]
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
    if [d for d in ledger if d["open"]]:
        signals.append("decisions still open or assumed in decisions.md")
    assumed = [d["id"] for d in ledger if not d["decided"] and d["kind"] == "default"]
    if assumed:
        signals.append(f"assumed decisions to confirm: {', '.join(assumed)}")
    signals += resolution_signals(worktree, folder, cfg)
    if list(folder.glob("build/land-*.ask.md")):
        signals.append(LANDING_FIXED)
    if unreviewed is None:
        signals.append(UNREVIEWED_UNKNOWN)
    elif unreviewed:
        signals.append(f"changed since its last review: {', '.join(unreviewed)}")
    if not cfg["land"]["auto"]:
        signals.append("land.auto is off on the base branch")
    if n := len((pre.get("undone") or {}).get("items") or []):
        signals.append(f"undone notes to dispose of: {n}")
    if n := len((pre.get("checks") or {}).get("checks") or []):
        signals.append(f"acceptance checks to run: {n}")
    if n := len((pre.get("cases") or {}).get("scope") or []):
        signals.append(f"skills' cases in scope: {n}")
    if n := len(parts["nits"]):
        past = sum(i["reason"] == CAP_REASON for i in nit_findings(worktree, folder, cfg))
        signals.append(
            f"nits to file: {n}" + (f", {past} past the cap of {NIT_CAP}" if past else "")
        )
    return signals, excluded


def land_question(batch: list[dict], base: str, moves: int = DEFAULTS["land"]["moves"]) -> str:
    """The batch's question, worded here so the skill never words its own: a clause for the checks
    and cases, for the dispositions and confirmations, for the agents' nits to file, and for `How
    to recover:`, each only when some change in the batch has one, and the cases' total ceiling,
    the cap per change with any; the most times the landing follows `base` moving
    (`land.moves`); and its four answers, `yes, with a fix` among them."""
    n = len(batch)
    names = ", ".join(c["change"] for c in batch)
    parts = ["each shipped with its approver's impact"]
    checks = any(c["checks"] for c in batch)
    with_cases = sum(1 for c in batch if c["cases"])
    runs = [w for w, has in (("acceptance checks", checks), ("skills' cases", with_cases)) if has]
    if runs:
        ceiling = f" (at most ${CASE_CAP_USD * with_cases})" if with_cases else ""
        parts.append(f"its {' and '.join(runs)} run as shown{ceiling}")
    undone = any(c["undone"] for c in batch)
    assumed = any(c["assumed"] for c in batch)
    bugs = any("bug" in u for c in batch for u in c["undone"])
    notes = ("its undone notes carried, filed as bugs or dropped" if bugs
             else "its undone notes carried or dropped")  # fmt: skip
    if undone and assumed:
        parts.append(f"{notes} and its assumed decisions confirmed as shown")
    elif undone:
        parts.append(f"{notes} as shown")
    elif assumed:
        parts.append("its assumed decisions confirmed as shown")
    if any(c.get("nits") for c in batch):
        parts.append("its agents' nits filed as shown")
    if any(c["recover"] for c in batch):
        parts.append("with how to recover shown")
    return (
        f"Land {n} change{'s' if n != 1 else ''} in this order, {names}, {', '.join(parts)}, "
        f"committed, brought up to date with {base} as often as it moves while landing, up to "
        f"{moves} times (a conflict resolved by its builder and reviewed again), and closed, "
        "pushed as git.push says? (yes / yes, with a fix / leave one out / no)"
    )


def cmd_land_check(root: Path, idents: list[str]) -> int:
    """The batch: the ready changes in `ready`'s order (or those named), at most `land.batch`, each
    with its signals, what the yes approves for it (`land_parts()`) and why any is left out, the
    question to ask (`land_question()`), and `clear`: true when no change in it has a signal, so
    the gate passes itself. Read-only."""
    cfg, warnings = load_config(root)
    picked = [
        r for r in ready(root) if not idents or any(names_change(r["change"], i) for i in idents)
    ]
    batch, left_out, over = [], [], []
    for r in picked:
        worktree = Path(r["worktree"])
        folder = worktree / work_rel(worktree) / r["change"]
        pre, said = _preflight(folder, worktree)
        unreviewed = _unreviewed_at_test(worktree, folder, cfg)
        signals, excluded = land_signals(
            folder, worktree, r["decision"], cfg, pre or {}, unreviewed=unreviewed
        )
        if pre is None:
            signals = [f"preflight couldn't be read: {said.strip()[-300:]}"]
        entry = {
            "change": r["change"], "worktree": r["worktree"], "decision": r["decision"],
            "impact": read_impact(folder), "signals": signals, "overlaps": r["overlaps"],
            **land_parts(folder, pre or {}, worktree, cfg),
        }  # fmt: skip
        if excluded:
            left_out.append({**entry, "excluded": excluded})
        elif len(batch) >= cfg["land"]["batch"]:
            over.append(r["change"])
        else:
            batch.append(entry)
    clear = bool(batch) and not any(c["signals"] for c in batch)
    base = _base(root) or "the base branch"
    question = land_question(batch, base, cfg["land"]["moves"]) if batch else None
    return emit({
        "batch": batch, "excluded": left_out, "over_limit": over, "clear": clear,
        "question": question, "auto": cfg["land"]["auto"], "limit": cfg["land"]["batch"],
        "warnings": warnings,
    })  # fmt: skip


# Where a change names the nits it takes in, as `/sdlc:intent` and `/sdlc:spec` write them: an id
# anywhere else (a Problem citing what an earlier change took in) is never taken in.
NIT_SECTIONS = (("intent.md", "## Approach"), ("spec.md", "## Requirements"))


def _section(text: str, heading: str) -> str:
    """The lines under `heading` in `text`, up to the next `## ` heading; empty when it has none."""
    found, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.rstrip() == heading
        elif inside:
            found.append(line)
    return "\n".join(found)


def named_nits(root: Path, folder: Path, text: str | None = None) -> list[str]:
    """The open `[nit]` entries of the checkout's register (or of the register `text`, as another
    commit holds it) that the change names by id in `NIT_SECTIONS`, in the register's order: each
    id matched whole, so `2026-11-17-1` is never named by `2026-11-17-11`. Never inferred from
    the diff."""
    named = "\n".join(
        _section((folder / f).read_text(encoding="utf-8"), heading)
        for f, heading in NIT_SECTIONS if (folder / f).is_file()
    )  # fmt: skip
    register = root / INBOX
    if text is None:
        text = register.read_text(encoding="utf-8") if register.is_file() else ""
    found, fenced = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
        elif not fenced and (m := NIT_RE.match(line)):
            found.append(m.group(1))
    return [i for i in found if re.search(rf"(?<![\w-]){re.escape(i)}(?![\w-])", named)]


def retire_nits(root: Path, ids: list[str]) -> None:
    """Delete each nit `ids` names from the checkout's register, as `/sdlc:ship` does: the
    change's commit carries the deletion."""
    drop_entries(root, ids)


# A register entry's heading, `## [<id>] [<tag>] <title>`, by its id; a heading at level one or
# two ends it, a deeper one is its own.
ENTRY_RE = re.compile(r"^##\s*\[(\d{4}-\d{2}-\d{2}-\d+)\]\s*\[[^\]]+\]")
ENTRY_END_RE = re.compile(r"^#{1,2}(?!#)")
ENTRY_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d+$")


def drop_entries(root: Path, ids: list[str]) -> list[str]:
    """Delete each entry `ids` names, by id alone, from the checkout's register, its heading up to
    the next heading outside a fence, every other line left byte for byte. The ids it deleted, in
    the register's order."""
    register = root / INBOX
    if not register.is_file():
        return []
    kept, gone, dropping, fenced = [], [], False, False
    for line in register.read_text(encoding="utf-8").splitlines(keepends=True):
        if FENCE_RE.match(line):
            fenced = not fenced
        elif not fenced and ENTRY_END_RE.match(line):
            m = ENTRY_RE.match(line)
            dropping = bool(m and m.group(1) in ids)
            if dropping:
                gone.append(m.group(1))
        if not dropping:
            kept.append(line)
    if gone:
        register.write_text("".join(kept), encoding="utf-8", newline="\n")
    return gone


def frontmatter_ids(text: str, key: str) -> list[str]:
    """The register ids an intent's `key:` names (`idea: 2026-11-17-6`, `fixes: [a, b]`), read as
    text: a value naming its seed by title is skipped, never matched."""
    value = frontmatter(text).get(key, "").strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    found = [v.strip().strip("'\"") for v in value.split(",")]
    return [v for v in found if ENTRY_ID_RE.match(v)]


def accept_path(folder: Path) -> Path:
    """The change's acceptance checks as the landing ran them: beside the landing's gate files."""
    return folder / "build" / "land-accept.md"


def accept_build(root: Path, folder: Path) -> str:
    """The build an accept attempt ran on: before the landing commits the change (`stage: test`),
    a digest of every path it touches outside its folder and of its `checks.md`, so the record,
    in the folder, never changes the identity it records; after, its commit (`landed_build()`)."""
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    if meta.get("stage") != "test":
        return landed_build(root)
    base = _base(root)
    digest = hashlib.sha256()
    for p, h in sorted((_tree_hashes(root, base) if base else {}).items()):
        digest.update(f"{h}  {p}\n".encode())
    checks = folder / "checks.md"
    digest.update(checks.read_bytes() if checks.is_file() else b"")
    return digest.hexdigest()[:16]


def _accept_state(root: Path, folder: Path, settled: bool = False) -> str | None:
    """The latest accept attempt's verdict when it ran on the build as it stands, else None.
    `settled` reads a landing round already reviewed, as `_land_gate_state()` does: its verdict
    stands whatever `HEAD` is now, which the landing's own record and later rebases move."""
    record = read_gate_file(accept_path(folder)) or {"attempts": []}
    last = record["attempts"][-1] if record["attempts"] else None
    ran_on = last and (settled or last["build"] == accept_build(root, folder))
    return last["verdict"] if ran_on else None


def cmd_accept(root: Path, ident: str) -> int:
    """Run change `ident`'s acceptance checks through `sdlc.py accept`, in its worktree, and add
    the attempt to `build/land-accept.md`, in the gate file's shape: never reading or running
    `checks.md` itself. No skill's rule grants it, so the harness asks before every run."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    build = accept_build(root, folder)
    code, found, said = _sdlc(["accept", folder.name], root)
    if found is None:
        why = f"sdlc.py accept: {said.strip()[-500:]}"
        return emit({"change": folder.name, "refusals": [why]}, 1)
    verdict = "PASS" if code == 0 and found.get("passed") else "FAIL"
    path = accept_path(folder)
    attempt = len((read_gate_file(path) or {"attempts": []})["attempts"]) + 1
    lines = []
    for check in found.get("checks") or []:
        mark = "passed" if check.get("passed") else "failed"
        left = f", left {', '.join(check['left'])}" if check.get("left") else ""
        lines.append(f"- {check.get('name')}: exit {check.get('exit')}, {mark}{left}\n")
        output = _placeholders(str(check.get("output") or ""), root).rstrip().splitlines()
        lines += [f"    {line}\n" for line in output[-GATE_TAIL:]] or ["    (no output)\n"]
    lines += [f"- problem: {_placeholders(str(w), root)}\n" for w in found.get("problems") or []]
    section = f"## Attempt {attempt}\n\nVerdict: {verdict}\nBuild: {build}\n\n" + (
        "".join(lines) or "- no checks\n"
    )
    # The first line is the latest verdict; the attempts before it stay as they were.
    earlier = path.read_text(encoding="utf-8").partition("\n")[2] if path.is_file() else ""
    earlier = earlier.rstrip("\n") + "\n" if earlier.strip() else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"ACCEPT: {verdict}\n{earlier}\n{section}", encoding="utf-8", newline="\n")
    out = {**found, "verdict": verdict, "attempt": attempt, "to": path.relative_to(root).as_posix()}
    return emit(out, 0 if verdict == "PASS" else 1)


def _note_says(folder: Path, line_re: re.Pattern) -> bool:
    """Whether `findings.md`'s note, before its first finding, holds a line `line_re` reads."""
    path = folder / "findings.md"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        if line.startswith("## "):
            break
        if line_re.match(line.strip()):
            return True
    return False


def _note_line(folder: Path, line_re: re.Pattern, line: str) -> None:
    """Set `line` in `findings.md`'s note, by line: in place of the one `line_re` reads, else after
    the note's last line, before the first finding. A missing file is started from
    `FINDINGS_HEAD`."""
    path = folder / "findings.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else FINDINGS_HEAD
    lines = text.splitlines()
    end = next((i for i, ln in enumerate(lines) if ln.startswith("## ")), len(lines))
    at = next((i for i in range(end) if line_re.match(lines[i].strip())), None)
    if at is not None:
        lines[at] = line
    else:
        at = end
        while at > 0 and not lines[at - 1].strip():
            at -= 1
        lines[at:at] = ["", line] if at and lines[at - 1].startswith(("# ", ">")) else [line]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def cmd_cases(root: Path, ident: str) -> int:
    """Run the skills' cases change `ident`'s diff calls for through `sdlc.py run-cases`, under its
    own cost cap, and write what ship reads into `findings.md`'s note: `Skill evals: ran, <passed>
    of <cases>`, or `skipped, <why>`. A failed case writes nothing and exits 1. Never `eval` in its
    name, and no skill's rule grants it: each run is paid, so the harness asks first."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    code, found, said = _sdlc(["run-cases", folder.name], root)
    if found is None:
        why = f"sdlc.py run-cases: {said.strip()[-500:]}"
        return emit({"change": folder.name, "refusals": [why]}, 1)
    out = {**found, "change": folder.name}
    if code:
        return emit({**out, "note": None}, 1)
    if found.get("skipped"):
        note = f"Skill evals: skipped, {found['skipped']}"
    else:
        rows = [r for r in found.get("cases") or [] if isinstance(r, dict)]
        passed = sum(1 for r in rows if isinstance(r.get("score"), int | float) and r["score"] >= 1)
        note = f"Skill evals: ran, {passed} of {len(rows)}"
    _note_line(folder, CASES_RE, note)
    return emit({**out, "note": note})


def _unreviewed_at_test(root: Path, folder: Path, cfg: dict) -> list[str] | None:
    """`land_unreviewed()` for a change at `stage: test`, before any landing rebase can move a
    file; nothing for one already shipped."""
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    return land_unreviewed(root, folder, cfg) if meta.get("stage") == "test" else []


def land_message(
    root: Path,
    folder: Path,
    by: str,
    refs: bool,
    nits: list[str] = (),
    unreviewed: list[str] | None = (),
) -> str:
    """The landed change's commit message: its title, its Problem's first sentence and its folder,
    a `Retired nits:` paragraph naming each nit it took in, ship's `Carried forward:`, `Dropped:`
    and `How to recover:` paragraphs, each when it holds anything (read from `notes.md`'s ticks
    and `decision.md`'s `- RECOVER:` lines, so a rerun's message is the same), as `/sdlc:ship`
    writes them, the paths changed since its last review (`unreviewed`, None when there is no
    snapshot to compare), `Refs #N` when its number is its issue's, and who passed the gate, with
    `unreviewed=<n|unknown>` when anything is. No `Sdlc-Findings`: the factory's rounds stood in
    for ship's review, and retro reads a missing line as unanswered. Paths go in the body, never
    in a trailer."""
    text = (folder / "intent.md").read_text(encoding="utf-8")
    title = next((ln for ln in text.splitlines() if ln.startswith("# ")), f"# {folder.name}")
    title = re.sub(r"^#\s+\d{3,}\s+—\s+", "", title).lstrip("# ").strip()
    problem = text.split("## Problem", 1)[1] if "## Problem" in text else ""
    prose = " ".join(problem.split("\n## ", 1)[0].split())
    first = first_sentence(prose)
    body = f"{first} See {folder.relative_to(root).as_posix()}/.".strip()
    paragraphs = [title, body]
    notes = folder / "notes.md"
    ticked = [m for line in (notes.read_text(encoding="utf-8").splitlines() if notes.is_file()
                             else []) if (m := TICKED_RE.match(line))]  # fmt: skip
    carried = [f"- {m.group(1)} → {m.group(3)}" for m in ticked if m.group(2) == "seed"]
    dropped = [f"- {m.group(1)}: {m.group(3)}" for m in ticked if m.group(2) == "dropped"]
    recover = [f"- {subject}: {way}" for subject, way in read_proposals(folder)[1]]
    retired = [f"- {n}: taken in by {folder.name}" for n in nits]
    for head, lines in (("Retired nits:", retired), ("Carried forward:", carried),
                        ("Dropped:", dropped), ("How to recover:", recover)):  # fmt: skip
        if lines:
            paragraphs.append("\n".join([head, *lines]))
    landed = f"{LANDED}: by={by}"
    if unreviewed is None:
        paragraphs.append("No snapshot of its last review.")
        landed += " unreviewed=unknown"
    elif unreviewed:
        paragraphs.append(f"Changed since its last review: {', '.join(unreviewed)}")
        landed += f" unreviewed={len(unreviewed)}"
    tail = [f"Refs #{int(folder.name.split('-')[0])}"] if refs else []
    tail.append(landed)
    return "\n\n".join([*paragraphs, "\n".join(tail)]) + "\n"


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


def filed_nit(text: str, change: str, nit: dict) -> bool:
    """Whether the register `text` already holds `nit` for `change`: a `[nit]` entry whose
    `Raised by:` names the change and whose body holds the nit's text. Never by title alone."""
    entry, fenced = None, False
    for line in [*text.splitlines(), "## end"]:
        if FENCE_RE.match(line):
            fenced = not fenced
        if fenced or not line.startswith("## "):
            if entry is not None:
                entry.append(line)
            continue
        if entry is not None:
            body = "\n".join(entry)
            raised = re.search(rf"^Raised by: {re.escape(change)}\b", body, re.M)
            if raised and nit["text"] in body:
                return True
        entry = [] if NIT_RE.match(line) else None
    return False


def _dispose(root: Path, folder: Path, pre: dict) -> tuple[list[str], str | None]:
    """What the person's yes approved for change `folder`'s undone notes, its agents' nits and its
    assumed decisions, written in its worktree before `sdlc.py ship`, every edit by line: each
    carried item appended to the register as an `[idea]` seed, each approved bug as a `[bug]` with
    its `Severity:` and `Paths:` and no `Introduced by:`, and each nit to file (`land_parts()`'s
    `nits`) as a `[nit]` with its `Theme:`, `Paths:`, `Cost:`, `Value:` and `Raised by:` (ids from
    one `next-entry` call; the register created from its template when missing), each item ticked
    `→ seed: <id>` or `→ bug: <id>`, each dropped one ticked `→ dropped: <reason>`, and each
    assumed decision ticked as confirmed. What a rerun finds ticked, or filed (`filed_nit()`), it
    never writes again. The ids of the nits it filed, and None or why nothing was
    written."""
    cfg, _ = load_config(root)
    parts = land_parts(folder, pre, root, cfg)
    seeds = [u for u in parts["undone"] if "seed" in u or "bug" in u]
    notes, ids, filed = folder / "notes.md", [], []
    nits = parts["nits"]
    if seeds or nits:
        _, config, said = _sdlc(["config"], root)
        register = ((config or {}).get("work") or {}).get("register")
        template = (((config or {}).get("templates") or {}).get("inbox.md") or {}).get("path")
        if not register:
            return [], f"sdlc.py config names no register: {said.strip()[-300:]}"
        register = Path(register)
        if not register.is_file() and not (template and Path(template).is_file()):
            return [], f"no register at {register.name}, and no template to start one from"
        text = (register.read_text(encoding="utf-8") if register.is_file()
                else Path(template).read_text(encoding="utf-8"))  # fmt: skip
        nits = [n for n in nits if not filed_nit(text, folder.name, n)]
    if seeds or nits:
        want = len(seeds) + len(nits)
        code, _, said = _sdlc(["next-entry", "--count", str(want)], root)
        ids = [w for w in said.split() if re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d+", w)]
        if code or len(ids) != want:
            return [], f"sdlc.py next-entry gave no ids: {said.strip()[-300:]}"
        rel = folder.relative_to(root).as_posix()
        for entry_id, item in zip(ids, seeds, strict=False):
            if bug := item.get("bug"):
                text = text.rstrip("\n") + (
                    f"\n\n## [{entry_id}] [bug] {bug['title']}\n\nFound by the review of "
                    f"{folder.name}.\n{item['text']}\n\nSeverity: {bug['severity']}\n"
                    f"Paths: {', '.join(bug['paths'])}\n"
                )
                continue
            text = text.rstrip("\n") + (
                f"\n\n## [{entry_id}] [idea] {item['seed']}\n\nLeft undone by {folder.name}, "
                f"carried forward when it landed: {item['text']}\nSee {rel}/notes.md in its "
                f"commit.\nRaised {entry_id[:10]}.\n"
            )
        for entry_id, nit in zip(ids[len(seeds) :], nits, strict=True):
            text = text.rstrip("\n") + (
                f"\n\n## [{entry_id}] [nit] {nit['title']}\n\nRaised by the {nit['role']} "
                f"review of {folder.name}, round {nit['round']}: {nit['text']}\n\n"
                f"Theme: {nit['theme']}\nPaths: {', '.join(nit['paths'])}\nCost: {nit['cost']}\n"
                f"Value: {nit['value']}\nRaised by: {folder.name} ({nit['pass']})\n"
            )
            filed.append(entry_id)
        register.parent.mkdir(parents=True, exist_ok=True)
        register.write_text(text, encoding="utf-8", newline="\n")
    if parts["undone"]:
        lines = notes.read_text(encoding="utf-8").splitlines()
        given = iter(ids)
        for item in parts["undone"]:
            if "dropped" in item:
                said = f"dropped: {item['dropped']}"
            else:
                said = f"{'bug' if 'bug' in item else 'seed'}: {next(given)}"
            at = item["line"] - 1
            lines[at] = lines[at].replace("[ ]", "[x]", 1).rstrip() + f" → {said}"
        notes.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    if parts["assumed"]:
        ledger = folder / "decisions.md"
        lines = ledger.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            m = LEDGER_RE.match(line)
            if m and m.group(1) == " " and m.group(4) == "default":
                lines[i] = "- [x]" + line.rstrip()[5:] + DECIDED + CONFIRMED
        ledger.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return filed, None


def cmd_land(root: Path, ident: str, by: str) -> int:
    """Land change `ident`'s first half, in its worktree: the approver's impact on `intent.md`,
    `sdlc.py ship` (stamped, the seed dropped, every path staged), the commit with
    `land_message()`, then `sdlc.py base`; `filed_nits`, the `[nit]` entries the person's yes filed
    (`_dispose()`). Its `state`: `current` (nothing to review again),
    `rebased` (the base moved: the gate and the spec's path run again before close), `conflict`
    (the rebase was aborted: `resolve` takes it), or `refused`, with why."""
    folder, refusal = find_change(root, ident)
    out: dict = {"change": None, "state": "refused", "refusals": [], "filed_nits": []}
    if refusal:
        return emit({**out, "refusals": [refusal]}, 1)
    out["change"] = folder.name
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    impact = read_impact(folder)
    nits: list[str] = []
    decision = read_decision(folder)[0]
    if meta.get("stage") not in ("test", "shipped") or decision is None:
        return emit(
            {**out, "refusals": [f"{folder.name} isn't ready: stage test with a decision"]}, 1
        )
    # The gate's rule is the script's, never only the skill's: a change only a person can ship is
    # refused whoever passed the gate, and `auto` is refused while any risk signal stands.
    cfg, _ = load_config(root)
    pre, said = _preflight(folder, root)
    if pre is None:
        return emit({**out, "refusals": [f"preflight couldn't be read: {said.strip()[-300:]}"]}, 1)
    unreviewed = _unreviewed_at_test(root, folder, cfg)
    signals, excluded = land_signals(folder, root, decision, cfg, pre, unreviewed=unreviewed)
    if excluded:
        return emit({**out, "refusals": [f"ship it by hand: {'; '.join(excluded)}"]}, 1)
    if by == "auto" and signals:
        return emit({**out, "refusals": [f"the gate is the person's: {'; '.join(signals)}"]}, 1)
    if meta.get("stage") == "test":
        # Every refusal before the first write: what the person's yes approved running has run,
        # on the change as it stands.
        if impact is None:
            return emit({**out, "refusals": ["no impact to set: decision.md has no - IMPACT:"]}, 1)
        num = folder.name.split("-")[0]
        if (pre.get("checks") or {}).get("checks") and _accept_state(root, folder) != "PASS":
            why = (f"its acceptance checks haven't passed on the change as it stands: run "
                   f"factory.py accept {num}")  # fmt: skip
            return emit({**out, "refusals": [why]}, 1)
        if (pre.get("cases") or {}).get("scope") and not _note_says(folder, CASES_RE):
            why = f"its skills' cases haven't run: run factory.py cases {num}"
            return emit({**out, "refusals": [why]}, 1)
        if not _set_impact(folder / "intent.md", impact):
            return emit({**out, "refusals": ["no impact to set: intent.md has no impact: line"]}, 1)
        if by == "person":
            out["filed_nits"], refused = _dispose(root, folder, pre)
            if refused:
                return emit({**out, "refusals": [refused]}, 1)
        if (pre.get("risk") or {}).get("deep") and not _note_says(folder, FRESH_RE):
            _note_line(folder, FRESH_RE, FRESH_SKIPPED)
        nits = named_nits(root, folder)
        code, _, said = _sdlc(["ship", folder.name], root)
        if code:
            return emit({**out, "refusals": [f"sdlc.py ship refused: {said.strip()[-500:]}"]}, 1)
        # The nits the change took in leave the register in its own commit, as ship's skill
        # deletes them: after ship, so every refusal of its comes before this write.
        if nits:
            retire_nits(root, nits)
            _git(root, "add", "--", INBOX.as_posix())
        if why := _land_commit(root, folder, by, nits, unreviewed):
            return emit({**out, "refusals": [why]}, 1)
    elif _commit_failed(root, folder):
        # Shipped, but its commit never made: ship again (a rerun is harmless) and commit what
        # the first run would have. Its disposals, checks and impact ran before ship stamped it.
        code, _, said = _sdlc(["ship", folder.name], root)
        if code:
            return emit({**out, "refusals": [f"sdlc.py ship refused: {said.strip()[-500:]}"]}, 1)
        before = _git(root, "show", f"HEAD:{INBOX.as_posix()}")
        nits = [n for n in named_nits(root, folder, before) if n not in named_nits(root, folder)]
        if why := _land_commit(root, folder, by, nits, unreviewed):
            return emit({**out, "refusals": [why]}, 1)
    # Landed before, and the base moved again: the earlier landing's record goes into the
    # change's commit first, or `base` refuses on a branch with a commit and uncommitted work.
    elif why := _amend_record(root, folder):
        return emit({**out, "refusals": [why]}, 1)
    code, based, said = _sdlc(["base", folder.name], root)
    action = (based or {}).get("action")
    reason = str((based or {}).get("reason") or said)
    out.update(head=_git(root, "rev-parse", "--short", "HEAD"), base=based, retired_nits=nits)
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


def _land_commit(
    root: Path, folder: Path, by: str, nits: list[str], unreviewed: list[str] | None
) -> str | None:
    """The landing's one commit of what `sdlc.py ship` staged, with `land_message()`: None, or
    why it failed, in git's own words (the tail of its stderr, else its stdout)."""
    _, cfg_out, _ = _sdlc(["config"], root)
    refs = ((cfg_out or {}).get("archive") or {}).get("ids_from") == "github"
    message = land_message(root, folder, by, refs, nits, unreviewed)
    try:
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-F", "-"], input=message,
            capture_output=True, encoding="utf-8", check=True,
        )  # fmt: skip
    except subprocess.CalledProcessError as e:
        said = (e.stderr or "").strip() or (e.stdout or "").strip() or str(e)
        return f"the commit failed: {said[-500:]}"
    except OSError as e:
        return f"the commit failed: {e}"
    return None


def _commit_failed(root: Path, folder: Path) -> bool:
    """Whether a landing stopped after `sdlc.py ship` and before its commit: `HEAD`'s message has
    no `Sdlc-Landed:` line and `HEAD`'s `intent.md` isn't shipped. One a person shipped and
    committed by hand says `stage: shipped` in `HEAD`, and is never committed again."""
    if f"\n{LANDED}: " in "\n" + (_git(root, "log", "-1", "--format=%B") or ""):
        return False
    rel = (folder / "intent.md").relative_to(root).as_posix()
    return frontmatter(_git(root, "show", f"HEAD:{rel}") or "").get("stage") != "shipped"


def _dirty(root: Path) -> list[str] | None:
    """Every path `root` has uncommitted, untracked ones included, read from `git status
    --porcelain -z` as it printed it: never through `_git()`, whose strip takes the first entry's
    leading space (` M path`) and so a character of its path. A rename's old path is skipped.
    None when git fails."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "-z", "--untracked-files=all"],
            capture_output=True, encoding="utf-8", check=True,
        )  # fmt: skip
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    entries, paths = done.stdout.split("\0"), []
    i = 0
    while i < len(entries):
        entry = entries[i]
        if len(entry) > 3:
            paths.append(entry[3:])
            if entry[0] in "RC":
                i += 1
        i += 1
    return paths


def _amend_record(root: Path, folder: Path, also: list[str] = ()) -> str | None:
    """The landing's own record (its gate, its review, a resolved conflict's marker, the run's
    costs), written after the change's commit, amended into that commit, so the change lands as
    one commit, and `sdlc.py base` and `close` find the worktree clean. Why not, or None: anything
    dirty outside the change's folder is not the landing's, and is refused, but the paths `also`
    names: a fix the builder made at landing (`cmd_land_fix()`), staged with the record."""
    dirty = _dirty(root)
    if dirty is None:
        return "git status couldn't be read"
    rel = folder.relative_to(root).as_posix() + "/"
    stray = [p for p in dirty if not p.startswith(rel) and p not in also]
    if stray:
        return f"uncommitted outside the change's folder: {', '.join(stray)}"
    if dirty:
        if f"\n{LANDED}: " not in "\n" + (_git(root, "log", "-1", "--format=%B") or ""):
            return "HEAD isn't the landing's commit, so its record has nothing to be amended into"
        _git(root, "add", "--", rel, *also)
        if _git(root, "commit", "-q", "--amend", "--no-edit") is None:
            return "the landing's record couldn't be added to the commit"
    return None


def cmd_land_close(root: Path, ident: str) -> int:
    """Land change `ident`'s second half: `sdlc.py close` run from the main checkout (from inside
    the change's worktree it would keep the worktree), which merges, archives, removes the folder,
    the worktree and the branch, and pushes as `git.push` says. Its JSON passes through. When the
    base branch has moved since the change was gated (`_behind()`), before the close or racing it,
    no close lands: the move is recorded in `runs/land-moves`, amended in with the record, and the
    state is `moved`, for `land` to rebase again, up to the base branch's `[land] moves`."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    # A batch that passed itself closes a change resolved while landing only once its review
    # passed: the script's rule, never only the skill's. Read before the amend moves `HEAD`. Only
    # the landing's signal: `land` read the rest before it committed, and its own rebase can move
    # the files `conflicts.md` names with nothing resolved.
    if f"\n{LANDED}: by=auto" in "\n" + (_git(root, "log", "-1", "--format=%B") or ""):
        cfg, _ = load_config(root)
        if LANDING_RESOLVED in resolution_signals(root, folder, cfg):
            why = f"landed by=auto, and {LANDING_RESOLVED}: no landing review has passed it"
            return emit({"refusals": [why]}, 1)
        if list(folder.glob("build/land-*.ask.md")):
            return emit(
                {"refusals": [f"landed by=auto, and {LANDING_FIXED}: the gate is the person's"]}, 1
            )
    # The base branch moved since the change was gated and reviewed: close would only refuse (it
    # fast-forwards), so the landing goes back to its rebase, `land` again, with the move
    # recorded before the amend so the commit it was found on carries it.
    cfg, _ = load_config(root)
    # The landing's review rounds join carry's record before it is amended in, every rerun
    # included; with none reviewed, carry's file stands as it is.
    landing, _ = read_rounds(folder, [], "land")
    for r in landing:
        r["complete"] = bool(r["reviews"])
    if any(r["complete"] for r in landing):
        write_findings(folder, _rounds_at_depth(root, folder, cfg)[0] + landing)
    moved = _behind(root) > 0
    if moved and (why := _record_move(root, folder, cfg)):
        return emit({"refusals": [why]}, 1)
    if why := _amend_record(root, folder):
        return emit({"refusals": [why]}, 1)
    if moved:
        return emit(_moved(folder))
    main = worktrees(root)[0][0] if worktrees(root) else root
    code, closed, said = _sdlc(["close", ident], main)
    # A move racing the close: read from the base, never from close's words.
    if code and not (closed or {}).get("done") and _behind(root) > 0:
        if why := _record_move(root, folder, cfg) or _amend_record(root, folder):
            return emit({"refusals": [why]}, 1)
        return emit(_moved(folder))
    return emit(closed or {"refusals": [said.strip()[-500:]]}, code)


LAND_MOVES = Path("runs") / "land-moves"


def _behind(root: Path) -> int:
    """How many commits the base branch has that the change's branch lacks: 0 when it hasn't
    moved, or when there is no base to count."""
    base = _base(root)
    count = _git(root, "rev-list", "--count", f"HEAD..refs/heads/{base}") if base else None
    return int(count) if count and count.isdigit() else 0


def _record_move(root: Path, folder: Path, cfg: dict) -> str | None:
    """One more move of the base branch, the tip it saw, a line of `runs/land-moves`; or why not:
    the base branch's `[land] moves` already followed."""
    path = folder / LAND_MOVES
    seen = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    base = _base(root) or "the base branch"
    if len(seen) >= cfg["land"]["moves"]:
        return (
            f"{base} moved {cfg['land']['moves']} times while {folder.name} landed: run "
            "/sdlc-factory:land again, or /sdlc:ship it by hand"
        )
    tip = _git(root, "rev-parse", f"refs/heads/{base}") or "unknown"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{s}\n" for s in [*seen, tip]), encoding="utf-8", newline="\n")
    return None


def _moved(folder: Path) -> dict:
    moves = len((folder / LAND_MOVES).read_text(encoding="utf-8").splitlines())
    return {"change": folder.name, "state": "moved", "moves": moves}


def cmd_land_fix(root: Path, ident: str, ask: str | None, commit: bool) -> int:
    """A fix the person asked for at landing, after the change's commit. `ask`: the id (`R3`) of
    the person's ticked `(person, fix)` line in `decisions.md`, never their words; on a shipped
    change whose landing round under way passed, or none is open, open round `land-<n+1>` and
    copy the line's words to `build/land-<n+1>.ask.md`, for the builder (`agent --task
    land-fix`) and then every reviewer at the run's depth. `commit`: amend what the builder
    changed outside the folder (`fixed`) into the change's commit through `_amend_record()`, so
    the new `HEAD` is gated again before its review."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    n = land_round(folder)
    out = {"change": folder.name}
    if commit:
        if land_ask(folder, n) is None:
            return emit({**out, "refusals": ["no fix was asked for: run land-fix --ask first"]}, 1)
        dirty = _dirty(root)
        if dirty is None:
            return emit({**out, "refusals": ["git status couldn't be read"]}, 1)
        rel = folder.relative_to(root).as_posix() + "/"
        fixed = [p for p in dirty if not p.startswith(rel)]
        if not fixed:
            why = "the builder changed nothing outside the change's folder: nothing to commit"
            return emit({**out, "refusals": [why]}, 1)
        if why := _amend_record(root, folder, also=fixed):
            return emit({**out, "refusals": [why]}, 1)
        head = _git(root, "rev-parse", "--short", "HEAD")
        return emit({**out, "round": n, "fixed": fixed, "head": head})
    meta = frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    if meta.get("stage") != "shipped":
        return emit({**out, "refusals": [f"{folder.name} isn't shipped: land it first"]}, 1)
    words = read_fix_words(folder, ask or "")
    if words is None:
        why = f"{ask} isn't a `- [x] {ask} (person, fix): …` line in decisions.md"
        return emit({**out, "refusals": [why]}, 1)
    cfg, _ = load_config(root)
    if n and land_verdict(root, folder, cfg, n)["next"] != "pass":
        why = f"landing round {n} hasn't passed: a fix is asked only after it does"
        return emit({**out, "refusals": [why]}, 1)
    (folder / "reviews" / f"land-{n + 1}").mkdir(parents=True, exist_ok=True)
    path = land_ask_path(folder, n + 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(words + "\n", encoding="utf-8", newline="\n")
    return emit({**out, "round": n + 1, "ask": path.relative_to(root).as_posix()})


def _conflicted(root: Path) -> list[str]:
    return (_git(root, "diff", "--name-only", "--diff-filter=U") or "").splitlines()


COUNTER = ".sdlc/last-id"
# The most commits `resolve` carries past a conflict in the counter alone, so it never spins.
RESOLVE_STEPS = 20


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
    lists the conflicted files (or finds none, `clean`, and it is done: `.sdlc/last-id` alone
    settles itself); `--continue` checks no conflict
    marker is left in them, stages them and continues, aborting the rebase on a second conflict.
    Every git step is this script's: the builder only edits the files it is given. A conflicted
    register loses, before it is staged, every entry the landing deleted from it, whatever the
    builder kept: the change's `idea:` and `fixes:` entries and the nits it retired, each by id
    (`dropped`). A finished
    resolution leaves `runs/land-resolved`: `land-<n>`, the round under way, then the files. It is
    a resolved conflict no reviewer has seen until round `n`'s review passes
    (`resolution_signals()`)."""
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
        # Only the counter conflicted, and it settled itself: nothing is left for the builder,
        # so the rebase goes on, a commit at a time, as long as that is all a commit conflicts on.
        for _ in range(RESOLVE_STEPS):
            stopped = _git(root, "rev-parse", "-q", "--verify", "REBASE_HEAD")
            if not (done.returncode and not files and stopped):
                break
            done = subprocess.run(["git", "-C", str(root), "rebase", "--continue"],
                                  capture_output=True, encoding="utf-8", env=env)  # fmt: skip
            _settle_counter(root)
            files = _conflicted(root)
        if done.returncode and not files:
            return emit({"refusals": [f"git rebase failed: {done.stderr.strip()[-300:]}"]}, 1)
        return emit(
            {"change": folder.name, "conflicted": files, "state": "conflict" if files else "clean"}
        )
    files = _conflicted(root)
    marked = [
        f for f in files
        if CONFLICT_MARKER_RE.search((root / f).read_text(encoding="utf-8", errors="replace"))
    ]  # fmt: skip
    if marked:
        return emit({"refusals": [f"conflict markers left in: {', '.join(marked)}"]}, 1)
    # What the landing deleted from the register stays deleted, whatever the builder kept: the
    # change's own seeds and the bugs it fixes, by id, and the nits it retired (`named_nits()`).
    dropped: list[str] = []
    if INBOX.as_posix() in files:
        text = (folder / "intent.md").read_text(encoding="utf-8")
        ids = [*frontmatter_ids(text, "idea"), *frontmatter_ids(text, "fixes")]
        dropped = drop_entries(root, [*ids, *named_nits(root, folder)])
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
    marker.write_text(
        f"land-{land_round(folder)}\n" + ", ".join(files) + "\n", encoding="utf-8", newline="\n"
    )
    head = _git(root, "rev-parse", "--short", "HEAD")
    return emit({"change": folder.name, "resolved": files, "state": "resolved",
                 "dropped": dropped, "head": head})  # fmt: skip


def cmd_land_verdicts(root: Path, ident: str) -> int:
    """The landing review of round `land-<n>`, and the step it takes next: `gate` (the script's
    gate on the change as rebased, before any reviewer, while the base branch names one),
    `accept` (a change with acceptance checks runs them again on its commit as rebased, through
    `factory.py accept`, after the gate),
    `review` for the `missing` reviewers (behaviour alone after a clean rebase, every reviewer at
    the run's depth after a resolved conflict or a fix the person asked for, `fixed`), `verify`
    when one asks for changes, `pass` when none is kept, `mend` when every problem is one the
    agent that wrote it can answer again (a behaviour check's missing `## Evidence` or `exit:`, a
    verdict after a preamble, the verifier's unread answers), with the roles in `mend`, each once a
    landing round (`land_mended()`), or `stop`, with why: a red gate or check, a kept change, a
    reply without a verdict, or a mendable problem beside one of those or after its one mend."""
    cfg, _ = load_config(root)
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    n = land_round(folder)
    if not n:
        return emit({"change": folder.name, "round": None, "next": "pass", "missing": []})
    return emit(land_verdict(root, folder, cfg, n))


def land_verdict(root: Path, folder: Path, cfg: dict, n: int, settled: bool = False) -> dict:
    """Landing round `n`'s verdicts and the step it takes next, as `land-verdicts` emits them for
    the round under way: the one reading of whether a landing review passed, which
    `resolution_signals()` asks too, `settled` (see `_land_gate_state()`)."""
    path = folder / "reviews" / f"land-{n}"
    resolved = (folder / "runs" / "land-resolved").is_file()
    fixed = land_ask(folder, n) is not None
    rounds, _, run = _rounds_at_depth(root, folder, cfg)
    wanted = list(run["reviewers"]) if resolved or fixed else ["behaviour"]
    reviews, problems = {}, []
    # Kept apart as they're added, by the role that mends each, as `loop_state()` keeps them: a
    # missing `## Evidence`, a verdict after a preamble, the verifier's unread answers.
    mendable: dict[str, list[str]] = {}
    for role in wanted:
        file = path / f"{role}.md"
        if not file.is_file():
            continue
        lines = file.read_text(encoding="utf-8").splitlines()
        m = VERDICT_RE.match(lines[0]) if lines else None
        if not m:
            problem = f"reviews/land-{n}/{role}.md doesn't open with a VERDICT"
            problems.append(problem)
            if preamble(file):
                mendable.setdefault(role, []).append(problem)
            continue
        reviews[role] = {
            "verdict": m.group(1),
            "changes": [c.group(1) for c in map(CHANGE_RE.match, lines[1:]) if c],
        }
        if role in RUNS_THE_CHANGE:
            found = read_evidence("\n".join(lines), f"reviews/land-{n}/{role}.md")
            problems += found
            mendable.setdefault(role, []).extend(found)
    missing = [r for r in wanted if r not in reviews]
    verified, wrong = read_verified(path / VERIFIED, n, reviews, f"reviews/land-{n}/{VERIFIED}")
    problems += wrong
    if wrong:
        mendable["verifier"] = wrong
    # Each role is mended once a landing round: one already mended is a stop like any other.
    for role in land_mended(folder, n) & set(mendable):
        del mendable[role]
    every = {p for found in mendable.values() for p in found}
    # The rebased change is gated by the script before any reviewer reads it, as each build was.
    # Red is a stop, never a fix: the landing has no builder round, so the person ships it.
    gate = _land_gate_state(root, folder, n, settled)
    if gate and gate["current"] == "FAIL":
        problems.append(
            f"the gate failed on the change as rebased (exit {gate['exit']}), in "
            f"build/land-{n}.gate.md: ship it by hand"
        )
    # So are its acceptance checks, on its commit as rebased, after the gate and before review.
    has_checks = (folder / "checks.md").is_file()
    accept = _accept_state(root, folder, settled) if has_checks else "PASS"
    if accept == "FAIL":
        problems.append(
            f"its acceptance checks failed on the change as rebased, in "
            f"{accept_path(folder).relative_to(folder).as_posix()}: ship it by hand"
        )
    out = {"change": folder.name, "round": n, "reviews": reviews, "missing": missing,
           "resolved": resolved, "fixed": fixed, "gate": gate, "accept": accept,
           "problems": problems, "mend": []}  # fmt: skip
    asks = any(r["verdict"] == "CHANGES" for r in reviews.values())
    if problems and set(problems) <= every:
        out["next"], out["mend"] = "mend", [role for role, found in mendable.items() if found]
    elif problems:
        out["next"] = "stop"
    elif gate and gate["current"] is None:
        out["next"] = "gate"
    elif accept is None:
        out["next"] = "accept"
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
    return out


# ---------------------------------------------------------------- what escaped, and old code
#
# The eval replays the reviewers on the diffs that let real bugs through, and the review looks at
# code no change touches. Both read what `sdlc.py` writes (the register's `[bug]` entries, the
# `Close` commits' `Sdlc-Fixes` and `Sdlc-Base` lines) with copies of its parsing, pinned to it by
# tests, since this plugin's cached copy has no `sdlc.py`. Neither writes the register: a review's
# bugs reach it only through `/sdlc:bug`.

INBOX = Path(".sdlc") / "work" / "inbox.md"
BUG_RE = re.compile(r"^##\s*\[(\d{4}-\d{2}-\d{2})-(\d+)\]\s*\[bug\]\s*(.+)$")
NIT_RE = re.compile(r"^##\s*\[(\d{4}-\d{2}-\d{2}-\d+)\]\s*\[nit\]")
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
# Starts of `[ui] serve`, each on a new port, before a port lost to another process is a problem.
SERVE_TRIES = 3


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


def _fixture_copy(root: Path, where: Path, fixture: str | None) -> tuple[str, str | None]:
    """A fresh copy of `[ui] fixture` at `where/fixture/` (a file inside it, by its name), and its
    path relative to the checkout, for `{fixture}`: ("", None) without one, and ("", a problem)
    when the checkout lacks it. Only that folder is replaced, which only `shots` writes, so a
    server that writes into its data never touches the committed fixture, nor the next shot's."""
    if not fixture:
        return "", None
    source = root / fixture
    if not source.exists():
        return "", f"ui.fixture {fixture} doesn't exist in the checkout, so no server started"
    copy = where / "fixture"
    if copy.exists():
        # A git repo a server built in its copy holds read-only objects Windows won't remove.
        for path in copy.rglob("*"):
            with suppress(OSError):
                path.chmod(stat.S_IWRITE | stat.S_IREAD | (stat.S_IEXEC if path.is_dir() else 0))
        shutil.rmtree(copy)
    if source.is_dir():
        shutil.copytree(source, copy, symlinks=True)
        served = copy
    else:
        copy.mkdir(parents=True)
        served = copy / source.name
        shutil.copy2(source, served)
    return served.relative_to(root).as_posix(), None


def _binds(host: str, port: int) -> bool:
    """Whether `host`:`port` binds now, the socket closed straight after: a port that won't is held
    by another process. `SO_REUSEADDR` lets a port whose last connection is in TIME_WAIT bind, as
    a server restarting on it would, while one another socket holds, listening or bound, still
    won't; on Windows it would let a held port bind too, and TIME_WAIT never blocks a bind there.
    The wildcard address is probed too: on macOS a port a server holds on `0.0.0.0` still lets
    `host` bind beside it."""
    for address in dict.fromkeys((host, "0.0.0.0")):
        try:
            with socket.socket() as s:
                if os.name != "nt":
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((address, port))
        except OSError:
            return False
    return True


def _lost(host: str, port: int) -> bool:
    """Whether a server that has exited lost `port` to another process, so a new one is worth
    trying: only when the port won't bind (`_binds()`). One that binds means the server failed on
    its own. The one place a serve's end is judged, whichever way it ended."""
    return not _binds(host, port)


def _up(proc: subprocess.Popen, host: str, port: int, timeout: float) -> tuple[str | None, bool]:
    """Whether the server `proc` came up on `port`: (None, False) once it answers, else why not and
    whether the port was lost (`_lost()`, for every way the server ended). A port that answers
    after `proc` exited is never shot. A timeout is the server's own, never lost."""
    deadline = time.monotonic() + timeout
    answered = False
    while proc.poll() is None:
        if _answers(host, port):
            answered = True
            # Answering, and still running after: up.
            if proc.poll() is None:
                return None, False
            break
        if time.monotonic() > deadline:
            return f"the dev server didn't answer on {port} in {timeout}s", False
        time.sleep(0.2)
    if answered:
        why = f"port {port} answered, but the dev server had exited {proc.returncode}"
    else:
        why = f"the dev server exited {proc.returncode} before answering on {port}"
    return why, _lost(host, port)


def _serve(
    root: Path, where: Path, ui: dict, record: dict, sink: BinaryIO
) -> tuple[subprocess.Popen | None, int | None]:
    """Start `[ui] serve` on a free port and wait until it answers, up to `SERVE_TRIES` times: a
    port another process took between `_free_port()` and the serve (it already answers, or won't
    bind once the server has exited, however it ended: `_lost()`) is tried again on a new one, each
    lost try in `record`'s `retries`. A server that exits on a port that binds, doesn't answer in
    time, or can't start, failed on its own and isn't retried. The process
    started and its port, or (None, …) with `record`'s `problem` set; a fresh fixture copy each
    try, since a server may have written into the last."""
    group = (
        {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    port = None
    for _ in range(SERVE_TRIES):
        port = _free_port()
        served, problem = _fixture_copy(root, where, ui.get("fixture"))
        # `{fixture}` only with one set: unset, `serve` runs as written.
        record["serve"] = _fill(ui["serve"], port=port, **({"fixture": served} if served else {}))
        record["port"], record["problem"] = port, problem
        if problem:
            # No data to serve, no server.
            return None, port
        # Wait where the shots will go: `[ui] url`'s host, not one assumed.
        host = urlparse(_fill(ui["url"], port=port)).hostname or "127.0.0.1"
        if _answers(host, port):
            lost = f"port {port} already answered before the dev server started"
            record["retries"].append({"port": port, "why": lost})
            record["problem"] = lost
            continue
        try:
            proc = subprocess.Popen(
                _sh(record["serve"]), cwd=root, stdin=subprocess.DEVNULL, stdout=sink,
                stderr=subprocess.STDOUT, **group,
            )  # fmt: skip
        except OSError as e:
            record["problem"] = f"the dev server couldn't be started: {e}"
            return None, port
        why, lost = _up(proc, host, port, ui["timeout"])
        if why is None:
            return proc, port
        _stop(proc)
        record["problem"] = why
        if not lost:
            return None, port
        record["retries"].append({"port": port, "why": why})
    record["problem"] = (
        f"the dev server came up on none of {SERVE_TRIES} ports: {record['problem']}"
    )
    return None, port


def shots(root: Path, folder: Path, label: str, ui: dict, role: str) -> tuple[list[Path], dict]:
    """Each page of `[ui]` at each width, as PNGs under
    `.sdlc/reports/shots/<change>/<label>/<role>/`, with `shots.json` saying what ran and how it
    ended: `problem` is None only when every shot was written. A label already shot for the role
    without a problem is reused, not shot again. Each role has its folder, fixture copy and server
    of its own, so a round's ui and ux reviewers can take theirs at once. With `fixture` set, the
    server is given a fresh copy of it (`_fixture_copy()`), or isn't started at all."""
    where = _reports(root) / "shots" / folder.name / label / role
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
    record: dict = {"serve": None, "port": None, "shots": [], "problem": None, "retries": []}
    log = where / "serve.log"
    with log.open("wb") as sink:
        proc = None
        try:
            proc, port = _serve(root, where, ui, record, sink)
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


def cmd_shots(root: Path, ident: str, n: int, role: str) -> int:
    """Round `n`'s screenshots of the change's pages, for its `role` UI reviewer (`shots()`)."""
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    ui = load_config(root)[0]["ui"]
    if not ui_complete(ui):
        return emit({"refusals": ["the base branch's [ui] needs serve, shoot and paths"]}, 1)
    paths, record = shots(root, folder, f"round-{n}", ui, role)
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
    p_fresh = sub.add_parser("fresh", help="bring the change's branch up to the base before a run")
    p_fresh.add_argument("id")
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
    p_shots.add_argument("--role", choices=UI_REVIEWERS, required=True)
    p_write = sub.add_parser("write-spec", help="copy runs/spec-draft.md into spec.md, once")
    p_write.add_argument("id")
    p_stage = sub.add_parser("stage", help="set the intent's stage: line, in place")
    p_stage.add_argument("id")
    p_stage.add_argument("stage")
    p_restart = sub.add_parser("restart", help="send an escalated change back for another build")
    p_restart.add_argument("id")
    p_restart.add_argument("--words", help="the person's words in decisions.md (R1), if any")
    p_upgrade = sub.add_parser("upgrade", help="make a Tier 1 change Tier 2 on the person's answer")
    p_upgrade.add_argument("id")
    p_agent = sub.add_parser("agent", help="run one agent session for a step, and file its reply")
    p_agent.add_argument("id")
    p_agent.add_argument("--task", choices=TASKS, required=True)
    p_agent.add_argument("--role", choices=[*REVIEWERS, "builder", "approver", "verifier"])
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
    p_accept = sub.add_parser(
        "accept", help="run a change's acceptance checks through sdlc.py accept; never pre-approved"
    )
    p_accept.add_argument("id")
    p_cases = sub.add_parser(
        "cases", help="run a change's skills' cases through sdlc.py run-cases; paid, never allowed"
    )
    p_cases.add_argument("id")
    p_fix = sub.add_parser("land-fix", help="a fix the person asked for at landing")
    p_fix.add_argument("id")
    fix_how = p_fix.add_mutually_exclusive_group(required=True)
    fix_how.add_argument("--ask", help="the person's fix in decisions.md (R1): open its round")
    fix_how.add_argument("--commit", action="store_true", help="amend the builder's fix in")
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
    if args.cmd == "accept":
        return cmd_accept(root, args.id)
    if args.cmd == "cases":
        return cmd_cases(root, args.id)
    if args.cmd == "land-fix":
        return cmd_land_fix(root, args.id, args.ask, args.commit)
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
    if args.cmd == "fresh":
        return cmd_fresh(root, args.id)
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
        return cmd_shots(root, args.id, args.round, args.role)
    if args.cmd == "restart":
        return cmd_restart(root, args.id, args.words)
    if args.cmd == "upgrade":
        return cmd_upgrade(root, args.id)
    if args.cmd == "write-spec":
        return cmd_write_spec(root, args.id)
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
