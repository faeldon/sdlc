---
id: 002
slug: setup-lifecycle
kind: spec
created: 2026-10-24
updated: 2026-10-24
---

# 002 — Keep a host's setup current, resettable and removable · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. Manifest.** `sdlc.py record` writes `.sdlc/setup.json` and nothing else: the plugin
   version (from `.claude-plugin/plugin.json`), the full config key set (`section.key`), a hash of
   each *unit* of each default backing a host doc (`docs.process`, `review`, `health`, `product`,
   `project`, where the host file exists), a hash of each plugin template, the paths setup created,
   and whether setup added the `.claude/worktrees/` ignore line. A unit is a heading section
   (levels 2–4) or a `- **…**` bullet. JSON, never YAML. A test pins its shape and that two runs
   with nothing changed write the same file.
2. **R2. Three-way drift per unit.** `sdlc.py drift` (read-only, JSON) compares each host doc with
   its current default (D) using the manifest's base hash (B) and the host text (H), and
   classifies each unit: `added` (in D, not in B or H), `refreshed` (D≠B, H=B), `removed` (in B,
   not in D, H=B), `conflict` (D≠B and H≠B; or removed upstream but edited by the host), `own`
   (only in H), `host-removed` (in B, not in H), `current`. It proposes text only for `added`,
   `refreshed` and `removed`. One test per class, on fixture docs.
3. **R3. No manifest.** Without one, `drift` compares two-way: a unit equal to D is `current`, one
   only in D is `added`, one that differs is `differs` with no proposal, and the output says
   `"base": "none"`. A test covers a host set up from 1.0.0's defaults.
4. **R4. Config drift.** `drift` reports a host key named in `RETIRED_KEYS` as **breaking** with its
   replacement and what to do; any other unknown key as `unknown`; and the keys in `CONFIG_KEYS`
   not in the manifest's key set as `new`, each with its default, `docs/REFERENCE.md` saying what
   it does (the plan's second deviation: a Python comment isn't there at runtime). A test checks
   every `RETIRED_KEYS` entry is absent from `CONFIG_KEYS` and its replacement present.
5. **R5. Template overrides.** For each `.sdlc/templates/<name>`, `drift` reports **breaking** for
   each `TEMPLATE_READS[name]` heading or frontmatter key the override lacks, and `changed` when
   the plugin template's hash differs from the manifest's. A test checks every `TEMPLATE_READS`
   entry exists in the plugin's own template, so the list can't go stale.
