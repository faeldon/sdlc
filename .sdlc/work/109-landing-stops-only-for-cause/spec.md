---
id: 109
slug: landing-stops-only-for-cause
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 109 — A landing stops only for what needs the person · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Each one names the test that fails without it, in `tests/test_land.py` (landing) or `tests/test_factory.py` (the build loop and `agent`).

**Things I'm taking as given, each checked in the code.** `land_verdict()` treats every missing `exit:` (`read_evidence()`) and every reply that doesn't open with `VERDICT:` as a plain `stop`; the landing has no mend. `cmd_agent()` lets a `mend` task run in any state, and always files a behaviour mend under `reviews/round-<last>/`, which is how 103's landing mend got into its build round. `cmd_land()` reports a `CalledProcessError` through `str(e)`, which leaves out its `stderr`. On `stage: shipped`, `cmd_land()` always goes to `_amend_record()`, which refuses when `HEAD` has no `Sdlc-Landed:` line. `land_parts()` takes the note text from `sdlc.py preflight`'s `undone` items, and `open_items()` gives only the `- [ ]` line itself; with no proposal, that whole line becomes the seed's title. `factory.py resolve --continue` stages whatever the builder left in `.sdlc/work/inbox.md`. `cmd_land()` retires the open `[nit]` entries that `named_nits()` finds (each one the change names by id in its intent's `## Approach` or its spec's `## Requirements`) in the same commit that `sdlc.py ship` deletes its seeds in.

