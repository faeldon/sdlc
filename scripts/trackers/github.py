"""The GitHub tracker: every call to `gh` the plugin makes.

One issue per change, labelled `sdlc` and marked `<!-- sdlc:... -->` in its body, and numbered by
it: /sdlc:intent opens the issue and the change takes its number.
`sync` rewrites it from the change's artifacts after each stage's approval: the body, the
`tier:`/`stage:`/`impact:` labels, and a blocked-by link for each id in `depends_on`. Close
renders it a last time, labels it `landed`, and reads it back before the folder goes; the Close
commit says `Closes #N`, so GitHub closes the issue when that commit reaches the default branch.
Where the default branch isn't the base branch close lands on (`change["base"]`), close closes it
itself.

Loaded by path from `sdlc.py` (`tracker()`), only when `archive.target = "github"`. It never
imports `sdlc.py` and never reads `work/` or `.sdlc/`: what it needs crosses as a `change` dict.
Only the stdlib and the script's PEP 723 dependencies are available here.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ARCHIVE_LABEL = "sdlc"
DESCRIPTION = "A change tracked by the sdlc plugin"
# Archived on the local base branch, open until its Close commit reaches the default branch. Never
# one of the labels `_reconcile()` manages, so nothing removes it.
LANDED = "landed"
# An issue triage has recorded, as an inbox entry, on a change's `closes:` line, or as a verdict
# that closed it; and one waiting on its author for more detail. Neither is ever managed by sync.
TRIAGED = "triaged"
NEEDS_INFO = "needs-info"
NEEDS_INFO_MARKER = "<!-- sdlc:needs-info -->"
# One colour per group, so a list of issues reads by group at a glance.
COLOURS = {
    ARCHIVE_LABEL: "C5DEF5", "tier": "5319E7", "stage": "FBCA04", "impact": "D93F0B",
    LANDED: "0E8A16", TRIAGED: "BFD4F2", NEEDS_INFO: "D876E3",
}  # fmt: skip
# A comment holding an overflowed artifact opens `<!-- sdlc:NNN-slug:spec.md -->`. A rerun skips
# one already posted, so nothing is posted twice.
COMMENT_RE = re.compile(r"^<!-- sdlc:[^:]+:(\S+) -->$")


def _url(made: subprocess.CompletedProcess) -> str:
    return made.stdout.strip().splitlines()[-1] if made.returncode == 0 and made.stdout else ""


class Tracker:
    numbers = True

    def __init__(self, home: Path, cfg: dict) -> None:
        self.home = home
        self.cfg = cfg
        # Set by `archive()`: the line the Close commit carries so GitHub closes the issue on the
        # push, or why close closed it itself.
        self.closes: str | None = None
        self.closed_because: str | None = None
        # Set by `archive()`: each issue on the change's `closes:` line it couldn't close or let go.
        self.closes_errors: list[str] = []

    # ------------------------------------------------------------ plumbing

    def _gh(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["gh", *args], cwd=self.home, capture_output=True, text=True, input=stdin
        )

    def unavailable(self) -> str | None:
        """Why this tracker can't run here, or None. Reads no network: whether `gh` is installed
        and a remote points at GitHub."""
        if not shutil.which("gh"):
            return "gh isn't installed"
        remotes = subprocess.run(
            ["git", "-C", str(self.home), "remote", "-v"], capture_output=True, text=True
        )
        if "github.com" not in (remotes.stdout if remotes.returncode == 0 else ""):
            return "no remote on github.com"
        return None

    def readiness(self) -> list[tuple[str, str, str]]:
        authed = subprocess.run(["gh", "auth", "token"], capture_output=True).returncode == 0
        return [
            (
                "gh auth",
                "ok" if authed else "missing",
                "signed in" if authed else "run `gh auth login`",
            )
        ]

    def _labels(self, names: set[str]) -> None:
        """Make sure each label exists; one that already does is left alone. A failure here shows
        up as the edit that needed it."""
        for name in sorted(names):
            group = name.split(":", 1)[0]
            args = ["label", "create", name, "--color", COLOURS.get(group, "EDEDED")]
            what = DESCRIPTION if name == ARCHIVE_LABEL else f"sdlc {group}"
            args += ["--description", what]
            self._gh(*args)

    def _view(self, ref: str, fields: str = "number,url,state,body,comments,labels") -> dict | None:
        seen = self._gh("issue", "view", ref, "--json", fields)
        try:
            return json.loads(seen.stdout) if seen.returncode == 0 else None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _labelled(issue: dict, name: str = ARCHIVE_LABEL) -> bool:
        return name in {lb.get("name") for lb in issue.get("labels") or []}

    def _default_branch(self) -> tuple[str | None, str | None]:
        """(the repo's GitHub default branch, None), or (None, why)."""
        seen = self._gh("repo", "view", "--json", "defaultBranchRef")
        try:
            name = json.loads(seen.stdout)["defaultBranchRef"]["name"]
        except (ValueError, KeyError, TypeError):
            name = None
        if seen.returncode != 0 or not name:
            return None, seen.stderr.strip() or "gh repo view gave no default branch"
        return name, None

    def _change_issue(self, change: dict) -> dict | None:
        """The issue /sdlc:intent opened for this change: the issue of its number, labelled, and
        marked for this slug when it was opened. An unrelated issue that happens to share its
        number is never touched."""
        issue = self._view(str(int(change["id"])))
        if not issue or not self._labelled(issue):
            return None
        body = issue.get("body") or ""
        marks = (f"<!-- sdlc:{change['slug']} -->", f"<!-- sdlc:{change['name']} -->")
        return issue if any(m in body for m in marks) else None

    def _dependency(self, n: int) -> str | None:
        """Issue `n` when it is labelled and marked as a change's, else None."""
        issue = self._view(str(n))
        ok = issue and self._labelled(issue) and "<!-- sdlc:" in (issue.get("body") or "")
        return str(n) if ok else None

    # ------------------------------------------------------------ numbering

    def next_guess(self) -> int | None:
        """What GitHub would most likely number the next issue: one past the newest issue or pull
        request, which share a sequence. A guess, as `next` always says; the issue decides."""
        out = self._gh(
            "api", "repos/{owner}/{repo}/issues?state=all&per_page=1", "--jq", ".[0].number // 0"
        )
        try:
            return int(out.stdout.strip() or 0) + 1 if out.returncode == 0 else None
        except ValueError:
            return None

    def lookup(self, field: str) -> tuple[list[str] | None, str | None]:
        """The values GitHub has for an issue field, or why not: the repo's open milestones, the
        people who can be assigned, or the owner's projects (which need `read:project`)."""
        if field == "milestone":
            out = self._gh(
                "api", "repos/{owner}/{repo}/milestones?state=open&per_page=100",
                "--jq", "[.[].title]",
            )  # fmt: skip
        elif field == "assignees":
            out = self._gh(
                "api", "repos/{owner}/{repo}/assignees?per_page=100", "--jq", "[.[].login]"
            )
        elif field == "project":
            owner = self._gh("repo", "view", "--json", "owner", "--jq", ".owner.login")
            if owner.returncode != 0:
                return None, f"gh repo view failed: {owner.stderr.strip()}"
            out = self._gh(
                "project", "list", "--owner", owner.stdout.strip(), "--format", "json",
                "--jq", "[.projects[].title]",
            )  # fmt: skip
        else:
            return None, f"GitHub has no issue field {field!r}"
        if out.returncode != 0:
            return None, out.stderr.strip() or f"gh failed listing {field}"
        try:
            return json.loads(out.stdout or "[]"), None
        except json.JSONDecodeError:
            return None, f"gh's {field} list didn't parse"

    def _create(self, title: str, labels: set[str], body: str) -> subprocess.CompletedProcess:
        """A new issue with these labels, assigned to whoever runs this."""
        self._labels(labels)
        args = ["issue", "create", "--title", title, "--body-file", "-", "--assignee", "@me"]
        for name in sorted(labels):
            args += ["--label", name]
        return self._gh(*args, stdin=body)

    def claim(
        self, slug: str, title: str, tier: int, used: set[int]
    ) -> tuple[int | None, str | None, str | None]:
        """Open the change's issue: (its number, URL, None), or (None, URL or None, why). The
        change is named after the number. No lock: GitHub hands out each number once, to whoever
        asks."""
        body = (
            f"<!-- sdlc:{slug} -->\nOpened by `/sdlc:intent`, which fills it in once the intent "
            "is written. Updated at each stage; archived by `/sdlc:close`.\n"
        )
        made = self._create(title, {ARCHIVE_LABEL, f"tier: {tier}", "stage: plan"}, body)
        url = _url(made)
        try:
            n = int(url.rstrip("/").rsplit("/", 1)[1])
        except (IndexError, ValueError):
            why = made.stderr.strip() or made.stdout.strip()
            return None, None, f"gh issue create failed: {why}"
        if n in used:
            left = self.drop(url, f"#{n} is already a change number here")
            what = f"it is still open: close it by hand ({left})" if left else "closed it"
            return (
                None,
                url,
                (
                    f"issue #{n} has a number a locally numbered open change already holds, so "
                    f'{what}. Keep `ids = "local"` until those are archived'
                ),
            )
        return n, url, None

    def drop(self, url: str, why: str) -> str | None:
        """Close an issue `claim()` opened for a change that was never made, as not planned: None,
        or why it is still open. Its `stage:` label goes too, in an edit of its own whose refusal
        is skipped, so a closed issue doesn't still read `stage: plan`."""
        closed = self._gh(
            "issue", "close", url, "--reason", "not planned", "--comment", f"Not opened: {why}."
        )
        if closed.returncode != 0:
            return closed.stderr.strip() or f"gh issue close exited {closed.returncode}"
        seen = (self._view(url, "labels") or {}).get("labels") or []
        stages = sorted(n for n in {lb.get("name") or "" for lb in seen} if n.startswith("stage: "))
        if stages:
            self._gh("issue", "edit", url, *(a for n in stages for a in ("--remove-label", n)))
        return None

    # ------------------------------------------------------------ intake
    #
    # Issues filed by people who don't run a session. The core decides what each one is and
    # renders every comment; these only read GitHub and set what they are told.

    INTAKE_FIELDS = "number,url,title,body,labels,author,createdAt,comments"

    def _issues(self, *args: str, fields: str, limit: int) -> tuple[list[dict] | None, str | None]:
        out = self._gh(
            "issue", "list", "--state", "open", *args, "--json", fields, "--limit", str(limit)
        )
        if out.returncode != 0:
            return None, out.stderr.strip() or "gh issue list failed"
        try:
            return json.loads(out.stdout or "[]"), None
        except json.JSONDecodeError:
            return None, "gh issue list didn't parse"

    @staticmethod
    def _names(issue: dict) -> set[str]:
        return {lb.get("name") or "" for lb in issue.get("labels") or []}

    @staticmethod
    def _replied(issue: dict) -> bool:
        """Whether the issue's author has commented since the newest comment asking for detail.
        With no such comment, the label was set by hand, and the issue is read as answered."""
        author = (issue.get("author") or {}).get("login")
        comments = issue.get("comments") or []
        asked = [k for k, c in enumerate(comments) if NEEDS_INFO_MARKER in (c.get("body") or "")]
        if not asked:
            return True
        later = comments[asked[-1] + 1 :]
        return any((c.get("author") or {}).get("login") == author for c in later)

    def intake(self, limit: int = 200) -> tuple[list[dict] | None, bool, str | None]:
        """The open issues no change claims and triage hasn't recorded: (issues, whether more than
        `limit` were left out, None), or (None, False, why). One waiting on its author for detail
        comes back once the author has replied, flagged `replied`."""
        items, err = self._issues(fields=self.INTAKE_FIELDS, limit=limit + 1)
        if items is None:
            return None, False, err
        more = len(items) > limit
        out = []
        for i in items[:limit]:
            names = self._names(i)
            if names & {ARCHIVE_LABEL, LANDED, TRIAGED}:
                continue
            waiting = NEEDS_INFO in names
            if waiting and not self._replied(i):
                continue
            out.append(
                {
                    "number": i.get("number"),
                    "url": i.get("url"),
                    "title": i.get("title"),
                    "body": i.get("body") or "",
                    "labels": sorted(names),
                    "author": (i.get("author") or {}).get("login"),
                    "created": i.get("createdAt"),
                    "replied": waiting,
                }
            )
        return out, more, None

    def dangling(
        self, recorded: set[int], limit: int = 200
    ) -> tuple[list[dict] | None, str | None]:
        """The open issues labelled `triaged` that `recorded`, the numbers the repo records, doesn't
        name: (issues, None), or (None, why). The core says what the repo records."""
        items, err = self._issues("--label", TRIAGED, fields="number,url,title", limit=limit)
        if items is None:
            return None, err
        return [i for i in items if i.get("number") not in recorded], None

    def titles(self, numbers: list[int]) -> list[dict]:
        """Each issue's number, title, state and URL, or its `error` when it can't be read."""
        out = []
        for n in numbers:
            seen = self._view(str(n), "number,title,state,url")
            out.append(seen if seen else {"number": n, "error": f"gh issue view failed on #{n}"})
        return out

    @staticmethod
    def _parent_of(issue: dict) -> int | None:
        parent = issue.get("parent")
        return parent.get("number") if isinstance(parent, dict) else None

    def _set_parent(self, ref: str, parent: int | None, have: int | None) -> str | None:
        """Make `parent` the issue's parent, or remove its parent when `parent` is None and it has
        one: None, or why not. A parent already right is left alone."""
        if have == parent:
            return None
        if have is not None:
            made = self._gh("issue", "edit", ref, "--remove-parent")
            if made.returncode != 0:
                return f"gh issue edit #{ref} --remove-parent failed: {made.stderr.strip()}"
        if parent is not None:
            made = self._gh("issue", "edit", ref, "--parent", str(parent))
            if made.returncode != 0:
                return f"gh issue edit #{ref} --parent {parent} failed: {made.stderr.strip()}"
        return None

    def _comment_once(self, ref: str, seen: dict, comment: str, marker: str) -> str | None:
        """Post `comment` under `marker` unless a comment already holds the marker."""
        if any(marker in (c.get("body") or "") for c in seen.get("comments") or []):
            return None
        said = self._gh("issue", "comment", ref, "--body-file", "-", stdin=f"{marker}\n{comment}")
        if said.returncode != 0:
            return f"gh issue comment failed on #{ref}: {said.stderr.strip()}"
        return None

    def mark(
        self,
        number: int,
        comment: str,
        marker: str,
        parent: int | None = None,
        close: str | None = None,
    ) -> str | None:
        """Record triage on issue `number`: its comment once, the `triaged` label (and no longer
        `needs-info`), `parent` as its parent when given, and closed for `close` (`completed` or
        `not planned`) when given and still open. None, or why not; safe to rerun."""
        ref = str(number)
        seen = self._view(ref, "number,state,comments,labels,parent")
        if seen is None:
            return f"gh issue view failed on #{number}"
        if err := self._comment_once(ref, seen, comment, marker):
            return err
        names = self._names(seen)
        args = []
        if TRIAGED not in names:
            self._labels({TRIAGED})
            args += ["--add-label", TRIAGED]
        if NEEDS_INFO in names:
            args += ["--remove-label", NEEDS_INFO]
        if args:
            made = self._gh("issue", "edit", ref, *args)
            if made.returncode != 0:
                return f"gh issue edit failed on #{number}: {made.stderr.strip()}"
        if parent is not None and (err := self._set_parent(ref, parent, self._parent_of(seen))):
            return err
        if close and seen.get("state") != "CLOSED":
            made = self._gh("issue", "close", ref, "--reason", close)
            if made.returncode != 0:
                return f"gh issue close failed on #{number}: {made.stderr.strip()}"
        return None

    def unmark(self, number: int, comment: str, marker: str) -> str | None:
        """Send issue `number` back to triage: its comment once, no `triaged` label, no parent.
        None, or why not; safe to rerun."""
        ref = str(number)
        seen = self._view(ref, "number,state,comments,labels,parent")
        if seen is None:
            return f"gh issue view failed on #{number}"
        if err := self._comment_once(ref, seen, comment, marker):
            return err
        if TRIAGED in self._names(seen):
            made = self._gh("issue", "edit", ref, "--remove-label", TRIAGED)
            if made.returncode != 0:
                return f"gh issue edit failed on #{number}: {made.stderr.strip()}"
        return self._set_parent(ref, None, self._parent_of(seen))

    def needs_info(self, number: int, comment: str) -> str | None:
        """Ask issue `number`'s author for detail: the comment, unless the last one asking is
        still unanswered, and the `needs-info` label. None, or why not; safe to rerun."""
        ref = str(number)
        seen = self._view(ref, "number,author,comments,labels")
        if seen is None:
            return f"gh issue view failed on #{number}"
        asked = any(NEEDS_INFO_MARKER in (c.get("body") or "") for c in seen.get("comments") or [])
        if not asked or self._replied(seen):
            said = self._gh(
                "issue", "comment", ref, "--body-file", "-",
                stdin=f"{NEEDS_INFO_MARKER}\n{comment}",
            )  # fmt: skip
            if said.returncode != 0:
                return f"gh issue comment failed on #{number}: {said.stderr.strip()}"
        if NEEDS_INFO not in self._names(seen):
            self._labels({NEEDS_INFO})
            made = self._gh("issue", "edit", ref, "--add-label", NEEDS_INFO)
            if made.returncode != 0:
                return f"gh issue edit failed on #{number}: {made.stderr.strip()}"
        return None

    # ------------------------------------------------------------ mirroring

    @staticmethod
    def _wanted(change: dict) -> set[str]:
        """The labels this change should carry: one per group, none for impact while unset."""
        out = {ARCHIVE_LABEL}
        for group in ("tier", "stage", "impact"):
            if change.get(group):
                out.add(f"{group}: {change[group]}")
        return out

    @staticmethod
    def _managed(change: dict) -> set[str]:
        """Every label sync may remove: exactly the names it would ever set. A host's own
        `impact: high` is not one of them."""
        return {f"{g}: {v}" for g, values in change["vocabulary"].items() for v in values}

    def _reconcile(self, url: str, change: dict) -> tuple[list[str], list[str], str | None]:
        """Labels and blocked-by links brought in line with the change: (done, skipped, error).
        Only managed labels and links to other changes' issues are ever removed."""
        # The project doc's fields are read only when it turns them on.
        extra = ",milestone,projectItems,assignees" if change.get("fields") else ""
        seen = self._view(url, "labels,blockedBy,subIssues" + extra)
        if seen is None:
            return [], [], f"gh issue view failed on {url}"
        have = {lb.get("name") for lb in seen.get("labels") or []}
        wanted = self._wanted(change)
        add = wanted - have
        drop = (have & self._managed(change)) - wanted
        done: list[str] = []
        skipped: list[str] = []
        # A GraphQL connection, `{"nodes": [...], "totalCount": n}`, not a list.
        nodes = (seen.get("blockedBy") or {}).get("nodes") or []
        linked = {str(b.get("number")) for b in nodes}
        wanted_links = set()
        for n in change["depends_on"]:
            ref = self._dependency(n)
            if ref is None:
                skipped.append(f"depends_on {n:03d}: no issue for it yet")
            else:
                wanted_links.add(ref)
        unlink = set()
        for ref in linked - wanted_links:
            other = self._view(ref)
            if other and self._labelled(other):
                unlink.add(ref)  # another change's issue no longer listed; anything else stays

        args = []
        for name in sorted(add):
            args += ["--add-label", name]
        for name in sorted(drop):
            args += ["--remove-label", name]
        for ref in sorted(wanted_links - linked):
            args += ["--add-blocked-by", ref]
        for ref in sorted(unlink):
            args += ["--remove-blocked-by", ref]
        if args:
            self._labels(add)
            edited = self._gh("issue", "edit", url, *args)
            if edited.returncode != 0:
                return done, skipped, f"gh issue edit failed on {url}: {edited.stderr.strip()}"
            done += [f"label {n}" for n in sorted(add)] + [f"unlabel {n}" for n in sorted(drop)]
            done += [f"blocked by #{r}" for r in sorted(wanted_links - linked)]
            done += [f"no longer blocked by #{r}" for r in sorted(unlink)]
        self._fields(url, change, seen, done, skipped)
        self._sub_issues(change, seen, done, skipped)
        return done, skipped, None

    def _sub_issues(self, change: dict, seen: dict, done: list[str], skipped: list[str]) -> None:
        """The change's issue made the parent of every issue on its `closes:` line, so a filer
        follows it; one that left the line goes back to no parent, but only one triage recorded
        (labelled `triaged`): a sub-issue a person added stays. A refusal is skipped, never
        fatal."""
        number = int(change["id"])
        nodes = seen.get("subIssues") or []
        nodes = nodes.get("nodes") or [] if isinstance(nodes, dict) else nodes
        have = {int(s["number"]) for s in nodes if s.get("number") is not None}
        wanted = set(change.get("closes") or [])
        for n in sorted(wanted - have):
            child = self._view(str(n), "number,parent")
            err = (
                f"gh issue view failed on #{n}"
                if child is None
                else self._set_parent(str(n), number, self._parent_of(child))
            )
            (skipped if err else done).append(f"closes #{n}: {err}" if err else f"sub-issue #{n}")
        for n in sorted(have - wanted):
            child = self._view(str(n), "number,labels,parent") or {}
            if TRIAGED not in self._names(child):
                continue
            err = self._set_parent(str(n), None, number)
            (skipped if err else done).append(
                f"closes #{n}: {err}" if err else f"no longer sub-issue #{n}"
            )

    def _fields(
        self, url: str, change: dict, seen: dict, done: list[str], skipped: list[str]
    ) -> None:
        """The project doc's fields made to match the intent exactly, one edit each, so one that
        GitHub refuses (no `project` scope, a milestone that's gone) is skipped and the rest still
        land. A field the doc doesn't turn on isn't in `change["fields"]`, and is never touched."""
        for name, want in (change.get("fields") or {}).items():
            if name == "milestone":
                have = (seen.get("milestone") or {}).get("title")
                target = want[0] if want else None
                if have == target:
                    continue
                args = ["--milestone", target] if target else ["--remove-milestone"]
                what = f"milestone {target}" if target else "no milestone"
            else:
                key, flag = {"project": ("title", "project"), "assignees": ("login", "assignee")}[
                    name
                ]
                items = seen.get("projectItems" if name == "project" else "assignees") or []
                have = {i.get(key) for i in items}
                add, drop = set(want) - have, have - set(want)
                if not add and not drop:
                    continue
                args = [a for v in sorted(add) for a in (f"--add-{flag}", v)]
                args += [a for v in sorted(drop) for a in (f"--remove-{flag}", v)]
                what = " ".join([*(f"+{v}" for v in sorted(add)), *(f"-{v}" for v in sorted(drop))])
                what = f"{name} {what}"
            edited = self._gh("issue", "edit", url, *args)
            if edited.returncode != 0:
                skipped.append(f"{name}: {edited.stderr.strip() or 'gh issue edit failed'}")
            else:
                done.append(what)

    def sync(self, change: dict) -> dict:
        """Rewrite the change's issue from its artifacts as they are now. Never creates one; a
        change at `stage: dropped` closes its issue as not planned."""
        if change["error"]:
            return {"error": change["error"]}
        issue = self._change_issue(change)
        if issue is None:
            why = f"no issue {int(change['id'])} labelled {ARCHIVE_LABEL} and marked for it"
            return {"nothing": why}
        url = issue["url"]
        if change["stage"] != "dropped" and issue["state"] == "CLOSED":
            return {"nothing": f"{url} is closed: /sdlc:close has archived it"}
        if change["stage"] != "dropped" and self._labelled(issue, LANDED):
            return {"nothing": f"{url} is {LANDED}: /sdlc:close has archived it"}
        report: dict = {"issue": url, "done": [], "skipped": [], "error": None}
        edited = self._gh("issue", "edit", url, "--body-file", "-", stdin=change["body"])
        if edited.returncode != 0:
            report["error"] = f"gh issue edit failed on {url}: {edited.stderr.strip()}"
            return report
        report["done"].append("body")
        done, skipped, err = self._reconcile(url, change)
        report["done"] += done
        report["skipped"] += skipped
        report["error"] = err
        if not err and change["stage"] == "dropped" and issue["state"] != "CLOSED":
            shut = self._gh("issue", "close", url, "--reason", "not planned")
            if shut.returncode != 0:
                report["error"] = f"gh issue close failed on {url}: {shut.stderr.strip()}"
            else:
                report["done"].append("closed as not planned")
        return report

    @staticmethod
    def _key(text: str) -> str:
        """Which artifact a comment holds, by its first line."""
        first = text.split("\n", 1)[0]
        m = COMMENT_RE.match(first)
        return m.group(1) if m else first

    def _holds(self, issue: dict, marker: str, comments: list[str]) -> bool:
        """Whether the issue is archived: closed or `landed`, marked, and with every overflow
        comment, each found by its header, so a person's comment never stands in for an artifact.
        Closed is how GitHub leaves it after the push."""
        posted = {self._key(c.get("body") or "") for c in issue.get("comments") or []}
        return (
            (issue.get("state") == "CLOSED" or self._labelled(issue, LANDED))
            and marker in (issue.get("body") or "")
            and {self._key(c) for c in comments} <= posted
        )

    def _fill_and_close(
        self,
        url: str,
        marker: str,
        comments: list[str],
        have: list[dict],
        reason: str,
        shut: bool,
        land: bool,
    ) -> str | None:
        """Post the comments the issue lacks, then label it `landed` when `land` says GitHub will
        close it on the push, else close it, unless `shut` says it already is; then read it back.
        Why not, or None."""
        posted = {self._key(c.get("body") or "") for c in have}
        for part in comments:
            if self._key(part) in posted:
                continue  # posted by an earlier run that stopped partway
            said = self._gh("issue", "comment", url, "--body-file", "-", stdin=part)
            if said.returncode != 0:
                return f"gh issue comment failed on {url}: {said.stderr.strip()}"
        if not shut and land:
            self._labels({LANDED})
            edited = self._gh("issue", "edit", url, "--add-label", LANDED)
            if edited.returncode != 0:
                return f"gh issue edit failed on {url}: {edited.stderr.strip()}"
        elif not shut:
            closed = self._gh("issue", "close", url, "--reason", reason)
            if closed.returncode != 0:
                return f"gh issue close failed on {url}: {closed.stderr.strip()}"
        # Read it back before anything is deleted: what counts is what GitHub holds, not what was
        # sent.
        if not self._holds(self._view(url) or {}, marker, comments):
            return f"{url} doesn't read back as archived with every artifact"
        return None

    def _landing(self, change: dict) -> bool:
        """Whether a push will close this change's issue, so close only labels it: a shipped
        change, on a repo whose default branch is the base branch close lands on (`base`).
        Otherwise close closes it, and `closed_because` says why for a shipped one."""
        if change.get("stage") == "dropped":
            return False
        branch, why = self._default_branch()
        base = change.get("base")
        if branch and branch == base:
            return True
        self.closed_because = (
            f"the default branch is {branch}, not {base}"
            if branch
            else f"couldn't read the default branch: {why}"
        )
        return False

    @staticmethod
    def _closing(url: str) -> str:
        """The line GitHub reads on the default branch to close the issue at `url`."""
        return f"Closes #{url.rstrip('/').rsplit('/', 1)[1]}"

    def archive(self, change: dict) -> tuple[str | None, str | None]:
        """(issue URL, None) once an issue holds every artifact, archived; (None, why) not.

        The change goes into the issue it was numbered from. Labels and links are set on the
        way; one GitHub won't set doesn't stop the archive, since the artifacts are what close
        has to have mirrored. A dropped change's issue is closed as not planned. A shipped one's
        is labelled `landed` and left open, with `closes` set for the Close commit, so the push
        closes it as completed; where no push would, close closes it now and `closed_because`
        says why."""
        self.closes = self.closed_because = None
        self.closes_errors = []
        if change["error"]:
            return None, change["error"]
        marker, body, comments = change["marker"], change["body"], change["comments"]
        name = change["name"]
        reason = "not planned" if change.get("stage") == "dropped" else "completed"
        issue = self._change_issue(change)
        if issue is None:
            return None, (
                f"no issue {int(change['id'])} labelled {ARCHIVE_LABEL} and marked for {name}"
            )
        land = self._landing(change)
        url = issue["url"]
        shut = issue["state"] == "CLOSED"
        if shut:
            self.closed_because = None  # closed already: close closes nothing now
        if self._holds(issue, marker, comments) and (shut or land):
            # Archived by an earlier run that stopped before deleting.
            self._settle(change, None if shut else self._closing(url), land)
            return url, None
        # Closed but not archived: sync closes a dropped change's issue without the comments.
        # Landed but no push will close it: close it now.
        edited = self._gh("issue", "edit", url, "--body-file", "-", stdin=body)
        if edited.returncode != 0:
            return None, f"gh issue edit failed on {url}: {edited.stderr.strip()}"
        self._reconcile(url, change)
        have = issue.get("comments", [])
        err = self._fill_and_close(url, marker, comments, have, reason, shut, land)
        if err:
            return None, err
        self._settle(change, self._closing(url) if land and not shut else None, land)
        return url, None

    def _settle(self, change: dict, own: str | None, land: bool) -> None:
        """What becomes of the issues on the change's `closes:` line, once its own is archived. A
        shipped change closes them: a `Closes #N` line each on the Close commit beside its own
        (`closes`) when the push will close them, or closed now where it won't. A dropped one lets
        them go back to triage. One that fails is in `closes_errors` and stays open: it never
        stops close. Every comment is the core's, in `change["texts"]`."""
        lines = [own] if own else []
        self.closes_errors = []
        texts = change.get("texts") or {}
        dropped = change.get("stage") == "dropped"
        for n in change.get("closes") or []:
            if dropped:
                err = self.unmark(
                    n, texts.get("dropped", ""), f"<!-- sdlc:drop:{change['name']} -->"
                )
            elif land:
                lines.append(f"Closes #{n}")
                continue
            else:
                seen = self._view(str(n), "number,state")
                if seen is None:
                    err = f"gh issue view failed on #{n}"
                elif seen.get("state") == "CLOSED":
                    err = None
                else:
                    made = self._gh(
                        "issue", "close", str(n), "--reason", "completed",
                        "--comment", texts.get("fixed", ""),
                    )  # fmt: skip
                    err = (
                        made.stderr.strip() or "gh issue close failed" if made.returncode else None
                    )
            if err:
                self.closes_errors.append(f"#{n}: {err}")
        self.closes = "\n".join(lines) or None


def make(home: Path, cfg: dict) -> Tracker:
    return Tracker(home, cfg)
