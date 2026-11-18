DECISION: READY

**Why.** All four seeds and the nine nits in the intent are built, and both reviewers say so in round 1: `code` and `behaviour` both returned `VERDICT: PASS`. The changes that alter behaviour have tests that were seen failing before the fix: -72, -62, -57 and -56. The docs edits are covered by the three acceptance checks in `checks.md`, and `sdlc.py accept 150` passes. The round-1 gate is green (`./check.sh` exit 0, 2832 passed, 28 skipped). Neither reviewer suggests the intent itself was wrong.

**Open items.** None. Neither round-1 review asks for a change. Code's one NIT is recorded as F1 in `findings.md`: `_terms()` accepts a term that matches the empty string, such as `a*`.

**Decisions to confirm.**
- SETTLED: D1: factory.py's argument parser marks both `--round` and `--role` as required for `shots` (`p_shots.add_argument(... required=True)` at lines 7692–7693), so the bare `factory.py shots NNN` the intent wrote would be refused. `plan.md` records the switch to the full command. `test_preflight_passes_ui` checks the exact text, and both round-1 reviewers accepted it. The intent's aim was "names the command that takes them", and only the full form does that.
- SETTLED: D2: per AGENTS.md (*Nothing about a project*), `.sdlc/terms.local` is "one regex per line" with no kind to name, so a per-kind placeholder would need a new file format, which the intent never asks for. The only constraint the intent sets is that a term is never quoted, and `test_a_reply_quoting_a_local_term_is_filed_as_a_placeholder` proves it, `defuse`'s JSON output included. Code's round 1 agreed.

**For the person at ship.** Look at -72 first:
- `_terms()` and `_defused(text, root)` in `plugins/factory/scripts/factory.py`, and the `_hand_terms()` copy in `scripts/sdlc.py`. This is the one place the change reads a local, gitignored file, and it must never print a term.
- The F1 edge case: a `terms.local` line such as `a*` would put `<term>` between every character.
- `_own_folder()`'s possessive `\*?+`, which needs Python 3.11 or later.
- The AGENTS.md commands block. The builder says this is the one place where more than line breaks changed: a comment now continues on a second `#` line, and one line lost some padding spaces.

- IMPACT: patch — ship's UI pass now names the command that takes the missing screenshots, and factory replies now hide local terms. Both are improvements to existing behaviour; nothing new to do and nothing to change for someone on the previous release.

**Undone items.**
- UNDONE: `plugins/factory/agents/reviewer-code.md` and `reviewer-ux.md` keep other lines past 100 columns (each frontmatter `description`, and the "Under a decision's line" paragraph after the `supersedes` sentence -55 wrapped), outside -55's scope. → seed: Wrap the reviewer agents' other lines past 100 columns
- UNDONE: `plugins/factory/README.md` keeps about twenty other lines past 100 columns, outside -63's scope (the one paragraph it named). → seed: Rewrap the factory README's lines past 100 columns
