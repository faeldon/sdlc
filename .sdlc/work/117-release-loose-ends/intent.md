---
id: 117
slug: release-loose-ends
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: [2026-10-25-4, 2026-10-25-5, 2026-10-25-6]
depends_on:
serves: [O1]
---

# 117 — Release keeps a host's changelog and version lines, and publish's note leaves the machine

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Three gaps in the release loop, each raised on 2026-10-25 by a host adopting the plugin:

- **2026-10-25-4:** `release.changelog` puts each release's `## X.Y.Z — date` section right under
  the file's `# ` title. A changelog that opens with prose or a table before its releases is split
  by it, and a Keep a Changelog file's `## [Unreleased]` section is left above the new one.
- **2026-10-25-5:** `VERSION_RE` reads `version = "x"` and `"version": "x"`, not Python's
  `__version__ = "x"`, so a host has to move its version elsewhere to use `/sdlc:release`. And with
  no tag for the current version, release's `git tag -a` hint points at the last commit that
  touched the version files, which can predate the repo's adoption of the plugin, so the first
  release takes in every change closed since.
- **2026-10-25-6:** publish marks a tag `published` in `refs/notes/sdlc` so a rerun skips the host's
  upload, but the notes ref isn't pushed: from a second clone, publish runs the upload again.
  `docs/REFERENCE.md` also doesn't say that the tag message holds the notes (`gh release create
  {tag} --notes-from-tag`), that `release.prepare` can show what a push will upload (`git lfs push
  --dry-run`), or that releases outside `release.tag`'s pattern live outside the loop.

## Outcome

- A host can mark where releases go in its changelog (`<!-- sdlc:releases -->`, inserted after),
  falling back to today's place, and the section heading is a template a host can override.
- Release reads `__version__ = "x"` as a version line.
- With no tag for the current version, the hint points at the adoption commit when that is later
  than the last version change.
- Publish pushes the notes ref with the tag, inside `cmd_publish`, so a second clone skips an
  upload already made.
- `docs/REFERENCE.md` says the three things above.
- Tests in `tests/test_release.py` (or where release is tested) pin each.
- **Moves O1:** a repo adopting the plugin releases with the changelog and version files it already
  has.

## Affected

- **Area:** the release loop.
- **Files & components:** `scripts/sdlc.py` (`VERSION_RE`, `cmd_release`, the changelog writer,
  the missing-tag hint, `cmd_publish`, `_push()`), `templates/` (a changelog section template),
  `docs/REFERENCE.md`, tests.
- **Downstream:** every host that releases or publishes with the plugin.
- **Contracts:** only the named steps push, through `_push()`, never forced (the notes ref goes
  through it too); a new template the script reads goes in `TEMPLATE_READS`; `stamp_shipped`-style
  in-place edits for version lines.

## Constraints

- A host with today's changelog sees no change unless it adds the marker.
- Pushing the notes ref never forces, and a refused notes push doesn't fail a publish.

## Open questions

- ~~Is the adoption commit found from `.sdlc/setup.json`'s first record, or the first commit adding
  `.sdlc/config.toml`?~~ Resolved: the first commit adding `.sdlc/config.toml` (spec R6).
- ~~Should the notes ref be pushed by release too (when `git.push` names it), or only by publish?~~
  Resolved: only publish, the one writer of `refs/notes/sdlc` (spec R7). The person chose the fetch
  after publish's yes, not before its question, and `templates/changelog.md` as a second exception
  to the one-shape invariant.
