---
id: 230
slug: nit-flow
kind: spec
created: 2026-11-22
updated: 2026-11-22
---

# 230 — Nits are filed once, only while still true, and can be retired · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: none.

**Reverses an earlier decision.** R2 reverses 129 R5 (`test_a_nit_not_raised_again_is_still_filed`).
That rule said only a cheap nit handed to the builder counts as fixed when later rounds stop
raising it. 129 R5 held because a reviewer was never asked to look at a nit again, so a nit that
stopped appearing proved nothing. R4 closes that gap first: each later reviewer is asked about its
earlier nits. R2 depends on R4 and does not stand without it.

1. **R1. A role's nits are filed from its last round only.** `agent_findings()` gives a nit a
   `file` only when the latest complete build round with that role in its reviews raised it. If
   round 1 of `code` raises `src/a.py:3: X {style M med}` and round 2 of `code` raises
   `src/a.py:4: X, reworded {style M med}`, exactly one nit is filed, and it is round 2's.
   `test_a_nit_a_later_round_raises_reworded_is_filed_once` fails if two are filed, or if round
   1's is filed.
2. **R2. A nit no later round raises is not filed, whatever its weights.** Take a nit from round N
   of role R. If a later complete build round of R exists and doesn't raise it word for word, the
   nit gets no `file`, whatever its cost and value. This holds across a restart and an upgrade
   too, since a later round is a later round. `test_a_nit_no_later_round_raises_is_fixed_whatever_its_weights`
   covers `M low`, `S low`, `M med` and a restart's first round. It fails if any of them is filed.
   `test_a_nit_not_raised_again_is_still_filed` is replaced by this test, not kept.
3. **R3. A nit not filed is never dropped silently.** An earlier-round nit that R1 or R2 leaves
   unfiled still gets its own `findings.md` section, with a `Reason:`:
   - `fixed` with `FIXED_REASON` ("not raised again by a later round of its review") when no nit
     from R's later rounds names the same path (`LEAD_RE`'s group 1);
   - `minor` with `REPEAT_REASON` ("raised again, reworded, by round <M> of its review, which it
     is filed from") when one does.

   `HANDED_REASON` is retired: a handed cheap nit is a case of `FIXED_REASON`.
   `test_a_nit_not_filed_says_why` asserts both reasons and that each nit has a section. It fails
   if a section is missing or has no `Reason:`.
4. **R4. Each reviewer is asked about its own earlier nits.** The review prompt for round N+1
   names, to each role, the nits that role raised in its latest complete build round before N+1.
   That includes the round before a restart's or an upgrade's first round. The prompt asks it to
   raise again, word for word with its weights, any that are still true. This is a new `review`
   part in `plugins/factory/prompts/review.md`, named with its placeholder in `PROMPT_PARTS`, so
   `_prompt_file()` refuses a file without it. The cheap nits already in the `handed` part are
   not named twice. `test_a_review_names_its_roles_earlier_nits` fails if a role's earlier nit is
   missing from its prompt, if another role's nit appears in it, or if a handed nit appears twice.
   The prompt fixtures in `tests/prompts/` that hold a round-2 review are updated to match.
5. **R5. The factory files only `med` value.** A weighed `S` or `M` nit of `low` value is `minor`
   with `LOW_REASON` ("weighed low value: below the factory's filing bar"). It is never filed, and
   so it never counts towards the landing's `nits to file` signal. `NIT_CAP` stays 5 (see open
   questions). `test_the_factory_files_no_low_value_nit` fails if a `low` nit gets a `file`.
   `test_carry_disposes_each_nit_by_its_weights`, `test_carry_caps_the_nits_it_files_at_five` and
   `test_a_landing_round_never_changes_the_nits_filed` change their weights so they still test
   what they name: the cap test's nits become `med`.
6. **R6. A landing round still never changes what is filed.**
   `test_a_landing_round_never_changes_the_nits_filed` still passes with R1 to R5 in place. A nit
   only a landing round raised stays `minor` with `NIT_REASON`, and R1's "last round" means the
   build's rounds alone.
7. **R7. A nit can be retired as `duplicate`, `stale` or `wontfix`.** `RETIRE_REASONS["nit"]`
   becomes `("duplicate", "stale", "wontfix")`. `inbox-commit` retires a nit given
   `--reason <id>=<word>` with one of those words. The commit subject is `Retire <id>` and the body
   line is `Reason <id>: <word>`, as an idea's are. No `Sdlc-Retired:` trailer is written, since
   that one is for bugs. Any other word is refused with "a nit's reason is one of
   duplicate|stale|wontfix". `test_inbox_commit_retires_by_the_entry_s_kind` loses its "is a nit:
   ship retires nits" refusal and gains a successful nit retirement and a refused `declined`.
