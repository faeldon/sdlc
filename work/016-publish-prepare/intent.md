---
id: 016
slug: publish-prepare
tier: 2
impact: minor
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea: A publish command that needs a confirmation, split into prepare and upload
depends_on:
serves: [O1]
---

# 016 — A release's upload is prepared before publish's approval, and never prompts after it

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc:publish` has one WAIT, before anything leaves. After it, `cmd_publish` pushes `main` and the
tag, then runs the host's `release.publish` with `subprocess.run(..., shell=True,
capture_output=True)`: no terminal, output captured, nothing to answer a prompt. A host whose
upload asks for confirmation ("upload N files? [y/N]") can't use it as `release.publish`: the
command hangs or fails after the push, leaving the release half out (tag pushed, nothing
uploaded). And the WAIT shows only the command's text, never what it will actually send.

A host hit this on 2026-10-25 while writing a spec and worked around it by splitting its own
command into a prepare and an upload step. Nothing in the plugin says `release.publish` must be
non-interactive: `docs/REFERENCE.md` calls it "run by /sdlc:publish after the push".

## Outcome

- A host can name a prepare command (e.g. `release.prepare`, with `{version}` and `{tag}`) that runs
  before publish's WAIT, whose output (the files or package that will be uploaded) is shown in the
  WAIT; the upload runs after it as `release.publish` does today. The one approval covers exactly
  what was shown, and no host command needs to prompt.
- With no prepare command set, `/sdlc:publish` behaves exactly as now.
- `docs/REFERENCE.md` says `release.publish` runs non-interactively (no terminal, output captured),
  so a command that prompts must be given its non-interactive flag or split.
- Tests: a prepare command's output reaches the report the WAIT reads; a failing prepare refuses
  before anything is pushed; no prepare, no change; a rerun after a failed upload doesn't prepare
  twice when it needn't.
- **Moves O1:** a host whose release upload needs a confirming step adopts `/sdlc:publish` as it is,
  without redesigning its own release commands to fit it.

## Affected

- **Area:** releasing: the `release` config and publish (script and skill)
- **Files & components:** `scripts/sdlc.py` (the `release` defaults, `load_config()`,
  `cmd_publish`, possibly `cmd_release` if prepare runs there), `skills/publish/SKILL.md` (Steps
  0–2, possibly `allowed-tools`), `docs/REFERENCE.md` (the `[release]` keys), the release tests,
  `TEMPLATE_READS`/`RETIRED_KEYS` only if a key's meaning moves
- **Downstream:** every host that sets `release.publish`; a new key `/sdlc:setup` records in
  `.sdlc/setup.json`
- **Contracts:** "only publish pushes" (`test_only_publish_pushes`): `"push"` stays inside
  `cmd_publish`. "Confirm before writing": a prepare step that writes anything before publish's
  WAIT would break it. `_release_refusals()` refuses uncommitted tracked changes, so prepare can't
  leave tracked files changed. Retired or renamed keys go in `RETIRED_KEYS`.

## Constraints

- Nothing leaves the machine before the WAIT: prepare may build or check locally, never upload or
  push.
- Prepare leaves no tracked file changed, or the release commit's guarantee (only what the release
  meant) is lost.
- A rerun stays safe: publish already skips what's done (the pushes, a `published` note on the
  tag); prepare must not upload twice or prepare something different from what was approved.
- Hosts that set only `release.publish` see no change.

## Open questions

- ~~Where does prepare run?~~ Resolved: at `/sdlc:release`, after its WAIT, between `after_bump`
  and the commit: approved, and a failure restores so release reruns; publish never prepares, so
  its rerun can't prepare twice.
- ~~Is `release.after_bump` already enough?~~ Resolved: no. Its tracked changes are committed while
  prepare's must leave every tracked file untouched, and its output never reaches publish's WAIT.
- ~~What does the WAIT show from prepare?~~ Resolved: its last 40 lines of stdout (at most 4,000
  characters), kept as a git note on the tag under `sdlc-prepared` and read by `publish --check`.
- ~~One prepare/publish pair, or a list of hooks?~~ Deferred: one command, chained with `&&`
  where a host needs more, until one needs a list.
- ~~Should `release.publish` get a closed stdin?~~ Resolved: yes, and so do `after_bump` and
  `prepare`, so a prompting command fails at once.
