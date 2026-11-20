---
id: 202
slug: defaults-to-landing
kind: spec
created: 2026-11-20
updated: 2026-11-20
---

# 202 — An escalation of assumed defaults alone goes to the landing's question · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

No nits are taken in: the intent names none.

Assumptions, each checked in the code:

- **The landing already handles a READY change with open defaults.** `ready()` takes any change at `stage: test` with a decision (`factory.py`). `land_parts()` lists every open default as `assumed`. `land_signals()` makes each one a signal, so the batch never passes itself. `land_question()` adds `its assumed decisions confirmed as shown`. On the yes, `_dispose()` ticks every open default `→ decided: the assumed default, confirmed when landing` (`CONFIRMED`).
- **Core reads only the decision word and the ledger.** `needs_of()`, `column()`, `decide_step()` and `answered()` in `sdlc.py`, reading through `factory_records.reading()`, use those two things only. A READY change at `test` needs nothing and sits in Ready.
- **`/sdlc-factory:decide` works on any change at `stage: test`.** `cmd_ask()` refuses only by stage and lists every open ledger line, whatever the decision says.
- **The approver's rule about defaults lives only in its prompt.** "ESCALATE while any default is escalated" is in `agents/approver.md` and `prompts/common.md`'s `weigh`. No code enforces it today.
- **The diff's sensitive paths are already known to the build loop.** `depth()` computes them from the base branch's `[review] sensitive` and `loop_state()` receives them as `run["sensitive"]`. `loop_state()` already reads `intent.md`'s frontmatter.

Requirements:

1. **R1. A new approver line for a default the landing may confirm.** For each open default, the approver gives exactly one line:
   - `- SETTLED: D<n>: …` (unchanged), or
   - `- ESCALATED: D<n>: …` (unchanged), or
   - `- CONFIRM: D<n>: <what the build assumed, and why the person's yes at the landing is enough>` (new).

   The decision may be `READY` when every open default is SETTLED or CONFIRM and nothing else would escalate. Both `agents/approver.md` and `prompts/common.md`'s `weigh` part say so. Tests: the golden prompt `tests/prompts/approve-defaults.txt` fails until `weigh` offers `CONFIRM`. `test_the_approver_doc_offers_confirm` fails if `approver.md` still says the decision is ESCALATE while any default is open.

2. **R2. A CONFIRM line never ticks the ledger.** `approver_weighing()` reads `- CONFIRM: D<n>: <reason>` into its own map (`CONFIRM_RE`). `cmd_decisions` leaves that line `- [ ]`: it stays in `assumed`, never in `settled`, and is never marked in any way. An id that has two of SETTLED, ESCALATED and CONFIRM is "named twice", as SETTLED twice is today. Test: `test_a_confirm_line_leaves_the_default_open` fails if D2's ledger line is ticked or D2 leaves `assumed`.

3. **R3. A READY that rests on a default it may not carry is a stop the run mends once.** `loop_state()` adds a problem when the decision is `READY` and any open default:
   - has no CONFIRM line (no line at all, or only an ESCALATED one), or
   - is CONFIRMed on a change whose diff touches a `[review] sensitive` path (`run["sensitive"]`), or
   - is CONFIRMed on a change whose `intent.md` has a non-empty `closes:`.

   The problem names each id and why. It is mendable by the approver once a round (`mendable["approver"]`), through a new `mend.md` part, `confirm`. A second time is a `rerun` stop. Tests:
   - `test_ready_with_an_uncarried_default_is_mended`, with one case each for an unlined default, an ESCALATED default, a CONFIRM on a sensitive path and a CONFIRM on a `closes:` change. Each must give `next: stop`, `way: mend`, `mend: ["approver"]`.
   - `test_a_second_uncarried_ready_is_a_rerun` fails if the mended round mends again.

4. **R4. The approve prompt offers CONFIRM only where it is allowed.** With open defaults and neither a sensitive path in the diff nor a `closes:`, `weigh` offers all three lines. With either, a new `weigh-no-confirm` part replaces the CONFIRM clause and names the reason (the sensitive paths, or the issue). Test: a new golden prompt `tests/prompts/approve-defaults-sensitive.txt` and a `closes:` case. Each fails if CONFIRM is offered.

5. **R5. CONFIRM counts for nothing on an ESCALATE.** On an ESCALATE decision, a CONFIRMed default stays an open default to decide, as today. `needs_of()` still says `confirm N defaults` and `decide_step()` still names `/sdlc-factory:decide`. Test: `test_confirm_on_an_escalate_still_needs_deciding` fails if the needs drop the defaults.

6. **R6. A READY with carried defaults is Ready, not Needs you.** At `stage: test`, a `READY` decision with open defaults gives `needs_of() == []`, `column() == "ready"` and `decide_step() is None`. The board card still shows `N default(s) assumed`. Test: `test_ready_with_assumed_defaults_is_ready` (in `tests/test_sdlc.py`) fails if the change is placed in Needs you.

