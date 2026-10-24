"""Every doc and template the plugin ships takes one shape, so a person who has filled in one
knows where everything is in the next.

Top to bottom: frontmatter only where the plugin reads keys, holding keys only; one `# ` title,
the doc's plain name (a change template keeps `# NNN — TITLE`); a `>` note saying what the file
is for and what the plugin reads from it; then `##` sections, with every `<…>` prompt inside one.
No `---` rules, and no heading that skips a level. A doc's note stays in a host's copy, so it is
written to be true there.

Files are found by glob, so a new default is held to this without being listed here.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_defaults", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

EXCEPTIONS = {
    # Its text is the issue body, rendered verbatim into every issue: a title or note would
    # land on all of them.
    "templates/issue.md": "rendered verbatim into every issue",
}
CHANGE_TEMPLATES = {"templates/intent.md", "templates/spec.md", "templates/plan.md"}
FILES = sorted(
    p.relative_to(ROOT).as_posix()
    for p in [*ROOT.glob("defaults/*.md"), *ROOT.glob("templates/*.md")]
    if p.relative_to(ROOT).as_posix() not in EXCEPTIONS
)
DOC_TITLE_RE = re.compile(r"^# [A-Z][a-z]+( [a-z]+)?$")
CHANGE_TITLE_RE = re.compile(r"^# NNN — TITLE( · (spec|plan))?$")
KEY_LINE_RE = re.compile(r"^(# )?([A-Za-z_][\w-]*):")
HOST_COPY_RE = re.compile(r"\bdefaults?\b|the plugin's|when the host", re.IGNORECASE)
PROJECT_FRONTMATTER = ["# milestone: tracker", "# project: [Roadmap]", "# assignees: tracker"]


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _frontmatter(text: str) -> list[str] | None:
    if not text.startswith("---\n") or (end := text.find("\n---", 4)) == -1:
        return None
    return text[4:end].splitlines()


def _unfenced(text: str) -> list[str]:
    """The body's lines outside code fences, each as it stands."""
    lines, fenced = [], False
    for line in sdlc._body_of(text).splitlines():
        if sdlc.FENCE_RE.match(line):
            fenced = not fenced
        elif not fenced:
            lines.append(line)
    return lines


