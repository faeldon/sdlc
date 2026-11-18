VERDICT: PASS

The gate record `build/round-1.gate.md` is green: attempt 1 failed, attempt 2 passed. Both outcomes in `intent.md` have code and a test that would fail without it.

**Requirements**
- **`[models]` from the base branch.** `load_config()` now reads it through `_base_factory()` and the new `_models()`.
  - `test_models_are_the_base_branch_s_even_for_an_older_worktree` commits `[models]` on the base branch only. It finds the entry in `start`'s `models_at` and in the `--model` argument `agent` passes to `claude`.
  - The same test shows a `[models]` entry in the change's own checkout changes nothing and warns, which answers the open question.
  - `test_a_host_s_own_depth_and_models_are_kept` now commits its models on the base branch via `_on_base()`.
- **Own-folder citations.** `_own_folder()` runs after `_placeholders()` in `cmd_agent`.
  - `test_a_reply_citing_its_own_change_by_number_is_filed_by_its_full_name` covers the bare number, `work/NNN/…`, the glob `work/NNN*`, and a case already written in full.
  - The same test checks another change's number, a longer number and `work/NNN-*` are left alone, and that `_forbidden_shapes()` finds nothing in the filed text.
  - Only a number and a folder name are rewritten, never a verdict or finding, so the constraints hold.

**Context.** I found no context doc that now says something false. AGENTS.md's mention of `[models]` only appears in the factory README, which the diff updates.

## Notes
- NIT: plugins/factory/scripts/factory.py:2822: `work/008*x` is rewritten to `work/008-slug*x`, because the regex backtracks off the `*` and the lookahead then passes on `*`. The shape is unrealistic, but `(?![\w-])` after an optional `\*?` could be made possessive or tightened {robustness S low}
- NIT: plugins/factory/README.md:383: the re-wrapped paragraph leaves one over-long line (`serve`, `shoot` and `paths` …) {docs S low}

**Done well**
- `_models()` keeps its warnings next to the base branch's table.
- The rewrite test builds its citations from parts, so the test file never trips the scan it guards against.

**Run:** read the gate record only. I ran no tests or commands myself.
