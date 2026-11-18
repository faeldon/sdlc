I resolved the conflict in `.sdlc/work/inbox.md` by keeping every entry from both sides, and the full gate passes on the result (2451 passed, 14 skipped). I ran no git command.

As last time, both sides only added new entries after `2026-11-18-16`, with ids that don't overlap, so nothing had to be merged within an entry.

- **From this change:** `2026-11-18-17` to `-20`, unchanged. These are the items its landing carried forward: moving a stopped landing to Needs you, a step for `accept`, `/sdlc:close` for a stopped shipped card, and plain words for the remaining stop reasons.
- **From the base branch:** `2026-11-18-21` (the landing train idea) and `-22` (the bug where an agent's evidence carries the home path), unchanged. They now come after this change's entries, so the ids run in order.

On the base branch, `-22` ends at `Theme: factory`, with no `Raised` line. I left it that way, since adding one would change the base branch's text.

No conflict markers are left. The register reads as 33 entries, every id is unique, and `-10` to `-22` are all present.

## Evidence

$ grep -cE '^(<{7} |={7}$|>{7} )' .sdlc/work/inbox.md
0
exit: 1

$ uv run --group dev python -c "…m.inbox_entries(Path('.'))…"
33 True ['2026-11-18-2', '2026-11-18-11', '2026-11-18-10', '2026-11-18-12', '2026-11-18-13', '2026-11-18-14', '2026-11-18-15', '2026-11-18-16', '2026-11-18-17', '2026-11-18-18', '2026-11-18-19', '2026-11-18-20', '2026-11-18-21', '2026-11-18-22']
exit: 0

$ ./check.sh
All checks passed!
2451 passed, 14 skipped in 67.83s (0:01:07)
✔ Validation passed
exit: 0
