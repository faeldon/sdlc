---
id: 117
slug: release-loose-ends
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 117 — Release keeps a host's changelog and version lines, and publish's note leaves the machine · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code before designing:
- The changelog writer is `with_changelog()`, called only from `cmd_release`'s `changelog()` step.
- Version lines are read and written only through `VERSION_RE` (`read_versions()`, `write_version()`).
- The missing-tag hint is built in one place, `unreleased()`.
- The `published` note is written only by `cmd_publish`'s `run_command()`, on `refs/notes/sdlc`. Release writes only `refs/notes/sdlc-prepared`.
- `sdlc.py` runs no `git fetch` today.
- Templates are found by `template_path()`, and the issue template's `{{name}}` placeholders are filled by plain `str.replace`.

The tests named below go in `tests/test_release.py` unless another file is named.

1. **R1. With the marker, the release goes after it.** When the changelog has a line whose stripped text is exactly `<!-- sdlc:releases -->`, release puts the new section right after the first such line: one blank line, then the section, then the rest of the file with its leading blank lines squeezed to one. Every byte before the marker and the marker line itself stay as they were. Test `test_a_marker_places_the_release_after_it`: a changelog of title, prose, a table, a `## [Unreleased]` section, the marker and an older release. Afterwards everything above the marker is byte-identical, and the new section sits between the marker and the older release. It fails if the section lands under the title.
2. **R2. Without the marker, nothing changes.** A changelog with no marker gets exactly the bytes it gets today: the section under a first-line `# ` title, else at the top. A new file still starts as `# Changelog`. The existing `test_the_notes_are_the_same_in_the_tag_the_commit_and_the_changelog` keeps passing. A new `test_without_a_marker_the_changelog_is_written_as_before` compares the output with the exact string today's `with_changelog` returns, for a titled file, an untitled file and an empty file.
3. **R3. The section comes from a template a host can override.** It is rendered from `templates/changelog.md` with the placeholders `{{version}}`, `{{date}}` and `{{notes}}`, filled by `str.replace`, so a brace in a note is never a format error. A host's `.sdlc/templates/changelog.md` replaces the plugin's (`template_path()`).
   - The plugin's template renders byte-for-byte what today's f-string does: `## {{version}} — {{date}}`, a blank line, `{{notes}}`.
   - Test `test_a_host_changelog_template_shapes_the_section`: a host template `## [{{version}}] - {{date}}` gives that heading in the changelog.
4. **R4. The template's placeholders are registered.**
   - `TEMPLATE_READS["changelog.md"]` lists the placeholders `{{version}}` and `{{notes}}`. `{{date}}` is optional, since a host may not want dates.
   - `changelog.md` is added to `DOC_TEMPLATES`, so `config` names it.
   - Test `test_a_changelog_template_without_notes_is_breaking`: drift reports a host override that lacks `{{notes}}` under `breaking`.
   - The existing readiness test, which compares the listed templates with `templates/*.md` (`tests/test_defaults.py`), still passes.
5. **R5. Release reads `__version__`.** `VERSION_RE` reads `__version__ = "1.2.0"` as a version line, and `write_version` changes only its value.
   - Test `test_python_s_dunder_version_is_a_version_line`: a `pkg/__init__.py` holding a docstring, `__version__ = "0.4.2"  # bumped by release` and other code is bumped to `0.5.0`, with every other byte unchanged.
   - `target-version = ...` and `my__version__ = ...` are still not version lines. The existing pyproject assertion still holds, and a new case asserts `my__version__`.
6. **R6. The missing-tag hint points at adoption when that is later.** When no tag exists for the current version, the hint names the later of two commits: the last commit to touch `release.version_files`, and the oldest commit that added `.sdlc/config.toml`. "Later" means the version commit is a strict ancestor of the adoption commit. When there is no version commit, it names the adoption commit. When there is neither, it keeps today's `<the commit that released it>`.
   - The existing `test_a_missing_tag_names_the_command_that_would_make_it` still passes: one commit holds both, so the hint names it.
   - Test `test_a_missing_tag_points_at_adoption_when_it_came_after_the_version`: version files committed first, `.sdlc/config.toml` added in a later commit. The hint names the second commit.
   - Test `test_a_version_bump_after_adoption_is_still_the_hint`: the version is bumped after adoption, and the hint names the bump.
