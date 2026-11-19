"""run_state — the build loop's one reading, apart from `factory.py`, where every change meets it.

What lives here is `loop_state()`, the one reading of a build run that `verdicts` prints and
`agent` builds its prompt from, and the helpers only it calls: the early stop (`early_stop()`),
what earlier rounds settled (`settled()`), the untouched changes (`_untouched()`), the cheap nits a
rework is handed (`cheap_nits()`), what a rework changed (`reworked()`), whether the approver's
reply disagrees with itself (`decision_preamble()`) and the gate as it stands (`_gate_state()`,
`read_gate()`). It decides from the rounds alone, reading no state file but
`runs/mended`; it writes nothing, and runs no process but the `git` calls `factory._git` makes for
it: never `claude`, never a host's command.

The line between here and `factory.py` is a rule `tests/test_modules.py` holds: a function lives
here when it is `loop_state` or only code here calls it; anything `factory.py` or `landing.py`
also calls stays there. So `factory.py` keeps every constant, regex and path this code reads
(`factory_records.py`'s copies are pinned against `factory.py`'s globals), `cmd_verdicts` and the
records it writes (`stop_text()`, `step_text()`, `read_step()`, which the board's copies follow),
and `cmd_agent`'s task building.

`factory.py` loads this file by path and binds `factory` here to a live view of its own names right
after, as it does `landing.py` (the factory never imports `sdlc.py`, and neither does this file).
Every name this code shares with the rest of the script is read as `factory.<name>` when it runs,
so a test's stand-in on the loaded `factory` module reaches it; `factory.py` calls
`run_state.loop_state`, and the tests `factory.run_state.<name>`. `factory` is unbound while this
file loads, so nothing evaluated at load may read it.
"""

from __future__ import annotations

from pathlib import Path

factory = None  # factory.py's own names, bound by factory.py right after it loads this file


def reworked(folder: Path, n: int) -> list[str] | None:
    """The paths round `n`'s build changed since round `n - 1`'s, by their snapshots: every
    changed path in round 1. None when a snapshot is missing, so the reviewers read it all."""
    now = factory.read_snapshot(folder, n)
    if now is None:
        return None
    if n == 1:
        return sorted(now)
    before = factory.read_snapshot(folder, n - 1)
    if before is None:
        return None
    return sorted(p for p in set(now) | set(before) if now.get(p) != before.get(p))


def _untouched(root: Path, change: str, changed: list[str]) -> bool:
    """Whether a `CHANGE:` is about code the change didn't touch: its path exists here and isn't
    among `changed`. A path that doesn't exist yet is one the change is asked to create, never
    pre-existing; with no changed paths known (no base branch), nothing is called untouched."""
    path = factory._change_path(change)
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


def decision_preamble(folder: Path) -> bool:
    """Whether `decision.md` holds `DECISION:` lines that disagree, none of them first:
    `preamble()`'s rule for the approver's reply, which the run may mend once by asking again."""
    return factory._disagrees(folder / "decision.md", factory.DECISION_RE)


def loop_state(root: Path, ident: str, head: str | None) -> tuple[dict, str | None]:
    """What `verdicts` prints, or why not: one reading of the loop, so the step `verdicts` names
    and the prompt `agent` sends for it are made from the same state."""
    cfg, warnings = factory.load_config(root)
    folder, refusal = factory.find_change(root, ident)
    if refusal:
        return {}, refusal
    rounds, problems, run = factory._rounds_at_depth(root, folder, cfg)
    last = rounds[-1] if rounds else None
    changes = last and any(v["verdict"] == "CHANGES" for v in last["reviews"].values())
    kept = bool(last and last["verified"] and last["verified"]["kept"])
    # A restarted or upgraded run's rounds count from its restart or its upgrade, the newer: round
    # R or P is its first.
    restart, upgrade = run["restart"], run["upgrade"]
    first = max(restart["round"] if restart else 1, upgrade["round"] if upgrade else 1)
    exhausted = bool(last and last["complete"] and changes and kept)
    exhausted = exhausted and last["round"] - first + 1 >= run["rounds"]
    stuck, untestable = early_stop(folder, rounds, first)
    exhausted = exhausted or bool(stuck or untestable)
    decision, problem = factory.read_decision(folder, exhausted)
    problems += [problem] if problem else []
    now = factory._git(root, "rev-parse", "--short", "HEAD")
    moved = bool(head) and now is not None and not now.startswith(head) and not head.startswith(now)
    out: dict = {"change": folder.name, "rounds": rounds, "decision": decision, "head": now}
    out.update(head_moved=moved, problems=problems, warnings=warnings, round=None, missing=[])
    out["mend"] = []
    out.update(exhausted=False, stuck=stuck, untestable=untestable)
    out.update({k: run[k] for k in ("depth", "sensitive", "why", "reviewers")})
    out["limit"] = first - 1 + run["rounds"]
    out["first"] = first
    out["restart"] = restart
    out.update(upgraded=upgrade, upgrading=None, written=None)
    meta = factory.frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    tier, stage = factory.change_tier(folder), meta.get("stage") or None
    ledger = factory.read_ledger(folder)
    out["pending"] = [d["id"] for d in ledger if d["kind"] == "blocking" and d["open"]]
    out["assumed"] = [d["id"] for d in ledger if d["kind"] == "default" and d["open"]]
    built = factory.build_round(folder)
    out["built"] = built
    # A build no review round has read yet is gated first; a reviewed one never is again.
    unreviewed = bool(built) and (last is None or last["round"] < built)
    gate, out["gate_why"] = _gate_state(root, folder, built) if built else (None, None)
    out["gate"] = gate
    if gate and unreviewed and gate["current"] == "FAIL" and gate["fails"] > factory.GATE_FIXES:
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
    # `## Evidence`, or verdict lines that disagree in the last round, each by the role that mends.
    mendable: dict[str, list[str]] = {}
    if built:
        report = folder / "build" / f"round-{built}.md"
        found = factory.read_evidence(report.read_text(encoding="utf-8"), f"build/round-{built}.md")
        mendable["builder"] = found
    for r in rounds:
        for role in factory.RUNS_THE_CHANGE:
            reply = folder / "reviews" / f"round-{r['round']}" / f"{role}.md"
            if role in r["reviews"]:
                where = f"reviews/round-{r['round']}/{role}.md"
                found = factory.read_evidence(reply.read_text(encoding="utf-8"), where)
                mendable.setdefault(role, []).extend(found)
    problems += [p for found in mendable.values() for p in found]
    for role in factory.REVIEWERS if last else ():
        if factory.preamble(folder / "reviews" / f"round-{last['round']}" / f"{role}.md"):
            mendable.setdefault(role, []).append(factory._no_verdict(last["round"], role))
    # The arbiter's answers in the last round the script couldn't read, and the approver's
    # decision lines that disagree: each its own agent's to give again.
    if last:
        path = folder / "reviews" / f"round-{last['round']}" / factory.VERIFIED
        _, wrong = factory.read_verified(path, last["round"], last["reviews"])
        if wrong:
            mendable["arbiter"] = wrong
    if decision_preamble(folder):
        mendable["approver"] = [factory.NO_DECISION]
    # Each role is mended once a round: one already mended (`runs/mended`) is a stop like any other.
    done = factory.mended(folder)
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
    elif tier == 1 and not decision and (upgrade or factory.upgrade_answer(ledger)):
        # A record with the tier still 1 is an upgrade cut short: the same one, finished.
        out["next"] = "upgrade"
        out["upgrading"] = upgrade["decision"] if upgrade else factory.upgrade_answer(ledger)["id"]
    elif upgrade and upgrade["round"] > built and stage != "build" and not decision:
        out["next"], out["round"] = "spec", upgrade["round"]
        spec = folder / "spec.md"
        out["written"] = spec.is_file() and not factory._scaffold(spec.read_text(encoding="utf-8"))
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
        out["next"], out["round"] = "arbitrate", last["round"]
    elif kept and not stuck and not untestable and last["round"] - first + 1 < run["rounds"]:
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


