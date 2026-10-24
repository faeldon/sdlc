---
id: 002
slug: setup-lifecycle
kind: plan
created: 2026-10-24
updated: 2026-10-24
---

# 002 — Keep a host's setup current, resettable and removable · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Context

After `claude plugin update`, a host's copies of `defaults/*.md`, its `.sdlc/templates/`
overrides and its `config.toml` keys drift silently: `readiness` only checks existence and `<`
prompts. Nothing resets a copy to the default, and nothing takes setup back out. The spec
(`work/002-setup-lifecycle/spec.md`, R1–R13) adds a per-unit hash manifest, a three-way `drift`
report, `reset`, `uninstall` and a `/sdlc:uninstall` skill.

**One deviation from the spec, to approve:** R12 says the status line goes "under Problems".
`analyze()["problems"]` is what `check --strict` counts, and ship and spec run it as a gate, so
counting drift there would fail every host's gate right after an update. The plan prints it as
its own one-line nudge (`■ Setup: …`), like `■ Retro due`, and never counts it as a problem.
The spec's R12 is edited to say so in step 7.

**A second deviation:** R4 says each `new` key is reported "with its comment from `CONFIG_KEYS`".
Those are Python comments, so they're gone at runtime. Keeping them would mean either parsing the
script's own source or duplicating every key's comment into a help dict. Instead the plan reports
each new key with its default and says to look it up in `docs/REFERENCE.md`, which already
documents every key. R4's wording is edited in step 7.

## Files to change

- `scripts/sdlc.py`: `doc_units()`, `unit_hash()`, `plugin_version()`, `RETIRED_KEYS`,
  `TEMPLATE_READS`, `HOST_DOCS` (doc key → default file), `MANIFEST` path; `drift()` +
  `cmd_drift`; `cmd_record`; `cmd_reset`; `cmd_uninstall`; a `drift` item in `cmd_readiness`;
  `setup_nudge()` in the status branch of `main()` and `print_status`; `drift` added to
  `READ_ONLY`; argparse entries for `drift`, `record`, `reset`, `uninstall`
- `skills/setup/SKILL.md`: Step 0 runs `drift`; an "already set up" branch drafts refreshes;
  the `reset` argument; Step 5 runs `record` (and `reset` for an override); three new `Bash(...)`
  rules; `argument-hint` gains `reset`
- `skills/uninstall/SKILL.md` (new): Step 0 `config` + `uninstall --check`, one WAIT, Step 2
  `uninstall`, report with the commit and `claude plugin uninstall sdlc@sdlc`
- `defaults/SDLC.md`, `.sdlc/SDLC.md`: `/sdlc:uninstall` in the skill list (line 18 of each)
- `docs/REFERENCE.md`: a new `## Setup, refresh and uninstall` section (manifest, drift
  classes, breaking, reset, uninstall); `README.md` *Updating*: run `/sdlc:setup` after an update,
  plus `/sdlc:uninstall` in the features list; `AGENTS.md` architecture map: one paragraph on the
  manifest and drift
- `.sdlc/setup.json` (new): this repo's own manifest, written by `record`
- `tests/test_setup_lifecycle.py` (new): R1–R10 unit and command tests
- `tests/test_defaults.py`: the own-copy tests move onto `sdlc.doc_units()`
- `tests/test_skills.py`: `uninstall` in `GATED`, `READS_CONFIG`, `test_skills_were_found`;
  setup's runs `drift` and `record`
- `tests/test_readiness.py`: the `drift` item; `drift` in `ALLOW_RULES`, still no writer
- `tests/test_adoption.py`: the old-manifest → drift → uninstall step, via `uv run --script`

## Work order

