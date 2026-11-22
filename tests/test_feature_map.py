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


# ---------------------------------------------------------------- one meaning per word (187)

# Each term the vocabulary defines once, saying what it means now and what it never means.
VOCABULARY = ("gate", "slow gate", "approval", "WAIT", "acceptance checks", "vet", "arbiter",
              "verification", "validation", "parked")  # fmt: skip


def test_every_vocabulary_term_has_an_entry() -> None:
    """187 R6: each term has its entry, and `gate` no longer says it is a person's approval."""
    entries = _entries()
    assert [t for t in VOCABULARY if t not in entries] == []
    assert "approval at a WAIT" not in entries["gate"]
    for term in ("stop", "Sdlc-Stage", "Sdlc-AfterGate", "Sdlc-Landed"):
        assert "approval" in entries[term], term


# A phrasing that no longer means what it once did, and the word to write instead. Matched in
# prose only, inline code and fenced blocks stripped, case-insensitively.
RETIRED_PHRASINGS = (
    (r"\bverifier\b", "arbiter"),
    (r"\bhuman gates?\b", "approval"),
    (r"\bWAIT gates?\b", "approval"),
    (r"\bapproval gates?\b", "approval"),
    (r"\bgates? at (a|the|every|each) (WAIT|stage)\b", "approval"),
    (r"\bgated (skill|span)s?\b", "a skill with a WAIT, the WAIT's span"),
    (r"\bslower (check|gate)\b", "slow gate"),
    (r"\baccepted as shown\b", "approved"),
    (r"\byes accepts\b", "approved"),
    (r"\b(the|its|a change's|the change's|own) checks\b", "acceptance checks, or acceptance"),
)
# A name the code no longer answers to, matched in code and prose alike.
RETIRED_NAMES = (
    r"sdlc\.py['\"]?\s+check\b",
    r"`check --strict`",
    r"sdlc-factory:verifier",
    r"\bland-verify\b",
    r"--task verify\b",
    r"agents/verifier\.md",
    r"prompts/(land-)?verify\.md",
)
# The one paragraph that names the old command on purpose, to say it is gone: REFERENCE.md's
# *After an update*, which a host reads to move its CI. Every line of it is exempt, and it must
# still be there, so the exemption never outlives it.
RENAME_NOTE = ("docs/REFERENCE.md", "**`sdlc.py check` is now `sdlc.py vet`.**")
# What history holds is left as it was written: the change folders, the retrospectives and the
# direction doc they keep.
PROSE = (
    "AGENTS.md",
    "README.md",
    "docs/*.md",
    "guide/*.md",
    "defaults/*.md",
    "templates/*.md",
    "skills/**/*.md",
    "agents/*.md",
    ".sdlc/SDLC.md",
    ".sdlc/REVIEW.md",
    ".sdlc/PRODUCT.md",
    "plugins/factory/README.md",
    "plugins/factory/agents/**/*.md",
    "plugins/factory/prompts/**/*.md",
    "plugins/factory/skills/**/*.md",
)
MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "plugins/factory/.claude-plugin/plugin.json",
)


def _prose_files(root: Path) -> list[Path]:
    return sorted({p for pattern in PROSE for p in root.glob(pattern) if p.is_file()})


def _descriptions(root: Path) -> dict[str, str]:
    """Each manifest's descriptions, the plugins' entries in the marketplace's included."""
    import json

    found = {}
    for rel in MANIFESTS:
        path = root / rel
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        texts = [data.get("description")]
        texts += [p.get("description") for p in data.get("plugins", [])]
        texts += [(data.get("metadata") or {}).get("description")]
        found[rel] = "\n".join(t for t in texts if isinstance(t, str))
    return found


