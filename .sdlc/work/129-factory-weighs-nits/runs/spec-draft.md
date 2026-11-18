---
id: 129
slug: factory-weighs-nits
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 129 — The factory weighs its agents' nits and files them as [nit] entries · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Facts this rests on, each checked in the code:

- Only the code, security and test reviewers write `- NIT:` lines (`agents/reviewer-{code,security,test}.md`). `read_rounds()` reads them with `FINDING_NIT_RE`, and `agent_findings()` records each distinct `(role, text)` as `nit`/`minor`, with `NIT_REASON`.
- `sdlc.py ship` refuses while any finding is `open` or `fix` (`cmd_ship`, `found["open"] + found["fix"]`). So a run can never leave a `fix` in `findings.md` that nothing will fix.
- A `[nit]` entry is valid only with `Theme:`, `Paths:`, `Cost:` (`S`/`M`), `Value:` (`med`/`low`) and `Raised by: NNN-slug (pass)` (`sdlc.py` `nit_entries()`, `NIT_COSTS`, `NIT_VALUES`).
- `_dispose()` already writes the register on `--by person` only, with ids from one `next-entry` call. `cmd_land` refuses `--by auto` while any signal stands.
- `skills/ship/factory.md` tells ship to keep every agent section of `findings.md` exactly as written. So a factory change shipped by hand never files its agents' nits today.

The requirements:

R1. **A reviewer weighs its own nits.** `reviewer-code.md`, `reviewer-security.md` and `reviewer-test.md` tell the reviewer to end each `- NIT:` line with `{<theme> <cost> <value>}`, using the process doc's nits rubric (`docs.process`, else the plugin's guide). Cost is `S`, `M` or `L`. Value is `high`, `med` or `low`. Theme is one word. `read_rounds()` reads the weights and gives each nit its text without them. `test_a_nit_is_read_with_its_weights` fails if the weights stay in the text, or if a line without weights stops being read.

R2. **The script turns weights into a disposition, never a model.** In `agent_findings()`, as `carry` writes them into `findings.md`:
   - `S` + `med` is weighed `fix`.
   - Any other `S`/`M` with `med`/`low` is `recorded`, which proposes a `[nit]` entry.
   - `high` value is never a nit. It is ranked `important`, `recorded`, and carried to `notes.md` as `- [ ] <role>: <text>`.
   - `L` cost is an idea, not a nit. It stays a `nit`, `recorded`, and is carried to `notes.md` the same way. In both cases the approver proposes it `seed` or `dropped` like any undone item.
   - A nit with no weights, or with weights it can't read, stays `minor` with `NIT_REASON`, as today.

   `test_carry_disposes_each_nit_by_its_weights` covers one nit of each kind and fails on any other disposition.

R3. **`findings.md` never holds `fix` from an agent.** A nit weighed `fix` becomes `fixed` when it was handed to the builder (R4) and no later complete round's review by the same role raises it again word for word. Otherwise it is `recorded` and filed like any other. `test_carry_never_leaves_a_fix_for_ship_to_refuse` fails if `sdlc.findings_entries()` reports any `fix` or `open` after `carry`.

R4. **A `fix` nit reaches the builder in the same run, only in a rework that runs anyway.**
   - The `rework` prompt for round N lists round N's `fix` nits after the kept changes, by role and in the reviewer's words.
   - Round N+1's `review` prompt for that role names the nits handed to the builder and asks it to raise again, word for word, any the rework didn't make.
   - A round with `fix` nits and no kept change goes to `approve`, never to `rework`. `verdicts` still decides from changes alone.
   - The first round of a restarted or upgraded run starts fresh, and is handed nothing.

   Tests: `test_rework_hands_the_builder_its_cheap_nits` and `test_a_round_with_only_nits_is_never_reworked`.

R5. **No silence counts as a fix except a handed nit's.** A `recorded` nit, or a `fix` nit never handed to the builder, stays `recorded` even when a later round doesn't raise it. `test_a_nit_not_raised_again_is_still_filed` fails if it turns `fixed`.

R6. **At most 5 nits filed per change.** A change files at most 5 nits, the first 5 in `agent_findings()`'s order. Each one past the cap is `minor`, with `Reason: past the cap of 5 nits a change files`. A nit whose text has no leading `path[:line]` (`LEAD_RE`) is `minor`, with `Reason: names no path, so it can't be filed as a nit`. `test_carry_caps_the_nits_it_files_at_five` fails at 6.

R7. **`findings.md` carries the weights.** Each `recorded` agent nit's section in `findings.md` also holds `Theme:`, `Cost:` and `Value:` lines, which `sdlc.py`'s parser ignores. `sdlc.findings_entries()` still reads the file with no problem, and the `Sdlc-Findings` trailer still counts these nits only in `agents=`. `test_carry_writes_each_agent_finding_once_by_its_role` is extended to check this.

R8. **The landing shows what it would file.**
   - `land_parts()` gains a `nits` part: each nit `carry` recorded, with its title, text, theme, paths, cost, value, pass and role. They come from the same `agent_findings()` call `carry` writes from, so the two can't differ.
   - `land-check` returns it for each change.
   - `land_question()` adds `its agents' nits filed as shown` when any change in the batch has one.

   Tests: `test_land_check_shows_the_nits_it_would_file`, and `test_land_question_names_the_nits` for the clause present and absent.