1. **R1.** In a landing round, a behaviour reply whose `## Evidence` has a command with no `exit:` line, or has no section at all, makes `land-verdicts` say `next: mend` with `mend: ["behaviour"]`, not `stop`. Test: `test_a_landing_review_missing_an_exit_is_mended_not_stopped` fails if a `VERDICT: PASS` reply with `$ head -5 intent.md` and no `exit:` reads as `stop`.
2. **R2.** In a landing round, a reviewer reply that holds its `VERDICT:` line after other lines (`preamble()`) makes `land-verdicts` say `next: mend` with that role. Test: `test_a_landing_verdict_after_a_preamble_is_mended`.
3. **R3.** Each role is mended at most once per landing round. `agent` records the mend in `runs/mended` as `<role> land-<n>`. A second reply that still needs a mend makes `land-verdicts` say `stop`, and a second `agent --task land-mend` for that role and round is refused before any session runs. Build-round mends and landing mends don't use up each other's allowance. Test: `test_a_landing_mend_is_once_a_role_a_round`, which also asserts that a build-loop `<role> <N>` line doesn't block a landing mend, and the reverse.
4. **R4.** `agent --task land-mend --role <role>` writes its reply to `reviews/land-<n>/<role>.md`, or to `reviews/land-<n>/verified.md` for the verifier, replacing the old reply. It never writes under `reviews/round-*`. Test: `test_a_landing_mend_writes_into_its_landing_round` fails if `reviews/round-1/` gains or changes a file.
5. **R5.** `agent --task mend --role <role>` is refused, with nothing run or written, unless `verdicts` says `next: stop`, `way: mend`, and lists that role in `mend`. A change at `stage: test` or `shipped` with a landing round open is refused that way. Test: `test_a_build_mend_is_refused_when_verdicts_names_none` (the 103 case: no file appears under `reviews/round-1/`).
6. **R6.** Only R1, R2 and R10 make a landing mendable. A red landing gate, failed acceptance checks, a kept change, a reply that is still unmendable after its one mend, or any mendable problem alongside an unmendable one leaves `land-verdicts` at `stop`, as it is today. Test: `test_a_landing_stops_for_cause_even_beside_a_mendable_problem` (red gate plus a missing exit gives `stop`).
7. **R7.** When the landing commit fails, the refusal carries the tail of git's own output (stderr, else stdout, last 500 characters). Test: `test_a_failed_landing_commit_carries_git_s_error` uses a `commit-msg` hook that prints `hook says no` and exits 1, and asserts the refusal contains `hook says no`.
8. **R8.** If a landing fails after `sdlc.py ship` and before its commit, rerunning `land` with the same `--by` makes the commit. It reruns `sdlc.py ship` (which is safe to run twice) and commits with `land_message()`. The new `HEAD` has `Sdlc-Landed: by=<by>` and the `Retired nits:` the first run would have written. Then `base` runs as usual. "The commit wasn't made" means `HEAD`'s message has no `Sdlc-Landed:` line and `HEAD`'s `intent.md` isn't `stage: shipped`. Test: `test_a_landing_whose_commit_failed_commits_on_rerun` (fail via the hook, remove the hook, rerun, assert one new commit with that message and a clean worktree).
9. **R9.** If `HEAD` has no `Sdlc-Landed:` line but its `intent.md` already says `stage: shipped` (the change was shipped by hand), `land` still refuses with no new commit, as `_amend_record()` does today. Test: `test_a_hand_shipped_change_is_not_committed_again`.
10. **R10.** In the build loop and in a landing, the approver and the verifier get one mend per round, as reviewers do. An approver mends when `decision.md` holds its `DECISION:` line after other lines. A verifier mends when `read_verified()` reports any problem with its reply: an answer missing, given twice, or written in another shape such as `- **KEPT:**`. `verdicts` then says `way: mend` with `approver` or `verifier` in `mend`. The mend resumes that agent's own session and replaces `decision.md` or `verified.md` with its new reply. A `decision.md` missing a `## Reconsider the approach` section when the rounds ran out is not mendable. Tests: `test_an_approver_s_preamble_is_mended_by_the_approver` and `test_a_verifier_s_unread_answers_are_mended_once`.
11. **R11.** A carried note's text includes its continuation lines. These are the lines after the `- [ ]` line that are indented and not blank, up to the first line that isn't, and they are joined with single spaces. This full text is used in `land-check`'s `undone[].text` and in the body of the seed `_dispose()` writes. The tick still goes on the `- [ ]` line. Test: `test_a_carried_note_keeps_its_continuation_lines`.
12. **R12.** A note with no approver proposal is carried as a seed titled by the first sentence of its full text (split as `land_message()` splits a Problem: after `.`, `!` or `?` followed by a space), or by the whole text if it has no sentence end. An approver's `- UNDONE:` line matches a note on either its first line or its full text. Test: `test_an_unproposed_seed_is_titled_from_its_first_sentence`.
13. **R13.** If `.sdlc/work/inbox.md` was among the conflicted files, `factory.py resolve --continue` deletes from it every entry the landing deleted, before staging, and reports their ids as `dropped`. That means each entry whose id the change's `idea:` or `fixes:` names, and each nit the landing retired: an open `[nit]` entry the change names by id in its intent's `## Approach` or its spec's `## Requirements` (`named_nits()`, read against the register as the builder resolved it). Every entry is matched by its id alone, never by title. Each is deleted from its heading up to the next `## ` heading outside a fence; every other entry stays byte for byte. Tests: `test_a_landing_resolution_never_keeps_the_change_s_own_seeds` (the 104 case: base and branch both edit the register, the builder's resolution keeps the change's `[building]` entry, and the landed commit doesn't have it) and `test_a_landing_resolution_never_keeps_the_nits_it_retired` (the builder's resolution keeps a nit the landing retired, and the landed commit doesn't have it, while an open nit the change doesn't name stays).
14. **R14.** The land skill handles `next: mend` by running `agent --task land-mend --role <role>` for each role listed, then reading `land-verdicts` again. The build skill names the approver and verifier mends. Test: `test_the_land_skill_names_its_mend` asserts `--task land-mend` appears in a bash block of `plugins/factory/skills/land/SKILL.md`; the existing `tests/test_skills.py` rule checks cover its command.

## Design

**One way to decide what's mendable, used by both loops.** Both the build loop and the landing collect mendable problems per role into a `mendable` dict, then drop roles already mended this round. If every problem is mendable, the run mends; otherwise it stops. `loop_state()` already works this way (lines 1425–1457). This change adds `approver` (the `decision.md` preamble, read by a new `decision_preamble()` that mirrors `preamble()` with `DECISION_RE`) and `verifier` (every problem `read_verified()` reports for the last round's `verified.md`) to `loop_state()`'s `mendable`. `land_verdict()` gets the same block for round `land-<n>`:

