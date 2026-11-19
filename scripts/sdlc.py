#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-frontmatter>=1.1", "PyYAML>=6.0"]
# ///
"""sdlc — the mechanical half of the change process in the host repo's process doc.

Every non-trivial change to a repo using this plugin gets a numbered folder under `.sdlc/work/`
holding its artifacts: `intent.md` always, plus `spec.md` and `plan.md` when the change is Tier 2.
That convention is only worth having if something checks it, because the failure mode is silent —
an intent stuck at `stage: build` for three weeks, or a Tier 2 change that quietly never got a
spec, looks exactly like a repo with nothing open.

`.sdlc/work/` is committed. A change's folder lives on its own branch, in its own worktree
(`.claude/worktrees/NNN-slug`), so a session there writes its artifacts where it works and the
review reads them in the diff. Close lands the branch, mirrors the folder to the tracker, and
removes it from `main` in a commit of its own: history is the copy. The folders this tool reads are
the checkout's own `.sdlc/work/` and each change worktree's folder (`change_dirs`).

So this tool answers the questions that are queries rather than decisions, and does the
mechanical steps the skills ask of it: ids, worktrees, scaffolding, audits, landing and
archiving. Its subcommands, each with a line on what it does, are the parser's own list, which
cannot drift from the code: `sdlc.py -h` lists them, and `sdlc.py <subcommand> -h` gives one's
arguments.

It deliberately does **not** write artifact prose. An `intent.md` is an argument about why a change
is worth making; generating one produces a restatement of the slug. The tool scaffolds and audits;
`/sdlc:intent`, plan mode and `/sdlc:ship` do the judgment.

This script is plugin-owned mechanism and knows nothing about what the host repo builds. It
locates the repo with `git rev-parse`; everything host-specific (the commands its gate and scans
are, the docs that hold its policy, its own templates) comes from `.sdlc/config.toml`, read by
`config` and by nothing else, so the skills have one place to ask.

It declares its own dependencies (the block above), so it runs the same in any repo:

    uv run --script sdlc.py                     # status report (no args)
    uv run --script sdlc.py new reopen-drafts --tier 2
    uv run --script sdlc.py check --strict      # exit 1 on any problem (for /sdlc:ship)
    uv run --script sdlc.py check --json
    uv run --script sdlc.py ship 001
    uv run --script sdlc.py config
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import importlib.util
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import unicodedata
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext, suppress
from datetime import UTC, date, datetime
from pathlib import Path

import frontmatter
import yaml


# The registry: each command declares its own parser and its adapter, beside its handler, with
# `@command`, and `main` builds the parsers from it (`_parser()`) and runs the adapter it names, so
# adding or changing a command never edits `main`. `HELP_ORDER` pins the order `--help` lists them
# in; a command it doesn't name follows, in the order it registered. A copy of these is in each of
# `sdlc.py` and `factory.py`, which never imports the other, pinned by a test.
class UsageError(Exception):
    """A command line the parser took but an adapter refuses: `main` prints it as the parser's own
    usage error, and exits 2."""


class Command:
    """One registered command: the adapter `main` runs, its help line, and its arguments."""

    def __init__(self, run, about: str, specs: tuple) -> None:
        self.run, self.about, self.specs = run, about, specs


COMMANDS: dict[str, Command] = {}


def arg(*names: str, **kwargs) -> tuple:
    """One `add_argument` call, recorded for `_parser()` to make."""
    return ("arg", names, kwargs)


def exclusive(*args: tuple, required: bool = False) -> tuple:
    """A mutually exclusive group of `arg()`s, recorded for `_parser()` to make."""
    return ("group", required, args)


def command(name: str, about: str, *specs: tuple):
    """Register the decorated adapter as command `name`, with its help line and its arguments in
    the order its parser takes them. A name registered twice is refused as the script loads."""

    def register(run):
        if name in COMMANDS:
            raise ValueError(f"command {name!r} is registered twice")
        COMMANDS[name] = Command(run, about, specs)
        return run

    return register


def _parser(description: str, required: bool) -> argparse.ArgumentParser:
    """The script's parser, one subparser a registered command, in `HELP_ORDER` then the rest: the
    one place a parser is built."""
    ap = argparse.ArgumentParser(description=description)
    sub = ap.add_subparsers(dest="cmd", required=required)
    for name in [*HELP_ORDER, *(n for n in COMMANDS if n not in HELP_ORDER)]:
        entry = COMMANDS[name]
        p = sub.add_parser(name, help=entry.about)
        for spec in entry.specs:
            if spec[0] == "group":
                group = p.add_mutually_exclusive_group(required=spec[1])
                for _, names, kwargs in spec[2]:
                    group.add_argument(*names, **kwargs)
            else:
                p.add_argument(*spec[1], **spec[2])
    return ap


HELP_ORDER = (
    "status", "new", "check", "ship", "next", "undone", "bugs", "inbox-commit", "intake",
    "closes", "preflight", "mark-triaged", "needs-info", "next-entry", "nits", "groups", "checks",
    "findings", "accept", "gate", "cases", "run-cases", "drop", "upgrade", "base", "resolve",
    "close", "sync", "lookup", "config", "readiness", "drift", "record", "reset", "uninstall",
    "context", "unreleased", "release", "publish", "retro", "retro-commit", "board",
)  # fmt: skip


# Stage 6 is "maintain", which loops back to a new intent rather than being a stage a folder sits
# in — so it has no entry here. `dropped` is terminal and exempt from artifact checks. `spike` is
# exploration meant to be thrown away: entered from any stage, left by setting the stage it left,
# owing nothing, and measured apart from rework at close.
STAGES = ["plan", "spike", "design", "build", "test", "ship", "shipped", "dropped"]

# What each tier owes. Tier 0 never gets a folder at all, so it isn't listed.
TIER_ARTIFACTS = {
    1: ["intent.md"],
    2: ["intent.md", "spec.md", "plan.md"],
}

# A plan is only owed once building has started; requiring it at stage: plan would make every
# freshly-created Tier 2 folder fail its own check on day one.
PLAN_REQUIRED_FROM = ["build", "test", "ship", "shipped"]
SPEC_REQUIRED_FROM = ["design", "build", "test", "ship", "shipped"]

# What a change does to the people who receive the next release, judged against the previous one,
# not by tier: a Tier 1 change can add a feature, a Tier 2 one can be invisible. The
# host repo's process doc says what each means; `ship` refuses without one, so every change reaching
# a release has said it while the diff was in front of someone.
IMPACTS = ("major", "minor", "patch", "none")

# Three digits at least: a local id is padded to three, a GitHub issue number may run longer.
DIR_RE = re.compile(r"^(\d{3,})-([a-z0-9][a-z0-9-]*)$")
# The templates prompt with angle-bracketed guidance lines. Checking only that an artifact *exists*
# would pass a Tier 2 change whose spec.md is still the untouched scaffold — the exact "looks done,
# is empty" failure this process keeps hitting elsewhere. Two or more surviving prompt lines means
# nobody has written it yet; prose almost never opens consecutive lines with '<'.
PROMPT_RE = re.compile(r"^<[^>]", re.M)
# A conflict marker as git writes it, a whole line: never a run of the signs quoted mid-line,
# as a check like this one, or a register naming it, holds.
CONFLICT_MARKER_RE = re.compile(r"^(?:<{7} |={7}$|>{7} )", re.M)
UNFILLED_THRESHOLD = 2
# .sdlc/work/inbox.md, the register of change requests: "## [2026-10-25-3] [idea] Some title",
# its id (the date it came in and a count) then its tag. Every entry is a seed, and its tag is its
# kind: `[idea]`, `[bug]` or `[nit]`, with `[building]` the tag older versions wrote on an idea a
# change was building (an open change's `idea:` line marks it now). Any other tag reads as an idea,
# `[seed]` (what ideas were tagged before) for good.
ENTRY_RE = re.compile(r"^##\s*\[(\d{4}-\d{2}-\d{2})-(\d+)\]\s*\[([^\]]+)\]\s*(.+)$")
# A heading from before ids, `[2026-10-17]` with no count, read for good where history is: an
# older intent's `idea:` may hold a whole heading (`_seed_title`). Never an entry.
OLD_HEADING_RE = re.compile(r"^##\s*\[\d{4}-\d{2}-\d{2}(?:-\d+)?\]\s*\[[^\]]+\]\s*(.+)$")
# The facts an entry holds as body lines, `Key: value`, read as text, the first of each kept. A
# seed that waits on others has `After: "Some title", "Another"`, the titles quoted as a
# milestone's `Groups:` line has them, and status holds it back while one is still open; `Issue:`
# names the tracker issues it was filed from, `#12, #15`, the first the others' parent; `Theme:`
# groups any entry with others and `Priority:` ranks an idea or a bug; the rest are a bug's or a
# nit's own.
BODY_KEYS = (
    "After", "Severity", "Paths", "Introduced by", "Theme", "Cost", "Value", "Raised by", "Issue",
    "Priority",
)  # fmt: skip
BODY_RE = re.compile(rf"^({'|'.join(BODY_KEYS)}):\s*(.+)$")
# A reference to an entry, on an `idea:`, `fixes:`, `After:` or `Groups:` line, is its id, written
# bare, or its title, quoted. Titles are read for good: the intents in history name seeds by them.
ENTRY_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d+$")
ENTRY_ID_TOKEN_RE = re.compile(r"(?<![\w-])\d{4}-\d{2}-\d{2}-\d+(?![\w-])")
REF_RE = re.compile(rf'"([^"]+)"|({ENTRY_ID_TOKEN_RE.pattern})')
# A nit is a `[nit]` entry: a finding ship approved unfixed, with `Theme:`, `Paths:`, `Cost:`,
# `Value:` and `Raised by: NNN-slug (pass)` lines. Ship writes and retires them, intent and spec
# offer them, retro counts them; the process doc's rubric says what each cost and value means. High
# value is never a nit, and L cost is an idea, so neither appears here.
NIT_RAISED_RE = re.compile(r"^(\d{3,}-[a-z0-9][a-z0-9-]*)\s*(?:\(([^)]*)\))?\s*$")
NIT_COSTS = ("S", "M")
NIT_VALUES = ("med", "low")
# notes.md is free-form, with one rule: anything left undone is an unticked `- [ ]` line.
# /sdlc:ship carries each one to a .sdlc/work/inbox.md seed or drops it with a reason, ticking it
# as it goes, and `ship` refuses while one is still unticked, so nothing lands on main with a
# question nobody answered.
OPEN_ITEM_RE = re.compile(r"^\s*[-*] \[ \] (.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# The plugin's own files, resolved from this one so they are found whether the plugin is loaded in
# place or from the plugin cache. Its templates are a default: the section structure a stage owes,
# with prompts that assume nothing about what the host builds. A host that wants its own prompts
# puts a file of the same name in `.sdlc/templates/`, and that one wins (`template_path`).
PLUGIN_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = PLUGIN_DIR / "templates"
DEFAULTS_DIR = PLUGIN_DIR / "defaults"
# The plugin's process and review guides, read in place and never copied: a host's doc holds only
# its answers, each block standing in for the guide's of the same key or read after its parent's.
GUIDE_DIR = PLUGIN_DIR / "guide"
GUIDES = {"process": "process.md", "review": "review.md"}
# The register's name, and the one it had before 1.2.0, which only readers of history still name.
INBOX = "inbox.md"
OLD_INBOX = "ideas.md"

# Everything host-specific lives in `.sdlc/config.toml`. The skills are prose and can't import
# anything, so `config` is the one door: they run it and read the JSON, rather than each one
# naming the host's tools. Every key is optional. A command left unset is null, and the skill
# says it has nothing to run rather than guessing one.
HOST_DIR = ".sdlc"
CONFIG_KEYS: dict[str, dict[str, object]] = {
    "commands": {
        "check": None,  # the gate /sdlc:ship runs on this diff, pass or fail
        "build": None,  # a slower gate /sdlc:ship runs when a changed path matches build_when
        "build_when": None,  # a regex over the changed paths
        "scan": None,  # drift across the whole repo, run by /sdlc:health: findings, not a pass
        "worktree_setup": None,  # after `new --worktree`, in the main checkout; {worktree}, {main}
        "close_list": None,  # read-only: what a closed change left behind; {suffix}
        # The command that removes it; {id}. Handed to the human, or, with close_cleanup_runs,
        # run by close itself as its last step, behind its question. Never run by a skill.
        "close_cleanup": None,
        "close_cleanup_runs": False,
    },
    # The process's own docs live in .sdlc/ beside its config, leaving docs/ to the host.
    "docs": {
        "process": ".sdlc/SDLC.md",  # the tier table, the stages, the gates
        "review": ".sdlc/REVIEW.md",  # the review passes /sdlc:ship works through
        # The host's invariants, which /sdlc:spec designs inside. AGENTS.md when there is no
        # CLAUDE.md and the host hasn't named one (`load_config`).
        "policy": "CLAUDE.md",
        "read_before_design": [],  # further docs /sdlc:spec reads first
        # What gives a session its context, which /sdlc:ship checks every diff against. A
        # CLAUDE.md or AGENTS.md above a changed path joins these on its own (`context`).
        "context": ["CLAUDE.md", ".claude/CLAUDE.md", "AGENTS.md"],
        "explore": None,  # a skill or command for looking at the system itself
        # What each scan finding means and its default response tier, which /sdlc:health
        # routes by. Off while the file doesn't exist.
        "health": ".sdlc/HEALTH.md",
        # Goals, milestones and the next major release, which /sdlc:retro rewrites each run.
        "direction": ".sdlc/DIRECTION.md",
        # Which issue fields the host fills, and where each one's values come from. Off while the
        # file doesn't exist.
        "project": ".sdlc/PROJECT.md",
        # Who the product is for and the outcomes it is after, by id, which every intent then
        # names in `serves:` and /sdlc:retro scores. Off while the file doesn't exist.
        "product": ".sdlc/PRODUCT.md",
    },
    # Where /sdlc:close mirrors a shipped change's folder before removing it from main. History is
    # the copy that counts; the tracker is where people read it.
    "archive": {
        # A tracker module in scripts/trackers/ (github, command), or none. It decides where a
        # change's number comes from: GitHub's issue, opened by /sdlc:intent, or the counter.
        # None until setup says otherwise: numbered locally, offline, mirrored nowhere.
        "target": "none",
        "command": None,  # target = command: archives {dir} ({id}, {slug}, {sha}); prints where
    },
    # The release loop, after a batch of closed changes: /sdlc:release bumps, commits and tags
    # locally, /sdlc:publish pushes and delivers. Off until `version_files` names somewhere the
    # version lives: nothing is bumped on a guess.
    "release": {
        "version_files": [],  # each holds one `version` line, edited in place; they must agree
        "tag": "v{version}",  # the release tag, and the next release's boundary
        "changelog": None,  # a file the notes are added to the top of, in the release commit
        # Run by /sdlc:release after the bump, before the commit, which takes the tracked files it
        # changes too: a lock file regenerated from the new version. {version}, {tag}
        "after_bump": None,
        # Run by /sdlc:release after `after_bump`, before the commit, to build what
        # /sdlc:publish will upload, into untracked or ignored paths only: its output is shown
        # at publish's approval. {version}, {tag}
        "prepare": None,
        "remote": "origin",  # where publish, close and release (`git.push`) push main and the tag
        "publish": None,  # run by /sdlc:publish after the push; {version}, {tag}
        # The shims the host keeps and the version that removes each, which release refuses to
        # cut while one is due. Off while the file doesn't exist.
        "deprecations": ".sdlc/deprecations.toml",
        # When `status` says a release is due, rather than only listing what's unreleased: this
        # many changes of impact minor or higher, or the oldest unreleased close this many days
        # old. A major change is always due. 0 turns that rule off.
        "due_after_changes": 5,
        "due_after_days": 14,
    },
    # When `status` says a retrospective is due. A major release always makes one due.
    "retro": {
        "after_releases": 2,  # release tags since the last retrospective; 0 turns the count off
        # Host commands printing what users did with the product, run by `retro` only while a
        # product doc exists, from the repo root. Counts and summaries, never personal data.
        "evidence": [],
        # What the architecture pass reads besides git: host commands printing measures only a
        # language can tell (complexity, dependency cycles), run by `retro` from the repo root.
        "indicators": [],
        # Host commands each printing a JUnit XML report of the test suite on stdout (run it, `cat`
        # a report the gate left, fetch CI's), run by `retro` from the repo root: the run times
        # the pruning pass reads. The format, never the runner, is the plugin's.
        "test_times": [],
        # The paths that are tests, and docs, when the conventions (`scripts/indicators.py`)
        # misread the host's layout: `dir/` prefixes or globs. Unset, the conventions.
        "test_paths": [],
        "doc_paths": [],
    },
    # What /sdlc:close records about a change, as trailers on its Close commit (scripts/metrics.py).
    "metrics": {
        "transcripts": True,  # read this repo's Claude Code transcripts, for numbers only
        "idle_minutes": 30,  # a wait longer than this is the person away, not answering
        # The stops beyond a change's gates its person should expect: each change's target is the
        # gates its tier and way of running pass, plus this.
        "stop_allowance": 1,
    },
    "review": {
        # Paths whose changes always get /sdlc:ship's deep review: the build check whatever
        # `build_when` says, a fresh-context reviewer, and the paths named in its question.
        "sensitive": [],
        # Paths a revert doesn't undo (data, a published artifact, what setup copies into hosts),
        # for which ship's commit says how to recover. Both: `dir/` prefixes or fnmatch globs.
        "irreversible": [],
    },
    # The branch every change starts from and lands on, which release tags and publish pushes.
    # Unset, it is `main` when there is one, else the branch `origin/HEAD` names (`_resolve_trunk`).
    "git": {
        "base": None,
        # Whether a session's commits and pull requests name the agent. Unset, setup asks and
        # writes nothing; `false` has setup write `ATTRIBUTION_OFF` into the shared settings;
        # `true` keeps the harness's own lines, and nothing is written.
        "attribution": None,
        # The steps that push the base branch to `release.remote`, each behind the question it
        # already asks: "close" (after its Close commit) and "release" (with the tag). Unset, both
        # where `archive.target` is github, so a closed change's issue closes as close ends, and
        # none elsewhere (`_resolve_docs`); `[]` leaves every push to /sdlc:publish.
        "push": None,
        # `status` and close's report suggest a push once this many closed changes sit on the base
        # branch and not on the remote; 0 turns the nudge off.
        "nudge_after_changes": 1,
    },
}
# Each tracker is a module in scripts/trackers/, so adding one adds a target. GitHub first, as the
# default; `none` is no tracker at all.
TRACKER_DIR = PLUGIN_DIR / "scripts" / "trackers"
ARCHIVE_TARGETS = (
    *sorted(
        (p.stem for p in TRACKER_DIR.glob("*.py") if not p.stem.startswith("_")),
        key=lambda s: (s != "github", s),
    ),
    "none",
)
# The [docs] keys that name a file, as opposed to `explore`, which names a tool.
DOC_FILES = ("process", "review", "policy", "health", "direction", "project", "product")
# The issue fields a project doc can turn on, and the one that holds a single value.
PROJECT_FIELDS = ("milestone", "project", "assignees")
SINGLE_FIELDS = ("milestone",)
# Templates `config` names besides the change artifacts: the direction doc /sdlc:retro drafts, the
# layout of a change's tracker issue, and the files a skill starts when a change first needs one:
# `.sdlc/work/inbox.md`, a change's `notes.md`, its `checks.md` and its `findings.md`; and the
# section release adds to `release.changelog`.
DOC_TEMPLATES = (
    "direction.md",
    "issue.md",
    INBOX,
    "notes.md",
    "checks.md",
    "findings.md",
    "retro.md",
    "changelog.md",
)
# The [docs] keys that hold a list of paths.
DOC_LISTS = ("read_before_design", "context")
# Every key, in any section, that holds a list of paths, or of commands, rather than a string.
COMMAND_LISTS = ("evidence", "indicators", "test_times")
REVIEW_LISTS = ("sensitive", "irreversible")
KIND_LISTS = ("test_paths", "doc_paths")
LIST_KEYS = (*DOC_LISTS, "version_files", *COMMAND_LISTS, *REVIEW_LISTS, *KIND_LISTS)
# Every key that holds a whole number, with its least value where that isn't 0.
INT_KEYS = (
    "after_releases", "due_after_changes", "due_after_days", "idle_minutes", "stop_allowance",
    "nudge_after_changes",
)  # fmt: skip
INT_MIN = {"idle_minutes": 1}
# Every key that holds true or false.
BOOL_KEYS = ("transcripts", "attribution", "close_cleanup_runs")
# The steps `git.push` may name.
PUSH_POINTS = ("close", "release")


def load_config(root: Path) -> tuple[dict, list[str], bool]:
    """The host's settings over the defaults, the warnings, and whether the file parsed.

    An unknown key is a warning rather than ignored: `buld = ...` would otherwise leave a host
    believing it had configured a build check that never runs."""
    cfg = {section: dict(keys) for section, keys in CONFIG_KEYS.items()}
    path = root / HOST_DIR / "config.toml"
    if not path.is_file():
        return _resolve_docs(root, cfg, set()), [], True
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        return _resolve_docs(root, cfg, set()), [f"{HOST_DIR}/config.toml won't parse: {e}"], False
    warnings = _apply_config(cfg, data)
    if cfg["archive"]["target"] not in ARCHIVE_TARGETS:
        warnings.append(f"archive.target must be one of {'|'.join(ARCHIVE_TARGETS)}")
    if cfg["commands"]["close_cleanup_runs"] and not cfg["commands"]["close_cleanup"]:
        warnings.append("commands.close_cleanup_runs is on with no close_cleanup: nothing runs")
    docs = data.get("docs")
    return _resolve_docs(root, cfg, set(docs) if isinstance(docs, dict) else set()), warnings, True


def _apply_config(cfg: dict, data: dict) -> list[str]:
    """Set each of `data`'s keys in `cfg` that `CONFIG_KEYS` knows and whose value fits, and the
    warnings for the rest: `load_config()`'s reading, and `_config_at()`'s."""
    warnings = []
    for section, values in data.items():
        if section not in CONFIG_KEYS or not isinstance(values, dict):
            warnings.append(f"unknown section [{section}]")
            continue
        for key, value in values.items():
            if key not in CONFIG_KEYS[section]:
                warnings.append(f"unknown key {section}.{key}")
            elif key in LIST_KEYS:
                if isinstance(value, list) and all(isinstance(v, str) for v in value):
                    cfg[section][key] = value
                else:
                    what = "commands" if key in COMMAND_LISTS else "paths"
                    warnings.append(f"{section}.{key} must be a list of {what}")
            elif key in INT_KEYS:
                least = INT_MIN.get(key, 0)
                if isinstance(value, int) and not isinstance(value, bool) and value >= least:
                    cfg[section][key] = value
                else:
                    warnings.append(f"{section}.{key} must be a whole number, {least} or more")
            elif key == "push":
                if isinstance(value, list) and all(v in PUSH_POINTS for v in value):
                    cfg[section][key] = value
                else:
                    warnings.append(f"git.push must be a list of {' and '.join(PUSH_POINTS)}")
            elif key in BOOL_KEYS:
                if isinstance(value, bool):
                    cfg[section][key] = value
                else:
                    warnings.append(f"{section}.{key} must be true or false")
            elif isinstance(value, str):
                cfg[section][key] = value
            else:
                warnings.append(f"{section}.{key} must be a string")
    return warnings


def _config_at(home: Path, ref: str) -> dict | None:
    """The settings `.sdlc/config.toml` held at `ref`, over the defaults, its paths left as
    written: what close reads its cleanup from, so a change can't turn on its own. A ref with no
    config is the defaults; None when the ref is missing or its config won't parse."""
    if _git(home, "rev-parse", "--verify", "-q", ref) is None:
        return None
    cfg = {section: dict(keys) for section, keys in CONFIG_KEYS.items()}
    text = _git(home, "show", f"{ref}:{HOST_DIR}/config.toml")
    if text is None:
        return cfg
    try:
        _apply_config(cfg, tomllib.loads(text))
    except tomllib.TOMLDecodeError:
        return None
    return cfg


def _resolve_docs(root: Path, cfg: dict, chosen: set[str]) -> dict:
    """With no CLAUDE.md, the policy is an AGENTS.md if there is one, unless the host set
    `docs.policy` (`chosen`). Every reader takes `cfg["docs"]`, so this is the one place it is
    decided. The base branch is resolved here too, for the same reason (`_resolve_trunk`), and
    `git.push`'s default, which follows the tracker."""
    agents_only = not (root / "CLAUDE.md").is_file() and (root / "AGENTS.md").is_file()
    if "policy" not in chosen and agents_only:
        cfg["docs"]["policy"] = "AGENTS.md"
    cfg["git"]["base"], cfg["git"]["base_source"] = _resolve_trunk(root, cfg["git"]["base"])
    if cfg["git"]["push"] is None:
        cfg["git"]["push"] = list(PUSH_POINTS) if cfg["archive"]["target"] == "github" else []
    return cfg


def _resolve_trunk(root: Path, given: str | None) -> tuple[str | None, str]:
    """The base branch and where it came from: `git.base` as set (`config`); else `main` when the
    repo has one, else the local branch `origin/HEAD` names (`detected`); else (None, `unset`).
    Never the checkout's current branch or `init.defaultBranch`, which describe one machine, and
    never GitHub's default branch, which would be a network call from core. A detected branch is
    cached per checkout, since `load_config` runs many times in one command; `unset` never is, as
    the branch can still be made."""
    if given:
        return given, "config"
    key = root.resolve()
    if key in _TRUNKS:
        return _TRUNKS[key], "detected"
    if _git(root, "rev-parse", "--verify", "-q", f"refs/heads/{DEFAULT_TRUNK}") is not None:
        _TRUNKS[key] = DEFAULT_TRUNK
        return DEFAULT_TRUNK, "detected"
    remote = _git(root, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD") or ""
    name = remote.removeprefix("origin/")
    named = remote.startswith("origin/") and name
    if named and _git(root, "rev-parse", "--verify", "-q", f"refs/heads/{name}") is not None:
        _TRUNKS[key] = name
        return name, "detected"
    return None, "unset"


_TRUNKS: dict[Path, str] = {}


# The one name the plugin assumes, and only when it exists: every other use of the base branch
# reads `git.base` as resolved.
DEFAULT_TRUNK = "main"
TRUNK_KEY = f"[git] base in {HOST_DIR}/config.toml"


def trunk_refusal(home: Path, trunk: str | None, source: str = "config") -> str | None:
    """Why a command that moves or reads the base branch can't run here, or None. Every command
    that writes asks this before anything else, so nothing is half made on a branch that isn't
    there."""
    if not trunk:
        return f"no base branch: there is no main and origin/HEAD names none; set {TRUNK_KEY}"
    if _git(home, "rev-parse", "--verify", "-q", f"refs/heads/{trunk}") is None:
        return f"base branch {trunk!r} doesn't exist here (git.base, {source}); set {TRUNK_KEY}"
    return None


def template_path(root: Path, name: str) -> tuple[Path, str]:
    """The template `new` scaffolds `name` from: the host's, else the plugin's."""
    host = root / HOST_DIR / "templates" / name
    return (host, "host") if host.is_file() else (TEMPLATE_DIR / name, "plugin")


def register_path(work: Path) -> Path:
    """The register in this change folder, the one file every reader and writer names."""
    return work / INBOX


def doc_path(root: Path, key: str, rel: str) -> dict:
    """Where a host doc is, and whether it exists. The process and review docs also name the
    plugin's guide to read before them (`guide`) and their `layout`, always `answers`. Only
    the review stands in for a missing doc, with the guide alone: a ship with no review passes to
    work through isn't a ship, while a missing policy doc is a fact the skill should say out loud
    rather than paper over with a generic one."""
    guide = str(GUIDE_DIR / GUIDES[key]) if key in GUIDES else None
    if (root / rel).is_file():
        found = {"path": rel, "exists": True, "source": "host"}
        if guide:
            found.update(layout="answers", guide=guide)
        return found
    if key == "review":
        return {
            "path": guide,
            "exists": True,
            "source": "plugin",
            "layout": "answers",
            "guide": None,
        }
    found = {"path": rel, "exists": False, "source": "host"}
    return found | ({"layout": "answers", "guide": guide} if guide else {})


def project_doc(root: Path, cfg: dict) -> tuple[dict[str, dict], list[str]]:
    """The issue fields the project doc turns on, each with its lookup, and what's wrong with it.

    Its frontmatter names each field with `tracker` (the tracker's own list), a list of the values
    allowed, or any other text, a host command printing one value per line. No file, or a field
    left out or empty, is off: the issue gets the plugin's labels and its opener, nothing more."""
    rel = cfg["docs"]["project"]
    path = root / rel if rel else None
    if path is None or not path.is_file():
        return {}, []
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or text.find("\n---", 4) == -1:
        return {}, [f"docs.project: {rel} has no frontmatter, so no issue field is on"]
    keys = re.findall(r"^([A-Za-z_][\w-]*):", text[4 : text.find("\n---", 4)], re.M)
    warnings = [
        f"docs.project: unknown field {k!r}; the fields are {', '.join(PROJECT_FIELDS)}"
        for k in keys
        if k not in PROJECT_FIELDS
    ]
    fields: dict[str, dict] = {}
    for name in PROJECT_FIELDS:
        entry = _frontmatter_entry(text, name)
        if entry is None or not entry[1]:
            continue
        listed, values = entry
        if listed:
            fields[name] = {"lookup": "list", "values": values}
        elif values == ["tracker"]:
            fields[name] = {"lookup": "tracker"}
        else:
            fields[name] = {"lookup": "command", "command": values[0]}
    return fields, warnings


def product_doc(root: Path, cfg: dict) -> dict | None:
    """The product doc's outcomes (`product_items()`), or None while it doesn't exist, which is
    off: no intent names an outcome, and the retrospective has no product pass."""
    rel = cfg["docs"]["product"]
    path = root / rel if rel else None
    if path is None or not path.is_file():
        return None
    return product_items(path.read_text(encoding="utf-8"))


FACTORY_PLUGIN = "sdlc-factory@"


def factory_enabled(home: Path) -> tuple[bool, str | None]:
    """Whether `sdlc-factory` is enabled for the repo whose main checkout is `home`, and the
    scope that says so: Claude Code's own `enabledPlugins`, read from the most specific file
    first (`local`, `project`, `user`), the first naming the factory, from any marketplace,
    deciding. Files only: nothing run, nothing of the factory's read, and a missing or unreadable
    file is skipped, since a wrong answer only hides intent's factory option."""
    files = (
        ("local", home / ".claude" / "settings.local.json"),
        ("project", home / ".claude" / "settings.json"),
        ("user", Path.home() / ".claude" / "settings.json"),
    )
    for scope, path in files:
        try:
            plugins = json.loads(path.read_text(encoding="utf-8")).get("enabledPlugins")
        except (OSError, ValueError, AttributeError):
            continue
        if not isinstance(plugins, dict):
            continue
        named = [v for k, v in plugins.items() if str(k).startswith(FACTORY_PLUGIN)]
        if named:
            return named[0] is True, scope
    return False, None


def cmd_config(root: Path) -> int:
    """The resolved settings as JSON, for every skill's Step 0. Writes nothing; exit 1 only when
    `.sdlc/config.toml` exists and won't parse, because then nothing it says can be trusted."""
    cfg, warnings, parsed = load_config(root)
    docs: dict[str, object] = {"explore": cfg["docs"]["explore"]}
    for key in DOC_FILES:
        rel = cfg["docs"][key]
        docs[key] = doc_path(root, key, rel) if rel else None
    docs["read_before_design"] = [
        doc_path(root, "read_before_design", rel) for rel in cfg["docs"]["read_before_design"]
    ]
    # Not warned about: the defaults name two places a CLAUDE.md can be, and a repo has one.
    docs["context"] = [doc_path(root, "context", rel) for rel in cfg["docs"]["context"]]
    # Not the direction doc, which the first retrospective writes, nor the project, product and
    # health docs, which are off while they don't exist.
    optional = ("direction", "project", "product", "health")
    for key in (*(k for k in DOC_FILES if k not in optional), "read_before_design"):
        entries = docs[key] if isinstance(docs[key], list) else [docs[key]]
        warnings += [
            f"docs.{key}: {d['path']} doesn't exist" for d in entries if d and not d["exists"]
        ]
    fields, problems = project_doc(root, cfg)
    if docs["project"]:
        docs["project"]["fields"] = fields
    warnings += problems
    # The outcomes an intent may name in `serves:`: the open ones, and nothing else.
    product = product_doc(root, cfg)
    if docs["product"]:
        docs["product"]["outcomes"] = [
            {"id": i["id"], "name": i["name"], "title": i["title"]}
            for i in (product or {"items": []})["items"]
            if i["status"] == "open"
        ]
    warnings += [f"docs.product: {p}" for p in (product or {"problems": []})["problems"]]
    if cfg["retro"]["evidence"] and product is None:
        warnings.append(
            "retro.evidence is set, but it runs only with a product doc "
            f"({cfg['docs']['product'] or 'docs.product is unset'})"
        )
    templates = {}
    for name in (*TIER_ARTIFACTS[2], *DOC_TEMPLATES):
        path, source = template_path(root, name)
        templates[name] = {"path": str(path), "source": source}
    home = main_root(root)
    ignored = work_ignored(root)
    if ignored:
        warnings.append(ignored_message(root))
    if not cfg["git"]["base"]:
        warnings.append(f"git.base: {trunk_refusal(home, None)}")
    cfg_file = root / HOST_DIR / "config.toml"
    out = {
        "config_file": f"{HOST_DIR}/config.toml" if cfg_file.is_file() else None,
        # This checkout's: a change's folder is committed on its branch, in its worktree.
        # The file entries go in, `.sdlc/work/inbox.md`, named so a skill never starts a second
        # register beside the one being read.
        "work": {
            "dir": str(work_dir(root)),
            "rel": work_rel(root),
            "ignored": ignored,
            "register": str(register_path(work_dir(root))),
        },
        "commands": cfg["commands"],
        "docs": docs,
        # Whether close can archive here, and why not when it can't; no network is touched.
        "archive": {
            **cfg["archive"],
            "unavailable": archive_unavailable(home, cfg),
            "ids_from": ids_mode(home, cfg),
        },
        "release": cfg["release"],
        "retro": cfg["retro"],
        "metrics": cfg["metrics"],
        # This checkout's lists; ship's `risk` reads the base branch's, which a change can't edit.
        "review": cfg["review"],
        "git": cfg["git"],
        # Whether intent may offer to hand the change to the factory: settings files alone.
        "factory": dict(zip(("enabled", "scope"), factory_enabled(home), strict=True)),
        "templates": templates,
        "warnings": warnings,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if parsed else 1


@command("config", "the host's .sdlc/config.toml, resolved, as JSON; writes nothing")
def cli_config(root: Path, home: Path, args) -> int:
    return cmd_config(root)


def repo_root() -> Path:
    """The git repo containing the current directory.

    `git rev-parse` rather than walking up looking for a marker file: the host repo decides its own
    layout, and this plugin shouldn't assert that some file must exist at the root to be found.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            encoding="utf-8",
            check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repo, or no git. Fall back to cwd so `status` can still say something useful
        # instead of a traceback; `ship` will fail later on its own terms.
        return Path.cwd()


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
    """The argv that runs a host's command, or a check's, through `sh -c` on every platform:
    `/bin/sh`, as `shell=True` uses, and on Windows the `sh` on PATH, Git for Windows', never
    `cmd.exe`, so one config means one thing everywhere. Raises OSError when Windows has none.
    `trackers/command.py` keeps a copy, pinned to this one by a test."""
    if os.name != "nt":
        return ["/bin/sh", "-c", command]
    found = shutil.which("sh")
    if found is None:
        raise OSError("no sh on PATH: install Git for Windows, whose sh runs a host's commands")
    return [found, "-c", command]


_MAIN_ROOTS: dict[Path, Path] = {}


def main_root(root: Path) -> Path:
    """The main checkout, whichever worktree `root` is. Its git dir is the common one, so the
    parent of `--git-common-dir` is the same answer from the main checkout and from every
    worktree. Falls back to `root` outside git, uncached, since `git init` can still make it one.
    Cached per checkout: a checkout's main checkout never changes while a command runs."""
    key = root.resolve()
    if key in _MAIN_ROOTS:
        return _MAIN_ROOTS[key]
    out = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not out:
        return root
    _MAIN_ROOTS[key] = Path(out).parent
    return _MAIN_ROOTS[key]


def ignored_message(home: Path) -> str:
    rel = work_rel(home)
    return (
        f"{rel}/ is gitignored: remove the line that ignores it from .gitignore. A change's "
        "artifacts are committed on its branch, and `git add` skips an ignored folder"
    )


def work_ignored(home: Path) -> bool | None:
    """Whether git ignores the change folder here; None outside git. With the slash, because
    `check-ignore` only matches a directory pattern against a path it is told is a directory, and
    the folder needn't exist yet."""
    try:
        code = subprocess.run(
            ["git", "-C", str(home), "check-ignore", "-q", f"{work_rel(home)}/"],
            capture_output=True,
        ).returncode
    except FileNotFoundError:
        return None
    return {0: True, 1: False}.get(code)


def _used(root: Path) -> list[tuple[str, str]]:
    """(id, slug) of every change any checkout holds (`change_dirs`): what `new` checks a slug
    against, and one of what `next_id` counts."""
    return [m.groups() for p in change_dirs(root) if (m := DIR_RE.match(p.name))]


def slugify(text: str) -> str:
    """kebab-case ASCII slug. Mirrors the host-repo convention `NNN-slug`."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return re.sub(r"-{2,}", "-", text)


# The change folder, relative to a checkout's root. `.sdlc/work`, beside the rest of what the
# plugin keeps, so adopting it adds no top-level folder.
WORK = ".sdlc/work"
# Where it was before 1.4.0, as history still holds it. Only readers of history name it, for
# good: a repo's changes from before the move keep their numbers and their `Close` commits.
HISTORY_WORK = "work"
# A path in a change's diff that is a change's own folder, under either name: history keeps both.
CHANGE_FOLDERS = (f"{WORK}/", f"{HISTORY_WORK}/")


def work_rel(root: Path) -> str:
    """The change folder of `root`'s repo, relative to a checkout's root: `WORK`. Every path to it,
    on disk and in git, is built from this, so nothing names the folder twice."""
    return WORK


def work_dir(root: Path) -> Path:
    return root / work_rel(root)


def checkout_of(folder: Path) -> Path:
    """The checkout a change folder `<checkout>/<WORK or HISTORY_WORK>/NNN-slug` sits in, read from
    its path alone, so it holds outside git too, and for a path history or a transcript holds."""
    parent = folder.parent
    if parent.name == Path(WORK).name and parent.parent.name == Path(WORK).parent.name:
        return parent.parent.parent
    return parent.parent


def _number(name: str) -> int:
    m = DIR_RE.match(name)
    return int(m.group(1)) if m else -1


def names_change(name: str, ident: str) -> bool:
    """Whether `ident`, as a human types it, names the change folder or branch `name`: `42`,
    `042`, `042-slug` and `042-slug` all name `042-slug`."""
    if ident.isdigit():
        return _number(name) == int(ident)
    return name == ident or name.startswith(f"{ident}-")


# The last id handed out, as the bare number, in `.sdlc/last-id`. "Last", not "next": the meaning
# is in the name, so nobody has to guess which side of the off-by-one the file is on. It is
# committed, so a fresh clone carries on from it, and removing a change's folder from
# `.sdlc/work/` (which close does once it is archived) can't reset the numbering. `new --worktree`
# writes it in the change's own worktree, so the bump reaches main with the change's commit: the
# main checkout is never left dirty, which close would refuse.
LAST_ID = "last-id"


def last_id_path(home: Path) -> Path:
    return state_path(home, LAST_ID)


def change_dirs(root: Path) -> list[Path]:
    """Every change folder this checkout can see: its own `.sdlc/work/`, the main checkout's, and
    each change worktree's own folder, `.sdlc/work/<branch>/`, one stopped mid-rebase included
    (`_change_trees()`). Only that one from a worktree: it also holds whatever `main` had when it
    was made, and those copies would read as the same change twice. A name found twice counts
    once, the copy on its own branch winning. Skips non-conforming names."""
    found: dict[str, Path] = {}
    for base in (work_dir(main_root(root)), work_dir(root)):
        if base.is_dir():
            found |= {p.name: p for p in base.iterdir() if p.is_dir() and DIR_RE.match(p.name)}
    for tree, branch in _change_trees(root):
        own = work_dir(tree) / branch
        if own.is_dir():
            found[branch] = own
    # By number, not by name: "1203-x" sorts before "142-y" as text.
    return sorted(found.values(), key=lambda p: (_number(p.name), p.name))


def _shown(path: Path, root: Path) -> str:
    """`path` relative to `root` when it is inside it, else absolute: a sibling worktree's."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


# `load_change()`'s product doc when the caller hasn't read it: None is a real answer (no doc).
_READ = object()


def load_change(
    path: Path, root: Path, project: dict[str, dict] | None = None, product: object = _READ
) -> dict:
    """One change folder as a record. `errors` collects anything malformed rather than raising —
    a broken intent should show up in the report, not crash it."""
    m = DIR_RE.match(path.name)
    rec: dict = {
        "id": m.group(1),
        "slug": m.group(2),
        "dir": _shown(path, root),
        "tier": None,
        "stage": None,
        "created": "",
        "updated": "",
        "title": "",
        "idea": "",
        "ideas": [],
        "impact": "",
        "artifacts": sorted(p.name for p in path.glob("*.md")),
        "open_questions": 0,
        "depends_on": [],
        "reworks": [],
        "fields": {},
        "serves": None,
        "fixes": [],
        "closes": [],
        "errors": [],
    }
    intent = path / "intent.md"
    if not intent.is_file():
        rec["errors"].append("no intent.md")
        return rec
    try:
        post = frontmatter.load(intent)
    except Exception as e:  # malformed YAML
        rec["errors"].append(f"intent.md frontmatter won't parse: {e}")
        return rec

    tier = post.get("tier")
    if tier not in TIER_ARTIFACTS:
        rec["errors"].append(f"tier must be 1 or 2, got {tier!r}")
    else:
        rec["tier"] = int(tier)

    stage = str(post.get("stage") or "")
    if stage not in STAGES:
        rec["errors"].append(f"stage must be one of {'|'.join(STAGES)}, got {stage!r}")
    else:
        rec["stage"] = stage

    for field in ("created", "updated"):
        rec[field] = str(post.get(field) or "")
        if not rec[field]:
            rec["errors"].append(f"missing {field}:")

    rec["ideas"] = intent_ideas(intent.read_text(encoding="utf-8"))
    rec["idea"] = (rec["ideas"] or [""])[0]
    # Empty until /sdlc:ship settles it.
    rec["impact"] = str(post.get("impact") or "")
    if rec["impact"] and rec["impact"] not in IMPACTS:
        rec["errors"].append(f"impact must be one of {'|'.join(IMPACTS)}, got {rec['impact']!r}")
    for line in (post.content or "").splitlines():
        if line.startswith("# "):
            rec["title"] = line[2:].strip()
            break
    rec["open_questions"] = open_questions(post.content or "")
    # The changes this one waits on, by id; a tracker mirrors them (GitHub: blocked-by).
    for dep in depends_on(intent.read_text(encoding="utf-8")):
        n = int(dep) if dep.isdigit() else None
        if n is None:
            rec["errors"].append(f"depends_on: {dep!r} isn't a change id")
        elif n == int(m.group(1)):
            rec["errors"].append("depends_on names this change itself")
        else:
            rec["depends_on"].append(n)
    # The earlier changes this one fixes, by id: the rework retro counts. Kept as written, since
    # one may be closed, dropped or open, which `check` settles against history.
    for ident in reworks(intent.read_text(encoding="utf-8")):
        if not ident.isdigit():
            rec["errors"].append(f"reworks: {ident!r} isn't a change id")
        elif int(ident) == int(m.group(1)):
            rec["errors"].append("reworks names this change itself")
        else:
            rec["reworks"].append(ident)
    # The issue fields the project doc turns on, set here and mirrored by the tracker. Checked
    # offline only: a fixed list can be, a tracker's or a command's can't without the network.
    text = intent.read_text(encoding="utf-8")
    if project is None:
        project = project_doc(root, load_config(root)[0])[0]
    for name in PROJECT_FIELDS:
        values = frontmatter_list(text, name)
        if values is None:
            continue
        rec["fields"][name] = values
        field = project.get(name)
        if field is None:
            rec["errors"].append(f"{name}: set, but the project doc doesn't turn it on")
            continue
        if name in SINGLE_FIELDS and len(values) > 1:
            rec["errors"].append(f"{name}: one value, got {len(values)}")
        for value in values if field["lookup"] == "list" else []:
            if value not in field["values"]:
                rec["errors"].append(f"{name}: {value!r} isn't one the project doc lists")
    if product is _READ:
        checkout = checkout_of(path)
        product = product_doc(checkout, load_config(checkout)[0])
    rec["serves"] = frontmatter_list(text, "serves")
    rec["errors"] += serves_errors(rec["serves"], product, rec["stage"])
    # The bugs a change fixes, by id, each an open `[bug]` in its own checkout's register until
    # ship removes it with the fix.
    rec["fixes"] = frontmatter_list(text, "fixes") or []
    if rec["fixes"] and rec["stage"] not in ("shipped", "dropped"):
        open_bugs = {e["id"] for e in inbox_entries(checkout_of(path)) if is_bug(e)}
        for f in rec["fixes"]:
            if not ENTRY_ID_RE.match(f):
                rec["errors"].append(f"fixes: {f!r} isn't an id: name each bug by its YYYY-MM-DD-n")
            elif f not in open_bugs:
                rec["errors"].append(
                    f"fixes: {f!r} isn't a [bug] in "
                    f"{work_rel(root)}/{register_path(path.parent).name}"
                )
    # The tracker issues the change closes when it lands, whatever their kind, by number: those
    # triage attached to it, and those its seed or bug carried on an `Issue:` line.
    for value in frontmatter_list(text, "closes") or []:
        if not value.isdigit():
            rec["errors"].append(f"closes: {value!r} isn't an issue number: write it bare, `12`")
        elif int(value) == int(m.group(1)):
            rec["errors"].append("closes: names this change's own issue")
        else:
            rec["closes"].append(int(value))
    return rec


def serves_errors(serves: list[str] | None, product: dict | None, stage: str | None) -> list[str]:
    """What's wrong with an intent's `serves:` line. With a product doc, every change still being
    worked names the outcomes it serves, or `none`, so "serves nothing" is always a decision. An
    outcome the doc has struck isn't one: a retrospective on main can strike what an open change
    still serves, and `retro` lists those instead."""
    if product is None:
        return ["serves: set, but there is no product doc"] if serves is not None else []
    if serves is None:
        if stage in ("shipped", "dropped"):
            return []
        return ["serves: missing; name the outcomes this serves from the product doc, or none"]
    if not serves:
        return ["serves: empty; name the outcomes this serves from the product doc, or none"]
    if "none" in serves:
        return ["serves: none can't be mixed with outcomes"] if len(serves) > 1 else []
    known = {i["id"] for i in product["items"]}
    return [f"serves: {s!r} isn't an outcome in the product doc" for s in serves if s not in known]


def _outside_quotes(text: str, stop: str) -> list[int]:
    """Where `stop` occurs in `text` outside single or double quotes."""
    found, quote = [], ""
    for i, ch in enumerate(text):
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif text.startswith(stop, i):
            found.append(i)
    return found


def _value(text: str) -> str:
    """One frontmatter value: a trailing ` #` comment dropped, then its quotes."""
    cut = _outside_quotes(text, " #")
    text = (text[: cut[0]] if cut else text).strip()
    return text[1:-1] if len(text) > 1 and text[0] == text[-1] and text[0] in "\"'" else text


def _frontmatter_entry(text: str, key: str) -> tuple[bool, list[str]] | None:
    """(written as a list, its items) for `key:` in `text`'s frontmatter, or None when absent.
    A flow list `[a, "b c"]`, a scalar, or a block list of `- ` lines."""
    if not text.startswith("---\n") or (end := text.find("\n---", 4)) == -1:
        return None
    lines = text[4:end].splitlines()
    for i, line in enumerate(lines):
        if not line.startswith(f"{key}:"):
            continue
        rest = line[len(key) + 1 :]
        cut = _outside_quotes(rest, " #")
        rest = (rest[: cut[0]] if cut else rest).strip()
        if rest.startswith("["):
            inner = rest[1 : rest.rfind("]")] if "]" in rest else rest[1:]
            bounds = [-1, *_outside_quotes(inner, ","), len(inner)]
            parts = [_value(inner[a + 1 : b]) for a, b in zip(bounds, bounds[1:], strict=False)]
            return True, [p for p in parts if p]
        if rest:
            return False, [_value(rest)]
        items = []
        for following in lines[i + 1 :]:
            m = re.match(r"\s*-\s*(.*)$", following)
            if not m:
                break
            if value := _value(m.group(1)):
                items.append(value)
        return bool(items), items
    return None


def frontmatter_list(text: str, key: str) -> list[str] | None:
    """The values on a frontmatter line, as written; None when the key is absent. Read as text,
    not through YAML, which takes a padded id for octal (`012` is 10) and a version for a float
    (`1.10` is 1.1): the plugin's own keys are ids and names, never numbers."""
    entry = _frontmatter_entry(text, key)
    return None if entry is None else entry[1]


def depends_on(text: str) -> list[str]:
    """The ids on an intent's `depends_on:` line: `[003, 012]`, `003`, or a block list."""
    return frontmatter_list(text, "depends_on") or []


def reworks(text: str) -> list[str]:
    """The ids on an intent's `reworks:` line, the earlier changes it fixes, read as
    `depends_on:` is."""
    return frontmatter_list(text, "reworks") or []


def open_questions(body: str) -> int:
    """Bullets under `## Open questions` that aren't struck through. Closing a question means
    striking it and saying how it went (`- ~~Question?~~ Resolved: ...`), as the intent template
    prompts, so one closed in prose alone still counts: read the number as a ceiling."""
    count, inside = 0, False
    for line in body.splitlines():
        if line.startswith("## "):
            inside = line.startswith("## Open questions")
        elif inside and line.startswith("- ") and not line.startswith("- ~~"):
            count += 1
    return count


def is_unfilled(path: Path) -> bool:
    """True if this artifact is still mostly the scaffold it was created from."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return len(PROMPT_RE.findall(text)) >= UNFILLED_THRESHOLD


def open_items(folder: Path) -> list[dict]:
    """The unticked `- [ ]` lines in a change's notes.md, with their line numbers. A marker inside
    a fenced code block is an example of the convention, not an item, so fences are skipped."""
    path = folder / "notes.md"
    if not path.is_file():
        return []
    out, fenced = [], False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        m = None if fenced else OPEN_ITEM_RE.match(line)
        if m:
            out.append({"file": "notes.md", "line": n, "text": m.group(1)})
    return out


# A change's acceptance checks: each `## ` section of its checks.md, holding one `sh` block that
# exits 0 while the outcome holds. `accept` runs them; it has no allow rule, so a person always
# sees the commands and answers a prompt before they run.
CHECKS = "checks.md"
SH_FENCE_RE = re.compile(r"^\s*(```|~~~)\s*sh\s*$")
CHECK_TIMEOUT = 300  # seconds for one check; a hung one fails rather than holds ship
CHECK_OUTPUT_LINES = 40


def acceptance(folder: Path) -> dict:
    """A change's acceptance checks, in file order, and what's wrong with its checks.md. Never
    raises: an unreadable or malformed file is a problem, and a section with one is left out."""
    path = folder / CHECKS
    out: dict = {"path": CHECKS, "exists": path.is_file(), "checks": [], "problems": []}
    if not out["exists"]:
        return out
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        out["problems"].append(f"{CHECKS} can't be read: {e}")
        return out
    if is_unfilled(path):
        out["problems"].append(f"{CHECKS} is still the template: fill it or delete it")
        return out
    sections: list[tuple[str | None, list[str]]] = [(None, [])]
    fence: list[str] | None = None
    sh = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            if fence is None:
                fence, sh = [], bool(SH_FENCE_RE.match(line))
            else:
                if sh:
                    sections[-1][1].append("\n".join(fence))
                fence = None
            continue
        if fence is not None:
            fence.append(line)
        elif line.startswith("## "):
            sections.append((line[3:].strip(), []))
    if fence is not None:
        out["problems"].append(f"{CHECKS}: a fenced block is never closed")
        return out
    seen: set[str] = set()
    for name, blocks in sections:
        if name is None:
            if blocks:
                out["problems"].append(f"{CHECKS}: an `sh` block above the first `## ` check")
            continue
        wrong = []
        if name in seen:
            wrong.append("its name is used twice")
        if len(blocks) != 1:
            wrong.append(f"holds {len(blocks)} `sh` blocks, not one")
        seen.add(name)
        if wrong:
            out["problems"] += [f"{CHECKS}: ## {name}: {w}" for w in wrong]
            continue
        out["checks"].append({"name": name, "command": blocks[0]})
    return out


# A change's review findings: each `## F<n>. [rank] [pass] title` section of its findings.md, which
# /sdlc:ship writes after every review, a run that stops included, and commits with the change.
# Each holds `Evidence:`, `Class:`, `Disposition:` and, for a dismissal, `Reason:` lines. `ship`
# refuses while one is still `open`; the `Sdlc-Findings` trailer is counted from the file.
FINDINGS = "findings.md"
FINDING_RE = re.compile(r"^##\s+F(\d+)\.\s*\[([^\]]+)\]\s*\[([^\]]+)\]\s*(.+)$")
FINDING_RANKS = {"important": "important", "nit": "nit", "pre-existing": "preexisting"}
FINDING_PASSES = ("correctness", "contract", "cost", "context")
DISMISSALS = ("wrong", "intentional", "minor")
# `fix` is proposed for fixing before the commit, with a `Fix:` line saying the change; like `open`
# it can't be committed, so the trailer counts only the dispositions a landed change can hold.
COUNTED = ("fixed", "recorded", *DISMISSALS)
DISPOSITIONS = ("open", "fix", *COUNTED)
FINDING_KEYS = ("Evidence", "Class", "Disposition", "Reason", "By", "Fix")
# A deep diff's findings.md says, in its note, whether the fresh-context review ran.
FRESH_RE = re.compile(r"^>?\s*Fresh review:\s*(ran|skipped)\b,?\s*(.*)$")
# And, in this plugin's repo, whether a diff that reaches a skill with cases ran them.
CASES_RE = re.compile(r"^>?\s*Skill evals:\s*(ran|skipped)\b,?\s*(.*)$")
# And, for each of ship's passes that applies (`_passes_report()`), whether it ran: `ui` is said
# as two lines, the UI and the UX review.
SECURITY_RE = re.compile(r"^>?\s*Security review:\s*(ran|skipped)\b,?\s*(.*)$")
BEHAVIOUR_RE = re.compile(r"^>?\s*Behaviour check:\s*(ran|skipped)\b,?\s*(.*)$")
UI_RE = re.compile(r"^>?\s*UI review:\s*(ran|skipped)\b,?\s*(.*)$")
UX_RE = re.compile(r"^>?\s*UX review:\s*(ran|skipped)\b,?\s*(.*)$")
PASS_LINES = {"security": SECURITY_RE, "behaviour": BEHAVIOUR_RE, "ui": UI_RE, "ux": UX_RE}
# The behaviour check's evidence, the file's last section: each `$ <command>` line, the tail of
# its output, then `exit: <n>`. Read as evidence, never as a finding.
EVIDENCE_HEADING = "## Evidence"
EVIDENCE_EXIT_RE = re.compile(r"^exit:\s*(-?\d+)\s*$")
# Who raised a finding, when it wasn't ship's own passes: `By: fresh`, the fresh-context reviewer
# a deep diff gets (`agents/reviewer.md`); one of ship's own further passes (`SHIP_PASSES`: its
# security, ui and ux agents, and the behaviour check it runs itself), prefixed so it never
# reads as the factory role of the same word; or a factory reviewer, whose findings `factory.py
# carry` writes. `AGENT_ROLES` is a copy of `factory.py`'s `REVIEWERS`, pinned by a test.
SHIP_PASSES = ("ship-security", "ship-behaviour", "ship-ui", "ship-ux")
AGENT_ROLES = ("code", "security", "test", "behaviour", "ui", "ux")
FINDING_BY = ("fresh", *SHIP_PASSES, *AGENT_ROLES)


def ship_findings(entries: list[dict]) -> list[dict]:
    """The findings ship's own review raised (no `By:`, `By: fresh`, or one of `SHIP_PASSES`),
    never a factory agent's: the ones the `Sdlc-Findings` trailer and `findings`' counts are of,
    so a factory review is never counted as the person's."""
    return [e for e in entries if e.get("by") in (None, "fresh", *SHIP_PASSES)]


def findings_entries(folder: Path) -> dict:
    """A change's review findings, in file order, the ones still `open`, and what's wrong with its
    findings.md. Never raises: an unreadable or malformed file is a problem, and a section with
    one is left out of the entries."""
    path = folder / FINDINGS
    out: dict = {"path": FINDINGS, "exists": path.is_file(), "entries": [], "open": [],
                 "fix": [], "fresh": None, "cases": None, "passes": dict.fromkeys(PASS_LINES),
                 "evidence": [], "problems": []}  # fmt: skip
    if not out["exists"]:
        return out
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        out["problems"].append(f"{FINDINGS} can't be read: {e}")
        return out
    if is_unfilled(path):
        out["problems"].append(f"{FINDINGS} is still the template: fill it or delete it")
        return out
    out["entries"], out["problems"] = _findings_from_text(text)
    out["open"] = [e["id"] for e in out["entries"] if e["disposition"] == "open"]
    out["fix"] = [e["id"] for e in out["entries"] if e["disposition"] == "fix"]
    out["fresh"] = findings_fresh(text)
    out["cases"] = _note_says(text, CASES_RE)
    out["passes"] = {name: _note_says(text, line_re) for name, line_re in PASS_LINES.items()}
    out["evidence"], wrong = findings_evidence(text)
    out["problems"] += wrong
    if (out["passes"]["behaviour"] or {}).get("ran") and not out["evidence"]:
        out["problems"].append(
            f"{FINDINGS}: its note says `Behaviour check: ran`, and its `{EVIDENCE_HEADING}` "
            "section holds no `$ <command>` with its `exit:`"
        )
    return out


def findings_evidence(text: str) -> tuple[list[dict], list[str]]:
    """The behaviour check's evidence in findings.md's `## Evidence` section, as `{"command",
    "exit"}` in order, and a problem for each `$` line with no `exit:` before the next or the
    section's end. Fenced output is skipped, as everywhere in the file."""
    evidence: list[dict] = []
    problems: list[str] = []
    inside = fenced = False
    command: str | None = None

    def unfinished() -> None:
        if command is not None:
            problems.append(f"{FINDINGS}: {EVIDENCE_HEADING}: `$ {command}` has no `exit:` line")

    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("## "):
            unfinished()
            command = None
            inside = line.strip() == EVIDENCE_HEADING
            continue
        if not inside:
            continue
        if line.startswith("$ "):
            unfinished()
            command = line[2:].strip()
        elif command is not None and (m := EVIDENCE_EXIT_RE.match(line.strip())):
            evidence.append({"command": command, "exit": int(m.group(1))})
            command = None
    unfinished()
    return evidence, problems


def _finding_number(ident: str) -> int | None:
    """`F5` → 5; None for anything else."""
    m = re.fullmatch(r"F(\d+)", ident.strip())
    return int(m.group(1)) if m else None


def findings_fresh(text: str) -> dict | None:
    """What findings.md's note says of the fresh-context review: `{"ran": True}`, `{"ran": False,
    "why": ...}`, or None when it says neither, as every file from before the line did."""
    return _note_says(text, FRESH_RE)


def conflicts_resolved(path: Path) -> list[str]:
    """Every file the change's `conflicts.md` says a resolution merged, each once, in order: what
    `sdlc.py resolve` wrote as each one finished, and ship's question names."""
    record = path / "conflicts.md"
    lines = record.read_text(encoding="utf-8").splitlines() if record.is_file() else []
    return list(dict.fromkeys(ln[2:].strip() for ln in lines if ln.startswith("- ")))


def _note_says(text: str, line_re: re.Pattern) -> dict | None:
    """What findings.md's note, before its first finding, says ran: `{"ran": True}`, with what it
    said after `ran,` as `said` when anything; `{"ran": False, "why": ...}`; or None."""
    for line in text.splitlines():
        if line.startswith("## "):
            break
        m = line_re.match(line.strip())
        if m:
            if m.group(1) == "skipped":
                return {"ran": False, "why": m.group(2)}
            return {"ran": True, "said": m.group(2)} if m.group(2) else {"ran": True}
    return None


def _findings_from_text(text: str) -> tuple[list[dict], list[str]]:
    """findings.md's entries and problems from its text: the one parser, for a file on disk
    (`findings_entries()`) and one read from history (`_review_at()`)."""
    entries: list[dict] = []
    problems: list[str] = []
    sections: list[tuple[str, dict]] = []
    fenced = evidence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        # The behaviour check's evidence is read by `findings_evidence()`, never as a finding.
        if line.strip() == EVIDENCE_HEADING:
            evidence = True
            continue
        if line.startswith("## "):
            evidence = False
            sections.append((line.strip(), {}))
            continue
        if evidence:
            continue
        m = re.match(rf"^({'|'.join(FINDING_KEYS)}):\s*(.*)$", line)
        if m and sections and m.group(1) not in sections[-1][1]:
            sections[-1][1][m.group(1)] = m.group(2).strip()
    seen: set[str] = set()
    for heading, fields in sections:
        m = FINDING_RE.match(heading)
        if not m:
            problems.append(f"{FINDINGS}: {heading!r} isn't `## F<n>. [rank] [pass] title`")
            continue
        ident, rank, pass_, title = f"F{m.group(1)}", m.group(2).strip(), m.group(3).strip(), m[4]
        disposition = fields.get("Disposition", "")
        wrong = []
        if ident in seen:
            wrong.append("its id is used twice")
        seen.add(ident)
        if rank not in FINDING_RANKS:
            wrong.append(f"rank must be one of {'|'.join(FINDING_RANKS)}, got {rank!r}")
        if pass_ not in FINDING_PASSES:
            wrong.append(f"pass must be one of {'|'.join(FINDING_PASSES)}, got {pass_!r}")
        for key in ("Evidence", "Class"):
            if not fields.get(key):
                wrong.append(f"no `{key}:` line")
        if disposition not in DISPOSITIONS:
            wrong.append(
                f"Disposition must be one of {'|'.join(DISPOSITIONS)}, got {disposition!r}"
            )
        elif disposition in DISMISSALS and not fields.get("Reason"):
            wrong.append(f"`{disposition}` with no `Reason:` line")
        elif disposition == "fix" and not fields.get("Fix"):
            wrong.append("`fix` with no `Fix:` line saying the change")
        elif disposition == "fix" and rank == "pre-existing":
            wrong.append("a pre-existing finding is filed as a bug, never `fix`")
        if "By" in fields and fields["By"] not in FINDING_BY:
            wrong.append(f"By must be one of {'|'.join(FINDING_BY)}, got {fields['By']!r}")
        if wrong:
            problems += [f"{FINDINGS}: {ident}: {w}" for w in wrong]
            continue
        entries.append(
            {"id": ident, "rank": FINDING_RANKS[rank], "pass": pass_, "title": title.strip(),
             "evidence": fields["Evidence"], "class": fields["Class"],
             "disposition": disposition, "reason": fields.get("Reason"),
             "by": fields.get("By"), "fix": fields.get("Fix")}
        )  # fmt: skip
    return entries, problems


def findings_trailer(entries: list[dict]) -> str:
    """The `Sdlc-Findings` line for a change's findings: the count by rank and by pass, as ship
    has always written it, then each disposition but `open` as its count by pass
    (`fixed=correctness:2,context:1`), or `0`, then how many the fresh reviewer raised and how
    many of those were answered `wrong`, then `agents=`, how many findings the factory's agents
    left in the file, counted in no other key (`ship_findings()`), then `passes=`, each of ship's
    own passes' counts (`security:1,ui:2`, or `0`), and `passes_wrong=`, how many of those were
    answered `wrong`. Old keys keep their meaning;
    retro reads a trailer without dispositions, or without `fresh`, as one whose answers are
    unknown there."""
    agents = len(entries) - len(ship_findings(entries))
    entries = ship_findings(entries)
    counts = {r: sum(e["rank"] == r for e in entries) for r in FINDING_RANKS.values()}
    passes = {p: sum(e["pass"] == p for e in entries) for p in FINDING_PASSES}
    words = [f"{k}={v}" for k, v in {**counts, **passes}.items()]
    for d in COUNTED:
        by = {p: sum(e["pass"] == p and e["disposition"] == d for e in entries)
              for p in FINDING_PASSES}  # fmt: skip
        words.append(f"{d}=" + (",".join(f"{p}:{n}" for p, n in by.items() if n) or "0"))
    fresh = [e for e in entries if e.get("by") == "fresh"]
    words.append(f"fresh={len(fresh)}")
    words.append(f"fresh_wrong={sum(e['disposition'] == 'wrong' for e in fresh)}")
    words.append(f"agents={agents}")
    by_pass = {p: [e for e in entries if e.get("by") == p] for p in SHIP_PASSES}
    shown = [f"{p.removeprefix('ship-')}:{len(found)}" for p, found in by_pass.items() if found]
    words.append("passes=" + (",".join(shown) or "0"))
    wrong = sum(e["disposition"] == "wrong" for found in by_pass.values() for e in found)
    words.append(f"passes_wrong={wrong}")
    return "Sdlc-Findings: " + " ".join(words)


def _age_days(rec: dict, today: date) -> int | None:
    try:
        return (today - date.fromisoformat(rec["created"])).days
    except ValueError:
        return None


def inbox_entries(root: Path) -> list[dict]:
    """Every entry in the register (`register_path()`): its id, its tag as
    written (`status`), its title, the titles its `After:` line names, its body lines by key, and
    its other lines as `text`. A closed entry is deleted once its change ships; history keeps it.
    Fenced lines are skipped, so a template's example is never an entry. A file that can't be read
    holds none: `nit_entries()` says why."""
    path = register_path(work_dir(root))
    try:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return []
    return parse_entries(text)


def parse_entries(text: str) -> list[dict]:
    """The entries a register's text holds, as `inbox_entries()` returns them."""
    out: list[dict] = []
    current: dict | None = None
    fenced = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = _heading_entry(line)
        if heading:
            current = {**heading, "after": [], "fields": {}, "text": []}
            out.append(current)
        elif line.startswith("#"):
            current = None
        elif current is not None and (body := BODY_RE.match(line.strip())):
            current["fields"].setdefault(body.group(1), body.group(2).strip())
            if body.group(1) == "After" and not current["after"]:
                current["after"] = refs_in(body.group(2))
        elif current is not None and line.strip():
            current["text"].append(line.strip())
    # An `After:` naming an entry by id reads as that entry's title, so what waits on what is
    # worked out on titles either way; an id naming nothing stays as written.
    by_id = {e["id"]: e["title"] for e in out}
    for e in out:
        e["after"] = [by_id.get(r, r) for r in e["after"]]
    return out


def _heading_entry(line: str) -> dict | None:
    """An entry's id, date, tag as written (`status`) and title, from its heading line; None for
    any other line."""
    m = ENTRY_RE.match(line)
    if not m:
        return None
    return {"id": f"{m.group(1)}-{m.group(2)}", "date": m.group(1), "status": m.group(3),
            "title": m.group(4).strip()}  # fmt: skip


def refs_in(text: str) -> list[str]:
    """The entries an `After:` or `Groups:` line names, in order: each quoted title, and each id
    written bare."""
    return [m.group(1) or m.group(2) for m in REF_RE.finditer(text)]


def entry_ref(text: str) -> tuple[str, str]:
    """A reference as `("id", …)` or `("title", …)`. An `idea:` may hold an id, a title, or a whole
    older heading, which comes back as its title."""
    text = text.strip().strip('"')
    return ("id", text) if ENTRY_ID_RE.match(text) else ("title", _seed_title(text))


def ref_matches(ref: str, entry: dict) -> bool:
    """Whether a reference names this entry: an id its id, a title its title."""
    kind, value = entry_ref(ref)
    if kind == "id":
        return entry.get("id") == value
    return _seed_title(entry["title"]) == value


def same_ref(a: str, b: str) -> bool:
    """Whether two references name the same thing as written: id to id, title to title."""
    return entry_ref(a) == entry_ref(b)


ISSUE_REF_RE = re.compile(r"^#(\d+)$")


def entry_issues(entry: dict) -> list[int] | None:
    """The issue numbers an entry's `Issue:` line names, in order, the first the others' parent;
    [] with no line, None when a value on it isn't `#N`."""
    raw = entry["fields"].get("Issue")
    if not raw:
        return []
    out = []
    for part in raw.split(","):
        m = ISSUE_REF_RE.match(part.strip())
        if not m:
            return None
        out.append(int(m.group(1)))
    return out


def intent_ideas(text: str) -> list[str]:
    """Every seed an intent's `idea:` names, read as text, so an id is never a date: one id or
    title, or a list of them (`idea: [2026-10-24-4, 2026-11-12-2]`) when a change takes several,
    a theme's. [] when it names none."""
    return [v for v in frontmatter_list(text, "idea") or [] if v.strip()]


def intent_idea(text: str) -> str:
    """The first seed an intent's `idea:` names; "" when it has none."""
    return (intent_ideas(text) or [""])[0]


def ideas_of(rec: dict) -> list[str]:
    """Every seed a change record names: its `ideas`, or, from a record built before there were
    several, its one `idea`."""
    return list(rec.get("ideas") or ([rec["idea"]] if rec.get("idea") else []))


def nit_entries(root: Path) -> tuple[list[dict], list[str]]:
    """Every open nit, the register's `[nit]` entries, and what about them can't be read. A retired
    nit is deleted by the ship that retires it; history keeps it. Its raised date is its id's, and
    who raised it is its `Raised by: NNN-slug (pass)` line."""
    path = register_path(work_dir(root))
    try:
        if path.is_file():
            path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [], [f"can't be read: {e}"]
    nits: list[dict] = []
    problems: list[str] = []
    for e in inbox_entries(root):
        if not is_nit(e):
            continue
        fields = e["fields"]
        name = e["id"]
        raised = NIT_RAISED_RE.match(fields.get("Raised by", ""))
        paths = fields.get("Paths", "")
        nit = {
            "id": e["id"],
            "theme": (fields.get("Theme") or "").strip(),
            "title": e["title"],
            "raised": e["date"],
            "by": raised.group(1) if raised else None,
            "pass": raised.group(2) if raised else None,
            "paths": [p.strip().strip("`") for p in paths.split(",") if p.strip()],
            "cost": fields.get("Cost"),
            "value": fields.get("Value"),
            "text": " ".join(e["text"]),
        }
        try:
            date.fromisoformat(e["date"])
        except ValueError:
            problems.append(f"{name}: {e['date']!r} isn't a date")
        if not nit["theme"]:
            problems.append(f"{name} has no `Theme:` line")
        if not raised:
            problems.append(f"{name} has no `Raised by: NNN-slug (pass)` line")
        if not nit["paths"]:
            problems.append(f"{name} has no `Paths:` line")
        if nit["cost"] not in NIT_COSTS:
            problems.append(
                f"{name}: Cost must be one of {'|'.join(NIT_COSTS)}, got {nit['cost']!r}"
            )
        if nit["value"] not in NIT_VALUES:
            problems.append(
                f"{name}: Value must be one of {'|'.join(NIT_VALUES)}, got {nit['value']!r}"
            )
        nits.append(nit)
    return nits, problems


def nit_touches(nit: dict, paths: list[str]) -> bool:
    """A nit's path is one of `paths`, or a folder holding one."""
    return any(p == q or q.startswith(p.rstrip("/") + "/") for p in nit["paths"] for q in paths)


def nits_summary(nits: list[dict], today: date) -> dict:
    """What retro weighs: how many are open, and per theme how many and how old the oldest is."""
    themes: dict[str, dict] = {}
    for n in nits:
        t = themes.setdefault(n["theme"], {"count": 0, "oldest": None})
        t["count"] += 1
        # As dates: a malformed one, which `check` reports, is never the oldest.
        try:
            raised = date.fromisoformat(n["raised"])
        except (TypeError, ValueError):
            continue
        if t["oldest"] is None or raised < date.fromisoformat(t["oldest"]):
            t["oldest"] = n["raised"]
    for t in themes.values():
        t["age_days"] = _age_days({"created": t["oldest"] or ""}, today)
    return {"open": len(nits), "themes": themes}


def is_building(idea: dict) -> bool:
    """The idea is tagged `[building]`, which older versions of intent wrote and nothing writes
    now: read for good, alongside the open changes' claims (`_open_claims()`)."""
    return "building" in idea["status"].lower()


def is_nit(entry: dict) -> bool:
    """A finding ship approved unfixed, `[nit]`: put forward by theme, never as a seed."""
    return entry["status"].strip().lower() == "nit"


def is_bug(entry: dict) -> bool:
    """Something already broken, `[bug]`: put forward first, by severity."""
    return entry["status"].strip().lower() == "bug"


def entry_kind(entry: dict) -> str:
    """`bug`, `nit` or `idea`: every other tag, `[seed]` and `[building]` included, is an idea."""
    return "bug" if is_bug(entry) else "nit" if is_nit(entry) else "idea"


# An idea or a bug may carry `Priority: high|med|low`: high is put forward before everything else,
# low after everything else, and med, or no line, where the rules put it. A nit has none: its
# `Cost:` and `Value:` are its rank.
PRIORITIES = ("high", "med", "low")


def entry_priority(entry: dict) -> str | None:
    """The entry's `Priority:` word, lowercased; None without the line."""
    word = (entry["fields"].get("Priority") or "").strip().lower()
    return word or None


def entry_theme(entry: dict) -> str | None:
    """The entry's `Theme:`, which a nit always has and an idea or a bug may; None without one."""
    return (entry["fields"].get("Theme") or "").strip() or None


def priority_problems(entries: list[dict]) -> list[str]:
    """A `Priority:` word that isn't one of PRIORITIES, or a `Priority:` on a nit."""
    problems = []
    for e in entries:
        word = entry_priority(e)
        if word is None:
            continue
        if is_nit(e):
            problems.append(f"{e['id']}: a nit has no Priority: its Cost: and Value: rank it")
        elif word not in PRIORITIES:
            words, got = "|".join(PRIORITIES), e["fields"]["Priority"]
            problems.append(f"{e['id']}: Priority must be one of {words}, got {got!r}")
    return problems


# The process doc names the severity words in a `- **severity:**` bullet in its section whose
# heading starts with `Bugs`, backticked and most severe first.
SEVERITY_RE = re.compile(r"^- \*\*severity:\*\*\s*(.*)$")


def severities(root: Path, cfg: dict) -> list[str]:
    """The severity words, most severe first: the host's process doc's, its answers or its full
    copy alike, else the guide's."""
    rel = cfg["docs"]["process"]
    for path in ([root / rel] if rel else []) + [GUIDE_DIR / GUIDES["process"]]:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        inside, bullet = False, None
        for line in text.splitlines():
            if line.startswith("#"):
                if bullet is not None:
                    break
                inside = line.lstrip("#").strip().startswith("Bugs")
            elif bullet is not None and line.startswith("  "):
                bullet += " " + line.strip()
            elif bullet is not None:
                break
            elif inside and (m := SEVERITY_RE.match(line)):
                bullet = m.group(1)
        words = re.findall(r"`([^`]+)`", bullet or "")
        if words:
            return words
    return []


def bug_entries(root: Path, words: list[str] | None = None) -> tuple[list[dict], list[str]]:
    """Every open bug, the register's `[bug]` entries, and what's wrong with them: no id, or a
    severity missing or not among the process doc's words. Its reported date is its id's."""
    if words is None:
        words = severities(root, load_config(root)[0])
    bugs: list[dict] = []
    problems: list[str] = []
    for e in inbox_entries(root):
        if not is_bug(e):
            continue
        fields = e["fields"]
        name = e["id"]
        severity = (fields.get("Severity") or "").strip()
        paths = fields.get("Paths", "")
        bugs.append(
            {
                "id": e["id"],
                "title": e["title"],
                "reported": e["date"],
                "severity": severity,
                "paths": [p.strip().strip("`") for p in paths.split(",") if p.strip()],
                "introduced_by": (fields.get("Introduced by") or "").strip() or None,
                "text": " ".join(e["text"]),
            }
        )
        if not severity:
            problems.append(f"{name} has no `Severity:` line")
        elif words and severity not in words:
            problems.append(f"{name}: Severity must be one of {'|'.join(words)}, got {severity!r}")
    return bugs, problems


def severity_rank(severity: str | None, words: list[str]) -> int:
    """Where a severity sorts: its place among the words, an unknown one last."""
    return words.index(severity) if severity in words else len(words)


def bugs_summary(bugs: list[dict], words: list[str], today: date) -> dict:
    """How many bugs are open, by severity in the process doc's order, and the oldest's age."""
    by = Counter(b["severity"] or "unset" for b in bugs)
    order = [w for w in words if by[w]] + sorted(k for k in by if k not in words)
    ages = [_age_days({"created": b["reported"]}, today) for b in bugs]
    return {
        "open": len(bugs),
        "by_severity": {k: by[k] for k in order},
        "oldest_days": max((a for a in ages if a is not None), default=None),
    }


def introducer(home: Path, trunk: str | None, path: str) -> str | None:
    """The closed change that last touched `path` on the base branch, or None: no commit touches
    it, or the newest one was committed outside a change. A candidate for a bug's `Introduced by:`
    line, never written without a person's word."""
    if not trunk:
        return None
    sha = _git(home, "log", "-1", "--format=%H", trunk, "--", path)
    if not sha:
        return None
    log = _git(home, "log", "--first-parent", "--reverse", "--format=%H %s", f"{sha}..{trunk}")
    for line in (log or "").splitlines():
        close, _, subject = line.partition(" ")
        name = subject.removeprefix(CLOSE_PREFIX)
        if subject.startswith(CLOSE_PREFIX) and DIR_RE.match(name):
            base = _change_base(home, name, f"{close}^", close)
            inside = base and _git(home, "merge-base", "--is-ancestor", base, sha) is not None
            return name if inside and base != sha else None
    return None


def analyze(root: Path, today: date | None = None) -> dict:
    today = today or date.today()
    cfg = load_config(root)[0]
    project = project_doc(root, cfg)[0]
    # Each change against the product doc on its own branch: one opened before the doc landed
    # owes no `serves:` line until it rebases onto a main that has it.
    products: dict[Path, dict | None] = {}
    changes = []
    for p in change_dirs(root):
        checkout = checkout_of(p)
        if checkout not in products:
            products[checkout] = product_doc(checkout, load_config(checkout)[0])
        changes.append(load_change(p, root, project, products[checkout]))
    for rec in changes:
        rec["age_days"] = _age_days(rec, today)
        folder = root / rec["dir"]
        rec["unfilled"] = [n for n in rec["artifacts"] if is_unfilled(folder / n)]
        rec["undone"] = open_items(folder)

    problems: list[dict] = []
    for rec in changes:
        where = rec["dir"]
        for err in rec["errors"]:
            problems.append({"dir": where, "kind": "frontmatter", "detail": err})
        tier, stage = rec["tier"], rec["stage"]
        folder = root / rec["dir"]
        if stage == "dropped":
            # Exempt from the artifacts its tier owes, but not from saying why and how far it got.
            text = (folder / "intent.md").read_text(encoding="utf-8")
            reached = (frontmatter_list(text, "dropped_at") or [""])[0]
            if reached and reached not in REACHED:
                problems.append(
                    {
                        "dir": where,
                        "kind": "frontmatter",
                        "detail": f"dropped_at must be one of {'|'.join(REACHED)}, got {reached!r}",
                    }
                )
            if not dropped_reason(text):
                problems.append(
                    {
                        "dir": where,
                        "kind": "unfilled artifact",
                        "detail": f"stage: dropped with no `## {DROPPED}` section saying why: "
                        "/sdlc:drop writes it",
                    }
                )
            continue
        for detail in acceptance(folder)["problems"]:
            problems.append({"dir": where, "kind": "checks", "detail": detail})
        # A finding still `open` is a review not yet answered, which only `ship` refuses.
        for detail in findings_entries(folder)["problems"]:
            problems.append({"dir": where, "kind": "findings", "detail": detail})
        if tier is None or stage is None:
            continue
        for name, due_from in (("spec.md", SPEC_REQUIRED_FROM), ("plan.md", PLAN_REQUIRED_FROM)):
            if tier != 2 or stage not in due_from:
                continue
            if name not in rec["artifacts"]:
                problems.append(
                    {
                        "dir": where,
                        "kind": "missing artifact",
                        "detail": f"tier 2 at stage: {stage} has no {name}",
                    }
                )
            elif is_unfilled(folder / name) and not (
                # The factory's builder writes plan.md as its first step, and rewrites it first in
                # an upgraded run's round P: a live build's scaffold is the plan being written,
                # not one left behind.
                name == "plan.md"
                and stage == "build"
                and (factory_records.first_build(folder) or factory_records.upgraded_build(folder))
            ):
                problems.append(
                    {
                        "dir": where,
                        "kind": "unfilled artifact",
                        "detail": f"{name} is still the template at stage: {stage}",
                    }
                )
        # Not at stage: plan — an intent being drafted is *supposed* to look like the
        # template, and a tool whose own `new` produces something that instantly fails `check`
        # teaches you to ignore the check. Age in `status` is what surfaces a stub left here.
        if stage != "plan" and is_unfilled(folder / "intent.md"):
            problems.append(
                {
                    "dir": where,
                    "kind": "unfilled artifact",
                    "detail": f"intent.md is still the template at stage: {stage}",
                }
            )

    entries = inbox_entries(root)
    ideas = [i for i in entries if is_building(i)]
    slugs = {rec["slug"] for rec in changes}
    rel = work_rel(root)
    register = f"{rel}/{register_path(work_dir(root)).name}"
    for entry_id, n in Counter(e["id"] for e in entries).items():
        if n > 1:
            problems.append(
                {"dir": register, "kind": "entry id", "detail": f"{entry_id} is used {n} times"}
            )
    # The explicit link: /sdlc:intent writes the seed's id into `idea:`, older intents its title or
    # the whole heading, with the status tag it had at promotion (`[seed]`) while the register moved
    # on to `[building]`, so a title is matched alone. A dropped change is building nothing and
    # can't vouch for a seed.
    linked = [i for rec in changes if rec["stage"] != "dropped" for i in ideas_of(rec)]
    for idea in ideas:
        # Substring either way, deliberately loose: a folder slug is usually a shortening of the
        # idea's title, never a copy of it. It errs toward staying quiet rather than nagging about
        # an idea that *is* being worked on under a shorter name.
        title_slug = slugify(idea["title"])
        by_slug = any(s in title_slug or title_slug in s for s in slugs)
        by_frontmatter = any(idea["title"] in ref or ref_matches(ref, idea) for ref in linked)
        if not (by_slug or by_frontmatter):
            problems.append(
                {
                    "dir": register,
                    "kind": "orphan idea",
                    "detail": f"[{idea['status']}] {idea['title']} — no change folder",
                }
            )
    # One issue, one record: an entry's `Issue:` line, or an open change's `closes:`.
    filed: dict[int, list[str]] = {}
    for e in entries:
        name = e["id"]
        issues = entry_issues(e)
        if issues is None:
            got = e["fields"]["Issue"]
            detail = f"{name}: Issue: names each issue as #N, got {got!r}"
            problems.append({"dir": register, "kind": "issue", "detail": detail})
        for n in issues or []:
            filed.setdefault(n, []).append(name)
    for n, names in sorted(filed.items()):
        if len(names) > 1:
            detail = f"#{n} is on {len(names)} entries: {', '.join(names)}"
            problems.append({"dir": register, "kind": "issue", "detail": detail})
    closing: dict[int, list[str]] = {}
    for rec in changes:
        if rec["stage"] not in ("shipped", "dropped"):
            for n in rec.get("closes") or []:
                closing.setdefault(n, []).append(f"{rec['id']}-{rec['slug']}")
    for n, names in sorted(closing.items()):
        if len(names) > 1:
            detail = f"#{n} is on the closes: line of {', '.join(names)}"
            problems.append({"dir": f"{rel}/", "kind": "closes", "detail": detail})
    for detail in nit_entries(root)[1]:
        problems.append({"dir": register, "kind": "nits", "detail": detail})
    for detail in priority_problems(entries):
        problems.append({"dir": register, "kind": "priority", "detail": detail})
    bugs, bug_problems = bug_entries(root)
    for detail in bug_problems:
        problems.append({"dir": register, "kind": "bugs", "detail": detail})
    claimed = [b for b in bugs if b["introduced_by"]]
    reworked = [(rec, ident) for rec in changes for ident in rec.get("reworks") or []]
    if claimed or reworked:
        trunk = load_config(root)[0]["git"]["base"]
        home = main_root(root)
        names = [c["name"] for c in closed_changes(home, None, trunk, read=False)]
        names += [f"{rec['id']}-{rec['slug']}" for rec in changes]
        # A change reworks what landed, what is still open, or what was dropped and picked up.
        dropped = [d["name"] for d in dropped_changes(home, None, trunk)] if reworked else []
        for rec, ident in reworked:
            if not any(names_change(n, ident) for n in [*names, *dropped]):
                problems.append({"dir": f"{rel}/{rec['id']}-{rec['slug']}", "kind": "reworks",
                                 "detail": f"reworks: {ident!r} names no change"})  # fmt: skip
        for b in claimed:
            if not any(names_change(n, b["introduced_by"]) for n in names):
                problems.append({"dir": register, "kind": "bugs",
                                 "detail": f"{b['id'] or b['title']}: Introduced by "
                                 f"{b['introduced_by']!r} names no change"})  # fmt: skip
    if work_ignored(root):
        problems.append({"dir": f"{rel}/", "kind": "ignored", "detail": ignored_message(root)})
    # A counter behind the folders is normal: main's committed one only moves when a change
    # merges, and allocation counts the open folders and worktrees itself. Only an unreadable one
    # is a problem. A missing file is fine; numbered by GitHub, there is none.
    if (
        ids_mode(root, load_config(root)[0]) != "github"
        and last_id_path(root).exists()
        and read_last_id(root) is None
    ):
        problems.append(
            {
                "dir": str(last_id_path(root)),
                "kind": "last id",
                "detail": "doesn't hold a number: restore it from git history, or delete it and "
                "the next `new` seeds it from the folders, worktrees and archive",
            }
        )

    return {
        "today": today.isoformat(),
        "work": str(work_dir(root)),
        "changes": changes,
        "open": [r for r in changes if r["stage"] not in ("shipped", "dropped")],
        "building_ideas": ideas,
        "problems": problems,
    }


def _highest(home: Path) -> int:
    return max((int(nid) for nid, _ in _used(home)), default=0)


def _read_number(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def read_last_id(home: Path) -> int | None:
    """The number in the last-id file: the last id handed out. None when the file is missing or
    doesn't hold a number, which `check` reports for the second."""
    return _read_number(last_id_path(home))


def _worktree_highest(home: Path) -> int:
    """The highest id among the branches checked out in a worktree and the directories under
    `.claude/worktrees/`: what an open change holds before its counter reaches main. A branch with
    no worktree counts for nothing, so one that merely looks like a change (`2024-cleanup`) can't
    move the numbering. A path that failed to become a worktree still holds its number, or the
    next `new` would land on it again. 0 outside git."""
    names = [b for _, b in worktrees(home)]
    trees = main_root(home) / ".claude" / "worktrees"
    if trees.is_dir():
        names += [p.name for p in trees.iterdir()]
    return max((_number(n) for n in names), default=0)


def next_id(home: Path) -> str:
    """One past the highest of main's counter, the change folders, and the open worktrees.

    The counter on main only moves when a change merges, so the open changes are counted too. A
    change abandoned before it merged (worktree, branch and folder all removed) leaves nothing
    behind, and its number is handed out again: it never reached main, so nothing refers to it.
    Only when the counter is missing does history count, to seed it: with `.sdlc/work/` empty,
    numbering from 001 would collide with every change already closed."""
    last = read_last_id(home)
    seeds = [last or 0, _highest(home), _worktree_highest(home)]
    if last is None:
        seeds.append(_history_highest(home))
    return f"{max(seeds) + 1:03d}"


@command("next", "the id `new` would allocate now; writes nothing")
def cli_next(root: Path, home: Path, args) -> int:
    cfg = load_config(home)[0]
    if ids_mode(home, cfg) == "github":
        numbering = None if archive_unavailable(home, cfg) else tracker(home, cfg)
        guess = numbering.next_guess() if numbering else None
        if guess is None:
            print("⚠  couldn't ask GitHub for its next issue number", file=sys.stderr)
            return 1
        print(f"{guess:03d}")
    else:
        print(next_id(home))
    return 0


def next_entry_ids(home: Path, day: str, count: int = 1) -> list[str]:
    """The next `count` register ids for entries dated `day` (`YYYY-MM-DD-n`): one past the highest
    `n` that day in the register of every checkout of the repo, uncommitted edits included, and in
    every commit on any branch that ever added or removed one, so an id deleted since is never
    handed out again; and in every change's `entries.md`, on disk and in any commit, so an id
    held until close is never handed out twice. A space of its own: never a change number, never
    the tracker's."""
    heading = re.compile(rf"^[+-]?##\s*\[{re.escape(day)}-(\d+)\]")
    texts = []
    for checkout in dict.fromkeys([main_root(home), *(p for p, _ in worktrees(home))]):
        # The register, and what each change there holds to file at close (`ENTRIES`).
        for path in [work_dir(checkout) / INBOX, *work_dir(checkout).glob(f"*/{ENTRIES}")]:
            try:
                texts.append(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
    paths = [f"{w}/{name}" for w in (WORK, HISTORY_WORK) for name in (INBOX, OLD_INBOX)]
    paths.append(f"{WORK}/*/{ENTRIES}")
    log = _git(home, "log", "--all", "-p", "--format=", "-G", rf"\[{day}-", "--", *paths)
    texts.append(log or "")
    used = [int(m.group(1)) for t in texts for line in t.splitlines() if (m := heading.match(line))]
    top = max(used, default=0)
    return [f"{day}-{top + k}" for k in range(1, count + 1)]


@command(
    "next-entry",
    "the id the next inbox entry would take today; writes nothing",
    arg("--count", type=int, default=1, help="this many ids, one per line"),
)
def cli_next_entry(root: Path, home: Path, args) -> int:
    for entry_id in next_entry_ids(home, date.today().isoformat(), max(args.count, 1)):
        print(entry_id)
    return 0


def _add_worktree(home: Path, name: str, base: str) -> tuple[Path | None, str | None]:
    """Make the change's worktree and branch, both `name`, from `base`: (path, None) or
    (None, why). Branched from `base` rather than from whatever this checkout has out, which is how
    one change ends up inside another's branch. Under .claude/worktrees/ because that is where
    Claude Code keeps its own, so one gitignore line covers both. A path already there is refused,
    and keeps its number spent (`_worktree_highest`), so the next `new` doesn't land on it again."""
    tree = home / ".claude" / "worktrees" / name
    if tree.exists():
        return None, f"{tree} already exists"
    made = subprocess.run(
        ["git", "-C", str(home), "worktree", "add", "-b", name, str(tree), base],
        capture_output=True,
        encoding="utf-8",
    )
    return (tree, None) if made.returncode == 0 else (None, made.stderr.strip())


def claim(
    home: Path, slug: str, where: Path | None = None, base: str | None = None
) -> tuple[Path | None, Path | None, str | None]:
    """Take the next number and make the change: (folder, worktree, None), or (None, None, why).

    With `base`, the change gets its worktree and branch from it, and its folder inside; without,
    its folder goes in `where`'s `.sdlc/work/` (the main checkout's by default). Under
    `_main_lock()`, which every worktree shares: a `mkdir` alone isn't one, since two sessions
    that read the same id for different slugs would both get it. What is made under the lock (the
    worktree's branch, or the folder) is what the next claim counts, so the counter can be written
    after the lock is released."""
    with closing._main_lock(home):
        name = f"{next_id(home)}-{slug}"
        tree = None
        if base is not None:
            tree, why = _add_worktree(home, name, base)
            if tree is None:
                return None, None, f"git worktree add failed: {why}"
        dest = work_dir(tree or where or home) / name
        try:
            dest.mkdir(parents=True)
        except FileExistsError:
            return None, None, f"{dest} already exists"
        return dest, tree, None


# When `new` opened a change, UTC to the minute, on the intent's `opened:` line: no seconds, so a
# YAML reader takes it for text, never a timestamp. Close times its lead from it.
OPENED_FORMAT = "%Y-%m-%dT%H:%MZ"


def _with_opened(text: str, stamp: str) -> str:
    """`text` with `opened: <stamp>` on the frontmatter line after `created:`, or before the
    closing `---` when there is none; every other line as it was, by `_stamp`'s rule. A text
    without a frontmatter block is returned as it is."""
    lines = text.splitlines(keepends=True)
    close = next((i for i, ln in enumerate(lines) if i and ln.strip() == "---"), None)
    if not lines or lines[0].strip() != "---" or close is None:
        return text
    created = next((i for i in range(1, close) if lines[i].startswith("created:")), None)
    lines.insert(close if created is None else created + 1, f"opened: {stamp}\n")
    return "".join(lines)


def cmd_new(
    root: Path,
    given_slug: str,
    tier: int,
    title: str | None,
    worktree: bool = False,
    base: str | None = None,
) -> int:
    home = main_root(root)
    slug = slugify(given_slug)
    if not slug:
        print(f"⚠  {given_slug!r} doesn't reduce to a usable slug", file=sys.stderr)
        return 1
    # Compare the folder's own slug, not its full name: `endswith(f"-{slug}")` also matches a
    # hyphen-suffix, so a new `drafts` would be refused as a duplicate of `003-reopen-drafts`.
    if slug in {s for _, s in _used(home)}:
        print(f"⚠  a change with slug {slug!r} already exists", file=sys.stderr)
        return 1
    # Refused rather than warned: `git add` skips an ignored folder, so the change's artifacts
    # would never reach its commit.
    if work_ignored(home):
        print(f"⚠  {ignored_message(home)}", file=sys.stderr)
        return 1
    # Before any number is claimed: a GitHub issue opened for a worktree git then can't branch
    # is a change half made.
    cfg, _, _ = load_config(home)
    base, source = (base, "--base") if base else (cfg["git"]["base"], cfg["git"]["base_source"])
    if worktree and (why := trunk_refusal(home, base, source)):
        print(f"⚠  {why}", file=sys.stderr)
        return 1

    wanted = TIER_ARTIFACTS[tier]
    missing = [n for n in wanted if not template_path(home, n)[0].is_file()]
    if missing:
        print(f"⚠  missing template(s) in {TEMPLATE_DIR}: {', '.join(missing)}", file=sys.stderr)
        return 1

    # The number first, then the worktree and branch named after it, then the folder inside: the
    # id is settled before anything in git can claim one, by the change's GitHub issue or by the
    # counter under a lock. Without a worktree, the folder goes in the checkout `new` ran in.
    here = Path(_git(root, "rev-parse", "--show-toplevel") or root)
    mode = ids_mode(home, cfg)
    issue = None
    if mode == "github":
        why = archive_unavailable(home, cfg)
        numbering = None if why else tracker(home, cfg)
        if numbering is None:
            print(
                f"⚠  changes are numbered by GitHub issues, but {why}. Set archive.target = "
                '"none" to number them locally',
                file=sys.stderr,
            )
            return 1
        used = {int(nid) for nid, _ in _used(home)}
        number, issue, err = numbering.claim(slug, title or slug.replace("-", " "), tier, used)
        if err:
            print(f"⚠  {err}", file=sys.stderr)
            return 1
        print(f"  opened   {issue}")
        name = f"{number:03d}-{slug}"
        tree, why = _add_worktree(home, name, base) if worktree else (None, None)
        if why:
            print(f"⚠  git worktree add failed: {why}", file=sys.stderr)
            _report_drop(issue, numbering.drop(issue, f"its worktree couldn't be made ({why})"))
            return 1
        dest = work_dir(tree or here) / name
        dest.mkdir(parents=True)
    else:
        dest, tree, err = claim(home, slug, here, base if worktree else None)
        if dest is None:
            print(f"⚠  couldn't claim {slug!r}: {err}", file=sys.stderr)
            return 1
    name = dest.name
    nid = name.split("-", 1)[0]
    if tree:
        # The main checkout too: `worktree_setup`'s `{main}`, filled by /sdlc:intent from here.
        print(f"  created  worktree {tree}  (branch {name}, from {base}, main checkout {home})")

    # The counter goes where the change will commit it, next to its folder: its worktree, or the
    # checkout `new` ran in.
    if mode == "local":
        _write_state(tree or here, LAST_ID, f"{nid}\n")

    heading = title or slug.replace("-", " ")
    stamp = date.today().isoformat()
    for artifact in wanted:
        text, origin = render_template(home, artifact, nid, slug, stamp, heading)
        if artifact == "intent.md":
            text = text.replace("tier: 1", f"tier: {tier}", 1)
            text = _with_opened(text, datetime.now(UTC).strftime(OPENED_FORMAT))
        (dest / artifact).write_text(text, encoding="utf-8", newline="\n")
        print(f"  created  {dest / artifact}  ({origin} template)")

    print(f"\n■ {name} — tier {tier}, stage: plan")
    print(
        f"    next: fill in {dest}/intent.md "
        f"({'Problem → Outcome → Approach' if tier == 1 else 'Problem → Outcome, then /sdlc:spec'})"
    )
    return 0


@command(
    "new",
    "scaffold the next change folder",
    arg("slug", help="kebab-case name, e.g. reopen-drafts"),
    arg(
        "--tier",
        type=int,
        choices=[1, 2],
        default=1,
        help="1 = intent only (default), 2 = intent + spec + plan",
    ),
    arg("--title", help="H1 for the artifacts (default: the slug, de-hyphenated)"),
    arg(
        "--worktree",
        action="store_true",
        help="create the change in its own worktree and branch, .claude/worktrees/NNN-slug",
    ),
    arg("--base", help="what --worktree branches from (git.base)"),
)
def cli_new(root: Path, home: Path, args) -> int:
    return cmd_new(root, args.slug, args.tier, args.title, args.worktree, args.base)


def render_template(
    home: Path, name: str, nid: str, slug: str, stamp: str, heading: str
) -> tuple[str, str]:
    """Template `name` as `new` scaffolds it, its placeholders filled, and whose it was (`host` or
    `plugin`): the one rendering `new` and `upgrade` share."""
    source, origin = template_path(home, name)
    text = source.read_text(encoding="utf-8")
    text = (
        text.replace("NNN", nid)
        .replace("SLUG", slug)
        .replace("YYYY-MM-DD", stamp)
        .replace("TITLE", heading)
    )
    return text, origin


# A change's title, as `new` wrote it into the intent's heading: `# NNN — TITLE`.
TITLE_RE = re.compile(r"^# \d{3,} — (.+?)\s*$", re.M)
# What `upgrade` takes a Tier 1 change from, and the files it owes as a Tier 2.
UPGRADE_FROM = ("plan", "build")
UPGRADE_SCAFFOLDS = ("spec.md", "plan.md")


def cmd_upgrade(root: Path, ident: str) -> int:
    """Upgrade a Tier 1 change to Tier 2 in its own checkout: `tier: 2`, `stage: plan` and
    `updated:` edited in place by `stamp_shipped`'s rule, every other byte of `intent.md` kept,
    and `spec.md` and `plan.md` scaffolded from the templates `new` uses, only where missing: a
    file there already is `kept`, never written over. Refused, writing nothing, on the base
    branch, for an id this checkout's branch doesn't name, a change already at Tier 2, or one at
    any stage but `plan` or `build`. The factory runs it, through `factory.py upgrade`, once the
    person's answer to a blocking decision says so; it is one-way, and there is no downgrade."""
    home = main_root(root)
    report: dict = {"change": None, "tier": None, "stage": None, "created": [], "kept": [],
                    "refusals": []}  # fmt: skip

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    git_cfg = load_config(home)[0]["git"]
    trunk = git_cfg["base"]
    if why := trunk_refusal(home, trunk, git_cfg["base_source"]):
        report["refusals"].append(why)
        return emit(1)
    branch = _git(root, "branch", "--show-current") or ""
    if branch == trunk:
        report["refusals"].append(
            f"this checkout is on the base branch {trunk}: upgrade a change from its own worktree"
        )
        return emit(1)
    if not DIR_RE.match(branch) or not names_change(branch, ident):
        report["refusals"].append(
            f"{ident} isn't this checkout's change: it is on {branch or '?'!r}; run upgrade from "
            "the change's own worktree"
        )
        return emit(1)
    folder = work_dir(root) / branch
    intent = folder / "intent.md"
    if not intent.is_file():
        report["refusals"].append(f"{work_rel(root)}/{branch}/intent.md doesn't exist")
        return emit(1)
    report["change"] = branch
    text = intent.read_text(encoding="utf-8")
    tier = (frontmatter_list(text, "tier") or [""])[0]
    stage = (frontmatter_list(text, "stage") or [""])[0]
    if tier == "2":
        report["refusals"].append(f"{branch} is already Tier 2: a change is upgraded once")
    elif tier != "1":
        report["refusals"].append(f"{branch} has no tier: 1 line to upgrade from")
    elif stage not in UPGRADE_FROM:
        report["refusals"].append(
            f"{branch} is at stage: {stage}; upgrade takes a Tier 1 change at stage: plan or build"
        )
    missing = [n for n in UPGRADE_SCAFFOLDS if not template_path(home, n)[0].is_file()]
    if missing:
        report["refusals"].append(f"missing template(s) in {TEMPLATE_DIR}: {', '.join(missing)}")
    stamp = date.today().isoformat()
    stamped, unplaced = _stamp(text, {"tier": "2", "stage": "plan", "updated": stamp})
    if unplaced:
        report["refusals"].append(f"intent.md has no {', '.join(unplaced)} line")
    if report["refusals"]:
        return emit(1)
    nid, slug = branch.split("-", 1)
    found = TITLE_RE.search(text)
    heading = found.group(1) if found else slug.replace("-", " ")
    for name in UPGRADE_SCAFFOLDS:
        if (folder / name).exists():
            report["kept"].append(name)
            continue
        rendered, _ = render_template(home, name, nid, slug, stamp, heading)
        (folder / name).write_text(rendered, encoding="utf-8", newline="\n")
        report["created"].append(name)
    intent.write_text(stamped, encoding="utf-8", newline="\n")
    report.update(tier=2, stage="plan")
    return emit(0)


@command(
    "upgrade",
    "make this checkout's Tier 1 change a Tier 2, its spec and plan scaffolded",
    arg("id", help="the change, e.g. 023"),
)
def cli_upgrade(root: Path, home: Path, args) -> int:
    return cmd_upgrade(root, args.id)


def _report_drop(issue: str, err: str | None) -> None:
    """Say what became of an issue `new` opened and then gave up on: printed either way, since
    `opened` is the last word otherwise, and it reads as if the issue were still open."""
    if err:
        print(f"⚠  {issue} is still open: close it by hand ({err})", file=sys.stderr)
    else:
        print(f"  closed   {issue}  (not planned)")


def stamp_shipped(text: str, stamp: str) -> tuple[str, list[str]]:
    """Set `stage: shipped` and the `updated:`/`shipped:` dates by editing those frontmatter lines.

    Deliberately **not** `frontmatter.dumps()`. Round-tripping the block through YAML rewrites
    all of it: keys come back alphabetized, an empty `idea:` becomes `idea: null`, and `id: 001` is
    re-read as the integer 1 — so a shipped intent silently stops matching every open one, and the
    tool that exists to do the bookkeeping is the thing corrupting it. An `intent.md` is
    hand-authored, hand-ordered prose; this is the Edit-not-Write rule applied to `.sdlc/work/`.

    Returns the new text plus the keys it could not place, so a pattern that matches nothing is
    reported instead of written past.
    """
    return _stamp(text, {"stage": "shipped", "updated": stamp, "shipped": stamp}, "shipped")


def stamp_dropped(text: str, stamp: str, reached: str) -> tuple[str, list[str]]:
    """Set `stage: dropped`, `updated:` and `dropped_at:` (the stage it got to) in place, by
    `stamp_shipped`'s rule."""
    return _stamp(text, {"stage": "dropped", "updated": stamp, "dropped_at": reached}, "dropped_at")


def _stamp(text: str, wanted: dict[str, str], new_key: str | None = None) -> tuple[str, list[str]]:
    """Each `wanted` frontmatter line rewritten in place; `new_key`, the one a first stamp adds,
    anchored under `updated:` (none for a stamp that adds no key). The new text and the keys it
    couldn't place."""
    lines = text.splitlines()
    close = next((i for i, ln in enumerate(lines) if i and ln.strip() == "---"), None)
    if not lines or lines[0].strip() != "---" or close is None:
        return text, ["a --- frontmatter block"]

    seen: set[str] = set()
    for i in range(1, close):
        key = lines[i].split(":", 1)[0].strip()
        if key in wanted:
            lines[i] = f"{key}: {wanted[key]}"
            seen.add(key)

    unplaced = [k for k in wanted if k not in seen]
    if new_key in unplaced:
        # First stamp, so the key doesn't exist yet. Anchor it under `updated:` so the two sit
        # together. If there's no `updated:` line it stays unplaced below and the caller refuses.
        anchor = next(
            (i for i in range(1, close) if lines[i].split(":", 1)[0].strip() == "updated"), None
        )
        if anchor is not None:
            lines.insert(anchor + 1, f"{new_key}: {wanted[new_key]}")
            unplaced.remove(new_key)

    return "\n".join(lines) + "\n", unplaced


def _one_change(root: Path, ident: str) -> Path | None:
    """The change folder `ident` names, in whichever checkout holds it; None, with the reason
    printed, when it names none or several."""
    matches = [p for p in change_dirs(root) if names_change(p.name, ident)]
    if not matches:
        print(f"⚠  no change matching {ident!r}", file=sys.stderr)
        return None
    if len(matches) > 1:
        print(f"⚠  {ident!r} is ambiguous: {', '.join(p.name for p in matches)}", file=sys.stderr)
        return None
    return matches[0]


def cmd_sync(root: Path, ident: str | None) -> int:
    """Mirror a change to its tracker as it is now, and say what changed, as JSON. Never creates
    an issue and never touches the change's folder. Exit 0 when it synced or there was nothing to
    sync (no tracker, one with no live view, no issue yet); 1 when the tracker refused."""
    if ident is None:
        here = _git(root, "branch", "--show-current") or ""
        ident = here if DIR_RE.match(here) else None
    if not ident:
        print("⚠  no change named, and this checkout isn't on an NNN-slug branch", file=sys.stderr)
        return 1
    path = _one_change(root, ident)
    if path is None:
        return 1
    home = main_root(root)
    cfg, _, _ = load_config(home)
    why = archive_unavailable(home, cfg)
    report = {"nothing": why} if why else tracker(home, cfg).sync(_tracker_change(home, path))
    if "nothing" in report:
        report = {"nothing to sync": report["nothing"]}
    elif not report.get("error"):
        # Each issue the change takes on hears so now, not at the next marking, and one that left
        # its line, with nothing else recording it, goes back to triage; never fatal.
        closes = set(load_change(path, home).get("closes") or [])
        found, _ = _intake_tracker(home, cfg)
        if found is not None:
            marked = mark_issues(home, found, closes) if closes else {"done": [], "failed": []}
            sent = withdraw_issues(home, found, path.name, closes)
            report.setdefault("done", []).extend(marked["done"] + sent["done"])
            report.setdefault("skipped", []).extend(marked["failed"] + sent["failed"])
    print(json.dumps({"change": path.name, **report}, indent=2, ensure_ascii=False))
    return 1 if report.get("error") else 0


@command(
    "sync",
    "rewrite the change's tracker issue from its artifacts as they are now",
    arg("id", nargs="?", help="the change, e.g. 023 (default: this checkout's)"),
)
def cli_sync(root: Path, home: Path, args) -> int:
    return cmd_sync(root, args.id)


def cmd_lookup(root: Path, names: list[str]) -> int:
    """The values each issue field the project doc turns on can take, as JSON, for /sdlc:intent to
    offer and nothing else. Writes nothing: a tracker's list is read, a fixed list is echoed, and
    a host command is the host's own read-only listing, run like `close_list`."""
    home = main_root(root)
    cfg, _, _ = load_config(root)
    fields, problems = project_doc(root, cfg)
    unknown = [n for n in names if n not in PROJECT_FIELDS]
    problems += [
        f"{n!r} isn't an issue field; they are {', '.join(PROJECT_FIELDS)}" for n in unknown
    ]
    asked = [n for n in names if n in PROJECT_FIELDS] if names else list(fields)
    why = archive_unavailable(home, cfg)
    found = None if why else tracker(home, cfg)
    out: dict[str, dict] = {}
    for name in asked:
        field = fields.get(name)
        row: dict = {"lookup": field["lookup"] if field else None, "values": [], "error": None}
        if field is None:
            row["error"] = "the project doc doesn't turn it on"
        elif field["lookup"] == "list":
            row["values"] = field["values"]
        elif field["lookup"] == "command":
            try:
                ran = subprocess.run(
                    _sh(field["command"].replace("{field}", name)),
                    cwd=home, capture_output=True, encoding="utf-8", errors="replace",
                )  # fmt: skip
            except OSError as e:
                row["error"] = f"the lookup command didn't run: {e}"
            else:
                if ran.returncode == 0:
                    row["values"] = [ln.strip() for ln in ran.stdout.splitlines() if ln.strip()]
                else:
                    why_not = ran.stderr.strip() or "no output"
                    row["error"] = f"the lookup command exited {ran.returncode}: {why_not}"
        elif found is None or not hasattr(found, "lookup"):
            row["error"] = f"no tracker to ask: {why or 'it has no lookups'}"
        else:
            row["values"], row["error"] = found.lookup(name)
            row["values"] = row["values"] or []
        out[name] = row
    print(json.dumps({"fields": out, "problems": problems}, indent=2, ensure_ascii=False))
    return 1 if unknown or (problems and not fields) else 0


@command(
    "lookup",
    "the values the project doc's issue fields can take, as JSON; writes nothing",
    arg("field", nargs="*", help="milestone, project, assignees (default: all on)"),
)
def cli_lookup(root: Path, home: Path, args) -> int:
    return cmd_lookup(root, args.field)


def _undone_report(root: Path, path: Path) -> dict:
    """A change's undone notes.md items, for `undone` and `preflight`."""
    return {
        "change": path.name,
        "notes": _shown(path / "notes.md", root),
        "items": [{"line": i["line"], "text": i["text"]} for i in open_items(path)],
    }


def cmd_undone(root: Path, ident: str) -> int:
    """A change's undone notes.md items as JSON, for /sdlc:ship's Step 0. Writes nothing."""
    path = _one_change(root, ident)
    if path is None:
        return 1
    print(json.dumps(_undone_report(root, path), indent=2, ensure_ascii=False))
    return 0


@command(
    "undone",
    "a change's unticked `- [ ]` items in notes.md, as JSON; writes nothing",
    arg("id", help="the 3-digit id, e.g. 025"),
)
def cli_undone(root: Path, home: Path, args) -> int:
    return cmd_undone(root, args.id)


# How many sensitive paths ship's question names before it says how many more.
RISK_SHOWN = 5


def risk_paths(paths: list[str], patterns: list[str]) -> list[str]:
    """The `paths` any of `patterns` names, in order: an entry ending in `/` names every path under
    it, any other is an fnmatch glob over the repo-relative path, its `*` crossing `/`."""

    def named(p: str) -> bool:
        return any(
            p.startswith(pat) if pat.endswith("/") else fnmatch.fnmatchcase(p, pat)
            for pat in patterns
        )

    return [p for p in paths if named(p)]


def _risk_report(root: Path, path: Path) -> dict | None:
    """What a change's diff against the base branch touches of `review.sensitive` and
    `review.irreversible`, for `preflight` and ship's question: a rename counts by both its paths.
    `deep` when a sensitive path is touched. None when the checkout has no merge base."""
    cfg = load_config(main_root(root))[0]
    trunk = cfg["git"]["base"]
    found = changed_paths(checkout_of(path), trunk) if trunk else None
    if found is None:
        return None
    paths = list(dict.fromkeys(p for _, p_, to in found[1] for p in (p_, to) if p))
    sensitive = risk_paths(paths, cfg["review"]["sensitive"])
    irreversible = risk_paths(paths, cfg["review"]["irreversible"])
    return {"sensitive": sensitive, "irreversible": irreversible, "deep": bool(sensitive)}


def _nits_report(root: Path, path: Path | None, touching: list[str] | None) -> dict | None:
    """The open nits with their age, for `nits` and `preflight`: those change `path`'s diff
    against the base branch touches, or the `touching` paths do, or all. None when the change's
    checkout has no merge base with the base branch."""
    nits, problems = nit_entries(root)
    paths = list(touching or [])
    if path is not None:
        trunk = load_config(main_root(root))[0]["git"]["base"]
        found = changed_paths(checkout_of(path), trunk) if trunk else None
        if found is None:
            return None
        paths += [p for _, path_, to in found[1] for p in (path_, to) if p]
    if path is not None or touching is not None:
        nits = [n for n in nits if nit_touches(n, paths)]
    today = date.today()
    claims = _open_claims(main_root(root))
    for n in nits:
        n["age_days"] = _age_days({"created": n["raised"] or ""}, today)
        n["building"] = _claimed_by(n, claims)
    return {"path": _shown(register_path(work_dir(root)), root), "nits": nits, "problems": problems}


def cmd_nits(root: Path, touching: list[str] | None, change: str | None) -> int:
    """The open nits, the register's `[nit]` entries, as JSON, with their age, for intent and
    spec to offer and ship to retire. `--change` keeps those a change's diff against the base
    branch touches, `--touching` those the given paths do. Writes nothing."""
    path = None
    if change:
        path = _one_change(root, change)
        if path is None:
            return 1
    out = _nits_report(root, path, touching)
    if out is None:
        trunk = load_config(main_root(root))[0]["git"]["base"]
        print(f"⚠  no merge base with {trunk!r}: is this a git checkout?", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if out["problems"] else 0


@command(
    "nits",
    "the open [nit] entries in the inbox, as JSON; writes nothing",
    arg("--touching", nargs="*", help="only those these paths touch"),
    arg("--change", help="only those this change's diff against main touches"),
)
def cli_nits(root: Path, home: Path, args) -> int:
    return cmd_nits(root, args.touching, args.change)


GROUP_KEYS = ("as", "tier", "after")


def _parse_group(text: str) -> tuple[dict, list[str]]:
    """One batch group, `<id> <id> as <slug> tier <n> after <slug>`, as its ids, slug, tier and
    `after`, and the words it couldn't read. The `— words` are the skill's, removed before this."""
    group: dict = {"ids": [], "slug": None, "tier": None, "after": None}
    bad: list[str] = []
    words = text.split()
    i = 0
    while i < len(words):
        word = words[i]
        if ENTRY_ID_RE.match(word):
            group["ids"].append(word)
        elif word in GROUP_KEYS and i + 1 < len(words):
            value = words[i + 1]
            i += 1
            if word == "tier":
                group["tier"] = int(value) if value.isdigit() else value
            else:
                group["slug" if word == "as" else "after"] = slugify(value) or value
        else:
            bad.append(word)
        i += 1
    return group, bad


def _group_order(groups: list[dict]) -> tuple[list[str], list[str]]:
    """The groups' slugs in creation order, each after the one its `after` names and in the given
    order otherwise, and the slugs a cycle leaves unplaced."""
    placed: list[str] = []
    waiting = [g for g in groups if g["slug"]]
    while waiting:
        ready = next((g for g in waiting if not g["after"] or g["after"] in placed), None)
        if ready is None:
            break
        placed.append(ready["slug"])
        waiting.remove(ready)
    return placed, [g["slug"] for g in waiting]


def cmd_groups(root: Path, texts: list[str]) -> int:
    """A batch of changes for `/sdlc:intent`, one group an argument, read against the register
    and the open changes, as JSON: each group's ids (kind, title, `Issue:` numbers), slug, tier,
    `after`, the open change already holding its slug (`created`, which makes a rerun skip it) and
    the number its `after` was created as (`depends_on`); `drafted`, false while that change's
    intent is still the scaffold `new` wrote (a run stopped between the two); the creation
    `order`; and `refusals`, each naming its group, which a batch must have none of before its
    question. A slug only a shipped or dropped folder holds is refused, as `new` would refuse it.
    Writes nothing: every number still comes from `new`, one change at a time."""
    home = main_root(root)
    entries = {e["id"]: e for e in inbox_entries(home)}
    claims = _open_claims(home)
    # Every folder on disk, as `new` checks a slug: an open one is this batch's own, made by an
    # earlier run, and a shipped or dropped one a slug `new` would refuse.
    folders = {DIR_RE.match(p.name).group(2): p for p in change_dirs(home)}
    refusals: list[str] = []
    groups: list[dict] = []
    seen_ids: dict[str, str] = {}
    for n, text in enumerate(texts, 1):
        group, bad = _parse_group(text)
        name = group["slug"] or f"group {n}"
        say = refusals.append
        if bad:
            say(f"{name}: can't read {' '.join(bad)!r}")
        if not group["ids"]:
            say(f"{name}: names no register id")
        if not group["slug"]:
            say(f"{name}: has no `as <slug>`")
        if group["tier"] not in (1, 2):
            say(f"{name}: tier must be 1 or 2, not {group['tier']!r}")
        created, drafted = None, None
        if (folder := folders.get(group["slug"])) is not None:
            stage = load_change(folder, home)["stage"]
            if stage in ("shipped", "dropped"):
                say(f"{name}: taken by {folder.name} ({stage})")
            else:
                created, drafted = folder.name, not is_unfilled(folder / "intent.md")
        ids = []
        for ident in group["ids"]:
            entry = entries.get(ident)
            if ident in seen_ids:
                say(f"{name}: {ident} is in {seen_ids[ident]} too")
            seen_ids.setdefault(ident, name)
            if entry is None:
                say(f"{name}: {ident} isn't in the register")
                ids.append({"id": ident, "kind": None, "title": None, "issues": []})
                continue
            holders = {c for r, c in claims if ref_matches(r, entry)} - {created}
            if holders:
                say(f"{name}: {ident} is taken by {', '.join(sorted(holders))}")
            elif entry["status"] == "building" and not created:
                say(f"{name}: {ident} is tagged [building]")
            issues = entry_issues(entry)
            if issues is None:
                say(f"{name}: {ident}'s Issue: line isn't #N, …")
            kind = "idea" if entry["status"] == "seed" else entry["status"]
            ids.append({"id": ident, "kind": kind, "title": entry["title"],
                        "issues": issues or []})  # fmt: skip
        groups.append(
            {**group, "ids": ids, "created": created, "drafted": drafted, "depends_on": None}
        )

    slugs = [g["slug"] for g in groups if g["slug"]]
    for slug in sorted({s for s in slugs if slugs.count(s) > 1}):
        refusals.append(f"{slug}: two groups take this slug")
    by_slug = {g["slug"]: g for g in groups if g["slug"]}
    for g in groups:
        if g["after"] and g["after"] not in by_slug:
            refusals.append(f"{g['slug']}: `after {g['after']}` names no group of this batch")
        elif g["after"] and (made := by_slug[g["after"]]["created"]):
            g["depends_on"] = made.split("-", 1)[0]
    order, cycle = _group_order([g for g in groups if g["after"] in (None, *by_slug)])
    if cycle:
        refusals.append(f"{', '.join(cycle)}: their `after`s make a cycle")
    print(json.dumps({"groups": groups, "order": order, "refusals": refusals}, indent=2,
                     ensure_ascii=False))  # fmt: skip
    return 1 if refusals else 0


@command(
    "groups",
    "a batch of changes for /sdlc:intent, read and ordered, as JSON; writes nothing",
    arg("group", nargs="+", help='one group each: "<id> … as <slug> tier <n>"'),
)
def cli_groups(root: Path, home: Path, args) -> int:
    return cmd_groups(root, args.group)


def cmd_bugs(root: Path, touching: list[str] | None, introduced: list[str] | None) -> int:
    """The open bugs, the register's `[bug]` entries, as JSON with their age and the process
    doc's severity words. `--touching` keeps those the given paths touch; `--introduced` names, for
    each path, the closed change that last touched it, a candidate for `Introduced by:`. Writes
    nothing."""
    cfg = load_config(root)[0]
    words = severities(root, cfg)
    bugs, problems = bug_entries(root, words)
    if touching is not None:
        bugs = [b for b in bugs if nit_touches(b, touching)]
    today = date.today()
    claims = _open_claims(main_root(root))
    for b in bugs:
        b["age_days"] = _age_days({"created": b["reported"]}, today)
        b["building"] = _claimed_by(b, claims)
    out: dict = {"path": _shown(register_path(work_dir(root)), root), "severities": words,
                 "bugs": bugs, "problems": problems}  # fmt: skip
    if introduced is not None:
        home, trunk = main_root(root), cfg["git"]["base"]
        out["introduced"] = [{"path": q, "change": introducer(home, trunk, q)} for q in introduced]
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if problems else 0


@command(
    "bugs",
    "the open [bug] entries in the inbox, as JSON",
    arg("--touching", nargs="*", help="only those these paths touch"),
    arg("--introduced", nargs="*", help="for each path, the closed change that last touched it"),
)
def cli_bugs(root: Path, home: Path, args) -> int:
    return cmd_bugs(root, args.touching, args.introduced)


def cmd_checks(root: Path, ident: str) -> int:
    """A change's acceptance checks as JSON, for /sdlc:ship to show before it runs them. Runs
    nothing and writes nothing, so it is allowed without a prompt; `accept` is not."""
    path = _one_change(root, ident)
    if path is None:
        return 1
    found = _checks_report(path)
    print(json.dumps(found, indent=2, ensure_ascii=False))
    return 1 if found["problems"] else 0


@command(
    "checks",
    "a change's acceptance checks in checks.md, as JSON; runs nothing",
    arg("id", help="the 3-digit id, e.g. 025"),
)
def cli_checks(root: Path, home: Path, args) -> int:
    return cmd_checks(root, args.id)


def _checks_report(path: Path) -> dict:
    """A change's acceptance checks, for `checks` and `preflight`."""
    return {"change": path.name, **acceptance(path)}


def _findings_report(path: Path) -> dict:
    """A change's review findings, for `findings` and `preflight`: the entries, the ones still
    `open`, the count by rank of ship's own (`ship_findings()`), how many the factory's agents
    left (`agents`), and the `Sdlc-Findings` line ship's commit carries."""
    found = findings_entries(path)
    entries = found["entries"]
    own = ship_findings(entries)
    counts = {r: sum(e["rank"] == r for e in own) for r in FINDING_RANKS.values()}
    return {"change": path.name, **found, "counts": counts, "agents": len(entries) - len(own),
            "trailer": findings_trailer(entries)}  # fmt: skip


def cmd_findings(root: Path, ident: str) -> int:
    """A change's findings.md as JSON, for /sdlc:ship's Step 4: its findings, the ones still
    `open`, their counts and the `Sdlc-Findings` line, so ship never counts by hand. Exits 1 on a
    problem or an open finding. Writes nothing."""
    path = _one_change(root, ident)
    if path is None:
        return 1
    found = _findings_report(path)
    print(json.dumps(found, indent=2, ensure_ascii=False))
    return 1 if found["problems"] or found["open"] else 0


@command(
    "findings",
    "a change's review findings in findings.md, as JSON; writes nothing",
    arg("id", help="the 3-digit id, e.g. 025"),
)
def cli_findings(root: Path, home: Path, args) -> int:
    return cmd_findings(root, args.id)


def _status_lines(checkout: Path) -> set[str]:
    return set((_git(checkout, "status", "--porcelain") or "").splitlines())


def cmd_accept(root: Path, ident: str) -> int:
    """Run a change's acceptance checks from its checkout root, each through `sh -c`, and say
    which pass. A check passes when it exits 0 within CHECK_TIMEOUT and leaves the working tree as
    it found it: ship commits that tree. Never in ALLOW_RULES or a skill's allowed-tools, since an
    agent may have written the commands: a person sees them listed and answers a prompt first."""
    path = _one_change(root, ident)
    if path is None:
        return 1
    found = acceptance(path)
    checkout = checkout_of(path)
    results = []

    def text(out: str | bytes | None) -> str:
        # A timeout's partial output is bytes even in text mode.
        return out.decode("utf-8", "replace") if isinstance(out, bytes) else out or ""

    for check in found["checks"]:
        # Per check, so one that leaves the tree changed fails alone.
        before = _status_lines(checkout)
        start = datetime.now(UTC)
        try:
            run = subprocess.run(
                _sh(check["command"]),
                cwd=checkout,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=CHECK_TIMEOUT,
                stdin=subprocess.DEVNULL,
            )
            code, output = run.returncode, run.stdout + run.stderr
        except subprocess.TimeoutExpired as e:
            code = None
            output = f"{text(e.stdout)}{text(e.stderr)}\ntimed out after {CHECK_TIMEOUT}s"
        except OSError as e:
            code, output = None, f"didn't run: {e}"
        seconds = round((datetime.now(UTC) - start).total_seconds(), 1)
        left = sorted(_status_lines(checkout) - before)
        results.append(
            {
                "name": check["name"],
                "command": check["command"],
                "exit": code,
                "passed": code == 0 and not left,
                "seconds": seconds,
                "left": left,
                "output": "\n".join(output.splitlines()[-CHECK_OUTPUT_LINES:]),
            }
        )
    passed = not found["problems"] and all(r["passed"] for r in results)
    report = {"change": path.name, "checks": results, "passed": passed}
    print(json.dumps({**report, "problems": found["problems"]}, indent=2, ensure_ascii=False))
    return 0 if passed else 1


@command(
    "accept",
    "run a change's acceptance checks from its checkout; never pre-approved",
    arg("id", help="the 3-digit id, e.g. 025"),
)
def cli_accept(root: Path, home: Path, args) -> int:
    return cmd_accept(root, args.id)


# ---------------------------------------------------------------- the gate, run by hand
#
# `gate` runs the base branch's `[commands] check` on a change built by hand and records the
# attempt in its folder's `build/gate.md`, in the shape `factory.py gate` writes
# `build/round-<N>.gate.md`, so the board and status read both alike. The constants below are
# `factory.py`'s, copied (each plugin is cached on its own) and pinned to it by a test; the record's
# own copies (its path, regexes, reader and placeholders) are `factory_records`'.
GATE_TIMEOUT = 30 * 60
GATE_TAIL = 80


def _hand_paths(checkout: Path, trunk: str) -> tuple[str | None, list[str]]:
    """Where the change left `trunk` (the merge-base) and every path it has changed since:
    committed, uncommitted and untracked but not ignored, less the change folders and the
    plugin's state files, sorted. `-z`, so git quotes no path."""
    fork = _git(checkout, "merge-base", trunk, "HEAD")
    if not fork:
        return None, []
    tracked = _git(checkout, "diff", "-z", "--name-only", "--no-renames", fork) or ""
    untracked = _git(checkout, "ls-files", "-z", "--others", "--exclude-standard") or ""
    own = (f"{work_rel(checkout)}/", *(f"{HOST_DIR}/{name}" for name in STATE_FILES))
    paths = {p for p in (tracked.split("\0") + untracked.split("\0")) if p}
    return fork, sorted(p for p in paths if not p.startswith(own))


def _hand_digests(checkout: Path, paths: list[str]) -> dict[str, str]:
    """Each path as the sha256 of its bytes, or `deleted`."""
    found = {}
    for p in paths:
        file = checkout / p
        found[p] = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else "deleted"
    return found


def _hand_hash(fork: str | None, digests: dict[str, str]) -> str:
    text = (fork or "") + "\n" + "".join(f"{p}\0{d}\n" for p, d in sorted(digests.items()))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def hand_build(checkout: Path, trunk: str) -> str:
    """The build a hand gate judged, as 16 hex digits: the merge-base with `trunk` and the content
    of every path the change touched (`_hand_paths()`). Over content, so ship's commit of the same
    work keeps it; over the merge-base, so a rebase onto a moved base doesn't; and never over the
    change's own folder, so writing the record, or notes, leaves it alone."""
    fork, paths = _hand_paths(checkout, trunk)
    return _hand_hash(fork, _hand_digests(checkout, paths))


def _hand_main(root: Path) -> Path:
    """The main checkout, the first worktree `git worktree list` names, else `root`: what
    `factory_records.placeholders()` writes as the clone's root and reads the terms file from."""
    listed = _git(root, "worktree", "list", "--porcelain") or ""
    checkouts = [Path(line[len("worktree ") :]) for line in listed.splitlines()
                 if line.startswith("worktree ")]  # fmt: skip
    return checkouts[0] if checkouts else root


# The factory's gate slots, which a hand gate shares while `sdlc-factory` is enabled, so the two
# never run more gates at once than the base branch's `gate_jobs`: a lock on each of
# `sdlc-factory-gate-<k>.lock` in the git common dir, never `sdlc.lock`. Copies of `factory.py`'s
# (`SLOT_NAME`, `SLOT_POLL`, `CONFIG_FILE`, `DEFAULTS["gate_jobs"]`, `_try_lock()`, `_gate_jobs()`,
# `gate_slot()`), pinned to it by `tests/test_hand_gate.py`, the lock functions by behaviour. The
# wait's limit is the hand gate's own: the factory waits for as long as it takes.
SLOT_NAME = "sdlc-factory-gate-{}.lock"
SLOT_POLL = 0.25
FACTORY_CONFIG = Path(HOST_DIR) / "factory.toml"
GATE_JOBS_DEFAULT = 1
SLOT_WAIT = GATE_TIMEOUT


class SlotTimeout(Exception):
    """No gate slot came free within the hand gate's wait."""


def _gate_jobs_at(home: Path, trunk: str) -> int:
    """`gate_jobs` as the base branch's `factory.toml` holds it, never the checkout's: a change
    can't give its own gate more room. Anything the factory would refuse, a missing file or one
    that won't parse is `GATE_JOBS_DEFAULT`; `factory.py config` is what warns of a bad value."""
    text = _git(home, "show", f"refs/heads/{trunk}:{FACTORY_CONFIG.as_posix()}") or ""
    try:
        jobs = tomllib.loads(text).get("gate_jobs", GATE_JOBS_DEFAULT)
    except tomllib.TOMLDecodeError:
        return GATE_JOBS_DEFAULT
    if not isinstance(jobs, int) or isinstance(jobs, bool) or jobs < 1:
        return GATE_JOBS_DEFAULT
    return jobs


# The base branch's `[ui]`, as far as ship's UI review reads it: whether it is complete and the
# pages, widths and paths its screenshots cover. Copies of `factory.py`'s (`DEFAULTS["ui"]`'s
# keys here, `_ui_table()`'s checks of them, `ui_complete()`, `_page_name()`), pinned to it by
# `tests/test_hand_gate.py`. Ship never takes a screenshot: it reads the sets `factory.py shots`
# left under `.sdlc/reports/shots/<change>/<label>/<role>/`.
UI_DEFAULTS = {"serve": None, "shoot": None, "pages": ["/"], "paths": [],
               "widths": [[1280, 800], [390, 844]]}  # fmt: skip
UI_ROLES = ("ui", "ux")
NO_SHOTS = "no screenshots of this change"


def _ui_complete(ui: dict) -> bool:
    """Whether `[ui]` says enough for a UI review: a server, a screenshot command and its paths."""
    return bool(ui.get("serve") and ui.get("shoot") and ui.get("paths"))


def _ui_page_name(page: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", page.strip("/")).strip("-") or "index"


def _ui_at(home: Path, trunk: str | None) -> dict:
    """`[ui]` as the base branch's `factory.toml` holds it, never the checkout's, so a change can't
    turn its own UI review off: `UI_DEFAULTS` with each value the factory would take, and
    `complete`. A missing file, one that won't parse, or a bad value leaves the default, as the
    factory does; `factory.py config` is what warns of one."""
    text = _git(home, "show", f"refs/heads/{trunk}:{FACTORY_CONFIG.as_posix()}") if trunk else ""
    try:
        table = tomllib.loads(text or "").get("ui", {})
    except tomllib.TOMLDecodeError:
        table = {}
    out = json.loads(json.dumps(UI_DEFAULTS))
    for key, value in table.items() if isinstance(table, dict) else ():
        texts = isinstance(value, list) and all(isinstance(v, str) for v in value)
        sizes = isinstance(value, list) and value and all(
            isinstance(v, list) and len(v) == 2
            and all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in v)
            for v in value
        )  # fmt: skip
        if key in ("serve", "shoot") and isinstance(value, str) and value.strip():
            out[key] = value
        elif key in ("pages", "paths") and texts:
            out[key] = list(value)
        elif key == "widths" and sizes:
            out[key] = [list(v) for v in value]
    out["complete"] = _ui_complete(out)
    return out


def _current_shots(checkout: Path, change: str, ui: dict, changed: list[str]) -> tuple[list, str]:
    """The newest screenshot set of `change` that a UI review can read, as repo-relative paths,
    and None; or no paths and why none can. A set is one `<label>/<role>/` folder: it counts when
    its `shots.json` parses with `problem: null`, every PNG `[ui]`'s pages and widths name is
    there, and the record is newer than every `changed` path under `[ui] paths`, so a page edited
    after its screenshots is never judged from them. Reads files only."""
    where = checkout / REPORTS / "shots" / change
    records = [r for role in UI_ROLES for r in where.glob(f"*/{role}/shots.json")]
    if not records:
        return [], NO_SHOTS
    names = [f"{_ui_page_name(page)}-{w}x{h}.png" for page in ui["pages"] for w, h in ui["widths"]]
    touched = [p for p in risk_paths(changed, ui["paths"]) if (checkout / p).is_file()]

    def stamp(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    why = None
    for record in sorted(records, key=stamp, reverse=True):
        try:
            data = json.loads(record.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            data = {"problem": "its shots.json can't be read"}
        problem = data.get("problem", "no record") if isinstance(data, dict) else "no record"
        missing = [n for n in names if not (record.parent / n).is_file()]
        newer = [p for p in touched if stamp(checkout / p) >= stamp(record)]
        if problem is not None:
            wrong = f"screenshots that didn't finish: {problem}"
        elif missing:
            wrong = f"screenshots missing {missing[0]}"
        elif newer:
            wrong = f"screenshots older than {newer[0]}"
        else:
            shown = [(record.parent / n).relative_to(checkout).as_posix() for n in names]
            return shown, None
        why = why or wrong
    return [], why


def _try_lock(fd: int) -> bool:
    """`_lock()` without waiting: True when taken, False when another holds it."""
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


def _wait_text(seconds: float) -> str:
    return f"{seconds / 60:g} minutes" if seconds >= 60 else f"{seconds:g} seconds"


@contextmanager
def _hand_slot(
    home: Path, jobs: int, change: str, wait: float
) -> Iterator[tuple[int | None, float]]:
    """Hold one of `jobs` gate slots for the `with` block, as `factory.py`'s `gate_slot()` does,
    and yield which (`k`) and the seconds waited (0.0 for none). A wait says so once on stderr,
    naming its limit; past `wait` with no slot, `SlotTimeout`, every descriptor closed. Outside
    a git repo there are no slots: `(None, 0.0)`."""
    common = _git(home, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common:
        yield None, 0.0
        return
    start, fds, held = time.monotonic(), [], None
    try:
        for k in range(jobs):
            fds.append(os.open(Path(common) / SLOT_NAME.format(k), os.O_RDWR | os.O_CREAT, 0o644))
        said = False
        while held is None:
            held = next((k for k, fd in enumerate(fds) if _try_lock(fd)), None)
            if held is None:
                if time.monotonic() - start >= wait:
                    raise SlotTimeout
                if not said:
                    print(f"{change}: waiting for a gate slot ({jobs} of {jobs} in use), up to "
                          f"{_wait_text(wait)}", file=sys.stderr, flush=True)  # fmt: skip
                    said = True
                time.sleep(SLOT_POLL)
        waited = round(time.monotonic() - start, 1) if said else 0.0
        try:
            yield held, waited
        finally:
            closing._unlock(fds[held])
    finally:
        for fd in fds:
            os.close(fd)


def _refused(why: str) -> int:
    print(json.dumps({"refusals": [why]}, indent=2, ensure_ascii=False))
    return 1


def cmd_gate(root: Path, ident: str) -> int:
    """Run the base branch's `[commands] check` on a change built by hand, from its checkout, and
    add the attempt to its folder's `build/gate.md`, as `factory.py gate` records a round's: PASS
    only on exit 0, within `GATE_TIMEOUT`, with every path the build covers as it found it. The
    check is read from the base branch, never the checkout, so a change can't edit the gate that
    judges it. Writes only that file, holding no path of this machine's. Never pre-approved: it
    runs a command, as `accept` does. A factory run is refused while it builds (`factory.py gate`
    gates it); at `stage: test`, where the factory's own gate has stopped, it gates it too, and its
    record clears the approver's `gate` reasons while it is current (`needs_of()`)."""
    home = main_root(root)
    trunk = load_config(home)[0]["git"]["base"]
    if refusal := trunk_refusal(home, trunk):
        return _refused(refusal)
    cfg = _config_at(home, f"refs/heads/{trunk}")
    if cfg is None:
        return _refused(f"the base branch's {HOST_DIR}/config.toml doesn't parse")
    command = cfg["commands"]["check"]
    if not isinstance(command, str) or not command.strip():
        return _refused(f"the base branch's {HOST_DIR}/config.toml has no [commands] check")
    folder = _one_change(root, ident)
    if folder is None:
        return 1
    if (folder / "runs").is_dir() and _stage(folder) != "test":
        return _refused(f"{folder.name} is a factory run: its gate is `factory.py gate`")
    checkout = checkout_of(folder)
    branch = _git(checkout, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != folder.name:
        return _refused(
            f"{_shown(checkout, home)} is on {branch or '?'!r}, not {folder.name}: the record "
            "must judge the change's own branch"
        )
    # With the factory, the hand gate takes one of its slots; without it, none, as before 113.
    jobs = _gate_jobs_at(home, trunk) if factory_enabled(home)[0] else None
    slot = _hand_slot(home, jobs, folder.name, SLOT_WAIT) if jobs else nullcontext((None, 0.0))
    try:
        with slot as (held, waited):
            fork, paths = _hand_paths(checkout, trunk)
            before = _hand_digests(checkout, paths)
            build = _hand_hash(fork, before)
            start = time.monotonic()
            try:
                done = subprocess.run(
                    _sh(command), cwd=checkout, capture_output=True, encoding="utf-8",
                    errors="replace", stdin=subprocess.DEVNULL, timeout=GATE_TIMEOUT,
                )  # fmt: skip
                code, output = done.returncode, done.stdout + done.stderr
                exit_text = str(code)
            except subprocess.TimeoutExpired as e:
                # A timeout's partial output is bytes even in text mode.
                partial = [o.decode("utf-8", "replace") if isinstance(o, bytes) else o or ""
                           for o in (e.stdout, e.stderr)]  # fmt: skip
                code, output = None, "".join(partial) + f"\ntimed out after {GATE_TIMEOUT}s"
                exit_text = "timeout"
            except OSError as e:
                code, output, exit_text = None, f"didn't run: {e}", "didn't run"
            seconds = round(time.monotonic() - start, 1)
            after = _hand_digests(checkout, _hand_paths(checkout, trunk)[1])
    except SlotTimeout:
        return _refused(
            f"no gate slot came free in {_wait_text(SLOT_WAIT)} ({jobs} of {jobs} in use): "
            "nothing was judged, run it again"
        )
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    verdict = "PASS" if code == 0 and not changed else "FAIL"
    path = folder / factory_records.HAND_GATE
    attempt = len(factory_records.gate_attempts(path)) + 1
    output = factory_records.placeholders(output, checkout, _hand_main(checkout))
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
    out = {"change": folder.name, "attempt": attempt, "verdict": verdict, "exit": exit_text}
    out.update(seconds=seconds, waited=waited, slot=held, tree=tree)
    out["to"] = path.relative_to(checkout).as_posix()
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if verdict == "PASS" else 1


@command(
    "gate",
    "run the base branch's check on a change built by hand, into build/gate.md; never pre-approved",
    arg("id", help="the 3-digit id, e.g. 025"),
)
def cli_gate(root: Path, home: Path, args) -> int:
    return cmd_gate(root, args.id)


def hand_gate(folder: Path, home: Path, trunk: str | None) -> dict | None:
    """A change's hand gate record as the board and status read it: None without `build/gate.md`,
    else its last attempt's `verdict`, `exit` and `seconds`, its `attempts` and `fails`, its
    `path`, and whether it is `current`: that attempt judged the build as it stands now
    (`hand_build()`), on the change's own branch. A record that won't read is `current: false`
    with a `problems` line, never an exception: it stands for nothing judged."""
    path = folder / factory_records.HAND_GATE
    if not path.is_file():
        return None
    checkout = checkout_of(folder)
    rel = path.relative_to(checkout).as_posix()
    try:
        attempts = factory_records.gate_attempts(path)
    except OSError as e:
        attempts, why = [], f"{rel} couldn't be read: {e}"
    else:
        why = f"{rel} has no ## Attempt section with its Verdict: line"
    last = attempts[-1] if attempts else None
    out = {
        "verdict": last["verdict"] if last else None,
        "current": False,
        "exit": last["exit"] if last else None,
        "seconds": last["seconds"] if last else None,
        "attempts": len(attempts),
        "fails": sum(a["verdict"] == "FAIL" for a in attempts),
        "path": rel,
    }
    if not last or not last["verdict"]:
        return out | {"problems": [why]}
    on_branch = _git(checkout, "rev-parse", "--abbrev-ref", "HEAD") == folder.name
    out["current"] = bool(
        trunk and on_branch and last["build"] and last["build"] == hand_build(checkout, trunk)
    )
    return out


# ---------------------------------------------------------------- the skills' own cases
#
# `evals/` holds a `claude plugin eval` suite for the core skills, in this plugin's own repo only.
# No command here has `eval` in its name: the harness refuses a command line holding the word from
# a worktree session. `cases` and `cases compare` only read; `run-cases` writes under
# `.sdlc/reports/` and is never pre-approved, like `accept`: each run is a paid model call.
CASES_DIR = "evals"
REPORTS = ".sdlc/reports"
CASES_RUN = "cases"  # a run's folder: `cases-<date>-<n>`
# What a run grants: a case's own `allowed_tools` grants none of these.
CASE_TOOLS = ("Bash", "Write", "Edit")
CASE_CAP = {"change": ("1", "5"), "full": ("3", "20")}  # runs per case, and the USD ceiling
# What a tool's result says when the eval's macOS sandbox couldn't start git (a stale xcrun cache):
# a run that failed with it in its trace is the environment's, never the skill's.
CASE_ENV_MARKERS = ("xcode-select: Failed to locate 'git'",)
CASE_RESULTS = ("passed", "passed on rerun", "failed", "environment")
CAP_WHY = "not rerun: the cost cap"
UNAVAILABLE = ("currently unavailable", "early access")


def case_tags(evals: Path) -> dict[str, list[str]]:
    """Each case (a folder holding `prompt.md`) and the tags its `case.yaml` gives it."""
    found = {}
    for prompt in sorted(evals.glob("*/prompt.md")):
        try:
            meta = yaml.safe_load((prompt.parent / "case.yaml").read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            meta = None
        tags = meta.get("tags") if isinstance(meta, dict) else None
        found[prompt.parent.name] = [str(t) for t in tags] if isinstance(tags, list) else []
    return found


def cases_scope(paths: list[str], tags: dict[str, list[str]]) -> list[str]:
    """The cases a diff's paths call for: those tagged with a core skill `landing_reach()` says it
    touches (`sdlc:ship` is tag `ship`). The factory's skills have no cases here."""
    skills = {s.removeprefix("sdlc:") for s in landing_reach(paths).get("skills", [])}
    return sorted(c for c, t in tags.items() if skills & set(t))


def compare_runs(prev: dict | None, cur: dict) -> dict:
    """Two `plugin eval` results' case scores side by side: each case's score now, before and the
    change, the cases that fell or failed, and `rerun`: a `--case` glob each, one run apiece, since
    the CLI takes one glob a run. A result that isn't the shape expected gives no cases, never an
    exception."""

    def scores(result: dict | None) -> dict[str, float]:
        out = {}
        for case in (result or {}).get("cases") or []:
            if isinstance(case, dict) and isinstance(case.get("name"), str):
                score = (case.get("aggregates") or {}).get("score")
                if isinstance(score, int | float):
                    out[case["name"]] = float(score)
        return out

    now, before = scores(cur), scores(prev)
    rows = [
        {"case": c, "score": s, "before": before.get(c),
         "delta": None if c not in before else round(s - before[c], 3)}
        for c, s in sorted(now.items())
    ]  # fmt: skip
    failed = [r["case"] for r in rows if r["score"] < 1]
    fell = [r["case"] for r in rows if r["delta"] is not None and r["delta"] < 0]
    rerun = [["--case", c] for c in failed]
    return {"cases": rows, "failed": failed, "fell": fell, "rerun": rerun,
            "passed": bool(rows) and not failed}  # fmt: skip


def case_runs(result: dict | None) -> dict[str, list[dict]]:
    """Each case's runs in a `plugin eval` result, in order: its `score`, whether it `failed`
    (below 1, or an error), its failing graders (`name`, `explanation`) and its `trace_path`.
    A result that isn't the shape expected gives no cases, never an exception."""
    out: dict[str, list[dict]] = {}
    for case in (result or {}).get("cases") or []:
        if not isinstance(case, dict) or not isinstance(case.get("name"), str):
            continue
        runs = ((case.get("arms") or {}).get("with")) or []
        out[case["name"]] = [
            {"score": float(r["score"]) if isinstance(r.get("score"), int | float) else 0.0,
             "failed": not (isinstance(r.get("score"), int | float) and r["score"] >= 1)
                       or bool(r.get("error")),
             "graders": [{"name": g.get("name"), "explanation": g.get("explanation")}
                         for g in r.get("graders") or []
                         if isinstance(g, dict) and g.get("passed") is False],
             "trace_path": r.get("tracePath") if isinstance(r.get("tracePath"), str) else None,
             "trace": None, "environment": False}
            for r in runs if isinstance(r, dict)
        ]  # fmt: skip
    return out


def _environment_run(trace: Path | None) -> bool:
    """Whether a run's trace shows the sandbox couldn't start git: one of `CASE_ENV_MARKERS` in a
    tool's result (a `user` entry's `tool_result`, as text or text blocks), never in the agent's
    own words or the prompt. False for a trace that can't be read."""
    try:
        lines = trace.read_text(encoding="utf-8", errors="replace").splitlines() if trace else []
    except OSError:
        return False
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("type") != "user":
            continue
        content = (entry.get("message") or {}).get("content")
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            said = block.get("content")
            if isinstance(said, list):
                said = "\n".join(b.get("text", "") for b in said if isinstance(b, dict))
            if isinstance(said, str) and any(m in said for m in CASE_ENV_MARKERS):
                return True
    return False


def classify_runs(runs: dict[str, list[dict]]) -> None:
    """Mark each failed run whose trace (the kept copy, else the eval's own) shows the sandbox
    couldn't start git as `environment`. A passing run never is."""
    for case_runs_ in runs.values():
        for r in case_runs_:
            where = r.get("kept") or r.get("trace_path")
            r["environment"] = r["failed"] and _environment_run(Path(where) if where else None)


def _workspace_of(trace: Path) -> Path | None:
    """The eval's own temporary workspace a trace sits in: the nearest folder named `e-*` above
    it, and only when that folder is directly in the resolved system temp dir or `/tmp`. None
    for anything else, which is never removed."""
    ws = next((p for p in trace.parents if p.name.startswith("e-")), None)
    if ws is None:
        return None
    temps = {Path(tempfile.gettempdir()).resolve()}
    if Path("/tmp").is_dir():
        temps.add(Path("/tmp").resolve())
    return ws if ws.resolve().parent in temps else None


def _remove_workspace(ws: Path) -> bool:
    """Remove an eval's workspace, whose folders it leaves unwritable (`e-*` and its `sealed/`):
    each folder is made the owner's to write first, never through a link. False when it stays."""
    try:
        os.chmod(ws, 0o700)
        for top, dirs, _ in os.walk(ws):
            for d in dirs:
                if not os.path.islink(os.path.join(top, d)):
                    os.chmod(os.path.join(top, d), 0o700)
        shutil.rmtree(ws)
    except OSError:
        return False
    return not ws.exists()


def _keep_traces(run: Path, home: Path, runs: dict[str, list[dict]], suffix: str,
                 keep: bool) -> list[str]:  # fmt: skip
    """After a `plugin eval` call: copy each failed run's trace into `<run>/traces/<case>-<n>
    <suffix>.jsonl` (its `trace`, relative to `home`), mark the sandbox's failures, and, without
    `keep`, remove each run's workspace that `_workspace_of()` allows. Returns the folders left
    where they were, for a guard they failed or a delete refused."""
    left: list[str] = []
    for case, case_runs_ in runs.items():
        for n, r in enumerate(case_runs_, 1):
            src = Path(r["trace_path"]) if r["trace_path"] else None
            if r["failed"] and src is not None and src.is_file():
                to = run / "traces" / f"{case}-{'rerun' if suffix else n}.jsonl"
                to.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copyfile(src, to)
                except OSError:
                    continue
                r["kept"] = str(to)
                r["trace"] = to.relative_to(home).as_posix()
    classify_runs(runs)
    if keep:
        return left
    for case_runs_ in runs.values():
        for r in case_runs_:
            if not r["trace_path"]:
                continue
            src = Path(r["trace_path"])
            ws = _workspace_of(src)
            if ws is None:
                near = next((p for p in src.parents if p.name.startswith("e-")), src.parent)
                if near.exists():
                    left.append(near.as_posix())
            elif ws.exists() and not _remove_workspace(ws):
                left.append(ws.as_posix())
    return sorted(set(left))


def case_verdicts(scope: str, runs: dict[str, list[dict]], reruns: dict) -> dict[str, dict]:
    """Each case's verdict from its runs, classed by `classify_runs()`: its `result` (one of
    `CASE_RESULTS`), its runs (score, failing graders, kept trace; a rerun's marked `rerun`) and
    `why`, when a failure wasn't rerun. A change's scope: a case fails only when its rerun
    (`reruns[case]`: its runs, or why there were none) fails too, and is `environment` only when
    every run it had was the sandbox's. A full run never reruns: a case fails on two failures of
    the skill's. A case whose every run was the sandbox's is `environment` in either."""
    out = {}
    for case, first in sorted(runs.items()):
        if not first:
            continue
        again = reruns.get(case)
        shown = [*first, *(again if isinstance(again, list) else [])]
        rows = [{"score": r["score"], "graders": r["graders"], "trace": r["trace"],
                 "environment": r["environment"], "rerun": i >= len(first)}
                for i, r in enumerate(shown)]  # fmt: skip
        verdict: dict = {"result": "passed", "runs": rows}
        skill = [r for r in shown if r["failed"] and not r["environment"]]
        if all(r["failed"] and r["environment"] for r in shown):
            verdict["result"] = "environment"
        elif scope == "full":
            verdict["result"] = "failed" if len(skill) >= 2 else "passed"
        elif any(r["failed"] and not r["environment"] for r in first):
            if isinstance(again, str) or not again:
                verdict |= {
                    "result": "failed",
                    "why": again if isinstance(again, str) else "rerun wrote no result",
                }
            elif any(r["failed"] for r in again):
                verdict["result"] = "failed"
            else:
                verdict["result"] = "passed on rerun"
        out[case] = verdict
    return out


def verdict_lists(verdicts: dict[str, dict]) -> dict[str, list[str]]:
    """The cases that `failed`, hit the `environment`, and `passed_on_rerun`."""
    of = {w: sorted(c for c, v in verdicts.items() if v.get("result") == w)
          for w in ("failed", "environment", "passed on rerun")}  # fmt: skip
    return {"failed": of["failed"], "environment": of["environment"],
            "passed_on_rerun": of["passed on rerun"]}  # fmt: skip


def cases_note(verdicts: dict[str, dict], run: str) -> str:
    """findings.md's line for a run, composed here only (`factory.py cases` writes it as given):
    `Skill evals: ran, <passed> of <cases>`, then each list that has a case, then the run."""
    lists = verdict_lists(verdicts)
    passed = sum(v.get("result") in ("passed", "passed on rerun") for v in verdicts.values())
    parts = [f"Skill evals: ran, {passed} of {len(verdicts)}"]
    for key, word in (("failed", "failed"), ("environment", "environment"),
                      ("passed_on_rerun", "passed on rerun")):  # fmt: skip
        if lists[key]:
            parts.append(f"{word}: {', '.join(lists[key])}")
    return "; ".join([*parts, f"run: {run}"])


def cases_failures(record: dict | None) -> dict[str, list[str]]:
    """Each failed case in a run's `scope.json` and the graders that failed in its runs, in
    order, once each: what the landing shows of a failure. `factory.py` reads it with a copy,
    pinned by a test. {} for a record from before verdicts, or none."""
    out: dict[str, list[str]] = {}
    verdicts = (record or {}).get("verdicts")
    for case, v in sorted(verdicts.items()) if isinstance(verdicts, dict) else []:
        if not isinstance(v, dict) or v.get("result") != "failed":
            continue
        names = [g.get("name") for r in v.get("runs") or [] if isinstance(r, dict)
                 for g in r.get("graders") or [] if isinstance(g, dict)]  # fmt: skip
        out[case] = list(dict.fromkeys(n for n in names if isinstance(n, str)))
    return out


def _claude_version() -> str | None:
    try:
        out = subprocess.run(
            ["claude", "--version"], capture_output=True, encoding="utf-8", errors="replace",
            timeout=30, stdin=subprocess.DEVNULL,
        )  # fmt: skip
    except (OSError, subprocess.TimeoutExpired):
        return None
    words = out.stdout.split()
    return words[0] if out.returncode == 0 and words else None


def _case_runs(home: Path) -> list[Path]:
    """The runs `run-cases` made, oldest first."""
    reports = home / REPORTS
    runs = [p for p in reports.glob(f"{CASES_RUN}-*") if p.is_dir()] if reports.is_dir() else []

    def order(p: Path) -> tuple[str, int]:
        day, _, n = p.name.removeprefix(f"{CASES_RUN}-").rpartition("-")
        return day, int(n) if n.isdigit() else 0

    return sorted(runs, key=order)


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _run_summary(run: Path) -> dict:
    """A run's scope and outcome: its confirmed failures from its record's verdicts, and, for a
    run made before there were any, from its `result.json`'s scores."""
    scope = _read_json(run / "scope.json") or {}
    result = _read_json(run / "result.json")
    found = compare_runs(None, result or {})
    if isinstance(scope.get("verdicts"), dict):
        failed = verdict_lists(scope["verdicts"])["failed"]
        passed = not failed if result else None
    else:
        failed, passed = found["failed"], found["passed"] if result else None
    return {
        "run": run.name, "scope": scope.get("scope"), "change": scope.get("change"),
        "skipped": scope.get("skipped"), "passed": passed, "failed": failed,
        "claude": (result or {}).get("claudeVersion"), "cost_usd": (result or {}).get("costUsd"),
    }  # fmt: skip


def _full_history(runs: list[Path]) -> list[dict]:
    """Every full run, oldest first: its date, Claude Code version, cost, and each case's score
    and verdict (from its record's verdicts, else `passed` at a score of 1)."""
    out = []
    for run in runs:
        record = _read_json(run / "scope.json") or {}
        result = _read_json(run / "result.json")
        if record.get("scope") != "full" or result is None:
            continue
        verdicts = record.get("verdicts") if isinstance(record.get("verdicts"), dict) else {}
        rows = compare_runs(None, result)["cases"]
        day = run.name.removeprefix(f"{CASES_RUN}-").rpartition("-")[0]
        out.append({
            "run": run.name, "date": day, "claude": result.get("claudeVersion"),
            "cost_usd": result.get("costUsd"),
            "cases": [{"case": r["case"], "score": r["score"],
                       "result": (verdicts.get(r["case"]) or {}).get("result")
                       or ("passed" if r["score"] >= 1 else "failed")} for r in rows],
        })  # fmt: skip
    return out


def _cases_report(root: Path, path: Path | None) -> dict:
    """What `cases` prints and `preflight` carries: whether this repo has the suite, its cases,
    for change `path` the ones its diff calls for, and the last runs. Empty in a host:
    `available` false, and nothing else is read."""
    home = main_root(root)
    evals = root / CASES_DIR
    if not (_own_repo(home) and evals.is_dir()):
        return {"available": False}
    tags = case_tags(evals)
    out: dict = {"available": True, "cases": tags}
    if path is not None:
        trunk = load_config(home)[0]["git"]["base"]
        found = changed_paths(checkout_of(path), trunk) if trunk else None
        paths = [p for _, p_, to in (found[1] if found else []) for p in (p_, to) if p]
        out["scope"] = cases_scope(paths, tags)
    runs = _case_runs(home)
    out["last"] = _run_summary(runs[-1]) if runs else None
    full = [r for r in runs if (_read_json(r / "scope.json") or {}).get("scope") == "full"]
    out["last_full"] = _run_summary(full[-1]) if full else None
    out["full_history"] = _full_history(full)
    return out


def cases_nudge(report: dict, current: str | None = None) -> str | None:
    """Status's line when the last full run of the skills' cases was on another Claude Code
    version, whose default model may differ: a nudge, never a problem. None in a host, before any
    full run, or when `claude` can't be asked. `current` is for tests; status asks `claude`."""
    last = (report.get("last_full") or {}) if report.get("available") else {}
    if not last.get("claude"):
        return None
    now = current or _claude_version()
    if now is None or now == last["claude"]:
        return None
    return (f"the skills' cases last ran in full on Claude Code {last['claude']}; now {now}: "
            "sdlc.py run-cases --full")  # fmt: skip


def cmd_cases(root: Path, ident: str | None) -> int:
    """The skills' cases, as JSON: for a change, the ones its diff calls for. Writes nothing."""
    path = _one_change(root, ident) if ident else None
    if ident and path is None:
        return 1
    report = _cases_report(root, path)
    if report["available"]:
        report["claude"] = _claude_version()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def cmd_cases_compare(root: Path, run: str) -> int:
    """A run's scores beside the run before it, as JSON. Writes nothing."""
    home = main_root(root)
    folder = Path(run) if Path(run).is_absolute() else root / run
    result = _read_json(folder / "result.json")
    if result is None:
        print(json.dumps({"run": run, "problems": ["no readable result.json in it"]}, indent=2))
        return 1
    runs = [r for r in _case_runs(home) if r.resolve() != folder.resolve()]
    earlier = [r for r in runs if _read_json(r / "result.json")]
    prev = _read_json(earlier[-1] / "result.json") if earlier else None
    found = compare_runs(prev, result)
    out = {"run": folder.name, "against": earlier[-1].name if earlier else None, **found,
           "claude": result.get("claudeVersion"), "cost_usd": result.get("costUsd")}  # fmt: skip
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if found["passed"] else 1


@command(
    "cases",
    "the skills' cases in evals/, and a change's scope of them; writes nothing",
    arg("id", nargs="?", help="a change's id for its scope, or `compare` to compare a run"),
    arg("run", nargs="?", help="with `compare`: the run's folder"),
)
def cli_cases(root: Path, home: Path, args) -> int:
    if args.id == "compare":
        if not args.run:
            raise UsageError("cases compare needs the run's folder")
        return cmd_cases_compare(root, args.run)
    return cmd_cases(root, args.id)


def _case_run_dir(home: Path) -> Path:
    """A fresh `cases-<date>-<n>` under `.sdlc/reports/`, which ignores itself, as `factory.py`'s
    `cmd_report_dir` makes its own (`test_the_report_folder_matches_the_factorys`)."""
    reports = home / REPORTS
    reports.mkdir(parents=True, exist_ok=True)
    ignore = reports / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("*\n", encoding="utf-8", newline="\n")
    stamp = f"{CASES_RUN}-{date.today().isoformat()}"
    n = 1 + sum(1 for p in reports.glob(f"{stamp}-*") if p.is_dir())
    run = reports / f"{stamp}-{n}"
    run.mkdir()
    return run


def cases_argv(
    target: Path, run: Path, scope: str, tags: list[str], case: str | None = None,
    cap: str | None = None,
) -> list[str]:  # fmt: skip
    """The `claude plugin eval` call for a run: the target first, as the CLI wants it, then, for a
    change's scope, its skills' tags (`--tag` takes a list), or, for a rerun, the one `case`
    (`--case` takes one glob, and a second replaces the first), the grants, the cost ceiling
    (the scope's, or `cap`), and `--keep-temp` always, so a failed run's trace can be kept."""
    runs, ceiling = CASE_CAP[scope]
    argv = ["claude", "plugin", "eval", str(target)]
    if case is not None:
        argv += ["--case", case]
        runs = "1"
    elif scope == "change":
        argv += ["--tag", *tags]
    argv += ["--scaffold", "--no-publish", "--trust-plugin", "--ablation", "none",
             "--runs", runs, "--max-cost-usd", cap or ceiling, "--output-dir", str(run),
             "--allow-tools", *CASE_TOOLS, "--keep-temp"]  # fmt: skip
    return [*argv, "--json", str(run / "result.json")]


def _eval(argv: list[str], root: Path) -> tuple[int | None, str]:
    """Run one `plugin eval` call: its exit and what it printed, or None and why it didn't run."""
    try:
        done = subprocess.run(
            argv, cwd=root, capture_output=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL,
        )  # fmt: skip
    except OSError as e:
        return None, f"claude didn't run: {e}"
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def _cost(result: dict | None) -> float:
    cost = (result or {}).get("costUsd")
    return float(cost) if isinstance(cost, int | float) else 0.0


def cmd_run_cases(root: Path, ident: str | None, keep: bool = False) -> int:
    """Run the skills' cases through `claude plugin eval`, a change's scope or the full suite, into
    a fresh folder under `.sdlc/reports/`, and print each case's verdict, the scores beside the
    last run's, and findings.md's `note`. In a change's scope a failed case reruns alone, once,
    under what's left of the cap (`case_verdicts()`); a run the sandbox spoiled is `environment`,
    never rerun or counted. A failed run's trace is kept in the run; each run's workspace is
    removed unless `keep`. Never pre-approved: every run is a paid model call. A missing
    `claude`, an unavailable eval or a first run the cost ceiling stopped is `skipped` with why,
    and exits 0; a case fails the run (exit 1) only when its verdict is `failed`."""
    path = _one_change(root, ident) if ident else None
    if ident and path is None:
        return 1
    report = _cases_report(root, path)
    if not report["available"]:
        print(json.dumps({"skipped": "this repo has no skill cases"}, indent=2))
        return 0
    scope = "change" if path is not None else "full"
    cases = report.get("scope", []) if path is not None else sorted(report["cases"])
    if not cases:
        print(json.dumps({"skipped": "no case covers the skills this diff touches"}, indent=2))
        return 0
    home = main_root(root)
    run = _case_run_dir(home)
    rel = run.relative_to(home).as_posix()
    record: dict = {"scope": scope, "change": path.name if path else None, "cases": cases}

    def write(out: dict) -> None:
        (run / "scope.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                        encoding="utf-8", newline="\n")  # fmt: skip

    tags = sorted({t for c in cases for t in report["cases"][c]})
    code, said = _eval(cases_argv(root / CASES_DIR, run, scope, tags), root)
    if code is None:
        record["skipped"] = said
    elif any(w in said for w in UNAVAILABLE):
        record["skipped"] = "plugin eval is unavailable: " + said.strip().splitlines()[-1]
    elif code == 2:
        record["skipped"] = "the run stopped early, at its cost ceiling or a refused credential"
    result = None if record.get("skipped") else _read_json(run / "result.json")
    if result is None and not record.get("skipped"):
        # A case that failed to load, or a run that never started: no run happened, as for an
        # unavailable eval.
        last = (said.strip().splitlines() or ["nothing printed"])[-1]
        record["skipped"] = f"plugin eval wrote no result: {last}"
    if record.get("skipped"):
        write(record)
        print(json.dumps({"run": rel, **record}, indent=2, ensure_ascii=False))
        return 0
    runs = case_runs(result)
    left = _keep_traces(run, home, runs, "", keep)
    spent, reruns = _cost(result), {}
    for case, first in sorted(runs.items()) if scope == "change" else []:
        if not any(r["failed"] and not r["environment"] for r in first):
            continue
        # Whole cents, rounded down, once float noise below a millionth of one is gone: 5 less
        # 0.65 leaves 4.35, never 4.34.
        ceiling = math.floor(round((float(CASE_CAP["change"][1]) - spent) * 100, 6)) / 100
        if ceiling <= 0:
            reruns[case] = CAP_WHY
            continue
        sub = run / f"rerun-{case}"
        sub.mkdir()
        code, said = _eval(cases_argv(root / CASES_DIR, sub, scope, [], case, f"{ceiling:g}"),
                           root)  # fmt: skip
        again = _read_json(sub / "result.json")
        spent += _cost(again)
        if code == 2:
            reruns[case] = CAP_WHY
            continue
        found = case_runs(again).get(case) if again else None
        if not found:
            reruns[case] = "rerun wrote no result"
            continue
        left += _keep_traces(run, home, {case: found}, "rerun", keep)
        reruns[case] = found
    verdicts = case_verdicts(scope, runs, reruns)
    lists = verdict_lists(verdicts)
    record |= {"verdicts": verdicts, **lists, "passed": not lists["failed"],
               "note": cases_note(verdicts, rel), "left": sorted(set(left))}  # fmt: skip
    write(record)
    earlier = [r for r in _case_runs(home)[:-1] if _read_json(r / "result.json")]
    found = compare_runs(_read_json(earlier[-1] / "result.json") if earlier else None, result)
    out = {"run": rel, **found, **record, "claude": result.get("claudeVersion"),
           "cost_usd": round(spent, 6)}  # fmt: skip
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if lists["failed"] else 0


@command(
    "run-cases",
    "run the skills' cases through plugin eval; paid, never pre-approved",
    exclusive(
        arg("id", nargs="?", help="a change's id: the cases its diff calls for"),
        arg("--full", action="store_true", help="every case"),
        required=True,
    ),
    arg(
        "--keep",
        action="store_true",
        help="keep each run's workspace, to debug a case (a failed run's trace is always kept)",
    ),
)
def cli_run_cases(root: Path, home: Path, args) -> int:
    return cmd_run_cases(root, None if args.full else args.id, args.keep)


def cmd_ship(
    root: Path,
    ident: str,
    leave: list[str] | tuple[str, ...] = (),
    fixed: list[str] | tuple[str, ...] = (),
    through: str | None = None,
) -> int:
    """Stamp a change shipped and stage everything its checkout has uncommitted but `leave`, for
    /sdlc:ship to commit. The register is never edited here: close retires the seeds and bugs the
    change names and files what its `entries.md` holds (`register_plan()`), so ship refuses an
    uncommitted edit to it and says what close will do. Runs after
    ship's WAIT; every refusal comes before the first write, and a rerun is harmless. Never
    commits. After a yes to `Fix …, then commit`, `fixed` names the findings the yes approved
    fixing and `through` the highest id the question was asked over: it refuses unless each of
    them reads `fixed` and the rerun review raised nothing new, so a surprise asks again."""
    path = _one_change(root, ident)
    if path is None:
        return 1

    intent = path / "intent.md"
    if not intent.is_file():
        print(f"⚠  {path.name} has no intent.md — nothing to stamp", file=sys.stderr)
        return 1

    # Every finding the review raised gets an answer before the change lands: fixed, recorded as
    # a seed, or dismissed with a reason. A change with no findings.md predates the file.
    found = findings_entries(path)
    unanswered = found["open"] + found["fix"]
    if unanswered:
        print(
            f"⚠  {path.name}/{FINDINGS} has {len(unanswered)} finding(s) still open or proposed "
            f"for fixing: {', '.join(unanswered)}. Fix each, or give it the disposition the person "
            "approved, and re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1
    by_id = {e["id"]: e for e in found["entries"]}
    unfixed = [f for f in fixed if (by_id.get(f) or {}).get("disposition") != "fixed"]
    if unfixed:
        print(
            f"⚠  {path.name}/{FINDINGS}: {', '.join(unfixed)} approved for fixing but not `fixed` "
            "after the rerun. Ask the person again. Not stamping.",
            file=sys.stderr,
        )
        return 1
    last = _finding_number(through) if through else None
    if through and last is None:
        print(f"⚠  --through {through}: not a finding id like F5. Not stamping.", file=sys.stderr)
        return 1
    new = [e["id"] for e in found["entries"] if last is not None and int(e["id"][1:]) > last]
    if new:
        print(
            f"⚠  {path.name}/{FINDINGS}: the rerun raised {', '.join(new)}, after the question "
            f"asked over {through}. Show it and ask again. Not stamping.",
            file=sys.stderr,
        )
        return 1
    # A deep diff never lands with its fresh review silently missing: the note says it ran, or
    # why it didn't.
    risk = _risk_report(root, path)
    if risk and risk["deep"] and found["fresh"] is None:
        print(
            f"⚠  {path.name} touches a sensitive path, and its {FINDINGS} doesn't say whether the "
            "fresh review ran: add `Fresh review: ran`, or `Fresh review: skipped, <why>`, to its "
            "note and re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1
    # Nor does any of ship's passes that applies: run again, since the diff may have moved since
    # preflight.
    passes = _passes_report(root, path, risk)
    unsaid = [PASS_SAID[line] for name, line in PASS_OF if passes[name]["applies"]
              and found["passes"][line] is None]  # fmt: skip
    if unsaid:
        lines = _and([f"`{s}: ran`, or `{s}: skipped, <why>`" for s in unsaid])
        print(
            f"⚠  {path.name}'s {FINDINGS} doesn't say whether {_and(unsaid)} ran, and "
            f"{'they apply' if len(unsaid) > 1 else 'it applies'}: add {lines}, to its note and "
            "re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1
    # Nor, in this plugin's repo, does a diff reaching a skill with cases land with them silently
    # unrun.
    if _cases_report(root, path).get("scope") and found["cases"] is None:
        print(
            f"⚠  {path.name} touches a skill with cases, and its {FINDINGS} doesn't say whether "
            "they ran: add `Skill evals: ran, <score>`, or `Skill evals: skipped, <why>`, to its "
            "note and re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1

    # An undone item that lands as-is is never read again. Shipping with a known gap is fine; with
    # an unanswered one it isn't. Refuse before stamping.
    undone = open_items(path)
    if undone:
        print(
            f"⚠  {path.name}/notes.md has {len(undone)} undone item(s):\n"
            + "".join(f"     notes.md:{i['line']}  {i['text']}\n" for i in undone)
            + "   Give each a disposition: tick it with `→ seed: <id>` after adding that seed "
            "to the inbox, `→ bug: <id>` after filing a `pre-existing:` one as a bug there, or "
            "`→ dropped: <reason>`. Then re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1

    # The release that carries this change proposes its bump from this line. Asked for
    # here, with the diff in front of someone, not reconstructed from commit subjects at release.
    try:
        post = frontmatter.load(intent)
        impact, named = str(post.get("impact") or ""), intent_ideas(intent.read_text("utf-8"))
    except Exception:  # malformed YAML: `check` reports it; ship refuses below like any other gap
        impact, named = "", []
    if impact not in IMPACTS:
        print(
            f"⚠  {path.name}/intent.md: impact must be one of {'|'.join(IMPACTS)}, got "
            f"{impact!r}. Say what this change does to someone holding the previous release "
            "(the process doc, Releases) and re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1

    # Each seed the change took, a theme's several or the one: every one found before anything
    # is written, so an ambiguous name refuses with nothing deleted.
    ideas = register_path(path.parent)
    seeds: dict[str, list[int]] = {idea: _seed_lines(ideas, idea) for idea in named}
    for idea, lines in seeds.items():
        if len(lines) > 1:
            print(
                f"⚠  {work_rel(root)}/{ideas.name} has {len(lines)} entries named "
                f"{entry_ref(idea)[1]!r} (lines "
                f"{', '.join(str(n + 1) for n in lines)}): delete the one this change built by "
                "hand, or retitle one, and re-run. Not stamping.",
                file=sys.stderr,
            )
            return 1
    tree = Path(_git(path, "rev-parse", "--show-toplevel") or checkout_of(path))
    staged = (_git(tree, "diff", "--cached", "--name-only", "-z") or "").split("\0")
    dirty = _dirty_paths(tree)
    unmatched = [p for p in leave if p not in dirty]
    if unmatched:
        print(
            f"⚠  --leave {', '.join(unmatched)}: not a path the checkout has uncommitted, so "
            "whatever it meant would be staged. Name it as `git status --porcelain` does, from "
            "the checkout's root, and re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1
    # The register rides no change's branch: an edit to it here is an entry filed the old way.
    edited = ideas.resolve().relative_to(tree.resolve()).as_posix() if ideas.parent.is_dir() else ""
    if edited in dirty:
        print(
            f"⚠  {edited} has uncommitted edits: a change's branch never edits the register. Move "
            f"each new entry, and a `Retire <id>: <reason>` line for each nit it retires, to "
            f"{_shown(path, root)}/{ENTRIES}, which close files, or file it now with /sdlc:idea; "
            f"then `git restore {edited}` and re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1
    held = [p for p in leave if p in staged]
    if held:
        print(
            f"⚠  {', '.join(held)}: left out with --leave but already staged, so it would be "
            "committed anyway: unstage it first (`git restore --staged <path>`). Not stamping.",
            file=sys.stderr,
        )
        return 1

    stamp = date.today().isoformat()
    stamped, unplaced = stamp_shipped(intent.read_text(encoding="utf-8"), stamp)
    if unplaced:
        print(
            f"⚠  {path.name}/intent.md: couldn't find {', '.join(unplaced)} — not stamping. "
            "Fix the frontmatter and re-run.",
            file=sys.stderr,
        )
        return 1
    intent.write_text(stamped, encoding="utf-8", newline="\n")
    print(
        f"■ shipped {path.name}  (stage: shipped, {stamp}): commit {_shown(path, root)}/ with "
        "the change"
    )
    # What close will do to the register, in the `Close` commit: nothing here edits it.
    reg = f"{work_rel(root)}/{ideas.name}"
    for idea, lines in seeds.items():
        if lines:
            print(f"  close retires seed {entry_ref(idea)[1]!r} from {reg}")
        else:
            print(f"  no seed to retire: {reg} has no entry named {entry_ref(idea)[1]!r}")
    for fixed in frontmatter_list(stamped, "fixes") or []:
        if ENTRY_ID_RE.match(fixed) and _seed_lines(ideas, fixed):
            print(f"  close retires bug {fixed} from {reg}")
        else:
            print(f"  no bug to retire: {reg} has no entry {fixed}")
    if (path / ENTRIES).is_file():
        held = held_entries((path / ENTRIES).read_text(encoding="utf-8"))
        print(
            f"  close files {len(held['ids'])} entr{'y' if len(held['ids']) == 1 else 'ies'} and "
            f"retires {len(held['retire'])} nit(s) from {_shown(path, root)}/{ENTRIES}"
        )
    paths, err = _stage_change(tree, leave)
    if err:
        print(f"⚠  git add failed: {err}. Fix it and re-run ship.", file=sys.stderr)
        return 1
    for p in paths:
        print(f"  staged {p}")
    if not paths:
        print("  staged nothing: the checkout has nothing uncommitted")
    return 0


@command(
    "ship",
    "stamp the change shipped, in place",
    arg("id", help="the 3-digit id, e.g. 001"),
    arg(
        "--leave", action="append", default=[], metavar="PATH",
        help="a path not to stage, to commit apart; repeatable",
    ),
    arg(
        "--fixed",
        metavar="IDS",
        help="the findings a yes approved fixing, `F2,F4`: each must read fixed",
    ),
    arg("--through", metavar="ID", help="the highest finding id the question was asked over"),
)  # fmt: skip
def cli_ship(root: Path, home: Path, args) -> int:
    fixed = [f.strip() for f in (args.fixed or "").split(",") if f.strip()]
    return cmd_ship(root, args.id, args.leave, fixed, args.through)


def _seed_title(text: str) -> str:
    """A seed's title from its heading, or from an `idea:` line holding the title or the heading,
    with or without its `## `: without the `[date] [tag]` prefix, or the ` → work/<folder>` pointer
    an older intent put in the heading. An arrow in the title itself stays."""
    text = text.strip()
    m = OLD_HEADING_RE.match(text) or OLD_HEADING_RE.match(f"## {text}")
    title = m.group(1) if m else text
    return title.split(" → work/")[0].strip()


def _seed_lines(ideas: Path, idea: str) -> list[int]:
    """The line numbers (from 0) of the register's headings the `idea:` names, by id or title; []
    with no `idea:` or no file."""
    if not idea.strip() or not ideas.is_file():
        return []
    lines = ideas.read_text(encoding="utf-8").splitlines()
    return [
        n
        for n, line in enumerate(lines)
        if (heading := _heading_entry(line)) and ref_matches(idea, heading)
    ]


def _entry_spans(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Each entry's lines in a register, by id: from its heading through the line before the next
    `## ` outside a fence, or the end."""
    spans: dict[str, tuple[int, int]] = {}
    current: tuple[str, int] | None = None
    fenced = False
    for n, line in enumerate(lines):
        if FENCE_RE.match(line):
            fenced = not fenced
        if fenced or not line.startswith("## "):
            continue
        if current:
            spans[current[0]] = (current[1], n)
        heading = _heading_entry(line.rstrip("\n"))
        current = (heading["id"], n) if heading else None
    if current:
        spans[current[0]] = (current[1], len(lines))
    return spans


def _splice_entries(target: str, source: str, ids: list[str]) -> str:
    """`target` with each of `ids` as `source` has it: replaced in place, appended at the end when
    only `source` has it, removed when only `target` does. Every other line stays byte for
    byte."""
    lines = target.splitlines(keepends=True)
    src = source.splitlines(keepends=True)
    src_spans = _entry_spans(src)
    for i in ids:
        chunk: list[str] | None = None
        if i in src_spans:
            s, e = src_spans[i]
            chunk = ("".join(src[s:e]).rstrip("\n") + "\n").splitlines(keepends=True)
        spans = _entry_spans(lines)
        if i in spans:
            s, e = spans[i]
            before, after = lines[:s], lines[e:]
            if chunk is not None:
                lines = before + chunk + (["\n"] if after else []) + after
                continue
            if not after:  # the last entry: no blank line left trailing the one before it
                while before and not before[-1].strip():
                    before.pop()
            lines = before + after
        elif chunk is not None:
            text = "".join(lines).rstrip("\n")
            lines = (text + "\n\n").splitlines(keepends=True) + chunk if text else chunk
    return "".join(lines)


# What a change files and retires in the register, held in its own folder until close lands it
# in the `Close` commit (`register_plan()`): `Retire <id>: <reason>` lines, then entries as the
# register holds them. `factory.py` writes it with copies of these, pinned by tests.
ENTRIES = "entries.md"
RETIRE_LINE_RE = re.compile(r"^Retire (\d{4}-\d{2}-\d{2}-\d+):\s*(.*)$")


def held_entries(text: str) -> dict:
    """A change's `entries.md` as close reads it: each `Retire` line before the first entry, as
    (id, reason); each entry's id in order, and its lines (`chunks`) as close appends them; and
    `problems`, what makes the file unreadable (a stray line before the first entry, a `## ` line
    that isn't an entry's heading, an id held twice), each naming its line."""
    lines = text.splitlines(keepends=True)
    out: dict = {"retire": [], "ids": [], "chunks": {}, "problems": []}
    fenced, seen = False, False
    for n, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        if FENCE_RE.match(line):
            fenced = not fenced
        if fenced and seen:
            continue
        if line.startswith("## "):
            heading = _heading_entry(line)
            if heading is None:
                out["problems"].append(f"line {n}: a `## ` line that isn't an entry's heading")
            elif heading["id"] in out["ids"]:
                out["problems"].append(f"line {n}: {heading['id']} is held twice")
            else:
                out["ids"].append(heading["id"])
            seen = True
        elif not seen and line.strip() and not line.startswith(("# ", ">")):
            if m := RETIRE_LINE_RE.match(line.strip()):
                out["retire"].append((m.group(1), m.group(2).strip()))
            else:
                out["problems"].append(
                    f"line {n}: neither a `Retire <id>: <reason>` line nor an entry"
                )
    spans = _entry_spans(lines)
    for i in out["ids"]:
        if i in spans:
            s, e = spans[i]
            out["chunks"][i] = "".join(lines[s:e]).rstrip("\n") + "\n"
    return out


def _stage_change(tree: Path, leave: list[str] | tuple[str, ...]) -> tuple[list[str], str | None]:
    """Stage every path the checkout has uncommitted, untracked ones included, but `leave`, and
    never by `-A`: the paths are named after `--`. Nothing outside git. A path already staged as
    it is in the tree is listed but not added: git refuses a staged deletion's path."""
    entries = [(xy, p) for xy, p in _status_entries(tree) if p not in leave]
    add = [p for xy, p in entries if xy[1] != " "]
    paths = [p for _, p in entries]
    return paths, (_git_err(tree, "add", "--", *add) if add else None)


# A dropped change says why under this heading of its intent, and its frontmatter's `dropped_at:`
# says how far it got: one of these.
DROPPED = "Dropped"
REACHED = (*(s for s in STAGES if s not in ("shipped", "dropped")), "unknown")
# What `new` writes beside a change's folder, committed with it whether it ships or is dropped.
STATE_FILES = (LAST_ID,)


def dropped_reason(text: str) -> str:
    """The `## Dropped` section of an intent's text; "" when it has none, or only prompts."""
    reason = _section(_body_of(text), DROPPED)
    return "" if PROMPT_RE.search(reason) else reason


def _dirty_paths(tree: Path) -> list[str]:
    """Every path `git status` lists in `tree`, untracked files one by one."""
    return [p for _, p in _status_entries(tree)]


def _status_entries(tree: Path) -> list[tuple[str, str]]:
    """Each path `git status` lists in `tree` with its two status letters (`XY`: the index's, then
    the tree's), untracked files one by one. Read raw: `_git` strips the leading space a status
    line starts with."""
    made = subprocess.run(
        ["git", "-C", str(tree), "status", "--porcelain", "-z", "--untracked-files=all"],
        capture_output=True,
        encoding="utf-8",
    )
    entries = made.stdout.split("\0") if made.returncode == 0 else []
    paths, i = [], 0
    while i < len(entries):
        entry = entries[i]
        if len(entry) > 3:
            paths.append((entry[:2], entry[3:]))
            if entry[0] in "RC":
                i += 1  # a rename's source follows it
        i += 1
    return paths


def _reached_before(tree: Path, rel: str) -> str:
    """The stage an intent set to `dropped` by hand had got to: the newest commit of it on this
    branch that says something else, or `unknown`."""
    for sha in (_git(tree, "log", "--format=%h", "--", rel) or "").split():
        stage = (frontmatter_list(_git(tree, "show", f"{sha}:{rel}") or "", "stage") or [""])[0]
        if stage in REACHED:
            return stage
    return "unknown"


def cmd_drop(root: Path, ident: str | None, check_only: bool = False) -> int:
    """Record a change as dropped on its own branch: stamp `stage: dropped` and `dropped_at:` in
    place, and commit its folder with the state `new` wrote beside it. Close then lands the record
    on main. The reason is the human's prose, written by /sdlc:drop before this runs: refused
    without it, and refused while anything else in the worktree is uncommitted, which is the
    human's to commit or discard."""
    if ident is None:
        here = _git(root, "branch", "--show-current") or ""
        ident = here if DIR_RE.match(here) else None
    report: dict = {"change": ident, "reached": None, "paths": [], "refusals": [], "done": []}

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    if not ident:
        report["refusals"].append(
            "no change named, and this checkout isn't on an NNN-slug branch: give its number"
        )
        return emit(1)
    path = _one_change(root, ident)
    if path is None:
        report["refusals"].append(f"{ident!r} names no single change folder")
        return emit(1)
    tree = Path(_git(path, "rev-parse", "--show-toplevel") or path)
    name, rel = path.name, f"{work_rel(root)}/{path.name}"
    report.update(change=name, worktree=str(tree))
    text = (path / "intent.md").read_text(encoding="utf-8")
    stage = (frontmatter_list(text, "stage") or [""])[0]
    reached = (frontmatter_list(text, "dropped_at") or [""])[0]
    if stage != "dropped":
        reached = stage if stage in REACHED else "unknown"
    elif reached not in REACHED:
        reached = _reached_before(tree, f"{rel}/intent.md")
    report["reached"] = reached

    if stage == "shipped":
        report["refusals"].append(f"{name} is shipped: close it with /sdlc:close")
    if _git(tree, "branch", "--show-current") != name:
        report["refusals"].append(f"{tree} isn't on {name}'s branch: drop it from its worktree")
    if not dropped_reason(text):
        report["refusals"].append(
            f"{rel}/intent.md has no `## {DROPPED}` section saying why, or it's still a prompt"
        )
    # A `Drop` commit keeps the base's tree, so an entry held here would never be filed.
    if (path / ENTRIES).is_file():
        held = held_entries((path / ENTRIES).read_text(encoding="utf-8", errors="replace"))
        if held["ids"]:
            report["refusals"].append(
                f"{rel}/{ENTRIES} holds {', '.join(held['ids'])}, which a drop would never file: "
                "file each with /sdlc:idea, delete it from the file, and re-run"
            )
    owned = {f".sdlc/{f}" for f in STATE_FILES}
    dirty = _dirty_paths(tree)
    stray = [p for p in dirty if not p.startswith(f"{rel}/") and p not in owned]
    if stray:
        report["refusals"].append(
            "uncommitted paths outside the change's folder, to commit or discard first: "
            + ", ".join(stray)
        )
    report["paths"] = [p for p in dirty if p not in stray]
    if report["refusals"] or check_only:
        return emit(1 if report["refusals"] else 0)

    stamped, unplaced = stamp_dropped(text, date.today().isoformat(), reached)
    if unplaced:
        report["refusals"].append(f"{rel}/intent.md: couldn't find {', '.join(unplaced)}")
        return emit(1)
    if stamped != text:
        (path / "intent.md").write_text(stamped, encoding="utf-8", newline="\n")
        report["done"].append("stamp")
    adds = [rel, *(p for p in owned if (tree / p).exists())]
    for args in (["add", "--", *adds], ["commit", "-q", "-m", f"Record why {name} was dropped"]):
        if args[0] == "commit" and _git(tree, "diff", "--cached", "--quiet") is not None:
            break  # committed by an earlier run
        err = _git_err(tree, *args)
        if err:
            report["refusals"].append(f"git {args[0]} failed: {err}")
            return emit(1)
        report["done"].append(args[0])
    return emit(0)


@command(
    "drop",
    "stamp the change dropped and commit its folder on its branch, for close",
    arg("id", nargs="?", help="the change, e.g. 023 (default: this checkout's)"),
    arg("--check", action="store_true", help="preconditions only, write nothing"),
)
def cli_drop(root: Path, home: Path, args) -> int:
    return cmd_drop(root, args.id, args.check)


def worktrees(root: Path) -> list[tuple[Path, str]]:
    """(path, branch) for every checkout of this repo with a branch out, the main one included."""
    out = _git(root, "worktree", "list", "--porcelain") or ""
    found: list[tuple[Path, str]] = []
    path: Path | None = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree ") :])
        elif line.startswith("branch refs/heads/") and path is not None:
            found.append((path, line[len("branch refs/heads/") :]))
    return found


def _stage(folder: Path) -> str | None:
    """The stage the folder's intent.md says; None when it has none that parses."""
    intent = folder / "intent.md"
    if not intent.is_file():
        return None
    try:
        return frontmatter.load(intent).get("stage")
    except Exception:
        return None


def _shipped(folder: Path) -> bool:
    return _stage(folder) == "shipped"


def ready_to_close(root: Path) -> list[dict]:
    """Worktrees whose change is shipped or dropped but still standing: what /sdlc:close is for.
    Read-only.

    The worktree is the signal, not whether `main` has the branch yet: close removes the one, and
    a change whose commit landed some other way still has a worktree to tidy."""
    main = main_root(root)
    out = []
    for tree, branch in worktrees(root):
        m = DIR_RE.match(branch)
        if not m or tree.resolve() == main.resolve():
            continue
        kind = _stage(work_dir(tree) / branch)
        if kind in ("shipped", "dropped"):
            out.append(
                {"id": m.group(1), "slug": m.group(2), "branch": branch, "worktree": str(tree),
                 "kind": kind}
            )  # fmt: skip
    return out


def held_by_rebase(root: Path) -> list[dict]:
    """Shipped or dropped changes a stopped rebase holds (a landing's, on a conflict its builder
    resolves), shaped as `ready_to_close()`'s: their worktree's HEAD is detached, so it can't see
    them, and the board keeps their cards (`rebasing_branches()`). Read-only."""
    trees = _change_trees(root)
    held = rebasing_branches(root, trees)
    out = []
    for tree, branch in trees:
        m = DIR_RE.match(branch)
        if branch not in held or not m:
            continue
        kind = _stage(work_dir(tree) / branch)
        if kind in ("shipped", "dropped"):
            out.append(
                {"id": m.group(1), "slug": m.group(2), "branch": branch, "worktree": str(tree),
                 "kind": kind}
            )  # fmt: skip
    return out


def behind_trunk(main: Path, branch: str, trunk: str | None) -> int | None:
    """How many of the base branch's commits `branch` lacks; None when either isn't a local
    branch. 0 is close's precondition, the base an ancestor of the branch, so a fast-forward is
    possible. Status shows anything else, and ship stops on it, before the gate and the review run
    on a base that close would refuse."""
    if not trunk:
        return None
    out = _git(main, "rev-list", "--count", f"refs/heads/{branch}..refs/heads/{trunk}")
    return int(out) if out and out.isdigit() else None


# An open change nothing has touched for this long is quiet: no session is likely on it, so the
# status skill may recommend finishing it. A busier one is in flight, someone's already.
QUIET_HOURS = 24


def last_touched(root: Path, rec: dict, trunk: str | None) -> float | None:
    """When an open change was last worked on, as a POSIX timestamp: the newest of its branch's
    own last commit and the times the files `git status` lists in its checkout were modified (in
    the main checkout, only those under its folder). None when neither says anything.
    Read-only: one log and one status per change."""
    checkout = checkout_of(Path(root, rec["dir"]))
    branch = f"refs/heads/{rec['id']}-{rec['slug']}"
    span = f"refs/heads/{trunk}..{branch}" if trunk else branch
    times = []
    out = _git(checkout, "log", "-1", "--format=%ct", span)
    if out and out.isdigit():
        times.append(float(out))
    dirty = _dirty_paths(checkout)
    if checkout.resolve() == main_root(root).resolve():
        # The main checkout's other edits are nobody's change: only the folder's own count.
        folder = f"{Path(root, rec['dir']).resolve().relative_to(checkout.resolve()).as_posix()}/"
        dirty = [p for p in dirty if p.startswith(folder)]
    for rel in dirty:
        with suppress(OSError):
            times.append((checkout / rel).stat().st_mtime)
    return max(times) if times else None


def _ago(seconds: float) -> str:
    """`12m`, `5h` or `3d`: how long ago, roughly."""
    minutes = max(int(seconds // 60), 0)
    if minutes < 60:
        return f"{minutes}m"
    return f"{minutes // 60}h" if minutes < 24 * 60 else f"{minutes // (24 * 60)}d"


def cmd_base(root: Path, ident: str | None) -> int:
    """Bring a change's branch up to date with the base branch (`git.base`) in its own worktree,
    or refuse, as JSON. /sdlc:ship runs it at Step 0, so the gate and the review see what close
    will fast-forward.

    One of the writes a skill makes before its WAIT, by a named exception (004's spec): it moves
    only the change's own local branch onto the base, only when nothing conflicts, and prints the
    command that undoes it. A branch with no commits of its own, the usual case at ship and always
    after a factory run, fast-forwards, and git carries the uncommitted work or refuses to
    overwrite it. One with commits rebases, from a clean tree only, and a conflict is aborted.
    Never a stash: the stack is shared with every worktree. Never a merge of the base into the
    branch: close would put it on the base's first-parent line, which `closed_changes()` walks.

    A conflict it refuses is `resolvable` when `resolve` can take it on: ship then resolves it
    (`cmd_resolve()`) rather than stopping. The factory's landing reads the same refusal and
    resolves with its own `factory.py resolve`, so `base` never resolves anything itself."""
    trees = [(t, b) for t, b in worktrees(root) if DIR_RE.match(b)]
    if ident is None:
        here = _git(root, "branch", "--show-current") or ""
        ident = here if DIR_RE.match(here) else None
    found = [(t, b) for t, b in trees if names_change(b, ident)] if ident else []
    main = main_root(root)
    report: dict = {"change": ident, "branch": None, "behind": None, "action": "current",
                    "from": None, "to": None, "undo": None, "reason": None,
                    "resolvable": False}  # fmt: skip

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    if len(found) != 1 or found[0][0].resolve() == main.resolve():
        report["reason"] = "not in a change's worktree: nothing to bring up to date"
        return emit(0)
    tree, branch = found[0]
    before = _git(tree, "rev-parse", "HEAD")
    git_cfg = load_config(main)[0]["git"]
    trunk = git_cfg["base"]
    behind = behind_trunk(main, branch, trunk)
    report.update(change=branch, branch=branch, behind=behind, **{"from": before, "to": before})

    def refuse(reason: str, resolvable: bool = False) -> int:
        """`resolvable`: a conflict `resolve` can take on, so ship resolves instead of stopping."""
        report.update(action="refused", reason=reason, to=_git(tree, "rev-parse", "HEAD"),
                      resolvable=resolvable)  # fmt: skip
        return emit(1)

    if why := trunk_refusal(main, trunk, git_cfg["base_source"]):
        return refuse(why)
    if behind is None:
        return refuse(f"no local {trunk} branch to bring it up to date with")
    if behind == 0:
        return emit(0)
    own = _git(main, "rev-list", "--count", f"refs/heads/{trunk}..refs/heads/{branch}")
    if own and own != "0":
        if _dirty_paths(tree):
            return refuse(
                f"{branch} has commits of its own and uncommitted work, so it can't rebase: "
                "commit the work, then run /sdlc:ship again",
                resolvable=True,
            )
        err = _git_err(tree, "rebase", "-q", trunk)
        if err:
            _git_err(tree, "rebase", "--abort")
            return refuse(f"rebasing onto {trunk} conflicts, so it was aborted: {err}", True)
        report["action"] = "rebased"
    else:
        # The counter `new` wrote beside the folder is untracked until ship commits it, and a
        # change closed meanwhile under local numbering committed the base's: git would refuse to
        # overwrite ours. Set it aside, and keep the higher number.
        counter = tree / ".sdlc" / LAST_ID
        kept = None
        if (
            counter.is_file()
            and _git(tree, "ls-files", "--error-unmatch", f".sdlc/{LAST_ID}") is None
            and _git(main, "cat-file", "-e", f"{trunk}:.sdlc/{LAST_ID}") is not None
        ):
            kept = counter.read_text(encoding="utf-8")
            counter.unlink()
        err = _git_err(tree, "merge", "--ff-only", "-q", trunk)
        if err:
            if kept is not None:
                counter.write_text(kept, encoding="utf-8", newline="\n")
            return refuse(
                f"{trunk} changed what this change's uncommitted work changes: {err}", True
            )
        ours = int(kept.strip()) if kept is not None and kept.strip().isdigit() else 0
        if kept is not None and (_read_number(counter) or 0) < ours:
            _write_state(tree, LAST_ID, kept)
        report["action"] = "fast-forwarded"
    report.update(to=_git(tree, "rev-parse", "HEAD"), undo=f"git -C {tree} reset --keep {before}")
    return emit(0)


@command(
    "base",
    "bring a change's branch up to date with main in its worktree, or refuse",
    arg("id", nargs="?", help="the change, e.g. 023 (default: this checkout's)"),
)
def cli_base(root: Path, home: Path, args) -> int:
    return cmd_base(root, args.id)


# What a resolution keeps, each under the change's branch name, in refs every worktree shares:
# `start`, the branch before; `aside`, the uncommitted work as a commit, when there was any; `end`,
# the branch once resolved (or, after an abort, the resolved work); `pending`, a blob listing the
# files resolved so far, only while one is under way. Refs, never a file in the tree, which the
# rebase would trip on. Close deletes them with the branch.
RESOLVE_REFS = ("start", "aside", "end", "pending")
ASIDE_MESSAGE = "sdlc: set aside for resolve"
CONFLICTS = "conflicts.md"


def _resolve_ref(kind: str, branch: str) -> str:
    return f"refs/sdlc/{kind}/{branch}"


def _rebasing(tree: Path) -> bool:
    """Whether a rebase is stopped in `tree`."""
    for name in ("rebase-merge", "rebase-apply"):
        found = _git(tree, "rev-parse", "--git-path", name)
        if found and (Path(found) if Path(found).is_absolute() else tree / found).exists():
            return True
    return False


def _rebase_branch(tree: Path) -> str | None:
    """The branch a rebase stopped in `tree` is rebasing: its HEAD is detached meanwhile, so
    `worktrees()` doesn't list it under its branch."""
    for name in ("rebase-merge", "rebase-apply"):
        found = _git(tree, "rev-parse", "--git-path", f"{name}/head-name")
        path = (Path(found) if Path(found).is_absolute() else tree / found) if found else None
        if path and path.is_file():
            head = path.read_text(encoding="utf-8").strip()
            return head.removeprefix("refs/heads/") or None
    return None


def _change_trees(root: Path) -> list[tuple[Path, str]]:
    """(worktree, branch) for each change's checkout, one stopped mid-rebase included."""
    found = [(t, b) for t, b in worktrees(root) if DIR_RE.match(b)]
    listed = {t for t, _ in found}
    for line in (_git(root, "worktree", "list", "--porcelain") or "").splitlines():
        if line.startswith("worktree "):
            tree = Path(line[len("worktree ") :])
            branch = None if tree in listed else _rebase_branch(tree)
            if branch and DIR_RE.match(branch):
                found.append((tree, branch))
    return found


def _unmerged(tree: Path) -> list[str]:
    """The files a rebase left unmerged in `tree`, each as it is named (`-z`): never git's quoted
    form of a path holding non-ASCII characters, which no file is called (bug 2026-11-18-73), and
    never through `_git()`, whose strip would take a leading space. Empty when git fails."""
    try:
        done = subprocess.run(
            ["git", "-C", str(tree), "diff", "--name-only", "--diff-filter=U", "-z"],
            capture_output=True, encoding="utf-8", check=True,
        )  # fmt: skip
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [p for p in done.stdout.split("\0") if p]


def _settle_last_id(tree: Path) -> None:
    """`.sdlc/last-id` conflicted: the higher number kept and staged, as `base` keeps it, so no
    number is handed out twice. Never the agent's to resolve. A copy of `factory.py`'s
    `_settle_counter()`."""
    rel = f".sdlc/{LAST_ID}"
    if rel not in _unmerged(tree):
        return
    sides = [_git(tree, "show", f":{n}:{rel}") or "" for n in (2, 3)]
    numbers = [int(s) for s in sides if s.strip().isdigit()]
    if numbers:
        (tree / rel).write_text(f"{max(numbers):03d}\n", encoding="utf-8", newline="\n")
        _git(tree, "add", "--", rel)


def _pending(tree: Path, branch: str) -> list[str] | None:
    """The files resolved so far in the resolution under way, or None when none is."""
    ref = _resolve_ref("pending", branch)
    if _git(tree, "rev-parse", "--verify", "-q", ref) is None:
        return None
    return (_git(tree, "cat-file", "-p", ref) or "").splitlines()


def _set_pending(tree: Path, branch: str, files: list[str]) -> None:
    made = subprocess.run(
        ["git", "-C", str(tree), "hash-object", "-w", "--stdin"],
        input="".join(f"{f}\n" for f in files), capture_output=True, encoding="utf-8",
    )  # fmt: skip
    _git(tree, "update-ref", _resolve_ref("pending", branch), made.stdout.strip())


def _go_on(tree: Path, env: dict) -> subprocess.CompletedProcess:
    """`git rebase --continue`, and when git won't go on because the step has nothing of its own
    left (nothing unmerged, the index and the tracked files as `HEAD` holds them: a conflict
    resolved to what the base already has), `git rebase --skip`, which drops only that empty step.
    Git's merge backend drops it itself; its apply backend answers "No changes". An empty aside
    commit is skipped the same way, which leaves what undoing it would: no work to put back."""

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(tree), *args],
                              capture_output=True, encoding="utf-8", env=env)  # fmt: skip

    done = git("rebase", "--continue")
    if done.returncode and _rebasing(tree) and not _unmerged(tree):
        empty = not git("diff", "--quiet", "HEAD").returncode
        if empty and not git("diff", "--cached", "--quiet", "HEAD").returncode:
            return git("rebase", "--skip")
    return done


def cmd_resolve(root: Path, ident: str | None, mode: str = "start") -> int:
    """Bring a change's branch up to date with the base branch when `base` refused on a conflict,
    leaving each conflicted file for the agent and doing every git step itself. `start` commits
    the uncommitted work as one temporary commit (`refs/sdlc/aside/<branch>`), rebases the branch
    onto the base and stops at the first conflict; `continue`, once the files hold no markers,
    stages them and goes on, stopping again at the next; when the rebase is done, the temporary
    commit is undone (a mixed reset), so the work is uncommitted on the new base, and the change's
    `conflicts.md` gets a section naming the files resolved. `abort` puts the worktree back where
    `start` found it, at any point before ship commits, keeping the resolved work under
    `refs/sdlc/end/<branch>` (`RESOLVE_REFS`). Ship's side file for it is
    `skills/ship/conflict.md`. `.sdlc/last-id` is settled by the script, never the agent. Never a
    stash, a merge of the base, `--force` or `--hard`; only the change's own branch moves."""
    trees = _change_trees(root)
    if ident is None:
        here = _git(root, "branch", "--show-current") or _rebase_branch(root) or ""
        ident = here if DIR_RE.match(here) else None
    found = [(t, b) for t, b in trees if names_change(b, ident)] if ident else []
    main = main_root(root)
    report: dict = {"change": ident, "state": None, "conflicted": [], "resolved": [],
                    "base": None, "undo": None, "reason": None}  # fmt: skip

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    def refuse(reason: str) -> int:
        report.update(state="refused", reason=reason)
        return emit(1)

    if len(found) != 1 or found[0][0].resolve() == main.resolve():
        return refuse("not in a change's worktree: nothing to resolve")
    tree, branch = found[0]
    git_cfg = load_config(main)[0]["git"]
    trunk = git_cfg["base"]
    report.update(change=branch, base=trunk)
    if why := trunk_refusal(main, trunk, git_cfg["base_source"]):
        return refuse(why)
    ref = {kind: _resolve_ref(kind, branch) for kind in RESOLVE_REFS}
    aside = _git(tree, "rev-parse", "--verify", "-q", ref["aside"])
    report["undo"] = f"sdlc.py resolve {branch} --abort" + (
        f" (the work as it was is commit {aside[:12]}, {ref['aside']})" if aside else ""
    )
    env = {**os.environ, "GIT_EDITOR": "true"}

    def finish() -> int:
        if aside and _git(tree, "log", "-1", "--format=%s") == ASIDE_MESSAGE:
            _git(tree, "reset", "-q", "HEAD^")
        _git(tree, "update-ref", ref["end"], _git(tree, "rev-parse", "HEAD") or "")
        files = list(dict.fromkeys(f for f in _pending(tree, branch) or [] if f))
        files = [f for f in files if f != f".sdlc/{LAST_ID}"]
        if files:
            path = tree / work_rel(tree) / branch / CONFLICTS
            path.parent.mkdir(parents=True, exist_ok=True)
            old = path.read_text(encoding="utf-8") if path.is_file() else "# Conflicts\n"
            sha = _git(tree, "rev-parse", "--short", trunk) or "?"
            section = f"\n## {date.today().isoformat()} onto {trunk} {sha}\n\n" + "".join(
                f"- {f}\n" for f in files
            )
            path.write_text(old.rstrip("\n") + "\n" + section, encoding="utf-8", newline="\n")
        _git(tree, "update-ref", "-d", ref["pending"])
        report.update(state="clean", resolved=files)
        return emit(0)

    def step() -> int:
        """Where the rebase stands now: a stop with files for the agent, or done."""
        while _rebasing(tree):
            _settle_last_id(tree)
            files = _unmerged(tree)
            if files:
                _set_pending(tree, branch, [*(_pending(tree, branch) or []), *files])
                report.update(state="conflict", conflicted=files)
                return emit(0)
            # Only `.sdlc/last-id` conflicted, and it is settled: go on.
            done = _go_on(tree, env)
            if done.returncode and not _unmerged(tree):
                return refuse(f"the rebase stopped: {(done.stderr or done.stdout).strip()[-300:]}")
        return finish()

    if mode == "continue":
        if not _rebasing(tree):
            if _pending(tree, branch) is not None:
                return finish()  # the rebase finished, and finish() didn't
            return refuse("no resolution is under way: run resolve first")
        files = _unmerged(tree)
        marked = [
            f for f in files
            if CONFLICT_MARKER_RE.search((tree / f).read_text(encoding="utf-8", errors="replace"))
        ]  # fmt: skip
        if marked:
            report["conflicted"] = files
            return refuse(f"conflict markers left in: {', '.join(marked)}")
        for f in files:
            _git(tree, "add", "--", f)
        done = _go_on(tree, env)
        if done.returncode and _rebasing(tree) and not _unmerged(tree):
            return refuse(f"the rebase won't go on: {(done.stderr or done.stdout).strip()[-300:]}")
        return step()

    if mode == "abort":
        start = _git(tree, "rev-parse", "--verify", "-q", ref["start"])
        if start is None:
            return refuse("no resolution to abort")
        if _rebasing(tree):
            _git_err(tree, "rebase", "--abort")
        else:
            end = _git(tree, "rev-parse", "--verify", "-q", ref["end"])
            if end is None or _git(tree, "rev-parse", "HEAD") != end:
                return refuse("the branch has moved since the resolution: nothing aborted")
            if _dirty_paths(tree):
                _git(tree, "add", "-A")
                _git(tree, "commit", "-q", "--no-verify", "-m", "sdlc: the resolved work, aborted")
                _git(tree, "update-ref", ref["end"], _git(tree, "rev-parse", "HEAD") or "")
            if err := _git_err(tree, "reset", "-q", "--keep", aside or start):
                return refuse(f"couldn't go back: {err}")
        if aside:
            _git(tree, "reset", "-q", start)
        for kind in ("start", "pending"):
            _git(tree, "update-ref", "-d", ref[kind])
        report.update(state="aborted", undo=None)
        return emit(0)

    # start
    if _rebasing(tree):
        return refuse("a resolution is under way: resolve --continue, or resolve --abort")
    if _pending(tree, branch) is not None:
        return refuse("an earlier resolution didn't finish: resolve --abort, then resolve again")
    before = _git(tree, "rev-parse", "HEAD") or ""
    behind = behind_trunk(main, branch, trunk)
    if behind is None:
        return refuse(f"no local {trunk} branch to bring it up to date with")
    if behind == 0:
        report.update(state="current")
        return emit(0)
    for kind in ("aside", "end"):
        _git(tree, "update-ref", "-d", ref[kind])
    _git(tree, "update-ref", ref["start"], before)
    aside = None
    if _dirty_paths(tree):
        _git(tree, "add", "-A")
        if err := _git_err(tree, "commit", "-q", "--no-verify", "-m", ASIDE_MESSAGE):
            _git(tree, "reset", "-q")
            return refuse(f"couldn't set the work aside: {err}")
        aside = _git(tree, "rev-parse", "HEAD")
        _git(tree, "update-ref", ref["aside"], aside or "")
        report["undo"] = (
            f"sdlc.py resolve {branch} --abort (the work as it was is commit {(aside or '')[:12]}, "
            f"{ref['aside']})"
        )
    else:
        report["undo"] = f"sdlc.py resolve {branch} --abort"
    _set_pending(tree, branch, [])
    err = _git_err(tree, "rebase", "-q", trunk)
    if err and not _rebasing(tree):
        if aside:
            _git(tree, "reset", "-q", before)
        for kind in ("start", "pending"):
            _git(tree, "update-ref", "-d", ref[kind])
        return refuse(f"rebasing onto {trunk} failed before any conflict: {err}")
    return step()


@command(
    "resolve",
    "bring a change's branch up to date when base refused on a conflict, file by file",
    arg("id", nargs="?", help="the change, e.g. 023 (default: this checkout's)"),
    exclusive(
        arg(
            "--continue", dest="cont", action="store_true",
            help="go on once the conflicted files hold no markers",
        ),
        arg("--abort", action="store_true", help="put the worktree back where resolve found it"),
    ),
)  # fmt: skip
def cli_resolve(root: Path, home: Path, args) -> int:
    mode = "continue" if args.cont else "abort" if args.abort else "start"
    return cmd_resolve(root, args.id, mode)


# What a stop needs from the person, by its way, in their words, not the factory's: an imperative
# like every other need, with no comma, since `status` joins a change's needs with one.
FACTORY_STOP_NEEDS = {
    "ship": "review an agent's commit",
    "mend": "rerun to ask an agent again",
    "rerun": "fix its cause and rerun",
}


def needs_of(rec: dict) -> list[str]:
    """What a change needs from the person, as short texts, from fields already read: `stage`,
    `tier`, `problems`, `stopped`, `land_stop`, `decision`, `reconsider`, `pending`, `assumed`,
    `ledger_lines`, `reasons`, `looks`, `gate` (the hand gate's record) and `spec_filled`. The
    one place the rules live, so the board and `status` can't disagree; it reads nothing itself.
    Every problem first, at any stage; at `test` or `shipped`, the landing's stages, a stopped
    landing (`land_stop`, `factory_records.read_land_stop()`), naming the step it stopped after;
    a closed change nothing more; at `build` a stop, then each blocking decision; at `test` with an
    ESCALATE what its ledger and decision still hold (each current `look` to acknowledge, and
    `gate it green` while a `gate` reason has no current green hand gate), or, with no reason and
    no ledger line at all, or a look reason not yet filed, the escalation itself; a Tier 2 at
    `plan` whose `spec.md` is written but whose stage never moved, its approval."""
    needs = [f"fix: {p}" for p in rec.get("problems") or []]
    stage = rec.get("stage")
    if stage in ("test", "shipped") and (stop := rec.get("land_stop")):
        needs.append(f"landing stopped at {stop.get('after') or 'a step'}")
    if stage in ("shipped", "dropped"):
        return needs
    pending = [f"decide {d['id']}" for d in rec.get("pending") or []]
    if stage == "build":
        if stop := rec.get("stopped"):
            way = FACTORY_STOP_NEEDS.get(stop.get("way") or "")
            needs.append(f"stopped: {way or f'read {factory_records.STOPPED.as_posix()}'}")
        needs += pending
    elif stage == "test" and rec.get("decision") == "ESCALATE":
        needs += pending
        if n := len(rec.get("assumed") or []):
            needs.append(f"confirm {n} default" + ("s" if n > 1 else ""))
        if rec.get("reconsider"):
            needs.append("reconsider the approach")
        needs += [f"acknowledge {d['id']}" for d in rec.get("looks") or []]
        reasons = rec.get("reasons") or []
        gate = rec.get("gate") or {}
        green = bool(gate.get("current")) and gate.get("verdict") == "PASS"
        if any(r["kind"] == "gate" for r in reasons) and not green:
            needs.append("gate it green")
        unfiled = any(r["kind"] == "look" and not r.get("filed") for r in reasons)
        if (not reasons and not rec.get("ledger_lines")) or unfiled:
            needs.append("read the escalation")
    elif stage == "plan" and rec.get("tier") == 2 and rec.get("spec_filled"):
        needs.append("approve its spec")
    return needs


def decide_step(rec: dict) -> str | None:
    """Where the person answers what an escalation at `test` still needs, from its `needs`: the
    factory's `/sdlc-factory:decide NNN`, while they hold a decision to make, defaults to confirm
    or a look to acknowledge; None otherwise. Status and the board both name it."""
    needs = rec.get("needs") or []
    asks = ("decide ", "confirm ", "acknowledge ")
    if rec.get("stage") != "test" or not any(n.startswith(asks) for n in needs):
        return None
    return f"/sdlc-factory:decide {rec['id']}"


def answered(rec: dict) -> bool:
    """An escalation the person has answered: an ESCALATE at `test` that needs nothing more, which
    `needs_of()` allows only with a ledger line or a reason, every line ticked, every gate reason
    cleared by a current green hand gate, and no `Reconsider` section."""
    return rec.get("stage") == "test" and rec.get("decision") == "ESCALATE" and not needs_of(rec)


# The board's columns, by the state of the work, the same for a change built by hand or by the
# factory (`board.html`'s `COLUMNS`, keyed as these): a stage's own column by its `stage:` line, or
# by `seen_stage()` for a change built by hand. `status` prints its sections by them too.
BY_STAGE = {"plan": "planned", "design": "designing", "build": "building", "ready": "ready"}


def column(entry: dict) -> str:
    """The board's column, by the state of the work, checked in this order: Needs you for a file
    that won't read, at any stage, or anything `needs_of()` names (a stop or a blocking decision
    at `build`, an escalation not yet cleared at `test`, a stopped landing, a written spec whose
    stage never moved), since a factory signal counts only at the stage it belongs to; Landing for
    a change committed and on its way (shipped or dropped and waiting on close, whatever the
    factory's files still say, or a factory landing in flight at `test`, `in_flight` from
    `factory_records.landing()`); Ready for a factory change at `test` the approver called READY,
    or whose escalation is answered, and a change built by hand whose review is written or whose
    gate is green (`seen_stage()`); else by how far it has got: Planned, Designing or Building (a
    factory change at `test` with no decision, a restart cut short, too). The one rule: the board
    and `status` both call it."""
    stage = entry["stage"]
    if entry["problems"] or entry.get("needs"):
        return "needs-you"
    if stage in ("shipped", "dropped") or entry.get("in_flight"):
        return "landing"
    if stage == "test" and entry["mode"] == "factory":
        ready = entry.get("decision") == "READY" or answered(entry)
        return "ready" if ready else "building"
    return BY_STAGE.get(entry.get("seen") or stage or "", "needs-you")


def seen_stage(entry: dict, folder: Path, home: Path, trunk: str | None) -> str | None:
    """How far a change built by hand has got, past what its `stage:` says: nothing moves that line
    between `plan` (or a Tier 2's `design`) and `shipped`, so the board and `status` read it.
    `ready` once ship's review has written `findings.md`, or once a gate run by hand passed on the
    build as it stands (`sdlc.py gate`'s record, current), and never while that record is current
    and red; `build` once the change touches a path outside the change folders and the plugin's
    own state, in its branch's commits or, in a worktree of its own, its uncommitted edits. None
    when neither says more, and always for a factory run, whose stage line the factory moves
    itself."""
    stage = entry["stage"]
    # A Tier 2 at `plan` has no spec yet: what it touches isn't its build.
    moving = ("plan", "design", "build") if entry["tier"] == 1 else ("design", "build")
    if entry["mode"] != "manual" or stage not in moving:
        return None
    gate = entry.get("gate") or {}
    red = gate.get("current") and gate.get("verdict") == "FAIL"
    green = gate.get("current") and gate.get("verdict") == "PASS"
    if not red and ((folder / "findings.md").is_file() or green):
        return "ready"
    if stage == "build":
        return None
    own = (f"{work_rel(home)}/", *(f".sdlc/{name}" for name in STATE_FILES))
    paths = touched_paths(entry, folder, home, trunk)
    return "build" if any(not p.startswith(own) for p in paths) else None


def touched_paths(entry: dict, folder: Path, home: Path, trunk: str | None) -> list[str]:
    """Every path the change has touched: what its branch changed against the base branch, and in
    a worktree of its own, its uncommitted edits. Nothing from the branch without a base branch."""
    paths = []
    if trunk:
        span = f"refs/heads/{trunk}...refs/heads/{entry['change']}"
        # `-z`, as `_dirty_paths()` reads them: unquoted, so both compare as the same text.
        out = _git(home, "diff", "-z", "--name-only", "--no-renames", span) or ""
        paths += out.split("\0")
    checkout = checkout_of(folder)
    if checkout.resolve() != home.resolve():
        paths += _dirty_paths(checkout)
    return [p for p in paths if p]


def rebasing_branches(root: Path, trees: list[tuple[Path, str]] | None = None) -> set[str]:
    """The branches a rebase is stopped on: it detaches the worktree's HEAD, so `worktrees()` no
    longer names them, and `_change_trees()` reads each from the rebase's own record. `trees` is
    that list when the caller already has it."""
    trees = _change_trees(root) if trees is None else trees
    return {b for _, b in trees} - {b for _, b in worktrees(root)}


def _change_base(
    main: Path, branch: str, rev: str | None = None, close: str | None = None
) -> str | None:
    """Where a change starts: where the base branch was when close merged it, as the `Close`
    commit `close` names says on its `Sdlc-Base:` line, or as close keeps it in `BASE_REF` between
    its runs. Before close wrote that, the parent of the commit that first holds its intent, which
    misses any commit the change made before its folder; `rev` is the change's own commit once
    its branch is gone, as retro reads it. None when nothing says."""
    said: dict = {}
    if close:
        said = metrics.parse_trailers(_git(main, "show", "-s", "--format=%B", close)) or {}
    for ref in (said.get("base"), BASE_REF + branch):
        if ref and (sha := _git(main, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}")):
            return sha
    added = _git(
        main, "log", "--diff-filter=A", "--format=%H", "--reverse", rev or branch, "--",
        f"{work_rel(main)}/{branch}/intent.md",
    )  # fmt: skip
    if not added:
        return None
    return _git(main, "rev-parse", "--verify", "-q", f"{added.split()[0]}^")


def _own_repo(main: Path) -> bool:
    """Whether the repo being closed is this plugin's own: its main checkout holds the `sdlc`
    manifest and `scripts/sdlc.py`. Read from its files, never guessed from where a script was
    loaded, so a host is never one."""
    try:
        manifest = json.loads((main / ".claude-plugin" / "plugin.json").read_text("utf-8"))
    except (OSError, ValueError):
        return False
    return (
        isinstance(manifest, dict)
        and manifest.get("name") == "sdlc"
        and (main / "scripts" / "sdlc.py").is_file()
    )


def _script_cmd() -> list[str]:
    """How a copy of this script is run, as the skills run it: `uv run --script`, or this
    interpreter where there is no `uv`."""
    uv = shutil.which("uv")
    return [uv, "run", "--quiet", "--script"] if uv else [sys.executable]


def landing_reach(paths: list[str]) -> dict:
    """What a landed change to this plugin asks of the sessions and hosts running it from a clone:
    `scripts` are live in every session at once, and so are the guides, read in place at each
    stage; `skills` and the `agents`, sdlc's and the factory's (by namespaced name), are read
    when a session starts, so need `/reload-plugins`, as does `settings` (the shared
    `.claude/settings.json`, its `enabledPlugins`; a new session for the rest), and `hosts`
    (setup's defaults and templates) need `/sdlc:setup` in each host. Only the kinds the paths
    touch."""
    scripts, skills, agents, hosts, settings = False, set(), set(), [], []
    for path in paths:
        parts = path.split("/")
        if parts[0] in ("scripts", "guide") or parts[:3] == ["plugins", "factory", "scripts"]:
            scripts = True
        elif parts[0] == "skills" and len(parts) > 2:
            skills.add(f"sdlc:{parts[1]}")
        elif parts[:3] == ["plugins", "factory", "skills"] and len(parts) > 4:
            skills.add(f"sdlc-factory:{parts[3]}")
        elif parts[:3] == ["plugins", "factory", "agents"] and path.endswith(".md"):
            agents.add(f"sdlc-factory:{parts[-1].removesuffix('.md')}")
        elif parts[0] == "agents" and len(parts) == 2 and path.endswith(".md"):
            agents.add(f"sdlc:{parts[1].removesuffix('.md')}")
        elif parts[0] in ("defaults", "templates"):
            hosts.append(path)
        elif path == ".claude/settings.json":
            settings.append(path)
    found = {
        "scripts": scripts, "skills": sorted(skills), "agents": sorted(agents),
        "settings": settings, "hosts": sorted(hosts),
    }  # fmt: skip
    return {k: v for k, v in found.items() if v}


# In the plugin's own repo, the commands ship runs from a change's worktree, the ones that write and
# the two whose reading the change may have changed, run the change's own `scripts/` once it edits
# them, so a change to ship or sync runs on its own code before it lands. The handoff comes before
# the arguments are parsed, so a flag only the change knows reaches it. The variable stops a second
# handoff, and set to anything by hand (`off`) skips the first.
OWN_SCRIPT_ENV = "SDLC_OWN_SCRIPT"
OWN_SCRIPT_CMDS = (
    "ship", "drop", "base", "resolve", "sync", "preflight", "findings", "run-cases", "gate",
)  # fmt: skip
OWN_RAN = "the change's own code"


def _own_script(root: Path) -> Path | None:
    """The change's own `scripts/sdlc.py` when this command should run it: in the plugin's own
    repo (`_own_repo()`, read from its files, so never a host), from a change's checkout whose
    branch edits `scripts/` against its merge base with the base branch, when that copy isn't the
    one running. None otherwise, and on any failure: a handoff is never a refusal."""
    try:
        if os.environ.get(OWN_SCRIPT_ENV):
            return None
        if not DIR_RE.match(_git(root, "branch", "--show-current") or ""):
            return None
        if not _own_repo(main_root(root)):
            return None
        trunk = load_config(main_root(root))[0]["git"]["base"]
        base = _git(root, "merge-base", trunk, "HEAD") if trunk else None
        if base is None:
            return None
        edited = _git(root, "diff", "--quiet", base, "--", "scripts") is None or bool(
            _git(root, "ls-files", "--others", "--exclude-standard", "--", "scripts")
        )
        script = root / "scripts" / "sdlc.py"
        running = (PLUGIN_DIR / "scripts" / "sdlc.py").resolve()
        return script if edited and script.is_file() and script.resolve() != running else None
    except Exception:
        return None


def _run_own(script: Path, argv: list[str]) -> int | None:
    """Run this command again as the change's own script, and give its output, saying so, and its
    exit code as this one's. None when that script crashed before it could answer (a traceback,
    or a failure with nothing said in the script's own voice: no stdout and no `⚠` line, as when
    `uv` can't start it), so the caller runs the command itself and the stage is never blocked by
    a half-built script. A refusal it prints, a `⚠` on stderr as ship's are, is its answer, never
    retried here with code that may not know to refuse."""
    made = subprocess.run(
        [*_script_cmd(), str(script), *argv],
        capture_output=True,
        encoding="utf-8",
        env=os.environ | {OWN_SCRIPT_ENV: "ran"},
    )
    voiced = made.stdout.strip() or any(
        ln.lstrip().startswith("⚠") for ln in made.stderr.splitlines()
    )
    if "Traceback (most recent call last)" in made.stderr or (made.returncode != 0 and not voiced):
        said = [ln for ln in made.stderr.splitlines() if ln.strip()]
        why = said[-1].strip() if said else f"exited {made.returncode}"
        print(
            f"⚠  the change's own {script} didn't run ({why}); running this copy instead",
            file=sys.stderr,
        )
        return None
    try:
        out = json.loads(made.stdout)
    except ValueError:
        out = None
    if isinstance(out, dict):
        out.setdefault("ran", OWN_RAN)
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(made.stdout, end="")
        # `preflight --question` prints ship's question, asked as printed: nothing after it.
        said = sys.stderr if argv[:1] == ["preflight"] else sys.stdout
        print(f"  ran {OWN_RAN}: {script}", file=said)
    print(made.stderr, end="", file=sys.stderr)
    return made.returncode


# ---------------------------------------------------------------- trackers
#
# Close mirrors a landed change's folder to a tracker before it removes the folder from main. A
# tracker is a module in scripts/trackers/ (`Tracker`, made by `make(home, cfg)`), loaded by path
# only when `archive.target` names it: with `none`, no tracker code runs at all. Core renders
# what the tracker shows; the tracker never reads .sdlc/, the change folder included.

# GitHub refuses an issue body or comment over 65,536 characters; this leaves room for the header.
ISSUE_LIMIT = 65_000
_TRACKERS: dict[str, object] = {}


def tracker(home: Path, cfg: dict):
    """The tracker `archive.target` names, or None for `none` (or a name with no module). By path,
    not import: `uv run --script` and the tests put different directories on sys.path."""
    target = cfg["archive"]["target"]
    if target == "none" or target not in ARCHIVE_TARGETS:
        return None
    mod = _TRACKERS.get(target)
    if mod is None:
        spec = importlib.util.spec_from_file_location(
            f"sdlc_tracker_{target}", TRACKER_DIR / f"{target}.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _TRACKERS[target] = mod
    return mod.make(home, cfg)


def archive_unavailable(home: Path, cfg: dict) -> str | None:
    """Why close can't archive here, or None when it can. Reads no network."""
    target = cfg["archive"]["target"]
    if target == "none":
        return "archive.target is none"
    if target not in ARCHIVE_TARGETS:
        return f"archive.target {target!r} isn't one of {'|'.join(ARCHIVE_TARGETS)}"
    return tracker(home, cfg).unavailable()


def _history_highest(home: Path) -> int:
    """The highest id a `Close` or `Drop` commit names on any branch, to seed a missing counter
    offline; 0 with none, or outside git. Only ever called when the counter is missing."""
    subjects = _git(home, "log", "--all", "--format=%s") or ""
    ids = [
        _number(m.group(1))
        for line in subjects.splitlines()
        if (m := re.match(rf"(?:{CLOSE_PREFIX}|{DROP_PREFIX})(\d{{3,}}-\S+)$", line))
    ]
    return max(ids, default=0)


# The issue's placeholders. A host template (`.sdlc/templates/issue.md`) may use any of them; the
# marker line is the script's, above the template, so no template can lose it.
ISSUE_FIELDS = (
    "title", "name", "tier", "stage", "impact", "branch", "commit", "depends_on", "updated",
    "problem", "outcome", "artifacts",
)  # fmt: skip
ARTIFACT_ORDER = {
    "intent.md": 0, "spec.md": 1, "plan.md": 2, "notes.md": 3, "checks.md": 4, "findings.md": 5,
}  # fmt: skip
HEADING_RE = re.compile(r"^(#{1,6}) ")


def _body_of(text: str) -> str:
    """An artifact without its frontmatter: the issue's table holds what that says."""
    if text.startswith("---\n") and (end := text.find("\n---", 4)) != -1:
        return text[end + 4 :].lstrip("\n")
    return text


def _section(text: str, heading: str) -> str:
    """The prose under `## heading` in an artifact, up to the next `## `; empty when absent."""
    out: list[str] = []
    inside = fenced = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            if inside:
                break
            inside = line[3:].strip().lower() == heading.lower()
            continue
        if inside:
            out.append(line)
    return "\n".join(out).strip()


BULLET_RE = re.compile(r"^- \*\*(.+?)\*\*")


def doc_units(text: str) -> list[tuple[str, str]]:
    """A doc's body cut into (key, text) blocks that run, in order, to the next block: what
    setup's drift compares one at a time. A block starts at a heading of level 2 to 4 or at a
    `- **lead**` bullet, outside code fences; what comes before the first is the preamble (`#`,
    the title and its note). A key is the path of headings above it, a bullet's ending with its
    lead, so two sections' `### Examples` stay apart. The blocks joined with newlines are the
    body again, which is what lets a refresh rewrite one and keep the rest as written."""
    units: list[tuple[str, list[str]]] = [("#", [])]
    path: list[tuple[int, str]] = []
    fenced = False
    for line in _body_of(text).splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
        elif not fenced and (m := HEADING_RE.match(line)) and 2 <= len(m.group(1)) <= 4:
            depth = len(m.group(1))
            path = [p for p in path if p[0] < depth] + [(depth, line.strip())]
            units.append((" > ".join(h for _, h in path), [line]))
            continue
        elif not fenced and (b := BULLET_RE.match(line)):
            where = " > ".join(h for _, h in path)
            units.append(((f"{where} > " if where else "") + f"- **{b.group(1)}**", [line]))
            continue
        units[-1][1].append(line)
    # A key met again (two `### Examples` under one section, a lead used twice) is numbered, so
    # every block is compared, and rewritten, on its own.
    seen: Counter[str] = Counter()
    out = []
    for key, lines in units:
        seen[key] += 1
        out.append((key if seen[key] == 1 else f"{key} ({seen[key]})", "\n".join(lines)))
    return out if out[0][1].strip() else out[1:]


def unit_hash(text: str) -> str:
    """A block's hash, blind to trailing spaces and to how many blank lines separate things, so
    reflowing a doc's whitespace isn't drift."""
    lines = [line.rstrip() for line in text.strip("\n").splitlines()]
    squeezed = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return "sha256:" + hashlib.sha256(squeezed.encode("utf-8")).hexdigest()[:16]


def _artifact_block(name: str, text: str) -> str:
    """One artifact as a collapsed section: its `# ` title dropped (the issue's title holds it),
    its headings demoted two levels so they sit under the issue's own, code fences untouched."""
    lines: list[str] = []
    sections: list[str] = []
    fenced = titled = False
    for line in _body_of(text).splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
        elif not fenced and (m := HEADING_RE.match(line)):
            if len(m.group(1)) == 1 and not titled:
                titled = True
                continue
            if len(m.group(1)) == 2:
                sections.append(line[3:].strip())
            line = "#" * min(len(m.group(1)) + 2, 6) + line[len(m.group(1)) :]
        lines.append(line)
    summary = f"<b>{name}</b>" + (f" — {' · '.join(sections)}" if sections else "")
    return (
        f"<details>\n<summary>{summary}</summary>\n\n{chr(10).join(lines).strip()}\n\n</details>\n"
    )


def render_issue(
    home: Path, folder: Path, rec: dict, branch: str | None, sha: str | None
) -> tuple[str, str, list[str]] | str:
    """(marker, body, comments): the change as its issue shows it, from the issue template. The
    artifacts stay in the body, in order, while it fits; the rest become one comment each, headed
    with a marker of their own so a rerun can tell what it posted. Why not, when one alone is too
    long for any of them."""
    name = folder.name
    marker = f"<!-- sdlc:{name} -->"
    files = sorted(folder.glob("*.md"), key=lambda p: (ARTIFACT_ORDER.get(p.name, 9), p.name))
    texts = {p.name: p.read_text(encoding="utf-8") for p in files}
    blocks = [(n, _artifact_block(n, t)) for n, t in texts.items()]
    intent = _body_of(texts.get("intent.md", ""))
    template = template_path(home, "issue.md")[0].read_text(encoding="utf-8")
    values = {
        "title": rec["title"] or name,
        "name": name,
        "tier": str(rec["tier"] or "?"),
        "stage": rec["stage"] or "?",
        "impact": rec["impact"] or "—",
        "branch": branch or name,
        "commit": f"`{sha}`" if sha else "—",
        "depends_on": ", ".join(f"{n:03d}" for n in rec.get("depends_on", [])) or "—",
        "updated": rec["updated"] or "?",
        "problem": _section(intent, "Problem") or "—",
        "outcome": _section(intent, "Outcome") or "—",
    }

    def fill(shown: list[tuple[str, str]], rest: list[str]) -> str:
        artifacts = "\n".join(b for _, b in shown)
        if rest:
            listed = ", ".join(f"`{n}`" for n in rest)
            artifacts += f"\n*Too long for this body, posted as comments at close: {listed}.*\n"
        body = template
        for key, value in {**values, "artifacts": artifacts}.items():
            body = body.replace("{{" + key + "}}", value)
        return f"{marker}\n{body}"

    keep = len(blocks)
    while keep and len(fill(blocks[:keep], [n for n, _ in blocks[keep:]])) > ISSUE_LIMIT:
        keep -= 1
    body = fill(blocks[:keep], [n for n, _ in blocks[keep:]])
    comments = [f"<!-- sdlc:{name}:{n} -->\n{b}" for n, b in blocks[keep:]]
    if any(len(p) > ISSUE_LIMIT for p in (body, *comments)):
        return f"an artifact is over GitHub's {ISSUE_LIMIT} characters; archive it by hand"
    return marker, body, comments


def closes_texts(name: str) -> dict[str, str]:
    """What the tracker posts on an issue a change's `closes:` line names: as it closes it where
    no push will (`fixed`), as it sends it back to triage when the change is dropped, and when the
    issue left the line with nothing else recording it (`withdrawn`, `withdraw_issues()`)."""
    return {
        "fixed": f"Fixed by {name}.",
        "dropped": f"{name} was dropped; this issue is open for triage again.",
        "withdrawn": f"{name} no longer takes this issue on; it is open for triage again.",
    }


def _tracker_change(home: Path, folder: Path, sha: str | None = None) -> dict:
    """What a tracker is handed about a change: its record, the checkout its folder is in, and
    the issue rendered from it. `sha` defaults to that checkout's HEAD."""
    rec = load_change(folder, home)
    branch = _git(folder, "branch", "--show-current") or folder.name
    sha = sha or _git(folder, "rev-parse", "--short", "HEAD")
    m = DIR_RE.match(folder.name)
    cfg = load_config(home)[0]
    change = {
        **rec,
        "name": folder.name,
        "id": m.group(1),
        "slug": m.group(2),
        "folder": folder,
        "sha": sha,
        "branch": branch,
        # The branch the change lands on, which a tracker compares with the repo's default.
        "base": cfg["git"]["base"],
        "marker": f"<!-- sdlc:{folder.name} -->",
        # The title the issue carries: the intent's heading without its id, as `new` opened it.
        "issue_title": TITLE_ID_RE.sub("", rec["title"]) or None,
        "body": "",
        "comments": [],
        "error": None,
        # The labels a tracker may set or remove.
        "vocabulary": {"tier": list(TIER_ARTIFACTS), "stage": STAGES, "impact": list(IMPACTS)},
        # The issue fields the project doc turns on, as the intent sets them; a tracker mirrors
        # these exactly and never reads or writes one that isn't here.
        "fields": {name: rec["fields"].get(name, []) for name in project_doc(home, cfg)[0]},
        # What the tracker posts on each issue the change's `closes:` line names, as it closes
        # them or, for a dropped change, sends them back to triage. Fixed text, the core's.
        "texts": closes_texts(folder.name),
    }
    parts = render_issue(home, folder, rec, branch, sha)
    if isinstance(parts, str):
        change["error"] = parts
    else:
        change["marker"], change["body"], change["comments"] = parts
    return change


# ---------------------------------------------------------------- where a number comes from


def state_path(home: Path, name: str) -> Path:
    """A file of the plugin's own state, as main has it: `.sdlc/<name>` in the main checkout,
    committed with the repo, in git or out of it."""
    return main_root(home) / ".sdlc" / name


def _write_state(where: Path, name: str, value: str) -> None:
    """Write `.sdlc/<name>` in the checkout `where`. Replaced, not rewritten in place, so a crash
    mid-write can't leave half a number."""
    path = where / ".sdlc" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(value, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def ids_mode(home: Path, cfg: dict) -> str:
    """`github` or `local`: where the next change's number comes from. GitHub's issue when the
    tracker numbers changes (`archive.target = "github"`), else the counter. Never a fallback
    from one to the other when GitHub is down: two schemes in one repo hand out a number twice."""
    target = cfg["archive"]["target"]
    numbers = target in ARCHIVE_TARGETS and target != "none" and tracker(home, cfg).numbers
    return "github" if numbers else "local"


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


# ---------------------------------------------------------------- release
#
# The release loop runs after a batch of closed changes, from the main checkout. History is the
# source: every `Close NNN-slug` commit since the current version's tag names a change, and the
# commit before it, the change's own, holds the intent.md whose `impact:` ship settled. `release`
# bumps the version files, commits and tags, undoable until pushed; `publish` pushes and runs the
# host's command. Close and release push too when `git.push` names them, behind their questions.

# One `version` line per version file: JSON's `"version": "1.2.0",`, TOML's `version = "1.2.0"`
# or Python's `__version__ = "1.2.0"`. Not `target-version = ...` or `my__version__ = ...`: the
# key must open the line.
VERSION_RE = re.compile(
    r'^([ \t]*(?:"?version"?|__version__)[ \t]*[:=][ \t]*")([^"\n]+)(".*)$', re.M
)
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
# Seconds before `release.after_bump` or `release.prepare` is stopped: a lock refresh or a build
# may resolve over the network.
AFTER_BUMP_TIMEOUT = 600
# Where release keeps what `release.prepare` printed, on the tag, for publish's approval to show:
# a ref of its own, since publish reads its `sdlc` note for the word `published`. Its last lines.
PREPARED_REF = "sdlc-prepared"
PREPARED_LINES = 40
PREPARED_CHARS = 4000


def _host_command(rel: dict, key: str, version: str, tag: str) -> tuple[str | None, str | None]:
    """`release.<key>` with `{version}` and `{tag}` filled in, shell-quoted, and None; or None and
    why, when the text holds a brace that isn't one of them (`${VAR}`, `{ …; }`), which
    `format()` would raise on."""
    try:
        return rel[key].format(version=shlex.quote(version), tag=shlex.quote(tag)), None
    except (KeyError, IndexError, ValueError):
        return None, (
            f"release.{key} may hold only {{version}} and {{tag}}: write a brace the shell needs "
            "as {{ or }}"
        )


def _read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def _tail(text: str) -> str:
    """The end of a host command's output, as much as an approval can show."""
    kept = "\n".join(text.rstrip().splitlines()[-PREPARED_LINES:])
    return kept[-PREPARED_CHARS:]


# Lowest first, so the index is the rank. `none` is listed in a release but never bumps it.
BUMPS = ("patch", "minor", "major")
CLOSE_PREFIX = "Close "
# A dropped change's record on main: a merge that keeps main's tree (`_drop_record`).
DROP_PREFIX = "Drop "
# Where a change starts, as close keeps it: the base branch's tip before the merge, in a ref of
# its own between close's runs (so a rerun after the fast-forward still knows it), then as a
# trailer on the `Close` commit, the ref going with the branch.
BASE_REF = "refs/sdlc/base/"
BASE_KEY = "Sdlc-Base"
# An intent's H1 is `# NNN — Title`; the notes carry the id once, in their own column.
TITLE_ID_RE = re.compile(r"^\d{3,}\s*[—–-]\s*")
# An intent's Outcome line saying what should change for users if it works: `**Moves O1:** …`.
MOVES_RE = re.compile(r"\*\*Moves (O\d+(?:,\s*O\d+)*):\*\*\s*(.+)")


def _semver(version: str) -> tuple[int, int, int]:
    m = SEMVER_RE.match(version)
    if not m:
        raise ValueError(version)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def read_versions(home: Path, cfg: dict) -> tuple[str | None, list[str]]:
    """The version the configured files agree on, or None and why not. Read as bytes, so a
    file's line endings are what `write_version` writes back."""
    found: dict[str, str] = {}
    problems: list[str] = []
    for rel in cfg["release"]["version_files"]:
        path = home / rel
        if not path.is_file():
            problems.append(f"release.version_files: {rel} doesn't exist")
            continue
        hits = VERSION_RE.findall(path.read_bytes().decode("utf-8"))
        if len(hits) != 1:
            problems.append(f"{rel}: {len(hits)} version lines, expected exactly one")
            continue
        found[rel] = hits[0][1]
    if len(set(found.values())) > 1:
        problems.append(
            "the version files disagree: " + ", ".join(f"{k} has {v}" for k, v in found.items())
        )
    elif found and not problems:
        version = next(iter(found.values()))
        if SEMVER_RE.match(version):
            return version, []
        problems.append(f"version {version!r} isn't X.Y.Z")
    return None, problems


def write_version(text: str, version: str) -> str:
    """`text` with its one version line's value replaced and every other byte as it was. Not a
    parse-and-dump round trip, which would reorder and reformat the file: `stamp_shipped`'s rule."""
    return VERSION_RE.sub(lambda m: m.group(1) + version + m.group(3), text, count=1)


# What one `[[shim]]` in `release.deprecations` holds: the first three always, `test` when a
# compatibility test covers it, so the test goes with the shim.
SHIM_KEYS = ("name", "remove_in", "where", "test")
SHIM_REQUIRED = SHIM_KEYS[:3]
# How `status` names each kind of shim `unreleased()` lists, in the order it prints them.
SHIM_STATES = {"overdue": " is overdue", "due": "", "unversioned": " (no version to compare)"}


def deprecations(home: Path, cfg: dict) -> dict:
    """The shims the host keeps, and what's wrong with its registry. Never raises: a bad entry is
    a problem naming it, and is left out of `shims`. `remove_in` must be a quoted X.Y.Z, so TOML
    can't read `1.10` as the number 1.1."""
    rel = cfg["release"]["deprecations"]
    out: dict = {"path": rel, "exists": False, "shims": [], "problems": []}
    path = home / rel
    if not path.is_file():
        return out
    out["exists"] = True
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        out["problems"].append(f"{rel} won't parse: {e}")
        return out
    entries = data.get("shim", [])
    if set(data) - {"shim"} or not isinstance(entries, list):
        out["problems"].append(f"{rel} may hold only [[shim]] tables")
        return out
    seen: set[str] = set()
    for n, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            out["problems"].append(f"{rel}: shim {n} isn't a table")
            continue
        label = f"shim {n}" + (f" ({entry['name']})" if isinstance(entry.get("name"), str) else "")
        wrong = [f"{k} is missing" for k in SHIM_REQUIRED if k not in entry]
        wrong += [f"{k} isn't a key a shim has" for k in entry if k not in SHIM_KEYS]
        for k in SHIM_KEYS:
            if k in entry and not isinstance(entry[k], str):
                wrong.append(f"{k} must be a " + ("quoted X.Y.Z" if k == "remove_in" else "string"))
        if isinstance(entry.get("remove_in"), str) and not SEMVER_RE.match(entry["remove_in"]):
            wrong.append(f"remove_in {entry['remove_in']!r} isn't X.Y.Z")
        if isinstance(entry.get("name"), str) and entry["name"] in seen:
            wrong.append("its name is used twice")
        if wrong:
            out["problems"] += [f"{rel}: {label}: {w}" for w in dict.fromkeys(wrong)]
            continue
        seen.add(entry["name"])
        out["shims"].append({k: entry.get(k) for k in SHIM_KEYS})
    return out


def shims_due(shims: list[dict], current: str | None, nxt: str | None) -> tuple[list, list]:
    """(overdue, due): the shims a version already released still carries, `remove_in` at or
    below `current`, and those the next release, `nxt`, would carry."""
    overdue = [s for s in shims if current and not _older(current, s["remove_in"])]
    due = [s for s in shims if s not in overdue and nxt and not _older(nxt, s["remove_in"])]
    return overdue, due


def next_version(version: str, impacts: list[str]) -> tuple[str | None, str | None]:
    """(the part bumped, the new version) for these impacts; (None, None) when none counts. Below
    1.0.0 a `major` is released as `minor`: 1.0.0 is its own decision, made with `--version`."""
    counted = [i for i in impacts if i in BUMPS]
    if not counted:
        return None, None
    part = max(counted, key=BUMPS.index)
    major, minor, patch = _semver(version)
    if part == "major" and major == 0:
        part = "minor"
    if part == "major":
        return part, f"{major + 1}.0.0"
    if part == "minor":
        return part, f"{major}.{minor + 1}.0"
    return part, f"{major}.{minor}.{patch + 1}"


def _change_record(name: str, text: str | None, sha: str, closed: bool, read: bool = True) -> dict:
    """One landed change from its intent.md's text: id, slug, title, tier, impact and created, the
    sha of the change's own commit, and under `problems` what's wrong with it. With `read` off,
    only what its name says."""
    m = DIR_RE.match(name)
    rec: dict = {"id": m.group(1), "slug": m.group(2), "name": name, "title": "", "tier": None}
    rec.update(impact="", created="", idea="", problem="", sha=sha, closed=closed, problems=[])
    rec["ideas"] = []
    rec.update(serves=None, moves=[], reworks=[], fixes=[])
    if not read:
        return rec
    try:
        post = frontmatter.loads(text) if text is not None else None
    except Exception:
        post = None
    if post is None:
        rec["problems"].append(f"{name}: its commit {sha} has no readable intent.md")
        return rec
    rec["tier"] = post.get("tier")
    rec["impact"] = str(post.get("impact") or "")
    rec["created"] = str(post.get("created") or "")
    rec["ideas"] = intent_ideas(text or "")
    rec["idea"] = (rec["ideas"] or [""])[0]
    rec["reworks"] = reworks(text or "")
    rec["fixes"] = frontmatter_list(text or "", "fixes") or []
    for line in (post.content or "").splitlines():
        if line.startswith("# "):
            rec["title"] = TITLE_ID_RE.sub("", line[2:].strip())
            break
    rec["problem"] = first_paragraph(post.content or "", "Problem")
    rec["serves"] = frontmatter_list(text, "serves")
    rec["moves"] = [
        {"ids": re.split(r",\s*", m[1]), "text": m[2].strip()}
        for m in MOVES_RE.finditer(_section(post.content or "", "Outcome"))
    ]
    if str(post.get("stage") or "") == "dropped":
        # As text: how far it got, and why it stopped. It never settles an impact.
        rec["dropped_at"] = (frontmatter_list(text, "dropped_at") or [""])[0] or "unknown"
        rec["reason"] = first_paragraph(post.content or "", DROPPED)
        return rec
    if rec["impact"] not in IMPACTS:
        rec["problems"].append(
            f"{name}: impact must be one of {'|'.join(IMPACTS)}, got {rec['impact']!r} in {sha}"
        )
    return rec


def closed_changes(
    home: Path, since: str | None, trunk: str | None, read: bool = True
) -> list[dict]:
    """Every change closed on the base branch `trunk` after `since` (all of it when None), oldest
    first, from history alone: each `Close NNN-slug` commit on the base's first-parent line names
    one, and its parent, the change's own commit, holds the intent. First parent only: close
    fast-forwards, so the base's own line is every change in order. `read=False` skips the
    intents, for a count. Each record adds the `Close` commit's sha and date (`close_sha`,
    `close_date`); `sha` is the change's own commit. The release loop reads it from the last tag,
    the retrospective from its own boundary. No base branch, no changes."""
    if not trunk:
        return []
    span = f"{since}..{trunk}" if since else trunk
    fmt = "--format=%h%x00%p%x00%cs%x00%cI%x00%s"
    log = _git(home, "log", "--first-parent", "--reverse", fmt, span) or ""
    found = []
    for line in log.splitlines():
        close_sha, parent, close_date, close_at, subject = (line.split("\x00") + [""] * 4)[:5]
        name = subject[len(CLOSE_PREFIX) :].strip() if subject.startswith(CLOSE_PREFIX) else ""
        if DIR_RE.match(name) and parent:
            at = f"{close_sha}^:{work_rel(home)}/{name}/intent.md"
            text = _git(home, "show", at) if read else None
            rec = _change_record(name, text, parent, closed=True, read=read)
            # What close measured, on its own commit, and what ship's review found and who
            # landed it (a factory landing's `Sdlc-Landed`), on the change's: all trailers.
            rec["metrics"] = rec["findings"] = rec["landed"] = None
            if read:
                rec["metrics"] = metrics.parse_trailers(
                    _git(home, "show", "-s", "--format=%B", close_sha)
                )
                own = metrics.parse_trailers(_git(home, "show", "-s", "--format=%B", parent))
                rec["findings"] = (own or {}).get("findings")
                rec["landed"] = (own or {}).get("landed")
            found.append(
                {**rec, "close_sha": close_sha, "close_date": close_date, "close_at": close_at}
            )
    return found


def dropped_changes(home: Path, since: str | None, trunk: str | None) -> list[dict]:
    """Every change dropped on the base branch `trunk` after `since` (all of it when None), oldest
    first: each `Drop NNN-slug` commit on the base's first-parent line names one, and its second
    parent, the branch's tip, holds the intent with `dropped_at:` and the reason. Never counted by
    a release, which reads only `Close` commits. Each record adds `drop_sha`, `drop_date` and
    `days_open`."""
    if not trunk:
        return []
    span = f"{since}..{trunk}" if since else trunk
    fmt = "--format=%h%x00%P%x00%cs%x00%s"
    log = _git(home, "log", "--first-parent", "--reverse", fmt, span) or ""
    found = []
    for line in log.splitlines():
        drop_sha, parents, drop_date, subject = (line.split("\x00") + ["", "", ""])[:4]
        name = subject[len(DROP_PREFIX) :].strip() if subject.startswith(DROP_PREFIX) else ""
        tip = parents.split()[1:2]
        if DIR_RE.match(name) and tip:
            text = _git(home, "show", f"{drop_sha}^2:{work_rel(home)}/{name}/intent.md")
            rec = _change_record(name, text, tip[0][:7], closed=False)
            rec.update(drop_sha=drop_sha, drop_date=drop_date)
            rec["days_open"] = _days_between(rec["created"], drop_date)
            # What close measured before it recorded the drop, as on a `Close` commit.
            rec["metrics"] = metrics.parse_trailers(
                _git(home, "show", "-s", "--format=%B", drop_sha)
            )
            found.append(rec)
    return found


def _release_tag(rel: dict, version: str) -> tuple[str | None, str | None]:
    """The tag `release.tag` names for `version`, or why it can't: a host's template is input,
    and bad input is reported rather than raised."""
    try:
        return rel["tag"].format(version=version), None
    except (KeyError, IndexError, ValueError):
        return None, f"release.tag {rel['tag']!r} may hold only {{version}}"


def _adoption_commit(home: Path) -> str | None:
    """The commit that first added `.sdlc/config.toml`: where the repo took the plugin up. The
    oldest add, `log`'s last line, since `-1 --reverse` limits before it reverses."""
    out = _git(home, "log", "--diff-filter=A", "--format=%h", "--", f"{HOST_DIR}/config.toml")
    return out.splitlines()[-1] if out else None


def unreleased(home: Path, cfg: dict, open_ids: list[str] | None = None, read: bool = True) -> dict:
    """Every change landed on main since the current version's tag, from history, with the bump
    they add up to. Read-only. `next` is set only when nothing stands in the way of a release.
    `open_ids`, when the caller has them, saves analyzing the changes twice; `read=False` lists
    without reading intents, which is all `status` needs while nothing is configured."""
    rel = cfg["release"]
    out: dict = {
        "version": None,
        "tag": None,
        "since": None,
        "changes": [],
        "open": [],
        "problems": [],
        "missing": None,
        "configure": None,
        "bump": None,
        "next": None,
        "nothing": False,
        "due": None,
    }
    if not rel["version_files"]:
        out["configure"] = "release.version_files"
    else:
        version, problems = read_versions(home, cfg)
        out["problems"] += problems
        if version:
            out["version"] = version
            tag, problem = _release_tag(rel, version)
            out["tag"] = tag
            if problem:
                out["problems"].append(problem)
            elif _git(home, "rev-parse", "-q", "--verify", f"refs/tags/{tag}") is not None:
                out["since"] = tag
            else:
                last = _git(home, "log", "-1", "--format=%h", "--", *rel["version_files"])
                adopt = _adoption_commit(home)
                at = last or adopt or "<the commit that released it>"
                # A version older than the plugin's adoption would take every change closed
                # since into the first release: tag where the repo took the plugin up instead.
                later = last and adopt and last != adopt
                if later and _git_err(home, "merge-base", "--is-ancestor", last, adopt) is None:
                    at = adopt
                out["missing"] = {"tag": tag, "hint": f'git tag -a {tag} -m "{tag}" {at}'}

    trunk = cfg["git"]["base"]
    if not trunk:
        out["problems"].append(trunk_refusal(home, trunk))
    out["changes"] = closed_changes(home, out["since"], trunk, read)
    # A close that stopped after its merge leaves the change's folder on main, shipped: landed,
    # so it is in this release, though not yet closed. Its sha is the commit that shipped it.
    base = work_dir(home)
    landed = sorted(base.iterdir(), key=lambda p: _number(p.name)) if base.is_dir() else []
    for folder in landed:
        intent = f"{work_rel(home)}/{folder.name}/intent.md"
        if DIR_RE.match(folder.name) and _shipped(folder) and _git(home, "ls-files", intent):
            sha = _git(home, "log", "-1", "--format=%h", "--", intent) or "?"
            text = (folder / "intent.md").read_text(encoding="utf-8")
            out["changes"].append(_change_record(folder.name, text, sha, False, read))
    for rec in out["changes"]:
        out["problems"] += rec.pop("problems")
    if open_ids is None:
        open_ids = [f"{r['id']}-{r['slug']}" for r in analyze(home)["open"]]
    out["open"] = open_ids
    # A bad registry blocks the bump the way a bad intent does: release can't tell what is due.
    reg = deprecations(home, cfg)
    out["problems"] += reg["problems"]

    if out["version"] and not out["missing"] and not out["problems"]:
        out["bump"], out["next"] = next_version(
            out["version"], [c["impact"] for c in out["changes"]]
        )
        out["nothing"] = out["next"] is None
        if out["next"]:
            out["due"] = release_due(out["changes"], rel, date.today())
    overdue, due = shims_due(reg["shims"], out["version"], out["next"])
    unversioned = [] if out["version"] else reg["shims"]
    out["deprecations"] = {"overdue": overdue, "due": due, "unversioned": unversioned}
    return out


def release_due(changes: list[dict], rel: dict, today: date) -> dict:
    """Whether the unreleased batch is big or old enough that `status` recommends releasing it:
    any `major`, `due_after_changes` changes of impact minor or higher, or the oldest close
    `due_after_days` old. A change landed but not closed has no close date and no age. Never
    refuses anything: `/sdlc:release` runs whenever a person chooses."""
    counted = [c for c in changes if c.get("impact") in ("major", "minor")]
    dates = sorted(c["close_date"] for c in changes if c.get("close_date"))
    oldest = _days_between(dates[0], today.isoformat()) if dates else None
    n, days = rel["due_after_changes"], rel["due_after_days"]
    why = []
    majors = [c["id"] for c in changes if c.get("impact") == "major"]
    if majors:
        why.append(f"major change {', '.join(majors)}")
    if n and len(counted) >= n:
        why.append(f"{len(counted)} changes of minor impact or higher")
    if days and oldest is not None and oldest >= days:
        why.append(f"the oldest closed {oldest}d ago")
    return {"due": bool(why), "why": why, "minor": len(counted), "oldest": oldest}


def release_notes(changes: list[dict], github: bool) -> str:
    """One line per change: its number, title and impact, and its issue when GitHub numbers it."""
    return "\n".join(
        f"- {c['id']} {c['title'] or c['slug']} ({c['impact']})"
        + (f" #{int(c['id'])}" if github else "")
        for c in changes
    )


# The line a host's changelog marks where releases go with: each new section goes right after it.
CHANGELOG_MARKER = "<!-- sdlc:releases -->"


def changelog_section(home: Path, version: str, notes: str, today: str) -> str:
    """This release's changelog section, from the changelog template (the host's, else the
    plugin's), ending in one newline. Filled by `str.replace`, so a brace in a note is text, and
    `{{notes}}` last, so a placeholder a note holds stays as written."""
    text = template_path(home, "changelog.md")[0].read_text(encoding="utf-8")
    text = text.replace("{{version}}", version).replace("{{date}}", today)
    return text.replace("{{notes}}", notes).rstrip("\r\n") + "\n"


def with_changelog(text: str, section: str) -> str:
    """`text` with this release's section added: right after the first `CHANGELOG_MARKER` line
    when there is one, every byte above it kept; else on top, under its `# ` title when it has
    one."""
    lines = text.splitlines(keepends=True)
    at = next((i for i, line in enumerate(lines) if line.strip() == CHANGELOG_MARKER), None)
    if at is not None:
        head = "".join(lines[: at + 1])
        head += "" if head.endswith("\n") else "\n"
        rest = lines[at + 1 :]
        while rest and not rest[0].strip():
            rest.pop(0)
        return f"{head}\n{section}" + (f"\n{''.join(rest)}" if rest else "")
    first, _, rest = text.partition("\n")
    if first.startswith("# "):
        rest = rest.lstrip("\n")
        return f"{first}\n\n{section}" + (f"\n{rest}" if rest else "")
    return section + (f"\n{text}" if text else "")


def _git_err(root: Path, *args: str) -> str | None:
    """None when the git command succeeds, else what it said: never empty, since a hook can fail
    a command without a word."""
    made = subprocess.run(["git", "-C", str(root), *args], capture_output=True, encoding="utf-8")
    if made.returncode == 0:
        return None
    return made.stderr.strip() or made.stdout.strip() or f"exited {made.returncode}"


def _release_refusals(root: Path, home: Path, cfg: dict) -> list[str]:
    """Where a release step may run: the main checkout, on the base branch, with nothing
    uncommitted."""
    refusals = []
    if root.resolve() != home.resolve():
        refusals.append(f"run it from the main checkout ({home}), not a change's worktree")
    trunk = cfg["git"]["base"]
    if why := trunk_refusal(home, trunk, cfg["git"]["base_source"]):
        refusals.append(why)
    elif _git(home, "branch", "--show-current") != trunk:
        refusals.append(f"the main checkout ({home}) isn't on {trunk}")
    if _git(home, "status", "--porcelain", "--untracked-files=no") not in ("", None):
        refusals.append(f"the main checkout ({home}) has uncommitted changes")
    return refusals


def _untracked(home: Path) -> set[str]:
    """The untracked files git doesn't ignore, by path from the repo root."""
    out = _git(home, "ls-files", "--others", "--exclude-standard", "-z") or ""
    return {p for p in out.split("\0") if p}


def _put_back(home: Path, paths: list[str]) -> None:
    """Put these paths back as HEAD has them: unstaged, and their HEAD text checked out. A path
    HEAD lacks is left untracked, never deleted, and kept out of the checkout, whose whole
    pathspec git refuses over one path it can't match."""
    if not paths:
        return
    _git(home, "reset", "-q", "HEAD", "--", *paths)
    out = _git(home, "ls-tree", "-r", "--name-only", "-z", "HEAD", "--", *paths) or ""
    if known := [p for p in out.split("\0") if p]:
        _git(home, "checkout", "-q", "--", *known)


def _lean(records: list[dict], metrics: bool) -> list[dict]:
    """Each change as printed: without the `metrics` its `Close` commit's trailers hold, which no
    skill reads one change at a time, unless `metrics` asks for them. Only what is printed loses
    them: every aggregate is built from the full records first."""
    return records if metrics else [{k: v for k, v in r.items() if k != "metrics"} for r in records]


def cmd_unreleased(root: Path, metrics: bool = False) -> int:
    """The changes since the last release, as JSON, each one's measured numbers only with
    `metrics`. Writes nothing."""
    home = main_root(root)
    cfg, _, parsed = load_config(home)
    out = unreleased(home, cfg)
    out["changes"] = _lean(out["changes"], metrics)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if parsed else 1


METRICS_HELP = "each change's measured numbers too, from its Close commit's trailers"


@command(
    "unreleased",
    "the changes landed since the last release tag, as JSON; writes nothing",
    arg("--metrics", action="store_true", help=METRICS_HELP),
)
def cli_unreleased(root: Path, home: Path, args) -> int:
    return cmd_unreleased(root, args.metrics)


def cmd_release(
    root: Path, check_only: bool = False, version: str | None = None, metrics: bool = False
) -> int:
    """Bump the version files, add the changelog section, commit `Release X.Y.Z` and tag it. All
    local: undone with `git tag -d` and `git reset --keep HEAD~1` until publish pushes it. Every
    refusal is found before anything is written."""
    home = main_root(root)
    cfg, _, parsed = load_config(home)
    rel = cfg["release"]
    u = unreleased(home, cfg)
    report: dict = {
        "version": u["version"],
        "next": None,
        "tag": None,
        "files": [*rel["version_files"], *([rel["changelog"]] if rel["changelog"] else [])],
        "changes": _lean(u["changes"], metrics),
        "notes": "",
        "refusals": _release_refusals(root, home, cfg),
        "done": [],
        "skipped": [],
        "undo": None,
    }

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    refusals = report["refusals"]
    if not parsed:
        refusals.append(f"{HOST_DIR}/config.toml won't parse")
    if u["configure"]:
        refusals.append(
            "set release.version_files in .sdlc/config.toml: the files that hold the version"
        )
    if u["missing"]:
        refusals.append(
            f"no tag {u['missing']['tag']} for the current version, so the release has no "
            f"boundary. Tag the commit that released it: {u['missing']['hint']}"
        )
    refusals += u["problems"]
    new = u["next"]
    if version is not None:
        if not SEMVER_RE.match(version):
            refusals.append(f"--version {version!r} isn't X.Y.Z")
        elif u["version"] and _semver(version) <= _semver(u["version"]):
            refusals.append(f"--version {version} isn't greater than {u['version']}")
        elif not u["changes"]:
            refusals.append(f"nothing has landed since {u['since']}: there is nothing to release")
        else:
            new = version
    elif u["nothing"]:
        refusals.append(
            f"nothing to release: no change since {u['since']} has an impact other than none"
        )
    # Against the version this release cuts, so a --version past a shim's remove_in is caught too.
    if new:
        overdue, due = shims_due(deprecations(home, cfg)["shims"], u["version"], new)
        for s in overdue + due:
            test = f"; its test: {s['test']}" if s["test"] else ""
            refusals.append(
                f"shim {s['name']} is due by {new}: remove it first ({s['where']}{test})"
            )
    if new and not refusals:
        tag, _ = _release_tag(rel, new)  # a bad template is already one of `problems`
        if tag and _git(home, "rev-parse", "-q", "--verify", f"refs/tags/{tag}") is not None:
            refusals.append(f"tag {tag} already exists")
        report.update(next=new, tag=tag, undo=f"git tag -d {tag} && git reset --keep HEAD~1")
        report["notes"] = release_notes(u["changes"], ids_mode(home, cfg) == "github")
        for key in ("after_bump", "prepare"):
            if rel[key]:
                report[key], problem = _host_command(rel, key, new, tag)
                if problem:
                    refusals.append(problem)
        if rel["after_bump"]:
            report["untracked"] = []
        report["push"] = closing._push_plan(home, cfg, "release")
    if refusals:
        return emit(1)

    tag, notes = report["tag"], report["notes"]
    created: list[str] = []  # files the release wrote that weren't there, which restore removes

    def bump() -> str | None:
        for rel_path in rel["version_files"]:
            path = home / rel_path
            path.write_bytes(write_version(path.read_bytes().decode("utf-8"), new).encode("utf-8"))
        return None

    def changelog() -> str | None:
        path = home / rel["changelog"]
        if not path.is_file():
            created.append(rel["changelog"])
        text = path.read_bytes().decode("utf-8") if path.is_file() else "# Changelog\n"
        section = changelog_section(home, new, notes, date.today().isoformat())
        path.write_bytes(with_changelog(text, section).encode())
        return None

    def restore() -> None:
        # Put the files back, so a rerun finds main clean and the same release to make.
        _put_back(home, report["files"])
        for rel_path in created:
            (home / rel_path).unlink(missing_ok=True)
        # Putting back leaves a new file after-bump staged untracked, whichever step failed: only
        # the release's own files are added, never what `prepare` built.
        if "untracked" in report:
            now = _untracked(home)
            left = {p for p in report["files"] if p in now}
            report["untracked"] = sorted(set(report["untracked"]) | left)

    def after_bump() -> str | None:
        # Main had no uncommitted tracked changes (`_release_refusals`), so every tracked file
        # changed now beyond the release's own is the command's. New untracked files are listed,
        # never committed: they may be anything the command leaves behind.
        before = _untracked(home)
        err = None
        try:
            ran = subprocess.run(
                _sh(report["after_bump"]), cwd=home, capture_output=True, encoding="utf-8",
                errors="replace", timeout=AFTER_BUMP_TIMEOUT, stdin=subprocess.DEVNULL,
            )  # fmt: skip
            if ran.returncode != 0:
                why = ran.stderr.strip()[:500] or "no output"
                err = f"release.after_bump exited {ran.returncode}: {why}"
        except subprocess.TimeoutExpired:
            err = f"release.after_bump timed out after {AFTER_BUMP_TIMEOUT}s"
        except OSError as e:
            err = f"release.after_bump didn't run: {e}"
        # Against HEAD, so a file the command staged is seen as well as one it only changed.
        changed = (_git(home, "diff", "--name-only", "-z", "HEAD") or "").split("\0")
        report["files"] += [p for p in changed if p and p not in report["files"]]
        if err:
            restore()
        # After restore, which leaves a new file the command staged untracked.
        report["untracked"] = sorted(_untracked(home) - before)
        return err

    def tracked_changes() -> set[str]:
        return {p for p in (_git(home, "diff", "--name-only", "-z", "HEAD") or "").split("\0") if p}

    def prepare() -> str | None:
        # A build, never part of the release commit: every tracked file it changes is put back
        # and refused, so the commit still holds only what the release meant.
        before = tracked_changes()
        # The release's own files are changed already, so a further edit shows only in their text.
        held = {p: _read_bytes(home / p) for p in report["files"]}
        err = None
        try:
            ran = subprocess.run(
                _sh(report["prepare"]), cwd=home, capture_output=True, encoding="utf-8",
                errors="replace", timeout=AFTER_BUMP_TIMEOUT, stdin=subprocess.DEVNULL,
            )  # fmt: skip
            if ran.returncode != 0:
                why = ran.stderr.strip()[:500] or "no output"
                err = f"release.prepare exited {ran.returncode}: {why}"
            else:
                report["prepared"] = _tail(ran.stdout)
        except subprocess.TimeoutExpired:
            err = f"release.prepare timed out after {AFTER_BUMP_TIMEOUT}s"
        except OSError as e:
            err = f"release.prepare didn't run: {e}"
        others = tracked_changes() - before - set(report["files"])
        touched = sorted(others | {p for p, b in held.items() if _read_bytes(home / p) != b})
        if others:
            _put_back(home, sorted(others))
        if touched:
            err = err or (
                f"release.prepare changed tracked files: {', '.join(touched)}; build into an "
                "untracked or ignored path"
            )
        if err:
            report.pop("prepared", None)
            restore()
        return err

    def note() -> str | None:
        # The tag exists now, so a failure here can't stop a release that a rerun would refuse:
        # it is said, and publish shows nothing prepared.
        text = report.get("prepared") or "(no output)"
        err = _git_err(home, "notes", "--ref", PREPARED_REF, "add", "-f", "-m", text, tag)
        if err:
            report["note_error"] = err
        return None

    def commit() -> str | None:
        err = _git_err(home, "add", "--", *report["files"]) or _git_err(
            home, "commit", "-q", "-m", f"Release {new}", "-m", notes
        )
        if err:
            restore()
        return err

    steps = [
        ("version files", bump),
        *([("changelog", changelog)] if rel["changelog"] else []),
        *([("after bump", after_bump)] if rel["after_bump"] else []),
        *([("prepare", prepare)] if rel["prepare"] else []),
        ("commit", commit),
        ("tag", lambda: _git_err(home, "tag", "-a", tag, "-m", tag, "-m", notes)),
        *([("note", note)] if rel["prepare"] else []),
    ]
    # In this plugin's repo, what release's question says of the skills' cases: advice, never a
    # refusal.
    cases = _cases_report(home, None)
    if cases["available"]:
        report["cases"] = {"last_full": cases["last_full"], "claude": _claude_version(),
                           "full_history": cases["full_history"]}  # fmt: skip
    if check_only:
        report["skipped"] = [f"{name} (--check)" for name, _ in steps]
        return emit(0)
    for i, (name, step) in enumerate(steps):
        err = step()
        if err:
            report["skipped"] = [n for n, _ in steps[i:]]
            refusals.append(f"{name} failed: {err}")
            return emit(1)
        report["done"].append(name)
    if report["push"]["on"]:
        # The release is made either way: a push that fails is said, and publish finishes it.
        trunk = cfg["git"]["base"]
        for ref in (f"refs/heads/{trunk}", f"refs/tags/{tag}"):
            if err := closing._push(home, report["push"]["remote"], ref):
                report["push_failed"] = f"{err}; /sdlc:publish pushes it"
                break
        else:
            report["done"].append("push")
    # With the new tag counted: a release is the usual moment a retrospective falls due.
    report["retro_due"] = retro_due(home, cfg)
    return emit(0)


@command(
    "release",
    "bump the version files, commit `Release X.Y.Z` and tag it, locally",
    arg("--check", action="store_true", help="the plan only, write nothing"),
    arg("--version", help="release as X.Y.Z instead of the computed version"),
    arg("--metrics", action="store_true", help=METRICS_HELP),
)
def cli_release(root: Path, home: Path, args) -> int:
    return cmd_release(root, args.check, args.version, args.metrics)


def _remote_sha(home: Path, remote: str, ref: str) -> str | None:
    out = _git(home, "ls-remote", remote, ref)
    return out.split()[0] if out else None


# Where publish keeps a run's `published` note on each tag, and the mirror of the remote's copy
# it fetches into, so a second clone skips an upload another one made.
NOTES_REF = "refs/notes/sdlc"
NOTES_MIRROR = "refs/notes/sdlc-remote"


def _fetch_notes(home: Path, remote: str) -> str | None:
    """Fold the remote's publish notes into this repo's; why not, or None. Called only by
    `cmd_publish`, after its approval. A remote with none is nothing to do. Fetched into a mirror,
    never forced, then merged: notes held here and not there (a push the remote refused) are kept,
    and both sides only ever say `published`, so the merge can't conflict. Like the one push, it
    never asks: no terminal prompt and stdin closed."""
    if _remote_sha(home, remote, NOTES_REF) is None:
        return None
    made = subprocess.run(
        ["git", "-C", str(home), "fetch", "-q", remote, f"{NOTES_REF}:{NOTES_MIRROR}"],
        capture_output=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )  # fmt: skip
    if made.returncode != 0:
        return made.stderr.strip() or made.stdout.strip() or f"exited {made.returncode}"
    return _git_err(
        home, "notes", "--ref", NOTES_REF, "merge", "-q", "-s", "cat_sort_uniq", NOTES_MIRROR
    )


def _pushed(home: Path, remote: str, ref: str) -> bool:
    """Whether the remote holds `ref` as this repo does: a rerun's push is skipped, not repeated."""
    return _remote_sha(home, remote, ref) == _git(home, "rev-parse", ref)


def _unpushed(home: Path, cfg: dict) -> dict | None:
    """What the base branch holds that its remote-tracking ref doesn't: each commit, the
    closed and dropped changes among them, the oldest one's age, and the issues their closing
    lines would close, read by the tracker's `closed_by()` when it has one. Read locally, never
    over the network, so a tracking ref older than the remote under-counts and never errs; None
    with no tracking ref to compare against."""
    remote, trunk = cfg["release"]["remote"], cfg["git"]["base"]
    if not trunk:
        return None
    ref = f"refs/remotes/{remote}/{trunk}"
    if _git(home, "rev-parse", "-q", "--verify", ref) is None:
        return None
    out = _git(home, "log", "--format=%h%x02%s%x02%ct%x02%b%x03", f"{ref}..{trunk}") or ""
    found: dict = {"remote": remote, "branch": trunk, "ahead": [], "changes": 0, "closes": []}
    closed_by = getattr(tracker(home, cfg), "closed_by", None)
    oldest = None
    for rec in out.split("\x03"):
        if not rec.strip():
            continue
        sha, subject, when, body = rec.strip("\n").split("\x02", 3)
        found["ahead"].append(f"{sha} {subject}")
        for prefix in (CLOSE_PREFIX, DROP_PREFIX):
            if subject.startswith(prefix) and DIR_RE.match(subject[len(prefix) :]):
                found["changes"] += 1
                oldest = int(when)  # newest first, so the last one seen is the oldest
                found["closes"] += closed_by(body) if closed_by else []
    found["closes"].sort()
    now = datetime.now(UTC).timestamp()
    found["oldest_days"] = None if oldest is None else int((now - oldest) // 86400)
    return found


def unpushed_line(up: dict) -> str:
    """`_unpushed()` in one line: how many closed changes, how old, and the issues a push closes."""
    n, days = up["changes"], up["oldest_days"]
    line = f"{n} closed change{'s' if n != 1 else ''} not on {up['remote']}/{up['branch']}"
    line += f", oldest {days}d" if days is not None else ""
    line += f" ({len(up['ahead'])} commits)"
    if up["closes"]:
        line += "; a push closes " + ", ".join(f"#{i}" for i in up["closes"])
    return line


def _nudge(home: Path, cfg: dict) -> dict | None:
    """`_unpushed()` once it holds `git.nudge_after_changes` closed changes; None below that, at 0,
    or with no tracking ref."""
    n = cfg["git"]["nudge_after_changes"]
    found = _unpushed(home, cfg) if n else None
    return found if found and found["changes"] >= n else None


def cmd_publish(root: Path, check_only: bool = False) -> int:
    """Push the base branch (`git.base`) and the release tag, then run the host's publish command.
    Never forced, so a remote that has moved is refused. A rerun skips what the remote already has
    and a publish command that already succeeded. Once the tag is on the remote, the base branch
    may have moved past it: what landed since is pushed alone, the retry for a push close or
    release couldn't make. While the tag isn't, a base branch past it is refused. With a command,
    the remote's `published` notes are read first and this repo's pushed after, so a second clone
    skips an upload; a refused notes push is reported, never a failed publish."""
    home = main_root(root)
    cfg, _, _ = load_config(home)
    rel = cfg["release"]
    remote = rel["remote"]
    trunk = cfg["git"]["base"]
    report: dict = {
        "version": None,
        "tag": None,
        "remote": remote,
        "command": None,
        "refusals": _release_refusals(root, home, cfg),
        "done": [],
        "skipped": [],
    }
    refusals = report["refusals"]

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    if not rel["version_files"]:
        refusals.append("set release.version_files in .sdlc/config.toml, then /sdlc:release")
        return emit(1)
    version, problems = read_versions(home, cfg)
    refusals += problems
    if version is None:
        return emit(1)
    tag, problem = _release_tag(rel, version)
    report.update(version=version, tag=tag)
    if problem:
        refusals.append(problem)
        return emit(1)
    # What release's `release.prepare` built for this tag, for the approval to show.
    report["prepared"] = _git(home, "notes", "--ref", PREPARED_REF, "show", tag)
    tagged = _git(home, "rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}")
    tag_ref = f"refs/tags/{tag}"
    if tagged is None:
        refusals.append(f"no tag {tag}: run /sdlc:release first")
    elif trunk and tagged != _git(home, "rev-parse", trunk) and not _pushed(home, remote, tag_ref):
        # Once the tag is on the remote, what follows it is landed work, pushed alone.
        refusals.append(
            f"{trunk} has moved past {tag}: publish a release before closing more changes onto "
            "it, or release again"
        )
    if _git(home, "remote", "get-url", remote) is None:
        refusals.append(f"no remote {remote!r}: set release.remote")
    if rel["publish"]:
        report["command"], problem = _host_command(rel, "publish", version, tag)
        if problem:
            refusals.append(problem)
    if refusals:
        return emit(1)
    # Another clone may have published already: read its note before deciding the command runs.
    if report["command"] and not check_only:
        err = _fetch_notes(home, remote)
        if err:
            report["notes_fetch_failed"] = err

    def published() -> bool:
        return "published" in (_git(home, "notes", "--ref", NOTES_REF, "show", tag) or "")

    def run_command() -> str | None:
        # No terminal and no stdin: the approval came before, so a command that asks fails now.
        try:
            ran = subprocess.run(
                _sh(report["command"]), cwd=home, capture_output=True, encoding="utf-8",
                errors="replace", stdin=subprocess.DEVNULL,
            )  # fmt: skip
        except OSError as e:
            return f"release.publish didn't run: {e}"
        if ran.returncode != 0:
            return f"release.publish exited {ran.returncode}: {ran.stderr.strip()}"
        return _git_err(home, "notes", "--ref", NOTES_REF, "add", "-f", "-m", "published", tag)

    def push(ref: str):
        return lambda: closing._push(home, remote, ref)

    trunk_ref = f"refs/heads/{trunk}"
    report["unpushed"] = _unpushed(home, cfg)
    steps = [
        (f"push {trunk}", lambda: _pushed(home, remote, trunk_ref), push(trunk_ref)),
        ("push tag", lambda: _pushed(home, remote, tag_ref), push(tag_ref)),
        ("publish command", lambda: not report["command"] or published(), run_command),
    ]
    if check_only:
        # What the remote already has, so the skill asks about what would run: everything, main
        # alone once the tag is out, or nothing at all.
        report["already"] = [name for name, done_already, _ in steps if done_already()]
        report["will_run"] = [name for name, _, _ in steps if name not in report["already"]]
        # The note's push is bookkeeping under the same yes: it goes when the command does.
        if "publish command" in report["will_run"]:
            report["will_run"].append("push notes")
        report["skipped"] = [f"{name} (--check)" for name in report["will_run"]]
        return emit(0)
    for i, (name, done_already, step) in enumerate(steps):
        if done_already():
            report["skipped"].append(f"{name} (already done)")
            continue
        err = step()
        if err:
            report["skipped"] += [n for n, _, _ in steps[i:]]
            refusals.append(f"{name} failed: {err}")
            return emit(1)
        report["done"].append(name)
    # So a second clone skips the upload. Not one of the steps: a refusal here leaves the release
    # published, so it is reported, never a failed publish.
    if report["command"] and _git(home, "rev-parse", "-q", "--verify", NOTES_REF) is not None:
        if _pushed(home, remote, NOTES_REF):
            report["skipped"].append("push notes (already done)")
        elif err := closing._push(home, remote, NOTES_REF):
            report["notes_push_failed"] = err
        else:
            report["done"].append("push notes")
    return emit(0)


@command(
    "publish",
    "push main and the release tag, then run release.publish",
    arg("--check", action="store_true", help="preconditions only, push nothing"),
)
def cli_publish(root: Path, home: Path, args) -> int:
    return cmd_publish(root, args.check)


# ---------------------------------------------------------------- retro
#
# The outermost loop: /sdlc:retro looks across the changes and releases since the last
# retrospective and sets direction. What can be counted is counted here, so the skill reads one
# JSON blob rather than history: the retrospective keeps the rule it audits.

RETRO_PREFIX = "Retrospective "
RETRO_RE = re.compile(r"^Retrospective (\d{4}-\d{2}-\d{2})$")
SEPARATORS = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")


def _load_metrics():
    """`scripts/metrics.py`, the transcript readers, by path like the trackers: `uv run --script`
    and the tests put different directories on sys.path."""
    spec = importlib.util.spec_from_file_location(
        "sdlc_metrics", PLUGIN_DIR / "scripts" / "metrics.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


metrics = _load_metrics()


def _load_factory_records():
    """`scripts/factory_records.py`, the one reader of a factory run's files, by path like
    `metrics.py`, and pure like it: nothing is bound into it. The board and close read it through
    their binding, as `sdlc.factory_records`, so a test's stand-in here reaches them too."""
    spec = importlib.util.spec_from_file_location(
        "sdlc_factory_records", PLUGIN_DIR / "scripts" / "factory_records.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


factory_records = _load_factory_records()
# Bound here so `retro` reads them, and its tests can stand in for them, by these names.
_project_dirs = metrics._project_dirs


class _Names:
    """This module's own names, read when retro.py uses them, so a test's stand-in reaches it."""

    def __init__(self, names: dict) -> None:
        self.__dict__ = names


def _load_retro():
    """`scripts/retro.py`, the retrospective's readers, by path like `metrics.py`. Unlike it,
    retro reads this module's names as `sdlc.<name>`, through a live view of its globals."""
    spec = importlib.util.spec_from_file_location("sdlc_retro", PLUGIN_DIR / "scripts" / "retro.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.sdlc = _Names(globals())
    return mod


retro = _load_retro()


def _load_closing():
    """`scripts/closing.py`, close, the push and the main lock, bound like retro: kept apart so
    `[review] sensitive` can name them without naming this whole file."""
    spec = importlib.util.spec_from_file_location(
        "sdlc_closing", PLUGIN_DIR / "scripts" / "closing.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.sdlc = _Names(globals())
    return mod


closing = _load_closing()


def _load_board():
    """`scripts/board.py`, the dashboard's server, bound like retro but loaded only when `board`
    runs: no other command pays for it."""
    spec = importlib.util.spec_from_file_location("sdlc_board", PLUGIN_DIR / "scripts" / "board.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.sdlc = _Names(globals())
    return mod


@command(
    "close",
    "land a shipped change on main, or record a dropped one there; mirror it, remove its "
    "folder, worktree and branch",
    arg("id", nargs="?", help="the change, e.g. 023 (default: this checkout's)"),
    arg("--check", action="store_true", help="preconditions only, write nothing"),
)
def cli_close(root: Path, home: Path, args) -> int:
    return closing.cmd_close(root, args.id, args.check)


@command(
    "retro",
    "what the retrospective counts since the last one, as JSON; writes nothing",
    arg("--metrics", action="store_true", help=METRICS_HELP),
    arg("--report", action="store_true", help="the report retro-commit would write, as Markdown"),
)
def cli_retro(root: Path, home: Path, args) -> int:
    return retro.cmd_retro(root, args.metrics, args.report)


@command(
    "retro-commit",
    "commit the direction doc, the inbox and the report as `Retrospective <date>`",
)
def cli_retro_commit(root: Path, home: Path, args) -> int:
    return retro.cmd_retro_commit(root)


@command(
    "board",
    "serve the dashboard of every open change on 127.0.0.1; writes nothing",
    arg("--port", type=int, default=5170),
)
def cli_board(root: Path, home: Path, args) -> int:
    return _load_board().cmd_board(root, args.port)


def first_paragraph(body: str, heading: str) -> str:
    """The first paragraph under `## <heading>`, on one line; "" when there is none."""
    lines: list[str] = []
    inside = False
    for line in body.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line[3:].strip() == heading
        elif inside and line.strip():
            lines.append(line.strip())
        elif inside and lines:
            break
    return " ".join(lines)


def bash_commands(text: str) -> list[str]:
    """Every command in a skill's bash blocks, split the way permission rules match them: on
    `&&`, `||`, `;` and `|`, with a `$(...)` checked as a command of its own. The tests check each
    skill's rules against this, and the retrospective counts with it."""
    found = []
    for block in re.findall(r"```bash\n(.*?)```", text, re.S):
        joined = re.sub(r"\\\n\s*", " ", block)
        for line in joined.splitlines():
            line = re.sub(r"\s+#\s.*$", "", line).strip()
            for part in [*SEPARATORS.split(line), *re.findall(r"\$\(([^()]*)\)", line)]:
                part = part.strip()
                if part and not part.startswith("<"):  # `<build>`: the repo's own command
                    found.append(part)
    return found


def _days_between(start: str, end: str) -> int | None:
    try:
        return (date.fromisoformat(end) - date.fromisoformat(start)).days
    except ValueError:
        return None


def retrospectives(home: Path, trunk: str | None) -> list[dict]:
    """Every `Retrospective YYYY-MM-DD` commit on the base branch's first-parent line, newest
    first: each one the boundary of the next. retro-commit writes the subject, so it is never a
    guess."""
    if not trunk:
        return []
    log = _git(home, "log", "--first-parent", "--format=%h%x00%s", trunk) or ""
    found = []
    for line in log.splitlines():
        sha, _, subject = line.partition("\x00")
        m = RETRO_RE.match(subject)
        if m:
            found.append({"sha": sha, "date": m.group(1)})
    return found


def last_retrospective(home: Path, trunk: str | None) -> dict | None:
    """The newest retrospective, the boundary of the next one."""
    return next(iter(retrospectives(home, trunk)), None)


def _release_tags(home: Path, cfg: dict, since: dict | None) -> list[dict]:
    """The release tags on the base branch after the last retrospective, oldest first."""
    trunk = cfg["git"]["base"]
    if not trunk:
        return []
    pattern = cfg["release"]["tag"].replace("{version}", "*")
    fmt = "--format=%(refname:short)%00%(creatordate:short)"
    listed = _git(home, "tag", "--merged", trunk, "--list", pattern, "--sort=creatordate", fmt)
    tags = []
    for line in (listed or "").splitlines():
        tag, _, when = line.partition("\x00")
        older = since and _git(home, "merge-base", "--is-ancestor", tag, since["sha"]) is not None
        if tag and not older:
            tags.append({"tag": tag, "date": when})
    return tags


# A goal is `- G1. …` and a milestone `### M1. …`, in the direction doc; an outcome is `- O1. …`,
# in the product doc. A closed one is struck with its status after it: `~~M2. …~~ Done:
# <evidence>`, `Dropped: <reason>`, `Revised → M5: <reason>`. The ids are in the lines people
# read, so there is no second copy to drift.
ITEM_RE = re.compile(
    r"^(?P<mark>- |### )(?P<struck>~~)?(?P<id>[GMO]\d+)\. (?P<title>.+?)(?:~~)?"
    r"(?:\s+(?P<status>Done|Dropped|Revised)(?: → (?P<successor>[GMO]\d+))?:\s*(?P<reason>.*))?$"
)
# Each kind of id: its name, the mark it's written with, and the doc that holds it.
ITEM_KINDS = {
    "G": ("goal", "- ", "the direction doc"),
    "M": ("milestone", "### ", "the direction doc"),
    "O": ("outcome", "- ", "the product doc"),
}
ITEM_FORMS = {"- ": "`- {id}.` list items", "### ": "`### {id}.` headings"}
# An item's short name, a bold lead after its id: `- O1. **First closed change.** …`. The skills
# show it beside the id, so a person never has to remember what O3 was. Open outcomes need one.
NAME_RE = re.compile(r"^\*\*(?P<name>[^*]+?)\.?\*\*\.?\s*")
GROUPS_RE = re.compile(r"^Groups:\s*(.+)$")
# What a goal or milestone answers to, which `retro` checks against the open outcomes: a goal ends
# with the outcomes it serves, `- G1. … (O1, O3)`; a milestone has a `Serves:` line beside its
# `Groups:`, naming its goal, outcomes or both. Optional, and never a problem: an uncited item is
# reported by `retro`, not refused.
CITES_RE = re.compile(r"\((O\d+(?:\s*,\s*O\d+)*)\)\s*$")
SERVES_RE = re.compile(r"^Serves:\s*(.+)$")
SERVES_ID_RE = re.compile(r"\b[GO]\d+\b")
GROUP_CHANGE_RE = re.compile(r"\b(\d{3,})(?:-[a-z0-9][a-z0-9-]*)?\b")


def _goal_cites(text: str) -> list[str]:
    """The outcome ids a goal's text ends with, `(O1, O3)`, in order; [] for any other ending."""
    cites = CITES_RE.search(text)
    return [o.strip() for o in cites[1].split(",")] if cites else []


def direction_items(text: str) -> dict:
    """The goals and milestones a direction doc holds, by id, with each one's status and what a
    milestone groups. What's wrong with them is under `problems`, never raised: a doc with no ids
    at all (one written before ids existed, or by hand) is simply empty."""
    return doc_items(text, "GM")


def product_items(text: str) -> dict:
    """The outcomes a product doc holds, by id, with each one's status: the only lines of it the
    plugin reads. The rest is the host's prose."""
    return doc_items(text, "O")


def doc_items(text: str, kinds: str) -> dict:
    """The ids of `kinds` (of `G`, `M`, `O`) a doc holds, with their statuses. An id written with
    the wrong mark, or of a kind this doc doesn't hold, is a problem and is skipped."""
    items: list[dict] = []
    problems: list[str] = []
    current: dict | None = None
    cited: set[str] = set()
    # A goal wrapped onto indented lines, with the text so far: its citation ends the last one.
    goal: tuple[dict, str] | None = None
    fenced = False
    for line in text.splitlines():
        # An example in a fence is the format shown, not an item.
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = ITEM_RE.match(line.rstrip())
        if m:
            goal = None
            letter = m["id"][0]
            kind, mark, belongs = ITEM_KINDS[letter]
            # Skipped either way, it would never be tracked, so say so rather than pass over it.
            if letter not in kinds:
                problems.append(f"{m['id']} is in the wrong doc: {kind}s belong in {belongs}")
                current = None
                continue
            if m["mark"] != mark:
                form = ITEM_FORMS[mark].format(id=f"{letter}1")
                problems.append(f"{m['id']} is written as the other kind; {kind}s are {form}")
                current = None
                continue
            struck = bool(m["struck"])
            # An open item's status words are its own text: only a struck one has a status.
            title = m["title"] if struck else line.rstrip().split(f"{m['id']}. ", 1)[1]
            named = NAME_RE.match(title)
            if named:
                title = title[named.end() :]
            item = {
                "id": m["id"],
                "kind": kind,
                "name": named["name"].strip() if named else "",
                "title": title.strip(),
                "status": (m["status"] or "").lower() if struck else "open",
                "reason": (m["reason"] or "").strip() if struck else "",
                "successor": m["successor"] if struck else None,
                "groups": {"changes": [], "seeds": []},
                "serves": [],
            }
            if kind == "goal":
                item["serves"] = _goal_cites(item["title"])
            # A struck goal's wrapped lines are its reason's, never its title's.
            goal = (item, item["title"]) if kind == "goal" and not struck else None
            status = item["status"]
            if m["struck"] and not m["status"]:
                problems.append(f"{m['id']} is struck through with no Done, Dropped or Revised")
            elif status in ("dropped", "revised") and not item["reason"]:
                problems.append(f"{m['id']} is {status} without a reason")
            if kind == "outcome" and status == "open" and not item["name"]:
                problems.append(f"{m['id']} has no short name: write `- {m['id']}. **<name>.** …`")
            if any(i["id"] == m["id"] for i in items):
                problems.append(f"{m['id']} is used twice")
            items.append(item)
            current = item if kind == "milestone" else None
            continue
        if goal and line[:1].isspace() and line.strip():
            goal = (goal[0], f"{goal[1]} {line.strip()}")
            goal[0]["serves"] = _goal_cites(goal[1])
            continue
        goal = None
        if line.startswith("#"):
            current = None
        g = GROUPS_RE.match(line.strip())
        if g and current and not any(current["groups"].values()):
            # Seeds by quoted title or bare id, then change numbers from what's left, so an id's
            # year is never read as a change.
            current["groups"]["seeds"] = refs_in(g[1])
            rest = ENTRY_ID_TOKEN_RE.sub("", re.sub(r'"[^"]*"', "", g[1]))
            current["groups"]["changes"] = GROUP_CHANGE_RE.findall(rest)
        s = SERVES_RE.match(line.strip())
        if s and current and current["id"] not in cited:
            # The first `Serves:` line under a milestone, as with `Groups:`.
            cited.add(current["id"])
            current["serves"] = SERVES_ID_RE.findall(s[1])
    ids = {i["id"] for i in items}
    for item in items:
        if item["status"] == "revised" and item["successor"] not in ids:
            problems.append(
                f"{item['id']} is revised to {item['successor']}, which isn't in the doc"
            )
    highest = {
        k: max((int(i["id"][1:]) for i in items if i["id"][0] == k), default=0) for k in kinds
    }
    return {
        "items": items,
        "problems": problems,
        "next_ids": {k: f"{k}{n + 1}" for k, n in highest.items()},
    }


def _milestone_verdicts(
    home: Path,
    items: list[dict],
    open_names: list[str],
    trunk: str | None,
    history: list[dict] | None = None,
) -> dict:
    """What each open milestone's grouped seeds and changes have become, from history: a change
    closed (with when), still open, or unknown; a seed still in the register, shipped by the change
    whose `idea:` names it, or vanished with no change behind it. `history`, every closed change,
    when the caller has walked it already."""
    wanted = [i for i in items if i["kind"] == "milestone" and i["status"] == "open"]
    if not wanted:
        return {}
    if history is None:
        history = closed_changes(home, None, trunk)
    entries = inbox_entries(home)
    out: dict[str, list[dict]] = {}
    for item in wanted:
        rows = []
        for ident in item["groups"]["changes"]:
            closed = next((c for c in history if names_change(c["name"], ident)), None)
            if closed:
                rows.append({"entry": ident, "kind": "change", "verdict": "closed",
                             "change": closed["name"], "date": closed["close_date"]})  # fmt: skip
            elif any(names_change(n, ident) for n in open_names):
                rows.append({"entry": ident, "kind": "change", "verdict": "open"})
            else:
                rows.append({"entry": ident, "kind": "change", "verdict": "unknown"})
        for seed in item["groups"]["seeds"]:
            # A shipped change's `idea:` and the `Groups:` line each name the seed by id or by
            # title, compared as written: id to id, title to title.
            shipped = next(
                (c for c in history if any(same_ref(i, seed) for i in ideas_of(c))),
                None,
            )
            if shipped:
                rows.append({"entry": seed, "kind": "seed", "verdict": "shipped",
                             "change": shipped["name"], "date": shipped["close_date"]})  # fmt: skip
            elif any(ref_matches(seed, e) for e in entries):
                rows.append({"entry": seed, "kind": "seed", "verdict": "open"})
            else:
                rows.append({"entry": seed, "kind": "seed", "verdict": "vanished"})
        out[item["id"]] = rows
    return out


def _direction_text(home: Path, cfg: dict) -> str:
    path = home / cfg["docs"]["direction"]
    return path.read_text(encoding="utf-8") if path.is_file() else ""


# What `status` puts forward once the open changes are done, in this order, each candidate once
# under the first rule it meets. A fixed order a person can argue with line by line, never a
# score; the status skill weighs it against the open changes, release and retro.
NEXT_RULES = (
    ("priority", "ideas and bugs marked Priority: high, bugs most severe first, then oldest"),
    ("bug", "entries tagged [bug], most severe first, then oldest"),
    ("milestone", "each open milestone's first grouped seed that is ready, in the doc's order"),
    ("series", "ready seeds whose After: seeds have all left the register, oldest first"),
    ("nits", "open nits of cost S, one line per theme, oldest theme first"),
    ("idea", "every other ready idea, oldest first"),
    ("low", "ideas and bugs marked Priority: low, oldest first"),
)
# What's ready to build: what a person or a review already weighed (marked high, a bug, placed in
# a milestone or a series, a nit's cost). The other rules' seeds need the person to decide whether
# they're worth building at all.
READY_RULES = ("priority", "bug", "milestone", "series", "nits")
NEXT_SHOWN = 10
# The theme an entry without a `Theme:` line is counted under, printed last.
NO_THEME = "(no theme)"
# How many open ideas and bugs with no `Theme:` make status point at `/sdlc:idea --themes`, which
# proposes them all behind one approval. Fewer is the trickle `/sdlc:idea` and `/sdlc:bug` theme
# as they file.
THEMELESS_NUDGE = 5


def _seed_state(entry: dict, open_titles: set[str], building: set[str]) -> str:
    """`building` (tagged so, or named by an open change's `idea:`), `waiting` (a seed its
    `After:` names is still open), or `ready`."""
    if is_building(entry) or entry["title"] in building:
        return "building"
    if any(t in open_titles for t in entry["after"]):
        return "waiting"
    return "ready"


def _after_loops(waiting: dict[str, list[str]]) -> list[list[str]]:
    """Each set of waiting seeds that wait on each other, through any of their `After:` titles,
    once, in the order first met, each set in register order."""

    def reach(start: str) -> set[str]:
        found: set[str] = set()
        stack = [start]
        while stack:
            for t in waiting[stack.pop()]:
                if t in waiting and t not in found:
                    found.add(t)
                    stack.append(t)
        return found

    reaches = {t: reach(t) for t in waiting}
    loops: list[list[str]] = []
    placed: set[str] = set()
    for t in waiting:
        if t in placed or t not in reaches[t]:
            continue
        loop = [u for u in waiting if u in reaches[t] and t in reaches[u]]
        loops.append(loop)
        placed.update(loop)
    return loops


def next_up(home: Path, cfg: dict, open_changes: list[dict], today: date) -> dict:
    """What to work on once the open changes are done, from the main checkout's ideas, nits and
    direction doc, ordered by NEXT_RULES. Read-only, and a missing file adds nothing. Also the
    open milestones with nothing left in their groups, and `After:` lines that can never be met."""
    ideas = [e for e in inbox_entries(home) if not is_nit(e)]
    nits = nit_entries(home)[0]
    doc = direction_items(_direction_text(home, cfg))
    named = [
        (ref, f"{r['id']}-{r['slug']}")
        for r in open_changes
        for ref in [*ideas_of(r), *(r.get("fixes") or [])]
    ]
    holder = {e["title"]: next((c for ref, c in named if ref_matches(ref, e)), None) for e in ideas}
    building = {t for t, c in holder.items() if c}
    states = {e["title"]: "building" for e in ideas if is_building(e) or e["title"] in building}
    open_titles = {e["title"] for e in ideas if e["title"] not in states}
    for e in ideas:
        states.setdefault(e["title"], _seed_state(e, open_titles, building))
    every = sorted((e for e in ideas if states[e["title"]] == "ready"), key=lambda e: e["date"])
    # High and low are ranked apart from the rules between them, so an entry without a
    # `Priority:` line ranks among the rest exactly as it did before there was one.
    high = [e for e in every if entry_priority(e) == "high"]
    low = [e for e in every if entry_priority(e) == "low"]
    ready = [e for e in every if entry_priority(e) not in ("high", "low")]
    known = {e["title"] for e in ideas}
    milestones = [i for i in doc["items"] if i["kind"] == "milestone" and i["status"] == "open"]
    words = severities(home, cfg)
    # An `After:` title no seed and no shipped change answers to can never be met: warned about,
    # and never "next in series". History is read only when one dangles.
    dangling = {t for e in ideas for t in e["after"] if t not in known}
    walked: list[list[dict]] = []

    def history() -> list[dict]:
        """Every closed change, walked once however many readers ask."""
        if not walked:
            walked.append(closed_changes(home, None, cfg["git"]["base"]))
        return walked[0]

    unmet: set[str] = set()
    if dangling:
        shipped = [i for c in history() for i in ideas_of(c)]
        unmet = {t for t in dangling if not any(same_ref(s, t) for s in shipped)}

    def seed(rule: str, label: str, e: dict) -> dict:
        return {"rule": rule, "label": label, "title": e["title"], "id": e["id"],
                "kind": entry_kind(e), "theme": entry_theme(e),
                "age_days": _age_days({"created": e["date"]}, today),
                "command": f"/sdlc:intent {e['id'] or e['title']}"}  # fmt: skip

    def kind_label(e: dict) -> str:
        return f"bug {e['fields'].get('Severity') or '?'}" if is_bug(e) else "idea"

    def by_severity(entries: list[dict]) -> list[dict]:
        return sorted(
            entries,
            key=lambda e: (severity_rank(e["fields"].get("Severity"), words), e["date"]),
        )

    items: list[dict] = []
    taken: set[str] = set()
    for rule, _ in NEXT_RULES:
        found: list[dict] = []
        if rule == "priority":
            ranked = by_severity([e for e in high if is_bug(e)])
            ranked += [e for e in high if not is_bug(e)]
            found = [seed(rule, f"priority high · {kind_label(e)}", e) for e in ranked]
        elif rule == "low":
            found = [seed(rule, f"priority low · {kind_label(e)}", e) for e in low]
        elif rule == "bug":
            bugs = by_severity([e for e in ready if is_bug(e)])
            found = [seed(rule, kind_label(e), e) for e in bugs]
        elif rule == "milestone":
            untaken = [e for e in ready if e["title"] not in taken]
            for m in milestones:
                first = next(
                    (e for ref in m["groups"]["seeds"] for e in untaken if ref_matches(ref, e)),
                    None,
                )
                if first:
                    found.append(seed(rule, f"{m['id']} ({m['name'] or m['title']})", first))
        elif rule == "series":
            found = [
                seed(rule, f'next in series after "{e["after"][-1]}"', e)
                for e in ready
                if e["after"] and not any(t in known or t in unmet for t in e["after"])
            ]
        elif rule == "nits":
            themes = nits_summary([n for n in nits if n["cost"] == "S"], today)["themes"]
            for theme, t in sorted(themes.items(), key=lambda kv: kv[1]["oldest"] or ""):
                found.append({"rule": rule, "label": "nits",
                              "title": f"[{theme}] {t['count']} open, cost S",
                              "id": None, "kind": "nit", "theme": theme,
                              "age_days": t["age_days"],
                              "command": f"/sdlc:intent pay down the [{theme}] nits"})  # fmt: skip
        else:
            found = [seed(rule, "idea", e) for e in ready]
        for item in found:
            if item["rule"] == "nits" or item["title"] not in taken:
                taken.add(item["title"])
                item["group"] = "ready" if rule in READY_RULES else "decide"
                items.append(item)

    # Waiting seeds are open too: a theme counts them, though none is a candidate yet.
    pending = [e for e in ideas if states[e["title"]] == "waiting"]
    themes, grouped = _next_themes(items, every + pending, nits, today)

    done = []
    if milestones:
        open_names = [f"{r['id']}-{r['slug']}" for r in open_changes]
        verdicts = _milestone_verdicts(
            home, doc["items"], open_names, cfg["git"]["base"], history()
        )
        for m_id, rows in verdicts.items():
            if rows and all(r["verdict"] in ("closed", "shipped", "vanished") for r in rows):
                done.append(m_id)

    warnings = [
        f'"{e["title"]}" waits on "{t}", which is no seed or change'
        for e in ideas
        for t in e["after"]
        if t in unmet
    ]
    waiting = {e["title"]: e["after"] for e in ideas if states[e["title"]] == "waiting"}
    for loop in _after_loops(waiting):
        names = ", ".join(f'"{t}"' for t in loop)
        warnings.append(f"these seeds wait on each other, so none will come up: {names}")
    themeless = sum(
        1 for e in ideas if states[e["title"]] in ("ready", "waiting") and not entry_theme(e)
    )
    # What open changes build, by their `idea:` and `fixes:` lines, and what a legacy `[building]`
    # tag alone says is (`change` None): counted in status, listed under `--all`.
    being_built = [
        {"id": e["id"], "title": e["title"], "kind": entry_kind(e), "change": holder[e["title"]]}
        for e in ideas
        if states[e["title"]] == "building"
    ]
    return {"items": items, "done_milestones": done, "warnings": warnings, "themes": themes,
            "waiting": len(waiting), "building": being_built, "themeless": themeless,
            "all": grouped}  # fmt: skip


def _next_themes(
    items: list[dict], seeds: list[dict], nits: list[dict], today: date
) -> tuple[list[dict], list[dict]]:
    """Every theme the open ideas and bugs (ready or waiting, so the counts match the no-theme
    nudge's) and the open nits (of any cost) carry, each with its
    entries counted by kind, its oldest's age and its best-ranked line in `items`, ordered by that
    rank (a theme with no line, after those with one, oldest first), and NO_THEME last. And beside
    it, for `status --all`, each theme's entries in rank order: its ranked seeds, then its nits."""
    rank = {i["id"]: n for n, i in enumerate(items) if i["id"]}
    rank_of_nits = {i["theme"]: n for n, i in enumerate(items) if i["rule"] == "nits"}
    by: dict[str, dict] = {}

    def add(theme: str | None, kind: str, raised: str, at: int | None) -> dict:
        t = by.setdefault(theme or NO_THEME, {"theme": theme or NO_THEME, "counts": {},
                                              "oldest": None, "rank": None})  # fmt: skip
        t["counts"][kind] = t["counts"].get(kind, 0) + 1
        if raised and (t["oldest"] is None or raised < t["oldest"]):
            t["oldest"] = raised
        if at is not None and (t["rank"] is None or at < t["rank"]):
            t["rank"] = at
        return t

    for e in seeds:
        add(entry_theme(e), entry_kind(e), e["date"], rank.get(e["id"]))
    for n in nits:
        add(n["theme"] or None, "nit", n["raised"], rank_of_nits.get(n["theme"]))
    for t in by.values():
        t["age_days"] = _age_days({"created": t["oldest"] or ""}, today)
    themes = sorted(
        by.values(),
        key=lambda t: (
            t["theme"] == NO_THEME,
            t["rank"] is None,
            t["rank"] or 0,
            t["oldest"] or "9999",
        ),  # fmt: skip
    )
    grouped = []
    for t in themes:
        name = None if t["theme"] == NO_THEME else t["theme"]
        rows = [i for i in items if i["id"] and i["theme"] == name]
        rows += [{"rule": "nit", "label": f"nit {n['cost'] or '?'}", "title": n["title"],
                  "id": n["id"], "kind": "nit", "theme": name,
                  "age_days": _age_days({"created": n["raised"]}, today),
                  "command": f"/sdlc:intent pay down the [{n['theme']}] nits"}
                 for n in nits if (n["theme"] or None) == name]  # fmt: skip
        # A theme's ideas taken as one change: every id on one `idea:` line. Ideas with no theme
        # share nothing, so they are never offered together.
        ids = [r["id"] for r in rows if r["kind"] == "idea" and r["id"]]
        command = f"/sdlc:intent {' '.join(ids)}" if name and len(ids) > 1 else None
        grouped.append({"theme": t["theme"], "items": rows, "command": command})
    return themes, grouped


def retro_due(home: Path, cfg: dict) -> dict:
    """Whether a retrospective is due, and why: `retro.after_releases` release tags since the last
    one (or since the start, with none yet), or any release in that range that raised the major
    version. Never runs one; `status` and release only say so."""
    since = last_retrospective(home, cfg["git"]["base"])
    every = _release_tags(home, cfg, None)
    in_range = _release_tags(home, cfg, since) if since else every
    template = cfg["release"]["tag"]
    pattern = re.escape(template).replace(re.escape("{version}"), r"(\d+\.\d+\.\d+)")
    version_re = re.compile(rf"^{pattern}$") if "{version}" in template else None

    def major(tag: str) -> int | None:
        # A tag template without {version} names no version: no major rule, only the count.
        m = version_re.match(tag) if version_re else None
        return _semver(m.group(1))[0] if m else None

    why = []
    threshold = cfg["retro"]["after_releases"]
    if threshold and len(in_range) >= threshold:
        names = ", ".join(t["tag"] for t in in_range)
        last = "the last retrospective" if since else "the start, with none yet"
        why.append(f"{len(in_range)} releases since {last} ({names})")
    tags = [t["tag"] for t in every]
    for t in in_range:
        i = tags.index(t["tag"])
        before = major(tags[i - 1]) if i > 0 else None
        now = major(t["tag"])
        if before is not None and now is not None and now > before:
            why.append(f"major release {t['tag']}")
    return {"due": bool(why), "why": why, "releases": [t["tag"] for t in in_range]}


# Why an entry left the register without a change, by its kind. A fixed bug or a built idea
# leaves through the ship that did it, and a nit only through ship.
RETIRE_REASONS = {
    "idea": ("duplicate", "superseded", "declined"),
    "bug": ("duplicate", "not-a-bug", "wontfix", "cant-reproduce"),
    "nit": (),
}
INBOX_SUBJECTS = ("File", "Retire", "Update")
# What triage can decide about an issue that closes it there: nothing more will be done. Anything
# else is filed as an entry or put on a change's `closes:` line, and closes when that lands.
TRIAGE_VERDICTS = ("resolved", "wontfix", "not-a-bug", "duplicate")
TRIAGE_REF_NEEDED = ("resolved", "duplicate")


def _triage_verdicts(
    triaged: list[str], whys: list[str], refusals: list[str]
) -> tuple[list[str], list[str], list[int]]:
    """`--triaged <N>=<verdict>[:<ref>]` and `--why <N>=<text>` as the `Sdlc-Triaged:` trailers,
    the `Why #N:` body lines and the issue numbers, adding to `refusals` what's malformed: a
    verdict not in TRIAGE_VERDICTS, a resolved or duplicate one with no ref, any other with no
    why. The why is the reason the issue's closing comment gives."""
    said: dict[int, str] = {}
    for w in whys:
        n, _, text = w.partition("=")
        if not n.strip().lstrip("#").isdigit() or not text.strip():
            refusals.append(f"--why {w}: give it as <N>=<one line>")
            continue
        said[int(n.strip().lstrip("#"))] = " ".join(text.split())
    trailers, body, numbers = [], [], []
    for t in triaged:
        n, _, rest = t.partition("=")
        verdict, _, ref = rest.partition(":")
        if not n.strip().lstrip("#").isdigit():
            refusals.append(f"--triaged {t}: the issue is a number, <N>=<verdict>[:<ref>]")
            continue
        number = int(n.strip().lstrip("#"))
        if verdict not in TRIAGE_VERDICTS:
            refusals.append(f"--triaged {t}: the verdict is one of {'|'.join(TRIAGE_VERDICTS)}")
            continue
        if verdict in TRIAGE_REF_NEEDED and not ref.strip():
            refusals.append(f"--triaged {t}: a {verdict} verdict names what it rests on, :<ref>")
            continue
        if verdict not in TRIAGE_REF_NEEDED and number not in said:
            refusals.append(f"--triaged {t}: give the reason as --why {number}=<one line>")
            continue
        numbers.append(number)
        trailers.append(f"Sdlc-Triaged: #{number} verdict={verdict} ref={ref.strip() or '-'}")
        if number in said:
            body.append(f"Why #{number}: {said[number]}")
    unused = sorted(set(said) - set(numbers))
    refusals += [f"--why {n}: no --triaged names #{n}" for n in unused]
    return trailers, body, numbers


def cmd_inbox_commit(
    root: Path,
    ids: list[str] | None = None,
    reasons: list[str] | None = None,
    triaged: list[str] | None = None,
    whys: list[str] | None = None,
) -> int:
    """Record what /sdlc:idea, /sdlc:bug or /sdlc:triage wrote: one commit of the register alone,
    on the base branch in the main checkout, its subject `File <id>`, `Retire <id>` or `Update
    <id>` for each entry added, removed or changed. A removed entry needs `--reason <id>=<word>`,
    one of its kind's RETIRE_REASONS: a bug's goes on an `Sdlc-Retired:` trailer, any other's on a
    `Reason <id>:` body line; a nit, or an entry being built, is never removed here. Each
    `--triaged` verdict adds an `Sdlc-Triaged:` trailer, and `Triage #N` to the subject; with
    nothing else to record, the commit is empty.

    From a change's worktree it files only the entries `ids` names, as the worktree's register
    has them against its own HEAD, into the main checkout's register, which must be clean and on
    the base branch; once committed there, those entries go back to HEAD in the worktree, which
    gets them from the base branch when it next comes up to date. The whole run holds the lock
    `claim()` takes, so two sessions filing at once keep both entries. Every refusal is found
    before anything is written."""
    home = main_root(root)
    cfg, _, _ = load_config(home)
    register = register_path(work_dir(home))
    rel = f"{work_rel(home)}/{register.name}"
    report: dict = {"commit": None, "entries": [], "refusals": [], "done": []}
    refusals = report["refusals"]
    ids = list(dict.fromkeys(i.strip() for i in ids or [] if i.strip()))
    in_tree = root.resolve() != home.resolve()

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    if in_tree and not ids:
        refusals.append("from a change's worktree, name the entries to file: inbox-commit <id>…")
    if ids and not in_tree:
        refusals.append("from the main checkout it records the whole register: name no entries")
    if in_tree and triaged:
        refusals.append(f"triage's verdicts are recorded from the main checkout ({home})")
    state = {"cfg": cfg, "register": register, "rel": rel, "ids": ids, "in_tree": in_tree,
             "reasons": reasons, "triaged": triaged, "whys": whys}  # fmt: skip
    with closing._main_lock(home):
        return emit(_inbox_commit(root, home, state, report))


@command(
    "inbox-commit",
    "commit the inbox alone, as File, Retire or Update <id>",
    arg("ids", nargs="*", help="from a change's worktree, the entries to file on the base branch"),
    arg("--reason", action="append", default=[], help="<id>=<word>, for each entry removed"),
    arg(
        "--triaged",
        action="append",
        default=[],
        help="<N>=<verdict>[:<ref>], for each issue triage closes: " + "|".join(TRIAGE_VERDICTS),
    ),
    arg("--why", action="append", default=[], help="<N>=<one line>, the reason a verdict gives"),
)
def cli_inbox_commit(root: Path, home: Path, args) -> int:
    return cmd_inbox_commit(root, args.ids, args.reason, args.triaged, args.why)


def _open_claims(home: Path) -> list[tuple[str, str]]:
    """(reference, change) for each entry an open change builds or fixes, from its `idea:` and
    `fixes:` lines, which are all that mark an entry taken: nothing edits the register for it, so
    the base branch's register shows such an entry as it was filed. A shipped change claims its
    entries until close retires them; a dropped change claims nothing, so its seed is open again
    with no edit."""
    claims = []
    for p in change_dirs(home):
        rec = load_change(p, home)
        if rec["stage"] == "dropped":
            continue
        claims += [(r, p.name) for r in [*ideas_of(rec), *rec["fixes"]] if r]
    return claims


def _claimed_by(entry: dict, claims: list[tuple[str, str]]) -> str | None:
    """The first open change `claims` (`_open_claims()`) says builds or fixes this entry, by its
    folder name; None when none does."""
    return next((name for ref, name in claims if ref_matches(ref, entry)), None)


def _as_written(entry: dict | None) -> dict | None:
    """An entry as its own lines hold it: without `after`, which `parse_entries()` resolves to the
    title of an entry still in the file, so a neighbour's removal would read as an edit. The
    `After:` line as written stays in `fields`."""
    return entry and {k: v for k, v in entry.items() if k != "after"}


def _inbox_commit(root: Path, home: Path, state: dict, report: dict) -> int:
    """`cmd_inbox_commit()`'s work, under its lock: the exit code, with `report` filled in.
    `state` is what the command resolved before taking the lock."""
    cfg, register, rel = state["cfg"], state["register"], state["rel"]
    ids, in_tree = state["ids"], state["in_tree"]
    reasons, triaged, whys = state["reasons"], state["triaged"], state["whys"]
    refusals = report["refusals"]
    trunk = cfg["git"]["base"]
    if why := trunk_refusal(home, trunk, cfg["git"]["base_source"]):
        refusals.append(why)
    elif _git(home, "branch", "--show-current") != trunk:
        refusals.append(f"the main checkout ({home}) isn't on {trunk}")
    tracked = _git(home, "-c", "core.quotePath=false", "diff", "--name-only", "HEAD") or ""
    untracked = (
        _git(home, "-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard") or ""
    )
    changed = sorted({p for p in (*tracked.splitlines(), *untracked.splitlines()) if p})
    stray = [p for p in changed if p != rel]
    if in_tree and changed:
        refusals.append(
            f"the main checkout ({home}) has uncommitted changes: " + ", ".join(changed)
        )
    elif stray:
        refusals.append(f"only {rel} may be uncommitted; also changed: " + ", ".join(stray))
    elif not changed and not triaged and not in_tree:
        refusals.append(f"nothing to record: {rel} is unchanged")
    verdicts, why_lines, numbers = _triage_verdicts(triaged or [], whys or [], refusals)
    given: dict[str, str] = {}
    for r in reasons or []:
        ident, _, word = r.partition("=")
        given[ident.strip()] = word.strip()

    head_text = _git(home, "show", f"HEAD:{rel}") or ""
    try:
        main_text = register.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        refusals.append(f"{rel} can't be read: {e}")
        main_text = head_text
    new_text = main_text
    tree_register = register_path(work_dir(root))
    tree_text = tree_head = ""
    if in_tree:
        tree_rel = f"{work_rel(root)}/{tree_register.name}"
        tree_head = _git(root, "show", f"HEAD:{tree_rel}") or ""
        try:
            tree_text = tree_register.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            refusals.append(f"{tree_rel} can't be read: {e}")
            tree_text = tree_head
        was = {e["id"]: e for e in parse_entries(tree_head)}
        now = {e["id"]: e for e in parse_entries(tree_text)}
        on_main = {e["id"] for e in parse_entries(main_text)}
        for i in ids:
            if _as_written(was.get(i)) == _as_written(now.get(i)):
                refusals.append(f"{i}: this worktree's {tree_rel} doesn't change it")
            elif i not in was and i in on_main:
                refusals.append(f"{i} is already in the main checkout's {rel}")
            elif i in was and i not in on_main:
                refusals.append(f"{i} isn't in the main checkout's {rel}")
        new_text = _splice_entries(main_text, tree_text, ids)

    before = {e["id"]: e for e in parse_entries(head_text)}
    after = {e["id"]: e for e in parse_entries(new_text)}
    actions: dict[str, list[str]] = {s: [] for s in INBOX_SUBJECTS}
    trailers: list[str] = []
    reason_lines: list[str] = []
    for k in after:
        if k not in before:
            actions["File"].append(k)
        elif _as_written(after[k]) != _as_written(before[k]):
            actions["Update"].append(k)
    claims: list[tuple[str, str]] | None = None
    for k, e in before.items():
        if k in after:
            continue
        actions["Retire"].append(k)
        kind = entry_kind(e)
        allowed = RETIRE_REASONS[kind]
        if claims is None:
            claims = _open_claims(home)
        by = _claimed_by(e, claims)
        if kind == "nit":
            refusals.append(f"{k} is a nit: ship retires nits, with the change that fixes one")
        elif by or is_building(e):
            refusals.append(
                f"{k} is being built{f' by {by}' if by else ''}: its change removes it at ship, "
                "or /sdlc:drop says why not"
            )
        elif k not in given:
            refusals.append(f"{k} is removed with no reason: give --reason {k}=<word>")
        elif given[k] not in allowed:
            refusals.append(
                f"--reason {k}={given[k]}: a{'n' if kind == 'idea' else ''} {kind}'s reason is "
                f"one of {'|'.join(allowed)}"
            )
        elif kind == "bug":
            severity = (e["fields"].get("Severity") or "unset").replace(" ", "-")
            trailers.append(
                f"Sdlc-Retired: {k} severity={severity} reported={e['date']} reason={given[k]}"
            )
        else:
            reason_lines.append(f"Reason {k}: {given[k]}")
    unused = [k for k in given if k not in actions["Retire"]]
    refusals += [f"--reason {k}: no entry by that id was removed" for k in unused]
    if refusals:
        return 1
    parts = [f"{s} {', '.join(i)}" for s, i in actions.items() if i]
    if numbers:
        parts.append("Triage " + ", ".join(f"#{n}" for n in numbers))
    subject = "; ".join(parts)
    if not subject:
        refusals.append(f"nothing to record: {rel} changed, but no entry did")
        return 1
    report["commit"] = subject
    report["entries"] = [{"action": s, "id": i} for s, found in actions.items() for i in found]
    report["triaged"] = numbers
    trailers += verdicts
    body = why_lines + reason_lines
    message = ["-m", subject] + (["-m", "\n".join(body)] if body else [])
    message += ["-m", "\n".join(trailers)] if trailers else []
    steps = [["add", "--", rel], ["commit", "-q", *message, "--", rel]]
    if not changed and not in_tree:
        steps = [["commit", "-q", "--allow-empty", *message]]
    if in_tree:
        register.parent.mkdir(parents=True, exist_ok=True)
        register.write_text(new_text, encoding="utf-8", newline="\n")
    for args in steps:
        made = subprocess.run(
            ["git", "-C", str(home), *args], capture_output=True, encoding="utf-8"
        )
        if made.returncode != 0:
            refusals.append(f"git {args[0]} failed: {made.stderr.strip()}")
            if in_tree:
                _git(home, "reset", "-q", "--", rel)
                register.write_text(main_text, encoding="utf-8", newline="\n")
            return 1
    report["done"].append("commit")
    report["sha"] = _git(home, "rev-parse", "--short", "HEAD")
    if in_tree:
        tree_register.write_text(
            _splice_entries(tree_text, tree_head, ids), encoding="utf-8", newline="\n"
        )
        report["done"].append("worktree")
    return 0


# ---------------------------------------------------------------- intake
#
# Issues filed on the tracker by people who don't run a session. Each one the repo records has
# one record: an inbox entry's `Issue:` line, a change's `closes:` line, or an `Sdlc-Triaged:`
# trailer on the base branch for a verdict that closed it. The core decides what each record says
# on its issue and which issue is its parent; the tracker only sets it. Every comment is fixed
# text with ids, numbers and names filled in, and a person's reason or questions as approved.

TRIAGED_RE = re.compile(r"^Why #(\d+):\s*(.+)$")


def _intake_tracker(home: Path, cfg: dict):
    """(the tracker, None) when it reads intake, or (None, why not)."""
    why = archive_unavailable(home, cfg)
    if why:
        return None, why
    found = tracker(home, cfg)
    if not hasattr(found, "intake"):
        return None, f"the {cfg['archive']['target']} tracker reads no issues people file"
    return found, None


def _verdicts(home: Path, trunk: str | None) -> dict[int, dict]:
    """Each issue an `Sdlc-Triaged:` trailer on the base branch names: its verdict, what it rests
    on, and the reason its commit gives; the newest for an issue that has several."""
    if not trunk:
        return {}
    log = _git(home, "log", "--format=%x1e%B", "--grep=^Sdlc-Triaged:", trunk) or ""
    out: dict[int, dict] = {}
    for body in reversed(log.split("\x1e")):
        whys = {int(m.group(1)): m.group(2).strip() for ln in body.splitlines()
                if (m := TRIAGED_RE.match(ln.strip()))}  # fmt: skip
        for name, fields in ((metrics.parse_trailers(body) or {}).get("triaged") or {}).items():
            n = int(str(name).lstrip("#"))
            ref = str(fields.get("ref", "-"))
            out[n] = {"verdict": str(fields.get("verdict")), "ref": ref, "why": whys.get(n, "")}
    return out


def recorded_issues(home: Path, committed_only: bool = False) -> dict[int, dict]:
    """Every issue the repo records, by number, each with what it should say on the tracker: its
    `comment`, `marker`, `parent`, and `close` reason when a verdict closed it, and `filed` (the
    entry id, change name or verdict that records it). A verdict outranks a change, and a change
    an entry: the newest decision about an issue is the one its filer follows. From the base
    branch's committed register when `committed_only`, else from every checkout's too, and every
    change's `entries.md` there.

    The one reader of all three records (an entry's `Issue:` line, a change's `closes:`, an
    `Sdlc-Triaged:` trailer), and the one that decides: the tracker's `mark()`, `unmark()` and
    `needs_info()` only set what this says, so a tracker still never reads `.sdlc/work/`."""
    home = main_root(home)
    cfg = load_config(home)[0]
    trunk = cfg["git"]["base"]
    register = f"{work_rel(home)}/{register_path(work_dir(home)).name}"
    texts = [_git(home, "show", f"{trunk}:{register}") or ""] if trunk else []
    if not committed_only:
        for checkout in dict.fromkeys([home, *(p for p, _ in worktrees(home))]):
            # The register, and each change's held entries: a seed split off at ship is its
            # issue's record from then, filed at close.
            work = work_dir(checkout)
            for path in [register_path(work), *sorted(work.glob(f"*/{ENTRIES}"))]:
                try:
                    texts.append(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError):
                    continue
    out: dict[int, dict] = {}
    for text in texts:
        for e in parse_entries(text):
            issues = entry_issues(e) or []
            if not issues:
                continue
            split = next((t for t in e["text"] if t.startswith("Split from ")), None)
            for k, n in enumerate(issues):
                if n in out:
                    continue
                first = issues[0]
                if k:
                    comment = f"Filed with #{first} as {e['id']}; follow #{first} for progress."
                elif split:
                    name = split[len("Split from ") :].split(":", 1)[0].strip()
                    comment = f"Not resolved by {name}; it stays open as {e['id']} in {register}."
                else:
                    comment = f"Filed as {e['id']} ([{e['status']}]) in {register}."
                out[n] = {
                    "filed": e["id"],
                    "comment": comment,
                    "marker": f"<!-- sdlc:intake:{e['id']} -->",
                    "parent": first if k else None,
                    "close": None,
                }
    for path in change_dirs(home):
        rec = load_change(path, home)
        if rec["stage"] == "dropped" or not rec.get("closes"):
            continue
        name, own = path.name, int(rec["id"])
        for n in rec["closes"]:
            out[n] = {
                "filed": name,
                "comment": f"Taken on by #{own} ({name}); follow #{own} for progress.",
                "marker": f"<!-- sdlc:intake:{name} -->",
                "parent": own,
                "close": None,
            }
    for n, v in _verdicts(home, trunk).items():
        ref, verdict = v["ref"], v["verdict"]
        if verdict == "resolved":
            comment = f"Already resolved by {ref}."
        else:
            comment = f"Closed as {verdict}: {v['why']}" + ("" if v["why"].endswith(".") else ".")
        dup = re.fullmatch(r"#(\d+)", ref) if verdict == "duplicate" else None
        out[n] = {
            "filed": f"#{n} {verdict}",
            "comment": comment,
            "marker": f"<!-- sdlc:triage:#{n} -->",
            "parent": int(dup.group(1)) if dup else None,
            "close": "completed" if verdict == "resolved" else "not planned",
        }
    return out


def cmd_intake(root: Path) -> int:
    """What /sdlc:triage reads, as JSON: the open issues no change claims and triage hasn't
    labelled, each with `filed` naming the record the repo already holds for it (so a rerun only
    labels it) or null; the `dangling` ones, labelled `triaged` with no record, each saying
    whether an unpushed commit closes it (`waits_on_push`, null with `dangling_unread` when
    those commits can't be read); the severities;
    and the open changes an issue could go to. Writes nothing."""
    home = main_root(root)
    cfg = load_config(home)[0]
    out: dict = {"unavailable": None, "issues": [], "more": False, "dangling": []}
    out["severities"] = severities(home, cfg)
    # Where an issue can go: each change still being built, with its intent's path, in its own
    # worktree, for triage to add the issue to its `closes:` line. One at ship or later is past it.
    out["open_changes"] = []
    for path in change_dirs(home):
        r = load_change(path, home)
        if r["stage"] in (None, "ship", "shipped", "dropped"):
            continue
        out["open_changes"].append(
            {"id": r["id"], "slug": r["slug"], "title": r["title"], "stage": r["stage"],
             "closes": r.get("closes") or [], "intent": str(path / "intent.md")}
        )  # fmt: skip
    found, why = _intake_tracker(home, cfg)
    if found is None:
        out["unavailable"] = why
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    issues, more, err = found.intake()
    if issues is None:
        out["unavailable"] = err
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 1
    records = recorded_issues(home)
    # A record only on disk, an entry written and not yet committed, isn't one mark-triaged will
    # act on: the register's commit comes first, so the skill commits it before it marks.
    committed = recorded_issues(home, committed_only=True)
    out["issues"] = [
        {
            **i,
            "filed": (records.get(i["number"]) or {}).get("filed"),
            "uncommitted": i["number"] in records and i["number"] not in committed,
        }
        for i in issues
    ]
    out["more"] = more
    dangling, err = found.dangling(set(records))
    # One a commit the base branch hasn't pushed closes lost its record to that commit's close:
    # it waits on the push, and isn't triage's again. Unread, none is said not to wait: each is
    # null, and `dangling_unread` says why, so triage offers none of them on a guess.
    closed_by = getattr(found, "closed_by", None)
    closing = unpushed_closes(home, cfg, closed_by) if dangling and closed_by else None
    if dangling and closing is None:
        out["dangling_unread"] = "couldn't read the commits the base branch hasn't pushed"
    out["dangling"] = [
        {**d, "waits_on_push": None if closing is None else d.get("number") in closing}
        for d in dangling or []
    ]
    if err:
        out["dangling_error"] = err
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


@command("intake", "the open issues triage has to read, as JSON; writes nothing")
def cli_intake(root: Path, home: Path, args) -> int:
    return cmd_intake(root)


# Ship's own passes beyond its four, which a hand-built change gets as the factory's reviewers
# would review it: each `preflight`'s `passes` part says applies, from the diff, the change's
# tier and spec, and the base branch's `[ui]`, never the skill. A factory run (a `decision.md`)
# gets none: its own reviewers ran. `ui` is the UI and the UX review, which share one set of
# screenshots.
PASS_NAMES = ("security", "behaviour", "ui")


def _passes_report(root: Path, path: Path, risk: dict | None) -> dict:
    """Which of ship's passes apply to change `path`, each `{"applies", "why"}`, `ui` with the
    `shots` it can read (`_current_shots()`): `security` on a deep diff (`risk`), `behaviour` on a
    Tier 2 with a filled spec, `ui` when the base branch's `[ui]` is complete and the diff touches
    its paths. `why` says why one doesn't apply, or why `ui` has no shots, with none taken the
    command that takes them when `sdlc-factory` is enabled. Writes nothing."""
    home = main_root(root)
    trunk = load_config(home)[0]["git"]["base"]

    def no(why: str) -> dict:
        return {"applies": False, "why": why}

    yes = {"applies": True, "why": None}
    if (path / factory_records.DECISION_FILE).exists():
        return {name: no("a factory run: its own reviewers ran") for name in PASS_NAMES}
    out: dict = {}
    if risk is None:
        out["security"] = no(f"no merge base with {trunk!r}")
    else:
        out["security"] = dict(yes) if risk["deep"] else no("the diff touches no sensitive path")
    spec = path / "spec.md"
    if load_change(path, home)["tier"] != 2:
        out["behaviour"] = no("not a Tier 2 change")
    elif not spec.is_file() or is_unfilled(spec):
        out["behaviour"] = no("no filled spec.md")
    else:
        out["behaviour"] = dict(yes)
    ui = _ui_at(home, trunk)
    found = changed_paths(checkout_of(path), trunk) if trunk else None
    changed = list(
        dict.fromkeys(p for _, p_, to in (found or (None, []))[1] for p in (p_, to) if p)
    )
    if not ui["complete"]:
        out["ui"] = no(f"the base branch's {FACTORY_CONFIG.as_posix()} has no complete [ui]")
    elif not risk_paths(changed, ui["paths"]):
        out["ui"] = no("the diff touches no [ui] path")
    else:
        shots, why = _current_shots(checkout_of(path), path.name, ui, changed)
        # Only a pointer: ship never starts a server or takes a screenshot itself.
        if why == NO_SHOTS and not factory_enabled(home)[0]:
            why = f"{why}: sdlc-factory isn't enabled, so none can be taken"
        elif why == NO_SHOTS:
            ident = path.name.split("-", 1)[0]
            why = f"{why}: take them with factory.py shots {ident} --round 1 --role ui"
        out["ui"] = {"applies": True, "why": why, "shots": shots}
    return out


# Each pass's note lines (`PASS_LINES`), and how ship's refusal and question name each.
PASS_OF = (("security", "security"), ("behaviour", "behaviour"), ("ui", "ui"), ("ui", "ux"))
PASS_SAID = {"security": "Security review", "behaviour": "Behaviour check", "ui": "UI review",
             "ux": "UX review"}  # fmt: skip


def _passes_said(passes: dict, said: dict) -> dict:
    """What findings.md's note says (`said`) of each note line whose pass applies (`passes`),
    for ship's question: a line unsaid is left out, as ship refuses it anyway."""
    return {line: said[line] for name, line in PASS_OF
            if passes[name]["applies"] and said.get(line) is not None}  # fmt: skip


def _passes_clauses(passes: dict) -> list[str]:
    """Ship's question's clauses for its passes: the ones that ran in one, `after the security
    review, the behaviour check and the UI and UX reviews`, then each skip with why."""
    ran = [line for line in PASS_SAID if (passes.get(line) or {}).get("ran")]
    names = {"security": "the security review", "behaviour": "the behaviour check"}
    shown = [names[line] for line in ran if line in names]
    pages = [line.upper() for line in ("ui", "ux") if line in ran]
    if pages:
        shown.append(f"the {' and '.join(pages)} review{'s' if len(pages) > 1 else ''}")
    clauses = [f"after {_and(shown)}"] if shown else []
    for line, said in PASS_SAID.items():
        note = passes.get(line)
        if note and not note["ran"]:
            clauses.append(f"without the {said[0].lower() + said[1:] if line in names else said} "
                           f"({note['why'] or 'no reason given'})")  # fmt: skip
    return clauses


def _pass_applies(parts: dict, name: str) -> bool:
    return bool(((parts.get("passes") or {}).get(name) or {}).get("applies"))


# Ship's rare branches: each file beside skills/ship/SKILL.md, in the order ship reads them, and
# when it applies, from preflight's parts and the change's folder. Ship reads only the files this
# names, so whether a branch applies is the script's call, never the skill's.
SHIP_BRANCHES = {
    "factory.md": lambda parts, path: (path / factory_records.DECISION_FILE).exists(),
    "undone.md": lambda parts, path: bool(parts["undone"]["items"]),
    "closes.md": lambda parts, path: bool(parts["closes"]["closes"]),
    "recover.md": lambda parts, path: bool((parts["risk"] or {}).get("irreversible")),
    "fresh.md": lambda parts, path: bool((parts["risk"] or {}).get("deep")),
    "security.md": lambda parts, path: _pass_applies(parts, "security"),
    "behaviour.md": lambda parts, path: _pass_applies(parts, "behaviour"),
    "ui.md": lambda parts, path: _pass_applies(parts, "ui"),
    "cases.md": lambda parts, path: bool(
        parts["cases"].get("available") and parts["cases"].get("scope")
    ),
    # Step 0 reads it on `base`'s `resolvable`; once a resolution is recorded, every later step.
    "conflict.md": lambda parts, path: (path / CONFLICTS).is_file(),
}


def ship_branches(parts: dict, path: Path) -> list[str]:
    """The files of `SHIP_BRANCHES` that apply to change `path`, given `preflight`'s parts."""
    return [name for name, applies in SHIP_BRANCHES.items() if applies(parts, path)]


def cmd_preflight(root: Path, ident: str) -> int:
    """Everything /sdlc:ship's Step 0 looks up about a change, as one JSON object: its undone
    items, the nits its diff touches, the issues it would close, its acceptance checks, the
    findings an earlier run of its review left, the sensitive and irreversible paths it touches,
    and the context docs its diff could have made wrong, each part as its own command gives it,
    then `branches`, the files beside ship's skill that these call for. Writes nothing, so it is
    allowed without a prompt. Exits 1 when a part reports problems, after printing every part."""
    path = _one_change(root, ident)
    if path is None:
        return 1
    home = main_root(root)
    rec = load_change(path, home)
    checkout = checkout_of(path)
    trunk = load_config(home)[0]["git"]["base"]
    parts = {
        "undone": _undone_report(root, path),
        "nits": _nits_report(root, path, None),
        "closes": _closes_report(root, path),
        "checks": _checks_report(path),
        "findings": _findings_report(path),
        "risk": _risk_report(root, path),
        "context": _context_report(checkout, trunk),
        "cases": _cases_report(root, path),
    }
    parts["passes"] = _passes_report(root, path, parts["risk"])
    parts["branches"] = ship_branches(parts, path)
    problems = [f"{name}: no merge base with {trunk!r}" for name, p in parts.items() if p is None]
    for name in ("nits", "checks", "findings"):
        problems += [f"{name}: {p}" for p in (parts[name] or {}).get("problems") or []]
    out = {"change": path.name, "tier": rec["tier"], "stage": rec["stage"],
           "folder": _shown(path, root), **parts, "problems": problems}  # fmt: skip
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if problems else 0


def _and(names: list[str]) -> str:
    """`A`, `A and B`, `A, B and C`."""
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def _issues(numbers: list[int]) -> str:
    """`#1`, `#1 and #2`, `#1, #2 and #3`, each number once."""
    return _and([f"#{n}" for n in sorted(set(numbers))])


def _question_head(findings: list[dict]) -> tuple[str, list[str], bool]:
    """How ship's question opens, its options, and whether a yes commits, from the change's
    findings: ship's recommendation leads, and `yes` takes it. Findings still `open` are fixed and
    reviewed again before any commit; ones proposed `fix` are fixed inside the yes, then committed.
    `fix all N first` is offered when more could be fixed than ship recommends: every finding not
    already `fixed`, dismissed `wrong` or `intentional`, or pre-existing."""
    open_ = [e["id"] for e in findings if e["disposition"] == "open"]
    fix = [e for e in findings if e["disposition"] == "fix"]
    fixable = [
        e for e in findings
        if e["rank"] != "preexisting" and e["disposition"] not in ("fixed", "wrong", "intentional")
    ]  # fmt: skip
    recommended = [e["id"] for e in findings if e["disposition"] in ("open", "fix")]
    fix_all = [f"fix all {len(fixable)} first"] if len(fixable) > len(recommended) else []
    if open_:
        return (
            f"Fix {_and(recommended)}, then review again",
            ["yes", *fix_all, "edit the findings"],
            False,
        )
    if fix:
        ids = _and([e["id"] for e in fix])
        unfixed = (
            [f"commit without fixing, recording {ids} as {'a nit' if len(fix) == 1 else 'nits'}"]
            if all(e["rank"] == "nit" for e in fix)
            else []
        )
        return f"Fix {ids}, then commit this", ["yes", *fix_all, *unfixed, "edit the message"], True
    return "Commit this", ["yes", *fix_all, "edit the message"], True


def ship_question(
    folder: str,
    closes: list[int],
    target: str | None,
    context: bool,
    nits: bool,
    closing: list[int],
    split: list[int],
    register: str,
    bugs: bool = False,
    sensitive: list[str] | None = None,
    irreversible: bool = False,
    fresh: dict | None = None,
    findings: list[dict] | None = None,
    cases: dict | None = None,
    conflicts: list[str] | None = None,
    passes: dict | None = None,
) -> tuple[str | None, str | None]:
    """Ship's WAIT question for change `folder` (`.sdlc/work/NNN-slug`), as (question, None), or
    (None, why) when the issues named don't partition its `closes:` line: ship asks about every
    one, so the question never leaves one out. It opens with ship's recommendation from
    `findings` (`_question_head()`). A question that commits has each clause only when its fact
    is: the sensitive paths the diff touches, the files a conflict with the base was resolved in
    (`conflicts`, from the change's conflicts.md), a fresh review that didn't run (`fresh`, from
    findings.md's note), skill evals that didn't run (`cases`, from the same note), ship's passes
    that ran and those skipped (`passes`, each applying pass's note line, `_passes_said()`), how to
    recover what a revert can't undo, the context update shown, the
    nits recorded in `register`, the pre-existing findings filed there as bugs, the issues closed
    and split off, and the issue update unless `archive.target` is `none`."""
    named = set(closes)
    stray = sorted(n for n in {*closing, *split} if n not in named)
    if stray:
        return None, f"{_issues(stray)} not on the change's closes: line"
    both = sorted(set(closing) & set(split))
    if both:
        return None, f"{_issues(both)} given to both --closing and --split"
    left = sorted(named - set(closing) - set(split))
    if left:
        return None, f"{_issues(left)} on closes: but given to neither --closing nor --split"
    lead, options, commits = _question_head(findings or [])
    if not commits:
        return f"{lead}? ({' / '.join(options)})", None
    clauses = []
    if sensitive:
        shown = sensitive[:RISK_SHOWN]
        more = len(sensitive) - len(shown)
        names = [*shown, f"{more} more"] if more else shown
        clauses.append(f"touching sensitive path{'s' if len(sensitive) > 1 else ''} {_and(names)}")
    if conflicts:
        shown = conflicts[:RISK_SHOWN]
        more = len(conflicts) - len(shown)
        clauses.append(f"with the conflicts in {_and([*shown, f'{more} more'] if more else shown)} "
                       "resolved")  # fmt: skip
    if fresh and not fresh["ran"]:
        clauses.append(f"without the fresh review ({fresh['why'] or 'no reason given'})")
    if cases and not cases["ran"]:
        clauses.append(f"without the skill evals ({cases['why'] or 'no reason given'})")
    clauses += _passes_clauses(passes or {})
    if irreversible:
        clauses.append("with how to recover it shown")
    if context:
        clauses.append("with the context update shown")
    if nits:
        clauses.append(f"the nits shown recorded in {register}")
    if bugs:
        clauses.append(f"the bugs shown filed in {register}")
    issues = []
    if closing:
        issues.append(f"closing {_issues(closing)} when it lands")
    if split:
        seeds = "a seed" if len(set(split)) == 1 else "seeds"
        issues.append(f"splitting {_issues(split)} off as {seeds}")
    if issues:
        clauses.append(" and ".join(issues))
    stamped = f"{folder}/ stamped shipped"
    body = f", {', '.join(clauses)}, and {stamped}" if clauses else f", with {stamped}"
    then = "" if target == "none" else ", then update its issue"
    return f"{lead}{body}{then}? ({' / '.join(options)})", None


def cmd_ship_question(root: Path, ident: str, context: bool, nits: bool,
                      closing: list[int], split: list[int], bugs: bool = False) -> int:  # fmt: skip
    """Print ship's WAIT question for a change, from what its Step 4 decided, its findings.md, and
    what its diff touches, which the script reads itself so the skill can't leave a sensitive path
    or a recommended fix out. Writes nothing."""
    path = _one_change(root, ident)
    if path is None:
        return 1
    home = main_root(root)
    cfg = load_config(home)[0]
    rel = work_rel(root)
    found = findings_entries(path)
    if found["problems"]:
        print(
            f"⚠  {path.name}/{FINDINGS}: {'; '.join(found['problems'])}. Not asking.",
            file=sys.stderr,
        )
        return 1
    found_risk = _risk_report(root, path)
    risk = found_risk or {"sensitive": [], "irreversible": []}
    passes = _passes_said(_passes_report(root, path, found_risk), found["passes"])
    question, why = ship_question(
        f"{rel}/{path.name}", load_change(path, home).get("closes") or [],
        cfg["archive"]["target"], context, nits, closing, split, f"{rel}/inbox.md", bugs,
        risk["sensitive"], bool(risk["irreversible"]), found["fresh"], found["entries"],
        found["cases"], conflicts_resolved(path), passes,
    )  # fmt: skip
    if question is None:
        print(f"⚠  {path.name}: {why}. Not asking.", file=sys.stderr)
        return 1
    print(question)
    return 0


@command(
    "preflight",
    "everything ship looks up about a change, as JSON; writes nothing",
    arg("id", help="the 3-digit id, e.g. 025"),
    arg("--question", action="store_true", help="print ship's WAIT question instead, from:"),
    arg("--context", action="store_true", help="a context update was proposed"),
    arg("--nits", action="store_true", help="nits are added or retired"),
    arg("--bugs", action="store_true", help="pre-existing findings are filed"),
    arg(
        "--closing", action="append", type=int, default=[], metavar="N",
        help="an issue on closes: this change resolved; repeatable",
    ),
    arg(
        "--split", action="append", type=int, default=[], metavar="N",
        help="an issue on closes: split off as a seed; repeatable",
    ),
)  # fmt: skip
def cli_preflight(root: Path, home: Path, args) -> int:
    if args.question:
        return cmd_ship_question(
            root, args.id, args.context, args.nits, args.closing, args.split, args.bugs
        )
    given = [
        f"--{name}" for name in ("context", "nits", "bugs", "closing", "split")
        if getattr(args, name)
    ]  # fmt: skip
    if given:
        print(
            f"⚠  preflight: {', '.join(given)} only word ship's question; add --question.",
            file=sys.stderr,
        )
        return 1
    return cmd_preflight(root, args.id)


def cmd_closes(root: Path, ident: str) -> int:
    """The issues a change's `closes:` line names, each with its title and state, as JSON, for
    /sdlc:ship to ask about one by one. Writes nothing."""
    path = _one_change(root, ident)
    if path is None:
        return 1
    print(json.dumps(_closes_report(root, path), indent=2, ensure_ascii=False))
    return 0


@command(
    "closes",
    "the issues a change's closes: line names, with titles; writes nothing",
    arg("id"),
)
def cli_closes(root: Path, home: Path, args) -> int:
    return cmd_closes(root, args.id)


def _closes_report(root: Path, path: Path) -> dict:
    """The issues change `path`'s `closes:` line names, with titles where the tracker answers,
    for `closes` and `preflight`."""
    home = main_root(root)
    cfg = load_config(home)[0]
    numbers = load_change(path, home).get("closes") or []
    out: dict = {"change": path.name, "closes": [{"number": n} for n in numbers]}
    found, why = _intake_tracker(home, cfg)
    if numbers and found is not None:
        out["closes"] = found.titles(numbers)
    elif numbers:
        out["unavailable"] = why
    return out


def mark_issues(home: Path, found, only: set[int] | None = None) -> dict:
    """Bring every open issue the base branch and the open changes record (or those of them in
    `only`) in line with its record on the tracker: its comment once, the `triaged` label, its
    parent, and closed for a verdict that closes it. A full pass (no `only`) also sends back to
    triage each one it marked whose record went (`unmark_withdrawn()`). Never raises; what
    failed is listed."""
    report: dict = {"done": [], "failed": []}
    records = recorded_issues(home, committed_only=True)
    if only is not None:
        records = {n: r for n, r in records.items() if n in only}
    if not records and (only is not None or not hasattr(found, "unmark")):
        return report
    # A full pass (close, mark-triaged) lists each issue's marks once, where the tracker can, so an
    # issue marked already costs no view of its own. A pass over a change's own few (`only`) lists
    # the numbers alone: every open issue's comments would cost more than the views they save.
    # A marks listing that fails falls back to the numbers.
    try:
        marks = None
        if only is None and hasattr(found, "open_marks"):
            marks = found.open_marks()
        still_open = marks if marks is not None else found.open_numbers()
    except Exception as e:  # a tracker that fails here still lets close land
        report["failed"].append(f"listing open issues: {type(e).__name__}: {e}")
        return report
    if still_open is None:
        report["failed"].append("couldn't list the open issues")
        return report
    marks = marks or {}
    for n, r in sorted(records.items()):
        if n not in still_open:
            continue
        seen = marks.get(n)
        if (
            seen
            and r["parent"] is None
            and not r["close"]
            and seen["triaged"]
            and not seen["needs_info"]
            and any(r["marker"] in body for body in seen["comments"])
        ):
            continue
        err = found.mark(n, r["comment"], r["marker"], parent=r["parent"], close=r["close"])
        (report["failed"] if err else report["done"]).append(err or f"#{n}: {r['filed']}")
    if only is None and hasattr(found, "unmark"):
        for k, v in unmark_withdrawn(home, found, marks).items():
            report[k] += v
    return report


# A comment core leaves on an issue: its marker names the record (`intake`, `triage`) or the one
# that let it go (`withdrawn`). Read from `open_marks()`'s comment bodies.
CORE_MARK_RE = re.compile(r"<!-- sdlc:(intake|triage|withdrawn):(.+?) -->")


def _last_core_mark(comments: list[str]) -> tuple[str, str] | None:
    """(kind, ref) of the newest comment core left on an issue, or None when it left none."""
    for body in reversed(comments):
        if m := CORE_MARK_RE.search(body):
            return m.group(1), m.group(2)
    return None


def unpushed_closes(home: Path, cfg: dict, closed_by) -> set[int] | None:
    """The issues a commit the base branch holds and its remote-tracking ref doesn't would close,
    each commit's message read by the tracker's `closed_by()`; with no tracking ref, every commit
    on the base branch, since none is known to be pushed. None when git can't say. Read locally."""
    remote, trunk = cfg["release"]["remote"], cfg["git"]["base"]
    if not trunk:
        return None
    ref = f"refs/remotes/{remote}/{trunk}"
    known = _git(home, "rev-parse", "-q", "--verify", ref) is not None
    out = _git(home, "log", "--format=%B%x03", f"{ref}..{trunk}" if known else trunk)
    if out is None:
        return None
    return {n for body in out.split("\x03") for n in closed_by(body)}


def unmark_withdrawn(home: Path, found, marks: dict[int, dict] | None) -> dict:
    """Send back to triage each open issue whose record went (an entry's `Issue:` line removed by
    hand): still `triaged`, core's newest comment on it a mark (not a withdrawal), no record the
    repo holds names it (`recorded_issues()`, every checkout's), and no commit the base branch
    hasn't pushed closes it, which close's pass, between its Close commit and the push, must
    leave for the push. Nothing on a guess: no listing of `marks`, no `closed_by()`, or git
    unable to read the unpushed commits, and nothing is unmarked. Never raises."""
    report: dict = {"done": [], "failed": []}
    closed_by = getattr(found, "closed_by", None)
    if not marks or closed_by is None:
        return report
    left = {}
    for n, seen in sorted(marks.items()):
        last = _last_core_mark(seen["comments"])
        if seen["triaged"] and last and last[0] != "withdrawn":
            left[n] = last[1]
    if not left:
        return report
    recorded = recorded_issues(home)
    left = {n: ref for n, ref in left.items() if n not in recorded}
    if not left:
        return report
    try:
        closing = unpushed_closes(home, load_config(home)[0], closed_by)
    except Exception as e:  # a tracker that fails here still lets close land
        report["failed"].append(f"reading the unpushed commits: {type(e).__name__}: {e}")
        return report
    if closing is None:
        report["failed"].append("couldn't read the unpushed commits; nothing sent back to triage")
        return report
    for n, ref in left.items():
        if n in closing:
            continue
        text = (
            f"{ref} no longer records this issue; it is open for triage again."
            if ENTRY_ID_RE.match(ref)
            else closes_texts(ref)["withdrawn"]
        )
        err = found.unmark(n, text, f"<!-- sdlc:withdrawn:{ref} -->")
        (report["failed"] if err else report["done"]).append(err or f"#{n}: back to triage")
    return report


def withdraw_issues(home: Path, found, name: str, closes: set[int]) -> dict:
    """Send back to triage, through the tracker's `unmark()`, each open issue change `name` marked
    (its `<!-- sdlc:intake:<name> -->` comment) that is still marked triaged, isn't on its
    `closes:` line now, and that no record the repo holds names (`recorded_issues()`): an issue a
    person labelled, or one another record took over, is never touched. A drop reaches `unmark()`
    through `archive()` instead. Needs `open_marks()` to see the comments; never raises."""
    report: dict = {"done": [], "failed": []}
    if not (hasattr(found, "unmark") and hasattr(found, "open_marks")):
        return report
    marker = f"<!-- sdlc:intake:{name} -->"
    try:
        marks = found.open_marks()
    except Exception as e:  # a tracker that fails here still lets sync report
        report["failed"].append(f"listing open issues: {type(e).__name__}: {e}")
        return report
    if marks is None:
        report["failed"].append("couldn't list the open issues")
        return report
    left = [
        n
        for n, seen in sorted(marks.items())
        if n not in closes and seen["triaged"] and any(marker in b for b in seen["comments"])
    ]
    if not left:
        return report
    recorded = recorded_issues(home)
    text = closes_texts(name)["withdrawn"]
    for n in left:
        if n in recorded:
            continue
        err = found.unmark(n, text, f"<!-- sdlc:withdrawn:{name} -->")
        (report["failed"] if err else report["done"]).append(err or f"#{n}: back to triage")
    return report


def cmd_mark_triaged(root: Path) -> int:
    """Label, comment on and relate each open issue the repo records, from the main checkout on
    the base branch, as /sdlc:triage's last write: after the register's commit, so a record that
    isn't committed is never marked, and a rerun finishes what a failed one left. JSON; exit 1
    when one failed."""
    home = main_root(root)
    cfg = load_config(home)[0]
    report: dict = {"done": [], "failed": [], "refusals": []}
    if root.resolve() != home.resolve():
        report["refusals"].append(f"run it from the main checkout ({home}), not a worktree")
    trunk = cfg["git"]["base"]
    if why := trunk_refusal(home, trunk, cfg["git"]["base_source"]):
        report["refusals"].append(why)
    elif _git(home, "branch", "--show-current") != trunk:
        report["refusals"].append(f"the main checkout ({home}) isn't on {trunk}")
    found, why = _intake_tracker(home, cfg)
    if found is None:
        report["refusals"].append(why)
    if report["refusals"]:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1
    report.update(mark_issues(home, found))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["failed"] else 0


@command("mark-triaged", "label, comment on and relate each open issue the repo records, from main")
def cli_mark_triaged(root: Path, home: Path, args) -> int:
    return cmd_mark_triaged(root)


NEEDS_INFO_LEAD = "Needs more detail before this can be triaged:"


def cmd_needs_info(root: Path, number: int, questions_file: str) -> int:
    """Ask issue `number`'s author for what triage needs: the approved questions under a fixed
    lead line, and the `needs-info` label, so `intake` leaves it out until they reply. JSON."""
    home = main_root(root)
    cfg = load_config(home)[0]
    report: dict = {"issue": number, "done": [], "refusals": []}
    try:
        questions = Path(questions_file).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as e:
        questions = ""
        report["refusals"].append(f"{questions_file} can't be read: {e}")
    if not questions and not report["refusals"]:
        report["refusals"].append(f"{questions_file} holds no questions")
    found, why = _intake_tracker(home, cfg)
    if found is None:
        report["refusals"].append(why)
    if report["refusals"]:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1
    err = found.needs_info(number, f"{NEEDS_INFO_LEAD}\n\n{questions}")
    if err:
        report["refusals"].append(err)
    else:
        report["done"].append(f"#{number}: asked")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if err else 0


@command(
    "needs-info",
    "ask an issue's author for more detail",
    arg("number", type=int),
    arg("--questions-file", required=True, help="the approved questions"),
)
def cli_needs_info(root: Path, home: Path, args) -> int:
    return cmd_needs_info(root, args.number, args.questions_file)


# ---------------------------------------------------------------- readiness
#
# What /sdlc:setup works from: each thing a repo can set up for this plugin, whether it has, and
# the commands its own task files suggest for the gate, the slower check and the scans. Reads
# only; the skill drafts, the human approves, the skill writes.

# A task name that sounds like one of the commands setup asks about, and the key it suggests. A
# host's own `doctor` or `health` task is a scan of its own, not the plugin's `readiness`.
CANDIDATE_KEYS = {
    "check": ("check", "ci", "verify", "test", "tests", "pytest", "lint", "gate"),
    "build": ("build", "integration", "e2e", "smoke", "slow"),
    "scan": ("scan", "audit", "doctor", "health"),
    "worktree_setup": ("setup", "bootstrap", "install", "init"),
}


def _task_names(root: Path) -> list[tuple[str, str]]:
    """(command, source) for every task the repo's own task files define."""
    found: list[tuple[str, str]] = []
    for name in ("Makefile", "makefile", "GNUmakefile"):
        if (root / name).is_file():
            text = (root / name).read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r"^([A-Za-z0-9][\w.-]*)\s*:(?!=)", text, re.M):
                if not m.group(1).startswith("."):
                    found.append((f"make {m.group(1)}", name))
    if (root / "package.json").is_file():
        try:
            scripts = json.loads((root / "package.json").read_text(encoding="utf-8"))["scripts"]
        except (ValueError, KeyError, TypeError):
            scripts = {}
        runner = next(
            (r for lock, r in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"),
                               ("bun.lockb", "bun run")) if (root / lock).is_file()),
            "npm run",
        )  # fmt: skip
        found += [(f"{runner} {s}", "package.json") for s in scripts]
    for name in ("justfile", "Justfile", ".justfile"):
        if (root / name).is_file():
            text = (root / name).read_text(encoding="utf-8", errors="replace")
            # A recipe's parameters may carry defaults (`scan target='x':`); `x := 1` is a variable.
            for m in re.finditer(r"^([A-Za-z0-9_-]+)(?:\s[^:\n]*)?:(?!=)", text, re.M):
                found.append((f"just {m.group(1)}", name))
    for name in ("mise.toml", ".mise.toml"):
        if (root / name).is_file():
            try:
                tasks = tomllib.loads((root / name).read_text(encoding="utf-8")).get("tasks", {})
            except tomllib.TOMLDecodeError:
                tasks = {}
            found += [(f"mise run {t}", name) for t in tasks]
    if (root / "pyproject.toml").is_file():
        try:
            tools = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            tools = {}
        run = "uv run " if (root / "uv.lock").is_file() else ""
        for tool, command in (("pytest", "pytest"), ("ruff", "ruff check .")):
            if tool in tools.get("tool", {}):
                found.append((f"{run}{command}", "pyproject.toml"))
    for folder in (root, root / "scripts", root / "bin"):
        if folder.is_dir():
            for p in sorted(folder.glob("*.sh")):
                rel = p.relative_to(root).as_posix()
                found.append((f"./{rel}", rel))
    return found


# The script's subcommands that only read, which setup proposes allowing without a prompt. The `*`
# before the path stands in for wherever the plugin is installed, which differs per machine and
# changes when it updates; a plugin can't ship permission rules of its own. Nothing that writes
# is here: new, ship and close keep asking, and so does accept, which runs a change's own checks.
READ_ONLY = (
    "status", "check", "config", "next", "undone", "checks", "context", "readiness", "unreleased",
    "drift", "next-entry", "bugs", "intake", "closes", "preflight", "nits", "findings", "groups",
)  # fmt: skip
ALLOW_RULES = [f"Bash(uv run --quiet --script */scripts/sdlc.py {c} *)" for c in READ_ONLY]
SETTINGS = ".claude/settings.json"  # as git prints it, on every platform
# Each person's own settings, which override the shared ones: read, never written.
LOCAL_SETTINGS = ".claude/settings.local.json"
# What `git.attribution = false` has setup write into the shared settings: the object form, an
# empty string hiding each line. Never `"attribution": false`, which Claude Code before v2.1.281
# rejects, skipping the whole file, allow rules and all.
ATTRIBUTION_OFF = {"commit": "", "pr": "", "sessionUrl": False}


def _allowed(root: Path) -> list[str]:
    try:
        allow = json.loads((root / SETTINGS).read_text(encoding="utf-8"))["permissions"]["allow"]
        return [a for a in allow if isinstance(a, str)]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def _settings_attribution(root: Path, rel: str) -> object | None:
    """The `attribution` a settings file holds, or None when it holds none or can't be read."""
    try:
        data = json.loads((root / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data.get("attribution") if isinstance(data, dict) else None


def attribution_status(root: Path, cfg: dict) -> tuple[str, str, str, dict | None]:
    """(name, status, detail, merge) for the host's answer on attribution against its settings:
    `merge` is the object setup writes into the shared settings, or None when there's nothing to
    write. Unset is a question setup still has to ask, never a default."""
    value = cfg["git"]["attribution"]
    if value is None:
        detail = "not chosen: setup asks whether commits and pull requests name the agent"
        return "attribution", "missing", detail, None
    if value:
        return "attribution", "ok", "on: the harness's own", None
    local = _settings_attribution(root, LOCAL_SETTINGS)
    if local is not None and local != ATTRIBUTION_OFF:
        detail = f"off, but {LOCAL_SETTINGS} sets its own attribution, which wins over {SETTINGS}"
        return "attribution", "warn", detail, None
    if _settings_attribution(root, SETTINGS) == ATTRIBUTION_OFF:
        return "attribution", "ok", f"off: {SETTINGS} hides the agent's lines", None
    detail = f"off, but {SETTINGS} doesn't hide the agent's lines yet"
    return "attribution", "missing", detail, dict(ATTRIBUTION_OFF)


def permissions_status(root: Path) -> tuple[str, str, str]:
    """(name, status, detail) for the read-only allowlist in the shared settings."""
    try:
        data = json.loads((root / SETTINGS).read_text(encoding="utf-8"))
        allow = data.get("permissions", {}).get("allow", [])
    except FileNotFoundError:
        allow = []
    except (ValueError, AttributeError):
        return "permissions", "warn", f"{SETTINGS} won't parse"
    missing = [r for r in ALLOW_RULES if r not in allow]
    if not missing:
        return "permissions", "ok", f"{SETTINGS} allows the read-only commands"
    return "permissions", "missing", f"{len(missing)} read-only rule(s) not in {SETTINGS}"


def detect_candidates(root: Path) -> dict[str, list[dict]]:
    """For each command key setup asks about, the repo's tasks whose names suggest it."""
    out: dict[str, list[dict]] = {key: [] for key in CANDIDATE_KEYS}
    for command, source in _task_names(root):
        words = set(re.split(r"[^a-z0-9]+", command.lower().rsplit("/", 1)[-1]))
        for key, hints in CANDIDATE_KEYS.items():
            if words & set(hints):
                out[key].append({"command": command, "source": source})
    return out


# The commands a repo may leave unset by choice: `missing` all the same, but never a gap that keeps
# setup from being complete.
UNSET_IS_A_CHOICE = ("commands.build", "commands.scan")


def cmd_readiness(root: Path) -> int:
    """Whether this repo is set up for the plugin, item by item, as JSON. Writes nothing.

    `required` items stop a skill until fixed; the rest the plugin works without, less well. A
    re-run on a repo that is set up is how setup says so: `complete` is true when every item is
    answered (but the `UNSET_IS_A_CHOICE` ones, listed in `unset`, and an `archive.target` of
    `none`) and `drift` has nothing in `breaking`, `refresh` or `report`, and setup then stops
    before its drafts."""
    home = main_root(root)
    cfg, warnings, parsed = load_config(root)
    items: list[dict] = []

    def item(name: str, status: str, detail: str, required: bool = False) -> None:
        items.append({"name": name, "status": status, "detail": detail, "required": required})

    ignored = work_ignored(home)
    if ignored is None:
        item("work", "n/a", "not a git repo")
    elif not ignored:
        item("work", "ok", f"{work_rel(home)}/ is committed", required=True)
    else:
        item("work", "missing", ignored_message(home), required=True)
    cfg_file = root / HOST_DIR / "config.toml"
    if not cfg_file.is_file():
        item("config", "missing", f"no {HOST_DIR}/config.toml: every setting is its default")
    else:
        item(
            "config",
            "ok" if parsed and not warnings else "warn",
            "; ".join(warnings) or f"{HOST_DIR}/config.toml parses",
            required=not parsed,
        )
    for key in ("process", "review", "policy"):
        rel = cfg["docs"][key]
        found = doc_path(root, key, rel) if rel else None
        if not found or not found["exists"]:
            item(f"docs.{key}", "missing", f"{rel} doesn't exist")
        elif found["source"] == "plugin":
            item(f"docs.{key}", "missing", f"{rel} doesn't exist; the plugin's guide stands in")
        elif is_unfilled(Path(found["path"]) if Path(found["path"]).is_absolute() else root / rel):
            item(f"docs.{key}", "warn", f"{rel} is still the template: fill in its `<` prompts")
        else:
            item(f"docs.{key}", "ok", rel)
    fields, problems = project_doc(root, cfg)
    rel = cfg["docs"]["project"]
    if problems:
        item("docs.project", "warn", "; ".join(problems))
    elif not rel or not (root / rel).is_file():
        item("docs.project", "ok", f"off: no {rel or 'project doc'}, so issues get labels only")
    else:
        item("docs.project", "ok", f"{rel}: " + (", ".join(fields) or "no field on"))
    product = product_doc(root, cfg)
    rel = cfg["docs"]["product"]
    evidence = cfg["retro"]["evidence"]
    if product is None:
        item("docs.product", "ok", f"off: no {rel or 'product doc'}, so no outcomes to serve")
        item(
            "retro.evidence",
            "warn" if evidence else "n/a",
            "set, but it runs only with a product doc" if evidence else "no product doc",
        )
    else:
        live = [i["id"] for i in product["items"] if i["status"] == "open"]
        item(
            "docs.product",
            "warn" if product["problems"] else "ok",
            "; ".join(product["problems"])
            or f"{rel}: {len(live)} open outcome(s)" + (f" ({', '.join(live)})" if live else ""),
        )
        item(
            "retro.evidence",
            "ok",
            f"{len(evidence)} command(s)" if evidence else "none: the product pass has no evidence",
        )
    context = [rel for rel in cfg["docs"]["context"] if (root / rel).is_file()]
    item(
        "context",
        "ok" if context else "missing",
        ", ".join(context)
        if context
        else "no CLAUDE.md or AGENTS.md: sessions start with no context here",
    )
    for key in ("check", "build", "scan"):
        value = cfg["commands"][key]
        item(f"commands.{key}", "ok" if value else "missing", value or "unset")
    # What the scan's findings mean. Off with no scan to explain; with one, worth drafting.
    rel = cfg["docs"]["health"]
    if not cfg["commands"]["scan"]:
        item("docs.health", "n/a", "no commands.scan, so no findings to route")
    elif not rel or not (root / rel).is_file():
        item(
            "docs.health",
            "missing",
            f"{rel or 'no health doc'}: findings route by the health check's defaults alone",
        )
    elif is_unfilled(root / rel):
        item("docs.health", "warn", f"{rel} is still the template: fill in its `<` prompts")
    else:
        item("docs.health", "ok", rel)
    unavailable = archive_unavailable(home, cfg)
    item(
        "archive",
        "ok" if not unavailable else "warn",
        f"{cfg['archive']['target']}" + (f": {unavailable}" if unavailable else ""),
    )
    if not unavailable:
        for name, status, detail in tracker(home, cfg).readiness():
            item(name, status, detail)
    item(*permissions_status(root))
    name, status, detail, merge = attribution_status(root, cfg)
    item(name, status, detail)
    found = drift(root) if cfg_file.is_file() else None
    if found is None:
        item("drift", "n/a", "not set up yet")
    else:
        changed = len(found["breaking"]) + len(found["refresh"])
        item(
            "drift",
            "warn" if changed else "ok",
            f"{len(found['breaking'])} breaking, {len(found['refresh'])} doc(s) to refresh, "
            f"{len(found['report'])} to look at"
            if changed
            else "setup matches this plugin's defaults",
        )

    unset = [i["name"] for i in items if i["name"] in UNSET_IS_A_CHOICE and i["status"] != "ok"]
    # A repo tracked locally archives nowhere by its own answer: a warning, never a gap.
    chosen = {*unset, *(["archive"] if cfg["archive"]["target"] == "none" else [])}
    out = {
        "ready": all(i["status"] in ("ok", "n/a") for i in items if i["required"]),
        # Nothing for setup to draft: every item answered, and nothing the plugin changed under it.
        "complete": found is not None
        and all(i["status"] in ("ok", "n/a") or i["name"] in chosen for i in items)
        and not (found["breaking"] or found["refresh"] or found["report"]),
        # The commands a repo usually sets, left unset, which a complete run lists.
        "unset": unset,
        "items": items,
        "candidates": detect_candidates(root),
        "permissions": {
            "file": SETTINGS,
            "rules": ALLOW_RULES,
            "missing": [r for r in ALLOW_RULES if r not in _allowed(root)],
        },
        # The host's answer, and the object setup merges into the shared settings for it.
        "attribution": {"value": cfg["git"]["attribution"], "merge": merge},
        # What setup copies from, when the repo has none of its own.
        "defaults": {key: str(DEFAULTS_DIR / name) for key, name in HOST_DOCS.items()},
        # The issue forms setup offers a repo tracked on GitHub, where each goes, and whether it is
        # there already: one that is, is the host's, never written over.
        "issue_forms": {
            rel: {"from": str(DEFAULTS_DIR / name), "present": (home / rel).is_file()}
            for rel, name in ISSUE_FORMS.items()
        }
        if cfg["archive"]["target"] == "github"
        else {},
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


@command("readiness", "whether this repo is set up for the plugin, as JSON; writes nothing")
def cli_readiness(root: Path, home: Path, args) -> int:
    return cmd_readiness(root)


# Setup's life after the first run. A host owns the docs setup copied from `defaults/`, so a newer
# plugin can't just overwrite them; `record` keeps a hash of each block of each default as it was
# copied, and `drift` compares three ways (the default now, that hash, the host's text) to tell
# what the plugin changed from what the host did. Neither writes a host doc: setup drafts the
# refresh, behind its one WAIT.
MANIFEST = f"{HOST_DIR}/setup.json"
# Each [docs] key setup fills from a default, and the default it copies.
HOST_DOCS = {
    "process": "SDLC.md",
    "review": "REVIEW.md",
    "project": "PROJECT.md",
    "product": "PRODUCT.md",
    "health": "HEALTH.md",
}
# The issue forms setup offers a repo tracked on GitHub, by where each goes, from `defaults/`, so
# a person filing a bug gives what a `[bug]` entry needs. The host's once written: never drifted,
# never removed by uninstall.
ISSUE_FORMS = {
    ".github/ISSUE_TEMPLATE/sdlc-bug.yml": "issue-forms/sdlc-bug.yml",
    ".github/ISSUE_TEMPLATE/sdlc-request.yml": "issue-forms/sdlc-request.yml",
}
# A config key a release renamed or removed: `section.old` → {"now": the key that replaced it, or
# None, "since": the version, "do": what a host does about it}. A host still setting one has a
# setting the plugin no longer reads, which is breaking. Each entry is a shim, registered in
# `.sdlc/deprecations.toml` and removed in the release its entry names; after that, drift reports
# the key as one it doesn't read.
RETIRED_KEYS: dict[str, dict[str, str | None]] = {}
# What the script reads from each template, so a host's override that lacks one would be misread.
# Frontmatter keys, `## ` headings and literal placeholders; a template with nothing read has no
# entry.
TEMPLATE_READS: dict[str, dict[str, tuple[str, ...]]] = {
    "intent.md": {
        "keys": (
            "id",
            "slug",
            "tier",
            "impact",
            "stage",
            "created",
            "updated",
            "idea",
            "depends_on",
        ),
        "headings": ("Problem", "Outcome", "Open questions"),
    },
    "issue.md": {"placeholders": ("{{artifacts}}",)},
    # `{{date}}` is left out: a host's changelog may not date its releases.
    "changelog.md": {"placeholders": ("{{version}}", "{{notes}}")},
    # The board's plan hint counts the paths this section names.
    "plan.md": {"headings": ("Files to change",)},
    # The report's spend view (`retro.render_report()`).
    "retro.md": {"headings": ("Spend",), "placeholders": ("{{spend}}",)},
}
# Classes a refresh proposes text for; the rest are reported or left alone.
PROPOSED = ("added", "refreshed", "removed")
WORKTREES_LINE = ".claude/worktrees/"
# A line in a context doc that names the plugin, which uninstall lists rather than edits.
MENTIONS_RE = re.compile(r"/sdlc:|\.sdlc/|(?<![\w.])work/")
PLUGIN_RULE_RE = re.compile(r"^Bash\(uv run --quiet --script \*/scripts/sdlc\.py [a-z-]+ \*\)$")


def plugin_version() -> str | None:
    """The version in this copy of the plugin's manifest."""
    try:
        path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
        return json.loads(path.read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _older(a: str | None, b: str | None) -> bool:
    """Whether version `a` comes before `b`; False when either isn't X.Y.Z."""
    try:
        return _semver(a or "") < _semver(b or "")
    except ValueError:
        return False


def read_manifest(root: Path) -> tuple[dict | None, str | None]:
    """(the manifest, why it couldn't be read). Neither when there is none: a repo set up before
    the manifest existed, which drift compares two ways."""
    path = root / MANIFEST
    if not path.is_file():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        return None, f"{MANIFEST} won't parse: {e}"
    if not isinstance(data, dict) or not isinstance(data.get("docs", {}), dict):
        return None, f"{MANIFEST} isn't a manifest"
    return data, None


def _copy_source(key: str) -> tuple[Path, str]:
    """The plugin text a host doc tracks, and its name: the guide for the process and review docs
    (which hold the host's answers to it), else the default setup copied."""
    if key in GUIDES:
        return GUIDE_DIR / GUIDES[key], GUIDES[key]
    return DEFAULTS_DIR / HOST_DOCS[key], HOST_DOCS[key]


def cmd_record(root: Path, created: list[str], gitignore_line: bool) -> int:
    """Write `.sdlc/setup.json`: this plugin's version, its config keys, and a hash of each block
    of each default behind a host doc, as of now. Writes nothing else. Setup runs it after every
    write, so the next drift compares against what the host was last offered.

    The process and review docs hold only the host's answers to the guide: each gets
    `layout: answers` and a hash of the whole guide, so drift can say when the guide changed,
    and no block hashes, since nothing of the guide's is in it."""
    if not (root / HOST_DIR / "config.toml").is_file():
        print(f"⚠  no {HOST_DIR}/config.toml: run /sdlc:setup first", file=sys.stderr)
        return 1
    bad = [p for p in created if Path(p).is_absolute() or ".." in Path(p).parts]
    if bad:
        print(f"⚠  --created takes paths inside the repo: {', '.join(bad)}", file=sys.stderr)
        return 1
    cfg = load_config(root)[0]
    before = read_manifest(root)[0] or {}
    docs = {}
    for key in HOST_DOCS:
        rel = cfg["docs"][key]
        if not rel or not (root / rel).is_file():
            continue
        source, name = _copy_source(key)
        text = source.read_text(encoding="utf-8")
        if key in GUIDES:
            docs[key] = {"path": rel, "layout": "answers", "guide": unit_hash(text)}
        else:
            units = {k: unit_hash(v) for k, v in doc_units(text)}
            docs[key] = {"path": rel, "default": name, "units": units}
    manifest = {
        "version": plugin_version(),
        "config_keys": sorted(f"{s}.{k}" for s, keys in CONFIG_KEYS.items() for k in keys),
        "docs": docs,
        "templates": {
            p.name: unit_hash(p.read_text(encoding="utf-8"))
            for p in sorted(TEMPLATE_DIR.glob("*.md"))
        },
        "created": sorted({*before.get("created", []), *(Path(p).as_posix() for p in created)}),
        "gitignore_line": bool(before.get("gitignore_line")) or gitignore_line,
        # Setup's: the host answered off, and the shared settings hide the agent's lines.
        "attribution": cfg["git"]["attribution"] is False
        and _settings_attribution(root, SETTINGS) == ATTRIBUTION_OFF,
    }
    (root / MANIFEST).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"  wrote  {MANIFEST}  (plugin {manifest['version']}, {len(docs)} doc(s))")
    return 0


@command(
    "record",
    "write .sdlc/setup.json: the defaults setup offered, for the next drift",
    arg("--created", nargs="*", default=[], help="the paths setup created"),
    arg(
        "--gitignore-line", action="store_true", help=f"setup added {WORKTREES_LINE} to .gitignore"
    ),
)
def cli_record(root: Path, home: Path, args) -> int:
    return cmd_record(root, args.created, args.gitignore_line)


def _classify(
    default: list[tuple[str, str]], host: list[tuple[str, str]], base: dict[str, str] | None
) -> list[dict]:
    """Each block of a host doc against its default, by key: what the plugin changed (`added`,
    `refreshed`, `removed`), what the host did (`own`, `edited`, `host-removed`), both (`conflict`),
    or neither (`current`). With no base, only `current`, `added`, `own` and `differs`."""
    d, h = dict(default), dict(host)
    out = []
    for key in dict.fromkeys([k for k, _ in default] + [k for k, _ in host]):
        dt, ht = d.get(key), h.get(key)
        dh, hh = (unit_hash(t) if t is not None else None for t in (dt, ht))
        bh = base.get(key) if base is not None else None
        if dt is not None and ht is not None:
            if dh == hh:
                cls = "current"
            elif base is None:
                cls = "differs"
            elif bh == hh:
                cls = "refreshed"
            elif bh == dh:
                cls = "edited"
            else:
                cls = "conflict"
        elif dt is not None:
            cls = "host-removed" if bh is not None else "added"
        elif base is None or bh is None:
            cls = "own"
        else:
            cls = "removed" if bh == hh else "conflict"
        out.append({"unit": key, "class": cls, "host": ht, "default": dt})
    return out


def _apply(host_text: str, default: list[tuple[str, str]], entries: list[dict]) -> str:
    """The host doc with each proposed block taken: a refreshed one replaced, a removed one
    dropped, an added one put after the nearest block before it in the default that the host
    has. Every other block stays exactly as the host wrote it."""
    by = {e["unit"]: e for e in entries if e["class"] in PROPOSED}
    blocks: list[list] = []  # [key, text, touched]
    for key, text in doc_units(host_text):
        e = by.get(key)
        if e is None:
            blocks.append([key, text, False])
        elif e["class"] == "refreshed":
            blocks.append([key, e["default"], True])
    for i, (key, text) in enumerate(default):
        e = by.get(key)
        if not e or e["class"] != "added":
            continue
        keys = [b[0] for b in blocks]
        anchor = next((k for k, _ in reversed(default[:i]) if k in keys), None)
        e["anchor"] = anchor
        at = keys.index(anchor) + 1 if anchor else int(bool(keys) and keys[0] == "#")
        blocks.insert(at, [key, text, True])
    # Where a taken block meets its neighbour, a blank line before a heading and none between two
    # bullets, so a list stays tight. Elsewhere the host's spacing is left as it is.
    texts = []
    for i, (_, text, touched) in enumerate(blocks):
        last = i == len(blocks) - 1
        if last and touched:
            text = text.rstrip("\n")
        elif not last and (touched or blocks[i + 1][2]):
            text = text.rstrip("\n") + ("" if blocks[i + 1][0].endswith("**") else "\n")
        texts.append(text)
    body = _body_of(host_text)
    head = host_text[: len(host_text) - len(body)]
    return head + "\n".join(texts) + ("\n" if host_text.endswith("\n") else "")


def _template_misses(name: str, text: str) -> list[str]:
    reads = TEMPLATE_READS.get(name, {})
    lines = {line.strip().lower() for line in text.splitlines()}
    return [
        *(
            f"the `{k}:` frontmatter key"
            for k in reads.get("keys", ())
            if frontmatter_list(text, k) is None
        ),
        *(
            f"the `## {h}` heading"
            for h in reads.get("headings", ())
            if f"## {h}".lower() not in lines
        ),
        *(f"the `{p}` placeholder" for p in reads.get("placeholders", ()) if p not in text),
    ]


def _under_guide(key: str, guide_keys: set[str]) -> bool:
    """Whether a host block's key is a guide block's, or sits under one: the only places an answer
    can stand in for, or follow, what the guide says."""
    while True:
        if key in guide_keys:
            return True
        if " > " not in key:
            return False
        key = key.rsplit(" > ", 1)[0]


def _answers_drift(
    rel: str, guide: Path, host_text: str, recorded: dict | None, version: str | None
) -> list[dict]:
    """What a person should read about an answers file: the guide changed since setup's record
    (a note, never a refresh, since nothing of the guide's is in the host's file), and each host
    block whose heading the guide has nowhere, which no reader can place."""
    text = guide.read_text(encoding="utf-8")
    found = []
    if recorded and recorded.get("guide") not in (None, unit_hash(text)):
        detail = f"the plugin's {guide.name} changed since {version}: read it"
        found.append({"what": "doc", "where": rel, "class": "guide-changed",
                      "guide": str(guide), "detail": detail})  # fmt: skip
    keys = {k for k, _ in doc_units(text)}
    found += [
        {
            "what": "doc",
            "where": rel,
            "class": "unknown",
            "unit": k,
            "detail": f"no heading in the plugin's {guide.name} to place it under",
        }  # fmt: skip
        for k, _ in doc_units(host_text)
        if k != "#" and not _under_guide(k, keys)
    ]
    return found


def drift(root: Path) -> dict:
    """What a newer plugin changed under a host's setup, read-only. `breaking` is what the plugin
    would now misread (a retired config key, an override lacking what the script reads, a doc the
    script can't parse); `refresh` the blocks of each host doc it can propose text for, with the
    doc as it would read (`proposed`); `report` the rest a person should see and decide."""
    cfg, _, parsed = load_config(root)
    manifest, unreadable = read_manifest(root)
    plugin = plugin_version()
    version = (manifest or {}).get("version")
    out: dict = {
        "base": "manifest" if manifest else "none",
        "version": {"manifest": version, "plugin": plugin},
        "breaking": [],
        "refresh": [],
        "report": [],
        "docs": {},
    }
    if unreadable:
        out["report"].append(
            {
                "what": "manifest",
                "where": MANIFEST,
                "class": "unreadable",
                "detail": unreadable,
            }
        )
    downgrade = _older(plugin, version)
    if downgrade:
        out["report"].append(
            {
                "what": "manifest",
                "where": MANIFEST,
                "class": "downgrade",
                "detail": f"recorded by {version}, newer than this {plugin}: nothing proposed",
            }
        )

    for key in HOST_DOCS:
        rel = cfg["docs"][key]
        if not rel or not (root / rel).is_file():
            continue
        host_text = (root / rel).read_text(encoding="utf-8")
        source, name = _copy_source(key)
        recorded = (manifest or {}).get("docs", {}).get(key)
        if key in GUIDES:
            out["docs"][key] = {"path": rel, "layout": "answers", "guide": str(source)}
            out["report"] += _answers_drift(rel, source, host_text, recorded, version)
            continue
        default = doc_units(source.read_text(encoding="utf-8"))
        if recorded and recorded.get("path") != rel:
            out["report"].append(
                {
                    "what": "doc",
                    "where": rel,
                    "class": "moved",
                    "detail": f"recorded at {recorded.get('path')}, now docs.{key} = {rel}",
                }
            )
        entries = _classify(default, doc_units(host_text), recorded["units"] if recorded else None)
        classes: dict[str, list[str]] = {}
        for e in entries:
            classes.setdefault(e["class"], []).append(e["unit"])
        out["docs"][key] = {"path": rel, "default": name, "classes": classes}
        changes = [e for e in entries if e["class"] in PROPOSED]
        if changes and not downgrade:
            proposed = _apply(host_text, default, changes)
            out["refresh"].append({"doc": key, "path": rel, "units": changes, "proposed": proposed})
        out["report"] += [
            {
                "what": "doc",
                "where": rel,
                "class": e["class"],
                "unit": e["unit"],
                "host": e["host"],
                "default": e["default"],
            }
            for e in entries
            if e["class"] in ("conflict", "differs")
        ]

    cfg_file = root / HOST_DIR / "config.toml"
    if cfg_file.is_file() and not parsed:
        out["breaking"].append(
            {
                "what": "config",
                "where": cfg_file.relative_to(root).as_posix(),
                "detail": "won't parse",
                "fix": "fix the TOML",
            }
        )
    elif cfg_file.is_file():
        data = tomllib.loads(cfg_file.read_text(encoding="utf-8"))
        for section, values in data.items():
            keys = values if isinstance(values, dict) else {None: values}
            for k in keys:
                where = f"{section}.{k}" if k is not None else f"[{section}]"
                if section in CONFIG_KEYS and k in CONFIG_KEYS[section]:
                    continue
                if where in RETIRED_KEYS:
                    r = RETIRED_KEYS[where]
                    out["breaking"].append(
                        {
                            "what": "config",
                            "where": where,
                            "now": r.get("now"),
                            "detail": f"retired in {r.get('since')}: the plugin no longer reads it",
                            "fix": r.get("do"),
                        }
                    )
                else:
                    out["report"].append(
                        {
                            "what": "config",
                            "where": where,
                            "class": "unknown",
                            "detail": "the plugin doesn't read it",
                        }
                    )
    if manifest:
        known = set(manifest.get("config_keys", []))
        for section, keys in CONFIG_KEYS.items():
            for k, value in keys.items():
                if f"{section}.{k}" not in known:
                    out["report"].append(
                        {
                            "what": "config",
                            "where": f"{section}.{k}",
                            "class": "new",
                            "default": value,
                            "detail": f"new since {version}; docs/REFERENCE.md says what it does",
                        }
                    )

    templates = root / HOST_DIR / "templates"
    for p in sorted(templates.glob("*.md")) if templates.is_dir() else []:
        where = f"{HOST_DIR}/templates/{p.name}"
        plugin_t = TEMPLATE_DIR / p.name
        if not plugin_t.is_file():
            out["report"].append(
                {
                    "what": "template",
                    "where": where,
                    "class": "unknown",
                    "detail": "no plugin template has this name: nothing reads it",
                }
            )
            continue
        for miss in _template_misses(p.name, p.read_text(encoding="utf-8")):
            out["breaking"].append(
                {
                    "what": "template",
                    "where": where,
                    "detail": f"lacks {miss}, which the plugin reads",
                    "fix": f"add it back, or `/sdlc:setup reset {p.name}` to use the plugin's",
                }
            )
        recorded = (manifest or {}).get("templates", {}).get(p.name)
        now = unit_hash(plugin_t.read_text(encoding="utf-8"))
        if recorded and recorded != now:
            out["report"].append(
                {
                    "what": "template",
                    "where": where,
                    "class": "changed",
                    "detail": f"the plugin's {p.name} changed since {version}",
                    "plugin": str(plugin_t),
                }
            )

    out["breaking"] += [
        {
            "what": "doc",
            "where": f"docs.project ({cfg['docs']['project']})",
            "detail": problem,
            "fix": "fix the doc's frontmatter",
        }
        for problem in project_doc(root, cfg)[1]
    ]
    product = product_doc(root, cfg)
    out["breaking"] += [
        {
            "what": "doc",
            "where": f"docs.product ({cfg['docs']['product']})",
            "detail": problem,
            "fix": "fix the outcome lines",
        }
        for problem in (product or {"problems": []})["problems"]
    ]
    return out


def cmd_drift(root: Path) -> int:
    print(json.dumps(drift(root), indent=2, ensure_ascii=False))
    return 0


@command("drift", "what changed under this repo's setup since it ran, as JSON; writes nothing")
def cli_drift(root: Path, home: Path, args) -> int:
    return cmd_drift(root)


def setup_nudge(root: Path) -> str | None:
    """One line for status when setup hasn't seen this plugin version; None when it has, or the
    repo isn't set up."""
    if not (root / HOST_DIR / "config.toml").is_file():
        return None
    manifest, unreadable = read_manifest(root)
    plugin = plugin_version()
    if unreadable:
        return f"{unreadable}  /sdlc:setup"
    if manifest is None:
        return f"no record of the plugin version that set this repo up (now {plugin})  /sdlc:setup"
    if _older(manifest.get("version"), plugin):
        return f"set up with {manifest.get('version')}, the plugin is {plugin}  /sdlc:setup"
    return None


def _tracked(home: Path, rel: str) -> list[str]:
    return [p for p in (_git(home, "ls-files", "--", rel) or "").splitlines() if p]


def cmd_reset(root: Path, name: str, check_only: bool = False) -> int:
    """Delete one template override in `.sdlc/templates/`, so the plugin's own is used again. It
    takes a bare file name and refuses anything else, and an override with uncommitted edits,
    which history couldn't bring back."""
    rel = f"{HOST_DIR}/templates/{name}"
    if not name or name != Path(name).name or name in (".", "..") or not name.endswith(".md"):
        print(
            f"⚠  reset takes a template's file name, e.g. intent.md, not {name!r}", file=sys.stderr
        )
        return 1
    if not (root / rel).is_file():
        print(f"⚠  no override {rel}: the plugin's own {name} is in use", file=sys.stderr)
        return 1
    if rel in _dirty_paths(root):
        print(f"⚠  {rel} has uncommitted edits: commit or discard them first", file=sys.stderr)
        return 1
    print(json.dumps({"remove": [rel], "then": str(TEMPLATE_DIR / name)}, indent=2))
    if not check_only:
        (root / rel).unlink()
    return 0


@command(
    "reset",
    "delete one .sdlc/templates/ override",
    arg("name", help="the template's file name, e.g. intent.md"),
    arg("--check", action="store_true", help="preconditions only, write nothing"),
)
def cli_reset(root: Path, home: Path, args) -> int:
    return cmd_reset(root, args.name, args.check)


def uninstall_plan(root: Path) -> dict:
    """What `uninstall` would remove and what it leaves, and why it refuses, if it does. It
    removes only setup's: `.sdlc/`'s committed files, the plugin's allow rules, and the worktrees
    ignore line when setup recorded adding it. A change still open, standing in a worktree or
    shipped and not closed refuses it, as does an uncommitted edit to anything it would remove:
    what it removes has to be in history."""
    home = main_root(root)
    cfg = load_config(home)[0]
    manifest = read_manifest(home)[0] or {}
    refused, named = [], set()
    for rec in analyze(home)["open"]:
        named.add(f"{rec['id']}-{rec['slug']}")
        refused.append(f"{rec['id']}-{rec['slug']} is open: ship and close it, or drop it")
    for rec in ready_to_close(home):
        named.add(rec["branch"])
        refused.append(f"{rec['branch']} is {rec['kind']} but not closed: /sdlc:close {rec['id']}")
    for tree, branch in worktrees(home):
        if DIR_RE.match(branch) and tree.resolve() != home.resolve() and branch not in named:
            refused.append(f"worktree {branch} still stands at {tree}")
    settings = home / SETTINGS
    touched = (f"{HOST_DIR}/", SETTINGS, ".gitignore")
    # The change folder sits under `.sdlc/`, but it is the repo's record, never setup's to remove.
    own = f"{work_rel(home)}/"
    refused += [
        f"{p} has uncommitted changes: commit or discard them first"
        for p in _dirty_paths(home)
        if (p.startswith(touched[0]) and not p.startswith(own)) or p in touched[1:]
    ]
    remove = [p for p in _tracked(home, HOST_DIR) if not p.startswith(own)]
    plan: dict = {"refused": refused, "remove": remove, "edit": [], "left": []}
    left = (
        sorted(
            p.relative_to(home).as_posix()
            for p in (home / HOST_DIR).rglob("*")
            if p.is_file()
            and p.relative_to(home).as_posix() not in plan["remove"]
            and not p.relative_to(home).as_posix().startswith(own)
        )
        if (home / HOST_DIR).is_dir()
        else []
    )
    plan["left"] += [{"path": p, "why": "not in git, so not setup's to remove"} for p in left]
    try:
        allow = json.loads(settings.read_text(encoding="utf-8"))["permissions"]["allow"]
        rules = [r for r in allow if isinstance(r, str) and PLUGIN_RULE_RE.match(r)]
    except (OSError, ValueError, KeyError, TypeError):
        rules = []
    attribution = _settings_attribution(home, SETTINGS)
    # Setup's object goes only when its record says setup wrote it and nobody changed it since.
    ours = bool(manifest.get("attribution")) and attribution == ATTRIBUTION_OFF
    if attribution is not None and not ours:
        why = "its attribution isn't setup's, or changed since setup wrote it"
        plan["left"].append({"path": f"{SETTINGS} attribution", "why": why})
    if rules or ours:
        created = SETTINGS in manifest.get("created", [])
        plan["edit"].append(
            {
                "path": SETTINGS,
                "remove_rules": rules,
                "remove_attribution": ours,
                "remove_if_empty": created,
            }  # fmt: skip
        )
    ignore = home / ".gitignore"
    if ignore.is_file() and WORKTREES_LINE in ignore.read_text(encoding="utf-8").splitlines():
        if manifest.get("gitignore_line"):
            # Setup's own file goes too, once its line was all it held.
            created = ".gitignore" in manifest.get("created", [])
            plan["edit"].append(
                {"path": ".gitignore", "remove_line": WORKTREES_LINE, "remove_if_empty": created}
            )
        else:
            plan["left"].append(
                {
                    "path": ".gitignore",
                    "why": f"no record that setup added "
                    f"{WORKTREES_LINE}: remove the line yourself if it did",
                }
            )
    plan["left"].append({"path": f"{work_rel(home)}/", "why": "the repo's record of its changes"})
    for rel in ISSUE_FORMS:
        if (home / rel).is_file():
            plan["left"].append({"path": rel, "why": "an issue form: the repo's once written"})
    if cfg["archive"]["target"] != "none":
        plan["left"].append(
            {
                "path": f"{cfg['archive']['target']} issues",
                "why": "the archive: nothing on the tracker is touched",
            }
        )
    mentions = []
    for rel in dict.fromkeys([cfg["docs"]["policy"], *cfg["docs"]["context"]]):
        path = home / rel if rel else None
        if path and path.is_file():
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if MENTIONS_RE.search(line):
                    mentions.append({"path": rel, "line": n, "text": line.strip()})
    plan["mentions"] = mentions
    return plan


def cmd_uninstall(root: Path, check_only: bool = False) -> int:
    """Take setup back out of the main checkout, after `uninstall_plan()`'s refusals. Commits
    nothing, and leaves `.sdlc/work/`, the context docs and the tracker alone."""
    home = main_root(root)
    plan = uninstall_plan(root)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    if plan["refused"]:
        return 1
    if check_only:
        return 0
    for rel in plan["remove"]:
        (home / rel).unlink(missing_ok=True)
    for folder in sorted((home / HOST_DIR).rglob("*"), reverse=True):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
    if (home / HOST_DIR).is_dir() and not any((home / HOST_DIR).iterdir()):
        (home / HOST_DIR).rmdir()
    for edit in plan["edit"]:
        path = home / edit["path"]
        if "remove_rules" in edit:
            data = json.loads(path.read_text(encoding="utf-8"))
            if edit["remove_rules"]:
                allow = data["permissions"]["allow"]
                data["permissions"]["allow"] = [r for r in allow if r not in edit["remove_rules"]]
            if edit.get("remove_attribution"):
                data.pop("attribution", None)
            # Setup's own file goes too, once its rules and its attribution were all it held.
            stub = data in ({}, {"permissions": {"allow": []}}, {"permissions": {}})
            if edit.get("remove_if_empty") and stub:
                path.unlink()
            else:
                text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
                path.write_text(text, encoding="utf-8", newline="\n")
        else:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            kept = [ln for ln in lines if ln.rstrip("\r\n") != edit["remove_line"]]
            if edit.get("remove_if_empty") and not "".join(kept).strip():
                path.unlink()
            else:
                path.write_text("".join(kept), encoding="utf-8", newline="\n")
    return 0


@command(
    "uninstall",
    "remove what setup wrote, refusing while any change is live",
    arg("--check", action="store_true", help="the plan only, write nothing"),
)
def cli_uninstall(root: Path, home: Path, args) -> int:
    return cmd_uninstall(root, args.check)


def changed_paths(root: Path, base: str) -> tuple[str, list[tuple[str, str, str | None]]] | None:
    """The merge base with `base`, and (status, path, renamed to) for everything this checkout
    changes since it: committed, uncommitted and untracked, since /sdlc:ship asks before the
    commit. None outside git or without `base`."""
    mb = _git(root, "merge-base", base, "HEAD")
    out = (
        _git(root, "-c", "core.quotePath=false", "diff", "--name-status", "-M", mb) if mb else None
    )
    if mb is None or out is None:
        return None
    rows: list[tuple[str, str, str | None]] = []
    for line in out.splitlines():
        parts = line.split("\t")
        rows.append((parts[0][0], parts[1], parts[2] if parts[0][0] == "R" else None))
    untracked = _git(
        root, "-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard"
    )
    rows += [("A", p, None) for p in (untracked or "").splitlines()]
    return mb, rows


def cmd_context(root: Path, base: str | None = None) -> int:
    """The context docs a change could have made wrong, as JSON, for /sdlc:ship's context pass.
    Writes nothing.

    `docs`: every `docs.context` file that exists, plus each CLAUDE.md or AGENTS.md in a folder
    above a changed path, since an agent loads that one whenever it works there. Both, when a
    folder has both: a CLAUDE.md importing AGENTS.md can still say things of its own. `stale`:
    their lines naming a
    path the diff deletes or renames, the way context goes wrong most often and most quietly.
    Whether anything else in them needs to change is judgment, and the skill's. The diff is taken
    against `base`, the base branch (`git.base`) unless given."""
    base = base or load_config(root)[0]["git"]["base"]
    out = _context_report(root, base)
    if out is None:
        print(
            f"⚠  no merge base with {base!r}: is this a git checkout with that branch?",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


@command(
    "context",
    "the context docs this checkout's diff could have made wrong, as JSON",
    arg("--base", help="what the diff is taken against (git.base)"),
)
def cli_context(root: Path, home: Path, args) -> int:
    return cmd_context(root, args.base)


def _context_report(root: Path, base: str | None) -> dict | None:
    """`context`'s report for checkout `root` against `base`, for `context` and `preflight`.
    None when there is no merge base."""
    cfg, _, _ = load_config(root)
    found = changed_paths(root, base) if base else None
    if found is None:
        return None
    mb, rows = found
    docs: dict[str, str] = {}
    for rel in cfg["docs"]["context"]:
        if (root / rel).is_file():
            docs.setdefault(rel, "docs.context")
    for _, path, to in rows:
        for p in filter(None, (path, to)):
            for parent in Path(p).parents:
                for name in ("CLAUDE.md", "AGENTS.md"):
                    cand = str(parent / name)
                    if (root / cand).is_file():
                        docs.setdefault(cand, f"above {p}")
    gone = [(path, st, to) for st, path, to in rows if st in ("D", "R")]
    stale = []
    for doc in docs:
        text = (root / doc).read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), start=1):
            for path, st, to in gone:
                if path in line:
                    stale.append(
                        {
                            "doc": doc,
                            "line": n,
                            "text": line.strip(),
                            "path": path,
                            "status": "renamed" if st == "R" else "deleted",
                            "to": to,
                        }
                    )
    out = {
        "base": base,
        "merge_base": mb,
        "changed": len(rows),
        "docs": [{"path": p, "why": why} for p, why in docs.items()],
        "stale": stale,
    }
    return out


def _not_due(due: dict, a: dict) -> str:
    """The Unreleased line's tail below the threshold: how far the batch is from due."""
    n, days = a.get("release_due_after", (0, 0))
    parts = [f"{due.get('minor', 0)} of {n} minor changes"] if n else []
    if days and due.get("oldest") is not None:
        parts.append(f"oldest {due['oldest']}d of {days}")
    return "not due: " + ", ".join(parts) if parts else "not due"


# How wide a line `print_status()` cuts a stopped run's problem to, so each stays one line.
STATUS_WIDTH = 100


def _cut(text: str, width: int) -> str:
    """`text` on one line of at most `width` characters, ending `…` when cut."""
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1].rstrip() + "…"


# `status`'s sections for the open changes, the board's columns in its order (`column()`), Needs
# you printed last, after Problems.
STATUS_STATES = (
    ("planned", "Planned"), ("designing", "Designing"), ("building", "Building"),
    ("ready", "Ready"), ("landing", "Landing"),
)  # fmt: skip
STATUS_TILDE = "    ~ = scaffolded from the template, not written yet"


def _by_state(a: dict) -> dict[str, tuple[list[dict], list[dict]]]:
    """Each state's open changes and its changes waiting on close, by each record's `column`, in
    `analyze()`'s order. A record read without one (a caller printing `analyze()` alone) sits
    where `column()` places it with nothing more to read than its stage and its errors."""
    shown: dict[str, tuple[list[dict], list[dict]]] = {
        key: ([], []) for key in (*(k for k, _ in STATUS_STATES), "needs-you")
    }
    for rec in a["open"]:
        key = rec.get("column") or column(
            {"stage": rec["stage"], "problems": rec.get("errors") or [], "mode": "manual"} | rec
        )
        shown[key][0].append(rec)
    for rec in a.get("ready") or []:
        shown[rec.get("column") or "landing"][1].append(rec)
    return shown


def _change_lines(rec: dict, a: dict) -> list[str]:
    """An open change's line, its title, and a stopped run's `⚠` and `→` lines."""
    tier = rec["tier"] if rec["tier"] is not None else "?"
    stage = rec["stage"] or "?"
    age = f"{rec['age_days']}d" if rec["age_days"] is not None else "?"
    have = (
        " ".join(
            n.removesuffix(".md") + ("~" if n in rec["unfilled"] else "") for n in rec["artifacts"]
        )
        or "(empty)"
    )
    undone = f"  · {len(rec['undone'])} undone" if rec.get("undone") else ""
    if rec.get("open_questions"):
        undone += f"  · {rec['open_questions']} open question(s)"
    if rec.get("behind"):
        undone += f"  · behind {a.get('trunk')} by {rec['behind']}: /sdlc:ship brings it up to date"
    if "quiet" in rec:
        ago = rec["touched_ago"]
        touched = f"touched {_ago(ago)} ago" if ago is not None else "never touched"
        mark = "stopped, " if rec.get("stopped") else "quiet, " if rec["quiet"] else ""
        undone += f"  · {mark}{touched}"
    gate = rec.get("gate")
    if gate and gate["current"]:
        undone += "  · gate green" if gate["verdict"] == "PASS" else "  · gate red"
    lines = [f"    {rec['id']}  T{tier} {stage:<8} {age:>4}  {rec['slug']:<28} {have}{undone}"]
    indent = " " * 30
    if rec["title"]:
        lines.append(f"{indent}{rec['title']}")
    if rec.get("stopped"):
        for problem in rec["stopped"]["problems"]:
            lines.append(f"{indent}⚠ {_cut(problem, STATUS_WIDTH - len(indent) - 2)}")
        lines.append(f"{indent}→ {rec['stopped']['next']}")
    return lines


def _close_line(rec: dict, a: dict) -> str:
    """A shipped or dropped change's line, naming `/sdlc:close`: marked dropped, or behind the base
    branch while its landing hasn't stopped (a stopped one says so on its `needs you:` line)."""
    mark = "  (dropped)" if rec.get("kind") == "dropped" else ""
    if not mark and rec.get("behind") and not rec.get("needs"):
        mark = f"  (behind {a.get('trunk')} by {rec['behind']}: rebase and ship again)"
    return f"    {rec['id']}  {rec['slug']:<28} → /sdlc:close {rec['id']}{mark}"


def print_status(a: dict) -> None:
    print(f"{a['work']} — {len(a['open'])} open, {len(a['changes'])} total   today: {a['today']}")

    states = _by_state(a)
    # The `~` legend once, after the last section that showed one.
    tildes = [k for k, (recs, _) in states.items() if any(r["unfilled"] for r in recs)]
    for key, label in STATUS_STATES:
        recs, closing = states[key]
        print(f"\n■ {label}: {len(recs) + len(closing)}")
        for rec in recs:
            for line in _change_lines(rec, a):
                print(line)
        for rec in closing:
            print(_close_line(rec, a))
        if tildes and tildes[-1] == key:
            print(STATUS_TILDE)

    # Left out where releasing isn't set up and nothing has landed: most repos, most of the time.
    rel = a.get("release")
    shims = rel.get("deprecations", {}) if rel else {}
    if rel and (rel["changes"] or not rel["configure"] or any(shims.values())):
        print(f"\n■ Unreleased: {len(rel['changes'])}")
        if rel["configure"]:
            print("    set release.version_files in .sdlc/config.toml to release them")
        elif rel["missing"]:
            missing = rel["missing"]
            print(f"    no tag {missing['tag']} for the current version: {missing['hint']}")
        elif rel["problems"]:
            for problem in rel["problems"]:
                print(f"    ⚠  {problem}")
        elif rel["nothing"]:
            print(f"    nothing to release since {rel['since']}")
        else:
            due = rel.get("due") or {}
            line = f"    since {rel['since']} → {rel['next']} ({rel['bump']})"
            print(f"{line}  /sdlc:release" if due.get("due") else f"{line}  {_not_due(due, a)}")
        # Warned about, never a problem: an overdue shim mustn't fail every change's gate.
        for kind, state in SHIM_STATES.items():
            for s in shims.get(kind, []):
                print(f"    ⚠  shim {s['name']}{state}: remove in {s['remove_in']} ({s['where']})")
        for c in rel["changes"]:
            landed = "" if c["closed"] else "  (landed, not closed)"
            print(f"    {c['id']}  {c['slug']:<28} {c['impact'] or '?'}{landed}")

    # Left out with no bug open, as Unreleased is with nothing landed.
    bugs = a.get("bugs")
    if bugs and bugs["open"]:
        counts = ", ".join(f"{k} {n}" for k, n in bugs["by_severity"].items())
        oldest = f", oldest {bugs['oldest_days']}d" if bugs["oldest_days"] is not None else ""
        print(f"\n■ Bugs: {bugs['open']} open ({counts}){oldest}  → /sdlc:bug")

    # Left out when the registers hold nothing to put forward, as Unreleased is.
    nxt = a.get("next_up")
    if nxt and (nxt["items"] or nxt["themes"] or nxt["done_milestones"] or nxt["warnings"]):
        print(f"\n■ Next up: {len(nxt['items'])}")

        def line(item: dict, indent: str) -> str:
            age = f"{item['age_days']}d" if item["age_days"] is not None else "?"
            # A nits line names its theme in its title already.
            theme = f"[{item['theme']}] " if item["theme"] and item["rule"] != "nits" else ""
            return f"{indent}{item['label']}  {theme}{item['title']}  ({age})  → {item['command']}"

        if a.get("all"):
            for group in nxt["all"]:
                print(f"    {group['theme']}")
                for item in group["items"]:
                    print(line({**item, "theme": None}, "      "))
                if group.get("command"):
                    print(f"      → {group['command']}  (its ideas as one change)")
        else:
            # What's ready to build first, then what needs the person's decision, sharing one cap.
            ready = [i for i in nxt["items"] if i.get("group") == "ready"]
            decide = [i for i in nxt["items"] if i.get("group") != "ready"]
            shown = (ready + decide)[:NEXT_SHOWN]
            low = sum(1 for i in decide if i["rule"] == "low")
            print(f"    Ready to build: {len(ready)}")
            for item in shown[: len(ready)]:
                print(line(item, "      "))
            print(f"    Needs a decision: {len(decide)}" + (f" ({low} low)" if low else ""))
            for item in shown[len(ready) :]:
                print(line(item, "      "))
            if len(nxt["items"]) > NEXT_SHOWN:
                print(f"    (+{len(nxt['items']) - NEXT_SHOWN} more: status --all)")
            if nxt["themes"]:
                print("    Themes:")
            for t in nxt["themes"]:
                total = sum(t["counts"].values())
                kinds = ", ".join(
                    f"{n} {k}s" if n > 1 else f"{n} {k}"
                    for k in ("bug", "idea", "nit")
                    if (n := t["counts"].get(k))
                )
                age = f", oldest {t['age_days']}d" if t["age_days"] is not None else ""
                print(f"      {t['theme']}  {total} ({kinds}){age}")
        if nxt["waiting"]:
            print(f"    {nxt['waiting']} waiting on earlier seeds")
        if nxt["building"]:
            print(f"    {len(nxt['building'])} being built")
        if a.get("all"):
            for b in nxt["building"]:
                by = b["change"] or "tagged [building]"
                print(f"      {b['id']} {b['title']} — {by}")
        if nxt["themeless"] >= THEMELESS_NUDGE:
            n = nxt["themeless"]
            print(f"    {n} ideas and bugs have no theme: /sdlc:idea --themes proposes them")
        for m in nxt["done_milestones"]:
            print(f"    {m} has nothing left in its groups: /sdlc:retro decides whether it's done")
        for w in nxt["warnings"]:
            print(f"    ⚠  {w}")

    # Nudges, not gates: one line each, only when it applies, and nothing runs. Never a problem:
    # `check --strict` is a gate, and a plugin update mustn't fail every host's.
    if a.get("setup"):
        print(f"\n■ Setup: {a['setup']}")
    if up := a.get("unpushed"):
        print(f"\n■ Unpushed: {unpushed_line(up)}  /sdlc:publish")
    if nudge := a.get("cases_nudge"):
        print(f"\n■ Skill evals: {nudge}")
    rdue = (rel or {}).get("due")
    if rdue and rdue["due"]:
        print(f"\n■ Release due: {'; '.join(rdue['why'])}  /sdlc:release")
    due = a.get("retro_due")
    if due and due["due"]:
        print(f"\n■ Retro due: {'; '.join(due['why'])}  /sdlc:retro")

    print(f"\n■ Problems: {len(a['problems'])}")
    if not a["problems"]:
        print("    none ✅")
    for pr in a["problems"]:
        print(f"    ⚠  {pr['dir']}: {pr['detail']}")

    # Last, so the answer to "what needs me?" is the line the eye ends on: the board's sixth state.
    recs, closing = states["needs-you"]
    print(f"\n■ Needs you: {len(recs) + len(closing)}")
    if not recs and not closing:
        print("    nothing")
    indent = " " * 30
    for rec in recs + closing:
        lines = _change_lines(rec, a) if rec in recs else [_close_line(rec, a)]
        for line in lines:
            print(line)
        needs = ", ".join(rec.get("needs") or []) or f"stage {rec.get('stage') or '?'}"
        step = decide_step(rec)
        print(f"{indent}needs you: {needs}" + (f"  {step}" if step else ""))
    if tildes and tildes[-1] == "needs-you":
        print(STATUS_TILDE)


@command(
    "status",
    "what's open, at what stage (the default)",
    arg("--all", action="store_true", help="every candidate in Next up, grouped by theme"),
)
def cli_status(root: Path, home: Path, args) -> int:
    a = analyze(root)
    a["ready"] = ready_to_close(root) + held_by_rebase(home)
    # Unconfigured, status shows only a count, so the intents behind it aren't read.
    cfg = load_config(home)[0]
    a["trunk"] = cfg["git"]["base"]
    # A problem here, not in `analyze()`: every change refuses to start without a base branch,
    # but `check` is a gate, and a repo whose `main` has no commit yet has none to name.
    if not a["trunk"]:
        a["problems"].append({"dir": "git.base", "detail": trunk_refusal(home, None)})
    # Here, not in `analyze()`: a stale base is a nudge, and `check` is a gate.
    for rec in a["open"] + a["ready"]:
        rec["behind"] = behind_trunk(home, f"{rec['id']}-{rec['slug']}", a["trunk"])
    now = datetime.now(UTC).timestamp()
    for rec in a["open"]:
        touched = last_touched(root, rec, a["trunk"])
        rec["touched_ago"] = None if touched is None else now - touched
        rec["quiet"] = touched is None or now - touched > QUIET_HOURS * 3600
        # A factory run its supervisor recorded as stopped waits on the person, never quiet.
        rec["stopped"] = (
            factory_records.read_stop(Path(root, rec["dir"])) if rec["stage"] == "build" else None
        )
        # A gate run by hand (`gate`) says whether the build as it stands is green; a factory
        # run's gate is its own while it builds, and at `test` the hand gate clears a `gate` reason.
        folder = Path(root, rec["dir"])
        hand = not (folder / "runs").is_dir() or rec["stage"] == "test"
        rec["gate"] = hand_gate(folder, home, a["trunk"]) if hand else None
        # What it needs from the person, by the rules the board reads (`needs_of()`); a factory
        # run's decision and ledger only where it ran, and nothing but the two answers kept.
        seen = factory_records.reading(folder) if (folder / "runs").is_dir() else {"problems": []}
        reading = rec | seen | {
            "problems": rec["errors"] + seen["problems"],
            "spec_filled": "spec.md" in rec["artifacts"] and "spec.md" not in rec["unfilled"],
            # A landing stopped before its commit; one stopped after is in the ready list.
            "land_stop": factory_records.read_land_stop(folder) if rec["stage"] == "test" else None,
            "mode": "factory" if (folder / "runs").is_dir() else "manual",
            "change": f"{rec['id']}-{rec['slug']}",
        }  # fmt: skip
        # A landing in flight, and a record that won't read, as the board reads them.
        reading["in_flight"], problem = factory_records.landing(folder, rec["stage"])
        reading["problems"] += [problem] if problem else []
        rec["needs"], rec["answered"] = needs_of(reading), answered(reading)
        # Its board column, by the one rule: how far a change built by hand has got, too.
        reading["needs"] = rec["needs"]
        reading["seen"] = seen_stage(reading, folder, home, a["trunk"])
        rec["column"] = column(reading)
    for rec in a["ready"]:
        # A shipped change whose landing stopped waits on the person, as on the board. At
        # `shipped`, `needs_of()` reads only `problems` and `land_stop`: a field it comes to read
        # there must be added to this `reading` too.
        folder = work_dir(Path(rec["worktree"])) / rec["branch"]
        reading = {
            "stage": rec["kind"],
            "problems": [],
            "land_stop": factory_records.read_land_stop(folder),
        }
        rec["needs"] = needs_of(reading)
        rec["column"] = column(reading | {"needs": rec["needs"], "mode": None})
    a["all"] = getattr(args, "all", False)
    open_ids = [f"{r['id']}-{r['slug']}" for r in a["open"]]
    a["release"] = unreleased(home, cfg, open_ids, read=bool(cfg["release"]["version_files"]))
    rel_cfg = cfg["release"]
    a["release_due_after"] = (rel_cfg["due_after_changes"], rel_cfg["due_after_days"])
    a["retro_due"] = retro_due(home, cfg)
    a["unpushed"] = _nudge(home, cfg)
    a["cases_nudge"] = cases_nudge(_cases_report(home, None))
    # Here, not in `analyze()`: `check` never reads the registers for what comes next.
    a["next_up"] = next_up(home, cfg, a["open"], date.fromisoformat(a["today"]))
    words = severities(home, cfg)
    fixing = {f for r in a["open"] for f in r.get("fixes") or []}
    bugs = [b for b in bug_entries(home, words)[0] if b["id"] not in fixing]
    a["bugs"] = bugs_summary(bugs, words, date.fromisoformat(a["today"]))
    a["setup"] = setup_nudge(root)
    print_status(a)
    return 0


@command(
    "check",
    "audit artifacts against declared tier/stage",
    arg("--strict", action="store_true", help="exit 1 if any problem is found"),
)
def cli_check(root: Path, home: Path, args) -> int:
    a = analyze(root)
    print(f"■ Problems: {len(a['problems'])}")
    for pr in a["problems"]:
        print(f"    ⚠  {pr['dir']}: {pr['detail']}")
    if not a["problems"]:
        print("    none ✅")
    return 1 if (args.strict and a["problems"]) else 0


def main() -> int:
    _utf8_streams()
    ap = _parser(
        "Track the change artifacts under .sdlc/work/ (see the repo's process doc).", False
    )
    # Before parsing: the change's own script may take a flag this copy doesn't know.
    if len(sys.argv) > 1 and sys.argv[1] in OWN_SCRIPT_CMDS and (own := _own_script(repo_root())):
        code = _run_own(own, sys.argv[1:])
        if code is not None:
            return code
    args = ap.parse_args()
    root = repo_root()
    # State, the lock and the worktree list belong to the main checkout; change folders are found
    # from here in every checkout (`change_dirs`). `config` reads this checkout's .sdlc/, which a
    # change's branch may be editing.
    home = main_root(root)
    run = COMMANDS[args.cmd].run if args.cmd else cli_status
    try:
        return run(root, home, args)
    except UsageError as e:
        ap.error(str(e))


if __name__ == "__main__":
    raise SystemExit(main())