8. **R8. A nit an open change takes in can't be retired from under it.** `inbox-commit` refuses to
   retire a nit that an open change claims. An open change is any change that isn't
   `stage: dropped`. It claims a nit when either holds:
   - the nit's id is on a `Nits taken in:` line in its intent's `## Approach` or its spec's
     `## Requirements`;
   - its `entries.md` holds a `Retire <id>:` line for the nit.

   The refusal names the change: "<id> is taken in by <NNN-slug>: its change retires it at ship".
   An id written in prose, or a dropped change's line, claims nothing.
   `test_inbox_commit_never_retires_a_nit_an_open_change_takes_in` covers all four cases. It fails
   if either claim lets the retirement through, or if prose or a dropped change blocks it.
9. **R9. Core reads `Nits taken in:` exactly as the factory does.** `sdlc.py` gets its own reader
   of the line, a copy of `factory.py`'s `NIT_SECTIONS`, `TAKEN_RE`, `LIST_ITEM_RE`, `taken_lines()`
   and `_section()`, never an import of it. A test runs the cases from `test_land.py`'s
   `named_nits` test through both readers and fails if they disagree on any case.
10. **R10. `/sdlc:idea` retires a nit.** Its Step 2 says a `[nit]` may be retired as `duplicate`,
    `stale` or `wontfix`, said with a line on why. It also says a nit an open change takes in is
    the script's to refuse. It drops "a `[nit]` is ship's", and its *Out of scope* no longer says
    ship alone handles nits. The one WAIT is unchanged: its retire question already covers any
    entry. `test_idea_retires_a_nit` fails if `SKILL.md` doesn't name each word of
    `RETIRE_REASONS["nit"]`. The existing skill tests (rules, WAIT, description) still pass.
11. **R11. The docs say what the code now does.** These are checked by ship's context pass and by
    the `REVIEW.md` class "A doc's claim the change made false":
    - `docs/REFERENCE.md`'s register paragraph ("A nit … is never retired this way") says a nit
      retires through `/sdlc:idea` with its three reasons, unless an open change takes it in;
    - `plugins/factory/README.md`'s nit paragraph ("any other `S` or `M` is filed at landing, at
      most five a change") states R1, R2 and R5;
    - the comments on `RETIRE_REASONS`, `agent_findings()` and `cmd_carry()` match.
12. **R12. Nothing else changes.**
    - `/sdlc:ship` files nits as before.
    - The landing's `nits` signal still fires for every nit that is filed. `landing.py` is not
      edited.
    - Release, publish and measuring never read the register, and
      `test_release_publish_and_measuring_never_read_the_register` still passes.
    - `guide/` and `defaults/` are not edited.

## Design

