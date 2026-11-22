VERDICT: PASS

The kept change was made: `skills/ship/docs.md:27` now says `sdlc.py ship` refuses "when the change has a `findings.md`, a diff this applies to whose note says neither". The other docs match it:
- `docs/REFERENCE.md` already says the docs pass "is asked of a `findings.md` that exists, never of a change with none".
- `skills/ship/SKILL.md` and `plugins/factory/README.md` make no unconditional claim.
- The REFERENCE.md line near 847 ("a pass that applies whose line is missing") is general. The paragraph at line 161 carries the qualifier.

D1 is still open for the person. If they pick "always", the three places above need to change with it.

## Notes
- NIT: plugins/factory/scripts/factory.py:1010: `docs_review` re-reads every listed doc's full text on each `_rounds_at_depth()` call, which `status` and `verdicts` may make many times. It is cheap now, but a docs-site `reviewed` list could make it slow. Cache per call, or short-circuit before the read loop when `changed` has a path outside `tests/` (clause e), since the read only decides which clause holds. {robustness S low}
- Done well: `test_ship_and_the_factory_join_by_the_same_rule` runs `docs_review` and `_docs_applies` over the same fixtures. That pins the two copies in step, which was last round's nit.
- Tests and commands: I ran no tests. `build/round-2.gate.md` records the gate as PASS. I read `skills/ship/docs.md`, the REFERENCE.md diff, the factory README and `decisions.md`.
