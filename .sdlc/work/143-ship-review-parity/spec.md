---
id: 143
slug: ship-review-parity
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 143 — Ship reviews a hand-built change as deeply as the factory reviews its own · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

What this design takes as given, each checked in the code:

- Ship decides nothing about its rarer steps itself. `SHIP_BRANCHES` in `scripts/sdlc.py` names each side file from `preflight`'s parts, and `test_ship_branches_condition` (`tests/test_preflight.py`) pins each condition.
- The one core agent today is `agents/reviewer.md` (`sdlc:reviewer`). It has exactly `Read, Grep, Glob`, pinned by `test_sdlc_s_reviewer_reads_and_nothing_more`.
- `[ui]` lives in the base branch's `.sdlc/factory.toml` (`factory.py`'s `_ui()` and `_base_factory()`). A UI review needs `serve`, `shoot` and `paths` (`ui_complete()`). The factory joins its UI reviewers when the diff touches `[ui] paths` (`ui_review()`, through `risk_paths()`).
- `factory.py shots` writes PNGs and a `shots.json` under `.sdlc/reports/shots/<change>/<label>/<role>/`. `problem` is null there only when every shot was written (`shots()`).
- `findings.md`'s `By:` is checked against `FINDING_BY = ("fresh", *AGENT_ROLES)`. `AGENT_ROLES` is pinned to `factory.py`'s `REVIEWERS`. `ship_findings()` counts only `By:` absent or `fresh` as ship's own.
- `sdlc.py ship` refuses a deep diff whose note doesn't say whether the fresh review ran (`cmd_ship`, from `FRESH_RE` and `_note_says()`).
- Ship's `SKILL.md` is held to 475 lines by `test_ship_s_skill_stays_under_its_budget`, and is at that budget now.

R1. `preflight` gains a `passes` part: `{"security": {...}, "behaviour": {...}, "ui": {...}}`, each with `applies` (bool) and `why` (text or null). `ui` covers both the UI and the UX review, which share one set of screenshots. A test per entry fails if `applies` holds when its condition doesn't, or fails to hold when it does: `test_preflight_passes_security`, `test_preflight_passes_behaviour`, `test_preflight_passes_ui`.

R2. `passes.security.applies` is true exactly when `risk.deep` is true and the change's folder has no `decision.md`. A deep factory-built change, and a shallow hand-built one, each give false.

R3. `passes.behaviour.applies` is true exactly when the change is Tier 2, its `spec.md` is filled (not `is_unfilled()`), and its folder has no `decision.md`. A Tier 1 change, an unfilled spec and a factory-built change each give false.

R4. `passes.ui.applies` is true exactly when all three hold:
- the base branch's `.sdlc/factory.toml` holds a complete `[ui]`;
- the diff against the base touches one of its `paths`, matched by `risk_paths()`;
- there is no `decision.md`.

`[ui]` is read from `refs/heads/<trunk>`, never the checkout. `test_ui_is_read_from_the_base_branch` fails if a change that removes or narrows `[ui]` in its own checkout turns its UI review off.

R5. `sdlc.py`'s copy of `ui_complete()`, and the handful of `[ui]` keys it reads (`paths`, `pages`, `widths`), are pinned to `factory.py`'s by a test in `tests/test_hand_gate.py`, beside the gate-slot copies. It fails when either side changes alone.

R6. When `passes.ui.applies`, `passes.ui` also lists `shots`: the newest screenshot set it finds under `.sdlc/reports/shots/<change>/*/{ui,ux}/`, as repo-relative POSIX paths. A set counts only when all three hold:
- its `shots.json` parses with `problem: null`;
- every PNG it names exists;
- the set is current: `shots.json` is newer than every changed path under `[ui] paths` in the checkout.

When no set qualifies, `shots` is empty and `why` says which of the three failed (for example, `no screenshots of this change`, or `screenshots older than web/drafts.css`). `test_stale_shots_are_not_current` fails if touching a changed path after the shots leaves them listed.

R7. `SHIP_BRANCHES` gains three entries, in this order after `fresh.md`:
- `security.md` when `passes.security.applies`;
- `behaviour.md` when `passes.behaviour.applies`;
- `ui.md` when `passes.ui.applies`.

