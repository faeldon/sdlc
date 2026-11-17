# 094 — Plan

> The build's plan, written after reading the code: what changes where, in what order, which test
> proves which outcome, and what a revert wouldn't undo.

## Files to change

- `scripts/sdlc.py`
  - `_inbox_commit()`: compare entries through a new `_as_written(entry)`, the parsed entry without
    its resolved `after` (its `fields["After"]` still holds the line as written, so a real edit to
    `After:` is still an `Update`). Used for both comparisons: `before`/`after` from the main
    checkout, and `was`/`now` in a worktree. `parse_entries()` is left alone.
  - `cmd_resolve()`: a new `_go_on(tree, env)` replaces both `git rebase --continue` calls (the
    `--continue` path and `step()`'s loop). When git won't go on, nothing is unmerged and the
    index and worktree both match `HEAD` (the step has nothing of its own left), it runs
    `git rebase --skip`. Git's default merge backend already drops such a commit; the apply
    backend (`rebase.backend = apply` in a host's config) answers "No changes", which is the stop
    nit 2026-11-17-11 describes.
- `plugins/factory/scripts/factory.py`
  - `_no_verdict(n, role)`: the problem's words, shared by `read_rounds()` and `loop_state()`
    (unchanged text, which the board and status show).
  - `preamble(path)`: a reply whose first line isn't a verdict but a later line is one.
  - `loop_state()`: the last round's preamble replies join the missing `## Evidence` as mendable:
    `way` is `mend` when every problem is one of them; new `mend` key, the roles to mend.
  - `_task()` (mend) and `cmd_agent()`: `--task mend --role <reviewer>` on a preamble reply
    resumes that reviewer's last session (`runs/reviewer-<role>.sessions`) with `VERDICT_MEND`,
    the reply written over the old one. A builder or behaviour evidence mend is as before.
  - `WAYS["mend"]` and `cmd_verdicts()`'s docstring name the new mend.
- `plugins/factory/skills/build/SKILL.md`: the `stop` step names both mends and `mend`'s roles.
- `runs/mended` (new, in the change's folder): the mends filed, `<role> <round>` a line.
- `AGENTS.md`: the factory paragraph says a preamble reply is mended once.

Reused: `parse_entries()`, `_rebasing()`, `_unmerged()`, `VERDICT_RE`, `read_evidence()`,
`agent_name()`, the sessions files `cmd_agent()` already writes.

## Work order

1. Inbox: test retiring an entry another's `After:` names (red), `_as_written()` (green).
2. Resolve: test a branch commit the base already holds, under the apply backend, resolved
   through with the aside commit still undone (red), `_go_on()` (green).
3. Factory: test a preamble reply → `verdicts` stop `mend` with `mend: [code]` → `agent --task
   mend --role code` resumes the reviewer's session and writes over the reply → `verdicts` reads
   the round (red), then the code, the skill and AGENTS.md.
4. Rework, round 1 (code C1): "once" is the script's, not only the skill's. `cmd_agent` appends
   `<role> <round>` to `runs/mended` when it files a mend (`mended()`, `mend_round()`: the
   builder's round is its report's, any other role's the last review round); `loop_state()` drops
   a role already mended that round from what's mendable, so the stop is `rerun`, and `agent`
   refuses a second mend. It covers the builder's evidence mend too.

## Tests

- `tests/test_bugs.py::test_inbox_commit_retires_an_entry_another_waits_on`: Outcome 1 (subject
  `Retire <id>` alone, `entries`), and an edited `After:` line still an `Update` (Outcome 2).
- `tests/test_sdlc.py::test_resolve_skips_a_commit_the_base_already_holds`: Outcome 3, the aside
  commit undone at the end, the empty commit gone, the other commit kept.
- `tests/test_factory.py::test_a_reviewer_s_preamble_is_mended_by_the_same_reviewer`: Outcome 4,
  a mend refused for a reviewer whose reply already opens with its verdict, and a second preamble
  after the mend read as `rerun`, its mend refused.
- `tests/test_factory.py::test_the_builder_s_evidence_is_mended_once_a_round`: the same marker
  holds the builder's evidence mend to once a round.
- `tests/test_skills.py::test_what_runs_the_change_shows_its_evidence_and_never_runs_checks`: its
  pinned sentence of the build skill's `stop` step follows the new wording (both mends, and never
  writing the evidence or the verdict).
- `tests/test_factory.py::test_a_stop_names_its_way`: unchanged, a reply with no verdict at all
  still `rerun`: only a reply that holds a verdict after a preamble is mended.

## Rollback

Nothing outside git: `git revert` undoes it all.