6. **R6. Breaking kept apart.** `drift`'s JSON has `breaking` (R4, R5, and the existing
   `project_doc`/`product_items` problems) separate from `refresh` (R2's proposals) and `report`
   (conflict, differs, unknown, new). Setup shows them in that order and drafts no edit for a
   `report` item.
7. **R7. Setup refreshes on rerun.** `/sdlc:setup` on a repo already set up runs `drift` in Step 0
   and, when anything is found, drafts each `refresh` item as a diff to the host doc and lists
   `breaking` and `report` items with their fix, behind the existing single WAIT; after writing it
   runs `record`. A test checks `skills/setup/SKILL.md` runs `drift` and `record`.
8. **R8. Reset.** `/sdlc:setup reset <doc|template|all>` drafts the default back in place of a host
   doc, re-filling its `<` prompts as a first setup would, and shows a diff of every `own` and
   edited unit it would lose. For a template override, reset is `sdlc.py reset <name>`, which
   deletes only `.sdlc/templates/<name>` and refuses any other path. Then `record`. A test checks
   `reset` refuses a path outside `.sdlc/templates/`.
9. **R9. Uninstall refuses while anything is live.** `sdlc.py uninstall --check` lists what it
   would remove, and refuses (exit 1, naming each) while there is an open change, a change
   worktree, a shipped change not yet closed, or an uncommitted change under any path it would
   remove. Tests for each refusal.
10. **R10. Uninstall removes only setup's.** `sdlc.py uninstall` removes `.sdlc/`, the
    `ALLOW_RULES` entries from `.claude/settings.json` (keeping every other key and rule), and the
    `.claude/worktrees/` ignore line only when the manifest says setup added it (no manifest: it is
    listed as left). It never touches `work/`, `AGENTS.md`, `CLAUDE.md`, issues, tags or history;
    it prints the `AGENTS.md`/`CLAUDE.md` lines naming `/sdlc:`, `.sdlc/` or `work/`; it commits
    nothing. A test runs it on a scratch repo and compares the tree with the one before setup,
    apart from `work/` and the context files.
11. **R11. `/sdlc:uninstall` skill.** Runs `config` and `uninstall --check`, has exactly one WAIT
    listing every path, then runs `uninstall`, and ends with the commit command for the human and
    `claude plugin uninstall sdlc@sdlc`. It passes `test_skills.py` (frontmatter, WAIT, exact
    `Bash(...)` rules, `READS_CONFIG`: `archive.target`, `docs.policy`, `docs.context`).
12. **R12. Visible without a rerun.** `readiness` gains a `drift` item: `warn` with counts when
    `breaking` or `refresh` is non-empty, `ok` otherwise, `n/a` with no config. `status` prints one
    `■ Setup:` nudge line, never counted as a problem (`check --strict` is a gate, and an update
    mustn't fail it), when the manifest's version is older than the plugin's, or there is a
    config and no manifest. `drift` joins `READ_ONLY`.
13. **R13. Docs.** `docs/REFERENCE.md` documents `setup.json`, `drift`, `reset` and `uninstall`;
    `README.md`'s *Updating* says to run `/sdlc:setup` after an update; `defaults/SDLC.md` and
    `.sdlc/SDLC.md` name `/sdlc:uninstall` in the skill list. This repo records its own
    `.sdlc/setup.json`.

## Design

**Units and hashing.** One function, `doc_units(text) -> list[(key, text)]`, used by `record` and
`drift`: it splits the body outside code fences into heading sections (level 2–4, key = the
heading line, text up to the next heading) and `- **lead**` bullets (key = the bold lead).
Trailing whitespace is stripped and blank-line runs collapsed before hashing, so a reflow isn't
drift. `test_defaults.py`'s `_headings`/bullet regex become this function, and its two own-copy
tests are rewritten on it, so the plugin's check of its own repo and a host's check are one code
path.

**Manifest** (`.sdlc/setup.json`):
```json
{"version": "1.1.0",
 "config_keys": ["commands.check", "..."],
 "docs": {"process": {"path": ".sdlc/SDLC.md", "default": "SDLC.md",
                      "units": {"## Tiers: the overhead control": "sha256:…"}}},
 "templates": {"intent.md": "sha256:…"},
 "created": [".sdlc/config.toml", ".sdlc/SDLC.md"],
 "gitignore_line": true}
```
`record` takes `--created <path>…` and `--gitignore-line` from setup, which knows what it wrote;
on a rerun it merges `created` with the previous manifest's. Base hashes always come from the
*current* defaults, so after a refresh a unit the host declined to take reads as host-edited,
which is correct: the host chose to diverge.

**Proposals.** For `added`, the anchor is the nearest preceding unit of D that exists in H (else
the end); `refreshed` replaces H's text with D's; `removed` deletes it. `drift` emits `{"doc",
"unit", "class", "before", "after", "anchor"}`, and setup turns them into `Edit` diffs; the
script never writes host docs.

**Breaking.** `RETIRED_KEYS = {"section.old": {"now": "section.new" | None, "since": "X.Y.Z",
"do": "…"}}`, empty today: the registry ships empty, and the first rename adds to it.
`TEMPLATE_READS` names, per template, the headings and keys the script reads (`intent.md`: keys
`id, slug, tier, impact, stage, created, updated, idea, depends_on`, headings `Problem, Outcome,
Open questions`; `issue.md`: its `{{…}}` placeholders; `ideas.md`, `notes.md`: their line forms).
`load_config`'s unknown-key warning stays as it is; `drift` classifies, nothing else.

**Commands.** `drift` and `record` sit beside `readiness`; `reset <name> [--check]` deletes one
override; `uninstall [--check]` reuses `analyze()` (open changes), `worktrees()`,
`ready_to_close()` and `_dirty_paths()` for its refusals, and `SETTINGS`/`ALLOW_RULES` for the
settings edit, rewriting the JSON with `indent=2` and key order kept (`json.loads` keeps it).
Version comes from `PLUGIN_DIR/.claude-plugin/plugin.json`, compared with `_semver()`.

**Skills.** Setup's Step 0 gains `drift`; a new "already set up" branch drafts R7's diffs; Step 5
gains `record`, and `reset` for the override case. New rules: `Bash(uv run --quiet --script
"${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py drift *)`, `… record *`, `… reset *`.
`skills/uninstall/SKILL.md`: Step 0 (`config`, `uninstall --check`), WAIT, Step 2 (`uninstall`),
report.

**Edge cases.** A host doc whose `docs.*` path was changed: the manifest stores the path; drift
follows `config`'s current one and reports the move. `docs.review` falling back to the plugin's
default: no host copy, nothing to drift. A default new in this version with no host doc: not
drift, `readiness` already reports it `missing` or off. A manifest from a newer plugin than the
running one (a downgrade): `drift` refuses to propose and says so.

## Contracts touched

- **Mechanism vs. policy / defaults are the host's once copied.** Kept: `drift` and `record` only
  read host docs or write the manifest; every change to a host doc goes through setup's single
  WAIT as a diff, and `own`, `host-removed` and `conflict` units are never rewritten.
- **Logic a permission rule must cover goes in the script.** All removal (`reset`, `uninstall`)
  and every refusal are in `sdlc.py`; the skills run plain commands.
- **Narrow `allowed-tools`, one WAIT per writing skill.** Setup gains three exact rules and keeps
  one WAIT; `uninstall` is a new gated skill, added to `GATED`, `READS_CONFIG` and
  `test_skills_were_found`. **This changes what setup runs without asking** (`record`, `reset`),
  which is why this is Tier 2.
- **Only publish pushes.** Nothing here pushes.
- **One shape for the shipped docs.** Unchanged, and now load-bearing: the unit split relies on
  it. `setup.json` is not in `defaults/` or `templates/`.
- **This repo's process docs track the defaults.** The own-copy tests move onto `doc_units()`
  with the same assertions, so their meaning doesn't change.
- **Frontmatter read as text.** The manifest is JSON; no doc's frontmatter changes.
- **`READ_ONLY` and the allowlist.** Adding `drift` adds an `ALLOW_RULES` entry, so every set-up
  host's `readiness` reports `permissions: missing` until its next setup: the intended nudge, and
  the first live use of R7.
- **Nothing local.** Fixtures use neutral docs; no paths.
- **O2 (Nothing lost).** Uninstall refuses while any change is live and on uncommitted paths, so
  everything it removes is in history.

## Alternatives rejected

- **Store a pristine copy of each default in the host** (`.sdlc/base/`). A true three-way text
  merge, but it duplicates every doc into every host, and old text isn't needed: proposals use the
  current default's text, so per-unit hashes are enough.
- **Fetch the old defaults from the plugin's GitHub tag.** Needs the network, and fails for a
  plugin installed from a fork or a local path.
- **A version stamp in each doc's frontmatter.** Breaks "frontmatter only where `sdlc.py` reads
  keys" and puts noise in every host doc.
- **Two-way comparison only.** Can't tell a host's edit from an upstream change, so every filled
  prompt reads as drift. Kept only as the no-manifest fallback.
- **Refresh automatically on plugin update.** There is no update hook, and it would write to a host
  without a WAIT.
- **Uninstall as a setup argument.** Setup would carry a removal rule on every run.
- **Uninstall removing `AGENTS.md`/`CLAUDE.md` or `work/`.** Other agents read the guide, and
  `work/` is the host's record; listing the plugin's lines is enough.
- **Hashing whole files.** One host edit flags a whole doc, and nothing narrower can be proposed.

## Verification

```bash
./check.sh                                                   # ruff, format, pytest, plugin validate: all pass
uv run --group dev pytest tests/test_setup_lifecycle.py -q   # R1–R10: one test per class and refusal
uv run --group dev pytest tests/test_skills.py tests/test_defaults.py tests/test_adoption.py -q
uv run --quiet --script scripts/sdlc.py drift                # in this repo after `record`: breaking [], refresh []
```

`test_adoption.py` gains a step: set up a scratch repo from a copy of the 1.0.0 defaults with a
1.0.0 manifest, change one default section in a temporary plugin copy, and check that `drift`
reports exactly that section `refreshed`, then that `uninstall` (nothing open) leaves the
pre-setup tree apart from `work/`.
