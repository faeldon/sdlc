---
id: 019
slug: status-next-work
kind: spec
created: 2026-10-25
updated: 2026-10-25
---

# 019 — Status recommends what to work on next, not only how to advance what's open · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. `sdlc.py status` prints a `■ Next up` section after `Unreleased` and before `Setup`/`Retro
   due`/`Problems`: at most 5 candidates, then `(+N more)`. With no candidates the section is left
   out, as `Unreleased` is.
2. Candidates come from the **main checkout's** `work/ideas.md`, `work/nits.md` and direction doc
   (`docs.direction`), whichever checkout runs `status`. A missing file contributes nothing and
   never raises; tests cover a repo with none of the three, and each alone.
3. A seed being built is never a candidate: tagged `[building]`, or its title matched by an open
   change's `idea:` in any worktree (a branch tags its seed while `main` still says `[seed]`).
   Tested with a change open in a worktree.
4. A seed's body may carry `After: "<title>"[, "<title>"]`, the same shape as a milestone's
   `Groups:` line. The seed is **waiting** while any title it names is still an open, not-building
   seed; otherwise it is **ready**. A waiting seed is never a candidate. `idea_entries()` returns
   `after: [titles]`, read as text. A ready seed whose `After:` titles have all left the register
   is labelled `next in series after "<title>"`.
5. Candidates are ordered by these rules, one ordered table in the code and the same in
   `docs/REFERENCE.md`:
   1. entries tagged `[bug]`, oldest first;
   2. for each open milestone in doc order, the first `Groups:` seed that is open and ready,
      labelled with the milestone's id and name;
   3. ready seeds labelled `next in series`, oldest first;
   4. open nits of cost `S`, one line per theme (count, oldest date), oldest theme first;
   5. every other ready seed, oldest first.

   A candidate appears once, under its highest rule. A test pins the order with fixtures that
   fire all five.
6. Each line shows the rule's label, the title, its age in days and the command that starts it:
   `/sdlc:intent <title>` for a seed or bug, `/sdlc:intent pay down the [<theme>] nits` for a nit
   theme.
7. An open milestone whose `Groups:` changes are all closed and seeds all shipped or gone gets one
   line under the list, not counted in the 5: `M2 has nothing left in its groups: /sdlc:retro
   decides whether it's done`. It reuses `_milestone_verdicts()`.
8. An `After:` title naming no open seed and no change in history whose `idea:` matches, and seeds
   that wait on each other in a loop, each get a `⚠` line in the section. Neither is a `check
   --strict` problem. Tested.
9. Nothing existing changes: every current status section and `check --strict` result is the same
   for a repo whose ideas carry no `After:` and no `[bug]`, and the existing status tests pass
   untouched.
10. `skills/status/SKILL.md`'s precedence becomes: check problems → open change at build or later →
    ready to close → a change others depend on → lowest-tier open change → release due
    (`Unreleased` lists changes) → retro due → the first `Next up` line → `/sdlc:intent`. The
    skill still reads nothing beyond Step 1's output, and its `allowed-tools` doesn't change.
    `test_skills.py` passes.
11. `templates/ideas.md`'s note names the `[bug]` tag and the `After:` line; `docs/REFERENCE.md`
    documents both and the `Next up` order; `skills/retro/SKILL.md` says to write `After:` when it
    proposes phased seeds. `defaults/` is unchanged.

## Design

**Reading.** `idea_entries(root)` grows an `after` list: while scanning lines, a line under an entry
matching `^After:\s*(.+)$` has its quoted titles extracted, with the same
`re.findall(r'"([^"]+)"', …)` that `doc_items()` uses for `Groups:`. The rest of an entry stays
prose.

**Collecting.** A new pure function `next_up(home, cfg, changes) -> dict`, called from `analyze()`
beside `retro_due`, takes `idea_entries(main_root)`, `nit_entries(main_root)[0]`,
`direction_items(_direction_text(home, cfg))`, the open changes' `idea:` values (from `changes`,
which already spans every worktree), and `_milestone_verdicts()` only when the doc has an open
milestone (it walks history, so a repo with no direction doc doesn't pay for it). It returns
`{"items": [...], "done_milestones": [...], "warnings": [...]}`, each item
`{rule, label, title, age_days, command}`. The rule table is a module-level tuple `NEXT_RULES` in
R5's order, so the order is read, not inferred from sort keys. Seed "state" (building / waiting /
ready) is one helper; a loop is found by walking the waiting seeds' `After:` edges.

**Printing.** `print_status()` adds the section per R1. It never touches the open-change section;
the skill does the cross-section precedence (R10), and the script never compares open work with
seeds.

**Command text.** Seed titles are passed as written: `/sdlc:intent` already reads its argument as
the human's own description and looks for a matching seed.

## Contracts touched

- **Mechanism vs. judgment.** Collecting and ordering is mechanical and goes in `sdlc.py`; picking
  one and saying why stays in the skill. The order is a fixed, documented table, never a score.
- **Always Tier 2: changes what `sdlc.py` reads in a host.** It adds an `After:` line and the
  meaning of a `[bug]` tag, both optional; a register with neither reads exactly as today (R9).
  Nothing writes them but a person or the skills. `TEMPLATE_READS` covers template headings and
  keys; this adds none, so it gets no entry.
- **Narrow `allowed-tools`.** Untouched: no new subcommand (R10).
- **Text, never YAML.** `After:` is parsed by regex, like `Groups:`.
- **`status` is read-only and in `READ_ONLY`.** It still runs no host command;
  `_milestone_verdicts()` reads git only.
- **Nits: release and publish never read the register.** Unaffected; status already reads it via
  `check`.
- **Nothing local.** Test fixtures use neutral seeds (`reopen-drafts`-style titles).

## Alternatives rejected

- **A separate `sdlc.py next-up` subcommand.** It needs an `allowed-tools` rule, a `READ_ONLY`
  entry and a second call in the skill for what belongs in "what's next"; a section costs nothing
  when empty.
- **Letting the skill read `ideas.md` and the direction doc.** It breaks the skill's budget, the
  reason it exists.
- **A score or weights.** It hides the order in numbers nobody can argue with line by line, and
  invites optimising them.
- **Detecting series and bugs from prose** ("first phase", "Raised … by a host"). Too loose to
  trust.
- **Making broken `After:` lines a `check --strict` problem.** A seed typo would fail every
  change's gate; seeds aren't committed work.
- **Waiting for the bugs register.** That seed is still weighing its shape; a `[bug]` tag costs
  nothing, and the register can replace it.

## Verification

```bash
./check.sh
uv run --group dev pytest tests/test_sdlc.py -q -k "next_up or idea_entries or status"
uv run --quiet --script scripts/sdlc.py status
```

Healthy in this repo: `■ Next up` lists M1's "Evidence for this repo's retrospective" and M3's
"Rework ignores shared docs and the setup record" ahead of plain seeds, the S-cost nit themes if
`work/nits.md` holds any, and the line saying M2 has nothing left in its groups; every section
above it is unchanged.
