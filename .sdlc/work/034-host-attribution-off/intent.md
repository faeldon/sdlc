---
id: 034
slug: host-attribution-off
tier: 2
impact: minor
stage: shipped
created: 2026-10-31
updated: 2026-10-31
shipped: 2026-10-31
idea: 2026-10-25-21
depends_on:
serves: [O1]
---

# 034 — Ask a host whether its commits name the agent, and apply its answer

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The commits `sdlc.py` makes itself (`Close`, `Drop`, `Release`, `Retrospective`) carry only the
`Sdlc-*` trailers. But the commits a session makes for a skill take the harness's
`Co-Authored-By:` line, and a pull request gets its "Generated with Claude Code" footer. That
covers ship's commit and the factory's build.

This repo keeps them out in two ways: AGENTS.md's "Nothing public names the agent" rule, and an
`attribution` object in its own committed `.claude/settings.json`. The plugin passes neither to a
host.

On 2026-10-29 a fresh install in faeldon-website kept attribution on, against what its owner
expected. It needed a hand edit to that repo's `.claude/settings.json`. `/sdlc:setup` already
writes into that same file, the read-only allow rules, but nothing else, and never asks.

## Outcome

- A new config key, `[git] attribution`, is unset by default. `sdlc.py config` reports it as
  `null` until the host answers, and setup leaves `.claude/settings.json` alone while it's unset.
- **Setup asks.** On a first setup, and on any later setup while the key is unset,
  `/sdlc:setup` asks whether Claude's attribution should appear in the host's commits and pull
  requests: on or off, with no proposed answer. The answer is written to `.sdlc/config.toml`.
- **Off:** setup writes `"attribution": {"commit": "", "pr": "", "sessionUrl": false}` into
  `.claude/settings.json` beside the allow rules. That's the object form, never
  `"attribution": false`, which Claude Code before v2.1.281 rejects, skipping the whole settings
  file. **On:** nothing is written to settings.
- **Record, drift and uninstall track it.** Record notes that setup wrote the object. Drift
  reports a host whose settings no longer match `attribution = false`. Uninstall removes the
  object only when setup wrote it.
- **The skill that commits says it too.** Ship tells the session to leave attribution off when
  the key is false, since `.claude/settings.local.json` and managed settings can override the
  project file. (The factory's build never commits.)
- **Moves O1:** a new host decides at setup whether its commits name the agent, and its first
  closed change follows that decision with no settings file edited by hand.

## Affected

- **Area:** config resolution, readiness, record and uninstall in `scripts/sdlc.py`; the setup
  and ship skills.
- **Files & components:**
  - `scripts/sdlc.py`: `CONFIG_KEYS`, `load_config()`, the readiness `permissions` item and
    `ALLOW_RULES` writer, `cmd_record`, `drift()`, `cmd_uninstall`;
  - `skills/setup/SKILL.md`, `skills/ship/SKILL.md`;
  - `docs/REFERENCE.md` (the `[git]` keys), README.md, AGENTS.md;
  - tests in `test_config_resolution.py`, `test_readiness.py`, `test_setup_lifecycle.py` and
    `test_skills.py`.
- **Downstream:**
  - Every host on its next `/sdlc:setup`, which asks while the key is unset.
  - Claude Code itself, which reads `.claude/settings.json`. A malformed or rejected setting drops
    every allow rule with it.
  - faeldon-website already has the object written by hand. On its next setup it gets asked, and
    answering off only records the key: its settings already match.
- **Contracts:**
  - **A config key added:** `CONFIG_KEYS` and drift's `new` key report.
  - **What setup writes into a host:** always Tier 2.
  - **A skill's prose and `allowed-tools`:** setup and ship gain prose; no new rule.
  - **Uninstall removes only setup's.**
  - **"Nothing public names the agent"** stays this repo's own rule; this change lets a host
    choose the same.

## Constraints

- Setup never drops or reorders a host's existing settings. It merges, as it does for the allow
  rules.
- The written value must be one every supported Claude Code version accepts.
- Unset or `true` means nothing is written, and drift doesn't nag. Only `false` has anything to
  check.
- The commits `sdlc.py` writes keep carrying `Sdlc-*` trailers only, whatever the key says.

## Open questions

- ~~Does the text the plugin writes into issues and their comments follow the same key?~~
  Resolved: nothing to do. The issue template, the trackers and `sdlc.py` write no agent line;
  only the harness adds one, in a session's commits and pull requests.
- ~~Where does setup's merge into `settings.json` live?~~ Resolved: the setup skill's own `Edit`,
  as for the allow rules; readiness reports the object to merge (spec R3, R6).
- ~~When a host's settings hold a different `attribution`, or `settings.local.json` overrides it,
  does drift report it, or readiness?~~ Resolved: readiness, beside `permissions` (spec R3).
