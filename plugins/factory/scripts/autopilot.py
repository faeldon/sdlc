"""autopilot — the factory running from seed to landing while the person is away (216).

What lives here is `factory.py autopilot` (`cmd_autopilot()`): `--preview`, which words the one
WAIT and writes nothing; `--begin`, which fixes the run's bounds and the base branch's
`[autopilot]` in `AUTOPILOT_STATE`, in the git common dir, never in a tree; `--run`, the loop, under
`factory.AUTOPILOT_RUN_LOCK`; `--cancel`, which writes `AUTOPILOT_CANCEL`, read between steps; and
`--summary`, read-only. This repo lists the file in `[review] sensitive` beside `landing.py`.

The loop is this script, never an agent. Each judgment goes to a fresh agent session with no
Write, through `factory.py agent` (the planner's `wave`, the intent-writer's `intent`, the build's
own agents), and the script files the reply. Every step is a subprocess of `factory.py`, run with
`factory.AUTOPILOT_RUN_ENV` naming the lock, the one way `--by autopilot` is accepted (R2), and
only the commands `AUTOPILOT_STEPS` names, through `run_step()`, which the tests stand in for. It
answers an escalated default as its default, a look as seen and a blocking line with its raiser's
first option, always as `→ decided by autopilot:`, never the person's (R5, R17); it holds what it
must not land (`hold_causes()`, R19); and it counts two budgets the script computes from signals it
already detects, never a model (`review_debt()`, `change_risk()`, R24–R26).

The line between here and `factory.py` is the rule `tests/test_modules.py` holds for `landing.py`:
a function lives here when it is the command or its run's named state, or only code here calls
it; `factory.py` keeps what other modules read (the lock, `autopilot_running()`, `answer`, the
agent's change-less tasks). `factory.py` loads this file by path and binds `factory` here to a live
view of its own names, as it does `landing.py`; `factory` is unbound while this file loads, so
nothing evaluated at load may read it, and this file has no path of its own.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

factory = None  # factory.py's own names, bound by factory.py right after it loads this file


AUTOPILOT_CANCEL = "sdlc-factory-autopilot.cancel"


UNDER_WAY = "an autopilot --run is under way"


# The base branch's `[autopilot]` (R28), fixed in the state at `--begin`: off until a host turns
# it on; at most `parallel` changes take a step at once; a batch waits up to `wait` minutes for a
# change nearly ready; `debt` and `risk` are the budgets' limits. `guards` unset is the policy and
# review docs, `[review] irreversible` and `[review] sensitive`.
CONFIG = {"enabled": False, "parallel": 3, "wait": 30, "debt": 40, "risk": 30, "guards": None}


# Review debt's weight for each kind of call autopilot makes (R24): `[autopilot.debt_weights]`.
# Not `[autopilot.debt]`, which TOML can't hold beside the limit `[autopilot] debt`.
DEBT_WEIGHTS = {"default": 1, "look": 2, "blocking": 3, "spec": 2, "intent": 1}


# Change risk's weight for each signal kind (R26), every other kind 1, and the factors a landing
# is multiplied by when its close pushed and when its train held more than one change:
# `[autopilot.risk_weights]`. `impact` weighs 3 only for a major impact.
RISK_WEIGHTS = {"sensitive": 3, "impact": 3, "escalated": 3, "resolved": 2, "fixed": 2,
                "unreviewed": 2, "issue": 2}  # fmt: skip
RISK_OTHER = 1
RISK_FACTORS = {"pushed": 2.0, "stacked": 1.5}


# The highest tier autopilot opens, a bound the person sets: 1 opens only Tier 1 changes.
LEVELS = (1, 2)


# Where a change autopilot opened stands: `waiting` on what it depends on, `spec` (a Tier 2 whose
# spec is drafted next) or `start` (a Tier 1 moved to `stage: build` next), `building`, `ready` at
# `stage: test`, `landed`, or `held` with why.
PLACES = ("waiting", "spec", "start", "building", "ready", "landed", "held")


# The commands the loop runs for each step `verdicts` names, and no others (R14), as `RUN_STEPS`
# is the train's: `{role}` each role the reading names, started together; `{round}` the round the
# builder's report went to. `decide`, `done`, `stop` and `parked` (222: a host resource held,
# waited out by the loop itself, running nothing) are the loop's own reading, and the landing's
# commands are `TRAIN_COMMANDS`.
AUTOPILOT_STEPS = {
    "read": (("decisions", "{num}"), ("verdicts", "{num}", "--head", "{head}", "--record")),
    "spec": (
        ("agent", "{num}", "--task", "spec"), ("write-spec", "{num}", "--by", "autopilot"),
        ("stage", "{num}", "design"), ("stage", "{num}", "build"),
    ),
    "start": (("stage", "{num}", "build"),),
    "build": (("agent", "{num}", "--task", "build"), ("snapshot", "{num}", "--round", "{round}")),
    "fix": (("agent", "{num}", "--task", "fix"), ("snapshot", "{num}", "--round", "{round}")),
    "gate": (("gate", "{num}"),),
    "review": (("agent", "{num}", "--task", "review", "--role", "{role}"),),
    "arbitrate": (("agent", "{num}", "--task", "arbitrate"),),
    "rework": (("agent", "{num}", "--task", "rework"), ("snapshot", "{num}", "--round", "{round}")),
    "approve": (("carry", "{num}"), ("agent", "{num}", "--task", "approve")),
    "mend": (("agent", "{num}", "--task", "mend", "--role", "{role}"),),
    "answer": (("answer", "{num}", "{decision}", "--by", "autopilot"),),
    "decided": (("agent", "{num}", "--task", "decided", "--decision", "{decision}"),),
    "finish": (("stage", "{num}", "test"),),
    "accept": (("accept", "{num}"),),
    "wave": (("agent", "--task", "wave"),),
    "intent": (("agent", "--task", "intent", "--seed", "{seed}"),),
}  # fmt: skip


TRAIN_COMMANDS = {
    "check": ("land-check", "{ids}"),
    "begin": ("train", "--begin", "{ids}", "--by", "autopilot"),
    "run": ("train", "--run"),
    "stop": ("train", "--stop"),
    "cancel": ("train", "--cancel"),
}


# What a reply says when a change could only be built by breaking a contract, a hard rule or a
# guard (`CONTRACT`), or would be far simpler with one relaxed (`RELAX`): either holds it (R19).
CONTRACT_RE = re.compile(r"^\s*- (CONTRACT|RELAX):\s*(.+?)\s*$", re.M)
# The planner's plan (231 R8): `## <risk>` groups of `- WAVE:` and `- WAITS:` lines, and
# `- LEAVE:` lines anywhere, each line's parts split on an em dash (or ` -- `).
PLAN_LINE_RE = re.compile(r"^\s*- (WAVE|WAITS|LEAVE):\s*(.*?)\s*$")
PLAN_GROUP_RE = re.compile(r"^##\s+(.+?)\s*$")
PLAN_SEP_RE = re.compile(r"\s*—\s*|\s+--\s+")
TIER_RE = re.compile(r"^tier\s+(\d+)$")
LEAVE_KINDS = ("fixed", "wrong", "off-goal")
# A word of a LEAVE's reason that may be a repo path: a backticked span, or a word with a `/` or a
# `.` in it, a `:<line>` after it dropped.
PATH_WORD_RE = re.compile(r"`([^`]+)`|(\S*[/.]\S*)")
LINE_SUFFIX_RE = re.compile(r":\d+(?:-\d+)?$")
CREATED_RE = re.compile(r"^■ (\d{3,}-[a-z0-9][a-z0-9-]*) — tier")
SEED_ID_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}-\d+\b")
CHANGE_ID_RE = re.compile(r"(?<![\d-])\d{3,}(?![\d-])")
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ID_FORMAT = "%Y%m%dT%H%M%SZ"
FIXED_FORWARD = (
    "A call you disagree with is fixed forward: a revert of the landed change, or a new seed "
    "through /sdlc:idea. Autopilot never edits a landed change."
)


# ---------------------------------------------------------------- config, bounds and state


@contextmanager
def autopilot_lock(root: Path) -> Iterator[bool]:
    """Try autopilot's run lock for the `with` block without waiting: True when this process holds
    it, False when another does. Outside a git repo there is none to take: True."""
    where = factory._slot_dir(root)
    if where is None:
        yield True
        return
    fd = os.open(where / factory.AUTOPILOT_RUN_LOCK, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        held = factory._try_lock(fd)
        try:
            yield held
        finally:
            if held:
                factory._unlock(fd)
    finally:
        os.close(fd)


def autopilot_config(root: Path) -> tuple[dict, list[str]]:
    """`[autopilot]` as the base branch's `factory.toml` holds it, over `CONFIG`, its debt and
    risk weights over `DEBT_WEIGHTS` and `RISK_WEIGHTS`, and what was wrong with it: a change in
    flight can't loosen the run it's in (R28). `guards` unset is the base branch's policy and
    review docs, its `[review] irreversible` and its `[review] sensitive`."""
    table = factory._base_factory(root).get("autopilot", {})
    warnings: list[str] = []
    if not isinstance(table, dict):
        table, warnings = {}, ["autopilot must be a table"]
    cfg = dict(CONFIG)
    for key, value in table.items():
        if key in ("debt_weights", "risk_weights") and isinstance(value, dict):
            continue
        flag = key == "enabled" and isinstance(value, bool)
        if flag or key in ("parallel", "wait", "debt", "risk") and _whole(value):
            cfg[key] = value
        elif key == "guards" and isinstance(value, list) and all(isinstance(v, str) for v in value):
            cfg[key] = list(value)
        else:
            warnings.append(f"autopilot.{key} isn't a setting autopilot reads, or has a bad value")
    debt = table.get("debt_weights") if isinstance(table.get("debt_weights"), dict) else {}
    risk = table.get("risk_weights") if isinstance(table.get("risk_weights"), dict) else {}
    cfg["debt_weights"], more = _weights(
        dict(DEBT_WEIGHTS), debt, "debt_weights", set(DEBT_WEIGHTS)
    )
    warnings += more
    kinds = {*factory.landing.SIGNAL_KINDS, *RISK_FACTORS}
    base_risk = {**{k: RISK_OTHER for k in factory.landing.SIGNAL_KINDS}, **RISK_WEIGHTS}
    cfg["risk_weights"], more = _weights({**base_risk, **RISK_FACTORS}, risk, "risk_weights", kinds)
    warnings += more
    if cfg["guards"] is None:
        cfg["guards"] = _default_guards(root)
    return cfg, warnings


def _whole(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _weights(into: dict, table: dict, name: str, known: set[str]) -> tuple[dict, list[str]]:
    warnings = []
    for key, value in table.items():
        if key in known and isinstance(value, int | float) and not isinstance(value, bool):
            into[key] = value
        else:
            warnings.append(f"autopilot.{name}.{key} isn't a weight autopilot reads")
    return into, warnings


def _default_guards(root: Path) -> list[str]:
    """The base branch's policy and review docs, as `sdlc.py config` resolves them, and its
    `[review] irreversible` and `[review] sensitive` paths: what autopilot never lands a change
    touching. Sensitive paths are where a weakening is exploitable, and may be the code that runs
    the rest of the run (D8)."""
    guards = []
    _, cfg, _ = factory._sdlc(["config"], root)
    for key in ("policy", "review"):
        doc = ((cfg or {}).get("docs") or {}).get(key)
        if isinstance(doc, dict) and doc.get("path"):
            guards.append(str(doc["path"]))
    base = factory._base(root)
    return guards + (
        factory._irreversible(root, base) + factory._sensitive(root, base) if base else []
    )


def bounds_of(
    seeds: list[str] | None, themes: list[str] | None, usd: float | None, hours: float | None,
    level: int | None,
) -> dict:  # fmt: skip
    return {"seeds": list(seeds or []), "themes": list(themes or []), "usd": usd, "hours": hours,
            "level": level or max(LEVELS)}  # fmt: skip


def state_path(main: Path) -> Path | None:
    where = factory._slot_dir(main)
    return where / factory.AUTOPILOT_STATE if where else None


def read_state(main: Path) -> dict | None:
    path = state_path(main)
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path and path.is_file() else None
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_state(main: Path, state: dict) -> None:
    """The state, written whole through a temporary file, so a killed loop leaves the last one."""
    path = state_path(main)
    if path is None:
        return
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=1), encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def run_path(main: Path, state: dict) -> Path:
    """`.sdlc/reports/autopilot/<started>/` in the main checkout, a folder that ignores itself:
    the run's briefs, the planner's and intent-writer's replies, `escalations.md`, `summary.md`."""
    return main / factory.REPORTS / "autopilot" / state["id"]


