I resolved the one conflicted file, `.sdlc/work/inbox.md`, by keeping every entry from both sides. The full gate passes on the result (2451 passed, 14 skipped), and I ran no git command.

The conflict was only in the register: both sides added new entries after `2026-11-18-10`, with ids that don't overlap.

- **From the base branch:** `2026-11-18-12` to `-16`, unchanged. These are the triage bullet, the approver weighing defaults, round limits, the decide skill, and register-only landing conflicts.
- **From this change:** `2026-11-18-17` to `-20`, unchanged, after the base branch's. These are the items its landing carried forward: moving a stopped landing to Needs you, a step for `accept`, `/sdlc:close` for a stopped shipped card, and plain words for the remaining stop reasons.
- **The shared last line:** the `Raised 2026-11-18.` after the markers ended the last entry on both sides. I gave `-16` its own copy, and `-20` keeps the original.

No conflict markers are left. The register parses into 31 entries, every id is unique, and `-10` to `-20` are all present.

## Evidence

$ grep -cE '^(<{7} |={7}$|>{7} )' .sdlc/work/inbox.md
0
exit: 1

$ uv run --group dev python -c "…m.inbox_entries(Path('.'))…"
31 True ['2026-11-18-11', '2026-11-18-10', '2026-11-18-12', '2026-11-18-13', '2026-11-18-14', '2026-11-18-15', '2026-11-18-16', '2026-11-18-17', '2026-11-18-18', '2026-11-18-19', '2026-11-18-20']
exit: 0

$ ./check.sh
All checks passed!
2451 passed, 14 skipped in 100.99s (0:01:40)
✔ Validation passed
exit: 0