`test_ship_branches_condition` gains a row for each, and `test_ship_branches_are_the_files_beside_ship` passes with the three new files present.

R8. Three new core agents. Each has tools exactly `Read, Grep, Glob`, a `name` equal to its file's stem, and a description over 80 characters that says `Not for`. Each returns its findings in `findings.md`'s section shape, with its pass one of the existing four.
- `agents/security.md` (`sdlc:security`): STRIDE from the trust boundaries the diff touches, as `reviewer-security` reviews them, without its Bash. Returns `By: ship-security`.
- `agents/ui.md` (`sdlc:ui`): the screenshots against the repo's styling. Returns `By: ship-ui`.
- `agents/ux.md` (`sdlc:ux`): the task, states, words and reach. Returns `By: ship-ux`.

`test_ship_s_agents_read_and_nothing_more` fails if any of the three gains a tool or loses its `By:` value. Any text adapted from `addyosmani/agent-skills` keeps the `Adapted from addyosmani/agent-skills (MIT)` line, and the notice is reachable from the core plugin. `test_adapted_agents_keep_the_notice` gains the core agents.

R9. `FINDING_BY` gains `SHIP_PASSES` as `ship-security`, `ship-behaviour`, `ship-ui` and `ship-ux`. `ship_findings()` counts these as ship's own, and the `agents=` key never counts them. `test_the_trailer_never_counts_an_agent_finding` gains a `By: ship-security` finding and fails if it lands in `agents=` or is missing from the rank and pass keys. `AGENT_ROLES` is unchanged, so its pin to `REVIEWERS` still holds.

R10. `findings_trailer()` appends two keys after `agents=` and changes no existing key:
- `passes=`: each ship pass's finding count, as `security:<n>` and so on for the nonzero ones, or `0`;
- `passes_wrong=<n>`.

`test_an_old_findings_file_keeps_its_trailer` fails if a file with no `ship-*` finding gets any change before `agents=`.

R11. `findings.md`'s note gains four lines, each `ran` or `skipped, <why>`, read by `_note_says()` with a regex each:
- `Security review:`
- `Behaviour check:`
- `UI review:`
- `UX review:`

`sdlc.py ship` refuses, saying which line is missing, when a pass applies (R2–R4) and its line is absent. A test per line fails if `ship` stamps without it: `test_ship_refuses_a_security_pass_unsaid`, `test_ship_refuses_a_behaviour_check_unsaid`, `test_ship_refuses_a_ui_review_unsaid`, `test_ship_refuses_a_ux_review_unsaid`.

R12. A pass that can't run is no stop. With its note line saying `skipped, <why>`, `ship` stamps, and the question names the skip (R14). `test_a_skipped_ui_review_still_ships` fails if `UI review: skipped, no current screenshots` makes `ship` refuse.

R13. The behaviour check's evidence lives in `findings.md` as a final `## Evidence` section. Each command is a `$ <command>` line, then the tail of its output, then `exit: <n>`. `_findings_from_text()` reads that section as evidence, never as a finding: it isn't a `problems` entry, and it is returned as `evidence: [{"command", "exit"}]`. It reports a problem in two cases:
- a `$` line with no `exit:` before the next `$` line or the end;
- `Behaviour check: ran` with no evidence command.

`test_behaviour_evidence_is_read_not_counted` fails if `## Evidence` is reported as a malformed finding, or if a command without its exit passes.

R14. `ship_question()` names each pass that applies:
- the ones that ran, as one clause: `after the security review, the behaviour check and the UI and UX reviews`, only those that ran;
- each skip as `without the <pass> (<why>)`, as the fresh review's skip is worded today.

With no pass applying, the question is byte-for-byte what it is today: every existing `ship_question` test passes unchanged. `test_the_question_names_the_passes` fails if a pass that ran or was skipped is left out.

R15. `skills/ship/behaviour.md` tells the session three things:
- take the end-to-end path from the spec's requirements and `## Verification`, leaving out the gate, which Step 1 already ran;
- show each command before running it, with no `Bash(...)` rule added for it, so the person answers its prompt, as `accept` is run;
- never run a `checks.md` command, which Step 1's `accept` runs.

