VERDICT: PASS

Every requirement R1–R12 has a test that would fail without it, and none of the tests I read can pass vacuously.

I did not run any test myself; the verification below rests on the gate record and on reading the diff.

**Requirement → test**
- **R1:** `test_origin_values_are_host_and_self` pins `ORIGINS == ("host", "self")`.
- **R2:** `test_vet_strict_passes_a_change_with_no_origin` fails if a missing line is refused. `test_an_origin_outside_host_and_self_is_an_error` is parametrized on `elsewhere` and `[host, self]` and also checks both good values.
- **R3:** `test_a_closed_change_without_origin_reads_none` calls `_change_record()` directly, the function `closed_changes()` builds every record with. It covers host, self, no line, an invalid value, an empty value and `read=False`. It fails if the unset one reads as `self`.
- **R4:** `test_close_writes_an_origin_trailer` closes a real change. It checks `git interpret-trailers --parse` and `parse_trailers()` on the `Close` body. `test_an_invalid_origin_closes_without_the_trailer` covers an invalid word and a missing branch.
- **R5:** `test_a_change_without_origin_closes_without_the_trailer` and `test_a_dropped_change_carries_no_origin_trailer`. The dropped test deliberately gives the change `origin: host`, so it can fail.
- **R6:** `test_parse_trailers_reads_origin_as_text` also checks that `origin` is absent when no such trailer is present.
- **R7 and R12:** `tests/test_feature_map.py`, which the gate ran green.
- **R8:** `test_retro_counts_changes_by_origin` covers a change before the window and a dropped one as well as the three origins. `test_a_window_before_origins_reads_as_all_unknown` covers an old window.
- **R9, R10, R11:** the three `test_skills.py` tests and `test_an_entry_reads_its_origin_line` (`fields["Origin"]`). The R9 test scopes its `G<n>` check to the `origins.host` reading passage. The R10 test pins the clause in the single and batch questions.

**Gate:** `round-1.gate.md` is PASS from `./check.sh`: `3635 passed, 29 skipped`, plugin validation passed.

## Notes
- The rerun case in R5 rests on `_close_commit()`'s existing early return. The plan says the existing rerun tests cover it, and the spec asks for nothing more.
- D1 (masking the plugin version in `_normal()`) is a sound fix, and the gate is green because of it. `D2` (`origin:` left unset on 207's own intent) leaves 207 itself uncounted, as the spec intends.
- There is no `checks.md` for this change, and I see no requirement that needs one.
- I ran no test command; the count above is the gate's.
- NIT: tests/test_skills.py: `test_idea_and_bug_offer_an_origin_line` only asserts that `Origin: self` is absent from the skill text. It would not catch the skills telling the person to write `self` in other words {tests S low}