**Taken as given, checked in the code.**
- `agent_findings()` (`factory.py:2917`) is the one place that decides a factory nit's
  disposition. `carry` writes the record from it (`write_findings()`), and the landing files from
  it (`landing.nit_findings()` → `land_parts()`'s `nits` → `_dispose()`). So a change to its
  rules changes the record, the landing question and the signal together, and `landing.py`
  needs no edit.
- Nits are only ever read from build rounds (`latest` is filled for `kind == "round"` alone).
- `RETIRE_REASONS` and the nit refusal live in `_inbox_commit()` (`sdlc.py:7699–7728`).
- `_open_claims()` already walks `change_dirs(home)` and skips dropped changes.
- `held_entries()` reads an `entries.md`'s `Retire` lines.
- Nothing in core parses `Nits taken in:` today. Only `factory.named_nits()` does, and core's
  `intent` and `spec` skills write the line.

**Filing (R1–R5), all inside `agent_findings()`.** The loop over `found` already looks up
`latest[(role, text)]` and `later`, the complete build rounds of that role after the nit's last
round. The decision order becomes:

1. Unweighed: `minor`, `NIT_REASON` (unchanged).
2. `high` value: `important`, recorded and noted (unchanged).
3. `L` cost: recorded and noted, `IDEA_REASON` (unchanged).
4. **`later` is non-empty:** not filed. The disposition is `minor` with `REPEAT_REASON` when a nit
   from any round in `later` (that role's) has the same `LEAD_RE` path, else `fixed` with
   `FIXED_REASON`. This replaces the `("S", "med") and reworked_round(...) and later` condition.
   `reworked_round()` then stays only if something else calls it; the plan checks.
5. **`low` value:** `minor`, `LOW_REASON`.
6. No path: `minor`, `NO_PATH_REASON` (unchanged).
7. Past `NIT_CAP`: `minor`, `CAP_REASON` (unchanged).
8. Otherwise filed, as now.

A repeat said word for word has the same `(role, text)` key, so step 4 never sees it. It is one
finding whose `latest` is the last round, and it is filed from there. A repeat that has been
reworded has a new key, so the earlier one hits step 4 and only the latest is filed. The path is
used only to choose the earlier finding's label, never to decide whether something is filed. Two
nits on the same file can't merge into one filed nit.

**Asking again (R4).** In `factory.py`'s review prompt builder (around line 5065), beside
`handed`, the role's earlier nits are taken from `state["rounds"]`. These are the nits of the
latest complete `kind == "round"` round before `rnd` in which the role reviewed, minus the ones
in `handed`, each in its original wording with its weights restored (`{theme cost value}`). They
are added through the new `review` part. This is a new part rather than a widened `handed`, so
the rework's `handed` list, which goes to the builder, is unchanged. Whether the list comes from
`run_state.loop_state()` or from the prompt builder is the plan's call. Both read only the
rounds.

**Retiring (R7–R9), in `sdlc.py`.**
- `RETIRE_REASONS["nit"]` gets its three words.
- In `_inbox_commit()`, the `kind == "nit"` refusal is replaced by a check:
  `_nit_claimed_by(k, home)` returns the first open change that claims the nit. It walks
  `change_dirs(home)`, skips any `stage: dropped` change (from `load_change()`), matches ids
  whole on its `Nits taken in:` lines (core's copy of the factory's reader), and reads its
  `entries.md` `Retire` ids (`held_entries()`).
- A claimed nit is refused, and an unclaimed one falls through to the existing reason checks and
  the `Reason <id>:` body line.
- The claims are read once per commit, as `claims` is now.
- The `is_building()` / `_claimed_by()` path stays for ideas and bugs only.

**`/sdlc:idea` (R10).** Its Step 2 *Retire* bullet gains the nit reasons. Its Step 0 already reads
the register and its Step 4 question already reads `Remove <id> … as <reason>`, so the dialog,
the preview and the `inbox-commit … --reason` call are unchanged. The front-matter description
gains "or retire a nit", and no tool rule changes.

**Edge cases.**
- A role that drops out of later rounds when the run's depth changes has no `later`, so its last
  nits are filed.
- An incomplete round never counts as later (only complete rounds count, as now).
- A restart's first round counts as later (R2). With R4 it has been asked about the earlier nits,
  which answers the 221 case: a nit filed after its own restart had fixed it.
- A nit retired from a change's worktree goes through `inbox-commit <id>`'s existing splice, with
  the same guard.

**Boundaries.**
- **Always:** every agent nit keeps a `findings.md` section with its reason. Every nit the factory
  files still raises the landing's `nits` signal, so no agent's nit is filed without the
  person's yes.
- **Asks first:** each retirement goes through `/sdlc:idea`'s one WAIT.
- **Never:** edit the register on the change's branch, retire a nit an open change claims, touch
  `landing.py`, `guide/` or `defaults/`, add a config key, change ship's own filing, or retire
  today's nits from inside this change (see open questions).

## Contracts touched

- **The register: `inbox-commit` is the only code that commits it alone, always on the base
  branch.** Unchanged. A nit's retirement is one more `Retire <id>` that `inbox-commit` makes,
  under `_main_lock()`. The entry is never removed on this change's branch.
- **Retiring needs a reason from `RETIRE_REASONS`.** Kept: the nit's tuple stops being empty. The
  reason goes in a `Reason <id>:` body line, as an idea's does. **No `Sdlc-*` trailer is added or
  changed.** `retired_entries()` already reads every `Retire` subject, so the retro counts a
  retired nit with no new format.
- **"`sdlc.py` only reads nits, and the skills write them."** Still true. `/sdlc:idea` deletes the
  entry and `inbox-commit` commits it.
- **"A nit to file is a signal, so no agent's nit is filed without the person's yes"**
  (`landing._signals()`). Kept as is. Fewer nits are filed, so the signal fires less, and the
  rule is untouched.
- **Skills: one WAIT, an `AskUserQuestion` dialog with a preview, narrow `allowed-tools`.**
  `/sdlc:idea` keeps its one WAIT and its one `inbox-commit` rule, and runs no new command.
- **The factory never imports `sdlc.py`, and each reads the other's files with copies of its
  parsing, pinned by tests.** R9's reader is such a copy, held by core this time, since core's
  skills write the line, and pinned by R9's test. Under the policy's pinning list this is a new
  pin. It is not a new import.
- **`[review] sensitive`.** The design avoids `landing.py`. `factory.py`, `run_state.py`,
  `prompts/review.md` and `sdlc.py` are not sensitive paths, so the change gets the ordinary
  review depth, and ship's preflight decides that.
- **`[review] irreversible` (`defaults/`, `templates/`) and the rule that changing `guide/` or
  `defaults/` needs `sdlc.py record`.** Neither is touched. The guide's "nits cap at 5" is about
  ship, which this change leaves alone.
- **Release, publish and measuring never read the register.** Untouched (R12).
- **An earlier decision (129 R5) is reversed** (see the top of *Requirements*). It is not a policy
  invariant, but it is pinned by a test, and that test is replaced deliberately, not loosened.

## Alternatives rejected

- **Matching a reworded repeat by `path:line`.** Lines move between rounds, because the rework
  edits the file, so a real repeat would be missed. Matching by path alone would merge two
  different nits on the same file into one filed nit. The path is only used to label the earlier
  finding, never to decide whether it is filed.
- **The reviewer marking a repeat** (`- NIT: REPEAT …`). The filing would then rest on a model's
  formatting, and a missed mark files twice. R1 and R4 decide from the rounds alone, as the rest
  of `agent_findings()` does.
- **Text similarity between nits.** A threshold no one can check, and nondeterministic across
  wordings. Not the script's way.
- **Keeping the "handed `S med` only" rule and just asking again.** That would leave 221's
  `.yaml` case filed (`M`, never handed). The intent asks for "whatever its weights".
- **Removing the landing's `nits` signal** so a nit never stops a batch. That breaks "no agent's
  nit is filed without the person's yes". Fewer, truer nits stop fewer batches instead.
- **A host config key for the floor or the cap.** The intent didn't ask for one, and it would mean
  more `READS_CONFIG`, setup and drift work. The constants stay in `factory.py`.
- **`stale` folded into `wontfix`.** The intent lists three reasons, and they mean different
  things to the retro: "the code it names has moved on" versus "true, but not worth doing".
- **Retiring today's duplicates and stale nits inside this change**, as held `Retire` lines in its
  `entries.md`. Those lines are for nits a diff fixes or makes moot, which is ship's rule. A
  change that hand-picks stale entries from a register still moving on the base branch would be
  out of date by its landing. `/sdlc:idea`, once this lands, is the tool for it.
- **Applying the factory's bar to `/sdlc:ship`.** Ship shows every nit to a person, who approves
  each one, so its noise is already judged. Left as an open question, not done.

## Verification

```bash
./check.sh
uv run --group dev pytest -q -n auto tests/test_factory_loop.py tests/test_bugs.py tests/test_skills.py tests/test_land.py tests/test_modules.py
uv run --group dev pytest -q -n auto -k "reworded_is_filed_once or fixed_whatever_its_weights or not_filed_says_why or names_its_roles_earlier_nits or files_no_low_value_nit or takes_in or retires_a_nit"
```

Healthy output:
- `check.sh` ends green: ruff check, ruff format, the whole suite and
  `claude plugin validate --strict`.
- Each new test named in R1–R10 runs and passes.
- `test_a_nit_not_raised_again_is_still_filed` no longer exists, since it is replaced by R2's
  test.
- `grep -n "is a nit: ship retires nits" -r scripts tests` prints nothing.
- `grep -n "at most five a change" plugins/factory/README.md` prints nothing.

After landing, by hand:
1. `/sdlc:idea 2026-11-21-55`, retired as `stale`, shows `Remove 2026-11-21-55 … as stale and
   commit it as "Retire 2026-11-21-55"?`. Its yes makes one commit on the base branch with
   `Reason 2026-11-21-55: stale` in the body.
2. Retiring a nit that an open change's `Nits taken in:` line names is refused, and the refusal
   names that change.