- the behaviour role's `read_evidence()` problems;
- any wanted role whose file fails `VERDICT_RE` on line 1 but passes `preamble()`;
- the verifier's `read_verified()` problems.

Roles listed by the new `land_mended(folder, n)` are dropped first. It reads the same `runs/mended` file and takes only `<role> land-<n>` lines. The existing `mended()` already skips those lines, because `"land-3".isdigit()` is false, so the two loops can't consume each other's allowance (R3). `land_verdict()` checks this before `gate`/`accept`/`review`: if there are problems and every one is in the remaining `mendable`, `next` is `mend` and `mend` lists the roles. Otherwise any problem gives `stop`, as today (R6).

**The landing's mend is a task of its own.** `land-mend` joins `TASKS` and `LAND_TASKS`. `_land_task()` handles it:

- it refuses unless `land_verdict()` says `mend` with that role;
- a verdict preamble resumes that reviewer's last session with `VERDICT_MEND`;
- a verifier problem resumes the verifier with a new `VERIFY_MEND`, which quotes the script's own problem lines and restates the `- KEPT: <role>: C<n>: …` shape;
- missing evidence starts a new behaviour session with the same prompt `land-review` would send, plus `MEND`.

The target is always under `reviews/land-<n>/` (R4). `cmd_agent()` decides whether to resume from a widened `verdict_mend()`, which covers reviewer, approver and verifier preambles in both loops. After filing, it appends `<role> land-<n>` to `runs/mended`.

**The build loop's `mend` checks its step (R5).** `cmd_agent()` adds one refusal before planning: for `task == "mend"`, `state["next"] == "stop" and state.get("way") == "mend" and role in state["mend"]`, otherwise `verdicts says <next>, not a mend for <role>`. This is what stops 103's misfiled reply. `_task()`'s mend branch gains `approver` (resumed, `DECISION_MEND`, to `decision.md`) and `verifier` (resumed, `VERIFY_MEND`, to `reviews/round-<R>/verified.md`). Its last refusal line names every role that can be mended. `WAYS["mend"]` changes to "…asks again for the missing ## Evidence, or an answer in its shape on the reply's first line…". Only the `NEXT:` sentence changes; `STOPPED_RE` and the board's copy are untouched.

**The commit's error and its resume (R7–R9).** The `except` in `cmd_land()` reports `(e.stderr or e.stdout or str(e)).strip()[-500:]` for a `CalledProcessError`, and `str(e)` for an `OSError`. The commit is moved into a helper, `_land_commit(root, folder, by, nits, unreviewed)`, used in two places:

- on the `stage: test` path, as today;
- on a new branch before the `elif _amend_record`: `stage == "shipped"`, no `Sdlc-Landed:` in `git log -1 --format=%B`, and `git show HEAD:<rel>/intent.md` doesn't read `stage: shipped`. That branch reruns `sdlc.py ship <folder>`, which restamps the same day and restages, then works out `nits` as the ids `named_nits()` would name against `HEAD`'s register (read with `git show HEAD:.sdlc/work/inbox.md`) that the tree's register no longer has. Then it commits.

`unreviewed` comes from `land_unreviewed()`; at `shipped` that is `_unreviewed_at_test()`'s `[]`, so the resumed message drops a `Changed since its last review:` paragraph the first attempt could have carried. The resume doesn't rerun `_dispose()`, the accept/cases checks or `_set_impact()`: each one ran, or refused, before ship stamped the change. Any other shipped state reaches `_amend_record()` unchanged, which keeps R9.