def early_stop(folder: Path, rounds: list[dict], first: int) -> tuple[list[str], list[str]]:
    """Why the last round ends the run's rework with rounds still left, from round files alone:
    `stuck`, each `role: change` its arbiter kept that it kept in the round before too, when that
    round is in this run (at or after `first`, so a restart or an upgrade starts fresh); and
    `untestable`, its builder report's `- UNTESTABLE:` lines. Each only once the round is complete
    and verified, or passed with nothing to verify; empty otherwise."""
    last = rounds[-1] if rounds else None
    changes = last and any(v["verdict"] == "CHANGES" for v in last["reviews"].values())
    if not last or not last["complete"] or (changes and last["verified"] is None):
        return [], []
    prev = next((r for r in rounds if r["round"] == last["round"] - 1), None)
    before = set()
    if prev and prev["round"] >= first and prev["verified"]:
        before = {(k["role"], k["change"]) for k in prev["verified"]["kept"]}
    kept = (last["verified"] or {"kept": []})["kept"]
    stuck = [f"{k['role']}: {k['change']}" for k in kept if (k["role"], k["change"]) in before]
    report = folder / "build" / f"round-{last['round']}.md"
    lines = report.read_text(encoding="utf-8").splitlines() if report.is_file() else []
    untestable = [m.group(1) for m in map(factory.UNTESTABLE_RE.match, lines) if m]
    return stuck, untestable


def cheap_nits(r: dict) -> list[tuple[str, str]]:
    """Round `r`'s nits weighed `S` and `med`, worth fixing before the commit that found them, as
    `(role, text)`, each once, in `REVIEWERS` order: what a rework of the round is handed."""
    return list(dict.fromkeys(
        (role, n["text"])
        for role in factory.REVIEWERS if role in r["reviews"]
        for n in r["reviews"][role].get("nits") or []
        if (n["cost"], n["value"]) == ("S", "med")
    ))  # fmt: skip


def read_gate(folder: Path, n: int) -> dict | None:
    """`build/round-<N>.gate.md` as its attempts, oldest first, each its verdict and the build it
    ran on, or None when the gate never ran on round `n`."""
    return factory.read_gate_file(factory.gate_path(folder, n))


def _gate_state(root: Path, folder: Path, built: int) -> tuple[dict | None, str | None]:
    """The gate as it stands for round `built`'s build, or None and why there is no gate: the
    command, its fails so far this round, and the last attempt's verdict when it ran on this
    build exactly (`current`), else None, which calls for a fresh attempt."""
    base = factory._base(root)
    command = factory._base_check(root, base) if base else None
    if command is None:
        return None, "the base branch's .sdlc/config.toml has no [commands] check"
    record = read_gate(folder, built) or {"attempts": [], "fails": 0}
    last = record["attempts"][-1] if record["attempts"] else None
    now = factory.build_hash(folder, built)
    current = last["verdict"] if last and last["build"] == now else None
    out = {"command": command, "round": built, "fails": record["fails"], "current": current}
    return out | {"exit": last["exit"] if last else None}, None