Each failure the path shows is a `[correctness]` finding with `By: ship-behaviour`. Any path the run leaves in the working tree is named in the evidence and in Step 4, and is removed or `--leave`d before Step 6. Ship's `allowed-tools` gains no rule: `test_ship_s_rules_are_used` and the rule-coverage tests still pass, and `test_behaviour_check_never_runs_checks` fails if `behaviour.md` names `accept` or `checks.md`'s commands as its own.

R16. `skills/ship/security.md` has the session spawn `sdlc:security` beside `sdlc:reviewer`, in the same message. `skills/ship/ui.md` has it spawn `sdlc:ui` and `sdlc:ux` with `passes.ui.shots` and the changed paths. With no shots, `ui.md` writes the two skip lines, using `passes.ui.why`. Each prompt holds only the diff, the folder, the review doc paths and, for UI, the screenshots: nothing of the session's reasoning, as `fresh.md` does. Each finding returned is confirmed or proposed `wrong` with a `Reason:`, never dropped. A `test_skills.py` test per file fails if its `subagent_type` is missing.

R17. `SKILL.md` names the three new side files in Step 3, and in Step 7's report says which passes ran. It grows by no net line: `test_ship_s_skill_stays_under_its_budget` (475) passes with the budget unchanged. The phrase `fresh-context review too,** in \`fresh.md\`` stays, for `test_sdlc_s_reviewer_reads_and_nothing_more`.

R18. `retro`'s `_review_sources()` orders the sources `ship`, `fresh`, then `SHIP_PASSES`, then `AGENT_ROLES`. `test_review_sources_split_ship_from_the_agents` gains a `ship-security` finding and fails if it is counted under `ship` or under a factory role.

R19. Every `skills/ship/*` command, `factory.md` included, behaves as before on a factory-built change. `test_ship_reads_the_agents_verdicts` and the factory carry tests pass unchanged, and preflight names none of the three new branches when `decision.md` exists (R2–R4).

R20. `guide/review.md`'s *Review dimensions* says who covers each dimension at ship:
- **security:** `sdlc:security` on a sensitive path;
- **end-to-end:** the behaviour check on a Tier 2 with a spec;
- **ui** and **ux:** `sdlc:ui` and `sdlc:ux` with the factory's `[ui]` set and current screenshots, otherwise skipped with why.

`fresh-eyes` names the new agents. `sdlc.py record` is run, and the gate fails while `sdlc.py drift` reports anything.

R21. `templates/findings.md`'s note names the four new note lines, the `ship-*` `By:` values and the `## Evidence` section. `tests/test_defaults.py` passes, with every `<…>` prompt still inside a `##` section.

R22. `docs/REFERENCE.md`'s *Risky paths* section and the paragraph on `findings.md` describe the new passes: their conditions, the note lines, the `By:` values, the trailer's `passes=` keys, and that `[ui]` and the screenshots are read from the base branch and `.sdlc/reports/shots/`.

R23. A ship eval case, `evals/ship-behaviour/`, holds a Tier 2 fixture with a filled spec. Its grader checks that `behaviour.md` is read, that `findings.md`'s note says `Behaviour check:`, and that nothing is committed or pushed. `tests/test_evals.py` builds it and runs `check --strict` on it. The existing `evals/ship` case still reads no branch file (`never-reads-a-branch.md`).

R24. `AGENTS.md`'s factory paragraph and its *Ship* paragraph change to say what this design needs. This is the policy edit flagged under *Contracts touched*, and lands only on the person's approval of this spec.

## Design

