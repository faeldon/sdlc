---
id: 034
slug: host-attribution-off
kind: plan
created: 2026-10-31
updated: 2026-10-31
---

# 034 — Ask a host whether its commits name the agent, and apply its answer · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `[git] attribution` in `CONFIG_KEYS` and `BOOL_KEYS`; `ATTRIBUTION_OFF`,
  `LOCAL_SETTINGS` and `_settings_attribution()` beside `SETTINGS`; `attribution_status()` beside
  `permissions_status()`, its readiness item and top-level `attribution` part; record's
  `attribution`; uninstall's settings edit takes the object when recorded and unchanged.
- `skills/setup/SKILL.md`: the question in Step 2, the key and the merge in Step 3, the answer in
  Step 6.
- `skills/ship/SKILL.md`: Step 6's sentence on attribution when the key is `false`.
- `docs/REFERENCE.md`, `README.md`, `AGENTS.md`: the key, what each answer writes, and what
  uninstall takes.
- `.sdlc/config.toml` and `.sdlc/setup.json`: this repo answers `false`, and records it.
- `tests/test_config_resolution.py`, `tests/test_readiness.py`, `tests/test_setup_lifecycle.py`,
  `tests/test_skills.py`.

## Work order

1. **Key and constant** (R1, R2), with their config tests.
2. **Readiness** (R3), with its five cases.
3. **Record and uninstall** (R4, R5), with lifecycle tests.
4. **Skills** (R6, R7) and `READS_CONFIG`.
5. **Docs and this repo's answer** (R8, R9): `.sdlc/config.toml`, then `sdlc.py record`.
6. `./check.sh` (R10); `drift` clean.

## Tests

- **R1:** `git.attribution` is `null` with no key, reads `true` and `false`, and a string warns
  `git.attribution must be true or false`.
- **R2:** `ATTRIBUTION_OFF` is a dict, never a bool.
- **R3:** readiness's `attribution` item for unset (`missing`, not chosen), `true` (`ok`), `false`
  with a matching object (`ok`, no merge), `false` with none or another value (`missing`, merge
  given), `false` overridden by `.claude/settings.local.json` (`warn`, naming it).
- **R4:** record writes `attribution: true` only when the key is `false` and the settings match.
- **R5:** uninstall removes the object when recorded and unchanged, and removes a settings file
  setup created once it's empty; it leaves an unrecorded or changed object, listed under `left`.
- **R6, R7:** `test_skills.py` finds setup's question and ship's sentence, and their
  `READS_CONFIG` holds `git.attribution`.
- **R9, R10:** `./check.sh`; `sdlc.py drift` reports nothing after `sdlc.py record`.
- **Manual:** in a scratch host, readiness goes `missing` (not chosen) → `missing` with `merge`
  once `false` is set → `ok` once the object is written; `uninstall --check` then lists its
  removal.

## Rollback

`git revert <sha>` of the ship commit removes the key, readiness's item, record's field and the
skills' prose. It doesn't cover a host that set the key or had setup write the object meanwhile:
the reverted plugin warns `unknown key git.attribution` until the line is removed from
`.sdlc/config.toml`, and the object stays in `.claude/settings.json`, harmless, until removed by
hand.
