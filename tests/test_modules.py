"""153: close, the push and the main lock live in `scripts/closing.py`, and the factory's landing
in `plugins/factory/scripts/landing.py`, each loaded by path and bound to a live view of its
script's names, so `[review] sensitive` can name them and a change elsewhere in either script
stays light. These read source: where the code lives, where the line between script and module
falls, and that neither module does anything while it loads."""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.portable

ROOT = Path(__file__).resolve().parents[1]
SDLC_PY = ROOT / "scripts" / "sdlc.py"
CLOSING_PY = ROOT / "scripts" / "closing.py"
FACTORY_PY = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
LANDING_PY = ROOT / "plugins" / "factory" / "scripts" / "landing.py"
RUN_STATE_PY = ROOT / "plugins" / "factory" / "scripts" / "run_state.py"

# R1's named entries: the lock family, close and its own helpers, and the push.
CLOSING_NAMES = {
    "_msvcrt_lock",
    "_msvcrt_unlock",
    "_flock_lock",
    "_flock_unlock",
    "_lock",
    "_unlock",
    "_lock_path",
    "_LOCK_DEPTH",
    "LOCK_HELD_ENV",
    "_lock_depth",
    "_main_lock",
    "_inherit_lock",
    "cmd_close",
    "_close_commit",
    "_drop_record",
    "_handoff",
    "HANDOFF_ENV",
    "_cleanup_plan",
    "CLEANUP_TIMEOUT",
    "_carries_others",
    "_ff_deletions",
    "_push",
    "_push_plan",
    # 172 R3: close's steps, and the stages around them.
    "_Close",
    "_step_merge",
    "_step_verify",
    "_step_measure",
    "_step_archive",
    "_step_remove_folder",
    "_step_tell_issues",
    "_step_record",
    "_step_remove_worktree",
    "_step_delete_branch",
    "_step_push",
    "_step_cleanup",
    "_close_target",
    "_close_refusals",
    "_close_preview",
    "_close_steps",
    "_run_close_steps",
}

# R2's named entries: land, land-check, train, resolve and land-verdicts, with the train's state.
LANDING_NAMES = {
    "cmd_land",
    "cmd_land_close",
    "cmd_land_fix",
    "cmd_land_check",
    "cmd_train",
    "_train_moved",
    "_train_fix",
    "_train_fail",
    "_train_took_part",
    "_train_begin",
    "_train_reading",
    "_train_waits",
    "_train_gate",
    "_train_eject",
    "_train_stop",
    "_train_cancel",
    "_train_run",
    "train_path",
    "train_live",
    "train_onto",
    "train_names",
    "train_record",
    "train_running",
    "TRAIN_STATE",
    "TRAIN_RUN_LOCK",
    "TRAIN_CANCEL",
    "TRAIN_RUN_ENV",
    "TRAIN_STEPS",
    "RUN_STEPS",
    "RUN_UNDER_WAY",
    "RUN_EJECTS",
    "RUN_STOPS",
    "RERUN",
    "PUT_BACK",
    "run_lock",
    "_run_env",
    "_run_one",
    "_run_group",
    "_run_plan",
    "_run_end",
    "_run_loop",
    "_rebase_settling",
    "cmd_resolve",
    "cmd_land_verdicts",
    "land_verdict",
}

# 171 R1: the build loop's one reading, and every function only it calls.
RUN_STATE_NAMES = {
    "loop_state",
    "early_stop",
    "settled",
    "_untouched",
    "cheap_nits",
    "reworked",
    "_gate_state",
    "read_gate",
    "decision_preamble",
}

# 171 R7: `verdicts` and the records it writes, which the board's copies follow, stay.
VERDICTS_NAMES = {
    "cmd_verdicts",
    "cli_verdicts",
    "stop_text",
    "early_lines",
    "step_text",
    "read_step",
    "_record_step",
    "STOPPED",
}

# script, module, what the script calls the module, what the module calls the script, R's names,
# and the other modules bound to the script, whose `<script>.<name>` calls count as the script's.
PAIRS = [
    pytest.param(
        SDLC_PY,
        CLOSING_PY,
        "closing",
        "sdlc",
        CLOSING_NAMES,
        [ROOT / "scripts" / "retro.py", ROOT / "scripts" / "board.py"],
        id="closing",
    ),
    pytest.param(
        FACTORY_PY, LANDING_PY, "landing", "factory", LANDING_NAMES, [RUN_STATE_PY], id="landing"
    ),
    pytest.param(
        FACTORY_PY,
        RUN_STATE_PY,
        "run_state",
        "factory",
        RUN_STATE_NAMES,
        [LANDING_PY],
        id="run_state",
    ),
]


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _defined(tree: ast.Module) -> set[str]:
    """Every name a top-level statement defines: a def, a class, or an assignment's targets."""
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
    return names