7. **R7. Carried defaults are always a signal at the landing.** For a READY change with open defaults, `land-check` gives:
   - the signal `assumed decisions to confirm: D…`,
   - `clear: false`,
   - a question holding `its assumed decisions confirmed as shown`.

   `land --by auto` refuses the change with `the gate is the person's`. So `Sdlc-Landed: by=auto` is never written for it. Test: `test_carried_defaults_keep_the_gate_the_persons` fails if `clear` is true or `--by auto` lands it.

8. **R8. The landing shows what the build assumed.** Each `assumed` entry from `land_parts()` gains:
   - `default`: the first `- OPTION:` under the ledger line, or null when there are none;
   - `reason`: the approver's CONFIRM reason, or null when there is none.

   `land_shown()` prints each one as `D2: <question> — assumed: <default> (the approver: <reason>)`, leaving out whichever part is null. Test: `test_the_landing_shows_each_assumed_default_with_its_default` fails if the default or the reason is missing from `shown`.

9. **R9. The landing's yes confirms exactly what it showed.** After a yes, each default shown under *Assumed decisions to confirm* reads `- [x] D<n> (…) → decided: the assumed default, confirmed when landing`. No other line changes. Test: `test_the_landing_yes_confirms_carried_defaults` fails if a CONFIRMed line is left open, or if a blocking or settled line is touched.

10. **R10. `/sdlc-factory:decide` still answers carried defaults before the landing.** For a READY change, `ask` lists each CONFIRMed default as an item. A new field, `confirm`, holds the approver's reason, and `escalated` stays null. `ask --answered` gives:
    - `ship` when every answer is the kept default;
    - `rebuild` with `then: /sdlc:ship NNN` when any answer is not.

    Test: `test_decide_answers_a_ready_changes_carried_defaults` fails if the item is missing or `next` is wrong.

11. **R11. `/sdlc:ship` still shows every assumed default.** `skills/ship/factory.md` Step 4 still lists every unticked default as an open item, with its options. It now adds the approver's CONFIRM reason beside it, and says the approval confirms the default. Test: `test_ship_shows_carried_defaults` reads the side file and fails if the CONFIRM reason or the "every unticked" rule is missing.

