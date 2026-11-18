# 149-landing-resolver-agent — entries

## [2026-11-18-83] [nit] the edited *The factory* paragraph now has a very long line, 4 lines down from the reflow.

Raised by the code review of 149-landing-resolver-agent, round 1: AGENTS.md:237: the edited *The factory* paragraph now has a very long line, 4 lines down from the reflow. Re-wrap it near the 100-column width the rest of the file keeps.

Theme: style
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 149-landing-resolver-agent (correctness)

## [2026-11-18-84] [nit] in `cmd_resolve --continue`, `_stray()` runs before the register is pruned, which is what the spec says.

Raised by the code review of 149-landing-resolver-agent, round 1: plugins/factory/scripts/factory.py:6966: in `cmd_resolve --continue`, `_stray()` runs before the register is pruned, which is what the spec says. If `.sdlc/last-id` is still modified in the worktree after `_rebase_settling()`, it would count as stray. Spec R9 says it is staged, and a test covers the clean path, so I'm only flagging it. A test where a conflicting stack also touches `last-id` would settle it.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 149-landing-resolver-agent (correctness)

## [2026-11-18-85] [nit] the fence test mixes tracked and untracked strays in one flow.

Raised by the test review of 149-landing-resolver-agent, round 1: tests/test_train.py:976: the fence test mixes tracked and untracked strays in one flow. A failure message won't say which case broke, so the `refused` helper could take a label

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 149-landing-resolver-agent (correctness)