def run_dir(main: Path, state: dict) -> Path:
    """`run_path()`, made, with the reports folder's `.gitignore`."""
    factory._reports(main)
    path = run_path(main, state)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _main(root: Path) -> Path:
    trees = factory.worktrees(root)
    return trees[0][0] if trees else root


def _now() -> datetime:
    return datetime.now(UTC)


# The longest the loop sleeps at once while only parked changes are left (222 R15), so a cancel or
# a spent budget is read within it.
PARK_SLICE = 30


def _pause(seconds: float) -> None:
    """The loop's one sleep, while it waits out a park: the tests stand in for it."""
    time.sleep(max(0.0, seconds))


def _retry_in(mine: dict) -> float | None:
    """Seconds until a parked change's next retry, None for a change not parked or past it."""
    if not mine.get("retry") or mine["place"] != "building":
        return None
    left = datetime.strptime(mine["retry"], TIME_FORMAT).replace(tzinfo=UTC) - _now()
    return left.total_seconds() if left.total_seconds() > 0 else None


def _stamp(when: datetime | None = None) -> str:
    return (when or _now()).strftime(TIME_FORMAT)


def _since(stamp: str) -> float:
    """Seconds since `stamp`."""
    then = datetime.strptime(stamp, TIME_FORMAT).replace(tzinfo=UTC)
    return (_now() - then).total_seconds()


# ---------------------------------------------------------------- the register's candidates


def status_items(main: Path) -> tuple[list[dict], str | None]:
    """`sdlc.py status --json`'s `next_up` items, through the `sdlc.py` of the factory's own
    version, or why they can't be read (`status_read()`, without the direction)."""
    items, _, why = status_read(main)
    return items, why


def candidates(
    items: list[dict], bounds: dict, state: dict | None = None, goal: dict | None = None
) -> list[dict]:
    """The `ready` group of `next_up`, in its order (R10), each a seed with an id, within the
    bounds' seeds or themes: never the `decide` group, a seed an open change already takes (which
    `next_up` leaves out of its items), nor a seed this run opened, held or left. A seed whose
    `Issue:` line names an issue, or can't be read (`issues` None), only when the bounds' seeds
    name it: text an outsider wrote is built unseen only by the person's choice (D9). A goal's
    `scope`, when it has one, keeps only the seeds it names: a goal narrows, never widens (231
    R3)."""
    taken = set((state or {}).get("seeds") or {})
    scope = (goal or {}).get("scope")
    found = []
    for item in items:
        if item.get("group") != "ready" or not item.get("id") or item["id"] in taken:
            continue
        if scope is not None and item["id"] not in scope:
            continue
        if bounds["seeds"] and item["id"] not in bounds["seeds"]:
            continue
        if item.get("issues", []) != [] and item["id"] not in bounds["seeds"]:
            continue
        if bounds["themes"] and item.get("theme") not in bounds["themes"]:
            continue
        found.append(item)
    return found


# ---------------------------------------------------------------- the goal (231)


# A goal named by its id in the direction doc, and a register theme's form.
GOAL_ID_RE = re.compile(r"^[GM]\d+$")
THEME_GOAL = "theme:"
# The outcomes a goal's text ends with, `(O1, O3)`, which its title leaves out: `serves` holds them.
GOAL_CITES_RE = re.compile(r"\s*\(O\d+(?:\s*,\s*O\d+)*\)\s*$")
NO_GOAL = "no goal: state one with --goal"
NOT_OPEN = "isn't an open goal or milestone in the direction doc"
# Where a goal came from, as the WAIT's `shown`, the brief and the summary say it.
SOURCES = {"direction": "from the direction doc", "register": "suggested from the register",
           "stated": "stated in the bounds"}  # fmt: skip


def status_read(main: Path) -> tuple[list[dict], dict, str | None]:
    """`sdlc.py status --json`'s `next_up` items and its `direction` (231 R1), through the
    `sdlc.py` of the factory's own version, or why they can't be read."""
    code, data, said = factory._sdlc(["status", "--json"], main)
    empty = {"goals": [], "milestones": [], "problems": []}
    if code or data is None:
        return [], empty, f"sdlc.py status couldn't be read: {said.strip()[-300:]}"
    direction = data.get("direction") if isinstance(data.get("direction"), dict) else {}
    return (list((data.get("next_up") or {}).get("items") or []),
            {k: list(direction.get(k) or []) for k in empty}, None)  # fmt: skip


def _item_title(item: dict) -> str:
    return item.get("name") or GOAL_CITES_RE.sub("", item.get("title") or "")


def goal_scope(arg: str, direction: dict, items: list[dict]) -> list[str] | None:
    """The seeds goal `arg` may take (R3): a milestone's `seeds`; a goal's, every seed of the
    milestones whose `Serves:` names it, None when none does; a theme's, its ready seeds; a
    stated goal's, None. None narrows nothing: the planner judges what serves it."""
    if arg.startswith(THEME_GOAL):
        theme = arg[len(THEME_GOAL) :]
        return [
            i["id"]
            for i in items
            if i.get("group") == "ready" and i.get("id") and i.get("theme") == theme
        ]
    if not GOAL_ID_RE.match(arg):
        return None
    if arg.startswith("M"):
        m = next((m for m in direction["milestones"] if m["id"] == arg), None)
        return list((m or {}).get("seeds") or [])
    serving = [m for m in direction["milestones"] if arg in (m.get("serves") or [])]
    if not serving:
        return None
    return list(dict.fromkeys(s for m in serving for s in m.get("seeds") or []))


def resolve_goal(
    arg: str | None, direction: dict, items: list[dict]
) -> tuple[dict | None, str | None]:
    """Goal `arg` read by its form (R2): `G<n>` or `M<n>` an open item of the direction doc
    (`direction`), `theme:<name>` a register theme, any other text the person's own; with its
    `source`, `arg`, `title`, `serves` and `scope`. (None, None) for no goal, (None, why) for an
    id the doc doesn't hold open."""
    arg = (arg or "").strip()
    if not arg:
        return None, None
    if GOAL_ID_RE.match(arg):
        found = next((i for i in [*direction["goals"], *direction["milestones"]]
                      if i["id"] == arg), None)  # fmt: skip
        if found is None:
            return None, f"{arg} {NOT_OPEN}"
        goal = {"source": "direction", "arg": arg, "title": _item_title(found),
                "serves": list(found.get("serves") or [])}  # fmt: skip
    elif arg.startswith(THEME_GOAL):
        theme = arg[len(THEME_GOAL) :].strip()
        if not theme:
            return None, "a theme goal names its theme: theme:<name>"
        arg = THEME_GOAL + theme
        goal = {"source": "register", "arg": arg, "title": f"the {theme} theme", "serves": []}
    else:
        goal = {"source": "stated", "arg": arg, "title": arg, "serves": []}
    return {**goal, "scope": goal_scope(arg, direction, items)}, None


def propose_goal(
    direction: dict, items: list[dict], bounds: dict
) -> tuple[dict | None, list[dict]]:
    """The goal `--preview` proposes when none is stated (R4), and up to three alternatives, each
    with its `count` of candidates within the bounds: the first open milestone, in the doc's
    order, with a candidate in its scope; else the theme with the most candidates (a tie to the
    theme whose best candidate ranks highest); else none. The alternatives are the other open
    milestones and goals with a candidate in scope, then the next themes."""
    found = candidates(items, bounds)
    ranked: list[dict] = []
    for item in [*direction["milestones"], *direction["goals"]]:
        goal, _ = resolve_goal(item["id"], direction, items)
        if goal and (n := len(candidates(items, bounds, None, goal))):
            ranked.append({**goal, "count": n})
    themes: dict[str, list[int]] = {}
    for at, item in enumerate(found):
        if item.get("theme"):
            themes.setdefault(item["theme"], []).append(at)
    for theme in sorted(themes, key=lambda t: (-len(themes[t]), themes[t][0])):
        goal, _ = resolve_goal(THEME_GOAL + theme, direction, items)
        ranked.append({**goal, "count": len(themes[theme])})
    pick = next((g for g in ranked if g["arg"].startswith("M")), None)
    pick = pick or next((g for g in ranked if g["source"] == "register"), None)
    if pick is None:
        return None, []
    return {k: v for k, v in pick.items() if k != "count"}, alternatives(ranked, pick["arg"])


