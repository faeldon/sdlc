---
id: 003
slug: test-lifetimes
tier: 2
impact: minor
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea: "Enforce test lifetimes: shim deadlines, acceptance checks in the change folder"
depends_on: [002]
serves: none
---

# 003 — Enforce shim deadlines, and sweep acceptance-only tests

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The test-triage change wrote the triage rule into Stage 4 and the review: a compatibility test
lives exactly as long as its shim, and the shim names the version that removes it. That rule is
only prose. Nothing reads a shim's removal version, so the plugin could ship an overdue shim, and
the reviewer would only catch it by remembering it. A host following the same Stage 4 has the same
gap and nowhere to write its shims down. Separately, `tests/` holds roughly 7,000 lines written
before the triage rule existed. Some of those tests can presumably fail only on a deliberate
revert, such as checking that a file moved or a key was renamed. They run on every gate and
protect nothing.

## Outcome

- The plugin's own shims are listed in one registry, each with a `remove_in` version. One test in
  this repo's gate fails once a shim's `remove_in` is at or below the version in
  `.claude-plugin/plugin.json`, so `/sdlc:release` can't produce a version that still carries an
  overdue shim.
- A host can list its own deprecations the same way. Its `/sdlc:status` and `/sdlc:release` show
  each one that's due, compared against the version its `release.version_files` hold.
- With no registry, a host sees nothing new, and an unparseable entry is reported as a problem
  rather than crashing.
- After the sweep, each test in `tests/` that only a revert could fail has either been removed,
  with its check recorded in this change's `notes.md`, or kept with a one-line reason.
- `./check.sh` passes.

## Affected

- **Area:** `scripts/sdlc.py` (config resolution, `status`, `release`/`unreleased()`), the
  plugin's test suite, and the host-facing contract.
- **Files & components:**
  - `scripts/sdlc.py` (`load_config()`, `unreleased()`, `cmd_release`, the `status` report)
  - `.sdlc/config.toml` and `defaults/` if a key or file is added
  - `docs/REFERENCE.md`
  - `tests/test_release.py`, `tests/test_config_resolution.py` and a new registry test
  - the files the sweep touches across `tests/`
  - `defaults/SDLC.md` and `.sdlc/SDLC.md`, Stage 4's compatibility line, if it should point at
    the registry
- **Downstream:**
  - Every host on a new release: `status` and `release` output changes for those that list
    deprecations.
  - `/sdlc:release` in this repo, which the overdue test can now block.
  - The skills that read `status`/`release` JSON.
- **Contracts:**
  - Mechanism vs. policy: host-specific data comes only through `sdlc.py config`, so a host's
    registry location is resolved once in `load_config()`.
  - Frontmatter and versions are read as text, never through YAML: `1.10` must not compare as
    `1.1`.
  - The release boundary is the tag for the version `release.version_files` hold now.
  - The adoption test (`tests/test_adoption.py`): a bare host with no registry must still run
    `new` → `close`.

## Constraints

- **Language-agnostic:** a host may not use pytest. The host-facing part can't depend on a
  `compat` marker or any test runner; that belongs to the plugin's own suite.
- **Never refuses on a missing registry:** absent means off, the way `docs.project` and
  `docs.product` are off while absent.
- **Reports, never edits:** `status` and `release` say what's due and don't remove anything.
  Whether a due shim blocks a host's release is the host's call, unless decided otherwise in the
  spec.
- **Versions compare as versions:** `1.10.0` is greater than `1.9.0`.
- **The sweep removes only true acceptance checks.** A test any later change could break by
  accident stays. When in doubt, it stays.
- **Item 2 of the seed is out of scope:** acceptance checks living in `work/NNN-slug/`, run by
  ship. It stays a seed.

## Open questions

- ~~Where does a host's registry live?~~ Resolved: a TOML file, `release.deprecations` (default
  `.sdlc/deprecations.toml`), off while absent. No hook.
- ~~Should the plugin's own registry use that same file format in this repo?~~ Resolved: yes,
  this repo's `.sdlc/deprecations.toml`, read by a gate test through the same parser.
- ~~What does an entry hold?~~ Resolved: `name`, `remove_in`, `where`, and an optional `test`;
  the `test` field replaces the seed's `compat` marker.
- ~~Should an overdue shim make `/sdlc:release` refuse, or only warn?~~ Resolved: release refuses
  for any shim due by the version it cuts, in every host; status warns; this repo's gate also fails
  on one already overdue.
- ~~How is the current version read with no `release.version_files`?~~ Resolved: it isn't;
  shims are listed as unversioned and nothing is compared.
- ~~Where does a removed test's record go?~~ Resolved: one list in this change's `notes.md`, one
  line per removal with what it checked.
