VERDICT: PASS

Every requirement R1–R15 has a test that would fail without it. The gate passed (`build/round-1.gate.md`: 3693 passed, 29 skipped, `claude plugin validate --strict` passed). I ran nothing myself.

## Notes

Where each requirement is covered, in `tests/test_upstream.py` unless noted:

- **R1, R2:** `test_upstream_repo_comes_from_the_manifest` and `test_upstream_is_unavailable_in_the_plugins_own_repo`.
- **R3, R8:** `test_bug_asks_which_kind_before_filing_upstream` and `test_bug_shows_the_upstream_body_before_its_wait`, both in `tests/test_skills.py`. The second pins the order render → show → WAIT → question → send, and the single WAIT heading.
- **R4:** `test_upstream_body_holds_only_the_allowlist` puts 13 sentinels plus the commit SHA and `#12` into every field and the output. It also checks that the extra `Files` section lands in `left_out`.
- **R5:** `test_upstream_diagnostics_name_keys_never_values` runs with `claude` and `uv` missing, then with fake ones, and checks that the unknown `made.up` key is counted but not named.
- **R6:** `test_upstream_cut_leaves_out_what_it_cannot_make_safe` and `test_upstream_cut_places_paths_by_where_they_are`. Together they cover the left-out note, the 40-line tail and the path placement.
- **R7:** `test_upstream_send_refuses_a_body_not_previewed`.
- **R9:** `test_github_file_issue_names_the_repo_and_sets_nothing_else` asserts the exact `gh` argument list.
- **R10:** `test_upstream_send_never_files_twice` and `test_upstream_send_after_a_stopped_send_finds_the_issue_first`, plus `test_a_stopped_send_with_no_issue_files_it`, which covers a stopped send where no issue exists yet.
- **R11:** `test_upstream_without_gh_files_nothing` and `test_upstream_without_a_login_files_nothing`.
- **R12:** `test_intake_flags_an_issue_from_a_host`, in `tests/test_archive.py`.
- **R13:** `test_an_upstream_send_changes_nothing_recorded_issues_reads`.
- **R14:** the render and cut tests are marked `portable`.
- **R15:** `test_feature_map` covers the `upstream` entry, and the one check in `checks.md` covers the prose.

Gaps that don't change the verdict:

- Triage's `Origin: host` text (R12's second half) has no skill-text test. It's prose, so this is a small gap.
- The R14 tests that need no fake `claude` or `uv` are the only ones marked `portable`. The send tests rely on a fake `gh`, which Windows can't run.

`checks.md` has one check, "The docs say what filing upstream does". It is a chain of `grep -q` calls on REFERENCE.md, README.md, AGENTS.md and FEATURES.md. It leaves the tree unchanged and fails only if those lines are removed. I expect it to pass, and I didn't run it.

- NIT: tests/test_skills.py: the triage skill's `Origin: host` instruction has no text test {tests S low}