GOAL_NEEDED = "the bounds need a goal (--goal), the one --preview named"


def begin_goal(main: Path, arg: str | None) -> tuple[dict | None, str | None]:
    """The goal `--begin` fixes (R6): `arg`, the one the preview named, resolved again against
    `status --json` as it is now, so the register moving since the yes can't swap the goal; or
    why not. Never a goal proposed here: no goal is a refusal."""
    if not (arg or "").strip():
        return None, GOAL_NEEDED
    items, direction, why = status_read(main)
    goal, refused = resolve_goal(arg, direction, items)
    if refused:
        return None, refused
    if why and goal["source"] != "stated":
        return None, why
    return goal, None


def register_ids(main: Path) -> list[str]:
    """The register's entry ids in the main checkout, in its order (R11): each `## [<id>] [tag]`
    heading `ENTRY_RE` reads, a fenced example never one."""
    path = main / factory.INBOX
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    ids, fenced = [], False
    for line in lines:
        if factory.FENCE_RE.match(line):
            fenced = not fenced
        elif not fenced and (m := factory.ENTRY_RE.match(line)):
            ids.append(m.group(1))
    return list(dict.fromkeys(ids))


def alternatives(ranked: list[dict], chosen: str) -> list[dict]:
    """Up to three of `ranked`'s goals, other than `chosen`, each its `arg`, `source`, `title`
    and `count`."""
    keys = ("arg", "source", "title", "count")
    return [{k: g[k] for k in keys} for g in ranked if g["arg"] != chosen][:3]


# ---------------------------------------------------------------- the budgets (R24–R27)


def review_debt(state: dict) -> dict:
    """The run's review debt: the sum, over its calls, of each kind's weight (R24), every call
    counted once by its kind, change and id, and what spent it, by kind."""
    weights = state["config"]["debt_weights"]
    seen, by_kind = set(), {}
    for call in state.get("calls") or []:
        key = (call.get("kind"), call.get("change"), call.get("id"))
        if key in seen or call.get("kind") not in weights:
            continue
        seen.add(key)
        by_kind[call["kind"]] = by_kind.get(call["kind"], 0) + weights[call["kind"]]
    return {"spent": sum(by_kind.values()), "limit": state["config"]["debt"], "by_kind": by_kind}


def change_risk(state: dict) -> dict:
    """The run's change risk over the changes it landed (R26): for each, its signal kinds'
    weights summed, each kind once (`impact` at its weight only for a major impact), times
    `pushed` when its close pushed and `stacked` when its train held more than one change."""
    weights = state["config"]["risk_weights"]
    by_change = {}
    for name, mine in (state.get("changes") or {}).items():
        if mine.get("place") != "landed":
            continue
        total = 0.0
        for kind in sorted({k for k, _ in mine.get("signals") or []}):
            texts = [t for k, t in mine["signals"] if k == kind]
            if kind == "impact" and "impact: major" not in texts:
                total += RISK_OTHER
            else:
                total += weights.get(kind, RISK_OTHER)
        if mine.get("pushed"):
            total *= weights["pushed"]
        if mine.get("stacked"):
            total *= weights["stacked"]
        by_change[name] = round(total, 2)
    spent = round(sum(by_change.values()), 2)
    return {"spent": spent, "limit": state["config"]["risk"], "by_change": by_change}


def run_usd(main: Path, state: dict) -> float:
    """What the run cost: each change it opened's `runs/costs.jsonl`, and its own sessions'."""
    total = factory.run_cost(run_path(main, state))["usd"]
    for mine in (state.get("changes") or {}).values():
        tree = Path(mine["worktree"])
        folder = tree / factory.work_rel(tree) / mine["name"]
        if folder.is_dir():
            total += factory.run_cost(folder)["usd"]
    return round(total, 4)


def spent(main: Path, state: dict) -> list[str]:
    """Why nothing new may start (R27): a budget reached, the dollar cap or the hours spent."""
    why = []
    debt, risk = review_debt(state), change_risk(state)
    if debt["spent"] >= debt["limit"]:
        why.append(f"review debt {debt['spent']} reached its limit {debt['limit']}")
    if risk["spent"] >= risk["limit"]:
        why.append(f"change risk {risk['spent']} reached its limit {risk['limit']}")
    return why + hard_stops(main, state)


def hard_stops(main: Path, state: dict) -> list[str]:
    """The dollar cap and the hours: once either is spent, no agent session starts at all."""
    why = []
    usd = run_usd(main, state)
    if usd >= state["bounds"]["usd"]:
        why.append(f"the run cost ${usd}, its cap ${state['bounds']['usd']}")
    if _since(state["started"]) >= state["bounds"]["hours"] * 3600:
        why.append(f"the run's {state['bounds']['hours']} hours are spent")
    return why


# ---------------------------------------------------------------- the steps


def _env(main: Path) -> dict[str, str]:
    where = factory._slot_dir(main)
    lock = str(where / factory.AUTOPILOT_RUN_LOCK) if where else "held"
    return {**factory.loop_env(), factory.AUTOPILOT_RUN_ENV: lock}


def run_step(main: Path, argv: list[str], cwd: Path) -> dict:
    """One command of `factory.py`, as a subprocess under the run's env: its `argv`, exit
    (`code`), JSON (`out`) and stderr (`said`). The one place the loop starts a process."""
    done = subprocess.run(
        [sys.executable, str(factory.FACTORY_SCRIPT), *argv], cwd=cwd, env=_env(main),
        capture_output=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
    )  # fmt: skip
    try:
        data = json.loads(done.stdout)
    except ValueError:
        data = None
    out = data if isinstance(data, dict) else None
    return {"argv": list(argv), "code": done.returncode, "out": out,
            "said": (done.stderr or done.stdout or "")[-500:]}  # fmt: skip


def commands(step: str, **fill: object) -> list[list[str]]:
    """`AUTOPILOT_STEPS[step]` filled, one argv a template; a `{role}` template once a role."""
    out = []
    for template in AUTOPILOT_STEPS[step]:
        roles = fill.get("roles") or [] if "{role}" in template else [None]
        for role in roles:
            out.append([str(part).format(**fill, role=role) for part in template])
    return out


def _failed(result: dict) -> str | None:
    """Why a step's command failed, or None: a gate or a check that ran red is the next reading's
    to read, as the train's loop reads them."""
    out = result["out"] or {}
    if result["argv"][0] in ("gate", "accept") and not out.get("refusals"):
        return None
    if result["code"] or out.get("problem") or out.get("refusals"):
        why = out.get("problem") or "; ".join(out.get("refusals") or [])
        return why or result["said"].strip()[-300:] or f"exit {result['code']}"
    return None


def run_all(main: Path, argvs: list[list[str]], cwd: Path, together: bool = False) -> list[dict]:
    """Each argv in turn, stopping at the first that fails; with `together`, all at once."""
    if together and len(argvs) > 1:
        with ThreadPoolExecutor(len(argvs)) as pool:
            return list(pool.map(lambda a: run_step(main, a, cwd), argvs))
    results = []
    for argv in argvs:
        results.append(run_step(main, argv, cwd))
        if _failed(results[-1]):
            break
    return results


def _round_of(result: dict) -> int | None:
    m = re.search(r"build/round-(\d+)\.md$", ((result.get("out") or {}).get("to")) or "")
    return int(m.group(1)) if m else None


def change_step(main: Path, name: str, mine: dict) -> dict:
    """One step of change `name`, in its worktree, from where it stands (`mine["place"]`): its
    spec (Tier 2) or its move to `stage: build` (Tier 1), or a building change's next step as
    `verdicts` names it (`build_step()`). Runs in a worker; returns what happened, which the loop
    applies to the state."""
    tree, num = Path(mine["worktree"]), name.split("-")[0]
    if mine["place"] in ("spec", "start"):
        results = run_all(main, commands(mine["place"], num=num), tree)
        failed = next((w for r in results if (w := _failed(r))), None)
        if failed:
            return {"results": results, "hold": f"{mine['place']}: {failed}"}
        copied = {"kind": "spec", "change": name, "id": "spec", "text": "spec.md copied unseen",
                  "answer": "write-spec --by autopilot"}  # fmt: skip
        calls = [copied] if mine["place"] == "spec" else []
        return {"results": results, "place": "building", "calls": calls}
    return build_step(main, name, mine, tree, num)


def build_step(main: Path, name: str, mine: dict, tree: Path, num: str) -> dict:
    """A building change's step (R14): `decisions` and `verdicts`, then the commands its `next`
    names in `AUTOPILOT_STEPS`; a `decide` answered as autopilot (R17), a `done` finished at
    `stage: test` (or held, R19), and `stop`, `upgrade` or `spec` held (R18)."""
    read = run_all(main, commands("read", num=num, head=mine["head"]), tree)
    reading = (read[-1]["out"] or {}) if len(read) == 2 else {}
    if not reading.get("next"):
        return {"results": read, "hold": f"verdicts couldn't be read: {read[-1]['said'][-200:]}"}
    nxt, rnd = reading["next"], reading.get("round")
    out: dict = {"results": list(read), "reading": {k: reading.get(k) for k in (
        "next", "round", "limit", "built", "decision", "way", "problems", "parked")}}  # fmt: skip
    if nxt == "parked":
        # A host resource is held (222 R15): no command runs; the loop waits out the retry.
        return {**out, "parked": reading.get("parked") or {}}
    if nxt == "stop" and reading.get("way") == "mend":
        out["results"] += run_all(
            main, commands("mend", num=num, roles=reading.get("mend")), tree, together=True
        )
        return out
    if nxt in ("stop", "upgrade", "spec"):
        why = {"upgrade": factory.AUTOPILOT_UPGRADES,
               "spec": "an upgraded change's spec is the person's"}.get(nxt)  # fmt: skip
        return {
            **out,
            "hold": why or "verdicts stopped: " + "; ".join(reading.get("problems") or []),
        }
    if nxt == "decide":
        return {**out, **answer_calls(main, name, tree, num, reading.get("pending") or [], True)}
    if nxt == "done":
        return {**out, **finish(main, name, mine, tree, num)}
    if nxt == "review":
        argvs = commands("review", num=num, roles=reading.get("missing"))
        out["results"] += run_all(main, argvs, tree, together=True)
        return out
    if nxt not in AUTOPILOT_STEPS:
        return {**out, "hold": f"the loop can't take the step {nxt!r}"}
    results = []
    for argv in commands(nxt, num=num, round="{round}"):
        if argv[0] == "snapshot":
            n = _round_of(results[-1]) if results else None
            argv = argv[:3] + [str(n or rnd or 1)]
        results.append(run_step(main, argv, tree))
        if _failed(results[-1]):
            break
    out["results"] += results
    return out


