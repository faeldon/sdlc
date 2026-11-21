# Plan

> How 215 is built: written after reading the agent prompts, `read_evidence()`, `is_read()`,
> `cmd_accept()` and `cmd_gate()`. Tier 1, but the Approach reaches across several files.

## Files to change

- `plugins/factory/agents/builder.md`, `reviewer-behaviour.md`, `resolver.md`: the three prompts
  that end with `## Evidence` (the other agents' `Evidence:` lines are a finding's field, not a
  section the script reads). Each asks for `exit: <n>` after every command, reads included, and
  drops "unless it is a read that shows its output". The behaviour prompt's gate-record citation
  shows its `exit: 0`.
- `plugins/factory/prompts/mend.md`, `## evidence`: says the same, and its three golden copies in
  `tests/prompts/` (`mend-builder.txt`, `mend-behaviour.txt`, `land-mend-evidence.txt`).
- `plugins/factory/README.md`, *Shown, not said*: the agents are asked for every exit; the read
  exemption stays the script's, for a reply that left one off.
- `plugins/factory/scripts/factory.py`: `cmd_accept()` checks its record is still vouched after
  `sdlc.py accept` ran, before it reads the earlier attempts, as `cmd_gate()` already does after its
  slot wait and run (nit 2026-11-20-61). The `READS` comment says the exemption is for a reply
  that left an exit off. `is_read()` and `read_evidence()` stay as they are.
- `tests/test_factory_depth.py`: the tests below.
- `tests/test_skills.py`: `test_what_runs_the_change_shows_its_evidence_and_never_runs_checks`
  pinned 123 R8's exemption wording; it now pins "every command, reads included".

Reused: `_unvouched_refusal()` for the accept re-check, with the same rewording `cmd_gate()` uses.

## Work order

1. Prompts: the wording test (red on today's prompts), then the three prompts, mend.md and its
   goldens, the README.
2. Evidence reader: the three commands from today's stops with their `exit:` lines read clean.
3. Accept: a check that rewrites `build/land-accept.md` while it runs is refused, never appended
   to (red today), then the re-check.

Nit 2026-11-20-47 (`intent_closes()` from the fork point) is not built: the fork point holds no
`intent.md` for a factory run, so the read would loosen the bar; see `notes.md` and the decision.

## Tests

- `test_no_agent_prompt_lets_a_read_leave_its_exit_off`: every `plugins/factory/agents/*.md` and
  `prompts/mend.md` holds none of the exemption's wordings, and each prompt with a `## Evidence`
  section asks for every command's exit, reads included; the behaviour prompt's gate-record
  citation shows `exit:`. Outcome bullets 1–3.
- `test_todays_stopped_commands_with_their_exits_read_clean`: the three commands from 2026-11-21's
  stops, each with `exit:`, give `read_evidence()` no problem; without the exits each is flagged,
  so the rule didn't loosen. Outcome bullet 3, the constraint.
- `test_a_record_forged_while_accept_ran_is_never_appended_to` (`tests/test_land.py`): nit 61.

## Rollback

Nothing outside the repo: `git revert` undoes it all.