**Who decides which pass runs: the script.** `cmd_preflight()` gains one part, `passes`, built by a new `_passes_report(root, path, parts)`. It reads three things it already has (`parts["risk"]`, `rec["tier"]`, and whether `decision.md` exists) and one new thing: `_ui_at(home, trunk)`. That function reads the base branch's `.sdlc/factory.toml` by `git show refs/heads/<trunk>:.sdlc/factory.toml`, as `_gate_jobs_at()` does, and returns the `[ui]` table's `paths`, `pages` and `widths`, plus whether it is complete. A missing file, one that won't parse, or an incomplete table means no UI review, with `why`. Whether `sdlc-factory` is enabled (`factory_enabled()`) words the `why` when shots are missing ("sdlc-factory isn't enabled, so no screenshots can be taken"). It never decides `applies`: a host that set `[ui]` is told its UI review was skipped, never left unaware of it.

**Screenshots: read, never taken.** `_current_shots(checkout, change, ui, changed)` globs `.sdlc/reports/shots/<change>/*/ui/shots.json` and `*/ux/shots.json` in the change's checkout. It parses each with a copy of the one key it needs (`problem`), and keeps the sets whose PNGs (`<page>-<w>x<h>.png`, `_page_name()`'s shape, copied and pinned) all exist. A set is current only when its `shots.json` mtime is later than every changed path under `[ui] paths`. A rebase rewrites those files, so it leaves the set stale, which errs toward a skip with why. The newest current set wins. `sdlc.py` never starts a server or runs `[ui] shoot`. How a hand-built change comes to have shots is left open below.

**Branches.** Three lambdas join `SHIP_BRANCHES`, each reading `parts["passes"][<name>]["applies"]`. Ship reads only the files preflight names, so a skill can't decide to run, or skip, a pass.

**The three side files.** Each holds its `## Step 3`, and for some a `## Step 4`, rule, as `fresh.md` does.
- `security.md`: spawn `sdlc:security` in the same message as `sdlc:reviewer`, so a deep diff pays one wait for two reviews. Then write `Security review: ran`, or `Security review: skipped, <why>` when the agent can't run.
- `behaviour.md`: read the spec's requirements and `## Verification`, and name the end-to-end path (the commands a person would run, and the output each requirement says they'd see), leaving out `commands.check`. Show the list. Note `git status --short` before. Run each command, then take `git status --short` again. Each failure against a requirement becomes a finding, `By: ship-behaviour`. Then write `Behaviour check: ran`, and the `## Evidence` section last in `findings.md`. A spec that names no runnable path is `Behaviour check: skipped, the spec names no path to run`, said in Step 4.
- `ui.md`: with `passes.ui.shots` non-empty, spawn `sdlc:ui` and `sdlc:ux` in one message, each given the shots and the changed paths. Otherwise write both skip lines with `passes.ui.why`.

**Findings.** The agents return sections in `findings.md`'s shape, as `sdlc:reviewer` does, `By:` naming them. A security finding takes the `contract` pass and a UI, UX or behaviour finding takes `correctness`, as *Review dimensions* already tags them, so `FINDING_PASSES` and every trailer key built from it are untouched. `FINDING_BY` becomes `("fresh", *SHIP_PASSES, *AGENT_ROLES)`. `ship_findings()` keeps `None`, `fresh` and `SHIP_PASSES`. The new `By:` values carry a `ship-` prefix so they never collide with a factory role of the same word, which `AGENT_ROLES` (and `board.py`'s `REVIEWER_ROLES`) already use for the factory's findings.

**The note and the refusal.** Four regexes beside `FRESH_RE` (`SECURITY_RE`, `BEHAVIOUR_RE`, `UI_RE`, `UX_RE`) are read by `_note_says()`, into `findings_entries()`'s new `passes` key. `cmd_ship` gets one loop beside the fresh-review refusal. It runs `_passes_report()` again, since the diff could have changed since preflight, and refuses for each applying pass whose line is `None`.

**The question.** `cmd_ship_question` passes `found["passes"]` and the `passes` part to `ship_question()`. It adds a clause for the passes that ran and one per skip, after the fresh-review clause and before `irreversible`'s. Every existing call site passes nothing new, so every pinned wording stands.

**Evidence parsing.** `_findings_from_text()` treats a `## Evidence` heading as the start of the evidence block: it isn't checked against `FINDING_RE`, and it holds no finding keys. Its `$ ` and `exit:` lines are paired in order, and fenced output is already skipped by the existing `FENCE_RE` handling. A `## ` line after `## Evidence` is read as a finding heading again, so a finding written after the evidence still parses. The rule is that evidence comes last, and the template note says so.

