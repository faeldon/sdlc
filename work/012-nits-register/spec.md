---
id: 012
slug: nits-register
kind: spec
created: 2026-10-25
updated: 2026-10-25
---

# 012 — A ship's unfixed nits are kept, weighed and paid down by theme · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. `templates/nits.md` gives the shape of `work/nits.md`: a `# Nits` title, a `>` note, then
   one `## <id> [<theme>] <title>` entry per nit, with lines `- **raised:** YYYY-MM-DD by NNN-slug
   (<pass>)`, `- **paths:** a, b`, `- **cost:** S|M  **value:** med|low`, then a line or two of
   prose. `tests/test_defaults.py`'s shape rules pass on it.
2. R2. `sdlc.py nits` (read-only) prints JSON: every open nit with its fields and `age_days`, and
   `problems` (a malformed entry, a duplicate id, an unknown cost or value), parsed as text, never
   YAML. `--touching <path>…` keeps the nits whose paths overlap; `--change <NNN>` uses that
   change's diff against `main` as the paths. No `work/nits.md`: an empty list, exit 0.
3. R3. `check --strict` reports the register's problems, so a malformed register fails the gate.
4. R4. Ship captures: at Step 4 each nit not fixed now is shown with its proposed theme, paths, cost
   and value under the rubric. L cost becomes a `work/ideas.md` seed instead. At Step 6 the approved
   ones are appended to `work/nits.md` with ids `<NNN>-<n>`. The WAIT question names it ("…and its
   nits added to work/nits.md…") only when there are some.
5. R5. Ship retires: Step 0 runs `sdlc.py nits --change <NNN>`; Step 4 proposes retiring each one
   listed that the diff fixed or made moot, with a one-line reason; Step 6 deletes the approved ones
   from `work/nits.md`, and the commit message gets a `Retired nits:` paragraph, one line per id and
   reason.
6. R6. Intent (Tier 1) and spec (Tier 2) run `sdlc.py nits` and list open nits matching the
   change's paths or theme, offering the S-cost ones to take in. Taken nits are named in the
   intent's Approach or the spec's Requirements; nothing is retired before ship (R5 does that). With
   no open nits, nothing is shown.
7. R7. `retro` gains `nits`: the open count, and per theme the count, oldest `raised` and oldest
   age. The retro skill applies the process doc's threshold and may propose a paydown seed in
   `work/ideas.md`, which its commit already allows. It never edits `work/nits.md`.
8. R8. The rubric and themes are in `defaults/SDLC.md`, mirrored in `.sdlc/SDLC.md`, under the
   review and ship text, and `scripts/sdlc.py record` is run after.
9. R9. Release and publish never read or write `work/nits.md`: a test asserts neither skill nor
   `cmd_release`/`cmd_publish` names it.
10. R10. `Sdlc-Findings` is unchanged: same keys, same meaning; `metrics_summary`'s findings counts
    are unchanged and existing tests pass unedited.
11. R11. A host with no unfixed nit sees nothing new: no file is created, and `status`, `check` and
    `retro` output is unchanged apart from an empty `nits`.
12. R12. The nine open nits are imported into this change's `work/nits.md`, each with its raising
    change, a raised date from that change's `Close` commit, theme, paths, cost and value; the seed
    "Carry a ship's unfixed nits forward" leaves `work/ideas.md`.
13. R13. Every skill that runs `sdlc.py nits` has a `Bash(...)` rule for it and names the config it
    reads (`tests/test_skills.py`). `nits` stays out of `READ_ONLY` and `ALLOW_RULES`, so existing
    hosts get no new "missing" permission nudge.

## Design

- **Rubric.** Two axes: cost (S: one sitting, a few lines; M: a test or several files; L: a design
  call) and value (med: a user or host could hit it; low: only a reader of the code notices). High
  value isn't a nit: it is an Important finding or a seed. L cost goes to a seed, not the register.
  S with med is the one to offer for "fix a finding first" at ship. The rest go to the register.
- **Themes.** Free text, with a default list in the process doc (`docs`, `refactor`,
  `robustness`, `tests`, `style`), which a host owns. Feature categories are deferred; a nit's
  paths stand in for them.
- **Retro threshold.** Prose in the process doc, so it is policy, not mechanism: by default a theme
  with 5 or more open nits, or any nit older than 60 days. `sdlc.py` reports counts and ages per
  theme; the retro skill applies the rule.
- **Mechanism vs judgment.** `sdlc.py` parses, filters (`--touching`, `--change`), ages, audits in
  `check` and counts for `retro`. The skills judge (rubric, theme, prose) and write entries with
  `Edit`/`Write`, as ship already does for `work/ideas.md`. Nothing in `sdlc.py` writes nit prose.
- **Ids by change.** `<NNN>-<n>` comes from the raising change, so ids are unique across parallel
  branches without a lock or counter. Matched as text, `names_change()`-style, never by prefix.
- **Where it is.** One `work/nits.md`, one `## ` entry per nit, like `work/ideas.md`. Ship writes
  it from `templates/nits.md` the first time it needs to; setup doesn't create it.
- **Pickup.** Plan mode isn't a skill, so intent (Tier 1) and spec (Tier 2) carry it.
- **Ship never fixes a nit itself.** It surfaces findings; "fix a finding first" is already the
  person's answer at its WAIT, and the rubric only says which nits to offer for that.
- **A change's paths.** `--change` reuses the diff `context` already computes against `main`'s
  merge-base.
- **Parsing.** A `NIT_RE` for the heading; bullet leads read like `doc_units()`' `- **lead**`
  bullets; dates through `date.fromisoformat`, a problem on failure, like `_age_days`.
- **Retro.** `nits` beside `ideas` in `retro()`'s return; `cmd_retro_commit`'s allowed paths are
  unchanged.
- **Conflicts.** Two branches appending to `work/nits.md` can conflict at `base`'s rebase, which
  refuses, as it does for `work/ideas.md` today. Accepted: the person resolves it and reruns ship.

## Contracts touched

- **A skill's WAIT or `allowed-tools`** (always Tier 2): ship's WAIT gains the register write when
  there are nits; ship, intent, spec and retro gain a `nits` rule. Everything that runs without
  asking is read-only.
- **What `sdlc.py` reads or writes in a host:** it reads a new file. Only skills write it, behind
  ship's WAIT.
- **One shape for shipped docs:** `templates/nits.md` follows it (R1).
- **Process docs track the defaults:** the rubric goes into both, and `record` runs (R8).
- **Metrics trailers are extended, never redefined:** no trailer changes (R10).
- **Frontmatter and text are never parsed as YAML:** R2.
- **Only publish pushes:** untouched.
- **Nothing local:** imported nits cite this repo's own changes only.

## Alternatives rejected

- **A seed per nit:** buries ideas under debt that moves no outcome, which the originator ruled out.
- **A counter for nit ids:** the `last-id` machinery for what a change-scoped id gives free.
- **Thresholds as config keys:** policy belongs in the host's process doc; a key adds drift entries
  and `RETIRED_KEYS` care for no gain.
- **A file per nit:** more files for git to churn; `ideas.md` already proved the one-list shape.
- **A release or publish pass:** ruled out by the originator; the release cycle is for features.
- **Feature categories:** no breakdown of features exists to name them against; paths stand in.
- **`nits` in `READ_ONLY`:** every set-up host would be nudged about a missing rule; the skills'
  own `allowed-tools` cover it.
- **Several changes:** the register's shape is what every stage reads, so a split ships a register
  nothing pays down. Plan mode may still split it if it proves too big.

## Verification

- `./check.sh` passes, with new tests: `tests/test_sdlc.py` (R2, R3, R7, R11, R12),
  `tests/test_skills.py` (R4–R6, R9, R13), `tests/test_defaults.py` (R1, R8).
- `uv run --quiet --script scripts/sdlc.py nits` lists nine entries, no problems.
- `… nits --change 012` lists those whose paths this diff touches.
- `uv run --quiet --script scripts/sdlc.py retro | jq .nits` shows counts by theme.
- `sdlc.py drift` reports nothing after `record`.
