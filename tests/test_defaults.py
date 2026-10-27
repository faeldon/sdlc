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
    for p in [*ROOT.glob("defaults/*.md"), *ROOT.glob("templates/*.md"), *ROOT.glob("guide/*.md")]
    if p.relative_to(ROOT).as_posix() not in EXCEPTIONS
)
# The guides are read in place from the plugin and never copied into a host, so their notes say
# what the plugin does; every other shipped doc's note stays in a host's copy.
GUIDES = {"defaults/SDLC.md": "guide/process.md", "defaults/REVIEW.md": "guide/review.md"}
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
    if name in CHANGE_TEMPLATES or name in GUIDES.values():
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


def test_the_inbox_template_shows_the_heading_the_script_reads() -> None:
    note = " ".join(_note(_text("templates/inbox.md")))
    form = re.search(r"`(## \[YYYY-MM-DD-n\] \[idea\] <title>)`", note)
    assert form, "the note names the idea heading form"
    heading = form.group(1).replace("YYYY-MM-DD-n", "2026-10-24-1").replace("<title>", "A seed")
    assert sdlc._heading_entry(heading)["id"] == "2026-10-24-1"
    assert not [line for line in _text("templates/inbox.md").splitlines() if line.startswith("## ")]


def test_the_inbox_note_defines_seed_and_its_kinds() -> None:
    """Someone reading only the note can tell a seed (any entry) from an idea (one kind)."""
    note = " ".join(line.lstrip("> ") for line in _note(_text("templates/inbox.md")))
    assert "Every entry is a **seed**" in note
    for tag in ("[idea]", "[bug]", "[nit]", "[building]", "[seed]"):
        assert f"`{tag}`" in note, tag
    assert "`[seed]` tag, from before ideas had their own, reads as `[idea]`" in note


def test_the_process_guide_names_the_seed_kinds_and_the_change_types() -> None:
    text = _text("guide/process.md")
    section = text.split("### Seeds, and the changes they become\n", 1)[1].split("\n## ", 1)[0]
    for word in ("[idea]", "[bug]", "[nit]", "feature", "fix", "refactor", "docs", "chore"):
        assert f"`{word}`" in section, word


@pytest.mark.parametrize(("answers", "guide"), GUIDES.items())
def test_every_prompt_sits_in_a_guide_slot(answers: str, guide: str) -> None:
    """A host's answer stands in for, or follows, a guide block by key, so every prompt setup
    fills must sit in a block whose key the guide has: a slot. And the guide asks nothing itself."""
    slots = dict(sdlc.doc_units(_text(guide)))
    prompted = [k for k, t in sdlc.doc_units(_text(answers)) if sdlc.PROMPT_RE.search(t)]
    assert prompted, f"{answers} has prompts"
    assert [k for k in prompted if k not in slots] == []
    assert not sdlc.PROMPT_RE.search(_text(guide)), f"{guide} carries a prompt"


def test_no_shipped_text_writes_a_seed_heading() -> None:
    """Ideas are tagged `[idea]`; `[seed]` is named only as the old tag, never written."""
    paths = [
        *ROOT.glob("skills/*/SKILL.md"),
        *ROOT.glob("plugins/factory/skills/*/SKILL.md"),
        *ROOT.glob("templates/*.md"),
        *ROOT.glob("defaults/*.md"),
        *ROOT.glob("guide/*.md"),
        ROOT / "docs" / "REFERENCE.md",
    ]
    assert not [str(p.relative_to(ROOT)) for p in paths if "] [seed]" in p.read_text("utf-8")]


def test_the_factory_starts_notes_from_the_same_text_as_the_template() -> None:
    path = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
    spec = importlib.util.spec_from_file_location("factory_notes", path)
    factory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factory)
    assert _text("templates/notes.md") == factory.NOTES_HEAD
    assert "unticked `- [ ]` line" in factory.NOTES_HEAD


def test_the_factory_builder_starts_checks_from_the_same_text_as_the_template() -> None:
    """The factory's cached copy has no `templates/`, so the builder carries the text itself."""
    builder = (ROOT / "plugins" / "factory" / "agents" / "builder.md").read_text(encoding="utf-8")
    assert f"````markdown\n{_text('templates/checks.md')}````" in builder


# This repo's own answers to the guides it ships. Only what is this plugin's alone lives there:
# every block sits under a heading the guide has, so a reader can place it, and none restates the
# guide's block word for word, which would only be a copy waiting to drift. An improvement any
# repo could use goes into the guide.
OWN_ANSWERS = {".sdlc/SDLC.md": "guide/process.md", ".sdlc/REVIEW.md": "guide/review.md"}


@pytest.mark.parametrize(("answers", "guide"), OWN_ANSWERS.items())
def test_this_repos_answers_are_guide_keys(answers: str, guide: str) -> None:
    keys = {k for k, _ in sdlc.doc_units(_text(guide))}
    units = sdlc.doc_units(_text(answers))
    stray = [k for k, _ in units if k != "#" and not sdlc._under_guide(k, keys)]
    assert stray == [], f"{answers} has blocks {guide} can't place"
    assert not [ln for ln in _text(answers).splitlines() if ln == "---"], f"{answers} has a rule"


