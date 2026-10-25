#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-frontmatter>=1.1", "PyYAML>=6.0"]
# ///
"""sdlc — the mechanical half of the change process in the host repo's process doc.

Every non-trivial change to a repo using this plugin gets a numbered folder under `work/` holding
its artifacts: `intent.md` always, plus `spec.md` and `plan.md` when the change is Tier 2. That
convention is only worth having if something checks it, because the failure mode is silent — an
intent stuck at `stage: build` for three weeks, or a Tier 2 change that quietly never got a spec,
looks exactly like a repo with nothing open.

`work/` is committed. A change's folder lives on its own branch, in its own worktree
(`.claude/worktrees/NNN-slug`), so a session there writes its artifacts where it works and the
review reads them in the diff. Close lands the branch, mirrors the folder to the tracker, and
removes it from `main` in a commit of its own: history is the copy. The folders this tool reads are
the checkout's own `work/` and each change worktree's folder (`change_dirs`).

So this tool answers the questions that are queries rather than decisions:

    status      every open change, in any worktree: its tier and stage, its age, which artifacts
                exist
    new         claim the next id, make the change's worktree and branch (--worktree), and scaffold
                its folder there from the host's .sdlc/templates/, or this plugin's templates/
                where the host has none
    check       artifacts missing for the declared tier/stage; frontmatter that won't parse;
                work/inbox.md entries tagged [building] with no change behind them
    ship        stamp stage: shipped + today's date, in place
                (refused while notes.md has an unticked `- [ ]` item)
    drop        stamp stage: dropped and how far it got, in place, and commit the change's folder
                on its branch (refused without a `## Dropped` reason)
    close       land a shipped change on main, measure what it cost from this repo's session
                transcripts (scripts/metrics.py), mirror it to the tracker, remove its folder in a
                commit carrying the numbers as Sdlc-* trailers, then its worktree and branch; a
                dropped one is measured too and gets a `Drop` commit instead
    sync        rewrite the change's tracker issue from its artifacts as they are now (the
                trackers are modules in scripts/trackers/; `archive.target = "none"` loads none)
    lookup      the values the project doc's issue fields can take (milestone, project,
                assignees), from the tracker, a host command or a fixed list, as JSON
    next-entry  the id the next work/inbox.md entry would take today, or --count N of them
    undone      a change's unticked `- [ ]` items in notes.md, as JSON
    readiness   whether this repo is set up for the plugin, item by item, with the commands its own
                task files suggest for the gate, the slower check and the scans, as JSON
    context     the docs that give a session its context and that this diff could have made
                wrong, with their lines naming a path it deletes or renames, as JSON
    config      the host's settings from .sdlc/config.toml, every path resolved, as JSON
    unreleased  the changes landed on main since the current version's tag, read from history,
                with their impacts and the version they add up to, as JSON
    release     bump the version files, commit `Release X.Y.Z` and tag it, locally
    publish     push main and the release tag, then run the host's publish command: the one
                command that sends anything anywhere
    retro       what the retrospective counts rather than judges: the changes closed since the
                last `Retrospective` commit, open changes, seeds, tiers, impacts, releases, rework
                and the size of each skill, as JSON
    retro-commit  record a retrospective: commit the direction doc and work/inbox.md, and nothing
                else, as `Retrospective YYYY-MM-DD`

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
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import tomllib
import unicodedata
from collections import Counter
from datetime import UTC, date, datetime
from datetime import time as dtime
from pathlib import Path

import frontmatter

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
UNFILLED_THRESHOLD = 2
# work/inbox.md, the register of change requests: "## [2026-10-25-3] [seed] Some title", its id
# (the date it came in and a count) then its tag. A bare date, `[2026-10-17]`, is an entry from
# before ids, read the same with no id.
ENTRY_RE = re.compile(r"^##\s*\[(\d{4}-\d{2}-\d{2})(?:-(\d+))?\]\s*\[([^\]]+)\]\s*(.+)$")
# The facts an entry holds as body lines, `Key: value`, read as text, the first of each kept. A
# seed that waits on others has `After: "Some title", "Another"`, the titles quoted as a
# milestone's `Groups:` line has them, and status holds it back while one is still open; the rest
# are a bug's or a nit's own.
BODY_KEYS = ("After", "Severity", "Paths", "Introduced by", "Theme", "Cost", "Value", "Raised by")
BODY_RE = re.compile(rf"^({'|'.join(BODY_KEYS)}):\s*(.+)$")
# A reference to an entry, on an `idea:`, `fixes:`, `After:` or `Groups:` line, is its id, written
# bare, or its title, quoted. Titles are read for good: the intents in history name seeds by them.
ENTRY_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d+$")
ENTRY_ID_TOKEN_RE = re.compile(r"(?<![\w-])\d{4}-\d{2}-\d{2}-\d+(?![\w-])")
REF_RE = re.compile(rf'"([^"]+)"|({ENTRY_ID_TOKEN_RE.pattern})')
# A nit is a `[nit]` entry: a finding ship approved unfixed, with `Theme:`, `Paths:`, `Cost:`,
# `Value:` and `Raised by: NNN-slug (pass)` lines. Ship writes and retires them, intent and spec
# offer them, retro counts them; the process doc's rubric says what each cost and value means. High
# value is never a nit, and L cost is a seed, so neither appears here.
NIT_RAISED_RE = re.compile(r"^(\d{3,}-[a-z0-9][a-z0-9-]*)\s*(?:\(([^)]*)\))?\s*$")
NIT_COSTS = ("S", "M")
NIT_VALUES = ("med", "low")
# notes.md is free-form, with one rule: anything left undone is an unticked `- [ ]` line.
# /sdlc:ship carries each one to a work/inbox.md seed or drops it with a reason, ticking it as it
# goes, and `ship` refuses while one is still unticked, so nothing lands on main with a question
# nobody answered.
OPEN_ITEM_RE = re.compile(r"^\s*[-*] \[ \] (.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# The plugin's own files, resolved from this one so they are found whether the plugin is loaded in
# place or from the plugin cache. Its templates are a default: the section structure a stage owes,
# with prompts that assume nothing about what the host builds. A host that wants its own prompts
# puts a file of the same name in `.sdlc/templates/`, and that one wins (`template_path`).
PLUGIN_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = PLUGIN_DIR / "templates"
DEFAULTS_DIR = PLUGIN_DIR / "defaults"
# The register's name, and the one it had before: a shim until 2.0.0 (.sdlc/deprecations.toml).
# A repo with only the old file is read from it, and so is a host template under the old name.
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
        "worktree_setup": None,  # run from the main checkout after `new --worktree`; {worktree}
        "close_list": None,  # read-only: what a closed change left behind; {suffix}
        "close_cleanup": None,  # the human's command to remove it; {id}. Never run by a skill
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
        "remote": "origin",  # where /sdlc:publish pushes main and the tag
        "publish": None,  # run by /sdlc:publish after the push; {version}, {tag}
        # The shims the host keeps and the version that removes each, which release refuses to
        # cut while one is due. Off while the file doesn't exist.
        "deprecations": ".sdlc/deprecations.toml",
    },
    # When `status` says a retrospective is due. A major release always makes one due.
    "retro": {
        "after_releases": 2,  # release tags since the last retrospective; 0 turns the count off
        # Host commands printing what users did with the product, run by `retro` only while a
        # product doc exists, from the repo root. Counts and summaries, never personal data.
        "evidence": [],
    },
    # What /sdlc:close records about a change, as trailers on its Close commit (scripts/metrics.py).
    "metrics": {
        "transcripts": True,  # read this repo's Claude Code transcripts, for numbers only
        "idle_minutes": 30,  # a wait longer than this is the person away, not answering
        # The stops beyond a change's gates its person should expect: each change's target is the
        # gates its tier and way of running pass, plus this.
        "stop_allowance": 1,
    },
    # The branch every change starts from and lands on, which release tags and publish pushes.
    # Unset, it is `main` when there is one, else the branch `origin/HEAD` names (`_resolve_trunk`).
    "git": {
        "base": None,
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
# `work/inbox.md`, a change's `notes.md` and its `checks.md`.
DOC_TEMPLATES = ("direction.md", "issue.md", INBOX, "notes.md", "checks.md")
# The [docs] keys that hold a list of paths.
DOC_LISTS = ("read_before_design", "context")
# Every key, in any section, that holds a list of paths, or of commands, rather than a string.
COMMAND_LISTS = ("evidence",)
LIST_KEYS = (*DOC_LISTS, "version_files", *COMMAND_LISTS)
# Every key that holds a whole number, with its least value where that isn't 0.
INT_KEYS = ("after_releases", "idle_minutes", "stop_allowance")
INT_MIN = {"idle_minutes": 1}
# Every key that holds true or false.
BOOL_KEYS = ("transcripts",)


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
            elif key in BOOL_KEYS:
                if isinstance(value, bool):
                    cfg[section][key] = value
                else:
                    warnings.append(f"{section}.{key} must be true or false")
            elif isinstance(value, str):
                cfg[section][key] = value
            else:
                warnings.append(f"{section}.{key} must be a string")
    if cfg["archive"]["target"] not in ARCHIVE_TARGETS:
        warnings.append(f"archive.target must be one of {'|'.join(ARCHIVE_TARGETS)}")
    docs = data.get("docs")
    return _resolve_docs(root, cfg, set(docs) if isinstance(docs, dict) else set()), warnings, True


def _resolve_docs(root: Path, cfg: dict, chosen: set[str]) -> dict:
    """With no CLAUDE.md, the policy is an AGENTS.md if there is one, unless the host set
    `docs.policy` (`chosen`). Every reader takes `cfg["docs"]`, so this is the one place it is
    decided. The base branch is resolved here too, for the same reason (`_resolve_trunk`)."""
    agents_only = not (root / "CLAUDE.md").is_file() and (root / "AGENTS.md").is_file()
    if "policy" not in chosen and agents_only:
        cfg["docs"]["policy"] = "AGENTS.md"
    cfg["git"]["base"], cfg["git"]["base_source"] = _resolve_trunk(root, cfg["git"]["base"])
    return cfg


def _resolve_trunk(root: Path, given: str | None) -> tuple[str | None, str]:
    """The base branch and where it came from: `git.base` as set (`config`); else `main` when the
    repo has one, else the local branch `origin/HEAD` names (`detected`); else (None, `unset`).
    Never the checkout's current branch or `init.defaultBranch`, which describe one machine, and
    never GitHub's default branch, which would be a network call from core."""
    if given:
        return given, "config"
    if _git(root, "rev-parse", "--verify", "-q", f"refs/heads/{DEFAULT_TRUNK}") is not None:
        return DEFAULT_TRUNK, "detected"
    remote = _git(root, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD") or ""
    name = remote.removeprefix("origin/")
    named = remote.startswith("origin/") and name
    if named and _git(root, "rev-parse", "--verify", "-q", f"refs/heads/{name}") is not None:
        return name, "detected"
    return None, "unset"


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
    """The template `new` scaffolds `name` from: the host's, else the plugin's. A host's inbox
    template may still be under the register's old name."""
    host = root / HOST_DIR / "templates" / name
    old = root / HOST_DIR / "templates" / OLD_INBOX
    if name == INBOX and not host.is_file() and old.is_file():
        host = old
    return (host, "host") if host.is_file() else (TEMPLATE_DIR / name, "plugin")


def register_path(work: Path) -> Path:
    """The register in this `work/` folder: `inbox.md`, or `ideas.md` while a repo has only that.
    The one place that knows the old name, so every reader and writer agrees on the file."""
    inbox = work / INBOX
    return work / OLD_INBOX if not inbox.is_file() and (work / OLD_INBOX).is_file() else inbox


def doc_path(root: Path, key: str, rel: str) -> dict:
    """Where a host doc is, and whether it exists. Only the review has a plugin fallback: a ship
    with no review passes to work through isn't a ship, while a missing policy doc is a fact the
    skill should say out loud rather than paper over with a generic one."""
    if (root / rel).is_file():
        return {"path": rel, "exists": True, "source": "host"}
    if key == "review":
        return {"path": str(DEFAULTS_DIR / "REVIEW.md"), "exists": True, "source": "plugin"}
    return {"path": rel, "exists": False, "source": "host"}


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
        warnings.append(IGNORED)
    if not cfg["git"]["base"]:
        warnings.append(f"git.base: {trunk_refusal(home, None)}")
    cfg_file = root / HOST_DIR / "config.toml"
    out = {
        "config_file": f"{HOST_DIR}/config.toml" if cfg_file.is_file() else None,
        # This checkout's: a change's folder is committed on its branch, in its worktree.
        "work": {"dir": str(work_dir(root)), "ignored": ignored},
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
        "git": cfg["git"],
        "templates": templates,
        "warnings": warnings,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if parsed else 1


def repo_root() -> Path:
    """The git repo containing the current directory.

    `git rev-parse` rather than walking up looking for a marker file: the host repo decides its own
    layout, and this plugin shouldn't assert that some file must exist at the root to be found.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
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
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip()


def main_root(root: Path) -> Path:
    """The main checkout, whichever worktree `root` is. Its git dir is the common one, so the
    parent of `--git-common-dir` is the same answer from the main checkout and from every
    worktree. Falls back to `root` outside git."""
    out = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(out).parent if out else root


IGNORED = (
    "work/ is gitignored: remove the `work/` line from .gitignore. A change's artifacts are "
    "committed on its branch, and `git add` skips an ignored folder"
)


def work_ignored(home: Path) -> bool | None:
    """Whether git ignores `work/` here; None outside git. `work/` with the slash, because
    `check-ignore` only matches a `work/` pattern against a path it is told is a directory, and
    the folder needn't exist yet."""
    try:
        code = subprocess.run(
            ["git", "-C", str(home), "check-ignore", "-q", "work/"], capture_output=True
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


def work_dir(root: Path) -> Path:
    return root / "work"


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
# committed, so a fresh clone carries on from it, and deleting work/ (which close does to a
# change's folder once it is archived) can't reset the numbering. `new --worktree` writes it in the
# change's own worktree, so the bump reaches main with the change's commit: the main checkout is
# never left dirty, which close would refuse.
LAST_ID = "last-id"


def last_id_path(home: Path) -> Path:
    return state_path(home, LAST_ID)


def change_dirs(root: Path) -> list[Path]:
    """Every change folder this checkout can see: its own `work/`, the main checkout's, and each
    change worktree's own folder, `work/<branch>/`. Only that one from a worktree: it also holds
    whatever `main` had when it was made, and those copies would read as the same change twice. A
    name found twice counts once, the copy on its own branch winning. Skips non-conforming names."""
    found: dict[str, Path] = {}
    for base in (work_dir(main_root(root)), work_dir(root)):
        if base.is_dir():
            found |= {p.name: p for p in base.iterdir() if p.is_dir() and DIR_RE.match(p.name)}
    for tree, branch in worktrees(root):
        own = work_dir(tree) / branch
        if DIR_RE.match(branch) and own.is_dir():
            found[branch] = own
    # By number, not by name: "1203-x" sorts before "142-y" as text.
    return sorted(found.values(), key=lambda p: (_number(p.name), p.name))


def _shown(path: Path, root: Path) -> str:
    """`path` relative to `root` when it is inside it, else absolute: a sibling worktree's."""
    try:
        return str(path.relative_to(root))
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
        "impact": "",
        "artifacts": sorted(p.name for p in path.glob("*.md")),
        "open_questions": 0,
        "depends_on": [],
        "fields": {},
        "serves": None,
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

    rec["idea"] = intent_idea(intent.read_text(encoding="utf-8"))
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
        checkout = path.parent.parent
        product = product_doc(checkout, load_config(checkout)[0])
    rec["serves"] = frontmatter_list(text, "serves")
    rec["errors"] += serves_errors(rec["serves"], product, rec["stage"])
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


def _age_days(rec: dict, today: date) -> int | None:
    try:
        return (today - date.fromisoformat(rec["created"])).days
    except ValueError:
        return None


def inbox_entries(root: Path) -> list[dict]:
    """Every entry in the register (`register_path()`): its id (None for a bare date), its tag as
    written (`status`), its title, the titles its `After:` line names, its body lines by key, and
    its other lines as `text`. A closed entry is deleted once its change ships; history keeps it.
    Fenced lines are skipped, so a template's example is never an entry. A file that can't be read
    holds none: `nit_entries()` says why."""
    path = register_path(work_dir(root))
    try:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return []
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
    by_id = {e["id"]: e["title"] for e in out if e["id"]}
    for e in out:
        e["after"] = [by_id.get(r, r) for r in e["after"]]
    return out


def _heading_entry(line: str) -> dict | None:
    """An entry's id (None for a bare date), date, tag as written (`status`) and title, from its
    heading line; None for any other line."""
    m = ENTRY_RE.match(line)
    if not m:
        return None
    return {"id": f"{m.group(1)}-{m.group(2)}" if m.group(2) else None, "date": m.group(1),
            "status": m.group(3), "title": m.group(4).strip()}  # fmt: skip


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


def intent_idea(text: str) -> str:
    """The `idea:` an intent names, read as text, so an id is never a date; "" when it has none."""
    return (frontmatter_list(text, "idea") or [""])[0]


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
        name = e["id"] or e["title"]
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
        if not e["id"]:
            problems.append(f"{name!r} has no id: its heading is `## [YYYY-MM-DD-n] [nit] title`")
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
    """Work has started: the seed is tagged `[building]`."""
    return "building" in idea["status"].lower()


def is_nit(entry: dict) -> bool:
    """A finding ship approved unfixed, `[nit]`: put forward by theme, never as a seed."""
    return entry["status"].strip().lower() == "nit"


def analyze(root: Path, today: date | None = None) -> dict:
    today = today or date.today()
    cfg = load_config(root)[0]
    project = project_doc(root, cfg)[0]
    # Each change against the product doc on its own branch: one opened before the doc landed
    # owes no `serves:` line until it rebases onto a main that has it.
    products: dict[Path, dict | None] = {}
    changes = []
    for p in change_dirs(root):
        checkout = p.parent.parent
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
            elif is_unfilled(folder / name):
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
    register = f"work/{register_path(work_dir(root)).name}"
    if (work_dir(root) / INBOX).is_file() and (work_dir(root) / OLD_INBOX).is_file():
        problems.append(
            {
                "dir": f"work/{OLD_INBOX}",
                "kind": "register",
                "detail": f"work/{INBOX} is the register, so this file is never read: move its "
                "entries there and delete it",
            }
        )
    for entry_id, n in Counter(e["id"] for e in entries if e["id"]).items():
        if n > 1:
            problems.append(
                {"dir": register, "kind": "entry id", "detail": f"{entry_id} is used {n} times"}
            )
    # The explicit link: /sdlc:intent writes the seed's id into `idea:`, older intents its title or
    # the whole heading, with the status tag it had at promotion (`[seed]`) while the register moved
    # on to `[building]`, so a title is matched alone. A dropped change is building nothing and
    # can't vouch for a seed.
    linked = [rec["idea"] for rec in changes if rec["idea"] and rec["stage"] != "dropped"]
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
                    "detail": f"[{idea['status']}] {idea['title']} — no work/ folder",
                }
            )
    for detail in nit_entries(root)[1]:
        problems.append({"dir": register, "kind": "nits", "detail": detail})
    if work_ignored(root):
        problems.append({"dir": "work/", "kind": "ignored", "detail": IGNORED})
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
    Only when the counter is missing does history count, to seed it: with work/ empty, numbering
    from 001 would collide with every change already closed."""
    last = read_last_id(home)
    seeds = [last or 0, _highest(home), _worktree_highest(home)]
    if last is None:
        seeds.append(_history_highest(home))
    return f"{max(seeds) + 1:03d}"


def next_entry_ids(home: Path, day: str, count: int = 1) -> list[str]:
    """The next `count` register ids for entries dated `day` (`YYYY-MM-DD-n`): one past the highest
    `n` that day in the register of every checkout of the repo, uncommitted edits included, and in
    every commit on any branch that ever added or removed one, so an id deleted since is never
    handed out again. A space of its own: never a change number, never the tracker's."""
    heading = re.compile(rf"^[+-]?##\s*\[{re.escape(day)}-(\d+)\]")
    texts = []
    for checkout in dict.fromkeys([main_root(home), *(p for p, _ in worktrees(home))]):
        for name in (INBOX, OLD_INBOX):
            try:
                texts.append((work_dir(checkout) / name).read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
    paths = [f"work/{INBOX}", f"work/{OLD_INBOX}"]
    log = _git(home, "log", "--all", "-p", "--format=", "-G", rf"\[{day}-", "--", *paths)
    texts.append(log or "")
    used = [int(m.group(1)) for t in texts for line in t.splitlines() if (m := heading.match(line))]
    top = max(used, default=0)
    return [f"{day}-{top + k}" for k in range(1, count + 1)]


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
        text=True,
    )
    return (tree, None) if made.returncode == 0 else (None, made.stderr.strip())


def claim(
    home: Path, slug: str, where: Path | None = None, base: str | None = None
) -> tuple[Path | None, Path | None, str | None]:
    """Take the next number and make the change: (folder, worktree, None), or (None, None, why).

    With `base`, the change gets its worktree and branch from it, and its folder inside; without,
    its folder goes in `where`'s `work/` (the main checkout's by default). Under an exclusive lock
    on the main checkout's `.sdlc/`, which every worktree shares: a `mkdir` alone isn't one, since
    two sessions that read the same id for different slugs would both get it. What is made under
    the lock (the worktree's branch, or the folder) is what the next claim counts, so the counter
    can be written after the lock is released."""
    lock = state_path(home, LAST_ID).parent
    lock.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
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
    finally:
        os.close(fd)  # and with it the lock


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
        print(f"⚠  {IGNORED}", file=sys.stderr)
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
        print(f"  created  worktree {tree}  (branch {name}, from {base})")

    # The counter goes where the change will commit it, next to its folder: its worktree, or the
    # checkout `new` ran in.
    if mode == "local":
        _write_state(tree or here, LAST_ID, f"{nid}\n")

    heading = title or slug.replace("-", " ")
    stamp = date.today().isoformat()
    for artifact in wanted:
        source, origin = template_path(home, artifact)
        text = source.read_text(encoding="utf-8")
        text = (
            text.replace("NNN", nid)
            .replace("SLUG", slug)
            .replace("YYYY-MM-DD", stamp)
            .replace("TITLE", heading)
        )
        if artifact == "intent.md":
            text = text.replace("tier: 1", f"tier: {tier}", 1)
        (dest / artifact).write_text(text, encoding="utf-8")
        print(f"  created  {dest / artifact}  ({origin} template)")

    print(f"\n■ {name} — tier {tier}, stage: plan")
    print(
        f"    next: fill in {dest}/intent.md "
        f"({'Problem → Outcome → Approach' if tier == 1 else 'Problem → Outcome, then /sdlc:spec'})"
    )
    return 0


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
    hand-authored, hand-ordered prose; this is the Edit-not-Write rule applied to `work/`.

    Returns the new text plus the keys it could not place, so a pattern that matches nothing is
    reported instead of written past.
    """
    return _stamp(text, {"stage": "shipped", "updated": stamp, "shipped": stamp}, "shipped")


def stamp_dropped(text: str, stamp: str, reached: str) -> tuple[str, list[str]]:
    """Set `stage: dropped`, `updated:` and `dropped_at:` (the stage it got to) in place, by
    `stamp_shipped`'s rule."""
    return _stamp(text, {"stage": "dropped", "updated": stamp, "dropped_at": reached}, "dropped_at")


def _stamp(text: str, wanted: dict[str, str], new_key: str) -> tuple[str, list[str]]:
    """Each `wanted` frontmatter line rewritten in place; `new_key`, the one a first stamp adds,
    anchored under `updated:`. The new text and the keys it couldn't place."""
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
    print(json.dumps({"change": path.name, **report}, indent=2, ensure_ascii=False))
    return 1 if report.get("error") else 0


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
            ran = subprocess.run(
                field["command"].replace("{field}", name),
                shell=True, cwd=home, capture_output=True, text=True,
            )  # fmt: skip
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


def cmd_undone(root: Path, ident: str) -> int:
    """A change's undone notes.md items as JSON, for /sdlc:ship's Step 0. Writes nothing."""
    path = _one_change(root, ident)
    if path is None:
        return 1
    items = open_items(path)
    print(
        json.dumps(
            {
                "change": path.name,
                "notes": _shown(path / "notes.md", root),
                "items": [{"line": i["line"], "text": i["text"]} for i in items],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_nits(root: Path, touching: list[str] | None, change: str | None) -> int:
    """The open nits, the register's `[nit]` entries, as JSON, with their age, for intent and
    spec to offer and ship to retire. `--change` keeps those a change's diff against the base
    branch touches, `--touching` those the given paths do. Writes nothing."""
    nits, problems = nit_entries(root)
    paths = list(touching or [])
    if change:
        path = _one_change(root, change)
        if path is None:
            return 1
        trunk = load_config(main_root(root))[0]["git"]["base"]
        found = changed_paths(path.parent.parent, trunk) if trunk else None
        if found is None:
            print(f"⚠  no merge base with {trunk!r}: is this a git checkout?", file=sys.stderr)
            return 1
        paths += [p for _, path_, to in found[1] for p in (path_, to) if p]
    if change or touching is not None:
        nits = [n for n in nits if nit_touches(n, paths)]
    today = date.today()
    for n in nits:
        n["age_days"] = _age_days({"created": n["raised"] or ""}, today)
    out = {"path": _shown(register_path(work_dir(root)), root), "nits": nits, "problems": problems}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if problems else 0


def cmd_checks(root: Path, ident: str) -> int:
    """A change's acceptance checks as JSON, for /sdlc:ship to show before it runs them. Runs
    nothing and writes nothing, so it is allowed without a prompt; `accept` is not."""
    path = _one_change(root, ident)
    if path is None:
        return 1
    found = acceptance(path)
    print(json.dumps({"change": path.name, **found}, indent=2, ensure_ascii=False))
    return 1 if found["problems"] else 0


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
    checkout = path.parent.parent
    results = []

    def text(out: str | bytes | None) -> str:
        # A timeout's partial output is bytes even with text=True.
        return out.decode("utf-8", "replace") if isinstance(out, bytes) else out or ""

    for check in found["checks"]:
        # Per check, so one that leaves the tree changed fails alone.
        before = _status_lines(checkout)
        start = datetime.now(UTC)
        try:
            run = subprocess.run(
                ["sh", "-c", check["command"]],
                cwd=checkout,
                capture_output=True,
                text=True,
                timeout=CHECK_TIMEOUT,
                stdin=subprocess.DEVNULL,
            )
            code, output = run.returncode, run.stdout + run.stderr
        except subprocess.TimeoutExpired as e:
            code = None
            output = f"{text(e.stdout)}{text(e.stderr)}\ntimed out after {CHECK_TIMEOUT}s"
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


def cmd_ship(root: Path, ident: str, leave: list[str] | tuple[str, ...] = ()) -> int:
    """Stamp a change shipped, delete the seed its `idea:` names from the register, and stage
    everything its checkout has uncommitted but `leave`, for /sdlc:ship to commit. Runs after
    ship's WAIT; every refusal comes before the first write, and a rerun is harmless. Never
    commits."""
    path = _one_change(root, ident)
    if path is None:
        return 1

    intent = path / "intent.md"
    if not intent.is_file():
        print(f"⚠  {path.name} has no intent.md — nothing to stamp", file=sys.stderr)
        return 1

    # An undone item that lands as-is is never read again. Shipping with a known gap is fine; with
    # an unanswered one it isn't. Refuse before stamping.
    undone = open_items(path)
    if undone:
        print(
            f"⚠  {path.name}/notes.md has {len(undone)} undone item(s):\n"
            + "".join(f"     notes.md:{i['line']}  {i['text']}\n" for i in undone)
            + "   Give each a disposition: tick it with `→ seed: <title>` after adding that seed "
            "to work/inbox.md, or `→ dropped: <reason>`. Then re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1

    # The release that carries this change proposes its bump from this line. Asked for
    # here, with the diff in front of someone, not reconstructed from commit subjects at release.
    try:
        post = frontmatter.load(intent)
        impact, idea = str(post.get("impact") or ""), intent_idea(intent.read_text("utf-8"))
    except Exception:  # malformed YAML: `check` reports it; ship refuses below like any other gap
        impact, idea = "", ""
    if impact not in IMPACTS:
        print(
            f"⚠  {path.name}/intent.md: impact must be one of {'|'.join(IMPACTS)}, got "
            f"{impact!r}. Say what this change does to someone holding the previous release "
            "(the process doc, Releases) and re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1

    ideas = register_path(path.parent)
    seeds = _seed_lines(ideas, idea)
    if len(seeds) > 1:
        print(
            f"⚠  work/{ideas.name} has {len(seeds)} entries named {entry_ref(idea)[1]!r} (lines "
            f"{', '.join(str(n + 1) for n in seeds)}): delete the one this change built by hand, "
            "or retitle one, and re-run. Not stamping.",
            file=sys.stderr,
        )
        return 1
    tree = Path(_git(path, "rev-parse", "--show-toplevel") or path.parent.parent)
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
    intent.write_text(stamped, encoding="utf-8")
    print(
        f"■ shipped {path.name}  (stage: shipped, {stamp}): commit {_shown(path, root)}/ with "
        "the change"
    )
    if seeds:
        _drop_seed(ideas, seeds[0])
        print(f"  removed seed {entry_ref(idea)[1]!r} from work/{ideas.name}")
    elif idea:
        print(f"  no seed to remove: work/{ideas.name} has no entry named {entry_ref(idea)[1]!r}")
    paths, err = _stage_change(tree, leave)
    if err:
        print(f"⚠  git add failed: {err}. Fix it and re-run ship.", file=sys.stderr)
        return 1
    for p in paths:
        print(f"  staged {p}")
    if not paths:
        print("  staged nothing: the checkout has nothing uncommitted")
    return 0


def _seed_title(text: str) -> str:
    """A seed's title from its heading, or from an `idea:` line holding the title or the heading,
    with or without its `## `: without the `[date] [tag]` prefix, or the ` → work/<folder>` pointer
    an older intent put in the heading. An arrow in the title itself stays."""
    text = text.strip()
    m = ENTRY_RE.match(text) or ENTRY_RE.match(f"## {text}")
    title = m.group(4) if m else text
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


def _drop_seed(ideas: Path, start: int) -> None:
    """Delete the entry whose heading is line `start`, through the line before the next `## ` (or
    the end), as lines, so every other entry stays byte for byte."""
    lines = ideas.read_text(encoding="utf-8").splitlines(keepends=True)
    end = next((n for n in range(start + 1, len(lines)) if lines[n].startswith("## ")), len(lines))
    before, after = lines[:start], lines[end:]
    if not after:  # the last entry: no blank line left trailing the one before it
        while before and not before[-1].strip():
            before.pop()
    ideas.write_text("".join(before + after), encoding="utf-8")


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
        text=True,
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
    name, rel = path.name, f"work/{path.name}"
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
        (path / "intent.md").write_text(stamped, encoding="utf-8")
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


def behind_trunk(main: Path, branch: str, trunk: str | None) -> int | None:
    """How many of the base branch's commits `branch` lacks; None when either isn't a local
    branch. 0 is close's precondition, the base an ancestor of the branch, so a fast-forward is
    possible. Status shows anything else, and ship stops on it, before the gate and the review run
    on a base that close would refuse."""
    if not trunk:
        return None
    out = _git(main, "rev-list", "--count", f"refs/heads/{branch}..refs/heads/{trunk}")
    return int(out) if out and out.isdigit() else None


def cmd_base(root: Path, ident: str | None) -> int:
    """Bring a change's branch up to date with the base branch (`git.base`) in its own worktree,
    or refuse, as JSON. /sdlc:ship runs it at Step 0, so the gate and the review see what close
    will fast-forward.

    The one write a skill makes before its WAIT, by a named exception (004's spec): it moves only
    the change's own local branch onto the base, only when nothing conflicts, and prints the
    command that undoes it. A branch with no commits of its own, the usual case at ship and always
    after a factory run, fast-forwards, and git carries the uncommitted work or refuses to
    overwrite it. One with commits rebases, from a clean tree only, and a conflict is aborted.
    Never a stash: the stack is shared with every worktree. Never a merge of the base into the
    branch: close would put it on the base's first-parent line, which `closed_changes()` walks."""
    trees = [(t, b) for t, b in worktrees(root) if DIR_RE.match(b)]
    if ident is None:
        here = _git(root, "branch", "--show-current") or ""
        ident = here if DIR_RE.match(here) else None
    found = [(t, b) for t, b in trees if names_change(b, ident)] if ident else []
    main = main_root(root)
    report: dict = {"change": ident, "branch": None, "behind": None, "action": "current",
                    "from": None, "to": None, "undo": None, "reason": None}  # fmt: skip

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

    def refuse(reason: str) -> int:
        report.update(action="refused", reason=reason, to=_git(tree, "rev-parse", "HEAD"))
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
                "commit the work, then run /sdlc:ship again"
            )
        err = _git_err(tree, "rebase", "-q", trunk)
        if err:
            _git_err(tree, "rebase", "--abort")
            return refuse(f"rebasing onto {trunk} conflicts, so it was aborted: {err}")
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
                counter.write_text(kept, encoding="utf-8")
            return refuse(f"{trunk} changed what this change's uncommitted work changes: {err}")
        ours = int(kept.strip()) if kept is not None and kept.strip().isdigit() else 0
        if kept is not None and (_read_number(counter) or 0) < ours:
            _write_state(tree, LAST_ID, kept)
        report["action"] = "fast-forwarded"
    report.update(to=_git(tree, "rev-parse", "HEAD"), undo=f"git -C {tree} reset --keep {before}")
    return emit(0)


def _close_times(main: Path, trunk: str) -> dict[str, datetime]:
    """When each change's `Close` commit landed on the base branch, by the change's name."""
    log = _git(main, "log", "--first-parent", "--format=%cI%x00%s", trunk) or ""
    found = {}
    for line in log.splitlines():
        when, _, subject = line.partition("\x00")
        name = subject[len(CLOSE_PREFIX) :].strip() if subject.startswith(CLOSE_PREFIX) else ""
        if DIR_RE.match(name):
            found[name] = datetime.fromisoformat(when)
    return found


# The factory's file formats, copied from `plugins/factory/scripts/factory.py` (never imported or
# run: the factory is optional), and pinned to its copies by `tests/test_metrics.py`.
FACTORY_VERDICT_RE = re.compile(r"^VERDICT: (PASS|CHANGES)\s*$")
FACTORY_DECISION_RE = re.compile(r"^DECISION: (READY|ESCALATE)\s*$")
FACTORY_CHANGE_RE = re.compile(r"^\s*- CHANGE:\s*(.+?)\s*$")
FACTORY_LEDGER_RE = re.compile(r"^- \[( |x)\] (D\d+) \(([^,)]+), (blocking|default)\): (.+?)\s*$")


def _factory_files(main: Path, branch: str) -> dict | None:
    """What the factory left in the change's commit, as counts: review rounds, each reviewer's
    `CHANGES` verdicts and change requests, the approver's decision, and the ledger's blocking
    and default decisions. None for a change built by hand (no `decision.md`)."""
    folder = f"work/{branch}"
    decision = _git(main, "show", f"{branch}:{folder}/decision.md")
    if decision is None:
        return None
    first = decision.splitlines()[0] if decision else ""
    m = FACTORY_DECISION_RE.match(first)
    listed = _git(main, "ls-tree", "-r", "--name-only", branch, f"{folder}/reviews") or ""
    rounds: set[str] = set()
    reviews: dict[str, dict] = {}
    for path in listed.splitlines():
        parts = path[len(folder) + 1 :].split("/")  # reviews, round-N, role.md
        if len(parts) != 3 or not parts[1].startswith("round-") or not parts[2].endswith(".md"):
            continue
        rounds.add(parts[1])
        lines = (_git(main, "show", f"{branch}:{path}") or "").splitlines()
        verdict = FACTORY_VERDICT_RE.match(lines[0]) if lines else None
        r = reviews.setdefault(parts[2].removesuffix(".md"), {"changes": 0, "requests": 0})
        r["changes"] += int(bool(verdict) and verdict.group(1) == "CHANGES")
        r["requests"] += sum(1 for line in lines[1:] if FACTORY_CHANGE_RE.match(line))
    ledger = _git(main, "show", f"{branch}:{folder}/decisions.md") or ""
    entries = [e for e in map(FACTORY_LEDGER_RE.match, ledger.splitlines()) if e]
    defaults = [e for e in entries if e.group(4) == "default"]
    return {
        "rounds": len(rounds),
        "reviews": reviews,
        "decision": m.group(1) if m else None,
        "blocking": sum(1 for e in entries if e.group(4) == "blocking"),
        "defaults": len(defaults),
        "defaults_open": sum(1 for e in defaults if e.group(1) == " "),
    }


def _change_base(main: Path, branch: str, rev: str | None = None) -> str | None:
    """Where a change starts: the parent of the commit that first holds its intent (ship's, since
    nothing commits before ship), so the answer is the same before close fast-forwards `main` and
    after, and on a rerun. `rev` is the change's own commit once its branch is gone, as retro
    reads it. None when no commit holds it."""
    added = _git(
        main, "log", "--diff-filter=A", "--format=%H", "--reverse", rev or branch, "--",
        f"work/{branch}/intent.md",
    )  # fmt: skip
    if not added:
        return None
    return _git(main, "rev-parse", "--verify", "-q", f"{added.split()[0]}^")


def _change_diff(main: Path, branch: str) -> int | None:
    """Lines added to code and tests by the change, from `_change_base()` to the branch's tip.
    Files are named by `metrics.artifact`, as the edits were; the plugin's own state in `.sdlc/`
    (the counter `new` writes in the change's worktree) is nobody's code."""
    base = _change_base(main, branch)
    numstat = _git(main, "diff", "--numstat", "--no-renames", base, branch) if base else None
    if numstat is None:
        return None
    total = 0
    for row in numstat.splitlines():
        plus, _, rest = row.partition("\t")
        path = rest.partition("\t")[2]
        if path.startswith(".sdlc/"):
            continue
        if plus.isdigit() and metrics.artifact(path, branch) in ("code", "test"):
            total += int(plus)
    return total


def measure_change(main: Path, branch: str, cfg: dict) -> tuple[dict, list[str]]:
    """What a change cost, as a summary and its `Sdlc-*` trailer lines: from this repo's
    transcripts when `metrics.transcripts` allows and they hold the change, else what history
    gives (elapsed since `created`, the way of running), saying why. Never raises: measuring
    must never stop a change landing."""
    settings = cfg["metrics"]
    text = _git(main, "show", f"{branch}:work/{branch}/intent.md") or ""
    decided = _git(main, "cat-file", "-e", f"{branch}:work/{branch}/decision.md")
    way = "factory" if decided is not None else "manual"
    try:
        post = frontmatter.loads(text)
        tier = int(post.get("tier") or 2)
        created = date.fromisoformat(str(post.get("created")))
    except Exception:
        tier, created = 2, None

    def finish(summary: dict, events: list[dict]) -> tuple[dict, list[str]]:
        # Rework within the change, on lines of its own. A failure here drops only those lines.
        try:
            factory = _factory_files(main, branch)
            done = metrics.rework(events, summary, factory, _change_diff(main, branch), tier)
            first_time = metrics.happy(events, summary, factory, tier, done)
            extra = metrics.in_change_trailers(done, first_time, metrics.spike(events, summary))
        except Exception:
            summary["coverage"] += " rework=failed"
            extra = []
        return summary, metrics.trailers(summary) + extra

    def from_history(reason: str) -> tuple[dict, list[str]]:
        now = datetime.now(UTC)
        start = datetime.combine(created, dtime(), UTC) if created else now
        summary = metrics.history_summary(
            (now - start).total_seconds(), way, tier, settings, reason
        )
        return finish(summary, [])

    if not settings["transcripts"]:
        return from_history("metrics.transcripts is off")
    try:
        dirs = _project_dirs(main)
        files = sum(1 for d in dirs for _ in d.glob("*.jsonl"))
        if not files:
            return from_history("no transcripts for this repo")
        events = metrics.read_events(dirs, branch, branch, cfg["commands"]["check"])
        if not events:
            return from_history("no transcripts for this change")
        closes = _close_times(main, cfg["git"]["base"])
        dep_closes = {}
        for ident in depends_on(text):
            name = next((n for n in closes if names_change(n, ident)), ident)
            dep_closes[name] = closes.get(name)
        summary = metrics.summarize(events, dep_closes, settings, way, tier)
        summary["coverage"] = f"transcripts={files} {summary['coverage']}"
        return finish(summary, events)
    except Exception as e:
        return from_history(f"capture failed: {type(e).__name__}")


def _drop_commit(main: Path, branch: str, trunk: str) -> str | None:
    """The `Drop <branch>` commit on the base's first-parent line whose second parent is the
    branch's tip: a rerun's sign that `record` is done. None when there is none."""
    tip = _git(main, "rev-parse", branch)
    log = _git(main, "log", "--first-parent", "--format=%H%x00%P%x00%s", trunk) or ""
    for line in log.splitlines():
        sha, parents, subject = (line.split("\x00") + ["", ""])[:3]
        if subject == f"{DROP_PREFIX}{branch}" and parents.split()[1:2] == [tip]:
            return sha
    return None


def _drop_record(
    main: Path,
    branch: str,
    sha: str,
    where: str | None,
    reached: str,
    reason: str,
    trailers: list[str] | None = None,
) -> str | None:
    """Record a dropped change on main: `Drop <branch>`, a merge that keeps main's tree, so the
    branch's commits stay reachable and `branch -d` can delete it. Only the state `new` wrote
    comes along: the higher counter, so the number stays spent. `measure`'s trailers end the
    message, as on a `Close` commit. Why not, or
    None; a failure leaves main as it was."""
    steps = [["merge", "-q", "-s", "ours", "--no-ff", "--no-commit", branch]]
    shown = _git(main, "show", f"{branch}:.sdlc/{LAST_ID}") or ""
    theirs = int(shown) if shown.isdigit() else None
    if theirs is not None and theirs > (read_last_id(main) or 0):
        steps.append(["write", LAST_ID, f"{theirs:03d}\n"])
    note = f"Dropped at {reached}; its artifacts are in {sha}" + (
        f", and archived to {where}." if where else "."
    )
    message = ["-m", f"{DROP_PREFIX}{branch}", "-m", reason, "-m", note]
    if trailers:
        message += ["-m", "\n".join(trailers)]
    steps.append(["commit", "-q", *message])
    for args in steps:
        if args[0] == "write":
            _write_state(main, args[1], args[2])
            args = ["add", "--", f".sdlc/{args[1]}"]
        err = _git_err(main, *args)
        if err:
            _git(main, "merge", "--abort")
            return f"git {args[0]} failed: {err}"
    return None


def _close_commit(
    main: Path,
    branch: str,
    sha: str,
    where: str | None,
    trailers: list[str] | None = None,
    closes: str | None = None,
) -> str | None:
    """Remove the change's folder from `main` in a commit of its own; why not, or None. A folder
    `main` no longer tracks was removed by an earlier run, which is done, so a rerun writes no
    second set of trailers. `trailers` end the message, where git reads them as trailers;
    `closes`, the tracker's line for closing its issue on the push, ends the paragraph before."""
    if not _git(main, "ls-files", f"work/{branch}"):
        return None
    said = f"Its artifacts are in {sha}" + (f", and archived to {where}." if where else ".")
    for args in (
        ["rm", "-r", "-q", f"work/{branch}"],
        [
            "commit", "-q", "-m", f"Close {branch}",
            "-m", said + (f"\n{closes}" if closes else ""),
            *(["-m", "\n".join(trailers)] if trailers else []),
        ],
    ):  # fmt: skip
        made = subprocess.run(["git", "-C", str(main), *args], capture_output=True, text=True)
        if made.returncode != 0:
            # Put the folder back, or the rerun that finishes this would find main dirty.
            _git(main, "reset", "-q", "HEAD", "--", f"work/{branch}")
            _git(main, "checkout", "-q", "--", f"work/{branch}")
            return f"git {args[0]} failed: {made.stderr.strip() or made.stdout.strip()}"
    return None


# Set on a close that another close handed off to: `home` once it runs main's script, `merged` once
# it runs the code its own merge brought. Read only here, so a handoff never loops.
HANDOFF_ENV = "SDLC_CLOSE_RAN"
RAN = {"home": "main's code", "merged": "merged code"}


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


def _handoff(main: Path, argv: list[str], ran: str, report: dict) -> int:
    """Run this close again with the main checkout's `scripts/sdlc.py`, as the skills run it, and
    give its report and exit code as this one's. A close is safe to rerun at any step, so the
    second one finds what this one did and carries on. If it prints no report (it didn't start),
    say so in `report` and stop: never carry on with the code this process loaded."""
    script = main / "scripts" / "sdlc.py"
    made = subprocess.run(
        [*_script_cmd(), str(script), "close", *argv],
        capture_output=True,
        text=True,
        env=os.environ | {HANDOFF_ENV: ran},
    )
    try:
        out = json.loads(made.stdout)
    except ValueError:
        out = None
    if isinstance(out, dict):
        out.setdefault("ran", RAN[ran])  # the innermost close says what ran it
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return made.returncode
    said = [ln for ln in made.stderr.splitlines() if ln.strip()]
    why = said[-1].strip() if said else f"exited {made.returncode}"
    if ran == "home":
        report["refusals"].append(f"main's sdlc.py didn't run: {why}")
    else:
        number = str(report.get("change") or "").split("-")[0]
        report["refusals"].append(
            f"merged code didn't run: {why}; main is merged, rerun /sdlc:close {number}"
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1


def cmd_close(root: Path, ident: str | None, check_only: bool = False) -> int:
    """Land a shipped change, mirror it, remove its folder, its worktree and its branch; or, for
    a dropped one, mirror it, record it on main in a `Drop` commit, and remove its worktree and
    branch.

    Every git step is one git refuses when something would be lost: `merge --ff-only`,
    `worktree remove` without --force, `branch -d`. The folder is removed only once the change's
    commit, which holds it, is on `main`: history is the copy, and the tracker a mirror of it. A
    dropped change's folder never reaches main's tree; its `Drop` merge makes its commits
    reachable from main before the branch goes. A rerun resumes: the merge is a no-op, the archive
    reuses its issue, a removed folder or a recorded drop is skipped. All preconditions are
    checked before anything is written.

    In the plugin's own repo, the close is run by main's script, then by the code its merge
    brought (`_handoff()`), so a change to close runs on its own close, and a stale copy of the
    plugin never closes anything."""
    main = main_root(root)
    own = _own_repo(main)
    if own and PLUGIN_DIR.resolve() != main.resolve() and not os.environ.get(HANDOFF_ENV):
        argv = [*([ident] if ident else []), *(["--check"] if check_only else [])]
        report = {"change": ident, "main_checkout": str(main), "refusals": [], "done": []}
        return _handoff(main, argv, "home", report | {"skipped": []})
    cfg, _, _ = load_config(main)
    trees = [(t, b) for t, b in worktrees(root) if DIR_RE.match(b)]
    if ident is None:
        here = _git(root, "branch", "--show-current") or ""
        ident = here if DIR_RE.match(here) else None
    found = [(t, b) for t, b in trees if names_change(b, ident)] if ident else []
    unavailable = archive_unavailable(main, cfg)
    report: dict = {
        "change": ident,
        "main_checkout": str(main),
        "archive": {"target": cfg["archive"]["target"], "location": None},
        "refusals": [],
        "done": [],
        "skipped": [],
    }
    # Nowhere to mirror to is an answer; a target set up wrong is a refusal.
    if unavailable and cfg["archive"]["target"] in ("none", "github"):
        report["archive"]["kept_because"] = unavailable
    elif unavailable:
        report["refusals"].append(f"archive: {unavailable}")

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    if not ident:
        report["refusals"].append(
            "no change named, and this checkout isn't on an NNN-slug branch: give its number"
        )
        return emit(1)
    if len(found) != 1:
        report["refusals"].append(
            f"{ident!r} matches {'no' if not found else len(found)} worktree(s)"
            + (f": {', '.join(b for _, b in found)}" if found else "")
        )
        return emit(1)
    tree, branch = found[0]
    folder = work_dir(tree) / branch
    kind = _stage(folder)
    report.update(change=branch, worktree=str(tree), branch=branch, kind=kind)

    if kind not in ("shipped", "dropped"):
        report["refusals"].append(
            f"{branch} isn't shipped: {folder}/intent.md with stage: shipped is missing. Run "
            "/sdlc:ship first, or /sdlc:drop to drop it."
        )
    elif kind == "dropped" and not dropped_reason((folder / "intent.md").read_text("utf-8")):
        report["refusals"].append(
            f"{branch} is dropped with no `## {DROPPED}` section saying why: run /sdlc:drop"
        )
    if _git(tree, "status", "--porcelain") not in ("", None):
        report["refusals"].append(f"{tree} has uncommitted or untracked files")
    trunk = cfg["git"]["base"]
    if why := trunk_refusal(main, trunk, cfg["git"]["base_source"]):
        report["refusals"].append(why)
        return emit(1)
    if _git(main, "branch", "--show-current") != trunk:
        report["refusals"].append(f"the main checkout ({main}) isn't on {trunk}")
    if _git(main, "status", "--porcelain", "--untracked-files=no") not in ("", None):
        report["refusals"].append(f"the main checkout ({main}) has uncommitted changes")
    # Merged already is a rerun's state, not a refusal.
    landed = _git(main, "merge-base", "--is-ancestor", branch, trunk) is not None
    if kind == "dropped":
        # A dropped change is recorded whatever the base has done since: nothing of it lands.
        if landed and not _drop_commit(main, branch, trunk):
            report["refusals"].append(
                f"{branch} is already on {trunk} with no {DROP_PREFIX}{branch} commit: it "
                "landed, so it isn't a drop"
            )
    elif not landed and behind_trunk(main, branch, trunk) != 0:
        report["refusals"].append(
            f"{trunk} has moved past {branch}'s base, so it can't fast-forward; rebase {branch} "
            f"onto {trunk} in its worktree and ship again"
        )
    if report["refusals"]:
        return emit(1)
    if own and kind == "shipped" and (reaches := _reaches(main, branch)):
        report["reaches"] = reaches

    sha = _git(main, "rev-parse", "--short", branch) or "?"
    kept: dict = {}

    def merge() -> str | None:
        return _git_err(main, "merge", "--ff-only", "-q", branch)

    def verify() -> str | None:
        # The copy that counts: the change's own commit, in main's history once it lands.
        text = _git(main, "show", f"{branch}:work/{branch}/intent.md")
        try:
            ok = text is not None and frontmatter.loads(text).get("stage") == kind
        except Exception:
            ok = False
        if not ok:
            return f"{branch}'s commit doesn't hold work/{branch}/intent.md, {kind}"
        if kind == "dropped":
            if not dropped_reason(text):
                return f"{branch}'s commit has no `## {DROPPED}` section in its intent.md"
            kept["reached"] = (frontmatter_list(text, "dropped_at") or [""])[0] or "unknown"
            kept["reason"] = first_paragraph(_body_of(text), DROPPED)
        return None

    captured: list[str] = []

    def measure() -> str | None:
        # Never a refusal: a change that can't be measured still lands, and says why.
        try:
            summary, lines = measure_change(main, branch, cfg)
        except Exception as e:
            summary, lines = {"coverage": f"none: capture failed: {type(e).__name__}"}, []
            lines = [f"Sdlc-Coverage: {summary['coverage']}"]
        captured[:] = lines
        report["measure"] = {"coverage": summary["coverage"], "trailers": lines}
        return None

    def mirror() -> str | None:
        if unavailable:
            return None
        change = _tracker_change(main, folder, sha)
        mirror_to = tracker(main, cfg)
        where, err = mirror_to.archive(change)
        report["archive"]["location"] = where
        # What the tracker says about closing its issue: a line for the Close commit, so the
        # push closes it, or why it closed it now. Only a tracker that has them sets them.
        for key in ("closes", "closed_because"):
            if getattr(mirror_to, key, None):
                report["archive"][key] = getattr(mirror_to, key)
        return err

    def remove_folder() -> str | None:
        where, closes = report["archive"]["location"], report["archive"].get("closes")
        return _close_commit(main, branch, sha, where, captured, closes)

    def record() -> str | None:
        if _drop_commit(main, branch, trunk):
            return None  # recorded by an earlier run that stopped before removing the worktree
        where = report["archive"]["location"]
        return _drop_record(main, branch, sha, where, kept["reached"], kept["reason"], captured)

    def git_step(*args: str):
        return lambda: _git_err(main, *args)

    if kind == "dropped":
        landing = [("verify", verify), ("measure", measure), ("archive", mirror)]
        landing.append(("record", record))
    else:
        landing = [("merge", merge), ("verify", verify), ("measure", measure)]
        landing += [("archive", mirror), ("remove folder", remove_folder)]
    steps = [
        *landing,
        ("remove worktree", git_step("worktree", "remove", str(tree))),
        ("delete branch", git_step("branch", "-d", branch)),
    ]
    if check_only:
        report["skipped"] = [f"{name} (--check)" for name, _ in steps]
        return emit(0)

    inside = Path.cwd().resolve().is_relative_to(tree.resolve())
    before = _git(main, "rev-parse", trunk)
    for i, (name, step) in enumerate(steps):
        if name == "remove worktree" and inside:
            report["skipped"] = [n for n, _ in steps[i:]]
            report["refusals"].append(
                f"worktree kept: this process runs inside {tree}. Run /sdlc:close "
                f"{branch.split('-')[0]} from the main checkout to finish."
            )
            return emit(3)
        if name == "archive" and unavailable:
            continue
        err = step()
        if err:
            report["skipped"] = [n for n, _ in steps[i:]]
            report["refusals"].append(f"{name} failed: {err}")
            return emit(1)
        report["done"].append(name)
        if name == "merge" and own and _merged_scripts(main, before, trunk):
            # The rest runs as the code this merge brought.
            report["skipped"] = [n for n, _ in steps[i + 1 :]]
            return _handoff(main, [branch], "merged", report)
    return emit(0)


def landing_reach(paths: list[str]) -> dict:
    """What a landed change to this plugin asks of the sessions and hosts running it from a clone:
    `scripts` are live in every session at once, `skills` and the factory's `agents` (by
    namespaced name) are read when a session starts, so need `/reload-plugins`, and `hosts`
    (setup's defaults and templates) need `/sdlc:setup` in each host. Only the kinds the paths
    touch."""
    scripts, skills, agents, hosts = False, set(), set(), []
    for path in paths:
        parts = path.split("/")
        if parts[0] == "scripts" or parts[:3] == ["plugins", "factory", "scripts"]:
            scripts = True
        elif parts[0] == "skills" and len(parts) > 2:
            skills.add(f"sdlc:{parts[1]}")
        elif parts[:3] == ["plugins", "factory", "skills"] and len(parts) > 4:
            skills.add(f"sdlc-factory:{parts[3]}")
        elif parts[:3] == ["plugins", "factory", "agents"] and path.endswith(".md"):
            agents.add(f"sdlc-factory:{parts[-1].removesuffix('.md')}")
        elif parts[0] in ("defaults", "templates"):
            hosts.append(path)
    found = {
        "scripts": scripts, "skills": sorted(skills), "agents": sorted(agents),
        "hosts": sorted(hosts),
    }  # fmt: skip
    return {k: v for k, v in found.items() if v}


def _reaches(main: Path, branch: str) -> dict | None:
    """`landing_reach()` over everything the change's branch touched; None when it touched
    nothing that reaches anyone. Never a refusal: a change whose paths can't be read lands, and
    `unknown` says why, so "nothing to do" is never a guess."""
    try:
        base = _change_base(main, branch)
        if base is None:
            return {"unknown": f"no commit on {branch} holds its intent"}
        names = _git(main, "diff", "--name-only", "--no-renames", base, branch)
        if names is None:
            return {"unknown": f"git couldn't diff {branch} against its base"}
        return landing_reach(names.splitlines()) or None
    except Exception as e:
        return {"unknown": f"reading the change's paths failed: {type(e).__name__}"}


# In the plugin's own repo, the commands that write from a change's worktree run the change's own
# `scripts/` once it edits them, so a change to ship or sync runs on its own code before it lands.
# The variable stops a second handoff, and set to anything by hand (`off`) skips the first.
OWN_SCRIPT_ENV = "SDLC_OWN_SCRIPT"
OWN_SCRIPT_CMDS = ("ship", "drop", "base", "sync")
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
        text=True,
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
        print(f"  ran {OWN_RAN}: {script}")
    print(made.stderr, end="", file=sys.stderr)
    return made.returncode


def _merged_scripts(main: Path, before: str | None, trunk: str) -> bool:
    """Whether a merge just brought this plugin's scripts into the main checkout it runs from, so
    the rest of the close must run as the merged code. Never twice for one close."""
    after = _git(main, "rev-parse", trunk)
    return (
        PLUGIN_DIR.resolve() == main.resolve()
        and os.environ.get(HANDOFF_ENV) != "merged"
        and before is not None
        and after != before
        and bool(_git(main, "diff", "--name-only", before, after, "--", "scripts"))
    )


# ---------------------------------------------------------------- trackers
#
# Close mirrors a landed change's folder to a tracker before it removes the folder from main. A
# tracker is a module in scripts/trackers/ (`Tracker`, made by `make(home, cfg)`), loaded by path
# only when `archive.target` names it: with `none`, no tracker code runs at all. Core renders
# what the tracker shows; the tracker never reads work/ or .sdlc/ itself.

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
ARTIFACT_ORDER = {"intent.md": 0, "spec.md": 1, "plan.md": 2, "notes.md": 3, "checks.md": 4}
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
        "body": "",
        "comments": [],
        "error": None,
        # The labels a tracker may set or remove.
        "vocabulary": {"tier": list(TIER_ARTIFACTS), "stage": STAGES, "impact": list(IMPACTS)},
        # The issue fields the project doc turns on, as the intent sets them; a tracker mirrors
        # these exactly and never reads or writes one that isn't here.
        "fields": {name: rec["fields"].get(name, []) for name in project_doc(home, cfg)[0]},
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
    tmp.write_text(value, encoding="utf-8")
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
# bumps the version files, commits and tags, all local and undoable; `publish` pushes and runs the
# host's command. Only publish pushes, and only behind its own approval.

# One `version` line per version file: JSON's `"version": "1.2.0",` or TOML's `version = "1.2.0"`.
# Not `target-version = ...`: the key must open the line.
VERSION_RE = re.compile(r'^([ \t]*"?version"?[ \t]*[:=][ \t]*")([^"\n]+)(".*)$', re.M)
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
    rec.update(serves=None, moves=[])
    if not read:
        return rec
    try:
        post = frontmatter.loads(text) if text is not None else None
    except Exception:
        post = None
    if post is None:
        rec["problems"].append(f"{name}: its commit {sha} has no readable work/{name}/intent.md")
        return rec
    rec["tier"] = post.get("tier")
    rec["impact"] = str(post.get("impact") or "")
    rec["created"] = str(post.get("created") or "")
    rec["idea"] = intent_idea(text or "")
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
    fmt = "--format=%h%x00%p%x00%cs%x00%s"
    log = _git(home, "log", "--first-parent", "--reverse", fmt, span) or ""
    found = []
    for line in log.splitlines():
        close_sha, parent, close_date, subject = (line.split("\x00") + ["", "", ""])[:4]
        name = subject[len(CLOSE_PREFIX) :].strip() if subject.startswith(CLOSE_PREFIX) else ""
        if DIR_RE.match(name) and parent:
            text = _git(home, "show", f"{close_sha}^:work/{name}/intent.md") if read else None
            rec = _change_record(name, text, parent, closed=True, read=read)
            # What close measured, on its own commit, and what ship's review found, on the
            # change's: both trailers.
            rec["metrics"] = rec["findings"] = None
            if read:
                rec["metrics"] = metrics.parse_trailers(
                    _git(home, "show", "-s", "--format=%B", close_sha)
                )
                own = metrics.parse_trailers(_git(home, "show", "-s", "--format=%B", parent))
                rec["findings"] = (own or {}).get("findings")
            found.append({**rec, "close_sha": close_sha, "close_date": close_date})
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
            text = _git(home, "show", f"{drop_sha}^2:work/{name}/intent.md")
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
                at = last or "<the commit that released it>"
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
        intent = f"work/{folder.name}/intent.md"
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
    overdue, due = shims_due(reg["shims"], out["version"], out["next"])
    unversioned = [] if out["version"] else reg["shims"]
    out["deprecations"] = {"overdue": overdue, "due": due, "unversioned": unversioned}
    return out


def release_notes(changes: list[dict], github: bool) -> str:
    """One line per change: its number, title and impact, and its issue when GitHub numbers it."""
    return "\n".join(
        f"- {c['id']} {c['title'] or c['slug']} ({c['impact']})"
        + (f" #{int(c['id'])}" if github else "")
        for c in changes
    )


def with_changelog(text: str, version: str, notes: str, today: str) -> str:
    """`text` with this release's section on top, under its `# ` title when it has one."""
    section = f"## {version} — {today}\n\n{notes}\n"
    first, _, rest = text.partition("\n")
    if first.startswith("# "):
        rest = rest.lstrip("\n")
        return f"{first}\n\n{section}" + (f"\n{rest}" if rest else "")
    return section + (f"\n{text}" if text else "")


def _git_err(root: Path, *args: str) -> str | None:
    """None when the git command succeeds, else what it said: never empty, since a hook can fail
    a command without a word."""
    made = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
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


def cmd_unreleased(root: Path) -> int:
    """The changes since the last release, as JSON. Writes nothing."""
    home = main_root(root)
    cfg, _, parsed = load_config(home)
    print(json.dumps(unreleased(home, cfg), indent=2, ensure_ascii=False))
    return 0 if parsed else 1


def cmd_release(root: Path, check_only: bool = False, version: str | None = None) -> int:
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
        "changes": u["changes"],
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
        path.write_bytes(with_changelog(text, new, notes, date.today().isoformat()).encode())
        return None

    def restore() -> None:
        # Put the files back, so a rerun finds main clean and the same release to make.
        _put_back(home, report["files"])
        for rel_path in created:
            (home / rel_path).unlink(missing_ok=True)

    def after_bump() -> str | None:
        # Main had no uncommitted tracked changes (`_release_refusals`), so every tracked file
        # changed now beyond the release's own is the command's. New untracked files are listed,
        # never committed: they may be anything the command leaves behind.
        before = _untracked(home)
        err = None
        try:
            ran = subprocess.run(
                report["after_bump"], shell=True, cwd=home, capture_output=True, text=True,
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
                report["prepare"], shell=True, cwd=home, capture_output=True, text=True,
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
    # With the new tag counted: a release is the usual moment a retrospective falls due.
    report["retro_due"] = retro_due(home, cfg)
    return emit(0)


def _remote_sha(home: Path, remote: str, ref: str) -> str | None:
    out = _git(home, "ls-remote", remote, ref)
    return out.split()[0] if out else None


def cmd_publish(root: Path, check_only: bool = False) -> int:
    """Push the base branch (`git.base`) and the release tag, then run the host's publish command:
    the one step in the plugin that sends anything anywhere. Never forced, so a remote that has
    moved is refused. A rerun skips what the remote already has and a publish command that
    already succeeded."""
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
    if tagged is None:
        refusals.append(f"no tag {tag}: run /sdlc:release first")
    elif trunk and tagged != _git(home, "rev-parse", trunk):
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

    def pushed(ref: str) -> bool:
        return _remote_sha(home, remote, ref) == _git(home, "rev-parse", ref)

    def published() -> bool:
        return "published" in (_git(home, "notes", "--ref", "sdlc", "show", tag) or "")

    def run_command() -> str | None:
        # No terminal and no stdin: the approval came before, so a command that asks fails now.
        ran = subprocess.run(
            report["command"], shell=True, cwd=home, capture_output=True, text=True,
            stdin=subprocess.DEVNULL,
        )  # fmt: skip
        if ran.returncode != 0:
            return f"release.publish exited {ran.returncode}: {ran.stderr.strip()}"
        return _git_err(home, "notes", "--ref", "sdlc", "add", "-f", "-m", "published", tag)

    def push(ref: str):
        # Never --force: a remote that has moved refuses, and that refusal is the answer.
        return lambda: _git_err(home, "push", "-q", remote, ref)

    trunk_ref, tag_ref = f"refs/heads/{trunk}", f"refs/tags/{tag}"
    steps = [
        (f"push {trunk}", lambda: pushed(trunk_ref), push(trunk_ref)),
        ("push tag", lambda: pushed(tag_ref), push(tag_ref)),
        ("publish command", lambda: not report["command"] or published(), run_command),
    ]
    if check_only:
        report["skipped"] = [f"{name} (--check)" for name, _, _ in steps]
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
    return emit(0)


# ---------------------------------------------------------------- retro
#
# The outermost loop: /sdlc:retro looks across the changes and releases since the last
# retrospective and sets direction. What can be counted is counted here, so the skill reads one
# JSON blob rather than history: the retrospective keeps the rule it audits.

RETRO_PREFIX = "Retrospective "
RETRO_RE = re.compile(r"^Retrospective (\d{4}-\d{2}-\d{2})$")
# A later change touching an earlier one's files within this many days reads as rework.
REWORK_DAYS = 7
# A file touched by more than this share of the window's changes is common to them, not rework:
# sharing it says nothing. Only once the share holds a pair (six changes, at a third), since in a
# smaller window the two changes of any pair would already be more than it.
REWORK_COMMON_SHARE = 1 / 3
# Each evidence command's limits: seconds before it's stopped, and characters of output kept.
EVIDENCE_TIMEOUT = 60
EVIDENCE_LIMIT = 20_000
# Signals the process doc names that history doesn't record, and what would record them.
UNMEASURED = [
    {
        # Ship's side is recorded (`Sdlc-Findings` on its commit); "later" isn't yet.
        "signal": "findings caught at ship vs. found later",
        "needs": "a later change to say which earlier change it fixes",
    },
]
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
# Bound here so `retro` reads them, and its tests can stand in for them, by these names.
_project_dirs = metrics._project_dirs


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


def last_retrospective(home: Path, trunk: str | None) -> dict | None:
    """The newest `Retrospective YYYY-MM-DD` commit on the base branch's first-parent line, the
    boundary of the next one. retro-commit writes the subject, so it is never a guess."""
    if not trunk:
        return None
    log = _git(home, "log", "--first-parent", "--format=%h%x00%s", trunk) or ""
    for line in log.splitlines():
        sha, _, subject = line.partition("\x00")
        m = RETRO_RE.match(subject)
        if m:
            return {"sha": sha, "date": m.group(1)}
    return None


def prose_metrics(home: Path, cfg: dict) -> dict:
    """How much each skill is, the plugin's: what every session in a host reads and follows. And
    the host docs the skills read on top. Tokens are an estimate, bytes / 4."""
    skills = {}
    for path in sorted((PLUGIN_DIR / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        size = len(text.encode("utf-8"))
        commands = bash_commands(text)
        skills[path.parent.name] = {
            "lines": len(text.splitlines()),
            "bytes": size,
            "est_tokens": size // 4,
            "commands": len(commands),
            "script_calls": sum("scripts/sdlc.py" in c for c in commands),
        }
    docs = {}
    wanted = [(k, cfg["docs"][k]) for k in ("process", "policy", "review") if cfg["docs"][k]]
    for key, rel in [*wanted, *(("context", rel) for rel in cfg["docs"]["context"])]:
        found = doc_path(home, key, rel)
        path = Path(found["path"]) if Path(found["path"]).is_absolute() else home / found["path"]
        if found["exists"] and found["path"] not in docs:
            size = path.stat().st_size
            docs[found["path"]] = {"bytes": size, "est_tokens": size // 4}
    script = Path(__file__).resolve()
    return {
        "estimate": "est_tokens is bytes / 4",
        "skills": skills,
        "docs": docs,
        "sdlc_py_lines": len(script.read_text(encoding="utf-8").splitlines()),
    }


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
GROUP_CHANGE_RE = re.compile(r"\b(\d{3,})(?:-[a-z0-9][a-z0-9-]*)?\b")


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
            }
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
        if line.startswith("#"):
            current = None
        g = GROUPS_RE.match(line.strip())
        if g and current and not any(current["groups"].values()):
            # Seeds by quoted title or bare id, then change numbers from what's left, so an id's
            # year is never read as a change.
            current["groups"]["seeds"] = refs_in(g[1])
            rest = ENTRY_ID_TOKEN_RE.sub("", re.sub(r'"[^"]*"', "", g[1]))
            current["groups"]["changes"] = GROUP_CHANGE_RE.findall(rest)
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
    home: Path, items: list[dict], open_names: list[str], trunk: str | None
) -> dict:
    """What each open milestone's grouped seeds and changes have become, from history: a change
    closed (with when), still open, or unknown; a seed still in the register, shipped by the change
    whose `idea:` names it, or vanished with no change behind it."""
    wanted = [i for i in items if i["kind"] == "milestone" and i["status"] == "open"]
    if not wanted:
        return {}
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
            shipped = next((c for c in history if c["idea"] and same_ref(c["idea"], seed)), None)
            if shipped:
                rows.append({"entry": seed, "kind": "seed", "verdict": "shipped",
                             "change": shipped["name"], "date": shipped["close_date"]})  # fmt: skip
            elif any(ref_matches(seed, e) for e in entries):
                rows.append({"entry": seed, "kind": "seed", "verdict": "open"})
            else:
                rows.append({"entry": seed, "kind": "seed", "verdict": "vanished"})
        out[item["id"]] = rows
    return out


def _release_of(home: Path, cfg: dict, sha: str) -> str | None:
    """The first release tag that holds a change's commit: when its users could have had it. None
    while no release does."""
    pattern = cfg["release"]["tag"].replace("{version}", "*")
    tags = _git(home, "tag", "--contains", sha, "--list", pattern, "--sort=creatordate")
    return (tags or "").splitlines()[0] if tags else None


def _evidence(home: Path, commands: list[str]) -> list[dict]:
    """Each evidence command's output, run from the repo root, one after another. Passed through
    unread: what it means is the host's, and the retrospective's to judge. A command that fails or
    hangs is a row saying so, never a failed retrospective."""
    rows = []
    for command in commands:
        row: dict = {"command": command, "exit": None, "output": "", "truncated": False}
        row["error"] = None
        try:
            # Output that isn't UTF-8 (a binary export, a stray byte) is replaced, not raised.
            ran = subprocess.run(
                command, shell=True, cwd=home, capture_output=True, text=True,
                errors="replace", timeout=EVIDENCE_TIMEOUT,
            )  # fmt: skip
        except subprocess.TimeoutExpired:
            row["error"] = f"timed out after {EVIDENCE_TIMEOUT}s"
            rows.append(row)
            continue
        except OSError as e:
            row["error"] = str(e)
            rows.append(row)
            continue
        row["exit"] = ran.returncode
        row["output"] = ran.stdout[:EVIDENCE_LIMIT]
        row["truncated"] = len(ran.stdout) > EVIDENCE_LIMIT
        if ran.returncode != 0:
            why = ran.stderr.strip()[:500] or "no output"
            row["error"] = f"exited {ran.returncode}: {why}"
        rows.append(row)
    return rows


def _product(home: Path, cfg: dict, doc: dict, changes: list[dict], open_recs: list[dict]) -> dict:
    """What the product pass counts: for each open outcome, the changes closed since the last
    retrospective that serve it and the open ones that do; the closed changes that name no outcome
    (`unlinked`, from before the doc) or say `none`; the open outcomes nothing serves; and the open
    changes still naming one a retrospective has struck (`stale`). Then the evidence."""
    open_ids = [i["id"] for i in doc["items"] if i["status"] == "open"]
    struck = {i["id"] for i in doc["items"] if i["status"] != "open"}
    outcomes: dict[str, dict] = {o: {"closed": [], "open": []} for o in open_ids}
    for rec in changes:
        for o in rec["serves"] or []:
            if o in outcomes:
                moves = [m["text"] for m in rec["moves"] if o in m["ids"]]
                outcomes[o]["closed"].append(
                    {"change": rec["name"], "release": rec["release"], "moves": moves}
                )
    stale = []
    for r in open_recs:
        name = f"{r['id']}-{r['slug']}"
        for o in r.get("serves") or []:
            if o in outcomes:
                outcomes[o]["open"].append(name)
            elif o in struck:
                stale.append({"change": name, "outcome": o})
    return {
        "items": doc["items"],
        "problems": doc["problems"],
        "next_ids": doc["next_ids"],
        "outcomes": outcomes,
        "unlinked": [c["name"] for c in changes if c["serves"] is None],
        "none": [c["name"] for c in changes if c["serves"] == ["none"]],
        "unserved": [o for o, rows in outcomes.items() if not rows["closed"] and not rows["open"]],
        "stale": stale,
        "evidence": _evidence(home, cfg["retro"]["evidence"]),
    }


def _direction_text(home: Path, cfg: dict) -> str:
    path = home / cfg["docs"]["direction"]
    return path.read_text(encoding="utf-8") if path.is_file() else ""


# What `status` puts forward once the open changes are done, in this order, each candidate once
# under the first rule it meets. A fixed order a person can argue with line by line, never a
# score; the status skill weighs it against the open changes, release and retro.
NEXT_RULES = (
    ("bug", "entries tagged [bug], oldest first"),
    ("milestone", "each open milestone's first grouped seed that is ready, in the doc's order"),
    ("series", "ready seeds whose After: seeds have all left the register, oldest first"),
    ("nits", "open nits of cost S, one line per theme, oldest theme first"),
    ("seed", "every other ready seed, oldest first"),
)
NEXT_SHOWN = 5


def _seed_state(entry: dict, open_titles: set[str], building: set[str]) -> str:
    """`building` (tagged so, or named by an open change's `idea:`), `waiting` (a seed its
    `After:` names is still open), or `ready`."""
    if is_building(entry) or entry["title"] in building:
        return "building"
    if any(t in open_titles for t in entry["after"]):
        return "waiting"
    return "ready"


def _after_loops(waiting: dict[str, list[str]]) -> list[list[str]]:
    """Each set of waiting seeds that wait on each other, once, in the order first met."""
    loops: list[list[str]] = []
    seen: set[str] = set()
    for start in waiting:
        path: list[str] = []
        node = start
        while node in waiting and node not in path and node not in seen:
            path.append(node)
            node = next((t for t in waiting[node] if t in waiting), "")
        if node in path:
            loops.append(path[path.index(node) :])
        seen.update(path)
    return loops


def next_up(home: Path, cfg: dict, open_changes: list[dict], today: date) -> dict:
    """What to work on once the open changes are done, from the main checkout's ideas, nits and
    direction doc, ordered by NEXT_RULES. Read-only, and a missing file adds nothing. Also the
    open milestones with nothing left in their groups, and `After:` lines that can never be met."""
    ideas = [e for e in inbox_entries(home) if not is_nit(e)]
    nits = nit_entries(home)[0]
    doc = direction_items(_direction_text(home, cfg))
    named = [r["idea"] for r in open_changes if r.get("idea")]
    building = {e["title"] for e in ideas if any(ref_matches(n, e) for n in named)}
    states = {e["title"]: "building" for e in ideas if is_building(e) or e["title"] in building}
    open_titles = {e["title"] for e in ideas if e["title"] not in states}
    for e in ideas:
        states.setdefault(e["title"], _seed_state(e, open_titles, building))
    ready = sorted((e for e in ideas if states[e["title"]] == "ready"), key=lambda e: e["date"])
    known = {e["title"] for e in ideas}
    milestones = [i for i in doc["items"] if i["kind"] == "milestone" and i["status"] == "open"]

    def seed(rule: str, label: str, e: dict) -> dict:
        return {"rule": rule, "label": label, "title": e["title"],
                "age_days": _age_days({"created": e["date"]}, today),
                "command": f"/sdlc:intent {e['id'] or e['title']}"}  # fmt: skip

    items: list[dict] = []
    taken: set[str] = set()
    for rule, _ in NEXT_RULES:
        found: list[dict] = []
        if rule == "bug":
            found = [seed(rule, "bug", e) for e in ready if e["status"].strip().lower() == "bug"]
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
                if e["after"] and not any(t in known for t in e["after"])
            ]
        elif rule == "nits":
            themes = nits_summary([n for n in nits if n["cost"] == "S"], today)["themes"]
            for theme, t in sorted(themes.items(), key=lambda kv: kv[1]["oldest"] or ""):
                found.append({"rule": rule, "label": "nits",
                              "title": f"[{theme}] {t['count']} open, cost S",
                              "age_days": t["age_days"],
                              "command": f"/sdlc:intent pay down the [{theme}] nits"})  # fmt: skip
        else:
            found = [seed(rule, "seed", e) for e in ready]
        for item in found:
            if item["rule"] == "nits" or item["title"] not in taken:
                taken.add(item["title"])
                items.append(item)

    done = []
    if milestones:
        open_names = [f"{r['id']}-{r['slug']}" for r in open_changes]
        verdicts = _milestone_verdicts(home, doc["items"], open_names, cfg["git"]["base"])
        for m_id, rows in verdicts.items():
            if rows and all(r["verdict"] in ("closed", "shipped", "vanished") for r in rows):
                done.append(m_id)

    warnings = []
    dangling = {t for e in ideas for t in e["after"] if t not in known}
    if dangling:
        history = closed_changes(home, None, cfg["git"]["base"])
        shipped = [c["idea"] for c in history if c.get("idea")]
        for e in ideas:
            for t in e["after"]:
                if t in dangling and not any(same_ref(s, t) for s in shipped):
                    warnings.append(f'"{e["title"]}" waits on "{t}", which is no seed or change')
    waiting = {e["title"]: e["after"] for e in ideas if states[e["title"]] == "waiting"}
    for loop in _after_loops(waiting):
        names = ", ".join(f'"{t}"' for t in loop)
        warnings.append(f"these seeds wait on each other, so none will come up: {names}")
    return {"items": items, "done_milestones": done, "warnings": warnings}


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


# The totals a retrospective compares, as medians per tier and way of running.
COMPARED = (
    "elapsed", "agent", "response", "away", "blocked", "stops", "required", "permission",
    "ship_runs", "reenter", "in", "cache_read", "out",
)  # fmt: skip


def _stop_target(totals: dict, allowance: int) -> int | None:
    """The stops a change was measured against: its own gates plus the allowance. A `Close`
    commit from before `allowance=` was recorded carries one flat `target=` for every change, so
    its target is worked out again from its own `required=` and today's allowance."""
    if "allowance" in totals:
        return totals.get("target")
    required = totals.get("required")
    return required + allowance if isinstance(required, int) else None


def metrics_summary(
    changes: list[dict], allowance: int = CONFIG_KEYS["metrics"]["stop_allowance"]
) -> dict:
    """What the `Close` trailers of the changes in range add up to: per tier and way of running,
    the median of each total, its stop target and the stops over it, tokens and agent time per
    stage and role, and ship's findings. Changes close couldn't measure are counted, not guessed
    at."""

    def median(values: list) -> float | None:
        values = [v for v in values if isinstance(v, int)]
        return statistics.median(values) if values else None

    def over(totals: dict) -> int | None:
        target, stops = _stop_target(totals, allowance), totals.get("stops")
        return stops - target if isinstance(stops, int) and isinstance(target, int) else None

    captured = [c for c in changes if (c.get("metrics") or {}).get("totals")]
    groups: dict[str, dict] = {}
    for c in captured:
        m = c["metrics"]
        key = f"tier {c['tier']}, {m.get('mode') or 'manual'}"
        g = groups.setdefault(key, {"changes": [], "findings": {"important": 0, "nit": 0}})
        g["changes"].append(m)
        for k in ("important", "nit"):
            g["findings"][k] += (c.get("findings") or {}).get(k) or 0
    out: dict = {
        "captured": len(captured),
        "uncaptured": len(changes) - len(captured),
        "groups": {},
    }
    for key, g in groups.items():
        ms = g["changes"]
        stages = sorted({s for m in ms for s in m["stages"]}, key=metrics.STAGES.index)
        roles = sorted({r for m in ms for r in m["roles"]})
        out["groups"][key] = {
            "changes": len(ms),
            "median": {
                **{k: median([m["totals"].get(k) for m in ms]) for k in COMPARED},
                "over": median([over(m["totals"]) for m in ms]),
            },
            "target": median([_stop_target(m["totals"], allowance) for m in ms]),
            "stages": {
                s: {
                    k: median([(m["stages"].get(s) or {}).get(k) for m in ms])
                    for k in ("elapsed", "agent", "response", "away", "gate", "extra", "cache_read")
                }
                for s in stages
            },
            "roles": {
                r: {
                    k: sum((m["roles"].get(r) or {}).get(k) or 0 for m in ms)
                    for k in ("runs", "agent", "cache_read", "out")
                }
                for r in roles
            },
            "findings": g["findings"],
            "in_change": _in_change_summary(ms, median),
        }
    return out


def _in_change_summary(ms: list[dict], median) -> dict:
    """Rework within the changes of one group: how often each stage went through first time, the
    share of changes where every stage seen did, the median of each rework count, and what spikes
    cost. Retro's own `rework` (a later change fixing this one) is another measure."""
    happy = [m["happy"] for m in ms if m.get("happy")]
    first_time = {}
    for stage in metrics.HAPPY_STAGES:
        marks = [h.get(stage) for h in happy if h.get(stage) in ("yes", "no")]
        if marks:
            first_time[stage] = round(marks.count("yes") / len(marks), 2)
    judged = [h for h in happy if h.get("of")]
    done = [m["rework"] for m in ms if m.get("rework")]
    spikes = [m["spike"] for m in ms if m.get("spike")]
    return {
        "first_time": first_time,
        "all_first": (
            round(sum(1 for h in judged if h["first"] == h["of"]) / len(judged), 2)
            if judged
            else None
        ),
        "rework": {
            k: median([d.get(k) for d in done]) for k in sorted({k for d in done for k in d})
        },
        "spike": {
            "changes": len(spikes),
            **{k: sum(s.get(k) or 0 for s in spikes) for k in ("segments", "agent", "edits")},
        },
    }


# What a dropped change's trailers add up to: the time and tokens spent on work that didn't ship.
DROPPED_COST = ("elapsed", "agent", "in", "cache_read", "out")


def dropped_cost(dropped: list[dict]) -> dict:
    """The `Drop` trailers in range summed by the stage each change reached, and by tier and way of
    running. Changes close couldn't measure are counted, not guessed at."""
    captured = [d for d in dropped if (d.get("metrics") or {}).get("totals")]
    by_stage: dict[str, dict] = {}
    by_group: dict[str, dict] = {}
    for d in captured:
        m = d["metrics"]
        group = f"tier {d['tier']}, {m.get('mode') or 'manual'}"
        for key, table in ((d.get("dropped_at", "unknown"), by_stage), (group, by_group)):
            sums = table.setdefault(key, {"changes": 0, **dict.fromkeys(DROPPED_COST, 0)})
            sums["changes"] += 1
            for k in DROPPED_COST:
                value = m["totals"].get(k)
                sums[k] += value if isinstance(value, int) else 0
    return {
        "captured": len(captured),
        "uncaptured": len(dropped) - len(captured),
        "by_stage": by_stage,
        "by_group": by_group,
    }


def retro(home: Path, cfg: dict, today: date | None = None) -> dict:
    """What the retrospective counts: everything since the last one, from history. Read-only."""
    today = today or date.today()
    trunk = cfg["git"]["base"]
    since = last_retrospective(home, trunk)
    changes = closed_changes(home, since["sha"] if since else None, trunk)
    problems: list[str] = [] if trunk else [trunk_refusal(home, trunk)]
    touched: dict[str, set[str]] = {}
    # Ship's context pass edits these on every change by design, so sharing them isn't rework.
    every_change = {*cfg["docs"]["context"], cfg["docs"]["process"], cfg["docs"]["policy"]}
    for rec in changes:
        problems += rec.pop("problems")
        # A change ships as one commit or several, and its size is all of them: its branch from
        # where it started. Without that start, the last commit still says what it touched.
        base = _change_base(home, rec["name"], rec["sha"])
        if base:
            numstat = _git(home, "diff", "--numstat", "--no-renames", base, rec["sha"]) or ""
        else:
            numstat = _git(home, "diff-tree", "--no-commit-id", "--numstat", "-r", rec["sha"]) or ""
            name = rec["name"]
            problems.append(
                f"{name}: no commit holds work/{name}/intent.md, so its size is unknown"
            )
        files, lines = [], 0
        for row in numstat.splitlines():
            parts = row.split("\t")
            if len(parts) == 3:
                files.append(parts[2])
                lines += sum(int(n) for n in parts[:2] if n.isdigit())
        # A change's own folder is its alone; the code and docs around it are what reworks.
        touched[rec["name"]] = {
            f for f in files if not f.startswith("work/") and f not in every_change
        }
        rec.update(
            files=len(files) if base else None,
            lines=lines if base else None,
            days_open=_days_between(rec["created"], rec["close_date"]),
            release=_release_of(home, cfg, rec["sha"]),
        )
    dropped = dropped_changes(home, since["sha"] if since else None, trunk)
    for rec in dropped:
        problems += rec.pop("problems")
        # What the dropped branch touched: its tip against where it left the base.
        fork = _git(home, "merge-base", f"{rec['drop_sha']}^1", f"{rec['drop_sha']}^2")
        files = (_git(home, "diff", "--name-only", fork, rec["sha"]) or "").split() if fork else []
        touched[rec["name"]] = {
            f for f in files if not f.startswith("work/") and f not in every_change
        }
        rec["files"] = len(files)
    counts = Counter(f for files in touched.values() for f in files)
    window = len(changes) + len(dropped)
    common = (
        {f: n for f, n in counts.items() if n > window * REWORK_COMMON_SHARE}
        if window * REWORK_COMMON_SHARE >= 2
        else {}
    )
    rework = []
    for i, earlier in enumerate(changes):
        for later in changes[i + 1 :]:
            gap = _days_between(earlier["close_date"], later["close_date"])
            shared = sorted(touched[earlier["name"]] & touched[later["name"]] - common.keys())
            if gap is not None and gap <= REWORK_DAYS and shared:
                rework.append(
                    {"change": later["name"], "reworks": earlier["name"], "days": gap,
                     "files": shared}
                )  # fmt: skip
    # Work picked up again after a drop: a change closed soon after it, on the same code.
    for gone in dropped:
        for later in changes:
            gap = _days_between(gone["drop_date"], later["close_date"])
            shared = sorted(touched[gone["name"]] & touched[later["name"]] - common.keys())
            if gap is not None and 0 <= gap <= REWORK_DAYS and shared:
                rework.append(
                    {"change": later["name"], "reworks": gone["name"], "days": gap,
                     "files": shared, "dropped": True}
                )  # fmt: skip
    a = analyze(home, today)
    seeds = [i for i in inbox_entries(home) if not is_building(i) and not is_nit(i)]
    direction = direction_items(_direction_text(home, cfg))
    open_names = [f"{r['id']}-{r['slug']}" for r in a["open"]]
    direction["milestones"] = _milestone_verdicts(home, direction["items"], open_names, trunk)
    doc = product_doc(home, cfg)
    product = None if doc is None else _product(home, cfg, doc, changes, a["open"])
    return {
        "since": since,
        "today": today.isoformat(),
        "changes": changes,
        "dropped": dropped,
        "dropped_at_counts": dict(Counter(d.get("dropped_at", "unknown") for d in dropped)),
        "dropped_cost": dropped_cost(dropped),
        "problems": problems,
        "rework": rework,
        "rework_common": [
            {"file": f, "changes": n}
            for f, n in sorted(common.items(), key=lambda c: (-c[1], c[0]))
        ],
        "open": [
            {
                "name": f"{r['id']}-{r['slug']}",
                "title": TITLE_ID_RE.sub("", r["title"]),
                "tier": r["tier"],
                "stage": r["stage"],
                "age_days": r.get("age_days"),
            }
            for r in a["open"]
        ],  # fmt: skip
        "ideas": {
            "seeds": len(seeds),
            "oldest": min((i["date"] for i in seeds), default=None),
        },
        "nits": nits_summary(nit_entries(home)[0], today),
        "tiers": dict(Counter(str(c["tier"]) for c in changes)),
        "impacts": dict(Counter(c["impact"] or "unset" for c in changes)),
        "releases": _release_tags(home, cfg, since),
        "unmeasured": UNMEASURED,
        "direction": direction,
        "metrics": metrics_summary(changes, cfg["metrics"]["stop_allowance"]),
        "product": product,
        "prose": prose_metrics(home, cfg),
    }


def cmd_retro(root: Path) -> int:
    """The retrospective's counts as JSON. Writes nothing, and reads nothing outside the repo."""
    home = main_root(root)
    cfg, _, parsed = load_config(home)
    out = retro(home, cfg)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0 if parsed else 1


def cmd_retro_commit(root: Path, today: date | None = None) -> int:
    """Record a retrospective: one commit, `Retrospective YYYY-MM-DD`, holding the direction doc,
    the register and the product doc's outcomes, and nothing else, so main is never left dirty.
    Every refusal is found before anything is written."""
    home = main_root(root)
    cfg, _, _ = load_config(home)
    stamp = (today or date.today()).isoformat()
    allowed = {cfg["docs"]["direction"], f"work/{register_path(work_dir(home)).name}"}
    if cfg["docs"]["product"]:
        allowed.add(cfg["docs"]["product"])
    report: dict = {"commit": f"{RETRO_PREFIX}{stamp}", "paths": [], "refusals": [], "done": []}
    refusals = report["refusals"]

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    if root.resolve() != home.resolve():
        refusals.append(f"run it from the main checkout ({home}), not a change's worktree")
    trunk = cfg["git"]["base"]
    if why := trunk_refusal(home, trunk, cfg["git"]["base_source"]):
        refusals.append(why)
    elif _git(home, "branch", "--show-current") != trunk:
        refusals.append(f"the main checkout ({home}) isn't on {trunk}")
    # Staged, unstaged and untracked, by name: porcelain's columns don't survive `_git`'s strip.
    tracked = _git(home, "-c", "core.quotePath=false", "diff", "--name-only", "HEAD") or ""
    untracked = (
        _git(home, "-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard") or ""
    )
    changed = sorted({p for p in (*tracked.splitlines(), *untracked.splitlines()) if p})
    stray = [p for p in changed if p not in allowed]
    if stray:
        refusals.append(
            f"only {' and '.join(sorted(allowed))} may be uncommitted; also changed: "
            + ", ".join(stray)
        )
    elif not changed:
        refusals.append(f"nothing to record: {' and '.join(sorted(allowed))} are unchanged")
    last = last_retrospective(home, trunk)
    if last and last["date"] == stamp:
        refusals.append(f"{report['commit']} is already on {trunk} ({last['sha']}): one a day")
    # Follow-through: every goal, milestone or outcome the committed docs left open is still
    # there, carried or struck with its status. One already struck may go: it stayed one
    # retrospective. A product doc the retrospective didn't touch is checked all the same.
    docs = [("direction", "GM")] + ([("product", "O")] if cfg["docs"]["product"] else [])
    for key, kinds in docs:
        rel = cfg["docs"][key]
        committed = doc_items(_git(home, "show", f"HEAD:{rel}") or "", kinds)
        path = home / rel
        new = doc_items(path.read_text(encoding="utf-8") if path.is_file() else "", kinds)
        kept = {i["id"] for i in new["items"]}
        for item in committed["items"]:
            if item["status"] == "open" and item["id"] not in kept:
                refusals.append(
                    f"{item['id']} was open and the new {key} doc drops it: carry it, or strike "
                    "it with Done, Dropped or Revised"
                )
        refusals += [f"{key} doc: {p}" for p in new["problems"]]
    if refusals:
        return emit(1)
    report["paths"] = changed
    for args in (["add", "--", *changed], ["commit", "-q", "-m", report["commit"], "--", *changed]):
        made = subprocess.run(["git", "-C", str(home), *args], capture_output=True, text=True)
        if made.returncode != 0:
            refusals.append(f"git {args[0]} failed: {made.stderr.strip()}")
            return emit(1)
    report["done"].append("commit")
    report["sha"] = _git(home, "rev-parse", "--short", "HEAD")
    return emit(0)


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
                rel = p.relative_to(root)
                found.append((f"./{rel}", str(rel)))
    return found


# The script's subcommands that only read, which setup proposes allowing without a prompt. The `*`
# before the path stands in for wherever the plugin is installed, which differs per machine and
# changes when it updates; a plugin can't ship permission rules of its own. Nothing that writes
# is here: new, ship and close keep asking, and so does accept, which runs a change's own checks.
READ_ONLY = (
    "status", "check", "config", "next", "undone", "checks", "context", "readiness", "unreleased",
    "drift", "next-entry",
)  # fmt: skip
ALLOW_RULES = [f"Bash(uv run --quiet --script */scripts/sdlc.py {c} *)" for c in READ_ONLY]
SETTINGS = Path(".claude") / "settings.json"


def _allowed(root: Path) -> list[str]:
    try:
        allow = json.loads((root / SETTINGS).read_text(encoding="utf-8"))["permissions"]["allow"]
        return [a for a in allow if isinstance(a, str)]
    except (OSError, ValueError, KeyError, TypeError):
        return []


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


def cmd_readiness(root: Path) -> int:
    """Whether this repo is set up for the plugin, item by item, as JSON. Writes nothing.

    `required` items stop a skill until fixed; the rest the plugin works without, less well. A
    re-run on a repo that is set up is how setup says so."""
    home = main_root(root)
    cfg, warnings, parsed = load_config(root)
    items: list[dict] = []

    def item(name: str, status: str, detail: str, required: bool = False) -> None:
        items.append({"name": name, "status": status, "detail": detail, "required": required})

    ignored = work_ignored(home)
    if ignored is None:
        item("work", "n/a", "not a git repo")
    elif not ignored:
        item("work", "ok", "work/ is committed", required=True)
    else:
        item("work", "missing", IGNORED, required=True)
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
            item(f"docs.{key}", "missing", f"{rel} doesn't exist; the plugin's default stands in")
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
    if not cfg_file.is_file():
        item("drift", "n/a", "not set up yet")
    else:
        found = drift(root)
        changed = len(found["breaking"]) + len(found["refresh"])
        item(
            "drift",
            "warn" if changed else "ok",
            f"{len(found['breaking'])} breaking, {len(found['refresh'])} doc(s) to refresh, "
            f"{len(found['report'])} to look at"
            if changed
            else "setup matches this plugin's defaults",
        )

    out = {
        "ready": all(i["status"] in ("ok", "n/a") for i in items if i["required"]),
        "items": items,
        "candidates": detect_candidates(root),
        "permissions": {
            "file": str(SETTINGS),
            "rules": ALLOW_RULES,
            "missing": [r for r in ALLOW_RULES if r not in _allowed(root)],
        },
        # What setup copies from, when the repo has none of its own.
        "defaults": {key: str(DEFAULTS_DIR / name) for key, name in HOST_DOCS.items()},
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


# Setup's life after the first run. A host owns the docs setup copied from `defaults/`, so a newer
# plugin can't just overwrite them; `record` keeps a hash of each block of each default as it was
# copied, and `drift` compares three ways (the default now, that hash, the host's text) to tell
# what the plugin changed from what the host did. Neither writes a host doc: setup drafts the
# refresh, behind its one WAIT.
MANIFEST = Path(HOST_DIR) / "setup.json"
# Each [docs] key setup fills from a default, and the default it copies.
HOST_DOCS = {
    "process": "SDLC.md",
    "review": "REVIEW.md",
    "project": "PROJECT.md",
    "product": "PRODUCT.md",
    "health": "HEALTH.md",
}
# A config key a release renamed or removed: `section.old` → {"now": the key that replaced it, or
# None, "since": the version, "do": what a host does about it}. A host still setting one has a
# setting the plugin no longer reads, which is breaking. Add to it, never prune it: a host can be
# several releases behind.
RETIRED_KEYS: dict[str, dict[str, str | None]] = {
    "metrics.target_stops": {
        "now": "metrics.stop_allowance",
        "since": "2.0.0",
        "do": "Delete it. A change's target is now its gates plus `stop_allowance` (1 by default); "
        "set that instead if you want a different allowance.",
    },
}
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


def cmd_record(root: Path, created: list[str], gitignore_line: bool) -> int:
    """Write `.sdlc/setup.json`: this plugin's version, its config keys, and a hash of each block
    of each default behind a host doc, as of now. Writes nothing else. Setup runs it after every
    write, so the next drift compares against what the host was last offered."""
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
    for key, name in HOST_DOCS.items():
        rel = cfg["docs"][key]
        if rel and (root / rel).is_file():
            text = (DEFAULTS_DIR / name).read_text(encoding="utf-8")
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
    }
    (root / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote  {MANIFEST}  (plugin {manifest['version']}, {len(docs)} doc(s))")
    return 0


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
                "where": str(MANIFEST),
                "class": "unreadable",
                "detail": unreadable,
            }
        )
    downgrade = _older(plugin, version)
    if downgrade:
        out["report"].append(
            {
                "what": "manifest",
                "where": str(MANIFEST),
                "class": "downgrade",
                "detail": f"recorded by {version}, newer than this {plugin}: nothing proposed",
            }
        )

    for key, name in HOST_DOCS.items():
        rel = cfg["docs"][key]
        if not rel or not (root / rel).is_file():
            continue
        host_text = (root / rel).read_text(encoding="utf-8")
        default = doc_units((DEFAULTS_DIR / name).read_text(encoding="utf-8"))
        recorded = (manifest or {}).get("docs", {}).get(key)
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
                "where": str(cfg_file.relative_to(root)),
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
        if p.name == OLD_INBOX:
            out["report"].append(
                {
                    "what": "template",
                    "where": where,
                    "class": "renamed",
                    "detail": f"read as {INBOX} until 2.0.0: rename it to {INBOX}",
                }
            )
            continue
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
    touched = (f"{HOST_DIR}/", str(SETTINGS), ".gitignore")
    refused += [
        f"{p} has uncommitted changes: commit or discard them first"
        for p in _dirty_paths(home)
        if p.startswith(touched[0]) or p in touched[1:]
    ]
    plan: dict = {"refused": refused, "remove": _tracked(home, HOST_DIR), "edit": [], "left": []}
    left = (
        sorted(
            str(p.relative_to(home))
            for p in (home / HOST_DIR).rglob("*")
            if p.is_file() and str(p.relative_to(home)) not in plan["remove"]
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
    if rules:
        created = str(SETTINGS) in manifest.get("created", [])
        plan["edit"].append(
            {"path": str(SETTINGS), "remove_rules": rules, "remove_if_empty": created}
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
    plan["left"].append({"path": "work/", "why": "the repo's record of its changes"})
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
    nothing, and leaves `work/`, the context docs and the tracker alone."""
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
            allow = data["permissions"]["allow"]
            data["permissions"]["allow"] = [r for r in allow if r not in edit["remove_rules"]]
            # Setup's own file goes too, once its rules were all it held.
            stub = data == {"permissions": {"allow": []}}
            if edit.get("remove_if_empty") and stub:
                path.unlink()
            else:
                text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
                path.write_text(text, encoding="utf-8")
        else:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            kept = [ln for ln in lines if ln.rstrip("\r\n") != edit["remove_line"]]
            if edit.get("remove_if_empty") and not "".join(kept).strip():
                path.unlink()
            else:
                path.write_text("".join(kept), encoding="utf-8")
    return 0


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
    cfg, _, _ = load_config(root)
    base = base or cfg["git"]["base"]
    found = changed_paths(root, base) if base else None
    if found is None:
        print(
            f"⚠  no merge base with {base!r}: is this a git checkout with that branch?",
            file=sys.stderr,
        )
        return 1
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
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def print_status(a: dict) -> None:
    print(f"{a['work']} — {len(a['open'])} open, {len(a['changes'])} total   today: {a['today']}")

    print(f"\n■ Open changes: {len(a['open'])}")
    if not a["open"]:
        print("    none")
    for rec in a["open"]:
        tier = rec["tier"] if rec["tier"] is not None else "?"
        stage = rec["stage"] or "?"
        age = f"{rec['age_days']}d" if rec["age_days"] is not None else "?"
        have = (
            " ".join(
                n.removesuffix(".md") + ("~" if n in rec["unfilled"] else "")
                for n in rec["artifacts"]
            )
            or "(empty)"
        )
        undone = f"  · {len(rec['undone'])} undone" if rec.get("undone") else ""
        if rec.get("open_questions"):
            undone += f"  · {rec['open_questions']} open question(s)"
        if rec.get("behind"):
            undone += (
                f"  · behind {a.get('trunk')} by {rec['behind']}: /sdlc:ship brings it up to date"
            )
        print(f"    {rec['id']}  T{tier} {stage:<8} {age:>4}  {rec['slug']:<28} {have}{undone}")
        if rec["title"]:
            print(f"                              {rec['title']}")
    if any(rec["unfilled"] for rec in a["open"]):
        print("    ~ = scaffolded from the template, not written yet")

    shipped = [r for r in a["changes"] if r["stage"] == "shipped"]
    print(f"\n■ Shipped: {len(shipped)}")
    for rec in shipped[-10:]:
        print(f"    {rec['id']}  {rec['slug']:<28} {rec['updated']}")
    if len(shipped) > 10:
        print(f"    (+{len(shipped) - 10} more)")
    if not shipped:
        print("    none")

    if a.get("ready"):
        print(f"\n■ Ready to close: {len(a['ready'])}")
        for rec in a["ready"]:
            mark = "  (dropped)" if rec.get("kind") == "dropped" else ""
            if rec.get("behind") and rec.get("kind") != "dropped":
                mark = f"  (behind {a.get('trunk')} by {rec['behind']}: rebase and ship again)"
            print(f"    {rec['id']}  {rec['slug']:<28} → /sdlc:close {rec['id']}{mark}")

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
            print(f"    since {rel['since']} → {rel['next']} ({rel['bump']})  /sdlc:release")
        # Warned about, never a problem: an overdue shim mustn't fail every change's gate.
        for kind, state in SHIM_STATES.items():
            for s in shims.get(kind, []):
                print(f"    ⚠  shim {s['name']}{state}: remove in {s['remove_in']} ({s['where']})")
        for c in rel["changes"]:
            landed = "" if c["closed"] else "  (landed, not closed)"
            print(f"    {c['id']}  {c['slug']:<28} {c['impact'] or '?'}{landed}")

    # Left out when the registers hold nothing to put forward, as Unreleased is.
    nxt = a.get("next_up")
    if nxt and (nxt["items"] or nxt["done_milestones"] or nxt["warnings"]):
        print(f"\n■ Next up: {len(nxt['items'])}")
        for item in nxt["items"][:NEXT_SHOWN]:
            age = f"{item['age_days']}d" if item["age_days"] is not None else "?"
            print(f"    {item['label']}  {item['title']}  ({age})  → {item['command']}")
        if len(nxt["items"]) > NEXT_SHOWN:
            print(f"    (+{len(nxt['items']) - NEXT_SHOWN} more)")
        for m in nxt["done_milestones"]:
            print(f"    {m} has nothing left in its groups: /sdlc:retro decides whether it's done")
        for w in nxt["warnings"]:
            print(f"    ⚠  {w}")

    # Nudges, not gates: one line each, only when it applies, and nothing runs. Never a problem:
    # `check --strict` is a gate, and a plugin update mustn't fail every host's.
    if a.get("setup"):
        print(f"\n■ Setup: {a['setup']}")
    due = a.get("retro_due")
    if due and due["due"]:
        print(f"\n■ Retro due: {'; '.join(due['why'])}  /sdlc:retro")

    print(f"\n■ Problems: {len(a['problems'])}")
    if not a["problems"]:
        print("    none ✅")
    for pr in a["problems"]:
        print(f"    ⚠  {pr['dir']}: {pr['detail']}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Track the change artifacts under work/ (see the repo's process doc)."
    )
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("status", help="what's open, at what stage (the default)")

    p_new = sub.add_parser("new", help="scaffold the next change folder")
    p_new.add_argument("slug", help="kebab-case name, e.g. reopen-drafts")
    p_new.add_argument(
        "--tier",
        type=int,
        choices=[1, 2],
        default=1,
        help="1 = intent only (default), 2 = intent + spec + plan",
    )
    p_new.add_argument("--title", help="H1 for the artifacts (default: the slug, de-hyphenated)")
    p_new.add_argument(
        "--worktree",
        action="store_true",
        help="create the change in its own worktree and branch, .claude/worktrees/NNN-slug",
    )
    p_new.add_argument("--base", help="what --worktree branches from (git.base)")

    p_check = sub.add_parser("check", help="audit artifacts against declared tier/stage")
    p_check.add_argument("--strict", action="store_true", help="exit 1 if any problem is found")

    p_ship = sub.add_parser("ship", help="stamp the change shipped, in place")
    p_ship.add_argument("id", help="the 3-digit id, e.g. 001")
    p_ship.add_argument(
        "--leave", action="append", default=[], metavar="PATH",
        help="a path not to stage, to commit apart; repeatable",
    )  # fmt: skip

    sub.add_parser("next", help="the id `new` would allocate now; writes nothing")

    p_undone = sub.add_parser(
        "undone", help="a change's unticked `- [ ]` items in notes.md, as JSON; writes nothing"
    )
    p_undone.add_argument("id", help="the 3-digit id, e.g. 025")

    p_entry = sub.add_parser(
        "next-entry", help="the id the next work/inbox.md entry would take today; writes nothing"
    )
    p_entry.add_argument("--count", type=int, default=1, help="this many ids, one per line")

    p_nits = sub.add_parser(
        "nits", help="the open [nit] entries in work/inbox.md, as JSON; writes nothing"
    )
    p_nits.add_argument("--touching", nargs="*", help="only those these paths touch")
    p_nits.add_argument("--change", help="only those this change's diff against main touches")

    p_checks = sub.add_parser(
        "checks", help="a change's acceptance checks in checks.md, as JSON; runs nothing"
    )
    p_checks.add_argument("id", help="the 3-digit id, e.g. 025")

    p_accept = sub.add_parser(
        "accept", help="run a change's acceptance checks from its checkout; never pre-approved"
    )
    p_accept.add_argument("id", help="the 3-digit id, e.g. 025")

    p_drop = sub.add_parser(
        "drop", help="stamp the change dropped and commit its folder on its branch, for close"
    )
    p_drop.add_argument("id", nargs="?", help="the change, e.g. 023 (default: this checkout's)")
    p_drop.add_argument("--check", action="store_true", help="preconditions only, write nothing")

    p_base = sub.add_parser(
        "base", help="bring a change's branch up to date with main in its worktree, or refuse"
    )
    p_base.add_argument("id", nargs="?", help="the change, e.g. 023 (default: this checkout's)")

    p_close = sub.add_parser(
        "close",
        help="land a shipped change on main, or record a dropped one there; mirror it, remove its "
        "folder, worktree and branch",
    )
    p_close.add_argument("id", nargs="?", help="the change, e.g. 023 (default: this checkout's)")
    p_close.add_argument("--check", action="store_true", help="preconditions only, write nothing")

    p_sync = sub.add_parser(
        "sync", help="rewrite the change's tracker issue from its artifacts as they are now"
    )
    p_sync.add_argument("id", nargs="?", help="the change, e.g. 023 (default: this checkout's)")

    p_lookup = sub.add_parser(
        "lookup", help="the values the project doc's issue fields can take, as JSON; writes nothing"
    )
    p_lookup.add_argument(
        "field", nargs="*", help="milestone, project, assignees (default: all on)"
    )

    sub.add_parser("config", help="the host's .sdlc/config.toml, resolved, as JSON; writes nothing")
    sub.add_parser(
        "readiness", help="whether this repo is set up for the plugin, as JSON; writes nothing"
    )

    sub.add_parser(
        "drift", help="what changed under this repo's setup since it ran, as JSON; writes nothing"
    )
    p_record = sub.add_parser(
        "record", help="write .sdlc/setup.json: the defaults setup offered, for the next drift"
    )
    p_record.add_argument("--created", nargs="*", default=[], help="the paths setup created")
    p_record.add_argument(
        "--gitignore-line", action="store_true", help=f"setup added {WORKTREES_LINE} to .gitignore"
    )
    p_reset = sub.add_parser("reset", help="delete one .sdlc/templates/ override")
    p_reset.add_argument("name", help="the template's file name, e.g. intent.md")
    p_reset.add_argument("--check", action="store_true", help="preconditions only, write nothing")
    p_uninstall = sub.add_parser(
        "uninstall", help="remove what setup wrote, refusing while any change is live"
    )
    p_uninstall.add_argument("--check", action="store_true", help="the plan only, write nothing")

    p_context = sub.add_parser(
        "context", help="the context docs this checkout's diff could have made wrong, as JSON"
    )
    p_context.add_argument("--base", help="what the diff is taken against (git.base)")

    sub.add_parser(
        "unreleased", help="the changes landed since the last release tag, as JSON; writes nothing"
    )
    p_release = sub.add_parser(
        "release", help="bump the version files, commit `Release X.Y.Z` and tag it, locally"
    )
    p_release.add_argument("--check", action="store_true", help="the plan only, write nothing")
    p_release.add_argument("--version", help="release as X.Y.Z instead of the computed version")
    p_publish = sub.add_parser(
        "publish", help="push main and the release tag, then run release.publish"
    )
    p_publish.add_argument("--check", action="store_true", help="preconditions only, push nothing")
    sub.add_parser(
        "retro", help="what the retrospective counts since the last one, as JSON; writes nothing"
    )
    sub.add_parser(
        "retro-commit", help="commit the direction doc and work/inbox.md as `Retrospective <date>`"
    )

    args = ap.parse_args()
    root = repo_root()
    # State, the lock and the worktree list belong to the main checkout; change folders are found
    # from here in every checkout (`change_dirs`). `config` reads this checkout's .sdlc/, which a
    # change's branch may be editing.
    home = main_root(root)
    if args.cmd in OWN_SCRIPT_CMDS and (own := _own_script(root)):
        code = _run_own(own, sys.argv[1:])
        if code is not None:
            return code
    if args.cmd == "config":
        return cmd_config(root)
    if args.cmd == "context":
        return cmd_context(root, args.base)
    if args.cmd == "readiness":
        return cmd_readiness(root)
    if args.cmd == "drift":
        return cmd_drift(root)
    if args.cmd == "record":
        return cmd_record(root, args.created, args.gitignore_line)
    if args.cmd == "reset":
        return cmd_reset(root, args.name, args.check)
    if args.cmd == "uninstall":
        return cmd_uninstall(root, args.check)
    if args.cmd == "new":
        return cmd_new(root, args.slug, args.tier, args.title, args.worktree, args.base)
    if args.cmd == "ship":
        return cmd_ship(root, args.id, args.leave)
    if args.cmd == "next":
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
    if args.cmd == "next-entry":
        for entry_id in next_entry_ids(home, date.today().isoformat(), max(args.count, 1)):
            print(entry_id)
        return 0
    if args.cmd == "undone":
        return cmd_undone(root, args.id)
    if args.cmd == "nits":
        return cmd_nits(root, args.touching, args.change)
    if args.cmd == "checks":
        return cmd_checks(root, args.id)
    if args.cmd == "accept":
        return cmd_accept(root, args.id)
    if args.cmd == "drop":
        return cmd_drop(root, args.id, args.check)
    if args.cmd == "base":
        return cmd_base(root, args.id)
    if args.cmd == "close":
        return cmd_close(root, args.id, args.check)
    if args.cmd == "unreleased":
        return cmd_unreleased(root)
    if args.cmd == "release":
        return cmd_release(root, args.check, args.version)
    if args.cmd == "publish":
        return cmd_publish(root, args.check)
    if args.cmd == "retro":
        return cmd_retro(root)
    if args.cmd == "retro-commit":
        return cmd_retro_commit(root)
    if args.cmd == "sync":
        return cmd_sync(root, args.id)
    if args.cmd == "lookup":
        return cmd_lookup(root, args.field)

    a = analyze(root)
    if args.cmd == "check":
        print(f"■ Problems: {len(a['problems'])}")
        for pr in a["problems"]:
            print(f"    ⚠  {pr['dir']}: {pr['detail']}")
        if not a["problems"]:
            print("    none ✅")
        return 1 if (args.strict and a["problems"]) else 0

    a["ready"] = ready_to_close(root)
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
    open_ids = [f"{r['id']}-{r['slug']}" for r in a["open"]]
    a["release"] = unreleased(home, cfg, open_ids, read=bool(cfg["release"]["version_files"]))
    a["retro_due"] = retro_due(home, cfg)
    # Here, not in `analyze()`: `check` never reads the registers for what comes next.
    a["next_up"] = next_up(home, cfg, a["open"], date.fromisoformat(a["today"]))
    a["setup"] = setup_nudge(root)
    print_status(a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
