"""retro — the retrospective's readers, apart from `sdlc.py` so a change to them reads on its own.

`sdlc.py` loads this file by path, as it loads `metrics.py`, and binds `sdlc` here to a live view of
its own names right after: every helper this code shares with the rest of the process (`_git`,
`load_config`, `closed_changes`, `inbox_entries` …) is read as `sdlc.<name>` when it runs, so a
test's stand-in on the loaded `sdlc` module reaches it. Unlike `metrics.py` and `indicators.py` it
is not pure, and it is never run on its own: `sdlc.py retro` and `sdlc.py retro-commit` are its
commands. The tests call this file's own names as `sdlc.retro.<name>`.

`sdlc` is unbound while this file loads, so a default argument here can't read it. What `status`
and release call on every run (`retro_due()`, `next_up()`, the doc readers, the history walks)
stays in `sdlc.py`.
"""

from __future__ import annotations

import importlib.util
import json
import statistics
import subprocess
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

sdlc = None  # sdlc.py's own names, bound by sdlc.py right after it loads this file


# Fewer closed changes than this in either window, and the escape rate's trend is `unknown`.
RATE_MIN_CHANGES = 5

# This many closed changes serving no outcome under one seed theme in the window, and the theme
# recurs: an aim the outcomes don't name, for the product pass to propose an outcome for.
NONE_THEME_RECURS = 3


# The closed changes hotspots and co-change read, back past the retrospective's boundary: where
# changes land is structure, and one window is too few changes to show it.
ARCH_LOOKBACK = 30


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