def answer_calls(
    main: Path, name: str, tree: Path, num: str, ids: list[str], carry_on: bool
) -> dict:
    """Each open ledger line in `ids` answered as autopilot (`answer --by autopilot`), each a call
    with its text, options and why, then, for a blocking line (`carry_on`), the builder told the
    answer (`agent --task decided`). A line the script won't answer holds the change."""
    folder = tree / factory.work_rel(tree) / name
    by_id = {d["id"]: d for d in factory.read_ledger(folder)}
    results, calls = [], []
    for ident in ids:
        result = run_step(main, commands("answer", num=num, decision=ident)[0], tree)
        results.append(result)
        if why := _failed(result):
            return {"results": results, "calls": calls, "hold": f"{ident}: {why}"}
        d = by_id.get(ident) or {}
        calls.append({"kind": d.get("kind"), "change": name, "id": ident, "text": d.get("text"),
                      "options": d.get("options") or [], "why": d.get("why"),
                      "answer": (result["out"] or {}).get("answer")})  # fmt: skip
        if carry_on:
            results += run_all(main, commands("decided", num=num, decision=ident), tree)
            if why := _failed(results[-1]):
                return {"results": results, "calls": calls, "hold": f"decided {ident}: {why}"}
    return {"results": results, "calls": calls}


def finish(main: Path, name: str, mine: dict, tree: Path, num: str) -> dict:
    """A change whose decision is in: held for any cause `hold_causes()` finds; else its open
    defaults and looks answered as autopilot, and set at `stage: test`, ready to land."""
    folder = tree / factory.work_rel(tree) / name
    causes = hold_causes(main, tree, folder, mine)
    if causes:
        return {"hold": "; ".join(causes)}
    open_ids = [d["id"] for d in factory.read_ledger(folder) if d["open"]]
    out = answer_calls(main, name, tree, num, open_ids, False)
    if out.get("hold"):
        return out
    results = out["results"] + run_all(main, commands("finish", num=num), tree)
    if why := _failed(results[-1]):
        return {**out, "results": results, "hold": f"stage test: {why}"}
    return {**out, "results": results, "place": "ready"}


def hold_causes(main: Path, tree: Path, folder: Path, mine: dict) -> list[str]:
    """Why a change with its decision in is held (R19, R21): a path in the base branch's
    `[autopilot] guards`, a `- CONTRACT:` or `- RELAX:` line in any reply of its run, an
    ESCALATE whose approver asks to reconsider the approach or gives a `gate` reason, an open
    default a reviewer or the approver raised that no later build made (`unbuilt_defaults()`,
    218), which `finish()` would otherwise answer and land unbuilt, or an acceptance check
    `read_only_command()` refuses. Skills' cases, and what `land-check`
    excludes, are read at landing (`land_batch()`)."""
    causes = contract_lines(folder)
    base = factory._base(tree)
    touched = factory.risk_paths(factory._changed_paths(tree, base), mine["guards"]) if base else []
    if touched:
        causes.append(f"touches guarded paths: {', '.join(touched[:5])}")
    decision = folder / "decision.md"
    if factory.read_decision(folder)[0] == "ESCALATE":
        if factory.reconsider_section(decision.read_text(encoding="utf-8")):
            causes.append("the approver asks to reconsider the approach")
        if any(r["kind"] == "gate" for r in factory.escalation_reasons(folder)):
            causes.append("the approver escalated on the gate")
    open_lines = [d for d in factory.read_ledger(folder) if d["open"]]
    if unbuilt := factory.unbuilt_defaults(folder, open_lines):
        ids = ", ".join(d["id"] for d in unbuilt)
        causes.append(f"a reviewer's or the approver's default no build made: {ids}")
    checks, why = factory.landing._checks_now(folder, tree)
    if why:
        causes.append(f"its acceptance checks can't be read: {why}")
    for check in checks:
        if refused := factory.landing.read_only_command(check["command"], tree):
            causes.append(f"acceptance check {check['name']!r} isn't read-only: {refused}")
    return causes


def contract_lines(folder: Path) -> list[str]:
    """Each `- CONTRACT:` or `- RELAX:` line an agent's reply in the change's folder holds."""
    found = []
    for path in sorted(folder.rglob("*.md")):
        rel = path.relative_to(folder).as_posix()
        if not rel.startswith(("build/", "reviews/", "decision", "runs/spec-draft")):
            continue
        for m in CONTRACT_RE.finditer(path.read_text(encoding="utf-8", errors="replace")):
            found.append(f"{rel}: {m.group(1)}: {m.group(2)}")
    return found


# ---------------------------------------------------------------- opening seeds (R11, R12)


def plan_wave(main: Path, state: dict, items: list[dict], room: int) -> dict:
    """The planner's next plan (231 R8) toward the run's goal: every candidate placed, at most
    `room` of them in its WAVE lines, which are the wave, in order. The script refuses a reply
    `read_plan()` won't read and asks once more with the refusal (the planner's mend); a second
    refusal ends the planning."""
    found = candidates(items, state["bounds"], state, state.get("goal"))
    if not found:
        return {"wave": [], "why": "no candidate is left within the bounds"}
    problem, results = None, []
    level = state["bounds"]["level"]
    for _ in range(2):
        write_brief(main, state, "wave", wave_brief(state, found, room, problem))
        result = run_step(main, commands("wave")[0], main)
        results.append(result)
        if why := _failed(result):
            return {"wave": [], "why": f"the planner failed: {why}", "results": results}
        plan, problem = read_plan(main, result, found, room, level)
        if problem is None:
            wave = [w["seed"] for w in plan["wave"]]
            why = None if wave else "the planner opened no seed: each candidate waits or was left"
            return {"wave": wave, "plan": plan, "why": why, "results": results}
    return {"wave": [], "why": f"the planner's plan was refused twice: {problem}",
            "results": results}  # fmt: skip


def read_plan(
    main: Path, result: dict, found: list[dict], room: int, level: int
) -> tuple[dict | None, str | None]:
    """The plan a planner's reply holds (R8): its `groups`, each a `## ` heading's risk with its
    `- WAVE: <seed> — tier <n> — <why>` and `- WAITS: <seed> — <why>` lines; its `wave` and
    `waits`, each line with its group; and its `leave`, `- LEAVE: <seed> — fixed|wrong|off-goal
    — <what shows it>` lines, anywhere. Or why the script refuses it: a candidate placed in no
    line or two, a line outside a group, a WAVE with no tier or one past `level`, an empty
    reason, a fixed or wrong LEAVE citing no path in `main`, a seed that isn't a candidate, or
    more WAVE lines than `room`."""
    to = (result["out"] or {}).get("to")
    text = (main / to).read_text(encoding="utf-8") if to and (main / to).is_file() else ""
    ids = [i["id"] for i in found]
    plan: dict = {"groups": [], "wave": [], "waits": [], "leave": []}
    problems, placed, group, fenced = [], [], None, False
    for line in text.splitlines():
        if factory.FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if g := PLAN_GROUP_RE.match(line):
            group = {"risk": g.group(1), "wave": [], "waits": []}
            plan["groups"].append(group)
            continue
        m = PLAN_LINE_RE.match(line)
        if not m:
            continue
        tag, parts = m.group(1), PLAN_SEP_RE.split(m.group(2), maxsplit=2)
        seed = parts[0].strip()
        placed.append(seed)
        if tag != "LEAVE" and group is None:
            problems.append(f"{tag} {seed} sits outside a `## <risk>` group")
            continue
        if tag == "WAVE":
            tier = TIER_RE.match(parts[1].strip()) if len(parts) > 1 else None
            if not tier:
                problems.append(f"WAVE {seed} has no `tier <1|2>`")
                continue
            if int(tier.group(1)) not in LEVELS or int(tier.group(1)) > level:
                problems.append(f"WAVE {seed} is tier {tier.group(1)}, past the level {level}")
                continue
            why = parts[2].strip() if len(parts) > 2 else ""
            row = {"seed": seed, "tier": int(tier.group(1)), "why": why, "group": group["risk"]}
        elif tag == "WAITS":
            why = PLAN_SEP_RE.split(m.group(2), maxsplit=1)[1:]
            why = why[0].strip() if why else ""
            row = {"seed": seed, "why": why, "group": group["risk"]}
        else:
            kind = parts[1].strip() if len(parts) > 1 else ""
            why = parts[2].strip() if len(parts) > 2 else ""
            if kind not in LEAVE_KINDS:
                problems.append(f"LEAVE {seed} needs a kind: {', '.join(LEAVE_KINDS)}")
                continue
            if why and kind != "off-goal" and not cited_paths(main, why):
                problems.append(f"LEAVE {seed} is {kind} but names no repo path that exists")
                continue
            row = {"seed": seed, "kind": kind, "why": why}
        if not why:
            problems.append(f"{tag} {seed} gives no reason")
            continue
        key = {"WAVE": "wave", "WAITS": "waits", "LEAVE": "leave"}[tag]
        plan[key].append(row)
        if key != "leave":
            group[key].append(row)
    if unknown := [p for p in dict.fromkeys(placed) if p not in ids]:
        problems.append(f"not candidates: {', '.join(unknown)}")
    if twice := [i for i in ids if placed.count(i) > 1]:
        problems.append(f"placed twice: {', '.join(twice)}")
    if nowhere := [i for i in ids if i not in placed]:
        problems.append(f"placed in no line: {', '.join(nowhere)}")
    if len(plan["wave"]) > room:
        problems.append(f"{len(plan['wave'])} WAVE lines, past the room for {room}")
    return (None, "; ".join(problems)) if problems else (plan, None)