**Edge cases.**
- A change that is Tier 2, deep and renders a page gets all four passes: three agents and the session's own check.
- A Tier 1 change touching nothing sensitive and no `[ui]` path gets none, and ship reads as it does today.
- An agent that fails is a `skipped, <why>` line, the same as the fresh review's.
- A factory-built change gets none of the new branches. Its own reviewers' findings arrive through `carry`, as now.

## Contracts touched

- **Mechanism vs. judgment; branches are the script's call** (*Ship*: "what only some runs need is a side file `preflight`'s `branches` names"). Every condition is in `_passes_report()`. The side files say how to run a pass, never whether.
- **Risk is matched by the script, read from the base branch** (*Ship*). `review.sensitive` still decides `deep`, and `[ui] paths` are matched by the same `risk_paths()`. Both are read from `refs/heads/<trunk>`, so a change can't lighten its own review (R4). Risk still never changes a tier.
- **The core plugin's one agent has nothing that writes** (*Ship*: "`agents/reviewer.md` (`sdlc:reviewer`), the core plugin's one agent, with `Read`, `Grep` and `Glob`"). The three new agents have exactly those tools (R8). The behaviour check, which must run commands, is the session's own, each command behind the person's prompt as `accept` is, so no core agent gets Bash. **That sentence stops being true as worded ("one agent")**: R24 rewrites it.
- **sdlc reads only named factory files** (*The factory*: "`sdlc` only reads the files a run leaves in a change's folder, and the base branch's `gate_jobs` and the gate slots' lock files"). **This design needs that list to grow, loudly.** It adds the base branch's `[ui]` in `.sdlc/factory.toml` and the screenshot records under `.sdlc/reports/shots/<change>/`, each read with pinned copies of `factory.py`'s parsing (R5, R6). `sdlc.py` never runs `factory.py`, and loads nothing from `plugins/` (`test_sdlc_loads_nothing_from_plugins` unchanged). This is a policy edit and needs the person's yes. It is R24.
- **One WAIT, its question from `preflight --question`; ship never pushes.** There is no new WAIT, and every new clause is worded by `ship_question()` (R14). No `push` is added anywhere.
- **Writes before a WAIT: four, named.** No fifth: the behaviour evidence goes into `findings.md`, already a named write that decides nothing (R13). Commands the behaviour check runs are the person's to allow, prompt by prompt, as acceptance checks are.
- **Narrow `allowed-tools`.** No rule is added. The behaviour commands sit in no bash block, so the rule-coverage tests have nothing new to cover (R15).
- **`No agent but the builder runs checks.md`.** No new agent runs anything, and `behaviour.md` never runs `checks.md` (R15).
- **A finding counted for the wrong reviewer** (`.sdlc/REVIEW.md`). The `ship-*` values are ship's, counted by every key but `agents=`, and pinned by R9. `AGENT_ROLES` is unchanged, so its pin to `REVIEWERS` holds.
- **The metrics trailer: extend, never redefine.** `passes=` and `passes_wrong=` come after `agents=`. Old keys keep their meaning, and an old-shaped file's trailer is byte-identical (R10).
- **Guide edits and `.sdlc/setup.json`.** R20 edits `guide/review.md`, so the change runs `scripts/sdlc.py record` from its own checkout. `.sdlc/REVIEW.md` gains nothing, since an answer any repo could use goes into the guide.
- **Skill side files.** The new files hold no frontmatter, gate, commit or `sdlc.py ship`, and `SKILL.md` names each (R7, R17). The line budget holds (R17).
- **Windows.** No new subprocess is added. `shots.json` and the PNGs are read with `encoding="utf-8"`, mtimes come from `Path.stat()`, and every path shown is `as_posix()`. The tests that need no shebang fake are marked `portable`.
- **Nothing local.** The fixtures use `reopen-drafts`-style examples, and screenshot fixtures are tiny PNGs written by the test.

## Alternatives rejected