def _functions(tree: ast.Module) -> dict[str, ast.AST]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def _reached(tree: ast.AST, via: str) -> set[str]:
    """The names `tree` reads as `<via>.<name>`."""
    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == via
    }


def _named(tree: ast.AST) -> set[str]:
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "script, module, names",
    [
        pytest.param(SDLC_PY, CLOSING_PY, CLOSING_NAMES, id="closing"),
        pytest.param(FACTORY_PY, LANDING_PY, LANDING_NAMES, id="landing"),
        pytest.param(FACTORY_PY, RUN_STATE_PY, RUN_STATE_NAMES, id="run_state"),
    ],
)
def test_the_named_code_lives_in_its_module(script: Path, module: Path, names: set[str]) -> None:
    """R1, R2: each named entry is defined in the module and not in the script, so the module's
    path in `[review] sensitive` names the code."""
    assert module.exists(), f"{module.name} is missing"
    in_script = names & _defined(_tree(script))
    missing = names - _defined(_tree(module))
    assert not in_script, f"{script.name} still defines {sorted(in_script)}"
    assert not missing, f"{module.name} lacks {sorted(missing)}"


def test_close_push_and_the_lock_live_in_closing() -> None:
    """R1, by its own name."""
    test_the_named_code_lives_in_its_module(SDLC_PY, CLOSING_PY, CLOSING_NAMES)


def test_close_is_a_sequence_of_named_steps() -> None:
    """172 R1, R2: `cmd_close` is a short run of named steps, with no step nested inside it, and
    no function in `closing.py` is long enough to make a review of it a long read."""
    functions = _functions(_tree(CLOSING_PY))
    close = functions["cmd_close"]
    nested = [n.name for n in ast.walk(close) if n is not close and isinstance(n, ast.FunctionDef)]
    assert not nested, f"cmd_close defines {nested}: make each a top-level step"
    body = close.body[1:] if ast.get_docstring(close) else close.body
    lines = body[-1].end_lineno - body[0].lineno + 1
    assert lines <= 40, f"cmd_close's body is {lines} lines, over 40"
    long = {
        name: node.end_lineno - node.lineno + 1
        for name, node in functions.items()
        if node.end_lineno - node.lineno + 1 > 100
    }
    assert not long, f"over 100 lines: {long}"


def test_the_landing_lives_in_landing() -> None:
    """R2, by its own name."""
    test_the_named_code_lives_in_its_module(FACTORY_PY, LANDING_PY, LANDING_NAMES)


def test_the_run_state_lives_in_run_state() -> None:
    """171 R1, R7, by its own name: the run's reading lives in `run_state.py`, while `verdicts`
    and the records it writes, which the board's copies are pinned to, stay in `factory.py`."""
    test_the_named_code_lives_in_its_module(FACTORY_PY, RUN_STATE_PY, RUN_STATE_NAMES)
    left = VERDICTS_NAMES - _defined(_tree(FACTORY_PY))
    assert not left, f"factory.py no longer defines {sorted(left)}"
    taken = VERDICTS_NAMES & _defined(_tree(RUN_STATE_PY))
    assert not taken, f"run_state.py took {sorted(taken)}"


def test_run_state_defines_no_constant() -> None:
    """171 R4: every constant, regex and path the run's reading uses stays in `factory.py`, where
    `test_every_shared_name_is_the_factorys` compares `factory_records.py`'s copies; the module's
    one top-level assignment is its binding."""
    assigned = [
        ast.unparse(node)
        for node in _tree(RUN_STATE_PY).body
        if isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign)
    ]
    assert assigned == ["factory = None"], assigned


