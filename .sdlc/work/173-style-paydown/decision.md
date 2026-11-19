Everything checks out, so I'm writing up the recommendation now.

DECISION: READY

**Why.** All four reviewers (code, security, test, behaviour) passed in round 1, and the gate is green: `./check.sh` exit 0, 3065 passed, 28 skipped, tree unchanged. Every outcome in the intent is met: the named lines are rewrapped with every word kept in order, `check.sh` answers -76, and `function-heat.py` gets -108's comment. The only edits to `check.yml` (a sensitive path), `check.sh` and `function-heat.py` are comments. The one open default can be settled from the intent itself.

**Open items**
- None. No CHANGE findings are open. The three NITs are minor or recorded in `findings.md` (code F1, test F2, test F3).

**Decisions to confirm**
- SETTLED: D1: the intent's Outcome asks each named line to wrap near 100 columns "as its file does", and its Constraints say "Rewrap only" and "No behaviour changes". Every agent file keeps its frontmatter `description:` on one line, and the harness reads that value, so wrapping it would change what Claude Code parses rather than rewrap prose. The round-1 code and security reviews both agree with this default, and `checks.md` leaves `description:` lines out on purpose.

**For the person at ship**
- Start with `.github/workflows/check.yml`. Confirm only the header comment (lines 1–6) moved and `on:`, permissions and jobs are byte-identical.
- Then read the two new comments, `check.sh`:11–12 and `.sdlc/function-heat.py`:124. They are the only new words in the change.
- The behaviour review saw 39 added lines in `.sdlc/work/inbox.md` in its `git diff <merge-base>`. The worktree's register has the same `2026-11-19-*` entries, on the same lines, as the main checkout's. So these look like `File` commits on the base, not a register edit carried on this branch. `round-1.files` doesn't list the register either. Worth a glance at `git status` before the commit.
- Expect a large diff in `AGENTS.md` and `plugins/factory/README.md`. The builder and two reviewers checked that the whitespace-collapsed text matches `HEAD`'s.

- IMPACT: none — only comments and line breaks changed. No command, config key, agent instruction or CI step behaves differently for anyone who has the previous release.

**Undone items**
- UNDONE: The other factory agents (`approver.md`, `builder.md`, `resolver.md`, `reviewer-behaviour.md`, `reviewer-security.md`, `reviewer-test.md`, `reviewer-ui.md`, `spec-writer.md`, `verifier.md`) keep prose lines past 100 columns; no entry named them, so they stayed out of this change. → seed: Rewrap the remaining factory agents' prose lines past 100 columns
- UNDONE: `plugins/factory/README.md` keeps table rows past 100 (the agents table, the run-log table) and fenced lines (the diagram, the folder listing): a markdown row can't wrap, so only rewording would shorten them. → dropped: a markdown table row and a fenced block can't wrap, and rewording them only to fit a column limit isn't worth a change
- UNDONE: `AGENTS.md` keeps a few short lines mid-paragraph outside the paragraphs the nits named (*Retrospectives*' "so `retro` is", the skills invariant's "is literally"). → dropped: purely cosmetic, no line goes past 100, and the next edit to those paragraphs can refill them
