VERDICT: PASS

Every requirement from R1 to R12 has a test that fails without it, and the full suite is green. R13 is covered by the acceptance check.

## Notes

- **Run:** `uv run --group dev pytest -q -n auto` gave 2351 passed, 13 skipped, no failures. `sdlc.py drift` reports `breaking: []`, `refresh: []` and `report: []`.
- **Requirement coverage:**
  - R1: `test_a_nit_is_read_with_its_weights` covers a nit with weights, an unweighed nit, and one with an invalid cost (`XL`). `test_the_nit_words_are_sdlcs` pins the copied cost and value words. `test_the_factory_reviewers_weigh_their_nits` covers the three reviewer prompts.
  - R2, R3, R5, R6, R7: the tests in `tests/test_factory.py` check the exact disposition, reason and rank of each nit kind through `sdlc.findings_entries()`. The `high` and `L` nits are also checked in `notes.md`. R5 also covers a restart's first round, which is handed nothing.
  - R4: `test_rework_hands_the_builder_its_cheap_nits` checks the exact rework and review prompt text and the role scoping. `test_a_round_with_only_nits_is_never_reworked` checks that a nits-only round goes to `approve`, and that a restart hands nothing.
  - R8 to R11: `test_land_check_shows_the_nits_it_would_file`, `test_land_question_names_the_nits`, `test_nits_to_file_keep_the_gate_the_persons`, `test_a_landing_files_the_nits_sdlc_reads` and `test_a_landing_rerun_files_each_nit_once`. These check the `nits` part against `agent_findings()`, the clause present and absent, `--by auto` refusing with nothing committed, `sdlc.nit_entries()` reading the filed entry with distinct ids, and a rerun filing nothing twice.
  - R12: `test_ship_files_the_agents_recorded_nits` is a text check on the side file.
- **`checks.md`:** the one section, "The docs name the factory's landing as a source of nits", is a single `grep` chain over `guide/review.md`, `guide/process.md` and `templates/inbox.md`. It leaves the tree unchanged. I ran only its `grep` chain, not the repo's acceptance command, and it exited 0 as written. A revert would remove the wording it greps for, so it fails without the change. It proves R13's wording requirements; the `.sdlc/setup.json` part is covered by `drift`.
- **Decisions:** D1 and D2 in `decisions.md` are default-answered builder decisions, not blocking. The tests follow both. D1 puts `Theme:`/`Cost:`/`Value:` only on nits to file. D2 counts a cheap nit as handed when the round kept a change and the next build isn't a restart's or upgrade's first round, which `test_a_nit_not_raised_again_is_still_filed` pins.
- **Gap, not a reason for CHANGES:** the spec says the R10 entry body is `Raised by the <role> review of <NNN-slug>, round <n>: <text>`. The test checks the prefix and the `Raised by:` pass but not the whole body. This is low risk.
- **NIT:** `tests/test_land.py:1328`: `test_a_landing_rerun_files_each_nit_once` reruns `_dispose()` directly with the same `pre`. It never reruns `cmd_land` end to end after a failed commit, so the rerun path through `cmd_land` is only covered indirectly.