**Carried notes (R11–R12).** A new `note_items(folder)` reads `notes.md` and returns, for each line number `preflight` reported, its full text including continuation lines. Fences are skipped the way `open_items()` skips them. `land_parts()` looks a proposal up by full text first, then by the first line, as preflight gives it. A missing proposal becomes `("seed", first_sentence(full))`. `item["text"]` becomes the full text, so `land-check` shows exactly what `_dispose()` will write. `first_sentence()` is pulled out of `land_message()`, which then calls it. `sdlc.py`'s `open_items()` doesn't change, so `/sdlc:ship` and `preflight` keep their contract.

**The register after a resolution (R13).** `cmd_resolve(cont=True)` builds the list of ids to drop only when `INBOX` is among the conflicted files. It runs after the marker check, on the register as the builder resolved it, and before `git add`:

- the change's `idea:` and `fixes:`, read from `intent.md` with a new `frontmatter_ids()`: the bracketed or bare list, split on commas, keeping values that match the register's id shape `\d{4}-\d{2}-\d{2}-\d+`. A value naming its seed by title is skipped, never matched;
- `named_nits(root, folder)`, unchanged: the open `[nit]` entries in that register that the change names by id in `NIT_SECTIONS`. The landing retired exactly these with the same function, so the resolution drops the same set. An entry the landing never retired (a nit the change doesn't name) is left alone.

It then calls `drop_entries(root, ids)`, which is `retire_nits()` generalised from `NIT_RE` to any heading `## [<id>] [<tag>]`, compared by id. `retire_nits()` becomes a call to it, so the two can't drift apart. The output gains `dropped`, the ids removed, in register order. The `resolve` prompt in `_land_task()` also tells the builder, by id, that the change's own seeds and its retired nits stay deleted. The script's drop is the guarantee; the prompt only avoids pointless edits.

**Prompts.** `agents/reviewer-behaviour.md`: every command in `## Evidence` gets its `exit:` line, a read included. `agents/approver.md`: nothing before the `DECISION:` line. `agents/verifier.md`: the answer lines are plain text, with no emphasis. These cut down how often a mend is needed; the mend is what makes sure a missed line doesn't stop the run.

## Contracts touched

- **A supervisor never patches an agent's reply** (factory, AGENTS.md; the land skill's "Never patch a verdict"). Every mend asks the agent again and files that agent's whole new reply over the old one. No script or skill moves, adds or edits a line in a reply. The R13 drop edits the register, which is the change's own `ship` and nit-retiring output brought back by a rebase, not an agent's reply. It is a script-owned git step like `_settle_counter()`.
- **"A missing evidence or a verdict after a preamble is the one stop a run mends, once a round for each role."** This is AGENTS.md's factory paragraph, and **it widens, as approved with this spec's revision**: the approver's preamble, the verifier's unread answers, and the same mends in a landing round. "Once a round for each role" still holds, with each landing round counting as its own round. AGENTS.md's paragraph, `cmd_verdicts()`'s docstring, `cmd_land_verdicts()`'s docstring and the factory README get updated at ship (AGENTS.md is in `docs.context`).
- **`verdicts` reads no state file but `runs/mended`.** Still true: `land_mended()` reads the same file, and `decision_preamble()` reads `decision.md`, which is already part of the run.
- **Landing commits only through sdlc's own steps; `factory.py` never imports `sdlc.py`.** The resume calls `sdlc.py ship` through `_sdlc()`. The commit stays in the one place `cmd_land()` already commits. `frontmatter_ids()` and `drop_entries()` are factory-side copies of the register's shape, and no new `sdlc.py` command is added.
- **Never match a register entry by title alone** (AGENTS.md, *The register*). R13 matches by id only. A title-valued `idea:` is skipped, not guessed.
- **A gate passes itself only with no risk signal; `Sdlc-Landed: by=auto` is never the person's.** The resume uses the same `--by` and runs after the same `land_signals()` refusal at the top of `cmd_land()`.
- **The register is committed on its own only by `inbox-commit`.** Not touched: the R13 drop rides in the change's rebased commit, just as ship's deletion and the nit retirement did.
- **Windows rules.** Every new `write_text` passes `newline="\n"`. The `git show` reads go through `_git()`. No new subprocess runs in text mode without `encoding="utf-8"`.
- **Skills' `allowed-tools`.** `land-mend` runs as `factory.py agent <NNN> --task land-mend …`, which the land skill's existing `factory.py agent *` rule covers, so no rule is added.
- **Run stops stay Tier 2's.** A run still stops only through `verdicts`/`land-verdicts`, and a person is never asked to step in for a mend.

