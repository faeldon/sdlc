# Decisions

- [x] R1 (person, revise): rename sdlc.py check to sdlc.py vet (and vet --strict), not validate, and the glossary entry is vet, not audit; impact minor; drop [models] verifier with no shim; rename the agent and prompt files; rename the guide heading; leave DIRECTION.md out of the term test.
- [x] D1 (builder round 1, default): R11 and R23 contradict each other. R23 has REFERENCE.md's *After an update* name `sdlc.py check`, and R11 bans that name everywhere. The term test exempts only that paragraph, found by its bold lead, and fails if the paragraph goes. So the spec's verification grep still prints four REFERENCE.md lines. Going ahead with that. → settled by the approver: R23 (your call in R1 and the spec) requires REFERENCE.md's *After an update* to name `sdlc.py check`. The term test exempts only that paragraph and fails if the paragraph goes (`RENAME_NOTE`, plan.md *As built*). The test reviewer judged the scope "sound", and the security reviewer cites the note as how hosts learn of the break.
  - OPTION: exempt that one paragraph — hosts get the note; the grep isn't empty
  - OPTION: drop the old name from the note — the grep is clean; a host's CI author can't search for what broke
  - WHY: R23's note is for a host that hits the removed command, and naming it is what lets them find it
- [x] D2 (builder round 1, default): The card's `, passed`/`, failed` shows only on factory cards, because only a factory landing writes `land-accept.md`. A card built by hand shows `acceptance: N` alone. Going ahead with that. → settled by the approver: R18 makes `, passed`/`, failed` depend on `build/land-accept.md` holding an attempt, and only a factory landing writes that file. The spec's *Alternatives rejected* rules out adding a record to `sdlc.py accept`. `factory_records.accept_verdict()` and `test_a_card_counts_acceptance_and_its_last_run` cover it.
  - OPTION: factory cards only — matches the only record that exists
  - OPTION: add a record to `sdlc.py accept` — every card could show it; a feature the spec rejected
  - WHY: the spec's *Alternatives rejected* rules out a record from `accept`
- [x] D3 (builder round 1, default): I reworded more than R7 and R9 list: → decided: the assumed default, confirmed
- [x] D4 (builder round 1, default): R11 and R23 contradict each other: R23's note has to name `sdlc.py check`, and R11 bans the name everywhere. The term test exempts only that REFERENCE.md paragraph, found by its bold lead, and fails if the paragraph goes. So the spec's verification grep still prints those lines. Going ahead with that. → settled by the approver: a duplicate of D1 (same R11/R23 conflict, same options), so it is settled on the same grounds: R23's required note and the scoped `RENAME_NOTE` exemption that the test reviewer judged sound.
  - OPTION: exempt that one paragraph — hosts get the note; the grep isn't empty
  - OPTION: drop the old name from the note — the grep is clean; a host's CI author can't search for what broke
  - WHY: R23's note is for a host that hits the removed command, and naming it is what lets them find it
- [x] D5 (builder round 1, default): The card's `, passed`/`, failed` after `acceptance: N` shows only on factory cards, because only a factory landing writes `land-accept.md`. A card built by hand shows the count alone. Going ahead with that. → settled by the approver: a duplicate of D2 (same card text, same options), so it is settled on the same grounds: R18 and the spec's *Alternatives rejected*.
  - OPTION: factory cards only — matches the only record that exists
  - OPTION: add a record to `sdlc.py accept` — every card could show it; a feature the spec rejected
  - WHY: the spec's *Alternatives rejected* rules out a record from `accept`