R9. **Nits to file make the gate the person's.** `land_signals()` adds `nits to file: <n>`, plus `, <m> past the cap of 5` when that applies. A batch holding one is never `clear`, and `land --by auto` refuses it. `test_nits_to_file_keep_the_gate_the_persons` fails if `clear` is true, or if `--by auto` lands.

R10. **The yes files them, with ids from the same `next-entry` call.** On `--by person`, `_dispose()` takes one `next-entry --count` for the seeds, bugs and nits together. It appends each nit to the register as:

    `## [<id>] [nit] <title>`
    `Raised by the <role> review of <NNN-slug>, round <n>: <text>`
    `Theme:`, `Paths:`, `Cost:`, `Value:` and `Raised by: <NNN-slug> (<pass>)` lines

   The append goes in the change's commit, as seeds already do. `cmd_land` reports the ids as `filed_nits`. `test_a_landing_files_the_nits_sdlc_reads` fails unless `sdlc.nit_entries()` reads each filed nit back with no problem, and every id differs from the seeds' and bugs'.

R11. **A rerun files nothing twice.** `_dispose()` skips a nit when the register already holds a `[nit]` entry whose `Raised by:` names this change and whose body holds the nit's text. That is never a match by title alone. `test_a_landing_rerun_files_each_nit_once` runs `_dispose()` twice and fails on a second entry.

R12. **Ship files a hand-shipped factory change's nits.** `skills/ship/factory.md` Step 4 says that the agents' `recorded` nits are proposed as the `[nit]` entries their `Theme:`/`Cost:`/`Value:` lines and `Evidence:` path give. Their ids come in the same `next-entry` call, with `--nits` passed. Ship still never re-dispositions an agent's section. `test_ship_files_the_agents_recorded_nits` (a text check in `tests/test_skills.py`) fails if the side file stops saying so.

R13. **The docs stop calling it a gap.**
   - `guide/review.md`'s **nits** row says the factory has reviewers weigh nits, hands the cheap ones to a rework, and files the rest at landing on the person's yes.
   - `guide/process.md`'s register table and `templates/inbox.md`'s note name the factory's landing beside `/sdlc:ship` as a source of `[nit]` entries.
   - `plugins/factory/README.md` and the land skill's text and description say what the landing files.
   - `.sdlc/setup.json` is re-recorded, and `sdlc.py drift` reports nothing.

## Design

**Weighing (`read_rounds()`).** A new `NIT_WEIGHT_RE` matches a trailing `{theme cost value}` on the text `FINDING_NIT_RE` captured. Each nit becomes `{"text": <without weights>, "theme", "cost", "value"}`. A line without weights keeps `theme`, `cost` and `value` as `None`. `factory.py` keeps copies of `sdlc.py`'s `NIT_COSTS` and `NIT_VALUES` (the filable subset). A test pins the copies to the originals, as `CONFLICT_MARKER_RE` and `FRESH_RE` are pinned today.