## Alternatives rejected

- **Make a missing `exit:` on a read-only command no problem at all.** The script would have to decide which commands are read-only, which is judgment it can't make reliably (`sdlc.py status` reads; `sdlc.py ship` writes). And a claim would stand on evidence no one saw finish. One mend fixes all the cases in 2026-11-17-71 at the cost of one session.
- **Route a landing's mend through the build loop's `mend` task, retargeted when a landing round is open.** One task would then write to two different round trees depending on state, which is the kind of mistake 2026-11-17-72 already is. A separate task in `LAND_TASKS`, refused outside its own step, keeps each loop's files apart.
- **Count a landing mend against the build round's once.** The build round's mended reply is a different session and a different reply. Sharing the allowance would turn a build that needed one mend into a landing that can never mend.
- **Have the supervisor or the skill move a verdict to line 1, or strip `**` from a verifier's lines.** That edits an agent's reply, which a constraint forbids.
- **Fix the carried note in `sdlc.py`'s `open_items()`.** `/sdlc:ship`, `undone` and `preflight` all promise one line per item, and ship ticks that line. Reading continuations on the factory side fixes the landing without changing what ship shows a person.
- **On a failed commit, reset the stamp and stage so a rerun starts from `stage: test`.** That undoes `sdlc.py ship`'s writes and the register deletion by hand, outside sdlc's own steps. Committing what ship already did is simpler, and ship is designed to be safe to rerun.
- **Only tell the builder in its prompt not to keep the change's seeds and retired nits.** 104's builder resolved conflicts sensibly and still kept them. A rule the script can enforce goes in the script.
- **Read the retired nits from the rebased commit's `Retired nits:` paragraph.** It works only while the rebase stops on the landing's own commit, and it parses prose. `named_nits()` is the rule the landing used to retire them, so applying it again gives the same set without either dependency.
- **Match a title-valued `idea:` as `sdlc.py`'s `ref_matches()` does.** That needs a factory copy of `ref_matches()` and a test pinning it, for a value new intents no longer write. Ids only is what the register's policy asks for.

## Verification

```bash
uv run --group dev pytest tests/test_land.py tests/test_factory.py -q -n auto
./check.sh
```

Healthy output: both pytest runs pass, including the fifteen tests named above. `./check.sh` ends with ruff clean, the formatter check clean, the full suite passing, and `claude plugin validate --strict` passing. Two manual checks with scratch landings:

- A behaviour reply has `$ head -5 intent.md` and no `exit:`. `factory.py land-verdicts <NNN>` prints `"next": "mend"` and `"mend": ["behaviour"]`. Then `agent --task land-mend --role behaviour`, run with the `claude` fake, adds `behaviour land-1` to `runs/mended`, and nothing under `reviews/round-*` changes.
- The register conflicts and the builder keeps the change's seed and a nit it retired. `factory.py resolve <NNN> --continue` prints both ids in `"dropped"`, and `git show HEAD:.sdlc/work/inbox.md` holds neither.

**Boundaries.**
- **Always:** a mend is the agent's own new reply; each role is mended at most once a round; a red gate, failed checks or a kept change stops the landing; a register entry is matched by id.
- **Ask first:** any widening of what a run mends beyond the approver, the verifier and landing rounds approved here.
- **Never:** edit an agent's reply, commit outside `cmd_land()`'s one commit and `_amend_record()`, mend a landing from the build loop's task, match a register entry by title, or touch `sdlc.py`'s `open_items()`.