def cited_paths(main: Path, text: str) -> list[str]:
    """The repo-relative paths `text` names that exist in the main checkout: never an absolute
    one, nor one climbing out with `..`, compared as POSIX text."""
    found = []
    for m in PATH_WORD_RE.finditer(text):
        # Quotes and brackets off either end, a sentence's stop off the end: `.gitignore` kept.
        word = (m.group(1) or m.group(2)).strip("\"'()[]").rstrip(",;:.!?")
        word = LINE_SUFFIX_RE.sub("", word)
        rel = word.replace("\\", "/")
        if not rel or rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
            continue
        if ".." in rel.split("/") or rel in (".", ""):
            continue
        if (main / rel).exists():
            found.append(rel)
    return found


def goal_lines(goal: dict | None) -> list[str]:
    """The goal as the brief and the summary say it, or that a run begun before goals has none."""
    if goal is None:
        return ["Goal: none (begun before goals)"]
    lines = [
        f'- Goal: {goal["arg"]} "{goal["title"]}"',
        f"- Source: {goal['source']} ({SOURCES.get(goal['source'], goal['source'])})",
    ]
    if goal.get("serves"):
        lines.append(f"- Serves: {', '.join(goal['serves'])}")
    return lines


def wave_brief(state: dict, found: list[dict], room: int, problem: str | None) -> str:
    """The planner's brief (R7): the goal and the level, then the room, the candidates (already
    narrowed to the goal's scope), what is in flight, and a refused reply's refusal."""
    lines = ["# Brief", "", "## Goal", "", *goal_lines(state.get("goal")), "",
             f"Level: {state['bounds']['level']}", "", f"Room: {room}", "",
             "## Candidates, in rank order", ""]  # fmt: skip
    lines += [f"- {i['id']} [{i.get('kind')}] {i.get('title')} ({i.get('label')}, theme "
              f"{i.get('theme') or 'none'})" for i in found]  # fmt: skip
    lines += ["", "## In flight", ""]
    lines += [f"- {n}: {m['place']}" for n, m in state["changes"].items()] or ["- nothing"]
    if problem:
        lines += ["", "## Your last reply was refused", "", problem]
    return "\n".join(lines) + "\n"


def write_brief(main: Path, state: dict, name: str, text: str) -> Path:
    path = run_dir(main, state) / "briefs" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def seed_text(main: Path, seed: str) -> str:
    """The register entry for `seed`, its heading and its lines, from the main checkout."""
    path = main / factory.INBOX
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    out, inside = [], False
    for line in lines:
        m = factory.ENTRY_RE.match(line)
        if m:
            inside = m.group(1) == seed
        elif inside and factory.ENTRY_END_RE.match(line):
            inside = False
        if inside:
            out.append(line)
    return "\n".join(out).strip() + "\n"


def open_seed(
    main: Path, state: dict, seed: str, opened: dict[str, str], issues: list[int] | None = (),
    planned: dict | None = None,
) -> dict:  # fmt: skip
    """Open `seed` as a change (R12): the intent-writer drafts its intent, `sdlc.py new` makes its
    worktree at the tier the draft says (never above the bounds' level), and the draft is written
    as its `intent.md` with `idea:` and `opened_by: autopilot` stamped in by line. `opened` maps
    the seeds opened before it in the run to their change, so a `depends_on:` naming one reads as
    that change. `issues`, the seed's `Issue:` numbers, become its `closes:` line, as
    `/sdlc:intent` writes it, so the landing's `issue` signal and the issue's close still hold;
    None (a line that can't be read) holds the seed before any agent runs (D9). `planned`, the
    planner's WAVE line for it, goes into the brief as `Planned:` after the entry (231 R10): the
    draft's own `tier:` still decides."""
    if issues is None:
        return {"seed": seed, "hold": "its Issue: line isn't #N, so its closes: can't be written",
                "results": []}  # fmt: skip
    brief = seed_text(main, seed)
    if planned:
        brief += f"\nPlanned: tier {planned['tier']}, {planned['group']}: {planned['why']}\n"
    write_brief(main, state, f"intent-{seed}", brief)
    result = run_step(main, commands("intent", seed=seed)[0], main)
    if why := _failed(result):
        return {"seed": seed, "hold": f"the intent-writer failed: {why}", "results": [result]}
    to = (result["out"] or {}).get("to")
    reply = (main / to).read_text(encoding="utf-8") if to and (main / to).is_file() else ""
    _, draft, _ = factory.split_draft(reply)
    meta = factory.frontmatter(draft)
    slug, tier = _slug(meta.get("slug") or ""), meta.get("tier")
    if not slug or tier not in ("1", "2"):
        return {"seed": seed, "hold": "the intent-writer's draft has no slug or tier 1|2",
                "results": [result]}  # fmt: skip
    if int(tier) > state["bounds"]["level"]:
        return {"seed": seed, "hold": f"tier {tier} is past the run's level "
                f"{state['bounds']['level']}", "results": [result]}  # fmt: skip
    raw = meta.get("depends_on") or ""
    after = [s for s in SEED_ID_RE.findall(raw) if s not in opened]
    depends = sorted(
        {
            *CHANGE_ID_RE.findall(SEED_ID_RE.sub("", raw)),
            *(opened[s].split("-")[0] for s in SEED_ID_RE.findall(raw) if s in opened),
        }
    )
    code, _, said = factory._sdlc(["new", slug, "--tier", tier, "--worktree"], main)
    created = next(
        (m.group(1) for line in said.splitlines() if (m := CREATED_RE.match(line))), None
    )
    if code or not created:
        return {"seed": seed, "hold": f"sdlc.py new refused: {said.strip()[-300:]}",
                "results": [result]}  # fmt: skip
    tree = next((p for p, b in factory.worktrees(main) if b == created), None)
    if tree is None:
        return {"seed": seed, "hold": f"{created} has no worktree", "results": [result]}
    folder = tree / factory.work_rel(tree) / created
    intent = folder / "intent.md"
    intent.write_text(
        opened_intent(intent.read_text(encoding="utf-8"), draft, seed, depends, list(issues)),
        encoding="utf-8", newline="\n",
    )  # fmt: skip
    head = factory._git(tree, "rev-parse", "--short", "HEAD") or ""
    return {"seed": seed, "change": created, "worktree": str(tree), "tier": int(tier),
            "depends": depends, "after": after, "head": head, "results": [result],
            "call": {"kind": "intent", "change": created, "id": seed,
                     "text": f"intent opened from seed {seed}",
                     "answer": f"tier {tier}"}}  # fmt: skip


def _slug(text: str) -> str:
    """A kebab-case slug, as `sdlc.py new` makes one; `new` checks it again."""
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-"))


def opened_intent(
    scaffold: str, draft: str, seed: str, depends: list[str], closes: list[int] = ()
) -> str:
    """The scaffold `new` wrote, its frontmatter kept line for line (`id:` as it is, never through
    YAML), `idea:`, `depends_on:`, `closes:` (when the seed names issues) and
    `opened_by: autopilot` set by line, then the draft's body."""
    lines = scaffold.splitlines(keepends=True)
    close = next((i for i, ln in enumerate(lines) if i and ln.strip() == "---"), None)
    if not lines or lines[0].strip() != "---" or close is None:
        return draft
    head = lines[1:close]
    values = {"idea": seed, "depends_on": f"[{', '.join(depends)}]" if depends else "",
              "opened_by": "autopilot"}  # fmt: skip
    if closes:
        values["closes"] = f"[{', '.join(str(n) for n in closes)}]"
    for key, value in values.items():
        line = f"{key}: {value}".rstrip() + "\n"
        at = next((i for i, ln in enumerate(head) if ln.startswith(f"{key}:")), None)
        if at is None:
            head.append(line)
        else:
            head[at] = line
    body_lines = draft.splitlines(keepends=True)
    end = next((i for i, ln in enumerate(body_lines) if i and ln.strip() == "---"), None)
    body = "".join(body_lines[end + 1 :] if end is not None else body_lines)
    return "".join(["---\n", *head, "---\n", "\n" if not body.startswith("\n") else "", body])


def open_wave(main: Path, state: dict, items: list[dict], room: int) -> dict:
    """The planner's wave, each seed in it opened in its order, the budgets read before each
    (R27): an intent opened is a call, so a spent debt opens no more."""
    planned = plan_wave(main, state, items, room)
    opened, done = {s: m["change"] for s, m in state["seeds"].items() if m.get("change")}, []
    issues = {i.get("id"): i.get("issues", []) for i in items}
    lines = {w["seed"]: w for w in (planned.get("plan") or {}).get("wave") or []}
    for seed in planned["wave"]:
        if spent(main, state):
            break
        got = open_seed(main, state, seed, opened, issues.get(seed, []), lines.get(seed))
        if got.get("change"):
            opened[seed] = got["change"]
            state["calls"].append(got["call"])
        done.append(got)
    return {**planned, "opened": done}


# ---------------------------------------------------------------- landing (R15, R21)


def near(mine: dict) -> bool:
    """A building change nearly ready: at `approve`, or reviewed in its last round."""
    reading = mine.get("reading") or {}
    return reading.get("next") == "approve" or (
        reading.get("round") is not None and reading.get("round") == reading.get("limit")
        and reading.get("next") in ("review", "arbitrate", "gate", "fix")
    )  # fmt: skip


def landing_due(state: dict, batch: int) -> list[str]:
    """The ready changes to land now, or []: none while a change still building is nearly ready
    and has been for less than `wait` minutes, unless the ready ones already fill a batch."""
    ready = [n for n, m in state["changes"].items() if m["place"] == "ready"]
    if not ready:
        return []
    if len(ready) >= batch:
        return ready[:batch]
    wait_s = state["config"]["wait"] * 60
    for mine in state["changes"].values():
        if mine["place"] == "building" and near(mine):
            since = mine.get("near_since")
            if since is None or _since(since) < wait_s:
                return []
    return ready


