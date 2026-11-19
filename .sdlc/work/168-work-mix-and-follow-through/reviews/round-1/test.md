VERDICT: PASS

I found no requirement without a test that would fail without it. Two gaps are noted below as nits.

## Notes

- **Gate:** `build/round-1.gate.md` reads `GATE: PASS` on `./check.sh`, with `3087 passed, 28 skipped`. I ran no tests myself, so I did not run any named tests to check a claim.
- **Coverage by requirement:**
  - R1 is covered by `test_work_mix_classes_each_change_by_its_first_signal`. It asserts the class, the `by` signal, and `also` for the mixed change, for process (`["debt"]`) and for the plain capability change (`[]`).
  - R2 is covered by the unmeasured test and the null-shares test.
  - R3 is covered by the process-work test, which includes the own-folder change.
  - R4 is covered by the `fixes` line test.
  - R5 and R6 are covered by the two time-to-users tests. The R6 test checks both the case with nothing released and a mixed released/unreleased window.
  - R7, R8 and R9 each have the test the spec names. The R9 test checks that nothing reads 0 where it should be null.
  - R10 is covered by the report-window test, the extended same-figures test, and the no-value-band test. The same-figures test still asserts that the report runs no host command.
  - R11, R12 and R13 add every case the spec lists to the parametrized tests. The R11 set also adds `\&`, which the spec's behaviour rule names.
- **Checks:** There is no `checks.md` in the change folder. Nothing needs one, because every requirement has a test.
- **Well covered:** each class rule's precedence, a seed deleted by hand (`vanished`), seeds already in the register before the retrospective, and milestones left unmeasured.
- NIT: tests/test_retro.py:2126: `test_retro_and_its_report_show_the_same_figures` compares only work mix and time to users with the report, and has no assertion on the follow-through sentence. The spec asks that the report and the JSON not disagree. The other test checks the report text, but follow-through is checked only in the JSON tests. {tests S med}
- NIT: tests/test_retro.py: R14 (the docs) has no test, as the spec says. Nothing here checks that `REFERENCE.md` and the retro skill's Step 0 name the three keys. {docs S low}
