"""Where a change's number comes from, and where a closed change goes.

With a GitHub remote, a change is numbered by the issue /sdlc:intent opens for it, and /sdlc:close
fills that issue with its artifacts and reads it back before it removes the folder from main.
Without one, the committed counter in `.sdlc/last-id` numbers it, and close mirrors to the host's
command or not at all: the change's own commit on main is the copy either way.
GitHub is a fake `gh` on PATH that keeps its issues in a JSON file, so these run offline and can
make any step fail.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_archive", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()
_spec = importlib.util.spec_from_file_location("sdlc_github", sdlc.TRACKER_DIR / "github.py")
sdlc_github = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sdlc_github)

FAKE_GH = r"""#!/usr/bin/env python3
import json, os, sys

path = os.environ["FAKE_GH_STATE"]
fail = os.environ.get("FAKE_GH_FAIL", "")
start = int(os.environ.get("FAKE_GH_START", "0"))
st = json.load(open(path)) if os.path.exists(path) else {"issues": [], "calls": []}
args = sys.argv[1:]
st["calls"].append(args)


def done(code=0, out=None):
    json.dump(st, open(path, "w"))
    if out is not None:
        print(out)
    sys.exit(code)


def find(ref):
    for i in st["issues"]:
        if ref in (i["url"], str(i["number"])):
            return i
    return None


def top():
    return max([start] + [i["number"] for i in st["issues"]])


def every(flag):
    return [args[k + 1] for k, a in enumerate(args) if a == flag]


if fail and args[:2] == ["issue", fail]:
    print("boom", file=sys.stderr)
    done(1)
# An edit carrying this flag fails, as GitHub refuses one field and not the rest.
flag = os.environ.get("FAKE_GH_FAIL_FLAG", "")
if flag and args[:2] == ["issue", "edit"] and flag in args:
    print(f"refused {flag}: missing required scopes [project]", file=sys.stderr)
    done(1)
if args[0] == "label":
    done()
if args[0] == "api":
    # Lists from the state, as the `--jq` the tracker passes would leave them.
    for kind in ("milestones", "assignees"):
        if f"/{kind}" in args[1]:
            done(out=json.dumps(st.get(kind, [])))
    done(out=str(top()))
if args[:2] == ["repo", "view"]:
    if "defaultBranchRef" in args:
        if fail == "repo":
            print("boom", file=sys.stderr)
            done(1)
        name = os.environ.get("FAKE_GH_DEFAULT", "main")
        done(out=json.dumps({"defaultBranchRef": {"name": name}}))
    done(out="o")
if args[:2] == ["project", "list"]:
    if fail == "project":
        print("error: your authentication token is missing required scopes [read:project]\n"
              "To request it, run:  gh auth refresh -s read:project", file=sys.stderr)
        done(1)
    done(out=json.dumps(st.get("projects", [])))
if args[:2] == ["issue", "list"]:
    keys = ("number", "title", "url", "state")
    done(out=json.dumps([{k: i[k] for k in keys} for i in st["issues"]]))
if args[:2] == ["issue", "create"]:
    n = top() + 1
    url = f"https://github.com/o/r/issues/{n}"
    st["issues"].append({
        "number": n, "title": args[args.index("--title") + 1], "url": url, "state": "OPEN",
        "labels": [{"name": name} for name in every("--label")], "body": sys.stdin.read(),
        "comments": [], "reason": None, "assignees": every("--assignee"), "blockedBy": [],
    })
    done(out=url)
if args[:2] == ["issue", "edit"]:
    i = find(args[2])
    if "--body-file" in args:
        i["body"] = sys.stdin.read()
    names = [lb["name"] for lb in i["labels"]]
    names = [x for x in names if x not in every("--remove-label")] + every("--add-label")
    i["labels"] = [{"name": x} for x in names]
    links = i.setdefault("blockedBy", [])
    links[:] = [x for x in links if str(x) not in every("--remove-blocked-by")]
    links += [int(x) for x in every("--add-blocked-by")]
    if "--milestone" in args:
        i["milestone"] = args[args.index("--milestone") + 1]
    if "--remove-milestone" in args:
        i["milestone"] = None
    for field, noun in (("projects", "project"), ("assignees", "assignee")):
        have = [x for x in i.get(field) or [] if x not in every(f"--remove-{noun}")]
        i[field] = have + [x for x in every(f"--add-{noun}") if x not in have]
    done()
if args[:2] == ["issue", "comment"]:
    find(args[2])["comments"].append({"body": sys.stdin.read()})
    done()
if args[:2] == ["issue", "close"]:
    i = find(args[2])
    i["state"], i["reason"] = "CLOSED", args[args.index("--reason") + 1]
    if "--comment" in args:
        i["comments"].append({"body": args[args.index("--comment") + 1]})
    done()
if args[:2] == ["issue", "view"]:
    i = find(args[2])
    if i is None:
        done(1)
    keys = args[args.index("--json") + 1].split(",")
    out = {k: i.get(k) for k in keys}
    if "blockedBy" in out:
        # As gh gives it: a GraphQL connection, not a list.
        links = i.get("blockedBy") or []
        out["blockedBy"] = {"nodes": [{"number": x} for x in links], "totalCount": len(links)}
    # And the fields in gh's shapes: objects, not the names the state keeps.
    if "milestone" in out:
        out["milestone"] = {"title": i["milestone"]} if i.get("milestone") else None
    if "projectItems" in keys:
        out["projectItems"] = [{"title": p} for p in i.get("projects") or []]
    if "assignees" in out:
        out["assignees"] = [{"login": a} for a in i.get("assignees") or []]
    done(out=json.dumps(out))
print("unexpected: " + " ".join(args), file=sys.stderr)
done(2)
"""


def _git(root: Path, *args: str, input: str | None = None) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
        input=input,
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, github: bool = True) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    if github:
        _config(root, '[archive]\ntarget = "github"\n')
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    if github:
        _git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    return root


def _config(root: Path, text: str) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text(text, encoding="utf-8")


def _state_dir(root: Path) -> Path:
    return root / ".sdlc"


def _open(root: Path, slug: str = "thing") -> Path:
    """A change opened in its own worktree; its folder there."""
    assert sdlc.cmd_new(root, slug, 1, f"The {slug}", worktree=True) == 0
    return next((root / ".claude" / "worktrees").glob(f"*-{slug}/work/*-{slug}"))


def _shipped(root: Path, slug: str = "thing", extra: dict[str, str] | None = None) -> str:
    """A change opened, written, shipped and committed in its worktree, as close finds it; its
    name. Its folder on main, once landed, is `root / "work" / name`."""
    folder = _open(root, slug)
    intent = folder / "intent.md"
    intent.write_text(intent.read_text().replace("impact:\n", "impact: none\n", 1))
    for name, text in (extra or {}).items():
        (folder / name).write_text(text, encoding="utf-8")
    assert sdlc.cmd_ship(root, folder.name.split("-")[0]) == 0
    tree = folder.parent.parent
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", f"ship {folder.name}")
    return folder.name


@pytest.fixture
def gh(tmp_path: Path, monkeypatch):
    """The fake gh on PATH; returns a reader for its state."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text(FAKE_GH, encoding="utf-8")
    (bin_dir / "gh").chmod(0o755)
    state = tmp_path / "gh.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_GH_STATE", str(state))
    monkeypatch.delenv("FAKE_GH_FAIL", raising=False)
    monkeypatch.delenv("FAKE_GH_FAIL_FLAG", raising=False)
    monkeypatch.delenv("FAKE_GH_START", raising=False)
    monkeypatch.delenv("FAKE_GH_DEFAULT", raising=False)
    return lambda: json.loads(state.read_text()) if state.exists() else {"issues": [], "calls": []}