12. **R12. No doc still says a default always escalates the change.** These are updated to the three-way weighing:
    - `plugins/factory/README.md` (*Default* bullet),
    - `plugins/factory/skills/build/SKILL.md` (decisions paragraph and Step 4),
    - `plugins/factory/skills/decide/SKILL.md` (description and opening: it also takes a READY change's carried defaults),
    - `factory.py`'s module docstring,
    - `AGENTS.md` (the factory paragraph's list of stops a run mends).

    Test: `test_no_doc_says_any_default_escalates` greps those files and fails on the phrases `ESCALATE while any` and `escalated while any`.

## Design

**The approver's three answers for a default.**

| line | meaning | ledger |
|---|---|---|
| `SETTLED` | the spec, code or rounds answer it | ticked `→ settled by the approver:` (unchanged) |
| `CONFIRM` | the person's yes at the landing is enough | stays open, so it is still assumed |
| `ESCALATED` | only the person can decide, before the landing | stays open, and the change is ESCALATE (unchanged) |

The rule about what can never be settled (scope, policy, cost, a destructive operation, a secret, a published interface) also covers CONFIRM: those stay ESCALATED. That part is the approver's judgment. The script enforces what it can see: sensitive paths and `closes:`.

**Reading the lines (`factory.py`).**
- New regex: `CONFIRM_RE = re.compile(r"^\s*- CONFIRM:\s*(D\d+):\s*(.+?)\s*$")`.
- `approver_weighing()` returns a third value, `confirms: dict[id, reason]`, from the current `decision.md` only. Each caller is updated: `cmd_decisions`, `cmd_ask`, and the new check.
- `cmd_decisions` treats a CONFIRM like an ESCALATED line for the "named twice" rule and for filling options. It never marks the line.

**The check (`run_state.py`).** A new helper, `uncarried(folder, ledger, decision, sensitive, closes)`, sits in `run_state.py` because only `loop_state()` calls it. It returns `[(id, why)]`. `loop_state()` adds one problem text per id after `read_decision()`. It registers that text under `mendable["approver"]`, the same way `decision_preamble()` registers `NO_DECISION`. `runs/mended` limits it to once a round, as today.

The mend prompt gets a new part, `mend.md`'s `confirm`, filled with the problems. It tells the approver to reply again in full: either ESCALATE, or give each named default a line it may give. `closes:` is read with `frontmatter()` as text, never as YAML: empty or absent means none.

**The approve prompt.** `weigh_text(ledger, sensitive, closes)` picks the new `weigh-no-confirm` part in place of the CONFIRM clause when either signal is present. The `cmd_agent` approve branch passes `run["sensitive"]`, already computed for the depth, and the intent's `closes:`.

**The landing (`landing.py`).** No change to signals, the question or `_dispose()`: they already treat an open default on a READY change as something to confirm (R7 and R9 pin this). `land_parts()` adds `default` and `reason` to each `assumed` entry, reading the ledger's `options` and `approver_weighing()`'s confirms. `land_shown()` prints them.

**Core (`sdlc.py`, `factory_records.py`, `board.html`).** No code change. `needs_of()` and `column()` already put a READY change at `test` in Ready, and the card already counts assumed defaults. R6 pins this, so a later change can't make carried defaults a need without a test failing. Core gets no copy of `CONFIRM_RE`: it never needs to tell a carried default from any other open one.

**Edge cases.**
- **A default raised after the approver ran.** It has no line, so R3 stops a READY.
- **A CONFIRM naming a line that isn't an open default** (blocking, settled, superseded, a look). It carries nothing. If it is the only line for an open default, R3 catches it.
- **A READY with no open defaults.** Unchanged.
- **The person leaves a change out at the landing.** Its defaults stay open. `/sdlc-factory:decide` or `/sdlc:ship` takes them (R10, R11).

## Contracts touched

- **An agent never ticks a decision the person didn't answer.** CONFIRM never ticks. Only two things tick an open default as decided:
  - the landing's yes, which writes `CONFIRMED` for the defaults its `shown` lists;
  - `/sdlc-factory:decide`, on the person's answer.
- **Approval is per question.** The landing's question already has the clause `its assumed decisions confirmed as shown`. `shown` (in the dialog's preview) lists each one, now with what the build assumed. The yes covers nothing it didn't show.
- **`Sdlc-Landed: by=auto` only for a batch with no signal.** An open default stays a signal in `land_signals()` (R7). Nothing here gives the auto path a way around it.
- **Agents that judge have no Write.** The approver still returns text, and `factory.py` reads it. No new tool.
- **`verdicts` decides from the rounds alone and reads no state file but `runs/mended`.** The new check reads `decision.md`, `decisions.md`, `intent.md`'s frontmatter and the diff's sensitive paths. `loop_state()` already reads all of these. No new state file.
- **[Policy text changes] The one stop a run mends** (AGENTS.md, *The factory*). The list gains: "a READY decision that leaves an open default it may not carry to the landing". This edits the policy doc's description of the mend rule, so it is called out here for the person to approve with the spec.
- **`[review] sensitive` is matched by the script and read from the base branch.** The CONFIRM bar uses `depth()`'s `hit`, which comes from the base branch's list, so a change can't lift its own bar.
- **Core reads factory records only through `factory_records.py`, with pinned copies.** No new copy is needed, so `tests/test_modules.py` is untouched.
- **Skill invariants.** No skill gains a bash command, an allowed-tools rule or a WAIT. `decide`'s single WAIT stays as it is. The prompt files keep one line per part, pinned by `tests/prompts/`.
- **This change's own risk.** `plugins/factory/scripts/landing.py` is in this repo's `[review] sensitive`, so this change gets the deep review.

## Alternatives rejected

- **ESCALATE with a "defaults only" reason kind (`- ESCALATED: landing: D2`).** Every reader that keys on the decision word would need an exception: `needs_of()`, `answered()`, `column()`, `decide_step()`, `land_signals()`'s `the approver escalated`, ship's "first and plainly when it is ESCALATE", and the build report's lead. Each exception would have to be copied into `factory_records.py` and pinned. The change would still say ESCALATE when it asks nothing of the person before the landing. READY plus an open default already means "confirm at the landing" in every reader.
- **The script carrying every escalated default to the landing on its own.** That overrides the approver's judgment that a default is a policy or scope call, which the intent keeps escalated.
- **Ticking a carried default in the ledger (`→ carried by the approver`).** A ticked line is no longer assumed, so the landing would stop showing it and the yes would confirm nothing. It would also be an agent ticking a line.
- **Allowing CONFIRM on sensitive or `closes:` changes, since the landing signals them anyway.** The intent says those still escalate. A signal makes the person look at the batch, not at that default with its options in `/sdlc-factory:decide`.
- **Making a READY that rests on an uncarried default a plain `rerun` stop.** The mend path already exists for an approver's reply the script can't use. One cheap re-ask is better than stopping the person.

## Verification

```bash
uv run --group dev pytest -q tests/test_factory_decisions.py tests/test_land.py tests/test_sdlc.py tests/test_board.py tests/test_skills.py -n auto
uv run --group dev pytest -q -k "confirm or carried or assumed_default or uncarried" -n auto
./check.sh
```

Healthy output:
- every named test passes;
- the golden prompts in `tests/prompts/` match;
- `./check.sh` ends green: ruff, the format check, the full suite, and `claude plugin validate --strict` with no errors.

A check by hand, on a scratch factory change whose only open default is CONFIRMed:
- `factory.py verdicts NNN` says `done` with `decision: READY`;
- `sdlc.py status` lists the change under Ready, not Needs you;
- `factory.py land-check NNN` shows `D<n>: … — assumed: <default> (the approver: …)` under *Assumed decisions to confirm*, with `clear: false`.