7. **R7. Publish pushes the notes ref after the command, and a refusal doesn't fail it.** After the publish command succeeds and records `published`, `cmd_publish` pushes `refs/notes/sdlc` to `release.remote` through `_push()`, never forced.
   - On success the report's `done` gains `push notes`.
   - When the remote refuses, publish still exits 0, and the report carries `notes_push_failed` with git's words.
   - On a rerun the notes push is skipped when the remote already holds the local ref (`_pushed()`).
   - Test `test_publish_pushes_the_published_note`: the bare remote's `refs/notes/sdlc` resolves to the local one after publish.
   - Test `test_a_refused_notes_push_does_not_fail_publish`: a `pre-receive` hook on the bare remote rejects `refs/notes/*`. The result is exit 0, `notes_push_failed` set, and `publish command` in `done`.
8. **R8. A second clone skips an upload already made.** In the run after approval, before its steps, publish fetches the remote's `refs/notes/sdlc`, not forced, into a mirror ref `refs/notes/sdlc-remote`. It merges that into the local `refs/notes/sdlc` with `git notes merge -s cat_sort_uniq`, so `published()` sees a note another clone pushed.
   - Test `test_a_second_clone_skips_the_upload_another_made`: clone A releases and publishes with a command that appends to a counter file outside both clones. Clone B, freshly cloned with tags, runs `cmd_publish`. The counter is unchanged, and B's `skipped` holds `publish command (already done)`.
   - A failed fetch (no such ref on the remote is not a failure) is reported as `notes_fetch_failed` and publish goes on with the local notes alone, as today.
9. **R9. Without a publish command, no notes move.** With no `release.publish`, publish neither fetches nor pushes notes. Test `test_publish_without_a_command_moves_no_notes`: the remote has no `refs/notes/sdlc` afterwards, and the local repo has no `refs/notes/sdlc-remote`.
10. **R10. Only `cmd_publish` fetches notes.** The fetch lives in one function called only by `cmd_publish`. It runs with `GIT_TERMINAL_PROMPT=0` and stdin closed, as `_push()` does. `tests/test_skills.py::test_only_the_named_steps_push` still passes unchanged: one `git push` call site, in `_push()`, whose callers are still `cmd_publish`, `cmd_close` and `cmd_release`.
11. **R11. `docs/REFERENCE.md` says what changed.** Under *Releases* and in the config example's `changelog` comment, it says:
    - the marker and where the section goes;
    - the `changelog.md` template, its placeholders and that a host can override it;
    - that `__version__ = "x"` is a version line;
    - where the missing-tag hint points;
    - that publish pushes `refs/notes/sdlc` after the command, and reads another clone's from the remote;
    - that the tag message holds the notes, so `release.publish = "gh release create {tag} --notes-from-tag"` uses them;
    - that `release.prepare` can show what a push will upload (`git lfs push --dry-run {remote} {tag}`-style; plan settles the exact line);
    - that a tag outside `release.tag`'s pattern is outside the loop: never a boundary, never counted.

    Test `test_reference_names_the_changelog_marker_and_the_notes_push`, in `tests/test_release.py`, greps REFERENCE.md for `<!-- sdlc:releases -->`, `--notes-from-tag` and `refs/notes/sdlc`, and fails if the docs lose them.
12. **R12. The publish skill knows the new step.** `skills/publish/SKILL.md` names the `push notes` step in Step 3, and in Step 4 says that `notes_push_failed` means the next clone may run the upload again. No new command, no new `Bash(...)` rule, and the WAIT's question is unchanged. `tests/test_skills.py` passes unchanged.

## Design

