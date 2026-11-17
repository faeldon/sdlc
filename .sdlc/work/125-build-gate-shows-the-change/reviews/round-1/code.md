VERDICT: PASS

- DECISION: [default] (D3, the builder's default) Step 2 keeps the fullest plain form as a reference, with its `<placeholders>`. The intent says the three template sentences leave the skill, and this fourth one is still a hand-fillable template. I'd keep the reference, because each WAIT must show a question with its answers (`test_every_gate_offers_two_to_four_answers`), and mark it in the skill as a form never to ask or fill in. The person should confirm this, since it departs from the intent's "templates leave the skill".

## Notes

- NIT: plugins/factory/scripts/factory.py:830: `_listed([])` returns `no reviewer`, so the sentence reads `no reviewer review it in up to 3 rounds`. The subject-verb agreement is wrong. An empty reviewer list is allowed by config, so consider wording the empty case as its own clause.
- NIT: `build_question()` writes `1 round` where the old template wrote `1 rounds`. The intent says the sentences stay word for word. `notes.md` already records this change, so it is a known, intentional departure and not a defect.
- NIT: `tests/test_skills.py` (`test_the_script_gates_each_build_before_any_reviewer`) now checks that `", with no gate configured"` appears anywhere in `factory.py`. That is a weak pin: a stray string elsewhere would satisfy it. The behaviour is already covered by the `start` tests in `tests/test_factory.py`, so the skill test could be dropped or narrowed.

What is done well:
- Each form matches the old template sentence word for word, with the same clauses and the same `more` and `again` rules. I checked each against the removed text in the skill diff.
- The `restart` and `upgraded` keys the script reads (`archive`, `round`, `upgraded.round`, `light`, `ui`) exist in `cmd_start` and `restart_state()`. The clauses are gated on what the base branch's config actually names (`_base_check`, `_sensitive`, `_ui`), not on the change's own copy, which the tests pin.
- Refusals, `--for spec` and a worktree-less change give `question: null`, and each is tested.
- Step 1's quoted-intent requirement is covered by an acceptance check in `checks.md`, and the Step 2 template removals are covered there too.
- No doc in the repo describes the build gate's wording, so no context CHANGE is needed.

Tests and commands run:
- `uv run --group dev pytest -q -p no:cacheprovider tests/test_factory.py tests/test_skills.py tests/test_defaults.py`: 742 passed.
- `ruff check` and `ruff format --check` on the three changed Python files: clean.
- Not run: the full `./check.sh` gate, `claude plugin validate --strict`, and the `checks.md` acceptance blocks. I did confirm by reading that their grep targets match the current skill text.
