VERDICT: CHANGES

- CHANGE: AGENTS.md:434: the factory paragraph says `verdicts` "decides from the rounds alone and never reads a state file", but the change makes `verdicts` read `runs/mended`, and the same paragraph (around line 441) now says `runs/mended` is "the one file a run writes that `verdicts` reads back". A policy doc can't hold both. Reword the line at 434 to name the exception, e.g. "`verdicts` decides from the rounds alone, bar `runs/mended` (the mends filed, read so a role is mended once a round; depth never comes from it)", and keep the depth reason, which still holds. Then rewrap the 437–443 paragraph while there.

## Notes

- Nit: `plugins/factory/skills/build/SKILL.md`, the `way` sentence in the `stop` step, still breaks after a dangling "with". Both earlier reviews flagged it and it's still there. Rewrap it with the AGENTS.md paragraph.
- Optional: `preamble()` counts any later line that matches `VERDICT:` as a verdict, so a reply that quotes the verdict format in its body is mendable as a preamble. The mend asks the reviewer to put its own line first, so the harm is small. Matching only the reviewer's `- CHANGE:` / verdict block would tighten it, but this isn't needed to land.
- Optional, carried from earlier rounds: a `behaviour` reply missing both its verdict and `## Evidence` gets only the verdict mend. It then stops as `rerun`, which is safe. Naming the evidence in `VERDICT_MEND` would make the mend finish the job.

## Done well

- The land-1 conflict resolution is right. Against `main`, `inbox.md` loses only the two `fixes:` entries (`-17`, `-18`): 30 entry headings on `main`, 28 on the branch. The six base-branch entries (`-19`, `-22` to `-26`) are intact, and no line still names `-17` or `-18`.
- `_as_written()` strips only the resolved `after`. `fields["After"]` keeps the line as written, so a real edit to `After:` is still an `Update`. The test covers both cases.
- `_go_on()` skips only when nothing is unmerged and both the index and the worktree match `HEAD`, so a non-empty step still refuses. The non-empty aside is still undone; the test checks it.
- `runs/mended` is written only after a reply is written, so a failed session records nothing and stays retryable. `loop_state()` and `cmd_agent()` both read the same `mended()`, so they can't disagree about what's mended.
- The mend test walks the whole chain: preamble → mend → `approve` → preamble again → `rerun` with `mend: []` and a refused second mend, with no new `claude` call.
- Commit `de128bf` carries only the plugin's `Sdlc-*` trailers and no agent attribution. The diff contains no `Claude`, `Anthropic` or co-author lines.

## What I ran

- I read the diff against `main`, the intent, the plan, D1–D3 (settled, so not raised again), the two earlier reviews and the verifier's note.
- I ran no tests in this session. I'm relying on the land-1 gate record: `./check.sh` at `de128bf` passed with 1956 tests, and the tree was unchanged. The gate doesn't cover the AGENTS.md contradiction above, which is why it's a CHANGE.
