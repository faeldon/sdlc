Everything my last report claimed has been rerun, and all of it passes. The full gate is green on the change as it now stands (exit 0, 3437 passed), including the late fix that lets an in-flight run's mend resume the arbiter from `runs/verifier.sessions`. HEAD is still `d0c566a` and everything is uncommitted.

One more fix since that report: AGENTS.md still named the old command in two places, "what `check` requires" and "runs `check --strict` on it". The second was split across a line break, so the retired-names test (which reads one line at a time) missed it. Both now say `vet`. A search across line breaks, outside the change folders, retrospectives and tests, finds `sdlc.py check` only in REFERENCE.md's *After an update* note, which is there on purpose.

Nothing else changed since my last report: the slices, tests, `checks.md`, `plan.md`'s *As built* section and the three `[default]` decisions all stand. I'm re-raising the decisions here so they are collected from this round.

- DECISION: [default] R11 and R23 contradict each other: R23's note has to name `sdlc.py check`, and R11 bans the name everywhere. The term test exempts only that REFERENCE.md paragraph, found by its bold lead, and fails if the paragraph goes. So the spec's verification grep still prints those lines. Going ahead with that.
  - OPTION: exempt that one paragraph — hosts get the note; the grep isn't empty
  - OPTION: drop the old name from the note — the grep is clean; a host's CI author can't search for what broke
  - WHY: R23's note is for a host that hits the removed command, and naming it is what lets them find it
- DECISION: [default] The card's `, passed`/`, failed` after `acceptance: N` shows only on factory cards, because only a factory landing writes `land-accept.md`. A card built by hand shows the count alone. Going ahead with that.
  - OPTION: factory cards only — matches the only record that exists
  - OPTION: add a record to `sdlc.py accept` — every card could show it; a feature the spec rejected
  - WHY: the spec's *Alternatives rejected* rules out a record from `accept`
- DECISION: [default] I reworded more than R7 and R9 list:
  - "gate" meaning a person's yes became approval or WAIT, across the land, retro, intent and health skills, REFERENCE.md and the factory README;
  - "build check" became "the slow gate" in ship's steps, the setup drafts, README.md and the landing question;
  - NOTICE lists `agents/arbiter.md` as written for this plugin.

  Going ahead with all of it.
  - OPTION: reword everywhere found — one meaning per word, as the intent asks; a larger diff for ship to read
  - OPTION: only the listed spots — a smaller diff; leaves "gate" meaning a yes in several docs
  - WHY: the intent's outcome, "a newcomer meets one meaning per word"

## Evidence

$ rg -n -U 'sdlc\.py\s+check\b|`check\s+--strict' --glob '!.sdlc/{work,retros}/**' --glob '!.sdlc/DIRECTION.md' --glob '!tests/**' .
./docs/REFERENCE.md:341:**`sdlc.py check` is now `sdlc.py vet`.** …
./docs/REFERENCE.md:342:tier and stage was renamed with no alias: `sdlc.py check` is gone, and argparse refuses it. A
./docs/REFERENCE.md:343:host's CI that runs `sdlc.py check --strict` must run `sdlc.py vet --strict` instead. The skills
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 187
All checks passed!
320 files already formatted
3437 passed, 29 skipped in 148.94s (0:02:28)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py::test_vet_strict_fails_on_a_problem tests/test_sdlc.py::test_check_is_no_longer_a_command tests/test_readiness.py::test_a_host_with_only_the_check_rule_is_missing_the_vet_rule tests/test_feature_map.py tests/test_retro.py::test_agents_by_role_groups_verifier_with_arbiter tests/test_modules.py tests/test_board.py tests/test_factory.py -k 'vet or check_is_no or vet_rule or vocabulary or retired or agents_md or verifier or arbiter or verify or shared_name or gate_readers or acceptance or gate_badge or old_gate'
38 passed, 720 deselected in 5.64s
exit: 0

$ uv run --quiet --script scripts/sdlc.py vet --strict
■ Problems: 0
    none ✅
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
sdlc.py: error: argument cmd: invalid choice: 'check' (choose from status, new, vet, ship, …)
exit: 2

$ uv run --quiet --script scripts/sdlc.py drift
{'breaking': [], 'refresh': [], 'report': []}
exit: 0

$ ! grep -q '179 R1' tests/test_metrics.py && ! grep -q '# 183' tests/test_skills.py
exit: 0

$ test -f plugins/factory/agents/arbiter.md && test -f plugins/factory/prompts/arbitrate.md && test -f plugins/factory/prompts/land-arbitrate.md && ! test -e plugins/factory/agents/verifier.md && ! test -e plugins/factory/prompts/verify.md && ! test -e plugins/factory/prompts/land-verify.md
exit: 0

$ grep -q '^impact: minor$' .sdlc/work/187-one-word-one-meaning/intent.md && grep -q 'sdlc.py check` is now `sdlc.py vet`' docs/REFERENCE.md && grep -q 'sdlc.py vet --strict` instead' docs/REFERENCE.md && grep -q '`\[models\] verifier` is now `\[models\] arbiter`' docs/REFERENCE.md && grep -q 'setup proposes it on its next run' docs/REFERENCE.md
exit: 0

$ git log --oneline -1
d0c566a Close 186-gate-reliability
exit: 0