def land_batch(main: Path, state: dict, names: list[str]) -> dict:
    """Land `names` as a train by autopilot: each one's read-only checks run first (`accept`), then
    `land-check` (a change it excludes, or one with skills' cases in scope, held), then `train
    --begin --by autopilot` and `train --run`; a train stop the loop can't take is ended with
    `train --stop`, which puts every change not landed back, and those are held."""
    held, results, kinds = {}, [], {}
    for name in names:
        mine = state["changes"][name]
        tree = Path(mine["worktree"])
        folder = tree / factory.work_rel(tree) / name
        if factory.landing._checks_now(folder, tree)[0]:
            result = run_step(main, commands("accept", num=name.split("-")[0])[0], tree)
            results.append(result)
            if _failed(result) or (result["out"] or {}).get("verdict") not in (None, "PASS"):
                held[name] = "its acceptance checks didn't pass"
    left = [n for n in names if n not in held]
    if not left:
        return {"held": held, "landed": [], "results": results, "kinds": kinds}
    ids = [n.split("-")[0] for n in left]
    check = run_step(main, ["land-check", *ids], main)
    results.append(check)
    out = check["out"] or {}
    for entry in out.get("excluded") or []:
        held[entry["change"]] = "land-check excludes it: " + "; ".join(entry.get("excluded") or [])
    batch = []
    for entry in out.get("batch") or []:
        pairs = list(zip(entry.get("signal_kinds") or [], entry.get("signals") or [], strict=False))
        kinds[entry["change"]] = pairs
        if any(k == "cases" for k, _ in pairs):
            held[entry["change"]] = "skills' cases are in its scope: they never run unattended"
        elif entry["change"] in left:
            batch.append(entry["change"])
    if not batch:
        return {"held": held, "landed": [], "results": results, "kinds": kinds}
    begin = run_step(main, ["train", "--begin", *[n.split("-")[0] for n in batch], "--by",
                            "autopilot"], main)  # fmt: skip
    results.append(begin)
    if why := _failed(begin):
        return {"held": {**held, **dict.fromkeys(batch, f"train --begin: {why}")},
                "landed": [], "results": results, "kinds": kinds}  # fmt: skip
    ran = run_step(main, list(TRAIN_COMMANDS["run"]), main)
    results.append(ran)
    run_out = ran["out"] or {}
    landed = list(run_out.get("landed") or [])
    for e in run_out.get("ejected") or []:
        held[e["change"]] = f"ejected by the train: {e.get('reason')}"
    stopped = run_out.get("stopped")
    if stopped:
        results.append(run_step(main, list(TRAIN_COMMANDS["stop"]), main))
        for name in batch:
            if name not in landed and name not in held:
                held[name] = f"the train stopped at {stopped.get('next')}: {stopped.get('reason')}"
    return {"held": held, "landed": landed, "results": results, "kinds": kinds,
            "stacked": len(batch) > 1,
            "cancelled": (stopped or {}).get("next") == "cancel"}  # fmt: skip


def pushed(main: Path, name: str) -> bool:
    """Whether change `name`'s `Close` commit is on its base branch's upstream: its close pushed."""
    base = factory._base(main)
    if not base:
        return False
    upstream = factory._git(main, "for-each-ref", "--format=%(upstream)", f"refs/heads/{base}")
    rec = factory.closes(main, base)[0].get(name)
    if not upstream or not rec:
        return False
    close = factory._git(main, "log", "--first-parent", "--format=%H %s", base) or ""
    sha = next((ln.split()[0] for ln in close.splitlines()
                if ln.split(" ", 1)[-1] == f"{factory.CLOSE_PREFIX}{name}"), None)  # fmt: skip
    if not sha:
        return False
    done = subprocess.run(
        ["git", "-C", str(main), "merge-base", "--is-ancestor", sha, upstream],
        capture_output=True, encoding="utf-8",
    )  # fmt: skip
    return done.returncode == 0


# ---------------------------------------------------------------- the loop (R13–R17, R27)


def deps_met(main: Path, state: dict, mine: dict) -> tuple[bool, str | None]:
    """Whether every change `mine` depends on has its `Close` commit on the base branch (R13),
    and what it still waits on."""
    waits = [f"seed {s}" for s in mine.get("after") or []
             if not (state["seeds"].get(s) or {}).get("change")]  # fmt: skip
    for s in mine.get("after") or []:
        change = (state["seeds"].get(s) or {}).get("change")
        if change and change.split("-")[0] not in mine["depends"]:
            mine["depends"].append(change.split("-")[0])
    base = factory._base(main)
    closed = list(factory.closes(main, base)[0]) if base else []
    for dep in mine["depends"]:
        if not any(factory.names_change(n, dep) for n in closed):
            waits.append(dep)
    return not waits, ", ".join(waits) or None


def hold(main: Path, state: dict, name: str, why: str) -> None:
    mine = state["changes"][name]
    mine.update(place="held", why=why)
    note(main, state, name, f"held: {why}")


def note(main: Path, state: dict, name: str, line: str) -> None:
    """A line in the change's `runs/autopilot.md`, committed with it: each call and hold."""
    mine = state["changes"][name]
    tree = Path(mine["worktree"])
    folder = tree / factory.work_rel(tree) / name
    if not folder.is_dir():
        return
    path = folder / "runs" / "autopilot.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(
            "# Autopilot\n\n> What autopilot did in this change, its calls never the person's. "
            f"Run {state['id']}.\n\n", encoding="utf-8", newline="\n",
        )  # fmt: skip
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(f"- {_stamp()} {factory._placeholders(line, main)}\n")


def record_calls(main: Path, state: dict, calls: list[dict]) -> None:
    """Each call in the state, the run's `escalations.md` and its change's `runs/autopilot.md`."""
    path = run_dir(main, state) / "escalations.md"
    if not path.is_file():
        path.write_text("# Escalations\n\n> Every call autopilot made, for the person to review. "
                        f"{FIXED_FORWARD}\n\n", encoding="utf-8", newline="\n")  # fmt: skip
    for call in calls:
        call = {**call, "at": _stamp()}
        state["calls"].append(call)
        lines = [f"## {call['change']} {call['id']} ({call['kind']})", "", f"{call.get('text')}"]
        lines += [
            f"- OPTION: {o['option']} — {o.get('notes', '')}" for o in call.get("options") or []
        ]
        if call.get("why"):
            lines.append(f"- WHY: {call['why']}")
        lines += [f"- ANSWER: {call.get('answer')}", ""]
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(factory._placeholders("\n".join(lines), main) + "\n")
        if call["change"] in state["changes"]:
            note(
                main,
                state,
                call["change"],
                f"decided by autopilot: {call['id']} ({call['kind']}): {call.get('answer')}",
            )


def apply_change(main: Path, state: dict, name: str, got: dict) -> None:
    """What a change's step did, onto the state: its calls, its new place, a hold, and a guard
    against the same step named twice with nothing changed."""
    mine = state["changes"][name]
    record_calls(main, state, got.get("calls") or [])
    reading = got.get("reading")
    if reading:
        key = [reading.get("next"), reading.get("round"), reading.get("built"),
               reading.get("decision")]  # fmt: skip
        if reading.get("next") not in ("decide", "done", "parked") and key == mine.get("last"):
            got = {**got, "hold": f"verdicts named {reading['next']} twice with nothing changed"}
        mine["last"] = key
        if near({"reading": reading}):
            mine.setdefault("near_since", _stamp())
        mine["reading"] = reading
        # A park's retry and deadline, kept on the change while its reading names one (R15).
        park = got.get("parked") if reading.get("next") == "parked" else None
        if park:
            if park.get("retry") != mine.get("retry"):
                note(main, state, name, f"parked on {park.get('resource')}, held by "
                     f"{park.get('holder')}: retry {park.get('retry')}, deadline "
                     f"{park.get('deadline')}")  # fmt: skip
            mine.update(retry=park.get("retry"), deadline=park.get("deadline"))
        else:
            mine.pop("retry", None)
            mine.pop("deadline", None)
    failed = next((w for r in got.get("results") or [] if (w := _failed(r))), None)
    tree = Path(mine["worktree"])
    folder = tree / factory.work_rel(tree) / name
    lines = contract_lines(folder) if folder.is_dir() else []
    if got.get("hold"):
        hold(main, state, name, got["hold"])
    elif lines:
        hold(main, state, name, "; ".join(lines))
    elif failed:
        hold(main, state, name, failed)
    elif got.get("place"):
        mine["place"] = got["place"]


def apply_wave(main: Path, state: dict, got: dict) -> None:
    """A wave onto the state: its seeds, its plan (231 R8), and each seed the plan leaves kept in
    `seeds` with its kind and reason, so no later wave offers it (R9). A left seed is the
    person's: nothing here writes the register or the direction doc."""
    state["waves"].append(got["wave"])
    if got.get("plan"):
        state.setdefault("plans", []).append(got["plan"])
        for left in got["plan"]["leave"]:
            state["seeds"][left["seed"]] = {"change": None, "left": left["kind"],
                                            "why": f"{left['kind']}: {left['why']}"}  # fmt: skip
    if not got["wave"]:
        state["planned_out"] = got.get("why") or "the planner opened no seed"
    for opened in got.get("opened") or []:
        seed = opened["seed"]
        state["seeds"][seed] = {"change": opened.get("change"), "why": opened.get("hold")}
        if not opened.get("change"):
            continue
        name = opened["change"]
        state["changes"][name] = {
            "name": name, "seed": seed, "worktree": opened["worktree"], "tier": opened["tier"],
            "depends": opened["depends"], "after": opened["after"], "head": opened["head"],
            "place": "waiting", "why": None, "guards": state["config"]["guards"],
        }  # fmt: skip
        record_calls(main, state, [opened["call"]])
        note(main, state, name, f"opened from seed {seed} at tier {opened['tier']}")


def apply_landing(main: Path, state: dict, got: dict) -> None:
    for name, why in got["held"].items():
        if name in state["changes"]:
            hold(main, state, name, why)
    for name in got["landed"]:
        mine = state["changes"].get(name)
        if mine is None:
            continue
        mine.update(place="landed", signals=got["kinds"].get(name) or [],
                    stacked=bool(got.get("stacked")), pushed=pushed(main, name))  # fmt: skip
    if got.get("cancelled"):
        state["cancel"] = True


