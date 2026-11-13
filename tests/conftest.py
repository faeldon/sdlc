"""What every test shares."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def git_identity(monkeypatch) -> None:
    """`close` commits on main, so the git it runs needs an author, as a host's git has one."""
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "t")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "t@t")


# GitHub, as a fake `gh` on PATH that keeps its issues in a JSON file, so the tests that
# reach the tracker run offline: test_archive.py's, and the adoption test that closes one.
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


def said(body):
    # A comment as gh gives it: who wrote it and when, the clock one tick per comment.
    st["clock"] = st.get("clock", 0) + 1
    who = os.environ.get("FAKE_GH_USER", "me")
    return {"body": body, "author": {"login": who}, "createdAt": f"2026-10-26T00:{st['clock']:04d}"}


def shaped(i, keys):
    # The fields in gh's shapes: objects and connections, not what the state keeps.
    out = {k: i.get(k) for k in keys}
    if "author" in out:
        out["author"] = {"login": i.get("author") or "me"}
    if "parent" in out:
        out["parent"] = {"number": i["parent"]} if i.get("parent") else None
    if "subIssues" in out:
        kids = [{"number": x["number"]} for x in st["issues"] if x.get("parent") == i["number"]]
        out["subIssues"] = {"nodes": kids, "totalCount": len(kids)}
    if "comments" in out:
        out["comments"] = i.get("comments") or []
    return out


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
    keys = ["number", "title", "url", "state"]
    if "--json" in args:
        keys = args[args.index("--json") + 1].split(",")
    found = [i for i in st["issues"] if "--state" not in args or i["state"] == "OPEN"]
    for name in every("--label"):
        found = [i for i in found if name in [lb["name"] for lb in i["labels"]]]
    if "--limit" in args:
        found = found[: int(args[args.index("--limit") + 1])]
    done(out=json.dumps([shaped(i, keys) for i in found]))
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
    if "--remove-parent" in args:
        i["parent"] = None
    if "--parent" in args:
        if i.get("parent"):
            print("issue already has a parent", file=sys.stderr)
            done(1)
        i["parent"] = int(args[args.index("--parent") + 1])
    if "--milestone" in args:
        i["milestone"] = args[args.index("--milestone") + 1]
    if "--remove-milestone" in args:
        i["milestone"] = None
    for field, noun in (("projects", "project"), ("assignees", "assignee")):
        have = [x for x in i.get(field) or [] if x not in every(f"--remove-{noun}")]
        i[field] = have + [x for x in every(f"--add-{noun}") if x not in have]
    done()
if args[:2] == ["issue", "comment"]:
    find(args[2])["comments"].append(said(sys.stdin.read()))
    done()
if args[:2] == ["issue", "close"]:
    i = find(args[2])
    i["state"], i["reason"] = "CLOSED", args[args.index("--reason") + 1]
    if "--comment" in args:
        i["comments"].append(said(args[args.index("--comment") + 1]))
    done()
if args[:2] == ["issue", "view"]:
    i = find(args[2])
    if i is None:
        done(1)
    keys = args[args.index("--json") + 1].split(",")
    out = shaped(i, keys)
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
