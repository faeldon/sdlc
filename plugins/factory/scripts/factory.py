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

It doesn't call `sdlc.py`. Installed from the marketplace, each plugin is cached on its own, so
the factory's copy has no `sdlc.py` beside it. It reads the change folder itself, the same way:
frontmatter by line, edited by line, never round-tripped (`sdlc.py`'s `stamp_shipped` rule).

    uv run --script factory.py config
    uv run --script factory.py start 008 --for build
    uv run --script factory.py decisions 008
    uv run --script factory.py verdicts 008 --head 1a2b3c4
    uv run --script factory.py carry 008
    uv run --script factory.py stage 008 test

Every command prints JSON and writes only where its name says: `decisions` to `decisions.md`,
`carry` to `notes.md`, `stage` to `intent.md`. Nothing is written outside the change's folder, and
nothing under `.git/`.

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
import re
import subprocess
import sys
import tomllib
from datetime import date
from pathlib import Path

# The change-folder names `sdlc.py` gives: three digits at least, then the slug.
DIR_RE = re.compile(r"^(\d{3,})-([a-z0-9][a-z0-9-]*)$")
# Every role a model can be set for, and the reviewers a repo can choose among.
ROLES = ("spec-writer", "builder", "code", "security", "test", "behaviour", "verifier", "approver")
REVIEWERS = ("code", "security", "test", "behaviour")
# `reviewers` and `rounds` are the full depth; `light` the one a diff touching no path in the
# base branch's `[review] sensitive` gets, once a host lists any.
DEFAULTS: dict = {
    "reviewers": ["code", "security", "test", "behaviour"],
    "rounds": 3,
    "light": {"reviewers": ["code"], "rounds": 2},
    "models": {},
}
MAX_ROUNDS = 5
# The stages a factory step moves a change between. `shipped` stays `sdlc ship`'s alone.
STAGES = ("plan", "design", "build", "test")
# What each step may start from. A build left at `stage: build` by a run that stopped resumes.
STARTS = {
    "spec": {(2, "plan")},
    "build": {(2, "design"), (2, "build"), (1, "plan"), (1, "build")},
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
# What an approver must write when the rounds ran out with changes still kept.
RECONSIDER = "## Reconsider the approach"
# What a builder report and a behaviour check end with: each command run (`$ <command>`), the tail
# of its output, and `exit: <n>`. A result claimed without one is a stop, never taken on trust.
EVIDENCE = "## Evidence"
EXIT_RE = re.compile(r"^\s*exit:\s*\d+\s*$")
# The reviewers whose replies owe evidence too: the ones that run the change.
RUNS_THE_CHANGE = ("behaviour",)
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
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip()


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
    path = root / CONFIG_FILE
    if not path.is_file():
        return cfg, []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        return cfg, [f"{CONFIG_FILE} won't parse: {e}"]
    warnings = [f"unknown key {key}" for key in data if key not in DEFAULTS]
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
    return cfg, warnings


def _depth_keys(data: dict, into: dict, prefix: str, warnings: list[str]) -> None:
    """A depth's `reviewers` and `rounds` from `data` into `into`, the top level's or `[light]`'s,
    each bad value a warning that leaves the default in place."""
    reviewers = data.get("reviewers", into["reviewers"])
    if not isinstance(reviewers, list) or not all(isinstance(r, str) for r in reviewers):
        warnings.append(f"{prefix}reviewers must be a list of names")
    else:
        unknown = [r for r in reviewers if r not in REVIEWERS]
        warnings += [
            f"unknown reviewer {r!r} in {prefix}reviewers: one of {', '.join(REVIEWERS)}"
            if prefix
            else f"unknown reviewer {r!r}: one of {', '.join(REVIEWERS)}"
            for r in unknown
        ]
        known = [r for r in dict.fromkeys(reviewers) if r in REVIEWERS]
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
    """The change folder this checkout's branch holds, or why not. A factory step runs in the
    change's own worktree, where `/sdlc:intent` put the session, so its agents work there."""
    branch = _git(root, "branch", "--show-current") or ""
    if not names_change(branch, ident):
        return None, (
            f"run it from change {ident}'s own worktree: this checkout is on {branch or '?'!r}, "
            "not that change's NNN-slug branch"
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
    each round's reviewers, verifier and builder resume. An upper bound to show before a person
    approves the cost, whatever depth the diff turns out to need."""
    return 2 + cfg["rounds"] * (len(cfg["reviewers"]) + 2)


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


def depth(root: Path, cfg: dict, rounds: list[dict]) -> dict:
    """The depth this run reviews at, from the diff as it stands: `full` with no sensitive list
    (every run, as before there was a choice), when the diff touches a listed path, or once any
    round ran beyond `[light]` (a run never lightens); `light` otherwise. Writes nothing."""
    base = _base(root)
    listed = _sensitive(root, base) if base else []
    changed = _changed_paths(root, base) if base else []
    hit = risk_paths(changed, listed)
    light = cfg["light"]
    beyond = any(
        r["round"] > light["rounds"] or set(r["reviews"]) - set(light["reviewers"]) for r in rounds
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
    out.update(change=folder.name, folder=str(folder), tier=tier, stage=stage)
    if (tier, stage) not in STARTS[purpose]:
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
                problems.append(
                    f"reviews/round-{n}/{role}.md doesn't open with VERDICT: PASS or "
                    "VERDICT: CHANGES"
                )
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


def read_verified(path: Path, n: int, reviews: dict) -> tuple[dict | None, list[str]]:
    """The verifier's `KEPT` and `DROPPED` lines for round `n`, or None before it answered. Every
    `CHANGE:` the round's `CHANGES` verdicts ask for is answered exactly once, and every answer
    names one: anything else is a problem, so no change is reworked or dropped unread."""
    if not path.is_file():
        return None, []
    kept, dropped = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if m := KEPT_RE.match(line):
            kept.append({"role": m.group(1), "change": m.group(2)})
        elif m := DROPPED_RE.match(line):
            change, sep, why = m.group(2).rpartition(DROP_WHY)
            text = change if sep else m.group(2)
            dropped.append({"role": m.group(1), "change": text.strip(), "why": why.strip()})
    asked = [
        (role, c) for role, r in reviews.items() if r["verdict"] == "CHANGES" for c in r["changes"]
    ]
    answered = [(a["role"], a["change"]) for a in kept + dropped]
    where = f"reviews/round-{n}/{VERIFIED}"
    problems = [
        f"{where} answers {role}: {c} {answered.count((role, c))} times, not once"
        for role, c in dict.fromkeys(asked)
        if answered.count((role, c)) != 1
    ]
    problems += [
        f"{where} answers {role}: {c}, which no review of round {n} asks for"
        for role, c in dict.fromkeys(answered)
        if (role, c) not in asked
    ]
    return {"kept": kept, "dropped": dropped}, problems


def _rounds_at_depth(root: Path, folder: Path, cfg: dict) -> tuple[list[dict], list[str], dict]:
    """The rounds, their problems and the run's depth, each round's `complete` judged against the
    reviewers that depth expects."""
    rounds, problems = read_rounds(folder, cfg["reviewers"])
    run = depth(root, cfg, rounds)
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
        path.write_text(body + "".join(new_lines), encoding="utf-8")
    pending = [d["id"] for d in ledger if d["kind"] == "blocking" and not d["decided"]]
    assumed = [d["id"] for d in ledger if d["kind"] == "default" and not d["decided"]]
    return emit(
        {"change": folder.name, "decisions": ledger, "added": added}
        | {"pending": pending, "assumed": assumed}
    )


def cmd_verdicts(root: Path, ident: str, head: str | None) -> int:
    """The review rounds and the decision so far, and the step the loop takes next:

    - `build`: no builder report yet: run the builder (`build/round-1.md`).
    - `review`: run the reviewers for `round` (all of them, or the `missing` ones).
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

    Run `decisions` first: this reads the ledger as it stands, and writes nothing.

    Beside the step: the run's `depth` (`depth()`), `reworked` (the paths the round to review
    changed since the last, from the snapshots), `settled` (what earlier rounds answered, never
    raised again), and for the verifier, `repeats` (a change raised again) and `untouched` (one on
    a path the change doesn't touch: pre-existing, never reworked).
    """
    cfg, warnings = load_config(root)
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    rounds, problems, run = _rounds_at_depth(root, folder, cfg)
    last = rounds[-1] if rounds else None
    changes = last and any(v["verdict"] == "CHANGES" for v in last["reviews"].values())
    kept = bool(last and last["verified"] and last["verified"]["kept"])
    exhausted = bool(last and last["complete"] and changes and kept)
    exhausted = exhausted and last["round"] >= run["rounds"]
    decision, problem = read_decision(folder, exhausted)
    problems += [problem] if problem else []
    now = _git(root, "rev-parse", "--short", "HEAD")
    moved = bool(head) and now is not None and not now.startswith(head) and not head.startswith(now)
    out: dict = {"change": folder.name, "rounds": rounds, "decision": decision, "head": now}
    out.update(head_moved=moved, problems=problems, warnings=warnings, round=None, missing=[])
    out["exhausted"] = False
    out.update({k: run[k] for k in ("depth", "sensitive", "why", "reviewers")})
    out["limit"] = run["rounds"]
    ledger = read_ledger(folder)
    out["pending"] = [d["id"] for d in ledger if d["kind"] == "blocking" and not d["decided"]]
    out["assumed"] = [d["id"] for d in ledger if d["kind"] == "default" and not d["decided"]]
    built = build_round(folder)
    out["built"] = built
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
    if built:
        report = folder / "build" / f"round-{built}.md"
        problems += read_evidence(report.read_text(encoding="utf-8"), f"build/round-{built}.md")
    for r in rounds:
        for role in RUNS_THE_CHANGE:
            reply = folder / "reviews" / f"round-{r['round']}" / f"{role}.md"
            if role in r["reviews"]:
                where = f"reviews/round-{r['round']}/{role}.md"
                problems += read_evidence(reply.read_text(encoding="utf-8"), where)
    if moved:
        problems.append(f"HEAD moved from {head} to {now}: no agent may commit")
    if last and last["round"] > built:
        problems.append(f"reviews/round-{last['round']}/ has no build/round-{last['round']}.md")
    if problems:
        out["next"] = "stop"
    elif out["pending"]:
        out["next"] = "decide"
    elif decision:
        out["next"] = "done"
    elif built == 0:
        out["next"], out["round"] = "build", 1
    elif last is None or last["round"] < built:
        out["next"], out["round"], out["missing"] = "review", built, list(run["reviewers"])
    elif not last["complete"]:
        out["next"], out["round"] = "review", last["round"]
        out["missing"] = [r for r in run["reviewers"] if r not in last["reviews"]]
    elif changes and last["verified"] is None:
        out["next"], out["round"] = "verify", last["round"]
    elif kept and last["round"] < run["rounds"]:
        out["next"], out["round"] = "rework", last["round"]
    else:
        out["next"], out["round"], out["exhausted"] = "approve", last["round"], exhausted
    return emit(out)


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
        notes.write_text(text, encoding="utf-8")
    return emit({"change": folder.name, "notes": str(notes), "added": added})


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
    lines = []
    for p in _changed_paths(root, base):
        file = root / p
        digest = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else "deleted"
        lines.append(f"{digest}  {p}\n")
    path = snapshot_path(folder, n)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")
    rel = str(path.relative_to(root))
    return emit({"change": folder.name, "snapshot": rel, "paths": len(lines)})


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
    intent.write_text(text, encoding="utf-8")
    return emit({"change": folder.name, "stage": stage})


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


def cmd_report_dir(root: Path, kind: str) -> int:
    """A fresh run folder under `.sdlc/reports/`, which ignores itself, for an eval or a review to
    write into: `<kind>-<date>-<n>/`."""
    reports = root / REPORTS
    reports.mkdir(parents=True, exist_ok=True)
    ignore = reports / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("*\n", encoding="utf-8")
    stamp = f"{kind}-{date.today().isoformat()}"
    n = 1 + sum(1 for p in reports.glob(f"{stamp}-*") if p.is_dir())
    run = reports / f"{stamp}-{n}"
    run.mkdir()
    return emit({"run": str(run.relative_to(root))})


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
    report.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return emit({"report": str(report.relative_to(root)), "reviewers": scores, "bugs": bugs})


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
    ap = argparse.ArgumentParser(description="The sdlc-factory layer's mechanism.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("config", help=f"{CONFIG_FILE} over the defaults, as JSON")
    p_start = sub.add_parser("start", help="whether a factory step may start on the change")
    p_start.add_argument("id")
    p_start.add_argument("--for", dest="purpose", choices=sorted(STARTS), required=True)
    p_verdicts = sub.add_parser("verdicts", help="the review rounds, the decision, the next step")
    p_verdicts.add_argument("id")
    p_verdicts.add_argument("--head", help="HEAD as `start` printed it; a move is a stop")
    p_decisions = sub.add_parser("decisions", help="the agents' decisions into decisions.md")
    p_decisions.add_argument("id")
    p_carry = sub.add_parser("carry", help="unresolved changes to notes.md as `- [ ]` items")
    p_carry.add_argument("id")
    p_snapshot = sub.add_parser("snapshot", help="hash what a round's build left, for the next")
    p_snapshot.add_argument("id")
    p_snapshot.add_argument("--round", dest="round", type=int, required=True)
    p_stage = sub.add_parser("stage", help="set the intent's stage: line, in place")
    p_stage.add_argument("id")
    p_stage.add_argument("stage")
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
    if args.cmd == "config":
        return cmd_config(root)
    if args.cmd == "start":
        return cmd_start(root, args.id, args.purpose)
    if args.cmd == "verdicts":
        return cmd_verdicts(root, args.id, args.head)
    if args.cmd == "decisions":
        return cmd_decisions(root, args.id)
    if args.cmd == "carry":
        return cmd_carry(root, args.id)
    if args.cmd == "snapshot":
        return cmd_snapshot(root, args.id, args.round)
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
