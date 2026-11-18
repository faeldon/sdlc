DECISION: ESCALATE

**Why.** The build looks complete. All three reviewers passed in round 1 and the gate is green: 2601 tests passed, `drift` is clean and `check --strict` reports nothing. Every requirement from R1 to R23 has a named test, and R22 and R24 were read and found to match. I'm escalating for two reasons. D1 is a policy call that the spec deliberately left open ("How a hand-built change comes to have shots is left open below"). And the change touches published interfaces: it adds `passes=` and `passes_wrong=` to the metrics trailer, adds `ship-*` `By:` values and note lines to the `findings.md` format, and makes a policy edit to AGENTS.md's *Ship* and factory paragraphs.

**Open items**
- None blocking. Three code-review NITs are already in `findings.md`. F1 and F2 are wording fixes in `skills/ship/behaviour.md:3` and `skills/ship/security.md:3`, both `recorded`. F3 is the repeated `_passes_report()` calls, marked `minor`. All three were raised by the code reviewer.

**Decisions to confirm**
- ESCALATED: D1: the spec leaves open how a hand-built change gets its screenshots. Whether ship should ever point someone at `factory.py shots`, a command that starts a dev server, is a question of policy and scope. The builder already passed it to the person ("once the person decides" in `notes.md`), so neither the spec nor the code nor a review round answers it.

**For the person at ship**
- Look first at `scripts/sdlc.py`:
  - `_passes_report()` and `_ui_at()`: check that `[ui]` is read from `refs/heads/<trunk>` and that no pass applies when `decision.md` exists.
  - `_current_shots()`: how it decides a set is stale.
  - The refusal loop in `cmd_ship()`.
  - `findings_trailer()`: check that nothing changes before `agents=`.
- Then the AGENTS.md policy edit (R24). It changes "the core plugin's one agent" and the list of factory files `sdlc` reads.
- The behaviour reviewer saw preflight report `behaviour.md` but never ran the question's pass and skip wording by hand. That wording rests only on `test_the_question_names_the_passes`.

- IMPACT: minor — a host's `/sdlc:ship` can now run security, behaviour, UI and UX passes on a hand-built change. The trailer and `findings.md` format only gain new parts, and an old findings file keeps its trailer byte for byte.

**Each undone item's disposition**
- UNDONE: Say in `ui.md`, or in `passes.ui.why` when `sdlc-factory` is enabled, how a hand-built change takes its screenshots (`factory.py shots`), once the person decides whether ship should point at a command that starts a dev server. → seed: Tell a hand-built change how to take screenshots for ship's UI review

**How to recover**
- RECOVER: templates/findings.md: fix forward: `git revert` puts the template back, but hosts keep the `findings.md` files and `Close` trailers already committed from it: the four note lines, `By: ship-*`, `## Evidence` and `passes=`. The follow-up would keep `FINDING_BY` accepting `SHIP_PASSES`, keep `_findings_from_text()` skipping `## Evidence`, and keep retro reading `passes=`/`passes_wrong=`, so that history still parses. It would also update `FINDINGS_HEAD` in `factory.py` to match.