def starts(main: Path, state: dict, running: dict, items: list[dict]) -> list[tuple[str, object]]:
    """What may start now (R27): each change the run opened takes its next step, on to `stage:
    test`, until the dollars or hours are spent; the next wave while there is room and a landing
    when one is due, only while no budget is spent either. Each is a key and a function of no
    arguments for a worker."""
    stops, hard = spent(main, state), hard_stops(main, state)
    state["stops"] = stops
    found: list[tuple[str, object]] = []
    busy = sum(1 for k in running if k in state["changes"])
    for name, mine in state["changes"].items():
        if name in running or busy >= state["config"]["parallel"]:
            continue
        if mine["place"] == "waiting" and not hard:
            ok, waits = deps_met(main, state, mine)
            mine["why"] = None if ok else f"waits on {waits}"
            if ok:
                mine["place"] = "spec" if mine["tier"] == 2 else "start"
        if _retry_in(mine) is not None:
            continue  # parked until its retry: it keeps its place in flight (R15)
        if mine["place"] in ("spec", "start", "building") and not hard:
            found.append((name, lambda n=name, m=dict(mine): change_step(main, n, m)))
            busy += 1
    in_flight = sum(1 for m in state["changes"].values() if m["place"] not in ("landed", "held"))
    room = state["config"]["parallel"] - in_flight
    if not stops and room > 0 and "wave" not in running and not state.get("planned_out"):
        found.append(("wave", lambda: open_wave(main, state_copy(state), items, room)))
    if not stops and "train" not in running:
        due = landing_due(state, state["config"]["land_batch"])
        if due:
            found.append(("train", lambda d=due: land_batch(main, state_copy(state), d)))
    return found


def state_copy(state: dict) -> dict:
    return json.loads(json.dumps(state))


def cancelled(main: Path) -> bool:
    where = factory._slot_dir(main)
    return bool(where) and (where / AUTOPILOT_CANCEL).is_file()


def run_loop(main: Path) -> int:
    """The loop (R13–R17, R27): read the cancel file and the budgets, start what may start, at
    most `parallel` changes at once, each step in a worker; apply each as it ends, writing the
    state after every one; end when nothing runs and nothing may start, writing the summary. A
    parked change (222 R15) is waited out, never an end: with nothing else running, the loop
    sleeps until its retry in slices of at most `PARK_SLICE` seconds, reading the cancel file
    and the budgets after each, and ends only once a cancel or a spent hour or dollar cap stops
    every change step."""
    state = read_state(main)
    where = factory._slot_dir(main)
    if where:
        (where / AUTOPILOT_CANCEL).unlink(missing_ok=True)  # one no loop read
    state.pop("ended", None)
    state["cancel"] = False
    running: dict = {}
    workers = state["config"]["parallel"] + 2
    with ThreadPoolExecutor(workers) as pool:
        while True:
            for key, fut in list(running.items()):
                if not fut.done():
                    continue
                del running[key]
                got = fut.result()
                if key == "wave":
                    apply_wave(main, state, got)
                elif key == "train":
                    apply_landing(main, state, got)
                else:
                    apply_change(main, state, key, got)
            write_state(main, state)
            if cancelled(main) and not state["cancel"]:
                state["cancel"] = True
                if "train" in running:
                    run_step(main, list(TRAIN_COMMANDS["cancel"]), main)
            if not state["cancel"]:
                items = []
                if "wave" not in running and not state.get("planned_out"):
                    items, why = status_items(main)
                    if why:
                        state["planned_out"] = why
                for key, fn in starts(main, state, running, items):
                    running[key] = pool.submit(fn)
                write_state(main, state)
            retries = [r for m in state["changes"].values() if (r := _retry_in(m)) is not None]
            parked = bool(retries) and not state["cancel"] and not hard_stops(main, state)
            if not running and not parked:
                return end_run(main, state)
            slice_s = min([PARK_SLICE, *retries]) if parked else None
            if not running:
                _pause(slice_s)
                continue
            wait(list(running.values()), timeout=slice_s, return_when=FIRST_COMPLETED)


def end_reason(state: dict) -> str:
    if state.get("cancel"):
        return "cancelled by autopilot --cancel"
    if state.get("stops"):
        return "; ".join(state["stops"])
    return state.get("planned_out") or "nothing left to take"


def end_run(main: Path, state: dict) -> int:
    where = factory._slot_dir(main)
    if where:
        (where / AUTOPILOT_CANCEL).unlink(missing_ok=True)
    state["ended"] = {"at": _stamp(), "reason": end_reason(state)}
    if isinstance(state.get("register"), dict):
        state["register"]["end"] = register_ids(main)
    path = write_summary(main, state)
    write_state(main, state)
    return factory.emit({"state": "ended", "reason": state["ended"]["reason"],
                         "summary": path.relative_to(main).as_posix(),
                         **summary(main, state)})  # fmt: skip


# ---------------------------------------------------------------- the summary (R22)


def register_moved(main: Path, state: dict) -> dict | None:
    """The register over the run (231 R11): its count at the start and at the end (now, while it
    runs), the ids `filed` since the start and those `drained`, and whether it `grew`: more filed
    than drained. Whoever moved it counts: a close filing a landing's held entries, the person,
    a shipped seed leaving. None for a run begun before goals, which never counted it."""
    reg = state.get("register")
    if not isinstance(reg, dict):
        return None
    start = list(reg.get("start") or [])
    end = list(reg["end"]) if "end" in reg else register_ids(main)
    filed = [i for i in end if i not in start]
    drained = [i for i in start if i not in end]
    return {"start": len(start), "end": len(end), "filed": filed, "drained": drained,
            "grew": len(filed) > len(drained)}  # fmt: skip


def summary(main: Path, state: dict) -> dict:
    """What the run did, as data: its time and cost, its goal and plans, each change by where it
    stands, the seeds left for the person, its calls, the budgets and what spent them, each
    landed change's signals, and how the register moved."""
    changes = state.get("changes") or {}
    by_place = {p: [n for n, m in changes.items() if m["place"] == p] for p in PLACES}
    end = state.get("ended") or {}
    hours = (_since(state["started"]) - (_since(end["at"]) if end.get("at") else 0)) / 3600
    return {
        "id": state["id"], "started": state["started"], "ended": end.get("at"),
        "reason": end.get("reason"), "hours": round(hours, 2), "usd": run_usd(main, state),
        "landed": by_place["landed"],
        "in_flight": {n: m["place"] for n, m in changes.items()
                      if m["place"] not in ("landed", "held")},  # fmt: skip
        "held": {n: m.get("why") for n, m in changes.items() if m["place"] == "held"},
        "seeds_held": {s: m["why"] for s, m in (state.get("seeds") or {}).items()
                       if m.get("why") and not m.get("left")},
        "left": {s: {"kind": m["left"], "why": m["why"].split(": ", 1)[-1]}
                 for s, m in (state.get("seeds") or {}).items() if m.get("left")},
        "calls": len(state.get("calls") or []),
        "debt": review_debt(state), "risk": change_risk(state),
        "goal": state.get("goal"), "plans": state.get("plans") or [],
        "register": register_moved(main, state),
    }  # fmt: skip


def plan_lines(plans: list[dict]) -> list[str]:
    """Each wave's groups, the risk each lowers and what it opened, then the last plan's WAITS
    and every seed left off the goal, each with its why."""
    if not plans:
        return ["- no plan was made"]
    lines = []
    for n, plan in enumerate(plans, 1):
        for group in plan["groups"]:
            opened = "; ".join(f"{w['seed']} at tier {w['tier']} ({w['why']})"
                               for w in group["wave"]) or "opens nothing"  # fmt: skip
            lines.append(f"- Wave {n}, {group['risk']}: {opened}")
    lines += [f"- Waits: {w['seed']}: {w['why']}" for w in plans[-1]["waits"]]
    lines += [f"- Off the goal: {x['seed']}: {x['why']}"
              for plan in plans for x in plan["leave"] if x["kind"] == "off-goal"]  # fmt: skip
    return lines


def write_summary(main: Path, state: dict) -> Path:
    """`summary.md` beside `escalations.md` in the run's folder, every path repo-relative and the
    whole defused, so it names no machine and no host."""
    data = summary(main, state)
    lines = ["# Autopilot run summary", "",
             f"> Run {state['id']}: what autopilot did while you were away, and what to review.",
             "", "## The run", "",
             f"- Started {data['started']}, ended {data['ended']}: {data['reason']}.",
             f"- Ran {data['hours']} hours and cost ${data['usd']} (API-equivalent).",
             f"- Bounds: {json.dumps(state['bounds'])}."]  # fmt: skip
    reg = data["register"]
    if reg is None:
        lines.append("- The register wasn't counted: this run began before goals.")
    else:
        lines.append(
            f"- The register held {reg['start']} entries at the start and {reg['end']} "
            f"at the end: {len(reg['filed'])} filed, {len(reg['drained'])} drained, by "
            "whoever moved it (a close filing a landing's entries, you, a shipped seed)."
        )
        if reg["grew"]:
            lines.append("- The register grew faster than this run drained it.")
    lines += ["", "## Goal", "", *goal_lines(data["goal"]), "", "## The plan", ""]
    lines += plan_lines(data["plans"])
    lines += ["", "## Landed", ""]
    changes = state.get("changes") or {}
    for name in data["landed"]:
        base = factory._base(main)
        rec = factory.closes(main, base)[0].get(name) if base else None
        lines.append(f"- {name}: its commit {rec['commit'][:7] if rec else 'unknown'}"
                     f"{', pushed' if changes[name].get('pushed') else ''}")  # fmt: skip
    lines += ["- nothing"] if not data["landed"] else []
    lines += ["", "## Mid-build", ""]
    for name, place in data["in_flight"].items():
        tree = Path(changes[name]["worktree"]).relative_to(main).as_posix()
        why = changes[name].get("why")
        lines.append(f"- {name}: {place} in {tree}" + (f" ({why})" if why else ""))
    lines += ["- nothing"] if not data["in_flight"] else []
    lines += ["", "## Held", ""]
    lines += [f"- {n}: {w}" for n, w in data["held"].items()]
    lines += [f"- seed {s}: {w}" for s, w in data["seeds_held"].items()]
    lines += ["- nothing"] if not (data["held"] or data["seeds_held"]) else []
    lines += ["", "## Left for you", ""]
    mine = {s: m for s, m in data["left"].items() if m["kind"] != "off-goal"}
    lines += [f"- seed {s}: {m['kind']}: {m['why']}" for s, m in mine.items()]
    lines += (
        [
            "",
            "The planner called these already fixed or wrong. The run retired none of "
            "them: each is yours to check against the code it cites.",
        ]
        if mine
        else ["- nothing"]
    )
    lines += ["", "## Calls autopilot made", ""]
    for call in state.get("calls") or []:
        lines.append(f"- {call['change']} {call['id']} ({call['kind']}): {call.get('text')} → "
                     f"{call.get('answer')}")  # fmt: skip
    lines += ["- none"] if not state.get("calls") else []
    debt, risk = data["debt"], data["risk"]
    lines += ["", "## Budgets", "",
              f"- Review debt: {debt['spent']} of {debt['limit']}, by kind "
              f"{json.dumps(debt['by_kind'])}",
              f"- Change risk: {risk['spent']} of {risk['limit']}, by change "
              f"{json.dumps(risk['by_change'])}", "", "## Risks to weigh", ""]  # fmt: skip
    for name in data["landed"]:
        texts = [t for _, t in changes[name].get("signals") or []]
        lines.append(f"- {name}: {'; '.join(texts) or 'no signal'}")
    lines += ["- nothing landed"] if not data["landed"] else []
    lines += ["", "## Fixing a call", "", FIXED_FORWARD, ""]
    path = run_dir(main, state) / "summary.md"
    text = factory._placeholders("\n".join(lines), main)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


