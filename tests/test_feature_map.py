"""The two maps (179): `docs/FEATURES.md`, every feature a host gets with its definition, where it
is specified and what it depends on, and `docs/PROCESS.md`, the change, release and retro loops.
Both are prose, kept by hand, and checked here against the code: a term the code fixes, a skill,
a stage or a WAIT missing from them fails.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.portable

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "docs" / "FEATURES.md"
PROCESS = ROOT / "docs" / "PROCESS.md"
FACTORY = ROOT / "plugins" / "factory"


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_feature_map", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

ENTRY_RE = re.compile(r"^- \*\*`([^`]+)`\*\*: (.+)$")
SPECIFIED_RE = re.compile(r"Specified: `([^`]+)`\.")
DEPENDS_RE = re.compile(r"Depends on: (.+)\.$")
NODE_RE = re.compile(r"^\s*\w+\[\"([^\"]+)\"\]", re.M)
# A trailer's key where the code writes it: a string starting `Sdlc-<Key>`.
TRAILER_RE = re.compile(r"[\"']Sdlc-([A-Z][A-Za-z]*)\b")
TRAILER_WRITERS = ("scripts/metrics.py", "scripts/sdlc.py", "scripts/closing.py")
COLUMN_RE = re.compile(r'\{ key: "[a-z-]+", label: "([^"]+)"')
CHANGE_RE = re.compile(r"\b\d{3}-[a-z]")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _entries() -> dict[str, str]:
    """Each entry's term and the rest of its line."""
    found = {}
    for line in _text(FEATURES).splitlines():
        m = ENTRY_RE.match(line)
        if m:
            assert m[1] not in found, f"{m[1]} has two entries"
            found[m[1]] = m[2]
    return found


def _skills() -> dict[str, Path]:
    """Every skill as it is typed, `/sdlc:ship`, and its `SKILL.md`."""
    core = {f"/sdlc:{p.parent.name}": p for p in (ROOT / "skills").glob("*/SKILL.md")}
    more = {f"/sdlc-factory:{p.parent.name}": p for p in (FACTORY / "skills").glob("*/SKILL.md")}
    return {**core, **more}


def _fixed_terms() -> set[str]:
    """Every term the code fixes, as the map writes it."""
    terms = {f"stage: {s}" for s in sdlc.STAGES}
    terms |= {f"Tier {t}" for t in (0, *sdlc.TIER_ARTIFACTS)}
    terms |= {f"impact: {i}" for i in sdlc.IMPACTS}
    terms |= {f"Cost: {c}" for c in sdlc.NIT_COSTS} | {f"Value: {v}" for v in sdlc.NIT_VALUES}
    terms |= set(sdlc.FINDING_PASSES) | set(sdlc.SHIP_PASSES)
    terms |= set(_skills())
    terms |= set(COLUMN_RE.findall(_text(ROOT / "scripts" / "board.html")))
    for rel in TRAILER_WRITERS:
        terms |= {f"Sdlc-{k}" for k in TRAILER_RE.findall(_text(ROOT / rel))}
    return terms


def test_every_fixed_term_has_an_entry() -> None:
    """R11: a stage, tier, impact, nit cost or value, review pass, skill, board column or trailer
    the code fixes, with no entry in the feature map, fails here."""
    entries = _entries()
    assert {"stage: build", "Tier 0", "/sdlc-factory:build", "Needs you", "Sdlc-Skill"} <= (
        _fixed_terms()
    ), "the terms are read from the code"
    assert sorted(_fixed_terms() - set(entries)) == []


def test_the_feature_map_points_at_real_things() -> None:
    """R12: every entry's `Specified:` path exists, every `Depends on:` term is another entry's,
    and the graph's nodes are the `##` sections, one each."""
    entries = _entries()
    for term, rest in entries.items():
        spec = SPECIFIED_RE.search(rest)
        assert spec, f"{term}: no Specified: path"
        assert (ROOT / spec[1]).exists(), f"{term}: {spec[1]} doesn't exist"
        depends = DEPENDS_RE.search(rest)
        assert depends, f"{term}: no Depends on:"
        if depends[1] != "nothing":
            named = re.findall(r"`([^`]+)`", depends[1])
            assert named, f"{term}: Depends on: names no term"
            assert set(named) <= set(entries) - {term}, f"{term}: {set(named) - set(entries)}"
    text = _text(FEATURES)
    graph = re.search(r"```mermaid\n(graph [A-Z]{2}\n.*?)```", text, re.S)
    assert graph, "one Mermaid graph"
    sections = re.findall(r"^## (.+)$", text, re.M)
    assert sorted(NODE_RE.findall(graph[1])) == sorted(sections)


def test_the_process_map_holds_every_stage_skill_and_wait() -> None:
    """R13: every skill is on the map, every stage written `stage: <value>`, and its `WAIT:` nodes
    are exactly the skills whose `SKILL.md` has a WAIT heading."""
    text = _text(PROCESS)
    assert len(re.findall(r"^```mermaid\nflowchart ", text, re.M)) == 3, "three loops"
    assert [s for s in _skills() if s not in text] == []
    assert [s for s in sdlc.STAGES if f"stage: {s}" not in text] == []
    gated = {
        name
        for name, path in _skills().items()
        if any(ln.startswith("#") and "WAIT" in ln for ln in _text(path).splitlines())
    }
    assert set(re.findall(r"WAIT: (/sdlc(?:-factory)?:[a-z-]+)", text)) == gated


@pytest.mark.parametrize("path", [FEATURES, PROCESS], ids=lambda p: p.name)
def test_the_maps_cite_no_change_and_hold_no_html(path: Path) -> None:
    """R14: neither map cites a change by its folder number, and neither is generated HTML."""
    text = _text(path)
    assert [ln for ln in text.splitlines() if CHANGE_RE.search(ln)] == []
    assert not re.search(r"<(html|div|svg|script)\b", text, re.I)
    assert not list((ROOT / "docs").glob("*.html"))