@pytest.mark.parametrize("script, module, modvar, binding, names, siblings", PAIRS)
def test_the_line_between_script_and_module_holds(
    script: Path, module: Path, modvar: str, binding: str, names: set[str], siblings: list[Path]
) -> None:
    """R3: a function moves when it is a named entry or only moved code calls it. One the script
    reaches in the module that isn't named should have stayed; one in the script that only the
    module calls should have moved."""
    script_tree, module_tree = _tree(script), _tree(module)
    module_functions = set(_functions(module_tree))
    stayed = sorted((_reached(script_tree, modvar) & module_functions) - names)
    assert not stayed, f"{script.name} calls these in {module.name}; they should stay: {stayed}"
    called_by_module = _reached(module_tree, binding)
    called_beside = set().union(*(_reached(_tree(p), binding) for p in siblings))
    should_move = []
    for name, node in _functions(script_tree).items():
        if name not in called_by_module or name in called_beside:
            continue
        rest = [n for n in script_tree.body if n is not node]
        if not any(name in _named(n) for n in rest):
            should_move.append(name)
    assert not should_move, f"only {module.name} calls these; they should move: {should_move}"


@pytest.mark.parametrize("script, module, modvar, binding, names, siblings", PAIRS)
def test_the_modules_are_loaded_by_path(
    script: Path, module: Path, modvar: str, binding: str, names: set[str], siblings: list[Path]
) -> None:
    """R4: the script loads the module by its path, never by an import or a `sys.path` edit,
    which `uv run --script` and the tests would each resolve differently."""
    source = script.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert modvar not in imported, f"{script.name} imports {modvar}"
    path_reads = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr == "path"
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
    ]
    assert not path_reads, f"{script.name} touches sys.path at {path_reads}"
    loads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "spec_from_file_location"
        and any(
            isinstance(c, ast.Constant) and c.value == module.name
            for arg in node.args
            for c in ast.walk(arg)
        )
    ]
    assert len(loads) == 1, f"{script.name} loads {module.name} by path once"


def test_the_modules_are_bound_live() -> None:
    """R4: each module reads its script's names through a live view of the script's globals, so
    a test's stand-in on the script reaches the moved code."""
    sdlc = _load("sdlc_modules_test", SDLC_PY)
    assert sdlc.closing.sdlc.__dict__ is vars(sdlc)
    factory = _load("factory_modules_test", FACTORY_PY)
    assert factory.landing.factory.__dict__ is vars(factory)
    assert factory.run_state.factory.__dict__ is vars(factory)


def _at_load(tree: ast.Module):
    """Every node a module evaluates while it loads: its top-level statements, and each
    function's decorators and default values, never a function's body."""
    stack = list(tree.body)
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            args = node.args
            stack.extend(args.defaults + [d for d in args.kw_defaults if d is not None])
            stack.extend(getattr(node, "decorator_list", []))
            continue
        stack.extend(ast.iter_child_nodes(node))


@pytest.mark.parametrize(
    "module, binding",
    [
        pytest.param(CLOSING_PY, "sdlc", id="closing"),
        pytest.param(LANDING_PY, "factory", id="landing"),
        pytest.param(RUN_STATE_PY, "factory", id="run_state"),
    ],
)
def test_the_modules_read_nothing_while_loading(module: Path, binding: str) -> None:
    """R5: the binding is unset while the module loads, and the module has no path of its own:
    no `__file__`, no script block, no `__main__`, and nothing evaluated at load reads the
    script's names."""
    source = module.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "# /// script" not in source
    assert "__file__" not in _named(tree)
    assert "__name__" not in _named(tree)
    early = sorted(
        f"line {node.lineno}: {binding}.{node.attr}"
        for node in _at_load(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == binding
    )
    assert not early, f"{module.name} reads {binding} while loading: {early}"


@pytest.mark.parametrize("path", [FACTORY_PY, LANDING_PY, RUN_STATE_PY], ids=lambda p: p.name)
def test_the_factory_never_loads_sdlc_py(path: Path) -> None:
    """R9, 171 R8: `factory.py`, `landing.py` and `run_state.py` never import `sdlc.py` nor load
    it by path; the factory runs `sdlc.py` as a process (`_sdlc()`), and copies what it parses."""
    tree = _tree(path)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    } | {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not [name for name in imported if "sdlc" in name], imported
    loads = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "spec_from_file_location"
        and any(
            isinstance(c, ast.Constant) and isinstance(c.value, str) and "sdlc" in c.value
            for arg in node.args
            for c in ast.walk(arg)
        )
    ]
    assert not loads, f"{path.name} loads sdlc.py at {loads}"


# 163: the factory's records, read in core through one pure module.
RECORDS_PY = ROOT / "scripts" / "factory_records.py"
BOARD_PY = ROOT / "scripts" / "board.py"
RETRO_PY = ROOT / "scripts" / "retro.py"

