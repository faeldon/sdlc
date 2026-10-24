# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `work/ideas.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Left out of scope at intent

- [x] Seed item 2: acceptance checks live in `work/NNN-slug/`, run by ship and archived by close
  with the folder, in place of the record in `notes.md`. Out of scope here (it changes the `work/`
  layout and what ship runs in a host); carry it forward as its own seed when this ships, since
  ship deletes the seed this change came from. → seed: Acceptance checks kept in the change
  folder, run by ship

## Redesigned after 002 landed

002 built no test-triage harness. It left helpers this change reuses (`plugin_version()`,
`_older()`) and two paths kept on purpose. `RETIRED_KEYS` lists keys the plugin stopped reading,
so no old code runs and it isn't a shim. The no-manifest path (two-way drift, the "no record"
nudge, uninstall leaving the ignore line) serves any host without a readable record. It was first
given `remove_in = "1.3.0"`, then kept for good: a 1.0.0 host's first rerun after removal would
record today's defaults as its base and never be offered the updates since 1.0.0. So the registry
starts empty. The spec's R5 moved overdue shims out of Problems, which `check --strict` gates on.

## Sweep

Removed, since only a revert could fail them:
- `test_retro.py` `test_it_reports_every_key_and_writes_nothing`: `"tokens" not in out`, a key
  removed from retro's output that nothing reads.
- `test_sdlc.py` `test_new_seeds_a_missing_counter_from_the_folders_then_writes_it`: `work/.last-id`
  absent, the counter's old place.
- `test_sdlc.py` `test_new_worktree_writes_the_counter_in_the_worktree_not_under_git` and
  `test_adoption.py` `test_a_bare_repo_runs_a_change_from_new_to_close`: `<git-dir>/sdlc` absent,
  the counter's older place.
- `test_skills.py` `test_close_lands_mirrors_and_removes_through_the_script_and_never_by_hand`:
  `"sdlc.py archive"` absent; there is no `archive` subcommand any more. `"rm -"` kept: a rule.
- `test_readiness.py` `test_the_allowlist_covers_only_subcommands_that_read`: `"archive"` in the
  writers, a subcommand that no longer exists.
- `test_archive.py` (drop): `.sdlc/ids` in the allowed changed paths, a file no script writes.
- `test_readiness.py` `test_the_defaults_setup_copies_from_exist`: `"### Stage 4 — Test"` and
  `"/sdlc:setup"` in `defaults/SDLC.md`; `test_playbook.py` pins every stage heading, and the
  mention pinned one edit. The files-exist check stays.
- `test_skills.py` `test_uninstall_plans_before_its_gate_and_removes_after`:
  `"claude plugin uninstall sdlc@sdlc"`, one line of prose nothing reads. The gate-order checks stay.

Rewritten to the rule they stand for:
- `test_skills.py` `test_setup_asks_what_kind_of_repo_first`: `len(rules) == 8`, which every
  setup rule added had to bump, becomes "no rule reads history or the tracker", the rule its
  comment states.
- `test_skills.py` `test_retro_closes_its_own_loop_and_release_says_when_one_is_due`: "Since the
  last retrospective" is checked with whitespace collapsed, not against one line wrap.
- `test_skills.py` `test_skills_show_an_outcome_by_its_name_beside_its_id`: the form `O1 (<name>)`,
  not the one example `O1 (Unaided setup)`.
- `test_setup_lifecycle.py` `test_the_shipped_defaults_have_one_block_per_key`: fails when its glob
  finds nothing, which it passed silently before.

Added: `test_setup_lifecycle.py` `test_uninstall_without_a_manifest_leaves_the_ignore_line`, the
one branch of the permanent no-manifest path with no test.

Kept, judged at build:
- `test_skills.py` `test_the_retro_keeps_evidence_and_the_product_docs_prose_out_of_what_it_writes`:
  "Quoting evidence output" and "only its outcome lines" are the out-of-scope rules the model
  follows (a host's users' data); "the product pass first of all" is an order rule.
- `test_playbook.py` `test_the_doc_describes_three_loops`: the phrases are the loops' rules
  ("No loop reaches past the one inside it", "never edits code or skills"), which the docstring
  keeps said on purpose.

## Acceptance check

Run once, in a scratch host (`pkg.json` at 1.0.0, tagged, one patch change closed, a shim
`old-flag` with `remove_in = "1.0.1"`), with this change's `scripts/sdlc.py`:

```
== release --check
['shim old-flag is due by 1.0.1: remove it first (src/config.py; its test: tests/test_config.py::test_old_flag_reads)']
== unreleased
{'overdue': [], 'due': [{'name': 'old-flag', 'remove_in': '1.0.1', 'where': 'src/config.py', 'test': 'tests/test_config.py::test_old_flag_reads'}], 'unversioned': []}
== status
■ Unreleased: 1
    since v1.0.0 → 1.0.1 (patch)  /sdlc:release
    ⚠  shim old-flag: remove in 1.0.1 (src/config.py)
    001  reopen-drafts                patch
== check --strict
exit 0
```

This repo's `.sdlc/setup.json` is recorded again (`sdlc.py record`), since the default's Stage 4
Compatibility line and the new config key changed; `sdlc.py drift` here reports nothing.
