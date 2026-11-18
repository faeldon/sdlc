"""153: close, the push and the main lock live in `scripts/closing.py`, and the factory's landing
in `plugins/factory/scripts/landing.py`, each loaded by path and bound to a live view of its
script's names, so `[review] sensitive` can name them and a change elsewhere in either script
stays light. These read source: where the code lives, where the line between script and module
falls, and that neither module does anything while it loads."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.portable

ROOT = Path(__file__).resolve().parents[1]
SDLC_PY = ROOT / "scripts" / "sdlc.py"
CLOSING_PY = ROOT / "scripts" / "closing.py"
FACTORY_PY = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
LANDING_PY = ROOT / "plugins" / "factory" / "scripts" / "landing.py"

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
    pytest.param(FACTORY_PY, LANDING_PY, "landing", "factory", LANDING_NAMES, [], id="landing"),
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


def test_the_landing_lives_in_landing() -> None:
    """R2, by its own name."""
    test_the_named_code_lives_in_its_module(FACTORY_PY, LANDING_PY, LANDING_NAMES)


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


@pytest.mark.parametrize("path", [FACTORY_PY, LANDING_PY], ids=lambda p: p.name)
def test_the_factory_never_loads_sdlc_py(path: Path) -> None:
    """R9: `factory.py` and `landing.py` never import `sdlc.py` nor load it by path; the factory
    runs `sdlc.py` as a process (`_sdlc()`), and copies what it parses."""
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