def _close(root: Path, capsys, ident: str, check: bool = False) -> tuple[int, dict]:
    capsys.readouterr()
    code = sdlc.cmd_close(root, ident, check)
    return code, json.loads(capsys.readouterr().out)


def _on_main(root: Path, name: str) -> bool:
    """Whether main still holds the change's folder: close removes it only after the mirror."""
    return (root / "work" / name).is_dir()


# ---------------------------------------------------------------- numbered by GitHub


def test_new_numbers_the_change_after_the_issue_it_opens(tmp_path, gh, monkeypatch) -> None:
    """Issues and pull requests share GitHub's sequence, so the number is wherever it has got to."""
    monkeypatch.setenv("FAKE_GH_START", "141")
    root = _repo(tmp_path)
    folder = _open(root)
    assert folder.name == "142-thing"
    tree = folder.parent.parent
    [issue] = gh()["issues"]
    assert issue["number"] == 142 and issue["state"] == "OPEN"
    assert issue["title"] == "The thing"
    assert {lb["name"] for lb in issue["labels"]} == {"sdlc", "tier: 1", "stage: plan"}
    assert issue["assignees"] == ["@me"], "assigned to whoever opened it"
    assert "<!-- sdlc:thing -->" in issue["body"]
    assert not (_state_dir(tree) / "last-id").exists(), "no counter when GitHub numbers"


def test_next_says_what_github_will_probably_assign(tmp_path, gh, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FAKE_GH_START", "57")
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "next"])
    capsys.readouterr()
    assert sdlc.main() == 0
    assert capsys.readouterr().out.strip() == "058"


def test_a_failed_issue_means_no_change(tmp_path, gh, monkeypatch, capsys) -> None:
    """Never a local number instead: two schemes in one repo hand out one number twice."""
    root = _repo(tmp_path)
    monkeypatch.setenv("FAKE_GH_FAIL", "create")
    assert sdlc.cmd_new(root, "thing", 1, None) == 1
    assert "issue create failed" in capsys.readouterr().err
    assert not (root / "work").exists() or not any((root / "work").iterdir())
    assert not (_state_dir(root) / "last-id").exists()


def test_a_worktree_that_fails_closes_its_issue_as_not_planned(tmp_path, gh) -> None:
    root = _repo(tmp_path)
    (root / ".claude" / "worktrees" / "001-taken").mkdir(parents=True)
    assert sdlc.cmd_new(root, "taken", 1, None, worktree=True) == 1
    [issue] = gh()["issues"]
    assert issue["state"] == "CLOSED" and issue["reason"] == "not planned"
    assert not (root / "work").exists()