@pytest.mark.parametrize(("answers", "guide"), OWN_ANSWERS.items())
def test_this_repos_answers_restate_no_guide_block(answers: str, guide: str) -> None:
    said = {sdlc.unit_hash(t) for k, t in sdlc.doc_units(_text(guide)) if k != "#"}
    # A heading with nothing under it only places what follows: it restates nothing.
    units = [(k, t) for k, t in sdlc.doc_units(_text(answers)) if len(t.strip().splitlines()) > 1]
    same = [k for k, t in units if k != "#" and sdlc.unit_hash(t) in said]
    assert same == [], f"{answers} restates {guide} at {same}: cut them"


def test_a_block_the_guide_can_t_place_is_stray() -> None:
    keys = {"## A", "## A > ### B"}
    assert sdlc._under_guide("## A > ### B > - **x**", keys)
    assert sdlc._under_guide("## A > ### Own", keys)
    assert not sdlc._under_guide("## Own", keys)


# What `sdlc.py record` clears, by drift class: it makes each default block the new base, re-lists
# the config keys and template hashes, and stamps this plugin's version and each doc's path. The
# rest (everything `breaking`, and an `unknown` key or template) it leaves as it found them.
RECORD_CLEARS = {
    *("added", "refreshed", "removed", "conflict", "differs"),
    *("new", "changed", "moved", "downgrade", "unreadable"),
}
RECORD = "`uv run --quiet --script scripts/sdlc.py record`"


def _drift_lines(found: dict) -> tuple[list[str], bool]:
    """A line per entry `drift` reports, each with what fixes it, and whether any needs `record`."""
    entries = [{**u, "where": r["path"]} for r in found["refresh"] for u in r["units"]]
    lines, needs_record = [], False
    for e in entries + found["breaking"] + found["report"]:
        where = f"{e['where']}: {e['unit']}" if e.get("unit") else e["where"]
        if e.get("fix"):
            fix = e["fix"]
        elif e.get("class") in RECORD_CLEARS:
            fix, needs_record = "record", True
        else:
            fix = e.get("detail") or "see `sdlc.py drift`"
        lines.append(f"{where} ({e.get('class') or 'breaking'}): {fix}")
    return lines, needs_record


def test_this_repos_setup_record_is_current() -> None:
    """`.sdlc/setup.json` holds the defaults this repo was last set up from. A change that edits
    `defaults/` and doesn't rerun `record` leaves drift for a later change to trip over at close;
    after a fresh record, `drift` reports nothing at all."""
    found = sdlc.drift(ROOT)
    assert found["base"] == "manifest", f".sdlc/setup.json is missing or won't parse: run {RECORD}"
    lines, needs_record = _drift_lines(found)
    advice = (
        f"; for each `record` line, bring .sdlc/ in step with defaults/, then run {RECORD} from "
        "this checkout"
        if needs_record
        else ""
    )
    assert not lines, (
        "this repo's setup has drifted from defaults/" + advice + "\n  " + "\n  ".join(lines)
    )


def test_drift_lines_name_each_fix() -> None:
    unknown = {"what": "config", "where": "commands.foo", "class": "unknown", "detail": "unread"}
    retired = {"what": "config", "where": "metrics.x", "detail": "retired", "fix": "Delete it."}
    conflict = {"what": "doc", "where": ".sdlc/REVIEW.md", "unit": "## B", "class": "conflict"}
    refresh = [{"path": ".sdlc/SDLC.md", "units": [{"unit": "## A", "class": "refreshed"}]}]
    found = {"refresh": refresh, "breaking": [retired], "report": [conflict, unknown]}
    assert _drift_lines(found) == (
        [
            ".sdlc/SDLC.md: ## A (refreshed): record",
            "metrics.x (breaking): Delete it.",
            ".sdlc/REVIEW.md: ## B (conflict): record",
            "commands.foo (unknown): unread",
        ],
        True,
    )
    assert _drift_lines({"refresh": [], "breaking": [retired], "report": [unknown]})[1] is False


@pytest.mark.parametrize("rel", sorted(sdlc.ISSUE_FORMS))
def test_each_issue_form_is_one_github_reads(rel: str) -> None:
    """GitHub ignores an issue form missing its keys, and a person filing gets a blank box."""
    import yaml

    source = sdlc.DEFAULTS_DIR / sdlc.ISSUE_FORMS[rel]
    form = yaml.safe_load(source.read_text(encoding="utf-8"))
    assert {"name", "description", "body"} <= set(form), rel
    assert form["labels"] == [], "a label a form sets would make triage skip its own issue"
    for field in form["body"]:
        assert field["type"] in ("textarea", "input", "dropdown") and field["attributes"]["label"]
    assert rel.startswith(".github/ISSUE_TEMPLATE/") and rel.endswith(".yml")


def test_the_bug_form_takes_its_severities_from_the_process_doc() -> None:
    import yaml

    text = (sdlc.DEFAULTS_DIR / "issue-forms" / "sdlc-bug.yml").read_text(encoding="utf-8")
    [severity] = [f for f in yaml.safe_load(text)["body"] if f["id"] == "severity"]
    assert severity["attributes"]["options"] == ["<severities>"], "setup fills it in"
