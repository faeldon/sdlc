"""160: each command in `sdlc.py` and `factory.py` declares its own parser beside its handler, in
the script's registry (`command()`), and `main` builds the parsers from it and dispatches, so a
change to one command edits only that command. These read source or load the scripts, and run
nothing."""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.portable

ROOT = Path(__file__).resolve().parents[1]
SDLC_PY = ROOT / "scripts" / "sdlc.py"
FACTORY_PY = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
SCRIPTS = [pytest.param(SDLC_PY, id="sdlc"), pytest.param(FACTORY_PY, id="factory")]
BUILDERS = {"add_parser", "add_argument", "add_mutually_exclusive_group"}
HELPERS = ("UsageError", "Command", "arg", "exclusive", "command", "_parser")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_LOADED: dict[Path, object] = {}


def _script(path: Path):
    if path not in _LOADED:
        _LOADED[path] = _load(path, f"registry_{path.stem}")
    return _LOADED[path]


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _top(tree: ast.Module, name: str) -> ast.AST:
    (node,) = [
        n for n in tree.body if isinstance(n, ast.FunctionDef | ast.ClassDef) and n.name == name
    ]
    return node


@pytest.mark.parametrize("path", SCRIPTS)
def test_every_parser_is_built_by_the_registry(path: Path) -> None:
    """R1: the argparse builder calls sit only in `_parser`, and `main` neither compares
    `args.cmd` nor names a registered command, so it can't grow back."""
    tree = _tree(path)
    inside = {id(n) for n in ast.walk(_top(tree, "_parser"))}
    outside = [
        (node.func.attr, node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in BUILDERS
        and id(node) not in inside
    ]
    assert not outside, f"{path.name} builds a parser outside the registry: {outside}"
    main = _top(tree, "main")
    compares = [
        node.lineno
        for node in ast.walk(main)
        if isinstance(node, ast.Compare)
        and any(
            isinstance(sub, ast.Attribute) and sub.attr == "cmd"
            for part in [node.left, *node.comparators]
            for sub in ast.walk(part)
        )
    ]
    assert not compares, f"{path.name}'s main compares args.cmd at {compares}"
    names = set(_script(path).COMMANDS)
    named = sorted(
        node.value
        for node in ast.walk(main)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in names
    )
    assert not named, f"{path.name}'s main names commands: {named}"


@pytest.mark.parametrize("path", SCRIPTS)
def test_each_command_sits_beside_its_handler(path: Path) -> None:
    """R2: an adapter calling exactly one `cmd_*` of its own script is the next top-level function
    after it."""
    mod, tree = _script(path), _tree(path)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    defined = {n.name for n in functions}
    after = {a.name: b.name for a, b in zip(functions, functions[1:], strict=False)}
    misplaced = []
    for name, entry in mod.COMMANDS.items():
        adapter = _top(tree, entry.run.__name__)
        called = {
            node.func.id
            for node in ast.walk(adapter)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id.startswith("cmd_")
            and node.func.id in defined
        }
        if len(called) == 1:
            (handler,) = called
            if after.get(handler) != adapter.name:
                misplaced.append((name, handler, after.get(handler)))
    assert not misplaced, f"{path.name}: adapters not beside their handler: {misplaced}"


def test_main_runs_a_stand_in_handler(monkeypatch, tmp_path) -> None:
    """R7: an adapter reaches its handler through the script's globals when it runs, so a stand-in
    set on the script is what `main()` runs."""
    sdlc = _load(SDLC_PY, "registry_sdlc_stand_in")
    monkeypatch.setattr(sdlc, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(sdlc, "main_root", lambda root: tmp_path)
    monkeypatch.setattr(sdlc, "cmd_config", lambda root: 41)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "config"])
    assert sdlc.main() == 41
    # No command at all runs `status`, looked up as it runs too, and without `--all`.
    seen = []
    monkeypatch.setattr(sdlc, "cli_status", lambda root, home, args: seen.append(args) or 40)
    monkeypatch.setattr(sys, "argv", ["sdlc.py"])
    assert sdlc.main() == 40
    assert seen[0].cmd is None and getattr(seen[0], "all", False) is False
    factory = _load(FACTORY_PY, "registry_factory_stand_in")
    monkeypatch.setattr(factory, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(factory, "cmd_config", lambda root: 42)
    monkeypatch.setattr(sys, "argv", ["factory.py", "config"])
    assert factory.main() == 42


def test_the_permission_lists_name_registered_commands() -> None:
    """R9: every command `READ_ONLY`, `ALLOW_RULES` and `OWN_SCRIPT_CMDS` name is registered."""
    sdlc = _script(SDLC_PY)
    rules = [re.fullmatch(r".*/sdlc\.py (\S+) \*\)", r) for r in sdlc.ALLOW_RULES]
    assert all(rules), sdlc.ALLOW_RULES
    named = [*sdlc.READ_ONLY, *(m.group(1) for m in rules), *sdlc.OWN_SCRIPT_CMDS]
    unknown = sorted(set(named) - set(sdlc.COMMANDS))
    assert not unknown, f"not registered: {unknown}"


@pytest.mark.parametrize("path", SCRIPTS)
def test_a_command_registered_twice_is_refused(path: Path) -> None:
    """R10: a second registration of one name fails, naming the command."""
    mod = _load(path, f"registry_twice_{path.stem}")
    mod.command("twice", "once")(lambda *a: 0)
    with pytest.raises(ValueError, match="twice"):
        mod.command("twice", "again")(lambda *a: 0)


@pytest.mark.parametrize("path", SCRIPTS)
def test_help_order_names_only_registered_commands(path: Path) -> None:
    """R11: `HELP_ORDER` names each command at most once and only registered ones; a command it
    leaves out follows the named ones."""
    mod = _script(path)
    order = list(mod.HELP_ORDER)
    assert len(order) == len(set(order)), "HELP_ORDER names a command twice"
    unknown = sorted(set(order) - set(mod.COMMANDS))
    assert not unknown, f"HELP_ORDER names unregistered commands: {unknown}"
    listed = list(mod._parser("d", False)._subparsers._group_actions[0].choices)
    rest = [n for n in mod.COMMANDS if n not in order]
    assert listed == [n for n in order] + rest


def _source(path: Path, name: str) -> str:
    node = _top(_tree(path), name)
    if ast.get_docstring(node) is not None and isinstance(node, ast.FunctionDef):
        node.body = node.body[1:]
    return ast.unparse(node)


@pytest.mark.parametrize("name", HELPERS)
def test_the_registry_copies_match(name: str) -> None:
    """R12: `factory.py` never imports `sdlc.py`, so it keeps a copy of the registry, pinned."""
    assert _source(FACTORY_PY, name) == _source(SDLC_PY, name)