def test_an_issue_number_a_local_folder_holds_is_refused(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    _config(root, '[archive]\ntarget = "github"\n')
    (root / "work" / "001-old").mkdir(parents=True)
    assert sdlc.cmd_new(root, "fresh", 1, None) == 1
    assert "already holds" in capsys.readouterr().err
    assert gh()["issues"][0]["reason"] == "not planned"
    assert not (root / "work" / "001-fresh").exists()


# Too long for one body: the intent and spec fit, plan and notes overflow into a comment each.
BIG = {"spec.md": "s" * 40_000, "plan.md": "p" * 40_000, "notes.md": "n" * 40_000}


def test_close_fills_the_changes_own_issue_then_removes_the_folder(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    name = _shipped(root, extra={"notes.md": "# notes\n\nIt went fine.\n"})
    sha = _git(root, "rev-parse", "--short", name)
    code, out = _close(root, capsys, "1")
    assert code == 0, out
    assert out["done"] == [
        "merge", "verify", "measure", "archive", "remove folder", "remove worktree", "delete branch"
    ]  # fmt: skip
    [issue] = gh()["issues"]
    # Archived but open: GitHub closes it when the Close commit reaches the default branch.
    assert issue["state"] == "OPEN" and {"name": "landed"} in issue["labels"]
    assert not [c for c in gh()["calls"] if c[:2] == ["issue", "close"]]
    assert "<!-- sdlc:001-thing -->" in issue["body"] and f"`{sha}`" in issue["body"]
    assert "<b>intent.md</b>" in issue["body"] and "<b>notes.md</b>" in issue["body"]
    assert "id: 001" not in issue["body"], "frontmatter is in the table, not pasted"
    assert out["archive"]["location"] == issue["url"]
    assert out["archive"]["closes"] == "Closes #1" and "closed_because" not in out["archive"]
    assert not _on_main(root, name)
    body = _git(root, "log", "-1", "--format=%b", "main")
    assert issue["url"] in body and "\nCloses #1\n" in body


def test_the_closing_line_leaves_the_trailers_as_they_were(tmp_path, gh, capsys) -> None:
    """`Closes #N` ends the paragraph before the trailers, so git and `parse_trailers` read the
    same `Sdlc-*` lines they would without it."""
    root = _repo(tmp_path)
    _shipped(root)
    assert _close(root, capsys, "001")[0] == 0
    message = _git(root, "log", "-1", "--format=%B", "main")
    without = message.replace("\nCloses #1", "")
    assert without != message
    parsed = _git(root, "interpret-trailers", "--parse", input=message).splitlines()
    assert parsed and all(line.startswith("Sdlc-") for line in parsed), parsed
    assert parsed == _git(root, "interpret-trailers", "--parse", input=without).splitlines()
    assert sdlc.metrics.parse_trailers(message) == sdlc.metrics.parse_trailers(without)


def test_artifacts_too_long_for_one_body_go_in_comments(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    _shipped(root, extra=BIG)
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    [issue] = gh()["issues"]
    assert "<b>spec.md</b>" in issue["body"] and "<b>plan.md</b>" not in issue["body"]
    assert "posted as comments at close: `plan.md`, `notes.md`" in issue["body"]
    firsts = [c["body"].split("\n", 1)[0] for c in issue["comments"]]
    assert firsts == ["<!-- sdlc:001-thing:plan.md -->", "<!-- sdlc:001-thing:notes.md -->"]


def test_an_artifact_over_the_limit_stops_close_before_the_removal(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    name = _shipped(root, extra={"spec.md": "s" * 70_000})
    code, out = _close(root, capsys, "001")
    assert code == 1 and any("over GitHub's" in r for r in out["refusals"])
    assert out["done"] == ["merge", "verify", "measure"]
    assert _on_main(root, name) and gh()["issues"][0]["state"] == "OPEN"


def test_a_failed_mirror_stops_close_and_a_rerun_finishes_without_repeating(
    tmp_path, gh, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    name = _shipped(root, extra=BIG)
    tree = root / ".claude" / "worktrees" / name
    monkeypatch.setenv("FAKE_GH_FAIL_FLAG", "--add-label")  # the comments go; `landed` doesn't
    code, out = _close(root, capsys, "001")
    assert code == 1 and any("edit failed" in r for r in out["refusals"])
    assert out["skipped"][0] == "archive" and _on_main(root, name) and tree.is_dir()
    monkeypatch.delenv("FAKE_GH_FAIL_FLAG")
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    [issue] = gh()["issues"]
    assert len(issue["comments"]) == 2, "comments posted by the first run aren't posted again"
    assert not _on_main(root, name) and not tree.exists()
    closes = _git(root, "log", "--format=%s", "--grep", f"^Close {name}$", "main").splitlines()
    assert closes == [f"Close {name}"], "one Close commit, so one set of trailers"


# ---------------------------------------------------------------- which code runs the close


def _own(root: Path, script: str = "print('main')\n", manifest: str = '{"name": "sdlc"}') -> Path:
    """Make the scratch repo look like the plugin's own: its manifest and `scripts/sdlc.py`."""
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text(manifest, encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "sdlc.py").write_text(script, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the plugin")
    return root


def _landing(root: Path, files: dict[str, str]) -> str:
    """A change shipped with `files` (paths from the worktree's root) in its commit; its name."""
    folder = _open(root)
    tree = folder.parent.parent
    intent = folder / "intent.md"
    intent.write_text(intent.read_text().replace("impact:\n", "impact: none\n", 1))
    for path, text in files.items():
        (tree / path).parent.mkdir(parents=True, exist_ok=True)
        (tree / path).write_text(text, encoding="utf-8")
    assert sdlc.cmd_ship(root, folder.name.split("-")[0]) == 0
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", f"ship {folder.name}")
    return folder.name


@pytest.fixture
def handoffs(monkeypatch):
    """Every handoff close asks for, stubbed: the calls, as (argv, ran)."""
    calls: list[tuple[list[str], str]] = []

    def record(main, argv, ran, report):
        calls.append((argv, ran))
        return 0

    monkeypatch.setattr(sdlc, "_handoff", record)
    monkeypatch.delenv(sdlc.HANDOFF_ENV, raising=False)
    return calls


@pytest.mark.parametrize("manifest", [None, '{"name": "other"}', "{not json"])
def test_a_host_repo_never_hands_off(tmp_path, gh, capsys, handoffs, monkeypatch, manifest):
    root = _repo(tmp_path)
    if manifest:
        _own(root, manifest=manifest)
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", tmp_path / "elsewhere")
    name = _landing(root, {"scripts/tool.py": "x = 1\n"})
    code, out = _close(root, capsys, "001")
    assert code == 0 and out["done"][-1] == "delete branch", out
    assert handoffs == [] and "ran" not in out and not _on_main(root, name)
    assert "reaches" not in out, "only the plugin's own close says what reaches its sessions"


@pytest.mark.parametrize("check", [False, True])
def test_a_copy_that_isnt_mains_hands_the_close_to_mains_script(
    tmp_path, gh, capsys, handoffs, monkeypatch, check
) -> None:
    root = _own(_repo(tmp_path))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", tmp_path / "cache" / "1.1.0")
    _landing(root, {"feature.txt": "x\n"})
    assert sdlc.cmd_close(root, "001", check) == 0
    assert handoffs == [(["001", "--check"] if check else ["001"], "main")]
    assert _git(root, "rev-parse", "main") != _git(root, "rev-parse", "001-thing"), "nothing done"


def test_mains_script_once_handed_the_close_runs_it(tmp_path, gh, capsys, handoffs, monkeypatch):
    root = _own(_repo(tmp_path))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", tmp_path / "cache" / "1.1.0")
    monkeypatch.setenv(sdlc.HANDOFF_ENV, "main")
    name = _landing(root, {"feature.txt": "x\n"})
    code, out = _close(root, capsys, "001")
    assert code == 0 and handoffs == [] and not _on_main(root, name), out


@pytest.mark.parametrize("path", ["scripts/sdlc.py", "scripts/trackers/github.py"])
def test_a_merge_that_brings_scripts_hands_the_rest_to_the_merged_code(
    tmp_path, gh, capsys, handoffs, monkeypatch, path
) -> None:
    root = _own(_repo(tmp_path))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", root)
    name = _landing(root, {path: "print('merged')\n"})
    assert sdlc.cmd_close(root, "001") == 0
    assert handoffs == [([name], "merged")]
    assert _git(root, "rev-parse", "main") == _git(root, "rev-parse", name), "merged first"
    assert _on_main(root, name), "everything after the merge is the merged code's"


@pytest.mark.parametrize(
    "files, ran_env",
    [({"feature.txt": "x\n"}, None), ({"scripts/sdlc.py": "print('merged')\n"}, "merged")],
)
def test_a_merge_with_no_scripts_or_already_merged_code_carries_on(
    tmp_path, gh, capsys, handoffs, monkeypatch, files, ran_env
) -> None:
    root = _own(_repo(tmp_path))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", root)
    if ran_env:
        monkeypatch.setenv(sdlc.HANDOFF_ENV, ran_env)
    name = _landing(root, files)
    code, out = _close(root, capsys, "001")
    assert code == 0 and handoffs == [] and not _on_main(root, name), out


def test_merged_code_that_wont_start_stops_after_the_merge(tmp_path, gh, capsys, monkeypatch):
    monkeypatch.delenv(sdlc.HANDOFF_ENV, raising=False)
    root = _own(_repo(tmp_path))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", root)
    name = _landing(root, {"scripts/sdlc.py": "def broken(:\n"})
    code, out = _close(root, capsys, "001")
    assert code == 1, out
    assert out["done"] == ["merge"] and out["skipped"][0] == "verify"
    assert any(
        r.startswith("merged code didn't run:") and r.endswith("rerun /sdlc:close 001")
        for r in out["refusals"]
    ), out["refusals"]
    assert _git(root, "rev-parse", "main") == _git(root, "rev-parse", name)
    assert _on_main(root, name) and gh()["issues"][0]["state"] == "OPEN", "nothing archived"


def test_mains_script_that_wont_start_does_nothing(tmp_path, gh, capsys, monkeypatch) -> None:
    monkeypatch.delenv(sdlc.HANDOFF_ENV, raising=False)
    root = _own(_repo(tmp_path), script="def broken(:\n")
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", tmp_path / "cache" / "1.1.0")
    name = _landing(root, {"feature.txt": "x\n"})
    code, out = _close(root, capsys, "001")
    assert code == 1 and out["done"] == [], out
    assert any(r.startswith("main's sdlc.py didn't run:") for r in out["refusals"])
    assert _git(root, "rev-parse", "main") != _git(root, "rev-parse", name)


# ---------------------------------------------------------------- the change's own script


@pytest.fixture
def own_tree(tmp_path, monkeypatch):
    """A change's worktree in a scratch plugin repo, run from a copy that isn't its own."""
    root = _own(_repo(tmp_path, github=False))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", tmp_path / "elsewhere")
    monkeypatch.delenv(sdlc.OWN_SCRIPT_ENV, raising=False)
    return root, _open(root).parent.parent


@pytest.mark.parametrize("how", ["committed", "uncommitted", "untracked"])
def test_a_change_that_edits_scripts_runs_its_own(own_tree, how) -> None:
    _, tree = own_tree
    path = tree / "scripts" / ("new.py" if how == "untracked" else "sdlc.py")
    path.write_text("print('the change')\n", encoding="utf-8")
    if how == "committed":
        _git(tree, "commit", "-qam", "edit the script")
    assert sdlc._own_script(tree) == tree / "scripts" / "sdlc.py"


def test_no_handoff_when_the_change_leaves_scripts_alone(own_tree) -> None:
    _, tree = own_tree
    (tree / "feature.txt").write_text("x\n", encoding="utf-8")
    assert sdlc._own_script(tree) is None


def test_no_handoff_when_the_running_copy_is_the_changes(own_tree, monkeypatch) -> None:
    _, tree = own_tree
    (tree / "scripts" / "sdlc.py").write_text("print('the change')\n", encoding="utf-8")
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", tree)
    assert sdlc._own_script(tree) is None


@pytest.mark.parametrize("value", ["ran", "off"])
def test_the_variable_stops_a_second_handoff_and_turns_the_first_off(
    own_tree, monkeypatch, value
) -> None:
    _, tree = own_tree
    (tree / "scripts" / "sdlc.py").write_text("print('the change')\n", encoding="utf-8")
    monkeypatch.setenv(sdlc.OWN_SCRIPT_ENV, value)
    assert sdlc._own_script(tree) is None


def test_no_handoff_off_a_change_branch(own_tree) -> None:
    root, _ = own_tree
    (root / "scripts" / "sdlc.py").write_text("print('on main')\n", encoding="utf-8")
    assert sdlc._own_script(root) is None


@pytest.mark.parametrize("manifest", [None, '{"name": "other"}', "{not json"])
def test_a_host_never_runs_a_changes_own_script(tmp_path, monkeypatch, manifest) -> None:
    root = _repo(tmp_path, github=False)
    if manifest:
        _own(root, manifest=manifest)
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", tmp_path / "elsewhere")
    monkeypatch.delenv(sdlc.OWN_SCRIPT_ENV, raising=False)
    tree = _open(root).parent.parent
    (tree / "scripts").mkdir(exist_ok=True)
    (tree / "scripts" / "sdlc.py").write_text("print('the change')\n", encoding="utf-8")
    assert sdlc._own_script(tree) is None


def _script(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "own" / "sdlc.py"
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_a_json_report_says_the_changes_own_code_ran(tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.delenv(sdlc.OWN_SCRIPT_ENV, raising=False)
    script = _script(
        tmp_path,
        "import json, os, sys\n"
        "print(json.dumps({'args': sys.argv[1:], 'env': os.environ['SDLC_OWN_SCRIPT']}))\n",
    )
    assert sdlc._run_own(script, ["sync", "001"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"args": ["sync", "001"], "env": "ran", "ran": sdlc.OWN_RAN}


def test_a_text_report_ends_with_which_code_ran(tmp_path, capsys) -> None:
    script = _script(tmp_path, "print('■ shipped 001-thing')\n")
    assert sdlc._run_own(script, ["ship", "001"]) == 0
    out = capsys.readouterr().out
    assert out == f"■ shipped 001-thing\n  ran {sdlc.OWN_RAN}: {script}\n"


def test_a_refusal_from_the_changes_own_code_stands(tmp_path, capsys) -> None:
    script = _script(
        tmp_path, "import sys\nprint('■ refused')\nprint('⚠  no', file=sys.stderr)\nsys.exit(1)\n"
    )
    assert sdlc._run_own(script, ["ship", "001"]) == 1
    captured = capsys.readouterr()
    assert "■ refused" in captured.out and "⚠  no" in captured.err
    assert "running this copy instead" not in captured.err


def test_a_refusal_said_only_on_stderr_stands(tmp_path, capsys) -> None:
    """Ship's refusals are a `⚠` on stderr and nothing on stdout: never taken for a crash, or the
    old code would run and write what the new code refused."""
    script = _script(
        tmp_path,
        "import sys\nprint('⚠  001-thing: refused. Not stamping.', file=sys.stderr)\nsys.exit(1)\n",
    )
    assert sdlc._run_own(script, ["ship", "001"]) == 1
    err = capsys.readouterr().err
    assert "Not stamping." in err and "running this copy instead" not in err


def test_a_change_script_that_cant_start_hands_back(tmp_path, capsys) -> None:
    script = _script(
        tmp_path, "import sys\nprint('error: no solution found', file=sys.stderr)\nsys.exit(2)\n"
    )
    assert sdlc._run_own(script, ["ship", "001"]) is None
    err = capsys.readouterr().err
    assert "didn't run (error: no solution found)" in err and "running this copy instead" in err


def test_a_change_script_that_crashes_hands_back(tmp_path, capsys) -> None:
    script = _script(tmp_path, "import no_such_module_anywhere\n")
    assert sdlc._run_own(script, ["ship", "001"]) is None
    err = capsys.readouterr().err
    assert "didn't run (ModuleNotFoundError" in err and "running this copy instead" in err


@pytest.mark.parametrize("answer", [0, None])
def test_main_runs_the_changes_own_script_or_carries_on(
    own_tree, monkeypatch, capsys, answer
) -> None:
    _, tree = own_tree
    (tree / "scripts" / "sdlc.py").write_text("print('the change')\n", encoding="utf-8")
    calls: list[tuple[Path, list[str]]] = []

    def run_own(script, argv):
        calls.append((script, argv))
        return answer

    monkeypatch.setattr(sdlc, "_run_own", run_own)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "sync", "001"])
    monkeypatch.chdir(tree)
    assert sdlc.main() == 0
    assert calls == [(tree / "scripts" / "sdlc.py", ["sync", "001"])]
    said = capsys.readouterr().out
    assert ("nothing to sync" in said.lower() or '"change"' in said) == (answer is None)


def test_main_never_hands_off_a_command_that_only_reads(own_tree, monkeypatch) -> None:
    _, tree = own_tree
    (tree / "scripts" / "sdlc.py").write_text("print('the change')\n", encoding="utf-8")
    monkeypatch.setattr(sdlc, "_run_own", lambda *a: pytest.fail("handed off"))
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status"])
    monkeypatch.chdir(tree)
    assert sdlc.main() == 0


# ---------------------------------------------------------------- what a landed change reaches


@pytest.mark.parametrize(
    "paths, reaches",
    [
        (["scripts/sdlc.py", "scripts/trackers/github.py"], {"scripts": True}),
        (["plugins/factory/scripts/factory.py"], {"scripts": True}),
        (
            ["skills/ship/SKILL.md", "skills/close/SKILL.md"],
            {"skills": ["sdlc:close", "sdlc:ship"]},
        ),
        (["plugins/factory/skills/build/SKILL.md"], {"skills": ["sdlc-factory:build"]}),
        (["plugins/factory/agents/reviewer-code.md"], {"agents": ["sdlc-factory:reviewer-code"]}),
        (
            ["templates/intent.md", "defaults/SDLC.md"],
            {"hosts": ["defaults/SDLC.md", "templates/intent.md"]},
        ),
        (
            ["scripts/sdlc.py", "skills/ship/SKILL.md", "defaults/REVIEW.md", "README.md"],
            {"scripts": True, "skills": ["sdlc:ship"], "hosts": ["defaults/REVIEW.md"]},
        ),
        (["README.md", "docs/CONTRIBUTING.md", "work/001-thing/intent.md", "tests/t.py"], {}),
    ],
)
def test_landing_reach_sorts_paths_into_what_each_needs(paths, reaches) -> None:
    assert sdlc.landing_reach(paths) == reaches


def test_the_plugins_own_close_reports_what_reaches_its_sessions(
    tmp_path, gh, capsys, handoffs, monkeypatch
) -> None:
    root = _own(_repo(tmp_path))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", root)
    _landing(root, {"skills/ship/SKILL.md": "x\n", "defaults/SDLC.md": "# Process\n"})
    code, out = _close(root, capsys, "001")
    assert code == 0 and handoffs == [], out
    assert out["reaches"] == {"skills": ["sdlc:ship"], "hosts": ["defaults/SDLC.md"]}


def test_a_close_that_cant_read_the_changes_paths_says_so(
    tmp_path, gh, capsys, handoffs, monkeypatch
) -> None:
    root = _own(_repo(tmp_path))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", root)
    _landing(root, {"skills/ship/SKILL.md": "x\n"})

    def broken(main, branch):
        raise OSError("disk")

    monkeypatch.setattr(sdlc, "_change_base", broken)
    code, out = _close(root, capsys, "001")
    assert code == 0, "never a refusal"
    assert out["reaches"] == {"unknown": "reading the change's paths failed: OSError"}


def test_a_change_that_reaches_nothing_reports_no_reaches(
    tmp_path, gh, capsys, handoffs, monkeypatch
) -> None:
    root = _own(_repo(tmp_path))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", root)
    _landing(root, {"docs/notes.md": "x\n"})
    code, out = _close(root, capsys, "001")
    assert code == 0 and "reaches" not in out, out


# ---------------------------------------------------------------- what close measures


def _transcript(home: Path, root: Path, branch: str, entries: list[dict]) -> None:
    """A session transcript for the repo at `root`, where Claude Code would keep it."""
    folder = home / ".claude" / "projects" / "".join(c if c.isalnum() else "-" for c in str(root))
    folder.mkdir(parents=True, exist_ok=True)
    lines = [{"gitBranch": branch, **e} for e in entries]
    (folder / "s1.jsonl").write_text("\n".join(json.dumps(e) for e in lines) + "\n")


SESSION = [
    {"type": "user", "timestamp": "2026-10-01T09:00:00Z",
     "message": {"content": "<command-name>/sdlc:ship</command-name>"}},
    {"type": "system", "subtype": "turn_duration", "timestamp": "2026-10-01T09:06:00Z",
     "durationMs": 360_000},
    {"type": "user", "timestamp": "2026-10-01T09:08:00Z", "message": {"content": "yes"}},
]  # fmt: skip


def test_close_records_what_the_change_cost_as_trailers(tmp_path, gh, capsys, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    root = _repo(tmp_path)
    name = _shipped(root)
    _transcript(home, root, name, SESSION)
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    assert out["measure"]["coverage"] == "transcripts=1 stages=ship"
    body = _git(root, "log", "-1", "--format=%B", "main")
    back = sdlc.metrics.parse_trailers(body)
    assert back["mode"] == "manual" and back["totals"]["agent"] == 6
    assert back["stages"]["ship"]["gate"] == 1 and back["totals"]["required"] == 3
    assert "/" not in "\n".join(ln for ln in body.splitlines() if ln.startswith("Sdlc-"))
    [rec] = [c for c in sdlc.closed_changes(root, None) if c["name"] == name]
    assert rec["metrics"]["totals"]["agent"] == 6


def test_a_reader_that_fails_never_stops_the_close(tmp_path, gh, capsys, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    root = _repo(tmp_path)
    name = _shipped(root)
    _transcript(home, root, name, SESSION)

    def broken(*_):
        raise RuntimeError("a transcript shape nobody planned for")

    monkeypatch.setattr(sdlc.metrics, "read_events", broken)
    code, out = _close(root, capsys, "001")
    assert code == 0 and not _on_main(root, name), out
    assert out["measure"]["coverage"] == "none: capture failed: RuntimeError"
    body = _git(root, "log", "-1", "--format=%B", "main")
    assert "Sdlc-Coverage: none: capture failed: RuntimeError" in body
    assert "a transcript shape" not in body


FACTORY_FILES = {
    "decision.md": "DECISION: READY\n\nShip it.\n",
    "reviews/round-1/code.md": "VERDICT: CHANGES\n\n- CHANGE: name it\n- CHANGE: test it\n",
    "reviews/round-1/test.md": "VERDICT: PASS\n",
    "reviews/round-2/code.md": "VERDICT: PASS\n",
    "decisions.md": "# Decisions\n\n- [x] D1 (builder round 1, blocking): which? → decided: a\n"
    "- [ ] D2 (code round 1, default): assume b\n",
}


def _factory_shipped(root: Path) -> str:
    """A change the factory built, shipped with 7 lines of code and 3 of tests beside its
    folder; its name."""
    folder = _open(root)
    tree = folder.parent.parent
    intent = folder / "intent.md"
    intent.write_text(intent.read_text().replace("impact:\n", "impact: none\n", 1))
    for name, text in FACTORY_FILES.items():
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(text, encoding="utf-8")
    (tree / "lib.py").write_text("x = 1\n" * 7)
    (tree / "tests").mkdir(exist_ok=True)
    (tree / "tests" / "test_lib.py").write_text("y = 1\n" * 3)
    assert sdlc.cmd_ship(root, folder.name.split("-")[0]) == 0
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", f"ship {folder.name}")
    return folder.name


def test_close_records_rework_and_the_happy_path_from_the_factorys_files(
    tmp_path, gh, capsys, monkeypatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    root = _repo(tmp_path)
    name = _factory_shipped(root)
    assert sdlc._change_diff(root, name) == 10, "before the merge"
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    body = _git(root, "log", "-1", "--format=%B", "main")
    back = sdlc.metrics.parse_trailers(body)
    assert back["mode"] == "factory"
    assert back["rework"] == {"final": 10, "rounds": 2, "changes": 1, "escalate": 0,
                              "blocking": 1, "defaults": 1, "defaults_open": 1}  # fmt: skip
    assert back["reviews"] == {"code": {"changes": 1, "requests": 2},
                               "test": {"changes": 0, "requests": 0}}  # fmt: skip
    assert back["happy"]["build"] == "unknown", "no transcripts: never guessed"
    assert "/" not in "\n".join(ln for ln in body.splitlines() if ln.startswith("Sdlc-"))


def test_the_diffs_size_is_the_same_after_the_merge(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    name = _factory_shipped(root)
    before = sdlc._change_diff(root, name)
    _git(root, "merge", "--ff-only", "-q", name)
    assert sdlc._change_diff(root, name) == before == 10
    assert sdlc._factory_files(root, name)["decision"] == "READY"
    assert sdlc._factory_files(root, "001-missing") is None


def test_rework_that_fails_drops_only_its_own_lines(tmp_path, gh, capsys, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    root = _repo(tmp_path)
    name = _shipped(root)
    _transcript(home, root, name, SESSION)

    def broken(*_):
        raise RuntimeError("a rework shape nobody planned for")

    monkeypatch.setattr(sdlc.metrics, "rework", broken)
    code, out = _close(root, capsys, "001")
    assert code == 0 and not _on_main(root, name), out
    body = _git(root, "log", "-1", "--format=%B", "main")
    assert "Sdlc-Coverage: transcripts=1 stages=ship rework=failed" in body
    assert "Sdlc-Totals:" in body and "Sdlc-Rework" not in body and "Sdlc-Happy" not in body


@pytest.mark.parametrize(
    "config, reason",
    [('[metrics]\ntranscripts = false\n', "metrics.transcripts is off"),
     ("", "no transcripts for this repo")],
)  # fmt: skip
def test_without_transcripts_close_records_what_history_gives(
    tmp_path, gh, capsys, monkeypatch, config, reason
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    root = _repo(tmp_path)
    if config:
        _config(root, config)
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "config")
    _shipped(root)
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    back = sdlc.metrics.parse_trailers(_git(root, "log", "-1", "--format=%B", "main"))
    assert back["coverage"] == f"none: {reason}"
    assert back["totals"]["required"] == 3 and "elapsed" in back["totals"]


def test_a_change_already_mirrored_is_only_removed(tmp_path, gh, capsys) -> None:
    """An earlier run filled and closed the issue, then its commit failed: here, to a hook."""
    root = _repo(tmp_path)
    name = _shipped(root)
    hook = Path(_git(root, "rev-parse", "--absolute-git-dir")) / "hooks" / "pre-commit"
    hook.parent.mkdir(exist_ok=True)
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    code, out = _close(root, capsys, "001")
    assert code == 1 and out["skipped"][0] == "remove folder", out
    assert _on_main(root, name) and _git(root, "status", "--porcelain") == ""
    calls = len(gh()["calls"])
    hook.unlink()
    code, out = _close(root, capsys, "001")
    assert code == 0 and not _on_main(root, name), out
    later = [c[:2] for c in gh()["calls"][calls:]]
    assert ["issue", "edit"] not in later and ["issue", "close"] not in later
    assert "\nCloses #1\n" in _git(root, "log", "-1", "--format=%b", "main")


def _hooked(root: Path, capsys, name: str) -> Path:
    """Close archives the change, then its Close commit fails to a hook; the hook, to remove."""
    hook = Path(_git(root, "rev-parse", "--absolute-git-dir")) / "hooks" / "pre-commit"
    hook.parent.mkdir(exist_ok=True)
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    code, out = _close(root, capsys, "001")
    assert code == 1 and out["skipped"][0] == "remove folder", out
    assert _on_main(root, name)
    return hook


def test_an_issue_already_closed_reads_as_archived(tmp_path, gh, capsys) -> None:
    """Closed with every artifact and no `landed`, as a person closing it by hand leaves it:
    archived, and the Close commit names no issue to close, since there is none left open."""
    root = _repo(tmp_path)
    name = _shipped(root)
    hook = _hooked(root, capsys, name)
    state = gh()
    issue = state["issues"][0]
    issue["state"], issue["reason"] = "CLOSED", "completed"
    issue["labels"] = [lb for lb in issue["labels"] if lb["name"] != "landed"]
    _put(state)
    calls = len(gh()["calls"])
    hook.unlink()
    code, out = _close(root, capsys, "001")
    assert code == 0 and not _on_main(root, name), out
    later = [c[:2] for c in gh()["calls"][calls:]]
    assert ["issue", "edit"] not in later and ["issue", "close"] not in later
    assert "closes" not in out["archive"]
    assert "Closes" not in _git(root, "log", "-1", "--format=%B", "main")


def test_sync_leaves_a_landed_issue_alone(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    name = _shipped(root)
    _hooked(root, capsys, name)
    calls = len(gh()["calls"])
    code, out = _sync(root, capsys, "001")
    assert code == 0 and "landed" in out["nothing to sync"], out
    assert not [c for c in gh()["calls"][calls:] if c[:2] == ["issue", "edit"]]


@pytest.mark.parametrize(
    "env, why",
    [
        ({"FAKE_GH_DEFAULT": "trunk"}, "the default branch is trunk, not main"),
        ({"FAKE_GH_FAIL": "repo"}, "couldn't read the default branch: boom"),
    ],
)
def test_a_default_branch_that_isnt_main_closes_the_issue_at_close(
    tmp_path, gh, capsys, monkeypatch, env: dict[str, str], why: str
) -> None:
    """No push to `main` would close it there, so close closes it, as before `landed`."""
    root = _repo(tmp_path)
    _shipped(root)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    [issue] = gh()["issues"]
    assert issue["state"] == "CLOSED" and issue["reason"] == "completed"
    assert {"name": "landed"} not in issue["labels"]
    assert out["archive"]["closed_because"] == why and "closes" not in out["archive"]
    assert "Closes" not in _git(root, "log", "-1", "--format=%B", "main")


def test_check_says_where_and_writes_nothing(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    _shipped(root)
    calls = len(gh()["calls"])
    main = _git(root, "rev-parse", "main")
    code, out = _close(root, capsys, "001", check=True)
    assert code == 0 and out["archive"] == {"target": "github", "location": None}
    assert _git(root, "rev-parse", "main") == main and len(gh()["calls"]) == calls


def test_only_a_shipped_change_is_closed(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    folder = _open(root, "open-one")
    code, out = _close(root, capsys, "001")
    assert code == 1 and any("isn't shipped" in r for r in out["refusals"]) and folder.is_dir()


# ---------------------------------------------------------------- dropped


def _dropped(
    root: Path, slug: str = "thing", at: str = "build", extra: dict[str, str] | None = None
) -> str:
    """A change opened, worked to `at`, given its reason and run through `drop` in its worktree,
    as /sdlc:drop leaves it for close; its name."""
    folder = _open(root, slug)
    intent = folder / "intent.md"
    text = intent.read_text().replace("stage: plan\n", f"stage: {at}\n", 1)
    intent.write_text(text + "\n## Dropped\n\nThe drafts it reopens are gone.\n\nMore.\n")
    for name, text in (extra or {}).items():
        (folder / name).write_text(text, encoding="utf-8")
    assert sdlc.cmd_drop(folder.parent.parent, None) == 0
    return folder.name


def _parents(root: Path, ref: str) -> list[str]:
    return _git(root, "log", "-1", "--format=%P", ref).split()


def test_a_dropped_change_is_recorded_on_main_and_its_issue_closed_not_planned(
    tmp_path, gh, capsys
) -> None:
    root = _repo(tmp_path)
    name = _dropped(root, extra=BIG)
    tree = root / ".claude" / "worktrees" / name
    before, tip = _git(root, "rev-parse", "main"), _git(root, "rev-parse", name)
    assert sdlc.ready_to_close(root)[0]["kind"] == "dropped"
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    assert out["kind"] == "dropped"
    assert out["done"] == [
        "verify",
        "measure",
        "archive",
        "record",
        "remove worktree",
        "delete branch",
    ]
    assert _git(root, "log", "-1", "--format=%s", "main") == f"Drop {name}"
    assert _parents(root, "main") == [before, tip]
    changed = _git(root, "diff", "--name-only", "main^1", "main").split()
    assert set(changed) <= {".sdlc/last-id"}, changed
    body = _git(root, "log", "-1", "--format=%b", "main")
    assert "The drafts it reopens are gone." in body and "More." not in body
    assert "Dropped at build" in body
    assert "Closes" not in body, "nothing lands, so no push closes its issue"
    assert "closes" not in out["archive"] and "closed_because" not in out["archive"]
    # What measure found, as close writes it on a `Close` commit: here, no transcripts at all.
    measured = sdlc.metrics.parse_trailers(body)
    assert measured and measured["coverage"].startswith("none")
    assert out["measure"]["trailers"] and body.endswith(out["measure"]["trailers"][-1])
    [issue] = gh()["issues"]
    assert issue["state"] == "CLOSED" and issue["reason"] == "not planned"
    assert len(issue["comments"]) == 2 and issue["url"] in body
    assert not tree.exists() and _git(root, "branch", "--list", name) == ""
    _git(root, "merge-base", "--is-ancestor", tip, "main")  # still reachable: raises if not
    assert not _on_main(root, name)
    intent = _git(root, "show", f"main^2:work/{name}/intent.md")
    assert "stage: dropped" in intent and "dropped_at: build" in intent


def test_a_change_dropped_at_intent_is_committed_and_recorded_too(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    name = _dropped(root, at="plan")
    assert _git(root, "log", "-1", "--format=%s", name) == f"Record why {name} was dropped"
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    assert "Dropped at plan" in _git(root, "log", "-1", "--format=%b", "main")


def test_dropping_a_change_set_to_dropped_by_hand_finds_how_far_it_got(tmp_path, gh) -> None:
    root = _repo(tmp_path)
    folder = _open(root)
    tree = folder.parent.parent
    intent = folder / "intent.md"
    intent.write_text(intent.read_text().replace("stage: plan\n", "stage: test\n", 1))
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "work")
    intent.write_text(
        intent.read_text().replace("stage: test\n", "stage: dropped\n", 1) + "\n## Dropped\n\nNo.\n"
    )
    assert sdlc.cmd_drop(tree, None) == 0
    assert "dropped_at: test" in intent.read_text()


def test_drop_refuses_without_a_reason_or_with_other_work_uncommitted(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    folder = _open(root)
    tree = folder.parent.parent
    (tree / "half-done.py").write_text("x = 1\n", encoding="utf-8")
    capsys.readouterr()
    assert sdlc.cmd_drop(tree, None) == 1
    refusals = json.loads(capsys.readouterr().out)["refusals"]
    assert any("## Dropped" in r for r in refusals)
    assert any("half-done.py" in r for r in refusals)
    assert "stage: plan" in (folder / "intent.md").read_text(), "nothing stamped"


def test_a_dropped_change_already_on_main_is_refused(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    name = _dropped(root)
    _git(root, "merge", "--ff-only", "-q", name)
    before = _git(root, "rev-parse", "main")
    code, out = _close(root, capsys, "001")
    assert code == 1 and any("it landed" in r for r in out["refusals"]), out
    assert _git(root, "rev-parse", "main") == before and not gh()["issues"][0]["reason"]


def test_a_dropped_change_whose_issue_sync_closed_still_gets_every_artifact(
    tmp_path, gh, capsys
) -> None:
    """Sync closes a dropped change's issue as not planned, without the overflow comments: that
    isn't archived, so close posts them rather than taking the closed issue as done."""
    root = _repo(tmp_path)
    _dropped(root, extra=BIG)
    assert _sync(root, capsys, "001")[0] == 0
    assert gh()["issues"][0]["state"] == "CLOSED" and gh()["issues"][0]["comments"] == []
    # Two comments from people: as many as the artifacts to post, and standing in for neither.
    state = gh()
    state["issues"][0]["comments"] = [{"body": "Agreed, drop it."}, {"body": "Noted."}]
    _put(state)
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    [issue] = gh()["issues"]
    firsts = [c["body"].split("\n", 1)[0] for c in issue["comments"][2:]]
    assert firsts == ["<!-- sdlc:001-thing:plan.md -->", "<!-- sdlc:001-thing:notes.md -->"]
    assert issue["reason"] == "not planned"
    closes = [c for c in gh()["calls"] if c[:2] == ["issue", "close"]]
    assert len(closes) == 1, "an issue already closed isn't closed again"


def test_a_failed_drop_record_leaves_main_clean_and_a_rerun_finishes(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    name = _dropped(root)
    before = _git(root, "rev-parse", "main")
    hook = Path(_git(root, "rev-parse", "--absolute-git-dir")) / "hooks" / "pre-commit"
    hook.parent.mkdir(exist_ok=True)
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    code, out = _close(root, capsys, "001")
    assert code == 1 and out["skipped"][0] == "record", out
    assert _git(root, "rev-parse", "main") == before
    assert _git(root, "status", "--porcelain") == ""
    calls = len(gh()["calls"])
    hook.unlink()
    code, out = _close(root, capsys, "001")
    assert code == 0 and _git(root, "log", "-1", "--format=%s", "main") == f"Drop {name}", out
    later = [c[:2] for c in gh()["calls"][calls:]]
    assert ["issue", "edit"] not in later and ["issue", "close"] not in later


def test_a_rerun_after_the_record_skips_it(tmp_path, gh, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    name = _dropped(root)
    tree = root / ".claude" / "worktrees" / name
    monkeypatch.chdir(tree)  # inside the worktree: close records, then keeps it
    code, out = _close(root, capsys, "001")
    assert code == 3 and out["done"] == ["verify", "measure", "archive", "record"], out
    drop = _git(root, "rev-parse", "main")
    monkeypatch.chdir(root)
    code, out = _close(root, capsys, "001")
    assert code == 0 and _git(root, "rev-parse", "main") == drop, out


# ---------------------------------------------------------------- numbered locally


def test_target_none_still_removes_the_folder(tmp_path, gh, capsys) -> None:
    """History is the copy: the change's commit on main holds the folder close removes."""
    root = _repo(tmp_path, github=False)
    name = _shipped(root)
    assert name == "001-thing", "no GitHub numbering without the GitHub archive"
    code, out = _close(root, capsys, "001")
    assert code == 0 and out["archive"]["kept_because"] == "archive.target is none", out
    assert "archive" not in out["done"] and gh()["calls"] == []
    assert not _on_main(root, name)
    assert "stage: shipped" in _git(root, "show", f"main~1:work/{name}/intent.md")


def test_a_host_command_archives_and_says_where(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path, github=False)
    store = tmp_path / "store"
    store.mkdir()
    command = f"cp -R {{dir}} {store}/{{id}} && echo {store}/{{id}}"
    _config(root, f'[archive]\ntarget = "command"\ncommand = "{command}"\n')
    name = _shipped(root)
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    assert out["archive"]["location"] == f"{store}/001"
    assert (store / "001" / "intent.md").is_file()
    assert not _on_main(root, name)
    assert "Closes" not in _git(root, "log", "-1", "--format=%B", "main")


@pytest.mark.parametrize(
    "command, needle",
    [("exit 3", "exited 3"), ("true", "printed nowhere")],
)
def test_a_host_command_that_fails_or_says_nothing_keeps_the_folder(
    tmp_path, gh, capsys, command: str, needle: str
) -> None:
    root = _repo(tmp_path, github=False)
    _config(root, f'[archive]\ntarget = "command"\ncommand = "{command}"\n')
    name = _shipped(root)
    code, out = _close(root, capsys, "001")
    assert code == 1 and any(needle in r for r in out["refusals"]) and _on_main(root, name)


def test_target_command_without_a_command_is_a_refusal(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path, github=False)
    _config(root, '[archive]\ntarget = "command"\n')
    _shipped(root)
    main = _git(root, "rev-parse", "main")
    code, out = _close(root, capsys, "001")
    assert code == 1 and any("no command" in r for r in out["refusals"])
    assert out["done"] == [] and _git(root, "rev-parse", "main") == main


def test_config_says_whether_close_can_archive_and_who_numbers(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path, github=False)
    capsys.readouterr()
    sdlc.cmd_config(root)
    out = json.loads(capsys.readouterr().out)
    assert out["archive"]["target"] == "none" and out["archive"]["ids_from"] == "local"
    _config(root, '[archive]\ntarget = "github"\n')
    sdlc.cmd_config(root)
    out = json.loads(capsys.readouterr().out)
    assert out["archive"]["unavailable"] == "no remote on github.com"
    assert out["archive"]["ids_from"] == "github"


def test_last_id_lives_in_sdlc_and_survives_deleting_work(tmp_path, gh) -> None:
    root = _repo(tmp_path, github=False)
    tree = _open(root, "first").parent.parent
    assert (_state_dir(tree) / "last-id").read_text(encoding="utf-8") == "001\n"
    shutil.rmtree(tree / "work")
    assert sdlc.next_id(root) == "002"


def test_two_open_changes_each_take_an_issue(tmp_path, gh, monkeypatch) -> None:
    """The first change hasn't merged when the second opens: both are numbered by GitHub."""
    monkeypatch.setenv("FAKE_GH_START", "41")
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "first", 1, None, worktree=True) == 0
    assert sdlc.cmd_new(root, "second", 1, None, worktree=True) == 0
    assert [i["number"] for i in gh()["issues"]] == [42, 43]
    assert (root / ".claude" / "worktrees" / "043-second" / "work" / "043-second").is_dir()


def test_a_missing_counter_carries_on_from_the_closes_in_history(tmp_path) -> None:
    """Its work/ is empty and it has no counter: only history knows 012 was used."""
    root = _repo(tmp_path, github=False)
    _config(root, '[archive]\ntarget = "none"\n')
    for subject in ("Close 003-old", "Drop 012-gone", "Close 9-not-a-change"):
        _git(root, "commit", "-q", "--allow-empty", "-m", subject)
    assert sdlc.next_id(root) == "013"


# ---------------------------------------------------------------- the issue while it is open


def _put(state: dict) -> None:
    Path(os.environ["FAKE_GH_STATE"]).write_text(json.dumps(state))


def _set(folder: Path, old: str, new: str) -> None:
    intent = folder / "intent.md"
    intent.write_text(intent.read_text().replace(old, new, 1))


def _sync(root: Path, capsys, ident: str) -> tuple[int, dict]:
    capsys.readouterr()
    code = sdlc.cmd_sync(root, ident)
    return code, json.loads(capsys.readouterr().out)


def test_tier_zero_never_reaches_github(tmp_path, gh, monkeypatch) -> None:
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "new", "typo", "--tier", "0"])
    with pytest.raises(SystemExit):
        sdlc.main()
    assert gh()["calls"] == [] and not (root / ".claude" / "worktrees").exists()


def test_sync_labels_a_spike_like_any_other_stage(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    folder = _open(root)
    _set(folder, "stage: plan\n", "stage: spike\n")
    code, out = _sync(root, capsys, "001")
    assert code == 0, out
    names = {lb["name"] for lb in gh()["issues"][0]["labels"]}
    assert "stage: spike" in names and "stage: plan" not in names


def test_sync_renders_the_issue_and_swaps_only_its_own_labels(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    folder = _open(root)
    state = gh()
    state["issues"][0]["labels"].append({"name": "impact: high"})  # the host's own, not ours
    _put(state)
    _set(folder, "stage: plan\n", "stage: design\n")
    code, out = _sync(root, capsys, "001")
    assert code == 0, out
    [issue] = gh()["issues"]
    names = {lb["name"] for lb in issue["labels"]}
    assert names == {"sdlc", "tier: 1", "stage: design", "impact: high"}
    assert "<!-- sdlc:001-thing -->" in issue["body"] and "<b>intent.md</b>" in issue["body"]
    assert out["done"][0] == "body" and "unlabel stage: plan" in out["done"]
    assert issue["state"] == "OPEN"


def test_sync_links_dependencies_and_unlinks_only_changes(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    _open(root, "first")
    _open(root, "second")
    mine = _open(root, "third")
    state = gh()
    bug = {"number": 9, "title": "A bug", "state": "OPEN", "labels": [], "body": "it broke"}
    state["issues"].append({**bug, "url": "https://github.com/o/r/issues/9", "comments": []})
    state["issues"][2]["blockedBy"] = [2, 9]  # a stale link to a change, and a person's own
    _put(state)
    _set(mine, "depends_on:\n", "depends_on: [001, 044]\n")
    code, out = _sync(root, capsys, "003")
    assert code == 0, out
    assert sorted(gh()["issues"][2]["blockedBy"]) == [1, 9]
    assert "blocked by #1" in out["done"] and "no longer blocked by #2" in out["done"]
    assert out["skipped"] == ["depends_on 044: no issue for it yet"]


def test_sync_with_nothing_to_sync_says_why_and_succeeds(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    _config(root, '[archive]\ntarget = "none"\n')
    _open(root)
    code, out = _sync(root, capsys, "001")
    assert code == 0 and "archive.target is none" in out["nothing to sync"]
    _config(root, '[archive]\ntarget = "command"\ncommand = "echo x"\n')
    code, out = _sync(root, capsys, "001")
    assert code == 0 and "at close only" in out["nothing to sync"]
    assert not [c for c in gh()["calls"] if c[:2] == ["issue", "edit"]]


def test_a_failed_sync_exits_1_and_leaves_the_folder(tmp_path, gh, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    folder = _open(root)
    before = {p.name: p.read_text() for p in folder.iterdir()}
    monkeypatch.setenv("FAKE_GH_FAIL", "edit")
    code, out = _sync(root, capsys, "001")
    assert code == 1 and "edit failed" in out["error"]
    assert {p.name: p.read_text() for p in folder.iterdir()} == before


def test_a_dropped_change_closes_its_issue_as_not_planned(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    folder = _open(root)
    _set(folder, "stage: plan\n", "stage: dropped\n")
    code, out = _sync(root, capsys, "001")
    assert code == 0, out
    [issue] = gh()["issues"]
    assert issue["state"] == "CLOSED" and issue["reason"] == "not planned"
    assert {"name": "stage: dropped"} in issue["labels"]


# ---------------------------------------------------------------- the project doc's fields

PROJECT_DOC = """---
milestone: tracker
project: [Roadmap, Ops]
assignees: tracker
---

# How changes are tracked here
"""
FIELD_FLAGS = {
    "--milestone", "--remove-milestone", "--add-project", "--remove-project",
    "--add-assignee", "--remove-assignee",
}  # fmt: skip


def _with_project(root: Path, text: str = PROJECT_DOC) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "PROJECT.md").write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "project doc")


def _field_edits(gh) -> list[list[str]]:
    return [c for c in gh()["calls"] if c[:2] == ["issue", "edit"] and FIELD_FLAGS & set(c)]


def test_without_a_project_doc_no_field_is_read_or_set(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    folder = _open(root)
    _set(folder, "stage: plan\n", "stage: design\n")
    code, out = _sync(root, capsys, "001")
    assert code == 0, out
    assert _field_edits(gh) == []
    views = [c[c.index("--json") + 1] for c in gh()["calls"] if c[:2] == ["issue", "view"]]
    assert not any("milestone" in fields for fields in views), "a field that's off isn't read"
    assert gh()["issues"][0]["assignees"] == ["@me"]


def test_lookups_list_what_github_has(tmp_path, gh, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    _with_project(root)
    state = gh()
    state.update(milestones=["1.10", "Q4 2026"], assignees=["ana", "bo"], projects=["Roadmap"])
    _put(state)
    capsys.readouterr()
    assert sdlc.cmd_lookup(root, []) == 0
    fields = json.loads(capsys.readouterr().out)["fields"]
    assert fields["milestone"] == {
        "lookup": "tracker",
        "values": ["1.10", "Q4 2026"],
        "error": None,
    }
    assert fields["assignees"]["values"] == ["ana", "bo"]
    assert fields["project"] == {"lookup": "list", "values": ["Roadmap", "Ops"], "error": None}

    _with_project(root, PROJECT_DOC.replace("project: [Roadmap, Ops]", "project: tracker"))
    assert sdlc.cmd_lookup(root, ["project"]) == 0
    assert json.loads(capsys.readouterr().out)["fields"]["project"]["values"] == ["Roadmap"]
    monkeypatch.setenv("FAKE_GH_FAIL", "project")
    assert sdlc.cmd_lookup(root, ["project"]) == 0, "a field's error isn't the command's"
    row = json.loads(capsys.readouterr().out)["fields"]["project"]
    assert row["values"] == [] and "gh auth refresh -s read:project" in row["error"]


def test_enabled_fields_are_mirrored_exactly(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    _with_project(root)
    folder = _open(root)
    _set(
        folder,
        "depends_on:\n",
        'depends_on:\nmilestone: "Q4 2026"\nproject: [Roadmap]\nassignees:\n  - ana\n  - bo\n',
    )
    code, out = _sync(root, capsys, "001")
    assert code == 0, out
    [issue] = gh()["issues"]
    assert issue["milestone"] == "Q4 2026" and issue["projects"] == ["Roadmap"]
    assert sorted(issue["assignees"]) == ["ana", "bo"], "the intent's people replace @me"
    assert "milestone Q4 2026" in out["done"] and "assignees +ana +bo -@me" in out["done"]

    _set(folder, 'milestone: "Q4 2026"', 'milestone: "1.10"')
    _set(folder, "project: [Roadmap]", "project: []")
    _set(folder, "  - bo\n", "")
    code, out = _sync(root, capsys, "001")
    [issue] = gh()["issues"]
    assert (
        issue["milestone"] == "1.10" and issue["projects"] == [] and issue["assignees"] == ["ana"]
    )

    _set(folder, 'milestone: "1.10"', "milestone:")
    code, out = _sync(root, capsys, "001")
    assert gh()["issues"][0]["milestone"] is None and "no milestone" in out["done"]
    before = len(_field_edits(gh))
    code, out = _sync(root, capsys, "001")
    assert len(_field_edits(gh)) == before, "nothing differs, so nothing is edited"


def test_a_field_github_refuses_is_skipped_and_the_rest_land(
    tmp_path, gh, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    _with_project(root)
    folder = _open(root)
    _set(folder, "depends_on:\n", 'depends_on:\nmilestone: "Q4 2026"\nproject: [Roadmap]\n')
    _set(folder, "stage: plan\n", "stage: design\n")
    monkeypatch.setenv("FAKE_GH_FAIL_FLAG", "--add-project")
    code, out = _sync(root, capsys, "001")
    assert code == 0 and out["error"] is None, out
    [issue] = gh()["issues"]
    assert issue["milestone"] == "Q4 2026" and not issue.get("projects")
    assert {"name": "stage: design"} in issue["labels"]
    assert any(s.startswith("project:") and "scopes" in s for s in out["skipped"]), out

    _set(folder, "impact:\n", "impact: none\n")
    assert sdlc.cmd_ship(root, "001") == 0
    tree = folder.parent.parent
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "ship 001-thing")
    code, out = _close(root, capsys, "001")
    assert code == 0, out
    landed = {"name": "landed"} in gh()["issues"][0]["labels"]
    assert landed, "a refused field never stops the archive"
