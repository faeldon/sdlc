---
id: 016
slug: publish-prepare
kind: spec
created: 2026-10-25
updated: 2026-10-25
---

# 016 — A release's upload is prepared before publish's approval, and never prompts after it · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** A new `release.prepare` key, off by default (`None`), takes `{version}` and `{tag}`, each
   shell-quoted as `release.publish`'s are; `sdlc.py config` shows it.
2. **R2.** With `release.prepare` set, `/sdlc:release` runs it as a `prepare` step after
   `after bump` and before `commit`, from the main checkout, within `after_bump`'s timeout.
   Release's report names the command, and `release --check` lists the step as skipped. Test:
   the step order is `version files, …, after bump, prepare, commit, tag`.
3. **R3.** Prepare must leave every tracked file as it found it: any tracked file it changes beyond
   what the release already changed is a refusal naming the file and saying to build into an
   untracked or ignored path; the release's files are restored (`restore()`) and no commit or tag
   is made. Test.
4. **R4.** A prepare that fails (non-zero exit, timeout, can't start) is a refusal with what it
   said, and the files are restored, as `after_bump`'s failures are; release then reruns
   successfully. Test.
5. **R5.** Prepare's stdout (its last 40 lines, at most 4,000 characters) is in release's report as
   `prepared`, and after the tag is written as a git note on the tag under
   `refs/notes/sdlc-prepared`. Publish's own `sdlc` note is untouched (test asserts it).
6. **R6.** `publish` and `publish --check` read that note into the report as `prepared` (`null` when
   there is none, never a refusal). Test for both.
7. **R7.** `release.after_bump`, `release.prepare` and `release.publish` run with `stdin` closed. Test:
   a command that reads stdin fails at once rather than hanging.
8. **R8.** With `release.prepare` unset, release and publish run exactly as today: no `prepare`
   step, `prepared: null`, nothing the skills mention. The existing release and publish tests pass
   unchanged.
9. **R9.** `/sdlc:release`'s Step 1 shows the prepare command and its WAIT names it (`…, run
   <prepare>, and commit…`); `/sdlc:publish`'s Step 1 shows `prepared` (what will be uploaded) and
   its WAIT says so when there is one. Both skills name `release.prepare`, which `READS_CONFIG`
   lists for both; `tests/test_skills.py` passes.
10. **R10.** `docs/REFERENCE.md`'s `[release]` block gains the `prepare` line and says
    `release.publish` runs non-interactively (no terminal, stdin closed, output captured).
    `defaults/SDLC.md`'s release paragraph names the prepare step, the same edit word for word in
    `.sdlc/SDLC.md`, and `.sdlc/setup.json` is re-recorded (`drift` clean).
11. **R11.** "Only publish pushes" holds: prepare never runs inside `cmd_publish`, and
    `test_only_publish_pushes` passes.

## Design

`cmd_release`: a `prepare()` step beside `after_bump()`. It notes the tracked diff before (`git
diff --name-only -z`), runs `report["prepare"]` with `shell=True, cwd=home, capture_output=True,
text=True, stdin=DEVNULL` and `after_bump`'s timeout; on failure, or when the tracked diff now
holds paths beyond the release's own `report["files"]`, it `restore()`s (and `git checkout --`
those paths) and refuses; on success it keeps the tail of stdout as `report["prepared"]`. After
the `tag` step, a `note` step (only when prepare is set) runs `git notes --ref sdlc-prepared add -f
-m <prepared> <tag>`.

`cmd_publish`: the report gains `prepared` from `git notes --ref sdlc-prepared show <tag>` (None on
failure). `run_command()` gains `stdin=DEVNULL`; so does `after_bump()`.

The key's text is formatted with `shlex.quote` exactly as `publish`'s is, so `{version}` and
`{tag}` can never be read as shell syntax.

## Contracts touched

- **Confirm before writing.** Prepare runs only after `/sdlc:release`'s WAIT, which names it.
  Publish adds no write and runs no host code before its WAIT: `--check` only reads a note.
- **Only publish pushes.** Prepare is local; no `push` added outside `cmd_publish`.
- **The release commit takes only what the release meant.** `_release_refusals()` already refuses
  a dirty main checkout, and R3 refuses a prepare that touches tracked files, so the commit holds
  the bump, the changelog and `after_bump`'s files, nothing else.
- **A config key added.** No rename or retirement, so nothing in `RETIRED_KEYS`; setup's record
  picks up the key when it next runs.
- **Skills read `config`.** `READS_CONFIG` gains `release.prepare` for release and publish; neither
  skill's `allowed-tools` changes (the script runs the command).
- **Nothing about a project.** Test data uses neutral commands (`echo`, `touch dist/…`).

## Alternatives rejected

- **Prepare in `publish --check`.** Runs host code with no approval, under a rule allowed because it
  writes nothing.
- **A second WAIT in publish.** Writing skills have exactly one, and one approval covering what was
  shown is the point.
- **Document `after_bump` as the prepare step.** Its tracked changes are committed, the opposite
  rule, and its output never reaches publish's WAIT.
- **Keep prepare's output in publish's `sdlc` note.** `published()` matches that note by substring,
  so prepared text could make publish skip the upload.
- **A list of hooks.** One command chained with `&&` covers every case seen so far.

## Verification

- `uv run --group dev pytest tests/test_release.py tests/test_skills.py tests/test_adoption.py -q`,
  then `./check.sh`: green, `drift` clean.
- Manual: once the build edits `scripts/`, this change's `sdlc.py sync 016` reports
  `"ran": "the change's own code"`: 015's first real check.
