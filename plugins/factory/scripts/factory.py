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
ROLES = ("spec-writer", "builder", "code", "security", "test", "approver")
REVIEWERS = ("code", "security", "test")
DEFAULTS: dict = {"reviewers": ["code", "security", "test"], "rounds": 3, "models": {}}
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
> disposition, carried to a `work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
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
    cfg = {"reviewers": list(DEFAULTS["reviewers"]), "rounds": DEFAULTS["rounds"], "models": {}}
    path = root / CONFIG_FILE
    if not path.is_file():
        return cfg, []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        return cfg, [f"{CONFIG_FILE} won't parse: {e}"]
    warnings = [f"unknown key {key}" for key in data if key not in DEFAULTS]
    reviewers = data.get("reviewers", cfg["reviewers"])
    if not isinstance(reviewers, list) or not all(isinstance(r, str) for r in reviewers):
        warnings.append("reviewers must be a list of names")
    else:
        unknown = [r for r in reviewers if r not in REVIEWERS]
        warnings += [f"unknown reviewer {r!r}: one of {', '.join(REVIEWERS)}" for r in unknown]
        known = [r for r in dict.fromkeys(reviewers) if r in REVIEWERS]
        if known:
            cfg["reviewers"] = known
        else:
            warnings.append("no known reviewer is configured, so the defaults run")
    rounds = data.get("rounds", cfg["rounds"])
    if isinstance(rounds, int) and not isinstance(rounds, bool) and 1 <= rounds <= MAX_ROUNDS:
        cfg["rounds"] = rounds
    else:
        warnings.append(f"rounds must be a whole number from 1 to {MAX_ROUNDS}")
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
    folder = root / "work" / branch
    if not (folder / "intent.md").is_file():
        return None, f"work/{branch}/intent.md doesn't exist on this branch"
    return folder, None


def max_runs(cfg: dict) -> int:
    """The most agent runs one build can take: the builder, the approver, and each round's
    reviewers and builder resume. An upper bound to show before a person approves the cost."""
    return 2 + cfg["rounds"] * (len(cfg["reviewers"]) + 1)


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
    """Every `reviews/round-<N>/`, in order: each configured reviewer's verdict and the changes it
    asks for, and whether the round is complete. A file whose first line isn't a verdict is a
    problem, never a guess."""
    base = folder / "reviews"
    found = []
    problems = []
    dirs = [p for p in base.glob("round-*") if p.is_dir() and p.name[6:].isdigit()]
    for path in sorted(dirs, key=lambda p: int(p.name[6:])):
        n = int(path.name[6:])
        reviews = {}
        for role in reviewers:
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
            reviews[role] = {"verdict": m.group(1), "changes": changes}
        found.append({"round": n, "reviews": reviews, "complete": set(reviews) == set(reviewers)})
    return found, problems


def build_round(folder: Path) -> int:
    """The newest builder report's round, `build/round-<N>.md`; 0 before the first."""
    names = [p.stem[6:] for p in (folder / "build").glob("round-*.md")]
    return max((int(n) for n in names if n.isdigit()), default=0)


def read_decision(folder: Path) -> tuple[str | None, str | None]:
    path = folder / "decision.md"
    if not path.is_file():
        return None, None
    lines = path.read_text(encoding="utf-8").splitlines()
    m = DECISION_RE.match(lines[0]) if lines else None
    if not m:
        return None, "decision.md doesn't open with DECISION: READY or DECISION: ESCALATE"
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
    - `rework`: resume the builder with `round`'s changes; its report is `build/round-<round+1>.md`.
    - `approve`: carry what's unresolved to notes.md and run the approver.
    - `decide`: a blocking decision in `decisions.md` is waiting for the person (`pending`).
    - `done`: the decision is in.
    - `stop`: a problem, or `HEAD` moved: an agent committed, which none may.

    What has been built and what has been reviewed are compared by round: a builder report newer
    than the last complete review round is always reviewed, whether it came from a rework or from
    an answer the person gave, so no build reaches the approver unreviewed.

    Run `decisions` first: this reads the ledger as it stands, and writes nothing.
    """
    cfg, warnings = load_config(root)
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    rounds, problems = read_rounds(folder, cfg["reviewers"])
    decision, problem = read_decision(folder)
    problems += [problem] if problem else []
    now = _git(root, "rev-parse", "--short", "HEAD")
    moved = bool(head) and now is not None and not now.startswith(head) and not head.startswith(now)
    out: dict = {"change": folder.name, "rounds": rounds, "decision": decision, "head": now}
    out.update(head_moved=moved, problems=problems, warnings=warnings, round=None, missing=[])
    out["exhausted"] = False
    ledger = read_ledger(folder)
    out["pending"] = [d["id"] for d in ledger if d["kind"] == "blocking" and not d["decided"]]
    out["assumed"] = [d["id"] for d in ledger if d["kind"] == "default" and not d["decided"]]
    last = rounds[-1] if rounds else None
    built = build_round(folder)
    out["built"] = built
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
        out["next"], out["round"], out["missing"] = "review", built, list(cfg["reviewers"])
    elif not last["complete"]:
        out["next"], out["round"] = "review", last["round"]
        out["missing"] = [r for r in cfg["reviewers"] if r not in last["reviews"]]
    elif any(v["verdict"] == "CHANGES" for v in last["reviews"].values()):
        if last["round"] < cfg["rounds"]:
            out["next"], out["round"] = "rework", last["round"]
        else:
            out["next"], out["round"], out["exhausted"] = "approve", last["round"], True
    else:
        out["next"], out["round"] = "approve", last["round"]
    return emit(out)


def cmd_carry(root: Path, ident: str) -> int:
    """Each change the last complete round still asks for, as an unticked `- [ ]` line in
    notes.md, so `/sdlc:ship` must give it a disposition. Once only: a line already there, ticked
    or not, isn't added again."""
    cfg, _ = load_config(root)
    folder, refusal = find_change(root, ident)
    if refusal:
        return emit({"refusals": [refusal]}, 1)
    rounds, _ = read_rounds(folder, cfg["reviewers"])
    done = [r for r in rounds if r["complete"]]
    wanted = []
    if done:
        for role, review in done[-1]["reviews"].items():
            if review["verdict"] == "CHANGES":
                wanted += [f"{role}: {text}" for text in review["changes"]]
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
    p_stage = sub.add_parser("stage", help="set the intent's stage: line, in place")
    p_stage.add_argument("id")
    p_stage.add_argument("stage")
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
    return cmd_stage(root, args.id, args.stage)


if __name__ == "__main__":
    sys.exit(main())
