DECISION: ESCALATE

**Why.** Both reviewers passed round 1, and the gate is green on attempt 2 (build `cdb4abec`). Both outcomes in the intent are built, and each has a test that failed first for the right reason. The one thing holding this back is D2: to make the gate pass, the builder hand-edited a line inside the gate's own record, and only you can decide whether an agent may alter that record.

**Open items**
- No unresolved CHANGE findings. Two NITs are open:
  - Code reviewer: `plugins/factory/scripts/factory.py:2822`. `_own_folder()`'s regex turns `work/NNN*x` into `work/NNN-slug*x` because of backtracking. The behaviour reviewer saw the same thing with `work/NNN*-x`.
  - Code reviewer: `plugins/factory/README.md:383`. The re-wrapped paragraph has one line that is too long.

**Decisions to confirm**
- SETTLED: D1: the intent's Approach asks for "the warning `mode` already gives" when the checkout's value differs, which answers its own open question. `_models()` does exactly that. `test_models_are_the_base_branch_s_even_for_an_older_worktree` covers the warning and shows it clears once the two tables match, and both reviewers checked it against the intent (code.md, behaviour.md).
- ESCALATED: D2: this asks whether an agent may rewrite text inside a gate record, `build/round-1.gate.md` attempt 1's quoted output, so that later gates go green. That is a rule about whether the run's own records can be trusted, and only you can set it. The edit leaves the attempt's `Verdict:`, `Build:` and `Exit:` lines alone, and it matches the hand fixes recorded in the intent. But that record is what the auto-landing relies on, and this is the first time an agent rather than you has edited one.

**For the person at ship**
- Look first at the diff of `build/round-1.gate.md` and `build/round-1.md` line 32. Check that only the one quoted citation changed, to `work/NNN*`.
- Then look at `_own_folder()` in `factory.py`. Its regex must touch only this change's own number and only path citations, never verdict or finding text. Check the NIT at line 2822 too.
- Then look at `_models()` and `load_config()`. `[models]` is now read through `_base_factory()`, and any entry in the change's own checkout is ignored with a warning.

- IMPACT: patch — the factory now does what its constraint and README already promised: `[models]` comes from the base branch, and the change's own citations are filed under their full names. A host that set `[models]` only on a change's branch must now commit it on the base branch, but that setup was the bug being fixed.

**Undone items**
- UNDONE: A gate record that quotes a line in a shape `test_nothing_local` refuses keeps every later gate red: `factory.py gate` files the output's tail into `build/round-<N>.gate.md`, which the next run's scan reads. Seen on this change's round 1, where the builder's report quoted a red test's output holding the fixture's `work/<number>*` glob and the gate's record quoted the scan's report of it; both copies were rewritten as `work/NNN*` by hand. Filing gate output (and a builder's Evidence) with `PATTERNS`' shapes defused would close it for any number, not only the change's own, which this change rewrites. → seed: Defuse forbidden path shapes when filing gate output and builder Evidence