# R3: every copy of the factory's record parsing, in the module.
RECORD_NAMES = {
    # regexes
    "VERDICT_RE", "DECISION_RE", "CHANGE_RE", "LEDGER_RE", "REASON_RE", "LOOK_SOURCE_RE",
    "KEPT_RE", "DROPPED_RE", "STOPPED_RE", "NEXT_RE", "PROBLEM_RE", "STEP_RE", "AFTER_RE",
    "ROUND_RE", "UPGRADED_FILE_RE", "LIMIT_RE", "REVIEWERS_RE", "SINCE_RE", "STUCK_RE",
    "UNTESTABLE_RE", "MOVES_RE", "TRAIN_RE", "WAITS_RE", "GATE_FAIL_RE", "ATTEMPT_VERDICT_RE",
    "BUILD_RE", "SECONDS_RE", "WAITED_RE", "DEPTH_RE", "TRAIN_GATE_RE",
    # constants and paths
    "REASON_KINDS", "DECIDED", "SETTLED", "STOPPED", "STEP", "LAND_STEP", "LAND_STOPS",
    "LAND_STEPS", "AGENT_TIMEOUT", "RECONSIDER", "VERIFIED", "COSTS", "LAND_TIMES", "PAUSES",
    "REVIEWERS", "OPEN_BOX", "NO_DECISION", "GARBLED_LEDGER", "HAND_GATE", "CLONE_MARK",
    "HOME_MARK", "TMP_MARK", "USER_MARK", "TERM_MARK", "DEFUSE", "TERMS_FILE", "DECISION_FILE",
    "LEDGER_FILE", "BUILDER_SESSIONS", "SESSIONS", "ARCHIVE_RE", "MENDED", "KEPT_ANSWER",
    "CONFIRMED", "SUPERSEDED", "LOOK_SEEN", "PURPOSES", "WASTE", "EJECTIONS", "PARTS",
    "LAND_TRAIN", "LAND_ACCEPT",
    # readers
    "opening", "no_verdict", "read_stop", "read_land_stop", "landing", "first_build",
    "upgraded_build", "newest_round", "reasons", "reading", "read_step", "read_land_step",
    "read_land_times", "cost", "card_reading", "reviewed", "builder_started", "run_counts",
    "session_roles", "session_models", "gate_kind", "gate_seconds", "gate_attempts", "_login",
    "_terms", "placeholders", "timed_rows", "land_sinces", "autonomy_counts", "spend_rows",
    "read_gate_attempts", "resolved_files", "pipeline_counts",
    # 180: the overrides retro reads, and core's reader of a fix asked at landing.
    "ejections", "land_asks", "LAND_ASK_RE",
}  # fmt: skip

# R3: the names the copies had before, in `sdlc.py`, `closing.py` and `board.py`.
OLD_NAMES = {
    *(f"FACTORY_{n}" for n in (
        "VERDICT_RE", "DECISION_RE", "CHANGE_RE", "LEDGER_RE", "REASON_RE", "LOOK_SOURCE_RE",
        "KEPT_RE", "DROPPED_RE", "STOPPED_RE", "NEXT_RE", "PROBLEM_RE", "STEP_RE", "AFTER_RE",
        "ROUND_RE", "UPGRADED_FILE_RE", "GATE_FAIL_RE", "REASON_KINDS", "DECIDED", "SETTLED",
        "STOPPED", "STEP", "LAND_STEP", "LAND_STOPS", "LAND_STEPS", "AGENT_TIMEOUT",
        "RECONSIDER",
    )),
    "_factory_opening", "factory_stop", "factory_land_stop", "factory_landing",
    "factory_first_build", "factory_upgraded_build", "factory_newest_round", "factory_reasons",
    "factory_reading", "_gate_attempts", "_hand_placeholders", "_hand_login", "_hand_terms",
    "HAND_DEFUSE", "HAND_TERMS_FILE", "REVIEWER_ROLES", "_factory", "_reviewed", "_timed_rows",
    "_land_sinces",
}  # fmt: skip

# R4: core's own rules over the records, and the copies of what isn't a run's record.
CONSUMER_NAMES = {
    "needs_of", "column", "seen_stage", "answered", "decide_step", "touched_paths", "BY_STAGE",
    "FACTORY_STOP_NEEDS", "hand_gate", "hand_build", "cmd_gate", "GATE_TIMEOUT", "GATE_TAIL",
    "SLOT_NAME", "_try_lock", "_gate_jobs_at", "FACTORY_CONFIG", "_ui_at", "_current_shots",
    "UI_DEFAULTS",
}  # fmt: skip