**Disposition (`agent_findings()`).** This stays the one function that decides, read by `carry` (`write_findings()`, `cmd_carry`'s `wanted`) and by `land_parts()`.
- It keys each nit by `(role, text-without-weights)`. The latest complete round that raised a nit gives its weights.
- "Handed to the builder" means: the nit was weighed `fix` in round N, a rework of round N ran, and round N+1 is not a restart's or upgrade's first round. That last condition is read from the same `build/round-<R>.restart.md` and `round-<P>.upgraded.md` files `_rounds_at_depth()` and `read_upgrade()` already use.
- The cap of 5 and the no-path rule apply last, in order.
- `high` and `L` nits join `cmd_carry`'s `wanted` list as `"<role>: <text>"`, so the approver's existing `- UNDONE:` contract covers them. Nothing about the approver changes.

**Hand-off (`_task()`).**
- `rework` appends `Also make these nits, each weighed cheap and worth it:` and one `- <role>: <text>` line per nit.
- `review` appends `Nits handed to the builder last round: …; raise again, word for word, any the rework didn't make.`
- `loop_state()` gains a `handed` list computed from the rounds. It reads no new state file, so `verdicts` still reads only `runs/mended`.

**Record (`finding_section()`).** For an agent nit that is `recorded`, three lines go after `Disposition:`: `Theme: …`, `Cost: …`, `Value: …`. `Evidence:` already holds the path.

**Landing.**
- `land_parts(folder, pre)` gets the rounds through a `root`/`cfg` its callers already hold. `land_signals()` and `cmd_land_check()` have both. `_dispose()` and `cmd_land()` load them as `cmd_land` loads `cfg`.
- The `nits` part has a `shown` line per nit: `[nit] <title> (<theme>, <cost>, <value>; <paths>)`. Land Step 1 shows it.
- `_dispose()` extends its one `next-entry` call to `len(seeds) + len(nits)`. It assigns ids in the order seeds, bugs, nits, appends each entry after the last, applies R11's skip, and writes with `newline="\n"`.
- The landing commit's message is unchanged: ship's message doesn't list new nits either, only retired ones.

**Edge cases.**
- A run from before this change has unweighed nits only. They stay `minor` exactly as today, and `test_carry_writes_each_agent_finding_once_by_its_role`'s F5 still holds.
- A reviewer that weighs a nit `high` was told a high-value finding is a `CHANGE`. The script still doesn't drop it: it reaches `notes.md`, which is a signal.
- A register missing at landing is started from its template, as for seeds.

## Contracts touched

- **Agents that judge have no Write.** Reviewers only add text to their reply. `carry` and `land` (the script) write `findings.md`, `notes.md` and the register. The approver is unchanged.
- **No agent writes the register, and nothing is filed without the person's yes.** Only `_dispose()` writes it, and only on `--by person`. R9 makes nits a signal, so `--by auto` can never reach a nit. This is the same rule undone notes follow.
- **The factory's review is never counted as the person's.** Agent nits keep `By: <role>`, are counted only in `agents=`, and the landing commit still carries no `Sdlc-Findings`. The `[nit]` entries feed `/sdlc:status` and retro's theme and age counts, never a findings count. This stays inside REVIEW.md's "a finding counted for the wrong reviewer".
- **`sdlc.py ship` refuses `open`/`fix`.** R3 keeps agent findings out of both.
- **`[nit]` entries keep their shape, and the cap of 5 holds.** R10 is pinned by `sdlc.nit_entries()`, and R6 caps filing per change.
- **`factory.py` never imports `sdlc.py`.** The cost and value words are copies pinned by a test. The register is written by the same by-line append `_dispose()` already uses.
- **`verdicts` decides from the rounds alone.** Nits never make a verdict `CHANGES` and never trigger a rework (R4). The next step is unchanged.
- **Skill invariants.** The land skill gets no new command and keeps its one WAIT. Ship's `factory.md` side file gets no command, gate or commit. `--nits` is already in ship's preflight rule.
- **Guide edits.** `guide/` changes, so the change runs `scripts/sdlc.py record` from its own checkout (R13).
- **Windows.** Every new write passes `newline="\n"`.

No invariant needs to move.

## Alternatives rejected

- **The approver weighs every nit.** It has no shell, judges second-hand from the reviews, and runs after the last round, so a `fix` could never reach the builder in the run. Ship's weighing is done by the session that reviewed, and the reviewer is the factory's equivalent.
- **A rework round for nits alone.** That costs every reviewer a round for S-sized polish, and breaks the existing contract that a nit never makes `CHANGES`.
- **Fixing `fix` nits at landing through `land-fix`.** Each would open a landing round, rerun the gate and every reviewer, and leave "a fix was made while landing" as a signal for the rest of the change's life.
- **Leaving `fix` in `findings.md` for ship.** `sdlc.py ship` would refuse every such landing.
- **Routing every nit through `notes.md` as undone items.** That mixes left-over work with debt, needs a new `→ nit:` tick in `sdlc.py`'s and `factory.py`'s readers, and still needs the weights from somewhere. Only `high` and `L`, which aren't nits, take that path.
- **Counting any nit a later round doesn't raise as fixed.** Reviewers are told to re-raise only handed nits, so their silence on any other nit says nothing about the code.
- **Filing nits under `--by auto`.** That files without the person's yes, against the intent's constraint.

## Verification

```bash
uv run --group dev pytest -q tests/test_factory.py tests/test_land.py tests/test_findings.py tests/test_nits.py tests/test_skills.py
uv run --quiet --script scripts/sdlc.py drift
./check.sh
```

What healthy looks like:
- Every test named in R1–R12 passes, along with the existing `test_nits_are_read_and_never_verified`, `test_carry_writes_each_agent_finding_once_by_its_role` and `test_a_landing_commits_the_agents_findings_and_no_trailer`.
- `drift` reports nothing to propose for this repo.
- `./check.sh` ends green: ruff check, ruff format --check, pytest, and `claude plugin validate --strict`.

A by-hand check in a scratch run: a code review with `- NIT: src/a.py:9: a long line {style S low}` produces a `recorded` F-section with `Theme: style`. `land-check` shows it under `nits` with the signal `nits to file: 1`. A `yes` leaves a `[nit]` entry that `sdlc.py status` lists.

Boundaries:
- Always: the script decides the disposition from the weights, every write is by line, and filing happens behind the landing's yes.
- Ask first: nothing new. The landing's existing question gets one more clause.
- Never: an agent writes the register, a nit makes a verdict `CHANGES` or starts a rework, `findings.md` keeps an agent `fix`, the approver's contract changes, or a nit is filed under `--by auto`.