def _note(text: str) -> list[str]:
    """The block straight after the title, up to the first blank line."""
    lines = sdlc._body_of(text).splitlines()[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines[: lines.index("")] if "" in lines else lines


def frontmatter_problems(name: str, text: str) -> list[str]:
    """Only keys. A commented-out line must name a field the plugin reads, so `# Note: …` is
    prose however it's punctuated."""
    problems = []
    for line in _frontmatter(text) or []:
        m = KEY_LINE_RE.match(line)
        if not m or (m.group(1) and m.group(2) not in sdlc.PROJECT_FIELDS):
            problems.append(f"{name}: frontmatter line isn't a key: {line!r}")
    return problems


def title_problems(name: str, text: str) -> list[str]:
    body = sdlc._body_of(text).splitlines()
    titles = [line for line in _unfenced(text) if line.startswith("# ")]
    pattern = CHANGE_TITLE_RE if name in CHANGE_TEMPLATES else DOC_TITLE_RE
    problems = []
    if not body or not pattern.match(body[0]):
        problems.append(f"{name}: first line {body[0] if body else ''!r} isn't a plain-name title")
    if len(titles) != 1:
        problems.append(f"{name}: {len(titles)} `# ` titles, not one")
    return problems


def note_problems(name: str, text: str) -> list[str]:
    note = _note(text)
    if not note or not all(line.startswith(">") for line in note):
        return [f"{name}: no `>` note straight under the title"]
    return []


def host_copy_problems(name: str, text: str) -> list[str]:
    if name in CHANGE_TEMPLATES:
        return []  # the filled artifact replaces the note; it never reaches a host's doc
    found = [m.group(0) for line in _note(text) if (m := HOST_COPY_RE.search(line))]
    return [f"{name}: note says {w!r}, which is false in a host's copy" for w in found]


def prompt_problems(name: str, text: str) -> list[str]:
    problems = []
    for line in _unfenced(text):
        if line.startswith("## "):
            break
        if sdlc.PROMPT_RE.match(line):
            problems.append(f"{name}: prompt above the first `##`: {line[:50]!r}")
    return problems


def layout_problems(name: str, text: str) -> list[str]:
    problems, level = [], 0
    for line in _unfenced(text):
        if line.strip() == "---":
            problems.append(f"{name}: a `---` rule; sections are separated by `##` headings")
        elif m := sdlc.HEADING_RE.match(line):
            depth = len(m.group(1))
            if depth > level + 1:
                problems.append(f"{name}: {line!r} skips a heading level")
            level = depth
    return problems


RULES = [
    frontmatter_problems,
    title_problems,
    note_problems,
    host_copy_problems,
    prompt_problems,
    layout_problems,
]


@pytest.mark.parametrize("rule", RULES, ids=[r.__name__ for r in RULES])
@pytest.mark.parametrize("name", FILES)
def test_every_shipped_file_takes_the_shape(name: str, rule) -> None:
    assert rule(name, _text(name)) == []


def test_the_project_doc_frontmatter_is_only_its_fields_commented_out() -> None:
    text = _text("defaults/PROJECT.md")
    assert _frontmatter(text) == PROJECT_FRONTMATTER
    headings = [line for line in _unfenced(text) if line.startswith("## ")]
    assert headings == ["## Milestones", "## Projects", "## Assignees"]


def test_what_the_plugin_reads_from_the_defaults_is_unchanged(tmp_path: Path) -> None:
    (tmp_path / ".sdlc").mkdir()
    shutil.copy(ROOT / "defaults" / "PROJECT.md", tmp_path / ".sdlc" / "PROJECT.md")
    assert sdlc.project_doc(tmp_path, {"docs": {"project": ".sdlc/PROJECT.md"}}) == ({}, [])
    product = sdlc.product_items(_text("defaults/PRODUCT.md"))
    assert product["items"] == [] and product["problems"] == []
    for name in ("SDLC.md", "PROJECT.md", "PRODUCT.md"):
        assert sdlc.is_unfilled(ROOT / "defaults" / name), f"{name}'s prompts are what setup fills"


def test_the_exceptions_exist_and_say_why() -> None:
    for name, reason in EXCEPTIONS.items():
        assert (ROOT / name).is_file() and len(reason) > 10, name
    assert {"defaults/PROJECT.md", "templates/direction.md", "templates/intent.md"} <= set(FILES)


def test_a_file_out_of_shape_fails() -> None:
    name, text = "defaults/PRODUCT.md", _text("defaults/PRODUCT.md")
    title, rest = text.split("\n", 1)
    note_end = rest.index("\n\n", 1)
    note, after = rest[:note_end], rest[note_end:]
    broken = {
        note_problems: f"{title}\n\nNo note here.\n{after}",
        title_problems: f"{text}\n# A second title\n",
        prompt_problems: f"{title}\n{note}\n\n<A prompt above every section.>\n{after}",
        frontmatter_problems: f"---\n# Says what this is.\nmilestone: tracker\n---\n\n{text}",
        layout_problems: f"{text}\n---\n\n#### Too deep\n",
        host_copy_problems: text.replace("\n>", "\n> The plugin's default.\n>", 1),
    }
    for rule, mutated in broken.items():
        assert rule(name, mutated), f"{rule.__name__} let a broken copy through"
    colon = f"---\n# Note: uncomment one.\n# milestone: tracker\n---\n\n{text}"
    assert frontmatter_problems(name, colon), "a prose comment with a colon got through"


def test_every_shipped_file_has_the_reader_its_folder_promises(tmp_path: Path, capsys) -> None:
    """A template is what the plugin writes from, so `config` names it; a default is what setup
    copies, so `readiness` names it. A file neither names is one nobody reads."""
    (tmp_path / "README.md").write_text("a repo\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    capsys.readouterr()
    sdlc.cmd_config(tmp_path)
    templates = {
        Path(t["path"]).name for t in json.loads(capsys.readouterr().out)["templates"].values()
    }
    assert templates == {p.name for p in ROOT.glob("templates/*.md")}
    sdlc.cmd_readiness(tmp_path)
    defaults = {Path(d).name for d in json.loads(capsys.readouterr().out)["defaults"].values()}
    assert defaults == {p.name for p in ROOT.glob("defaults/*.md")}


def test_the_ideas_template_shows_the_heading_the_script_reads() -> None:
    note = " ".join(_note(_text("templates/ideas.md")))
    form = re.search(r"`(## \[YYYY-MM-DD\] \[seed\] <title>)`", note)
    assert form, "the note names the seed heading form"
    heading = form.group(1).replace("YYYY-MM-DD", "2026-10-24").replace("<title>", "A seed")
    assert sdlc.IDEA_RE.match(heading)
    assert not [line for line in _text("templates/ideas.md").splitlines() if line.startswith("## ")]


def test_the_factory_starts_notes_from_the_same_text_as_the_template() -> None:
    path = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
    spec = importlib.util.spec_from_file_location("factory_notes", path)
    factory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factory)
    assert _text("templates/notes.md") == factory.NOTES_HEAD
    assert "unticked `- [ ]` line" in factory.NOTES_HEAD


# This repo's own copies of the defaults it ships. An improvement made to one that any repo could
# use belongs in the default too, so the two are held together: the copy keeps every heading of
# the default in order (adding its own between them), and every review bullet word for word.
OWN_COPIES = {"defaults/SDLC.md": ".sdlc/SDLC.md", "defaults/REVIEW.md": ".sdlc/REVIEW.md"}


def _headings(text: str) -> list[str]:
    return [line for line in text.splitlines() if re.match(r"#{1,4} ", line)]


def _in_order(wanted: list[str], have: list[str]) -> bool:
    rest = iter(have)
    return all(any(w == h for h in rest) for w in wanted)


@pytest.mark.parametrize(("default", "copy"), OWN_COPIES.items())
def test_this_repos_copy_keeps_the_defaults_sections(default: str, copy: str) -> None:
    assert _in_order(_headings(_text(default)), _headings(_text(copy))), (
        f"{copy} has lost or reordered a section of {default}: move the change to both"
    )
    assert not [ln for ln in _text(copy).splitlines() if ln == "---"], f"{copy} has a `---` rule"


def test_this_repos_review_keeps_every_default_failure_class() -> None:
    bullets = re.findall(r"^- \*\*.*?(?=\n(?:- |\n|$))", _text("defaults/REVIEW.md"), re.M | re.S)
    assert bullets, "the default's bullets were read"
    missing = [b.splitlines()[0] for b in bullets if b not in _text(".sdlc/REVIEW.md")]
    assert not missing, f".sdlc/REVIEW.md differs from defaults/REVIEW.md at: {missing}"


def test_a_copy_that_drops_a_section_fails() -> None:
    assert not _in_order(["## A", "## B"], ["## B", "## A"])
    assert not _in_order(["## A", "## B"], ["## A"])
    assert _in_order(["## A", "## B"], ["## A", "## Own", "## B"])