1. **Units.** Add `doc_units(text) -> list[tuple[str, str]]` to `sdlc.py`, near `_section`
   (line ~2066), reusing `_body_of`, `FENCE_RE` and `HEADING_RE`: heading sections at levels
   2–4 keyed by the heading line, and `- **lead**` bullets keyed by `- **lead**` (body = the
   bullet up to the next `- `, blank line or heading, the same extent as test_defaults' regex).
   Add `unit_hash()` (sha256 over the text with trailing spaces stripped and blank runs
   collapsed). Move `test_defaults.py`'s `test_this_repos_copy_keeps_the_defaults_sections` and
   `…_review_keeps_every_default_failure_class` onto it, with the same assertions. Run
   `pytest tests/test_defaults.py`. Stop point: no behaviour change.
2. **Constants and manifest.**
   - Add `HOST_DOCS = {"process": "SDLC.md", "review": "REVIEW.md", "health": "HEALTH.md",
     "product": "PRODUCT.md", "project": "PROJECT.md"}` and reuse it in `cmd_readiness`'s
     `defaults` map.
   - Add `RETIRED_KEYS: dict = {}`, and `TEMPLATE_READS` built from what the script reads
     (intent keys and headings `Problem`, `Outcome`, `Open questions`; `issue.md` placeholders
     from `render_issue`; `ideas.md`'s `IDEA_RE` form; `notes.md`'s `- [ ]`).
   - Add `plugin_version()`, which reads `PLUGIN_DIR/.claude-plugin/plugin.json`.
   - Add `cmd_record(root, created, gitignore_line)`, which writes `.sdlc/setup.json` with sorted
     keys and `indent=2`, merges `created` with an earlier manifest, and keeps an earlier
     `gitignore_line: true`.
   - Tests (R1): the shape; idempotence; and every `TEMPLATE_READS` item found in the plugin's
     template (R5's staleness guard).
3. **Drift.** `drift(root, cfg) -> dict` with `breaking`, `refresh`, `report` and `base`
   (`"manifest"` or `"none"`):
   - per host doc, the R2 classes, or R3's two-way classes with no manifest;
   - config: unknown keys come from re-reading the toml the way `load_config` does, then are
     split into `RETIRED_KEYS` (breaking) and `unknown`. `new` = `CONFIG_KEYS` minus the
     manifest's `config_keys`, each with its default value and a pointer to its line in
     `docs/REFERENCE.md` (see the second deviation);
   - template overrides: `TEMPLATE_READS` misses (breaking), and the hash differing from the
     manifest's (`changed`);
   - `project_doc`/`product_items` problems are copied into `breaking`;
   - a manifest version newer than `plugin_version()` (a downgrade): no proposals, plus a
     `report` entry.

   Add `cmd_drift`, which prints JSON and exits 0. Tests, one per class: `added`, `refreshed`,
   `removed`, `conflict` (both variants), `own`, `host-removed`, `current`, `differs`, a
   retired key, an unknown key, a new key, an override missing a key, a changed template, a
   downgrade. Each test builds a fake plugin dir by monkeypatching `DEFAULTS_DIR`/`TEMPLATE_DIR`
   to tmp copies.
4. **Visible.**
   - `cmd_readiness` gains a `drift` item: `n/a` with no config, `warn` with counts when
     `breaking` or `refresh` is non-empty, else `ok`.
   - `setup_nudge(home)` returns a line when there is a config and either no manifest or a
     manifest older than the plugin. `main()`'s status branch sets `a["setup"]`, and
     `print_status` prints `■ Setup: …  /sdlc:setup` just before `■ Retro due`.
   - `"drift"` is added to `READ_ONLY`.
   - Tests (R12): the readiness item in all three states; `drift` in `ALLOW_RULES` and the
     no-writer assertions at `test_readiness.py:131` still pass; the nudge prints for a missing
     or old manifest and not for a current one; `check --strict` stays 0 with drift present.
5. **Reset and uninstall.**
   - `cmd_reset(root, name, check_only)`: `name` must be a bare filename that exists in
     `.sdlc/templates/`, and anything else is refused (`..`, `/`, a doc path). It deletes the
     one file.
   - `cmd_uninstall(root, check_only)`, from `main_root`:
     - refusals: `analyze(home)["open"]`, any `worktrees()` entry under `.claude/worktrees/`
       other than main, `ready_to_close()`, and `_dirty_paths(home)` filtered to `.sdlc/`,
       `.claude/settings.json` and `.gitignore`;
     - plan: `.sdlc/` (every file), the `ALLOW_RULES` in settings (the file's rewritten and kept
       even when `allow` empties), and the ignore line only with `gitignore_line: true`
       (otherwise listed as left in place);
     - the lines in each existing `docs.context`/`docs.policy` file that match
       `/sdlc:|\.sdlc/|\bwork/`;
     - it prints JSON either way, and without `--check` it applies.
   - Tests (R8–R10): reset refuses a path outside the folder; each of the four refusals;
     uninstall on a scratch repo matches the pre-setup tree apart from `work/` and the context
     files, keeps unrelated settings keys and rules, keeps a pre-existing ignore line, and
     commits nothing (HEAD unchanged).
6. **Skills.**
   - Edit `skills/setup/SKILL.md`:
     - Step 0 adds `sdlc.py drift`. "If every item is `ok`" also requires `drift` to have
       nothing.
     - A Step 3 bullet, **Refresh**: each `refresh` item becomes an `Edit` diff; `breaking`
       items are listed first, each with its fix; `report` items are listed, with no edit.
     - A `reset` argument paragraph covering a doc (draft the default and re-fill its prompts,
       with a diff of what's lost) and a template (`sdlc.py reset <name>`).
     - Step 5 adds `sdlc.py record --created <paths> [--gitignore-line]`.
     - The new rules, written exactly as run.
   - Write `skills/uninstall/SKILL.md`, following the drop skill's shape: frontmatter with the
     description (>80 chars, says when not to use it), `disable-model-invocation: true`, and
     `allowed-tools` `Bash(cd *)`, `Bash(git rev-parse *)`, `config *`, `uninstall *`. Its body
     names `archive.target`, `docs.policy` and `docs.context`.
   - Update `test_skills.py`'s sets. Run `pytest tests/test_skills.py`.
7. **Docs and own manifest.**
   - Edit `defaults/SDLC.md` and `.sdlc/SDLC.md` line 18 identically.
   - Write the REFERENCE.md section, README *Updating* and features, and the AGENTS.md paragraph.
   - Edit spec R12 (the nudge) and R4 (new keys with their default).
   - Run `sdlc.py record` in this worktree to write `.sdlc/setup.json` (`--created` left empty:
     this repo's files predate the manifest), then check that `sdlc.py drift` shows `breaking: []`
     and `refresh: []`.
8. **Adoption.** In `test_adoption.py`, copy `scripts/`, `defaults/`, `templates/` and
   `.claude-plugin/` to a tmp plugin dir, run `record` from it in a scratch repo, edit one
   default section in that copy, run `drift`, and check that exactly that unit is `refreshed`.
   Then run `uninstall` and compare the tree. All through `_run()`-style `uv run --script`
   against the copied script. Run `./check.sh`.

## Tests

- **R1:** `test_record_writes_the_manifest_shape`, `test_record_twice_is_identical`,
  `test_record_keeps_created_and_ignore_line`
- **R2:** `test_drift_<class>` for each of `added`, `refreshed`, `removed`, `conflict_both`,
  `conflict_removed_but_edited`, `own`, `host_removed`, `current`
- **R3:** `test_drift_without_manifest_is_two_way`, on a host set up from the 1.0.0 defaults (the
  current `defaults/` with a 1.0.0 version stamp)
- **R4:** `test_retired_key_is_breaking`, `test_unknown_key_is_reported`, `test_new_keys_listed`,
  `test_retired_keys_point_at_live_keys`
- **R5:** `test_override_missing_a_read_is_breaking`, `test_changed_template_is_reported`,
  `test_template_reads_exist_in_the_plugins_templates`
- **R6:** `test_drift_keeps_breaking_refresh_and_report_apart`
- **R7:** `test_setup_runs_drift_and_record` (test_skills.py); manual: run `/sdlc:setup` in a
  scratch repo with an old manifest, expect one diff per `refresh` item behind one WAIT
- **R8:** `test_reset_deletes_only_an_override`, `test_reset_refuses_other_paths`
- **R9:** `test_uninstall_refuses_open_change`, `…_worktree`, `…_unclosed_shipped`,
  `…_uncommitted`
- **R10:** `test_uninstall_leaves_the_pre_setup_tree`, `test_uninstall_keeps_unrelated_settings`,
  `test_uninstall_keeps_a_preexisting_ignore_line`, `test_uninstall_commits_nothing`
- **R11:** the existing parametrized `test_skills.py` checks, with uninstall added to the sets
- **R12:** `test_readiness_drift_item`, `test_status_nudges_on_old_manifest`,
  `test_check_strict_ignores_drift`
- **R13:** `test_defaults.py` own-copy tests (the SDLC.md line edited in both);
  `test_nothing_local.py` over the new files; manual: `sdlc.py drift` in this repo shows nothing
- **Gate:** `./check.sh`

## Rollback

`git revert` the change's commit restores every file, this repo's `.sdlc/setup.json` included.
It does not cover:
- **Hosts that ran `record`:** their `.sdlc/setup.json` stays behind. It's inert under the old
  code, since nothing reads it, and the host deletes it with `git rm .sdlc/setup.json`.
- **Hosts that ran `uninstall`:** their `.sdlc/` and settings rules are gone from the working tree
  but in their history. `git checkout HEAD~ -- .sdlc .claude/settings.json .gitignore` from the
  commit before their uninstall commit restores them.
- **The `drift` allow rule** added to hosts' `.claude/settings.json` by a refresh. It's harmless
  once the subcommand is gone, and they remove the one line.
- **Issue #2's body:** it's rewritten by `sync` and stays as last synced until it's synced again.