def _strip_code(text: str) -> str:
    """`text` with fenced blocks blanked line for line, then each inline code span, so a line
    number still names the line it was."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else re.sub(r"`+[^`]*`+", "", line))
    return "\n".join(out)


def _retired_phrasings(texts: dict[str, str]) -> list[str]:
    found = []
    for name, text in texts.items():
        for n, line in enumerate(_strip_code(text).splitlines(), 1):
            for pattern, instead in RETIRED_PHRASINGS:
                if m := re.search(pattern, line, re.I):
                    found.append(f"{name}:{n}: {m[0]!r}, write {instead}")
    return found


def _retired_names(texts: dict[str, str]) -> list[str]:
    found = []
    for name, text in texts.items():
        note = False
        for n, line in enumerate(text.splitlines(), 1):
            if name == RENAME_NOTE[0] and line.startswith(RENAME_NOTE[1]):
                note = True
            elif not line.strip():
                note = False
            if note:
                continue
            for pattern in RETIRED_NAMES:
                if m := re.search(pattern, line):
                    found.append(f"{name}:{n}: {m[0]!r}")
    return found


def _prose(root: Path) -> dict[str, str]:
    texts = {p.relative_to(root).as_posix(): _text(p) for p in _prose_files(root)}
    return {**texts, **_descriptions(root)}


def test_no_doc_uses_a_retired_phrasing(tmp_path: Path) -> None:
    """187 R10: no doc, skill, agent or manifest uses a word in a meaning it no longer has. A
    fixture doc holding each phrasing, in prose and in code, proves each pattern matches prose."""
    # One phrasing a line, so adding or removing one is a one-line edit.
    lines = [
        "The verifier keeps it.",
        "A human gate.",
        "Each WAIT gate.",
        "The approval gates.",
        "A gate at every stage.",
        "Gates at the WAIT.",
        "A gated skill.",
        "The gated spans.",
        "The slower check.",
        "A slower gate.",
        "Its cases accepted as shown.",
        "The yes accepts it.",
        "It runs the checks.",
        "Its checks pass.",
        "A change's checks.",
        "The change's checks.",
        "Its own checks.",
    ]
    code = "Not prose: `the verifier`, `Sdlc-AfterGate`.\n\n```sh\nits checks\n```\n"
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "fixture.md").write_text(
        "\n".join(lines) + "\n" + code, encoding="utf-8", newline="\n"
    )
    found = _retired_phrasings(_prose(tmp_path))
    assert len(found) == len(lines), found
    assert [int(f.split(":")[1]) for f in found] == list(range(1, len(lines) + 1))
    assert _retired_phrasings(_prose(ROOT)) == []


def test_no_file_names_a_retired_name(tmp_path: Path) -> None:
    """187 R11: nothing calls a command, agent, task or file by the name it no longer has, in code
    or prose."""
    names = [
        "uv run --script sdlc.py check --strict", "run `check --strict`",
        "sdlc-factory:verifier", "--task land-verify", "agent 001 --task verify",
        "agents/verifier.md", "prompts/verify.md", "prompts/land-verify.md",
    ]  # fmt: skip
    (tmp_path / "skills" / "x").mkdir(parents=True)
    (tmp_path / "skills" / "x" / "SKILL.md").write_text(
        "\n".join(names) + "\nsdlc.py checks 001\nsdlc.py vet --strict\n", encoding="utf-8"
    )
    found = _retired_names(_prose(tmp_path))
    assert sorted({int(f.split(":")[1]) for f in found}) == list(range(1, len(names) + 1)), found
    assert _retired_names(_prose(ROOT)) == []
    reference = _text(ROOT / RENAME_NOTE[0])
    assert any(line.startswith(RENAME_NOTE[1]) for line in reference.splitlines()), (
        "the note the exemption names is gone: drop the exemption"
    )


def test_agents_md_fits_100_columns() -> None:
    """187 R20 (nit 2026-11-19-41): no line of AGENTS.md runs past 100 columns."""
    lines = _text(ROOT / "AGENTS.md").splitlines()
    assert [n for n, line in enumerate(lines, 1) if len(line) > 100] == []