# A name a script defines for something of its own that a record's copy shares: `sdlc.py`'s
# `MOVES_RE` reads the direction doc's `**Moves O<n>:**`, never a landing's `MOVES:` line.
UNRELATED = {("sdlc.py", "MOVES_RE")}

# R5: the factory's records by name. Kept here, so the module can't loosen it.
RECORD_FILES = (
    "decision.md", "decisions.md", "stopped.md", "step.md", "verified.md", "costs.jsonl",
    "land-times.jsonl", "gate.md", "round-", ".sessions", "ejections.jsonl", "land-train.md",
    "land-accept.md", ".ask.md",
)  # fmt: skip


def _loads_of(tree: ast.AST, name: str) -> list[int]:
    """The lines of every `spec_from_file_location` call naming `name` in a constant."""
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "spec_from_file_location"
        and any(
            isinstance(c, ast.Constant) and isinstance(c.value, str) and name in c.value
            for arg in node.args
            for c in ast.walk(arg)
        )
    ]


def _docstrings(tree: ast.AST) -> set[int]:
    """The ids of every docstring's node: a module's, a class's or a function's first string."""
    found = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        first = body[0] if body else None
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            found.add(id(first.value))
    return found


def _strings(tree: ast.AST) -> list[ast.Constant]:
    """Every string constant but a docstring, f-string pieces included."""
    docs = _docstrings(tree)
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs
    ]


def _names_a_record(source: str) -> list[str]:
    """R5's checker: each string literal in `source` that names a factory record and holds no
    whitespace (prose does), as `line N: 'text'`."""
    return [
        f"line {node.lineno}: {node.value!r}"
        for node in _strings(ast.parse(source))
        if not any(ch.isspace() for ch in node.value)
        and any(name in node.value for name in RECORD_FILES)
    ]


def test_factory_records_is_pure_and_loaded_once() -> None:
    """163 R1: `sdlc.py` loads the module by path, once, and binds nothing into it; the module
    runs no process, names no `sdlc`, loads nothing, and only defines names while it loads."""
    assert RECORDS_PY.exists(), "scripts/factory_records.py is missing"
    scripts = [
        *sorted((ROOT / "scripts").glob("*.py")),
        *(ROOT / "scripts" / "trackers").glob("*.py"),
    ]
    sites = {p.name: _loads_of(_tree(p), "factory_records.py") for p in scripts}
    sites = {k: v for k, v in sites.items() if v}
    assert list(sites) == ["sdlc.py"] and len(sites["sdlc.py"]) == 1, sites
    tree = _tree(RECORDS_PY)
    names = (
        _named(tree)
        | _reached(tree, "importlib")
        | {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in node.names
        }
        | {(n.module or "") for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    )
    assert "subprocess" not in names, "the module runs no process"
    assert "sdlc" not in names, "the module names no sdlc"
    assert "importlib" not in names and not _loads_of(tree, ""), "the module loads nothing"
    loads = [n.value for n in _strings(tree) if "sdlc.py" in n.value or "factory.py" in n.value]
    assert not loads, f"the module names a script outside its docstrings: {loads}"
    kinds = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign)
    docs = _docstrings(tree)
    acts = [
        node.lineno
        for node in tree.body
        if not isinstance(node, kinds)
        and not (isinstance(node, ast.Expr) and id(node.value) in docs)
    ]
    assert not acts, f"the module does more than define names at load: lines {acts}"
    sdlc = _load("sdlc_records_test", SDLC_PY)
    assert not hasattr(sdlc.factory_records, "sdlc"), "sdlc binds nothing into the module"
    assert Path(sdlc.factory_records.__file__).name == "factory_records.py"


def test_the_board_and_close_read_records_through_sdlc() -> None:
    """163 R2: the board and close reach the module as `sdlc.factory_records`, never loading or
    naming it on their own, so they and `status` read through one module object; retro too (169
    R10)."""
    for path in (BOARD_PY, CLOSING_PY, RETRO_PY):
        tree = _tree(path)
        assert not _loads_of(tree, "factory_records"), f"{path.name} loads the module"
        assert "factory_records" not in _named(tree), f"{path.name} names it bare"
        assert "factory_records" in _reached(tree, "sdlc"), f"{path.name} reads no record"
    sdlc = _load("sdlc_records_bound_test", SDLC_PY)
    assert sdlc.factory_records is sdlc._load_board().sdlc.factory_records
    assert sdlc.factory_records is sdlc.closing.sdlc.factory_records
    assert sdlc.factory_records is sdlc.retro.sdlc.factory_records