# ---------------------------------------------------------------- the command


def preview_question(goal: dict, bounds: dict, cfg: dict) -> str:
    """The WAIT's question, naming the goal its yes approves with the caps (231 R5). The skill
    quotes it with its values as `<…>` marks (`test_the_skill_quotes_the_preview_question`)."""
    return (
        f'Run autopilot toward {goal["arg"]} "{goal["title"]}" ({goal["source"]}) until '
        f"${bounds['usd']} or {bounds['hours']} hours are spent, review debt "
        f"reaches {cfg['debt']} or change risk {cfg['risk']}, or you turn it off: it plans "
        "seeds from the register toward that goal within these bounds, opens their intents, "
        "drafts and copies their specs unseen, builds them, answers every escalated call on its "
        "default (recorded as autopilot's, never yours), holds what touches a guard or a "
        "contract, and lands the rest in batches as by=autopilot, pushed as git.push says? "
        "(yes / no)"
    )


def preview(main: Path, bounds: dict, goal_arg: str | None = None) -> dict:
    """`--preview`'s reading (R8): the goal, `goal_arg` resolved or one proposed (231 R4, R5), the
    bounds, the base branch's limits, the goal's first candidates in rank order, the WAIT's
    question and what its preview shows. Writes nothing. A `goal_arg` the doc doesn't hold open
    is under `refusals`; with no goal, the question is None and `warnings` says so."""
    cfg, warnings = autopilot_config(main)
    items, direction, why = status_read(main)
    proposed, alts = propose_goal(direction, items, bounds)
    if (goal_arg or "").strip():
        goal, refused = resolve_goal(goal_arg, direction, items)
        if refused:
            return {"refusals": [refused], "warnings": warnings + ([why] if why else [])}
        pool = [*([{**proposed, "count": len(candidates(items, bounds, None, proposed))}]
                  if proposed else []), *alts]  # fmt: skip
        alts = alternatives(pool, goal["arg"])
    else:
        goal = proposed
    found = candidates(items, bounds, None, goal)
    land = factory.load_config(main)[0]["land"]
    warnings += [f"the direction doc: {p}" for p in direction["problems"]]
    if goal is None:
        warnings.append(NO_GOAL)
    elif not found:
        warnings.append(f"the goal {goal['arg']} has no candidate within the bounds")
    question = None if goal is None else preview_question(goal, bounds, cfg)
    if goal is None:
        said = ["- none: no milestone or theme has a candidate within the bounds"]
    else:
        serves = f", serving {', '.join(goal['serves'])}" if goal["serves"] else ""
        said = [
            f'- {goal["arg"]} "{goal["title"]}", {SOURCES[goal["source"]]}{serves}: '
            f"{len(found)} candidate{'s' if len(found) != 1 else ''} within the bounds"
        ]
    shown = [
        "Goal:", *said,
        *[f'- or {a["arg"]} "{a["title"]}" ({a["source"]}, {a["count"]} candidates)'
          for a in alts],
        "- another goal is a new --preview with --goal <it>, and this question asked again",
        "Bounds:",
        f"- seeds: {', '.join(bounds['seeds']) or 'any'}; themes: "
        f"{', '.join(bounds['themes']) or 'any'}",
        f"- dollar cap: ${bounds['usd']}; hours: {bounds['hours']}; level: Tier "
        f"{bounds['level']} at most; parallel: {cfg['parallel']}",
        "Budgets (the base branch's [autopilot]):",
        f"- review debt limit {cfg['debt']}, weights {json.dumps(cfg['debt_weights'])}",
        f"- change risk limit {cfg['risk']}, weights {json.dumps(cfg['risk_weights'])}",
        f"- guards: {', '.join(cfg['guards']) or 'none'}; a batch waits {cfg['wait']} minutes "
        f"for a nearly ready change; land.batch {land['batch']}",
        "First candidates toward the goal, in rank order:",
        *[f"- {i['id']} {i.get('title')} ({i.get('label')})" for i in found[:10]],
        *(["- none within the bounds"] if not found else []),
        "Every call autopilot makes is recorded as autopilot's (by=autopilot, → decided by "
        "autopilot:), never as yours, in each change's runs/autopilot.md and the run's "
        "escalations.md, with a summary at the end.",
    ]  # fmt: skip
    shown_goal = (
        None
        if goal is None
        else {**{k: goal[k] for k in ("source", "arg", "title", "serves")}, "count": len(found)}
    )
    return {"goal": shown_goal, "alternatives": alts, "bounds": bounds, "config": cfg,
            "candidates": found, "question": question, "shown": "\n".join(shown),
            "warnings": warnings + ([why] if why else []), "land_auto": land["auto"]}  # fmt: skip


def begin_refusals(main: Path, bounds: dict, cfg: dict) -> list[str]:
    refusals = []
    if not cfg["enabled"]:
        refusals.append("the base branch's .sdlc/factory.toml has no [autopilot] enabled = true")
    if not factory.load_config(main)[0]["land"]["auto"]:
        refusals.append(
            "land.auto is off on the base branch: autopilot never lands by another door"
        )
    if factory.landing.train_running(main):
        refusals.append(factory.landing.RUN_UNDER_WAY)
    with autopilot_lock(main) as held:
        if not held:
            refusals.append(UNDER_WAY)
    if not bounds["usd"] or bounds["usd"] <= 0:
        refusals.append("the bounds need a dollar cap (--usd)")
    if not bounds["hours"] or bounds["hours"] <= 0:
        refusals.append("the bounds need hours (--hours)")
    if bounds["level"] not in LEVELS:
        refusals.append(f"--level is one of {', '.join(map(str, LEVELS))}")
    state = read_state(main)
    if state is not None and not state.get("ended"):
        refusals.append("an autopilot run is under way: --run resumes it, or --cancel ends it")
    return refusals


def cmd_autopilot(
    root: Path, mode: str, seeds: list[str] | None = None, themes: list[str] | None = None,
    usd: float | None = None, hours: float | None = None, level: int | None = None,
    goal: str | None = None,
) -> int:  # fmt: skip
    """`autopilot --preview|--begin|--run|--cancel|--summary`: the one WAIT's words, the run's
    state fixed after the yes, the loop under its lock, its off switch, and what it did."""
    main = _main(root)
    if mode == "preview":
        out = preview(main, bounds_of(seeds, themes, usd, hours, level), goal)
        return factory.emit(out, 1 if out.get("refusals") else 0)
    if mode == "begin":
        bounds = bounds_of(seeds, themes, usd, hours, level)
        cfg, warnings = autopilot_config(main)
        fixed, refused = begin_goal(main, goal)
        refusals = begin_refusals(main, bounds, cfg) + ([refused] if refused else [])
        if refusals:
            return factory.emit({"refusals": refusals, "warnings": warnings}, 1)
        # `[land] batch` is the base branch's, fixed here with the rest (R28).
        cfg["land_batch"] = factory.load_config(main)[0]["land"]["batch"]
        now = _now()
        # The goal joins the bounds, fixed here once (231 R6), and the register's ids, which the
        # summary counts against its end (R11).
        state = {"id": now.strftime(ID_FORMAT), "started": _stamp(now), "bounds": bounds,
                 "config": cfg, "goal": fixed, "register": {"start": register_ids(main)},
                 "waves": [], "plans": [], "seeds": {}, "changes": {}, "calls": []}  # fmt: skip
        write_state(main, state)
        return factory.emit({"state": "begun", "id": state["id"], "bounds": bounds,
                             "goal": fixed})  # fmt: skip
    if mode == "cancel":
        where = factory._slot_dir(main)
        with autopilot_lock(main) as held:
            if held or where is None:
                return factory.emit({"refusals": ["no autopilot --run is under way"]}, 1)
        (where / AUTOPILOT_CANCEL).write_text("cancel\n", encoding="utf-8", newline="\n")
        return factory.emit({"state": "cancelling", "after": "the steps in flight"})
    state = read_state(main)
    if mode == "summary":
        if state is None:
            return factory.emit({"refusals": ["no autopilot run to summarise"]}, 1)
        with autopilot_lock(main) as held:
            return factory.emit({"running": not held, **summary(main, state)})
    with autopilot_lock(main) as held:
        if not held:
            return factory.emit({"refusals": [UNDER_WAY]}, 1)
        if state is None:
            return factory.emit({"refusals": ["no autopilot run: --begin it first"]}, 1)
        return run_loop(main)
