---
id: 034
slug: host-attribution-off
kind: spec
created: 2026-10-31
updated: 2026-10-31
---

# 034 — Ask a host whether its commits name the agent, and apply its answer · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `CONFIG_KEYS["git"]` gains `attribution`, default `None`, in `BOOL_KEYS`. `config`
   prints `git.attribution` as `null`, `true` or `false`, and a non-bool value warns
   `git.attribution must be true or false`. Tests: each of the three values, plus the warning.
2. **R2.** `ATTRIBUTION_OFF = {"commit": "", "pr": "", "sessionUrl": false}` is the one value the
   plugin writes. A test pins that it's an object, never `false`.
3. **R3.** `readiness` reports an `attribution` item, never required, with the object to merge when
   it's needed:
   - **unset:** `missing`, detail "not chosen: setup asks whether commits and pull requests name
     the agent";
   - **`true`:** `ok`, "on: the harness's own";
   - **`false`, and `.claude/settings.json` holds an `attribution` equal to `ATTRIBUTION_OFF`:**
     `ok`;
   - **`false`, and the settings lack it or hold another value:** `missing`, with
     `merge: ATTRIBUTION_OFF`;
   - **`false`, and `.claude/settings.local.json` sets a different `attribution`:** `warn`, naming
     the file, since it overrides the shared one.

   Tests for each case.
4. **R4.** `cmd_record` writes `"attribution": true` in `setup.json` when the key is `false` and
   the settings hold `ATTRIBUTION_OFF`. Otherwise it writes `false`.
5. **R5.** `cmd_uninstall` removes `.claude/settings.json`'s `attribution` only when the record
   says setup wrote it and the value still equals `ATTRIBUTION_OFF`. Its plan lists that, and the
   settings file is removed when it's then empty, as today. Tests: removed when recorded; left
   alone when not recorded, or when changed.
6. **R6.** `skills/setup/SKILL.md` asks in Step 2 while `git.attribution` is unset, on a first
   setup or a later one: "Should Claude's attribution appear in this repo's commits and pull
   requests? (on / off)", with no proposed answer.
   - Step 3 drafts the answer as `[git] attribution = true|false` in `.sdlc/config.toml`.
   - For `off`, it also drafts readiness's `merge` object into `.claude/settings.json`, keeping
     everything there.
   - Step 6 says what was decided.

   `READS_CONFIG["sdlc:setup"]` gains `git.attribution`.
7. **R7.** `skills/ship/SKILL.md` Step 6: when `git.attribution` is `false`, the commit message
   carries no `Co-Authored-By:` line naming an agent, and no "Generated with" line, whatever the
   harness suggests. `READS_CONFIG["sdlc:ship"]` gains `git.attribution`. Test: `test_skills.py`
   finds the sentence.
8. **R8.** `docs/REFERENCE.md` documents `[git] attribution` (unset, `true`, `false`, what each
   writes, and the object form and why). README's setup section names the question. AGENTS.md's
   setup's-record paragraph names the record's `attribution` and what uninstall takes.
9. **R9.** This repo answers too: `[git] attribution = false` in `.sdlc/config.toml`, so readiness
   reads `ok` for its existing settings and `sdlc.py record` records it. Drift stays clean.
10. **R10.** `./check.sh` passes.

## Design

**Mechanism in the script, the write in the skill.** `sdlc.py` decides the facts: the key, the
object, readiness's verdict and `merge` value, the record and the uninstall plan. The setup skill
does the edit behind its one WAIT, the same way it merges `permissions.missing` today. No new
subcommand and no new `allowed-tools` rule.

**Unset is a real state.** It isn't "on by default". Nothing is written, readiness says setup will
ask, and setup asks until there's an answer. `true` is an answer too, so a host that wants the
line is asked once and never again.

**Comparison is by value.** A host whose hand-written object equals `ATTRIBUTION_OFF`, like
faeldon-website, reads `ok` with nothing to write. Record marks it as setup's only once the key
says `false`, so uninstall then takes it out. That's the right reading, since the host chose
`false` through setup.

**`settings.local.json`** is only read, never written: it's each person's own file. When it
overrides the answer, readiness warns and ship's prose still holds the line.

## Contracts touched

- **Config keys (`CONFIG_KEYS`, drift's `new`):** a new key, reported once as `new` by drift on
  hosts recorded before it. That's no `RETIRED_KEYS` entry and no shim.
- **What setup writes into a host:** one more merge into the settings file setup already writes.
  It never drops or reorders existing keys.
- **Uninstall removes only setup's:** kept by R5's two conditions.
- **Narrow `allowed-tools`:** unchanged, since the write is the skill's `Edit`.
- **Skills read config keys they name (`READS_CONFIG`):** setup and ship gain `git.attribution`.
- **"Nothing public names the agent"** stays this repo's own rule. R9 makes this repo state it
  through the key as well.

## Alternatives rejected

- **`attribution = false` as the default:** the owner chose to ask. A default would decide for
  hosts that never answer.
- **A `sdlc.py` write command for settings:** that adds a command, a rule and an approval path for
  one JSON merge the skill already does for the allow rules.
- **Factory build prose:** the factory never commits, so nothing there carries the line.
- **Drift for a settings mismatch:** drift reports plugin defaults against the host; a settings
  file disagreeing with the host's own answer is readiness's kind of fact.
- **`"attribution": false`:** Claude Code before v2.1.281 rejects it, and with it the whole
  settings file.

## Verification

- `./check.sh` green.
- `sdlc.py config` shows `git.attribution: false` here.
- `sdlc.py readiness` shows `attribution: ok`.
- `sdlc.py drift` reports nothing after `sdlc.py record`.
- In a scratch host: readiness says `missing` (not chosen); set `false`, and readiness gives
  `merge`; merge it, and readiness says `ok`; record, then uninstall `--check` lists the
  attribution removal.