def _load_indicators():
    """`scripts/indicators.py`, the architecture pass's counts, by path like `metrics.py`: beside
    this file, since it loads before `sdlc` is bound."""
    spec = importlib.util.spec_from_file_location(
        "sdlc_indicators", Path(__file__).with_name("indicators.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


indicators = _load_indicators()


def prose_metrics(home: Path, cfg: dict) -> dict:
    """How much each skill is, the plugin's: what every session in a host reads and follows. A
    skill's size is its `SKILL.md`'s, which every run reads; the files beside it, read only when
    their branch applies, are its `branches`, and its commands are counted across them all. And
    the host docs the skills read on top. Tokens are an estimate, bytes / 4."""

    def size(text: str) -> dict:
        n = len(text.encode("utf-8"))
        return {"lines": len(text.splitlines()), "bytes": n, "est_tokens": n // 4}

    skills = {}
    for path in sorted((sdlc.PLUGIN_DIR / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        side = {
            p.name: p.read_text(encoding="utf-8")
            for p in sorted(path.parent.glob("*.md"))
            if p.name != "SKILL.md"
        }
        commands = [c for t in (text, *side.values()) for c in sdlc.bash_commands(t)]
        skills[path.parent.name] = {
            **size(text),
            "commands": len(commands),
            "script_calls": sum("scripts/sdlc.py" in c for c in commands),
            **({"branches": {name: size(t) for name, t in side.items()}} if side else {}),
        }
    docs = {}
    wanted = [(k, cfg["docs"][k]) for k in ("process", "policy", "review") if cfg["docs"][k]]
    for key, rel in [*wanted, *(("context", rel) for rel in cfg["docs"]["context"])]:
        found = sdlc.doc_path(home, key, rel)
        path = Path(found["path"]) if Path(found["path"]).is_absolute() else home / found["path"]
        if found["exists"] and found["path"] not in docs:
            size = path.stat().st_size
            docs[found["path"]] = {"bytes": size, "est_tokens": size // 4}
    script = sdlc.PLUGIN_DIR / "scripts" / "sdlc.py"
    return {
        "estimate": "est_tokens is bytes / 4",
        "skills": skills,
        "docs": docs,
        "sdlc_py_lines": len(script.read_text(encoding="utf-8").splitlines()),
    }


def _release_of(home: Path, cfg: dict, sha: str) -> str | None:
    """The first release tag that holds a change's commit: when its users could have had it. None
    while no release does."""
    pattern = cfg["release"]["tag"].replace("{version}", "*")
    tags = sdlc._git(home, "tag", "--contains", sha, "--list", pattern, "--sort=creatordate")
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
                sdlc._sh(command), cwd=home, capture_output=True, encoding="utf-8",
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


def _product(
    home: Path,
    cfg: dict,
    doc: dict,
    changes: list[dict],
    open_recs: list[dict],
    direction: dict,
    bases: dict[str, str | None],
) -> dict:
    """What the product pass counts: for each open outcome, the changes closed since the last
    retrospective that serve it and the open ones that do; the closed changes that name no outcome
    (`unlinked`, from before the doc) or say `none`, and those by their seeds' themes; the open
    outcomes nothing serves; the open changes still naming one a retrospective has struck
    (`stale`); and the direction doc's open goals and milestones that reach no open outcome
    (`uncited`). Then the evidence."""
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
        "uncited": _uncited(direction["items"], doc["items"]),
        "none_themes": _none_themes(home, changes, bases),
        "evidence": _evidence(home, cfg["retro"]["evidence"]),
    }


def _uncited(items: list[dict], outcomes: list[dict]) -> list[dict]:
    """The open goals and milestones, in the direction doc's order, whose citations reach no open
    outcome: a goal through the outcomes it ends with, a milestone through its `Serves:` line's
    outcomes and the outcomes of each goal it names, at whatever status. `why` is `none` when it
    reaches no outcome at all, `closed` when all it reaches is struck, and `unknown` when it names
    an id neither doc holds."""
    open_o = {o["id"] for o in outcomes if o["status"] == "open"}
    every_o = {o["id"] for o in outcomes}
    goals = {i["id"]: i for i in items if i["kind"] == "goal"}
    rows = []
    for item in items:
        if item["status"] != "open":
            continue
        reaches: list[str] = []
        unknown = False
        for ref in item["serves"]:
            if ref.startswith("G"):
                unknown |= ref not in goals
                cited = goals[ref]["serves"] if ref in goals else []
            else:
                cited = [ref]
            reaches += [o for o in cited if o not in reaches]
        unknown |= any(o not in every_o for o in reaches)
        if any(o in open_o for o in reaches):
            continue
        why = "unknown" if unknown else "closed" if reaches else "none"
        rows.append({
            "id": item["id"], "kind": item["kind"], "name": item["name"], "title": item["title"],
            "serves": item["serves"], "reaches": reaches, "why": why,
        })  # fmt: skip
    return rows


def _none_themes(home: Path, changes: list[dict], bases: dict[str, str | None]) -> list[dict]:
    """The closed changes serving no outcome, by the `Theme:` of the seeds their `idea:` names, as
    the register held them at each change's base: ship deletes a change's seeds on its branch, so
    the base is the last the base branch saw of them. A change counts once under each theme, and
    under `(no theme)` when none of its seeds has one. Rows by count, then theme; `recurring` at
    NONE_THEME_RECURS changes, never for `(no theme)`."""
    registers: dict[str, list[dict]] = {}
    grouped: dict[str, list[str]] = {}
    for rec in changes:
        if rec["serves"] != ["none"]:
            continue
        base = bases.get(rec["name"])
        if base and base not in registers:
            rel = f"{sdlc.work_rel(home)}/{sdlc.INBOX}"
            registers[base] = sdlc.parse_entries(sdlc._git(home, "show", f"{base}:{rel}") or "")
        entries = registers.get(base or "", [])
        themes: list[str] = []
        for ref in sdlc.ideas_of(rec):
            for e in entries:
                theme = sdlc.ref_matches(ref, e) and sdlc.entry_theme(e)
                if theme and theme not in themes:
                    themes.append(theme)
        for theme in themes or [sdlc.NO_THEME]:
            grouped.setdefault(theme, []).append(rec["name"])
    return [
        {"theme": theme, "changes": names,
         "recurring": theme != sdlc.NO_THEME and len(names) >= NONE_THEME_RECURS}
        for theme, names in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]  # fmt: skip


# The totals a retrospective compares, as medians per tier and way of running.
COMPARED = (
    "elapsed", "agent", "response", "away", "blocked", "stops", "required", "prompts",
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


def metrics_summary(changes: list[dict], allowance: int | None = None) -> dict:
    """What the `Close` trailers of the changes in range add up to: per tier and way of running,
    the median of each total, its stop target and the stops over it, tokens and agent time per
    stage and role, and ship's findings. Changes close couldn't measure are counted, not guessed
    at. `allowance` defaults to the config's, read when called: `sdlc` isn't bound at load."""
    if allowance is None:
        allowance = sdlc.CONFIG_KEYS["metrics"]["stop_allowance"]

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
        g = groups.setdefault(key, {"changes": [], "findings": _no_findings()})
        g["changes"].append(m)
        _add_findings(g["findings"], c.get("findings") or {})
    out: dict = {
        "captured": len(captured),
        "uncaptured": len(changes) - len(captured),
        "prompts": _prompt_report(captured),
        "extra": _extra_report(captured),
        "groups": {},
    }
    for key, g in groups.items():
        ms = g["changes"]
        stages = sorted({s for m in ms for s in m["stages"]}, key=sdlc.metrics.STAGES.index)
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


def _prompt_report(captured: list[dict]) -> dict:
    """The tool prompts across the window, from each `Close` commit's `Sdlc-Prompt` lines: each
    name's asks and rejections and how many changes it came from, most asked first, and how many
    changes ran in each permission mode. Only commits that carry `prompts=` are `recorded`: an
    older one's `permission=` counted questions and plan approvals, and is never read here."""
    names: dict[str, dict] = {}
    modes: Counter = Counter()
    recorded = 0
    for c in captured:
        m = c["metrics"]
        if not isinstance(m["totals"].get("prompts"), int):
            continue
        recorded += 1
        for mode in str(m["totals"].get("prompt_modes") or "-").split(","):
            modes[mode] += 1
        for name, p in (m.get("prompts") or {}).items():
            row = names.setdefault(name, {"asked": 0, "rejected": 0, "changes": 0})
            row["asked"] += p.get("asked") or 0
            row["rejected"] += p.get("rejected") or 0
            row["changes"] += 1
    ordered = dict(sorted(names.items(), key=lambda kv: (-kv[1]["asked"], kv[0])))
    return {"recorded": recorded, "names": ordered, "modes": dict(sorted(modes.items()))}


def _extra_report(captured: list[dict]) -> dict:
    """The extra stops across the window, from each `Close` commit's `Sdlc-Extra` lines: each
    kind's count and how many changes it came from, and the harness entries and other commands
    left out of the stops. Only commits that carry `harness=` on `Sdlc-Totals` are `recorded`: an
    older one counted those as `extra`, unclassified, and is never read here as none."""
    kinds = {k: {"count": 0, "changes": 0} for k in sdlc.metrics.EXTRA_KINDS}
    recorded = harness = command = 0
    for c in captured:
        m = c["metrics"]
        if not isinstance(m["totals"].get("harness"), int):
            continue
        recorded += 1
        harness += m["totals"]["harness"]
        command += m["totals"].get("command") or 0
        for kind, row in kinds.items():
            n = sum((s.get(kind) or 0) for s in (m.get("extra") or {}).values())
            row["count"] += n
            row["changes"] += 1 if n else 0
    return {"recorded": recorded, "kinds": kinds, "harness": harness, "command": command}


def _no_findings() -> dict:
    """What a group's ship findings add up to before any change is counted."""
    return {
        "important": 0, "nit": 0, "preexisting": 0,
        "passes": dict.fromkeys(sdlc.FINDING_PASSES, 0),
        "dispositions": {d: dict.fromkeys(sdlc.FINDING_PASSES, 0) for d in sdlc.COUNTED},
        "answered": 0,
        "fresh": 0, "fresh_wrong": 0, "fresh_counted": 0,
    }  # fmt: skip


def _add_findings(total: dict, found: dict) -> None:
    """Add one change's `Sdlc-Findings` to `total`. Counts add whatever the trailer's age; its
    dispositions add only when it carries them, and `answered` counts those changes, so a
    trailer from before dispositions is unknown there, never zero."""
    for k in ("important", "nit", "preexisting"):
        total[k] += found.get(k) if isinstance(found.get(k), int) else 0
    for p in sdlc.FINDING_PASSES:
        total["passes"][p] += found.get(p) if isinstance(found.get(p), int) else 0
    # The fresh reviewer's count, only from trailers that carry it, as `fresh_counted` says.
    if isinstance(found.get("fresh"), int):
        total["fresh_counted"] += 1
        total["fresh"] += found["fresh"]
        total["fresh_wrong"] += found.get("fresh_wrong") or 0
    if not all(d in found for d in sdlc.COUNTED):
        return
    total["answered"] += 1
    for d in sdlc.COUNTED:
        # `fixed=correctness:2` reads as a dict, `fixed=0` as 0, and a lone `pass:n` as a dict.
        by = found[d] if isinstance(found[d], dict) else {}
        for p in sdlc.FINDING_PASSES:
            total["dispositions"][d][p] += by.get(p) or 0


def _in_change_summary(ms: list[dict], median) -> dict:
    """Rework within the changes of one group: how often each stage went through first time, the
    share of changes where every stage seen did, the median of each rework count, and what spikes
    cost. Retro's own `rework` (a later change fixing this one) is another measure."""
    happy = [m["happy"] for m in ms if m.get("happy")]
    first_time = {}
    # A ship that stopped only for its own review's findings (`fixed`) went through first time; a
    # trailer from before that value has only yes and no, read as they always were.
    for stage in sdlc.metrics.HAPPY_STAGES:
        marks = [h.get(stage) for h in happy if h.get(stage) in ("yes", "fixed", "no")]
        if marks:
            first_time[stage] = round(sum(m != "no" for m in marks) / len(marks), 2)
    ships = [h.get("ship") for h in happy if h.get("ship") in ("yes", "fixed", "no")]
    judged = [h for h in happy if h.get("of")]
    done = [m["rework"] for m in ms if m.get("rework")]
    spikes = [m["spike"] for m in ms if m.get("spike")]
    return {
        "first_time": first_time,
        "ship_fixed": round(ships.count("fixed") / len(ships), 2) if ships else None,
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


CLOCKS = ("agent", "response", "away", "blocked")


def process_views(
    changes: list[dict], dropped: list[dict], rework: list[dict], questions: list[dict],
    bugs: dict, since: dict | None, today: date,
) -> dict:  # fmt: skip
    """The retrospective's process views, the report's figures: cycle time, throughput, where the
    time went, how many changes ran at once and what that did to them, rework and escapes. Only
    changes close measured (`Sdlc-Totals` with `elapsed`) are in the four timed views, which are
    None with none; the rest count every change. No figure combines them into one."""

    def median(values: list) -> float | None:
        values = [v for v in values if isinstance(v, int)]
        return statistics.median(values) if values else None

    def totals(c: dict) -> dict:
        return (c.get("metrics") or {}).get("totals") or {}

    measured = [c for c in changes if isinstance(totals(c).get("elapsed"), int)]
    by_tier = lambda rows: {str(t): [c for c in rows if c["tier"] == t]  # noqa: E731
                            for t in sorted({c["tier"] for c in rows}, key=str)}  # fmt: skip
    weeks: dict[str, Counter] = {}
    for c in changes:
        day = date.fromisoformat(c["close_date"])
        week = (day - timedelta(days=day.weekday())).isoformat()
        weeks.setdefault(week, Counter())[str(c["tier"])] += 1
    out: dict = {
        "window": {
            "since": since["date"] if since else None,
            "today": today.isoformat(),
            "closed": len(changes),
            "tiers": dict(sorted(Counter(str(c["tier"]) for c in changes).items())),
            "dropped": len(dropped),
            "measured": len(measured),
            "unmeasured": len(changes) - len(measured),
        },
        "throughput": [
            {"week": w, "tiers": dict(sorted(n.items())), "total": sum(n.values())}
            for w, n in sorted(weeks.items())
        ],
        "rework": {
            "links": len(rework),
            "reworked": len({r["reworks"] for r in rework}),
            "per_change": round(len(rework) / len(changes), 2) if changes else None,
            "questions": len(questions),
        },
        "escapes": {
            "reported": sum((bugs.get("reported") or {}).values()),
            "fixed": sum((bugs.get("fixed") or {}).values()),
            "days_to_fix": (bugs.get("days_to_fix") or {}).get("median"),
            "rate": ((bugs.get("rate") or {}).get("window") or {}).get("rate"),
            "previous": ((bugs.get("rate") or {}).get("previous") or {}).get("rate"),
            "trend": (bugs.get("rate") or {}).get("trend"),
        },
        "cycle": None, "time": None, "wip": None, "capacity": None,
    }  # fmt: skip
    if not measured:
        return out
    out["cycle"] = {
        tier: {
            "n": len(rows),
            "elapsed": median([totals(c)["elapsed"] for c in rows]),
            "max": max(totals(c)["elapsed"] for c in rows),
            "agent": median([totals(c).get("agent") for c in rows]),
            "days_open": median([c.get("days_open") for c in rows]),
        }
        for tier, rows in by_tier(measured).items()
    }
    sums = {k: sum(v for c in measured if isinstance(v := totals(c).get(k), int)) for k in CLOCKS}
    spent = sums["agent"] + sums["response"] + sums["away"]
    out["time"] = {
        "tiers": {
            tier: {k: median([totals(c).get(k) for c in rows]) for k in CLOCKS}
            for tier, rows in by_tier(measured).items()
        },
        "sums": sums,
        "agent_share": round(sums["agent"] / spent, 2) if spent else None,
    }
    # A change's span ends at its `Close` commit and starts `elapsed` minutes before it; its
    # concurrency is the most spans open at once while it was, its own included.
    spans = []
    for c in measured:
        end = datetime.fromisoformat(c["close_at"]) if c.get("close_at") else None
        if end:
            spans.append((end - timedelta(minutes=totals(c)["elapsed"]), end, c))
    at_once = []
    for start, end, c in spans:
        points = sorted(s for s, _, _ in spans if start <= s <= end) or [start]
        most = max(sum(1 for s, e, _ in spans if s <= p <= e) for p in [start, *points])
        at_once.append((most, c))
    counts = [n for n, _ in at_once]
    out["wip"] = {
        "spans": len(at_once),
        "median": statistics.median(counts) if counts else None,
        "max": max(counts, default=None),
    }
    rows: dict[str, list[dict]] = {"1": [], "2": [], "3+": []}
    for n, c in at_once:
        rows["1" if n == 1 else "2" if n == 2 else "3+"].append(c)
    out["capacity"] = {
        key: {"n": len(cs), **{k: median([totals(c).get(k) for c in cs])
                               for k in ("elapsed", "agent", "response")}}
        for key, cs in rows.items()
    }  # fmt: skip
    return out


# Where a retrospective's report is committed, under the host's `.sdlc/`, one a day.
RETROS = "retros"


def report_rel(today: date) -> str:
    """The report `retro-commit` writes for `today`, as a repo path."""
    return f"{sdlc.HOST_DIR}/{RETROS}/{today.isoformat()}.md"


def _hm(minutes: float | None) -> str:
    """Minutes as `1h 16m`, `—` for none."""
    if minutes is None:
        return "—"
    hours, mins = divmod(round(minutes), 60)
    return f"{hours}h {mins}m" if hours else f"{mins}m"


def _table(head: list[str], rows: list[list]) -> str:
    """A Markdown table, `—` for a missing value."""
    cell = lambda v: "—" if v is None else str(int(v) if v == int(v) else v) if isinstance(  # noqa: E731
        v, float) else str(v)  # fmt: skip
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return "\n".join([*lines, *("| " + " | ".join(cell(v) for v in r) + " |" for r in rows)])


# The spend measures as the report names them.
SPEND_NAMES = {
    "comment_share": "comment share",
    "out_per_line": "out tokens per code line",
    "tools_per_line": "tool calls per code line",
}


def _spend_text(spend: dict | None, closed: int) -> str:
    """`## Spend`: how many changes the token and call figures rest on and why the rest don't,
    each tier's medians, the changes over twice theirs, and the tools most called and failed."""
    if spend is None:
        return "Not counted."
    left = "; ".join(f"{why}: {n}" for why, n in sorted(spend.get("why", {}).items()))
    head = (
        f"{spend['recorded']} of the {closed} changes closed recorded their tool calls and words; "
        "the token and call figures rest on those alone, and comment lines come from every "
        "change's diff." + (f" Left out of them: {left}." if left else "")
    )
    tiers = _table(
        ["Tier", "Changes", *(f"Median {n}" for n in SPEND_NAMES.values())],
        [[t, r["changes"], *(r[k] for k in SPEND_NAMES)] for t, r in spend["tiers"].items()],
    )
    outliers = (
        _table(
            ["Change", "Tier", "Measure", "Value", "Tier median", "Times"],
            [
                [
                    o["change"],
                    o["tier"],
                    SPEND_NAMES[o["measure"]],
                    o["value"],
                    o["median"],
                    o["times"],
                ]
                for o in spend["outliers"]
            ],
        )  # fmt: skip
        if spend["outliers"]
        else "No change is over twice its tier's median on any measure."
    )
    head_tools = ["Tool", "Calls", "Errors", "Error share", "Changes"]
    rows = lambda ts: [[t[k] for k in ("name", "calls", "errors", "error_share", "changes")]  # noqa: E731
                       for t in ts]  # fmt: skip
    called, failed = spend["tools"]["most_called"], spend["tools"]["most_errors"]
    return "\n\n".join([
        head, tiers, outliers,
        "Most called:\n\n" + (_table(head_tools, rows(called)) if called else "No calls recorded."),
        "Most errors:\n\n" + (_table(head_tools, rows(failed)) if failed else "No call failed."),
    ])  # fmt: skip


def render_report(template: str, process: dict, spend: dict | None = None) -> str:
    """The report: `template` with each `{{key}}` replaced by its view as a table, or by
    "not measured" where close measured none of the window's changes. `spend` is `_spend()`'s
    block, "not counted" without it."""
    w = process["window"]
    unmeasured = f"Not measured: none of the {w['closed']} changes closed has its numbers."
    tiers = ", ".join(f"tier {t}: {n}" for t, n in w["tiers"].items()) or "none"
    values = {
        "since": w["since"] or "the start of history",
        "today": w["today"],
        "window": (
            f"From {w['since'] or 'the start of history'} to {w['today']}: {w['closed']} changes "
            f"closed ({tiers}), {w['dropped']} dropped. {w['measured']} of them were measured, and "
            f"the timed views rest on those alone; {w['unmeasured']} weren't."
        ),
        "throughput": _table(
            ["Week of", "Tiers", "Closed"],
            [[r["week"], ", ".join(f"{t}: {n}" for t, n in r["tiers"].items()), r["total"]]
             for r in process["throughput"]],
        ),  # fmt: skip
        "rework": _table(
            ["Declared links", "Changes reworked", "Links per closed change", "Questions"],
            [[process["rework"][k] for k in ("links", "reworked", "per_change", "questions")]],
        ),
        "escapes": _table(
            ["Reported", "Fixed", "Median days to fix", "Rate", "Previous rate", "Trend"],
            [[process["escapes"][k]
              for k in ("reported", "fixed", "days_to_fix", "rate", "previous", "trend")]],
        ),  # fmt: skip
        "cycle": unmeasured, "time": unmeasured, "capacity": unmeasured,
        "spend": _spend_text(spend, w["closed"]),
    }  # fmt: skip
    if process["cycle"]:
        values["cycle"] = _table(
            ["Tier", "Changes", "Median elapsed", "Longest", "Median agent", "Median days open"],
            [[t, r["n"], _hm(r["elapsed"]), _hm(r["max"]), _hm(r["agent"]), r["days_open"]]
             for t, r in process["cycle"].items()],
        )  # fmt: skip
        t = process["time"]
        values["time"] = _table(
            ["Tier", *(f"Median {k}" for k in CLOCKS)],
            [[tier, *(_hm(r[k]) for k in CLOCKS)] for tier, r in t["tiers"].items()],
        ) + (
            f"\n\nOver the window: agent {_hm(t['sums']['agent'])}, the person's response "
            f"{_hm(t['sums']['response'])}, away {_hm(t['sums']['away'])}, blocked "
            f"{_hm(t['sums']['blocked'])}. Agent share of agent, response and away: "
            f"{t['agent_share']}."
        )
        wip = process["wip"]
        values["capacity"] = (
            f"Changes open at once: median {wip['median']}, most {wip['max']}, over "
            f"{wip['spans']} changes.\n\n"
            + _table(
                ["Open at once", "Changes", "Median elapsed", "Median agent", "Median response"],
                [
                    [k, r["n"], _hm(r["elapsed"]), _hm(r["agent"]), _hm(r["response"])]
                    for k, r in process["capacity"].items()
                ],
            )  # fmt: skip
        )
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def retro_report(home: Path, cfg: dict, today: date) -> str:
    """The report for the window since the last retrospective, from history alone: the records
    `retro()` reads for its process views and its spend, without the product pass, the
    architecture, the prose or any host command."""
    trunk = cfg["git"]["base"]
    since = sdlc.last_retrospective(home, trunk)
    changes = sdlc.closed_changes(home, since["sha"] if since else None, trunk)
    bases = {}
    for rec in changes:
        bases[rec["name"]] = _change_rows(home, rec)[0]
        rec["days_open"] = sdlc._days_between(rec["created"], rec["close_date"])
    dropped = sdlc.dropped_changes(home, since["sha"] if since else None, trunk)
    rework, questions, _ = _rework(home, trunk, changes, bases)
    bugs = bugs_retro(home, cfg, since, changes, today)
    process = process_views(changes, dropped, rework, questions, bugs, since, today)
    template = sdlc.template_path(home, "retro.md")[0].read_text(encoding="utf-8")
    return render_report(template, process, _spend(home, cfg, changes, bases))


def rankable_entries(home: Path, today: date) -> list[dict]:
    """The register's entries a retrospective may re-rank: open ideas and bugs, each with its
    `Priority:` and `Theme:` as they stand. Nits are ranked by their `Cost:` and `Value:`, and an
    entry being built (tagged, or named by an open change's `idea:` or `fixes:`) is its change's,
    so neither is listed."""
    claims = [ref for ref, _ in sdlc._open_claims(home)]
    return [
        {"id": e["id"], "title": e["title"], "kind": sdlc.entry_kind(e),
         "priority": sdlc.entry_priority(e), "theme": sdlc.entry_theme(e),
         "age_days": sdlc._age_days({"created": e["date"]}, today)}
        for e in sdlc.inbox_entries(home)
        if not (sdlc.is_nit(e) or sdlc.is_building(e)
                or any(sdlc.ref_matches(r, e) for r in claims))
    ]  # fmt: skip


def _rework(
    home: Path, trunk: str | None, changes: list[dict], bases: dict[str, str | None]
) -> tuple[list[dict], list[dict], list[str]]:
    """Retro's rework, from what people declared, and the questions blame raises beside it.

    A link is declared on a change's own `reworks:` line, or by a bug it fixed whose
    `Introduced by:` names a change: `{change, reworks, days, via}`, the earlier change anywhere in
    history (`dropped` when it never landed), whatever the gap. A question is what blame finds and
    no link explains: lines an earlier change in the window wrote that a later one removed or
    replaced, blamed at the later change's start. Appending touches nothing, so it is never one.
    Questions are never counted: a planned follow-up replacing a first draft isn't a fix. Each id
    naming no change is a problem."""
    if not changes:
        return [], [], []
    closed = {
        c["name"]: c["close_date"] for c in sdlc.closed_changes(home, None, trunk, read=False)
    }
    gone = {d["name"]: d["drop_date"] for d in sdlc.dropped_changes(home, None, trunk)}
    links: dict[tuple[str, str], dict] = {}
    problems: list[str] = []

    def link(later: dict, ident: str, why: str) -> bool:
        name = next((n for n in [*closed, *gone] if sdlc.names_change(n, ident)), None)
        if name is None:
            return False
        if name != later["name"]:
            row = links.setdefault((later["name"], name), {
                "change": later["name"], "reworks": name, "via": [],
                "days": sdlc._days_between(closed.get(name) or gone.get(name) or "",
                                      later["close_date"]),
            })  # fmt: skip
            if name not in closed:
                row["dropped"] = True
            if why not in row["via"]:
                row["via"].append(why)
        return True

    for rec in changes:
        for ident in rec.get("reworks") or []:
            if not link(rec, ident, "reworks"):
                problems.append(f"{rec['name']}: reworks {ident!r} names no change")
        for bug_id, fixed in ((rec.get("metrics") or {}).get("fixes") or {}).items():
            by = str(fixed.get("introduced_by") or "")
            if by and by != "unknown":
                link(rec, by, f"bug {bug_id}")

    # Which change wrote each commit in the window: its branch from where it started. A commit two
    # ranges share is the earlier change's.
    order = {rec["name"]: i for i, rec in enumerate(changes)}
    owners: dict[str, str] = {}
    for rec in changes:
        if base := bases.get(rec["name"]):
            for sha in (sdlc._git(home, "rev-list", f"{base}..{rec['sha']}") or "").split():
                owners.setdefault(sha, rec["name"])
    # The register and setup's record are rewritten by the script, never by one change's hand.
    written = {f"{sdlc.work_rel(home)}/{sdlc.INBOX}", sdlc.MANIFEST}
    hits: dict[tuple[str, str], dict] = {}
    for rec in changes:
        base = bases.get(rec["name"])
        if not base:
            continue
        diff = sdlc._git(home, "diff", "-U0", "--no-renames", base, rec["sha"]) or ""
        for path, runs in indicators.removed_ranges(diff).items():
            if path.startswith(sdlc.CHANGE_FOLDERS) or path in written:
                continue
            spans = [arg for start, n in runs for arg in ("-L", f"{start},+{n}")]
            blame = sdlc._git(home, "blame", "--porcelain", *spans, base, "--", path) or ""
            for sha in indicators.blame_commits(blame):
                owner = owners.get(sha)
                if owner and order[owner] < order[rec["name"]]:
                    hit = hits.setdefault((rec["name"], owner), {
                        "change": rec["name"], "touches": owner, "files": [], "lines": 0,
                    })  # fmt: skip
                    hit["lines"] += 1
                    if path not in hit["files"]:
                        hit["files"].append(path)
    questions = [hit for pair, hit in hits.items() if pair not in links]
    return list(links.values()), questions, problems


def retro(home: Path, cfg: dict, today: date | None = None) -> dict:
    """What the retrospective counts: everything since the last one, from history. Read-only."""
    today = today or date.today()
    trunk = cfg["git"]["base"]
    since = sdlc.last_retrospective(home, trunk)
    changes = sdlc.closed_changes(home, since["sha"] if since else None, trunk)
    problems: list[str] = [] if trunk else [sdlc.trunk_refusal(home, trunk)]
    kind = _kind(cfg)
    bases: dict[str, str | None] = {}
    for rec in changes:
        problems += rec.pop("problems")
        # A change ships as one commit or several, and its size is all of them: its branch from
        # where it started. Without that start, the last commit still says what it touched.
        base, rows = _change_rows(home, rec)
        bases[rec["name"]] = base
        if not base:
            name, work = rec["name"], sdlc.work_rel(home)
            problems.append(
                f"{name}: no commit holds {work}/{name}/intent.md, so its size is unknown"
            )
        files = [path for path, _, _ in rows]
        lines = sum((added or 0) + (deleted or 0) for _, added, deleted in rows)
        size = indicators.change_size(rows, kind)
        rec.update(
            files=len(files) if base else None,
            lines=lines if base else None,
            added=size["added"] if base else None,
            deleted=size["deleted"] if base else None,
            by_kind=size["by_kind"] if base else None,
            days_open=sdlc._days_between(rec["created"], rec["close_date"]),
            release=_release_of(home, cfg, rec["sha"]),
        )
    dropped = sdlc.dropped_changes(home, since["sha"] if since else None, trunk)
    for rec in dropped:
        problems += rec.pop("problems")
        # What the dropped branch touched: its tip against where it left the base.
        fork = sdlc._git(home, "merge-base", f"{rec['drop_sha']}^1", f"{rec['drop_sha']}^2")
        files = (
            (sdlc._git(home, "diff", "--name-only", fork, rec["sha"]) or "").split() if fork else []
        )
        rec["files"] = len(files)
    rework, questions, unnamed = _rework(home, trunk, changes, bases)
    problems += unnamed
    bugs = bugs_retro(home, cfg, since, changes, today)
    a = sdlc.analyze(home, today)
    ideas = [
        i
        for i in sdlc.inbox_entries(home)
        if not (sdlc.is_building(i) or sdlc.is_nit(i) or sdlc.is_bug(i))
    ]
    direction = sdlc.direction_items(sdlc._direction_text(home, cfg))
    open_names = [f"{r['id']}-{r['slug']}" for r in a["open"]]
    direction["milestones"] = sdlc._milestone_verdicts(home, direction["items"], open_names, trunk)
    doc = sdlc.product_doc(home, cfg)
    product = (
        None if doc is None else _product(home, cfg, doc, changes, a["open"], direction, bases)
    )
    return {
        "since": since,
        "today": today.isoformat(),
        "changes": changes,
        "dropped": dropped,
        "dropped_at_counts": dict(Counter(d.get("dropped_at", "unknown") for d in dropped)),
        "dropped_cost": dropped_cost(dropped),
        "problems": problems,
        "rework": rework,
        "rework_questions": questions,
        "open": [
            {
                "name": f"{r['id']}-{r['slug']}",
                "title": sdlc.TITLE_ID_RE.sub("", r["title"]),
                "tier": r["tier"],
                "stage": r["stage"],
                "age_days": r.get("age_days"),
            }
            for r in a["open"]
        ],  # fmt: skip
        "ideas": {
            "open": len(ideas),
            "oldest": min((i["date"] for i in ideas), default=None),
        },
        "entries": rankable_entries(home, today),
        "nits": sdlc.nits_summary(sdlc.nit_entries(home)[0], today),
        "bugs": bugs,
        "process": process_views(changes, dropped, rework, questions, bugs, since, today),
        "report": report_rel(today),
        "tiers": dict(Counter(str(c["tier"]) for c in changes)),
        "impacts": dict(Counter(c["impact"] or "unset" for c in changes)),
        "releases": sdlc._release_tags(home, cfg, since),
        "unmeasured": UNMEASURED,
        "direction": direction,
        "metrics": metrics_summary(changes, cfg["metrics"]["stop_allowance"]),
        "product": product,
        "prose": prose_metrics(home, cfg),
        "architecture": _architecture(home, cfg, since, changes, kind),
        "spend": _spend(home, cfg, changes, bases),
    }


def _change_rows(home: Path, rec: dict) -> tuple[str | None, list]:
    """A closed change's numstat rows: its whole branch from where it started, or, with no start,
    its last commit alone. The start comes first, None when it couldn't be found."""
    base = sdlc._change_base(home, rec["name"], rec["sha"], rec["close_sha"])
    if base:
        numstat = sdlc._git(home, "diff", "--numstat", "--no-renames", base, rec["sha"]) or ""
    else:
        numstat = (
            sdlc._git(home, "diff-tree", "--no-commit-id", "--numstat", "-r", rec["sha"]) or ""
        )
    return base, indicators.numstat_rows(numstat)


def _added_diff(home: Path, rec: dict, base: str | None) -> str:
    """A closed change's `git diff -U0`, on the same base as `_change_rows()`: its whole branch
    from where it started, or its last commit alone without a start."""
    if base:
        return sdlc._git(home, "diff", "-U0", "--no-renames", base, rec["sha"]) or ""
    return sdlc._git(home, "diff-tree", "-U0", "-p", "--no-commit-id", "-r", rec["sha"]) or ""


def _unrecorded(m: dict | None) -> str | None:
    """Why a change's `Close` commit carries no tool calls or words, None when it does."""
    totals = (m or {}).get("totals") or {}
    if isinstance(totals.get("tools"), int) and isinstance(totals.get("words"), int):
        return None
    if not totals:
        return "not measured at close"
    coverage = str((m or {}).get("coverage") or "")
    if coverage.startswith("none:"):
        return coverage.removeprefix("none:").strip()
    return "closed before tool calls and words were counted"


def _spend(home: Path, cfg: dict, changes: list[dict], bases: dict[str, str | None]) -> dict:
    """What each change in the window spent beside its size: its added code lines and their line
    comments (`indicators.comment_lines()`, code alone as `_kind()` tells it), its agent `out`
    tokens, the person's words per stage and its tool calls from its `Close` commit, then
    `indicators.spend()`'s medians, outliers and tool ranking over them. A change whose commit has
    no `tools=` or `words=` is `recorded: false` with `why`, and its missing counts stay None.
    `changes` holds a change's own numbers: `cmd_retro()` prints them only with `--metrics`."""
    kind = _kind(cfg)
    register = f"{sdlc.work_rel(home)}/{sdlc.INBOX}"

    def code(path: str) -> bool:
        return (
            not path.startswith(sdlc.CHANGE_FOLDERS) and path != register and kind(path) == "code"
        )

    rows = []
    for rec in changes:
        m = rec.get("metrics") or {}
        totals = m.get("totals") or {}
        why = _unrecorded(m)
        counted = indicators.comment_lines(_added_diff(home, rec, bases.get(rec["name"])), code)
        tools = m.get("tools") or {}
        rows.append({
            "change": rec["name"], "tier": rec["tier"],
            "code_added": counted["added"] + counted["unknown_lines"],
            "comment_lines": counted["comment_lines"], "comment_base": counted["added"],
            "out": totals.get("out") if isinstance(totals.get("out"), int) else None,
            "words": None if why else {
                s: v.get("words") for s, v in (m.get("stages") or {}).items()
                if isinstance(v.get("words"), int)
            },
            "tools": None if why else totals["tools"],
            "errors": None if why else sum(t.get("errors") or 0 for t in tools.values()),
            "by_tool": {} if why else {
                n: {"calls": t.get("calls") or 0, "errors": t.get("errors") or 0}
                for n, t in tools.items()
            },
            "recorded": why is None, "why": why,
        })  # fmt: skip
    out = indicators.spend(rows)
    out["why"] = dict(Counter(r["why"] for r in rows if r["why"]))
    out["changes"] = rows
    return out


def _kind(cfg: dict):
    """A path's kind (code, tests or docs): `retro.test_paths` and `retro.doc_paths` where set,
    the conventions in `scripts/indicators.py` where not."""
    tests, docs = cfg["retro"]["test_paths"], cfg["retro"]["doc_paths"]
    is_tests = (lambda p: bool(sdlc.risk_paths([p], tests))) if tests else indicators.is_test
    is_docs = (lambda p: bool(sdlc.risk_paths([p], docs))) if docs else indicators.is_doc
    return lambda p: indicators.classify(p, is_tests, is_docs)


def _line_counts(home: Path, ref: str) -> dict[str, int]:
    """Lines per text file at `ref`, in one git call."""
    return indicators.grep_counts(sdlc._git(home, "grep", "-I", "-c", "", ref) or "", ref)


def _architecture(
    home: Path, cfg: dict, since: dict | None, changes: list[dict], kind
) -> dict | None:
    """What the architecture pass reads: size per tier over the window; hotspots and co-change
    over the last `ARCH_LOOKBACK` closed changes, past the boundary; the largest files and each
    kind's totals now and at the last retrospective; and the host's `retro.indicators` output,
    through `_evidence()`. None without a base branch."""
    trunk = cfg["git"]["base"]
    if not trunk:
        return None
    register = f"{sdlc.work_rel(home)}/{sdlc.INBOX}"

    def skip(path: str) -> bool:
        return path.startswith(sdlc.CHANGE_FOLDERS) or path == register

    recent = sdlc.closed_changes(home, None, trunk, read=False)[-ARCH_LOOKBACK:]
    lookback = [_change_rows(home, rec)[1] for rec in recent]
    now = _line_counts(home, trunk)
    # Every path on the base branch, so a hotspot with no lines to count reads as binary or
    # empty when it's there, and as gone when it isn't. Quoted as numstat quotes the hotspots'
    # paths (git's default), so the two compare; a listing that fails leaves `gone` unknown.
    listed = sdlc._git(home, "ls-tree", "-r", "--name-only", trunk)
    present = None if listed is None else set(listed.splitlines())
    then = _line_counts(home, since["sha"]) if since else None
    tests, docs = cfg["retro"]["test_paths"], cfg["retro"]["doc_paths"]
    return {
        "lookback": {
            "changes": len(recent),
            "first": recent[0]["name"] if recent else None,
            "last": recent[-1]["name"] if recent else None,
        },
        "kinds": {"tests": tests or "conventions", "docs": docs or "conventions"},
        "size": indicators.size_by_tier(changes),
        "hotspots": indicators.hotspots(lookback, now, skip, present=present),
        "co_change": indicators.co_change(lookback, skip),
        "largest": indicators.largest(now, then, skip),
        "totals": {
            "now": indicators.totals(now, kind, skip),
            "then": None if then is None else indicators.totals(then, kind, skip),
        },
        "host": _evidence(home, cfg["retro"]["indicators"]),
    }


def bugs_retro(home: Path, cfg: dict, since: dict | None, changes: list[dict], today: date) -> dict:
    """What retro counts about bugs in its window: each reported one once, by id and its reported
    date (open in the register, fixed on a `Close` commit's `Sdlc-Fixes:`, retired on a `Retire`
    commit's `Sdlc-Retired:`), the fixed by severity, the retired by reason, the days from report
    to fix, the open ones by age, and the escapes: each introducing change with its tier, and how
    many no one attributed. Read from the register and history alone."""
    trunk = cfg["git"]["base"]
    start = since["date"] if since else None
    words = sdlc.severities(home, cfg)
    open_bugs = sdlc.bug_entries(home, words)[0]
    fixed = []
    for rec in changes:
        for bug_id, f in ((rec.get("metrics") or {}).get("fixes") or {}).items():
            fixed.append({"id": bug_id, "change": rec["name"], "date": rec["close_date"],
                          **{k: str(v) for k, v in f.items()}})  # fmt: skip
    retired = []
    triaged: Counter = Counter()
    span = f"{since['sha']}..{trunk}" if since else trunk
    log = sdlc._git(home, "log", "--first-parent", "--format=%x1e%cs%x00%B", span) if trunk else ""
    for record in (log or "").split("\x1e"):
        day, _, body = record.partition("\x00")
        trailers = sdlc.metrics.parse_trailers(body) or {}
        for bug_id, f in (trailers.get("retired") or {}).items():
            retired.append({"id": bug_id, "date": day.strip(), **{k: str(v) for k, v in f.items()}})
        # Issues triage closed without a change: already resolved, or nothing will be done.
        for f in (trailers.get("triaged") or {}).values():
            triaged[str(f.get("verdict") or "unset")] += 1

    def in_window(reported: str | None) -> bool:
        return bool(reported) and reported != "unknown" and (start is None or reported >= start)

    reported: dict[str, str] = {}
    for b in open_bugs:
        if b["id"] and in_window(b["reported"]):
            reported.setdefault(b["id"], b["severity"] or "unset")
    for f in fixed + retired:
        if in_window(f.get("reported")):
            reported.setdefault(f["id"], f.get("severity") or "unset")
    days = sorted(
        d for f in fixed if (d := sdlc._days_between(f.get("reported", ""), f["date"])) is not None
    )
    history = {c["name"]: c for c in sdlc.closed_changes(home, None, trunk, read=True)}
    reviews: dict[str, dict] = {}

    def review(name: str) -> dict:
        """What the change's ship review left, read once."""
        if name not in reviews:
            rec = history.get(name)
            reviews[name] = (
                _review_at(home, name, rec["sha"], rec.get("findings"))
                if rec
                else {"state": "unknown", "counts": None, "findings": [], "problems": []}
            )
        return reviews[name]

    escapes: dict[str, dict] = {}
    unattributed = 0
    opened = [
        {"id": b["id"], "title": b["title"], "severity": b["severity"] or None,
         "paths": b["paths"] or None, "introduced_by": b["introduced_by"],
         "reported": b["reported"]}
        for b in open_bugs
    ]  # fmt: skip
    for source in [*fixed, *opened]:
        if not in_window(source.get("reported")):
            continue
        by = source.get("introduced_by")
        if not by or by == "unknown":
            unattributed += 1
            continue
        name = next((n for n in history if sdlc.names_change(n, by)), by)
        row = escapes.setdefault(
            name, {"bugs": 0, "tier": (history.get(name) or {}).get("tier"), "escaped": []}
        )
        row["bugs"] += 1
        row["escaped"].append(
            {"id": source.get("id"), "title": source.get("title"),
             "severity": source.get("severity"), "paths": _bug_paths(source.get("paths"))}
        )  # fmt: skip
    for name, row in escapes.items():
        known = [p for b in row["escaped"] for p in b["paths"] or []]
        paths = known if any(b["paths"] is not None for b in row["escaped"]) else None
        seen = review(name)
        marked = [{**f, "on_paths": _on_paths(f["evidence"], paths)} for f in seen["findings"]]
        row["review"] = {**seen, "findings": marked}

    # The escape rate, this window's against the one before: bugs reported in a window and tied
    # to a change, over the changes closed in it, whenever they're fixed. Retired ones never.
    ever_fixed = [
        f
        for rec in history.values()
        for f in ((rec.get("metrics") or {}).get("fixes") or {}).values()
    ]
    attributed = [
        str(b["reported"])
        for b in [*opened, *ever_fixed]
        if b.get("introduced_by") not in (None, "", "unknown")
        and str(b.get("reported") or "unknown") != "unknown"
    ]

    def window_rate(first: str | None, last: str | None, closed: int) -> dict:
        n = sum((first is None or r >= first) and (last is None or r < last) for r in attributed)
        return {"escapes": n, "changes": closed, "rate": round(n / closed, 2) if closed else None}

    now = window_rate(start, None, len(changes))
    bounds = sdlc.retrospectives(home, trunk)
    before = None
    if len(bounds) >= 2:
        newer, older = bounds[0], bounds[1]
        closed = len(sdlc.closed_changes(home, older["sha"], newer["sha"], read=False))
        before = window_rate(older["date"], newer["date"], closed)
    trend = "unknown"
    if before and min(now["changes"], before["changes"]) >= RATE_MIN_CHANGES:
        a, b = now["rate"], before["rate"]
        trend = "up" if a > b else "down" if a < b else "flat"

    # The window's Important findings, for a class that recurs across changes.
    important, important_unknown = [], 0
    for rec in changes:
        seen = review(rec["name"])
        if seen["state"] != "file":
            important_unknown += 1
            continue
        if seen["problems"]:  # what parsed is listed, but the count isn't known
            important_unknown += 1
        important += [
            {"change": rec["name"], **{k: f[k] for k in ("id", "pass", "title", "class",
                                                         "disposition")}}
            for f in seen["findings"]
            if f["rank"] == "important"
        ]  # fmt: skip

    def by_severity(rows: list[dict] | list[str]) -> dict[str, int]:
        counts = Counter(r if isinstance(r, str) else r.get("severity") or "unset" for r in rows)
        order = [w for w in words if counts[w]] + sorted(k for k in counts if k not in words)
        return {k: counts[k] for k in order}

    return {
        "reported": by_severity(list(reported.values())),
        "fixed": by_severity(fixed),
        "retired": dict(Counter(r.get("reason") or "unset" for r in retired)),
        "triaged": dict(triaged),
        "days_to_fix": {
            "median": days[len(days) // 2] if days else None,
            "max": days[-1] if days else None,
        },
        "open": sorted(
            (
                {
                    "id": b["id"],
                    "title": b["title"],
                    "severity": b["severity"],
                    "age_days": sdlc._age_days({"created": b["reported"]}, today),
                }
                for b in open_bugs
            ),
            key=lambda b: -(b["age_days"] or 0),
        ),
        "escapes": [{"change": n, **row} for n, row in sorted(escapes.items())],
        "unattributed": unattributed,
        "rate": {"window": now, "previous": before, "trend": trend},
        "important": important,
        "important_unknown": important_unknown,
    }


def _bug_paths(raw: object) -> list[str] | None:
    """A bug's paths, from the register (a list) or an `Sdlc-Fixes` line's `paths=` (text, or
    `unknown`); None when nobody recorded them, as on a line written before the key."""
    if isinstance(raw, list):
        return raw or None
    if not isinstance(raw, str) or raw in ("", "unknown"):
        return None
    return [p for p in raw.split(",") if p]


def _on_paths(evidence: str, paths: list[str] | None) -> bool | None:
    """Whether a finding's `Evidence:` path is one of an escaped bug's paths, under one, or holds
    one; None when the bug's paths are unknown."""
    if paths is None:
        return None
    where = (evidence.split() or [""])[0].split(":", 1)[0].strip("`").rstrip("/")
    for p in paths:
        p = p.strip("`").rstrip("/")
        if where and p and (where == p or where.startswith(p + "/") or p.startswith(where + "/")):
            return True
    return False


def _review_at(home: Path, name: str, sha: str, counts: dict | None) -> dict:
    """What a closed change's ship review left, from its own commit: its findings.md (`file`), only
    the `Sdlc-Findings` counts (`trailer`), or neither (`unknown`, never a clean review)."""
    text = sdlc._git(home, "show", f"{sha}:{sdlc.work_rel(home)}/{name}/{sdlc.FINDINGS}")
    entries, problems = sdlc._findings_from_text(text) if text else ([], [])
    keys = ("id", "rank", "pass", "title", "class", "disposition", "by", "evidence")
    return {
        "state": "file" if text else "trailer" if counts else "unknown",
        "counts": counts,
        "findings": [{k: e[k] for k in keys} for e in entries],
        # A section that no longer parses is said, never quietly one finding fewer.
        "problems": problems,
    }


def cmd_retro(root: Path, metrics: bool = False, report: bool = False) -> int:
    """The retrospective's counts as JSON, each change's measured numbers only with `metrics`
    (their medians are always there), or with `report` the report `retro-commit` would write, as
    Markdown. Writes nothing, and reads nothing outside the repo."""
    home = sdlc.main_root(root)
    cfg, _, parsed = sdlc.load_config(home)
    if report:
        print(retro_report(home, cfg, date.today()), end="")
        return 0 if parsed else 1
    out = retro(home, cfg)
    out["changes"], out["dropped"] = (
        sdlc._lean(out["changes"], metrics),
        sdlc._lean(out["dropped"], metrics),
    )
    if not metrics:  # each change's own spend, as its `metrics` are: the summary stays
        out["spend"] = {k: v for k, v in out["spend"].items() if k != "changes"}
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0 if parsed else 1


# What a retrospective may change on an entry already in the register: its rank and its theme.
RERANK_KEYS = ("Priority", "Theme")


def register_drift(old: str, new: str) -> list[str]:
    """What a retrospective did to the register beyond re-ranking: each entry the committed text
    held that is gone, or changed in more than its `RERANK_KEYS` lines (its heading, tag, prose,
    or any other key line). Entries added are a retrospective's seeds, and fine."""
    after = {e["id"]: e for e in sdlc.parse_entries(new) if e["id"]}

    def kept(e: dict) -> tuple:
        rest = {k: v for k, v in e["fields"].items() if k not in RERANK_KEYS}
        return e["status"], e["title"], e["text"], rest

    problems = []
    for e in sdlc.parse_entries(old):
        if not e["id"]:
            continue
        if e["id"] not in after:
            problems.append(f"{e['id']} was removed: retire it with /sdlc:idea, not a retro")
        elif kept(after[e["id"]]) != kept(e):
            keys = " and ".join(f"{k}:" for k in RERANK_KEYS)
            problems.append(f"{e['id']} changed beyond its {keys} lines")
    return problems


def cmd_retro_commit(root: Path, today: date | None = None) -> int:
    """Record a retrospective: one commit, `Retrospective YYYY-MM-DD`, holding the direction doc,
    the register, the product doc's outcomes, and the report it writes itself, and nothing else,
    so main is never left dirty.
    Every refusal is found before anything is written."""
    home = sdlc.main_root(root)
    cfg, _, _ = sdlc.load_config(home)
    stamp = (today or date.today()).isoformat()
    allowed = {
        cfg["docs"]["direction"],
        f"{sdlc.work_rel(home)}/{sdlc.register_path(sdlc.work_dir(home)).name}",
    }
    if cfg["docs"]["product"]:
        allowed.add(cfg["docs"]["product"])
    report: dict = {
        "commit": f"{sdlc.RETRO_PREFIX}{stamp}",
        "paths": [],
        "refusals": [],
        "done": [],
    }
    refusals = report["refusals"]

    def emit(code: int) -> int:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return code

    if root.resolve() != home.resolve():
        refusals.append(f"run it from the main checkout ({home}), not a change's worktree")
    trunk = cfg["git"]["base"]
    if why := sdlc.trunk_refusal(home, trunk, cfg["git"]["base_source"]):
        refusals.append(why)
    elif sdlc._git(home, "branch", "--show-current") != trunk:
        refusals.append(f"the main checkout ({home}) isn't on {trunk}")
    # Staged, unstaged and untracked, by name: porcelain's columns don't survive `_git`'s strip.
    tracked = sdlc._git(home, "-c", "core.quotePath=false", "diff", "--name-only", "HEAD") or ""
    untracked = (
        sdlc._git(home, "-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard")
        or ""
    )
    changed = sorted({p for p in (*tracked.splitlines(), *untracked.splitlines()) if p})
    # The report is the script's to write, below, once nothing refuses; one already there was
    # written by hand, or by a retrospective today.
    day = today or date.today()
    report_at = report_rel(day)
    if (home / report_at).exists():
        refusals.append(f"{report_at} already exists: retro-commit writes the report itself")
    stray = [p for p in changed if p not in allowed and p != report_at]
    if stray:
        refusals.append(
            f"only {' and '.join(sorted(allowed))} may be uncommitted; also changed: "
            + ", ".join(stray)
        )
    elif not changed:
        refusals.append(f"nothing to record: {' and '.join(sorted(allowed))} are unchanged")
    last = sdlc.last_retrospective(home, trunk)
    if last and last["date"] == stamp:
        refusals.append(f"{report['commit']} is already on {trunk} ({last['sha']}): one a day")
    # Follow-through: every goal, milestone or outcome the committed docs left open is still
    # there, carried or struck with its status. One already struck may go: it stayed one
    # retrospective. A product doc the retrospective didn't touch is checked all the same.
    docs = [("direction", "GM")] + ([("product", "O")] if cfg["docs"]["product"] else [])
    for key, kinds in docs:
        rel = cfg["docs"][key]
        committed = sdlc.doc_items(sdlc._git(home, "show", f"HEAD:{rel}") or "", kinds)
        path = home / rel
        new = sdlc.doc_items(path.read_text(encoding="utf-8") if path.is_file() else "", kinds)
        kept = {i["id"] for i in new["items"]}
        for item in committed["items"]:
            if item["status"] == "open" and item["id"] not in kept:
                refusals.append(
                    f"{item['id']} was open and the new {key} doc drops it: carry it, or strike "
                    "it with Done, Dropped or Revised"
                )
        refusals += [f"{key} doc: {p}" for p in new["problems"]]
    # The register: a retrospective appends seeds and re-ranks, and nothing else; an entry leaves
    # through ship, /sdlc:idea or /sdlc:bug, never through a retro.
    register = f"{sdlc.work_rel(home)}/{sdlc.register_path(sdlc.work_dir(home)).name}"
    committed = sdlc._git(home, "show", f"HEAD:{register}")
    if committed is not None:
        path = home / register
        refusals += register_drift(
            committed, path.read_text(encoding="utf-8") if path.is_file() else ""
        )
    if refusals:
        return emit(1)
    path = home / report_at
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(retro_report(home, cfg, day), encoding="utf-8", newline="\n")
    changed = sorted({*changed, report_at})
    report["paths"] = changed
    for args in (["add", "--", *changed], ["commit", "-q", "-m", report["commit"], "--", *changed]):
        made = subprocess.run(
            ["git", "-C", str(home), *args], capture_output=True, encoding="utf-8"
        )
        if made.returncode != 0:
            refusals.append(f"git {args[0]} failed: {made.stderr.strip()}")
            path.unlink(missing_ok=True)
            return emit(1)
    report["done"].append("commit")
    report["sha"] = sdlc._git(home, "rev-parse", "--short", "HEAD")
    return emit(0)