- **Borrowing the factory's reviewers when `sdlc-factory` is installed.** They return `VERDICT:` and `CHANGE:` lines for `factory.py` to file into `reviews/round-N/`, read `decisions.md`, and speak of rounds a hand-built change doesn't have. `reviewer-security` and `reviewer-behaviour` carry Bash. Ship's depth would also hang on whether a second plugin is installed. Core agents in `findings.md`'s shape are the same lenses, in the shape ship already reads.
- **One fresh reviewer covering security too.** This would be the cheapest option: no extra paid call. But the reviewer's job is the guide's passes, and one prompt holding five lenses dilutes each, which is why the factory splits them. The two run in one message, so the cost is tokens, not wall time.
- **The behaviour check as a core agent with Bash.** That gives the core plugin an agent that can write, against the constraint. The session running the spec's commands behind the person's prompts has the same evidence and keeps every write the person's to allow.
- **`sdlc.py` taking its own screenshots.** That would put a second copy of `shots()`'s server and port handling in the core plugin, and the core would start a dev server. Reading what `factory.py shots` left keeps one owner for that machinery.
- **A `[review] boundaries` key for trust boundaries.** That would be a second list for what `review.sensitive` already means: paths whose changes need the deep review, which the security pass is part of. It would also be one more key for setup to ask about and `drift` to track.
- **New finding passes (`security`, `ui`, …) in `FINDING_PASSES`.** That would add trailer keys, change the template's heading prompt and every reader of `[pass]`. The `By:` line already says who raised a finding, and *Review dimensions* already tags these dimensions with existing passes.
- **A separate `behaviour.md` evidence file in the change folder.** That would be a fifth write before the WAIT, which is a policy change. `findings.md` already is the write that decides nothing.
- **Replacing `checks.md` with the behaviour check.** Acceptance checks are proof only a revert could break, rerun on every later ship by `accept` with the tree judged by the script. The behaviour check is a one-time walk of the spec's path, judged by reading it. They answer different questions, so both stay.
- **Running the new passes on a factory-built change too.** Its reviewers already ran those lenses on the same diff, and their findings reach `findings.md` through `carry`. Running them again would double the paid review for no new eyes.

## Verification

```bash
./check.sh
```

Healthy output: `ruff check` and `ruff format --check` clean, `pytest -n auto` all passed with the count printed, and `claude plugin validate --strict` passing with the three new agents listed.

```bash
uv run --group dev pytest -q tests/test_preflight.py tests/test_findings.py tests/test_hand_gate.py tests/test_skills.py tests/test_retro.py tests/test_defaults.py tests/test_evals.py -n auto
```

Healthy output: every test named in R1–R23 passes. The existing `test_ship_branches_condition` rows, `ship_question` wordings, `test_the_trailer_never_counts_an_agent_finding` and `test_ship_s_skill_stays_under_its_budget` pass unchanged.

```bash
uv run --quiet --script scripts/sdlc.py record && uv run --quiet --script scripts/sdlc.py drift
uv run --group dev pytest -q -m portable
```

Healthy output: `drift` reports nothing. The portable subset passes, as CI's Windows job runs it.

By hand, in a scratch host with a Tier 2 change touching a `review.sensitive` path and a `[ui]` path, with `[ui]` committed on its base branch:
- `sdlc.py preflight NNN` shows `passes` with all three `applies: true` and `branches` holding `security.md`, `behaviour.md` and `ui.md`.
- With no screenshots, `passes.ui.why` says so, and `ship` stamps once `findings.md` says `UI review: skipped, …` and `UX review: skipped, …`.
- With the `Security review:` line removed, `ship` refuses and names it.
- `preflight --question` names `after the security review and the behaviour check` and `without the UI review (…)`.

**Boundaries.**
- *Always:* passes are decided by the script, every pass that applies says `ran` or `skipped, <why>`, and every finding an agent returns reaches the person.
- *Asks first:* every command the behaviour check runs, through the permission prompt.
- *Never:* a push, a new WAIT, a core agent with a tool that writes, `sdlc.py` starting a server or running `factory.py`, a pass on a factory-built change, or a `[ui]` read from the change's own checkout.

