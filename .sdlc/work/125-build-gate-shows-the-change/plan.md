# 125 — Plan

> How the change is built, written after reading the code: the files, the order, the tests, and
> what a revert wouldn't undo.

## Files to change

- `plugins/factory/scripts/factory.py`: a new `build_question(...)` beside `land_question()`, pure
  (takes the values, reads nothing), and `cmd_start` sets `out["question"]` from it for
  `--for build` with no refusals (None otherwise). `cmd_start` already has everything the
  question needs but two values: the base branch's `[review] sensitive` (`_sensitive(root, base)`)
  and `[commands] check` (`_base_check(root, base)`), both read from the base branch as `depth()`
  and `gate` read them. `cfg["ui"]` is already the base branch's (`_ui()`).
- `plugins/factory/skills/build/SKILL.md`: Step 1 opens with the change quoted from `intent.md`;
  Step 2 asks `start`'s `question` literally, and the four template sentences (spec draft, none,
  restart, upgraded: the intent named three, the skill holds four) and the clause rules leave
  it, said once in `build_question()`'s docstring instead. As built: like `land`'s Step 2, the
  skill keeps the question's fullest plain form as a reference (each `WAIT` must show a question
  with its answers, `test_every_gate_offers_two_to_four_answers`), the restart and upgraded
  forms are gone, and a sentence says how the other forms differ.
- `tests/test_skills.py`: two build-skill tests pinned the template sentences and the leave-out
  rules; they now pin that Step 2 asks `start`'s `question` and that the script holds the no-gate
  form.
- `tests/test_factory.py`: tests of `build_question()` and of `start`'s `question`.
- `plugins/factory/README.md`: quotes none of the sentences; unchanged.

Reused: `_sensitive()`, `_base_check()`, `_base()`, `light_reviewers()` (via `out["light"]`),
`max_runs()`, `restart_state()`'s `archive` and `round`, `read_upgrade()`'s `round`.

## Work order

1. **The question, plain form.** Test: `start --for build` on a Tier 1 at `plan` with no config
   gives the no-spec sentence, word for word, with `, with no gate configured` and no parenthesis
   or `[ui]` clause. Then `build_question()` and the `start` field.
2. **The clauses.** Tests: with a base-branch `[commands] check` the gate clause names it; with
   `[review] sensitive` the light parenthesis appears with `start`'s `light` reviewers and
   rounds; with `[ui]`'s `serve`, `shoot` and `paths` the UI clause appears, and not with one
   missing.
   `_listed()` joins reviewers as a sentence, `no reviewer` for an empty list the config allows.
3. **The other forms.** Tests: a Tier 2 at `plan` gets the spec-draft form; an escalated change
   at `test` the restart form with its archive and round; an upgraded run the upgraded form with
   its round. A refused `start`, and `--for spec`, give `question: null`.
4. **The skill.** Step 1's opening and Step 2's literal ask; the existing skill tests
   (`test_every_wait_asks_in_a_dialog`, the allowed-tools rules) stay green.

## Tests

- Outcome bullet 2 and 4 (`question`, its forms and clauses): slices 1–3.
- Outcome bullet 3 (Step 2 asks it literally, the templates gone): an acceptance check in
  `checks.md`, since only a revert of the skill text could fail it.
- Outcome bullet 1 (Step 1 opens with the quoted intent): the same check, on Step 1's text.

## Rollback

Nothing outside git: `start` stays read-only and the change writes no data. `git revert` undoes it.