def test_the_record_readers_live_in_factory_records() -> None:
    """163 R3, R4: every copy is defined in the module and nowhere else, under no old name, and
    core's own rules over the records stay in `sdlc.py`."""
    defined = _defined(_tree(RECORDS_PY))
    assert not RECORD_NAMES - defined, f"the module lacks {sorted(RECORD_NAMES - defined)}"
    for path in (SDLC_PY, CLOSING_PY, BOARD_PY, RETRO_PY):
        left = (RECORD_NAMES | OLD_NAMES) & _defined(_tree(path))
        left -= {name for script, name in UNRELATED if script == path.name}
        assert not left, f"{path.name} still defines {sorted(left)}"
    script = _defined(_tree(SDLC_PY))
    assert not CONSUMER_NAMES - script, f"sdlc.py lacks {sorted(CONSUMER_NAMES - script)}"
    moved = CONSUMER_NAMES & defined
    assert not moved, f"the module took core's own rules: {sorted(moved)}"


def test_no_factory_record_is_named_outside_its_reader() -> None:
    """163 R5: no string in the core's scripts but the module's names a factory record, outside a
    docstring or a line of prose; the checker is shown to catch one first."""
    assert _names_a_record('text = (folder / "decision.md").read_text()\n')
    assert _names_a_record('p = f"{branch}:{folder}/runs/costs.jsonl"\n')
    assert not _names_a_record('def f():\n    """Reads `decision.md`."""\n')
    assert not _names_a_record('help = "into build/gate.md; never pre-approved"\n')
    scripts = [*(ROOT / "scripts").glob("*.py"), *(ROOT / "scripts" / "trackers").glob("*.py")]
    found = {
        p.name: hits
        for p in sorted(scripts)
        if p != RECORDS_PY and (hits := _names_a_record(p.read_text(encoding="utf-8")))
    }
    assert not found, f"a factory record named outside factory_records.py: {found}"


def _comparable(value) -> bool:
    if isinstance(value, tuple):
        return all(_comparable(v) for v in value)
    return isinstance(value, str | int | float | Path | re.Pattern)


def _shape(value):
    if isinstance(value, tuple):
        return tuple(_shape(v) for v in value)
    if isinstance(value, re.Pattern):
        return ("pattern", value.pattern, value.flags)
    return value


def test_every_shared_name_is_the_factorys() -> None:
    """163 R6: each constant, regex and path the module shares with `factory.py` by name has the
    factory's value, so a copy added later under the factory's name is pinned with no new test."""
    records = _load("factory_records_pins", RECORDS_PY)
    factory = _load("factory_records_theirs", FACTORY_PY)
    shared = {
        name
        for name in set(vars(records)) & set(vars(factory))
        if not name.startswith("__") and _comparable(getattr(records, name))
    }
    assert {"LEDGER_RE", "STOPPED", "LAND_STEPS", "NO_DECISION", "REVIEWERS"} <= shared, shared
    assert _shape(re.compile("a")) != _shape(re.compile("a", re.I)), "flags count"
    drift = sorted(
        name for name in shared if _shape(getattr(records, name)) != _shape(getattr(factory, name))
    )
    assert not drift, f"these differ from factory.py's: {drift}"


def test_land_ask_re_reads_the_factorys_path(tmp_path) -> None:
    """180 R11: `LAND_ASK_RE` is core's own name for the file `factory.py`'s `land_ask_path()`
    writes, so it is pinned to that function, not to a name the two share."""
    records = _load("factory_records_ask", RECORDS_PY)
    factory = _load("factory_records_ask_theirs", FACTORY_PY)
    folder = tmp_path / "001-reopen-drafts"
    rel = factory.land_ask_path(folder, 3).relative_to(folder).as_posix()
    assert records.LAND_ASK_RE.match(rel), rel
    assert records.land_asks(lambda _: f"{rel}\nbuild/round-1.md") == 1


def test_look_seen_is_the_decide_skills_answer() -> None:
    """169 R10: `LOOK_SEEN` is core's own name for the answer the decide skill writes on a look the
    person acknowledged as it stood, so it is pinned to that skill's words, not to `factory.py`."""
    records = _load("factory_records_look", RECORDS_PY)
    skill = (ROOT / "plugins" / "factory" / "skills" / "decide" / "SKILL.md").read_text("utf-8")
    assert f"`→ decided: {records.LOOK_SEEN}`" in skill
    assert f"`{records.KEPT_ANSWER}`" in skill