**Changelog.**
- `with_changelog(text, section)` takes the rendered section instead of building it.
- A new `changelog_section(home, version, notes, today)` reads `template_path(home, "changelog.md")`, fills the three placeholders with `str.replace` (as `render_issue`'s `fill()` does), and normalises the section to end in exactly one newline.
- In `with_changelog`, a module constant `CHANGELOG_MARKER = "<!-- sdlc:releases -->"` is looked for line by line (`line.strip() == CHANGELOG_MARKER`), keeping line endings by splitting with `keepends=True`.
  - If it is found: the text up to and including the first marker line, a blank line, the section, a blank line if anything follows, then the rest with its leading blank lines stripped.
  - Otherwise: today's code path, unchanged.
- The marker is not read inside fences or specially elsewhere. A changelog that shows the marker in a code block before the real one is the host's to fix, and the docs say to put the marker on a line of its own.
- `templates/changelog.md` holds only the section's text. Like `templates/issue.md`, it is rendered verbatim, so it carries no title, note or frontmatter. It joins `EXCEPTIONS` in `tests/test_defaults.py` with the reason "rendered verbatim into every release's changelog section". Contracts touched covers this.

**Version line.** `VERSION_RE` becomes `^([ \t]*(?:"?version"?|__version__)[ \t]*[:=][ \t]*")([^"\n]+)(".*)$`, with the same groups, so `read_versions` and `write_version` need no change. The key still has to open the line, after whitespace only, so `target-version` and `my__version__` stay out. The comment above it gains the Python form.

**Missing-tag hint.** A new `_adoption_commit(home)` returns the last line of `git log --diff-filter=A --format=%h -- <HOST_DIR>/config.toml`, the oldest add, or None. `git log -1 --reverse` won't do, because `-1` is applied before the reverse. The path is built from `HOST_DIR`, never a literal. In `unreleased()`, where the hint is built:
- `last` is the newest commit to touch the version files, as today, and `adopt` is the adoption commit.
- If `last` and `adopt` are both set, differ, and `git merge-base --is-ancestor last adopt` succeeds, the hint names `adopt`. `_git_err` returns None on exit 0, so that is the test to use. Otherwise it names `last or adopt`.
- With neither commit, the placeholder stays.

The refusal text in `cmd_release` already quotes `u["missing"]["hint"]`, so it needs no change.

**Publish's note.**
- A new `_fetch_notes(home, remote)` runs `git fetch -q <remote> refs/notes/sdlc:refs/notes/sdlc-remote`, without `+`, with `GIT_TERMINAL_PROMPT=0` and stdin closed. It first asks `_remote_sha(home, remote, "refs/notes/sdlc")`. If the remote has no such ref, it does nothing and returns None. Otherwise it returns git's error or None.
- After a successful fetch, `git notes --ref sdlc merge -q -s cat_sort_uniq refs/notes/sdlc-remote` folds the remote's notes in. Both sides' text for one tag is the same word, so `cat_sort_uniq` never conflicts. Merging into a local ref that doesn't exist yet has to create it; plan verifies `git notes merge` does, else it uses `update-ref` for that one case.
- Both run in `cmd_publish` only when not `--check` and `report["command"]` is set, after the refusals and before the step loop. So `published()`, which is unchanged, reads the merged ref.
- After the step loop succeeds, a separate notes step runs, not one of the `steps` tuples, because its failure must not exit 1. When `report["command"]` is set and the local `refs/notes/sdlc` exists, it runs `_push(home, remote, "refs/notes/sdlc")` unless `_pushed()` says the remote already holds it.
  - Success appends `push notes` to `done`. A skip appends `push notes (already done)` to `skipped`.
  - An error sets `report["notes_push_failed"]`.
- `--check` adds `push notes` to `will_run` when the command will run. The skill's question doesn't name it: it is bookkeeping under the same approval.

**Release doesn't push notes** (open question 2). Release writes no `refs/notes/sdlc` note, only `sdlc-prepared`, so it has nothing of this ref to push. `sdlc-prepared` stays local: what `prepare` built is local too.

## Contracts touched

- **Only the named steps push (`test_only_the_named_steps_push`).** The notes push is one more `_push()` call inside `cmd_publish`, behind publish's approval, never forced. The test counts call sites of `git push` and the callers of `_push`, and neither changes. The new `git fetch` isn't a push. It has no `+`, so it can't overwrite anything, and it writes only `refs/notes/sdlc-remote`, a mirror no other code reads.
- **Writes before a WAIT.** The fetch and the notes merge run only after the yes, never in `--check`. So publish's read before the question stays read-only, and AGENTS.md's list of four exceptions is unchanged. Open question A below covers the cost: the question may offer a command a second clone will then skip.
- **"One shape for the shipped docs" (`tests/test_defaults.py`). THIS CHANGES A STATED INVARIANT.** AGENTS.md says `templates/issue.md` is *the one exception* to the shipped-doc shape. `templates/changelog.md` would be a second, for the same reason: its text is rendered verbatim into a host's file, so a title or `>` note would land in every changelog section.
  - The intent asks for the section heading to be a template in `templates/`, and that template can't take the shape. The spec therefore proposes editing AGENTS.md's bullet to name both exceptions, and adding the entry to `EXCEPTIONS`.
  - This is the person's call: see open question B, and *Alternatives rejected* for the config-key route that avoids it.
- **`TEMPLATE_READS` / drift's `breaking`.** The new template is registered with the placeholders the script needs (R4). No host has an override yet, so nothing becomes breaking for an existing host, and no `RETIRED_KEYS` entry is needed.
- **`stamp_shipped`'s rule (edit in place, no round trip).**
  - Version files: `write_version` stays a single regex substitution, and R5 pins byte equality.
  - The changelog: every byte outside the inserted section is kept, and R1 pins it.
- **`_release_refusals()` / the release commit sweeping tracked files.** This is untouched. The changelog step still writes only `release.changelog`.
- **Windows.**
  - The new subprocess calls go through `_git`/`_git_err`, or name `encoding="utf-8"`.
  - The template is read with `encoding="utf-8"`, and the changelog is still written with `write_bytes`.
  - The marker split keeps CRLF lines intact, and a CRLF case is added to R2's test.
  - No platform module is imported.
- **The base branch.** No new git call names `main`. The notes ref and the mirror ref are fixed names that aren't branches.
- **Nothing local.** Test data uses `demo`, `reopen-drafts` and `export-totals`, as the file does now.
- **`.sdlc/setup.json`.** It records a hash of every `templates/*.md`. This change runs `sdlc.py record` from its own checkout if `sdlc.py drift` reports the new template, so the gate stays green.

## Alternatives rejected

- **A config key for the heading (`release.changelog_heading = "## {version} — {date}"`).**
  - For: it would avoid a second template exception and fit `release.tag`'s `{version}` style.
  - Against: the intent names a template, a key doesn't give a host the section's whole shape (where notes go, any trailing link line), and `format()` raises on stray braces the way `_host_command` has to guard against.
  - It stays the fallback if the person declines the invariant edit (question B).
- **Detecting Keep a Changelog's `## [Unreleased]` and inserting under it.** That means guessing a layout. The marker is the host saying where, and costs one line.
- **Forced fetch (`+refs/notes/sdlc:…`) or fetching straight into `refs/notes/sdlc`.**
  - Forced is unnecessary, since the remote's notes only fast-forward, and pushes are never forced.
  - Fetching into the live ref is refused whenever local notes hold something the remote doesn't, such as an earlier refused push. The mirror plus `cat_sort_uniq` merge covers both cases in one path.
- **Reading the remote's notes with `ls-remote` alone.** `ls-remote` gives a sha, not the note's text for a tag, so the objects have to be fetched.
- **Having release push `refs/notes/sdlc` when `git.push` names it.** Release writes nothing on that ref, so there is nothing to push.
- **Pushing `refs/notes/sdlc-prepared` too.** It's out of the intent's scope, and what it describes is a local build.
- **Using `.sdlc/setup.json`'s first record as the adoption point.** setup.json is rewritten on every `record` and holds no date. Its first commit could be found, but `.sdlc/config.toml` is what makes a repo set up: `cmd_record` refuses without it, and every command reads it. So its first add is the adoption commit.
- **Single-quoted `__version__ = '1.2.0'`.** The intent asks for the double-quoted form. A host with single quotes gets a clear "0 version lines" problem rather than a misread, so this can wait for a host that asks.

## Verification

```bash
uv run --group dev pytest -q tests/test_release.py tests/test_push.py tests/test_defaults.py tests/test_skills.py
uv run --quiet --script scripts/sdlc.py drift      # from this worktree: reports nothing
./check.sh
```

What healthy output looks like:
- The named tests pass, including every new test listed in R1–R12, and so do the existing release, push, defaults and skills tests.
- `drift` reports nothing. If it lists `templates/changelog.md`, run `uv run --quiet --script scripts/sdlc.py record` and rerun.
- `./check.sh` ends green: `ruff check`, `ruff format --check`, `pytest -n auto` with no failures, and `claude plugin validate --strict` passing.
- A manual check, if wanted: in a scratch repo with a bare remote, publish from one clone, then publish from a fresh clone. The second run's report lists `publish command (already done)` under `skipped`.

