VERDICT: CHANGES

- CHANGE: [context] AGENTS.md:195: it says "Ship, and the factory's `carry`, write `findings.md`". After this diff `land --close` writes it too, so a session would take carry as the factory's only writer. Change it to "Ship, the factory's `carry`, and its `land --close` write `findings.md`, and `sdlc.py` only reads it".

## Notes

- NIT: plugins/factory/scripts/factory.py:4315: `complete` for a landing round is `bool(r["reviews"])`, which is looser than the build rounds' "complete for the depth" test. It is safe today because the land skill runs `land --close` only after `land-verdicts` says `pass`, but `land --close` doesn't check that itself. A partly reviewed landing round would have its partial findings written. If you want the guard here, use `land_verdict(...)["next"] == "pass"`, or keep the note and say the skill owns it.
- NIT: plugins/factory/scripts/factory.py:1959 (`write_findings`, reached from `carry`): a rerun of `carry` after a landing has begun drops the `land-<n>` sections, since they carry `By:` roles and carry's rounds are build rounds only. The next `land --close` restores them, so nothing is lost unless a commit lands in between. Whether that can happen depends on whether the approve step can rerun after a landing. Worth a line in the README if it can.
- NIT: notes.md already has the unticked line about `templates/findings.md`'s note, which still names only carry. Ship will need a disposition for it.
- Done well: the change reuses `read_rounds`, `read_verified`, `write_findings` and `finding_section` through a `kind` parameter instead of a parallel reader. The `land --close` write happens before `_record_move` and `_amend_record`, so the amend carries it. The by=auto refusals come before the write. The landing's rounds are kept out of `carried` unless the last landing round kept them, which is the rule D3 records. Retro needs no change: `_review_sources` groups by `By:`, which the landing sections carry, and `Sdlc-Findings` is still not written at a landing.
- Defaults D1–D3 in decisions.md are reasonable as written. I'd leave them open for the person.
- spec.md is absent. Tier 1 doesn't require it, so I reviewed against intent.md and plan.md.
- Ran: `pytest tests/test_land.py -k "landing or land_close or close"` (31 passed); `pytest tests/test_nothing_local.py tests/test_defaults.py` (129 passed); `ruff check` and `ruff format --check` on `factory.py` and `test_land.py` (clean). I did not run the full `./check.sh`, and I did not check the `claude plugin validate` step.
