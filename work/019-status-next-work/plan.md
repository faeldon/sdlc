---
id: 019
slug: status-next-work
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 019 — Status recommends what to work on next, not only how to advance what's open · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Context

`/sdlc:status` only advances open changes; with none open it says "run `/sdlc:intent`", and the
real "what's next" (a milestone's remaining seeds, a phased series, a host bug, nits) takes a
conversation, because the skill rightly never reads `work/ideas.md` or the direction doc. Spec
`work/019-status-next-work/spec.md` (R1–R11): `sdlc.py status` collects and orders candidates in a
`■ Next up` section by a fixed rule table; the skill picks one. Two new, optional seed forms: a
`[bug]` tag and an `After: "<title>"` line.

One refinement of the spec's Design: `next_up()` is called from `main()`'s status branch beside
`unreleased()`/`retro_due()` (`scripts/sdlc.py:5460`), not inside `analyze()`, so `check` never
pays for it and its output can't change (R9). Recorded in plan.md.

## Files to change

- `scripts/sdlc.py` — `idea_entries()` (:879) gains `after`; new `AFTER_RE`, `NEXT_RULES`,
  `NEXT_SHOWN = 5`, `_seed_state()`, `next_up()`; `main()` status branch sets `a["next_up"]`;
  `print_status()` (:5156) prints the section after Unreleased, before Setup.
- `tests/test_sdlc.py` — new tests (below).
- `skills/status/SKILL.md` — precedence list (:114) per R10; Step 1's "nothing open → /sdlc:intent"
  becomes "→ the first Next up line, else /sdlc:intent"; say the Next up section is read from the
  output like the rest (no new reads, no allowed-tools change).
- `skills/retro/SKILL.md` — one sentence: phased seeds carry `After: "<earlier seed>"`.
- `templates/ideas.md` — note names `[bug]` and the `After:` line.
- `docs/REFERENCE.md` — near the `work/ideas.md` paragraph (:206): the two forms and the Next up
  order.
- `work/019-status-next-work/plan.md` — this plan, trimmed to the template.

## Work order

1. **Read `After:`.** `AFTER_RE = re.compile(r"^After:\s*(.+)$")`; in `idea_entries()` each entry
   dict gets `"after": []`, and a matching line under the current entry sets it from
   `re.findall(r'"([^"]+)"', …)` (as `doc_items()` does for `Groups:`). Existing callers
   (`analyze()` orphan check, `_milestone_verdicts()`) only use date/status/title — unaffected.
   Test, then stop.
2. **`_seed_state(entry, open_titles, building_titles)`** → `building` (tag `[building]` via
   `is_building()`, or title in the open changes' `idea:` titles via `_seed_title()`), `waiting`
   (any `after` title in `open_titles` and not building), else `ready`.
3. **`next_up(home, cfg, open_changes, today)`**, pure apart from reads:
   - `main = main_root(home)`; `ideas = idea_entries(main)`, `nits = nit_entries(main)[0]`,
     `doc = direction_items(_direction_text(home, cfg))`.
   - `building` = titles from `_seed_title(rec["idea"])` for open changes with `idea:`.
   - `NEXT_RULES` tuple, in R5's order: `("bug", …)`, `("milestone", …)`, `("series", …)`,
     `("nits", …)`, `("seed", …)`; each a label and a collector; walk them in order, skipping a
     title already taken (R5 "once, under its highest rule").
     - bug: ready entries whose tag lower-cases to `bug`, by date.
     - milestone: for open milestones in doc order, first `groups["seeds"]` title that is an open
       ready entry; label `M1 (name)`.
     - series: ready entries with non-empty `after`, label `next in series after "<title>"`.
     - nits: cost `S`, grouped by theme (reuse `nits_summary()` shape: count, oldest), oldest
       first; command `/sdlc:intent pay down the [<theme>] nits`.
     - seed: remaining ready entries, oldest first.
   - `done_milestones`: only when an open milestone exists, `_milestone_verdicts(home,
     doc["items"], open_names)`; a milestone whose rows are all `closed`/`shipped`/`vanished`
     (and has at least one row).
   - `warnings`: an `after` title not an entry title and not any `closed_changes()` `idea`
     (history walked only if some `after` is dangling against the register); loops by DFS over
     waiting entries' `after` edges, reported once per cycle.
   - Items `{rule, label, title, age_days, command}`; age via `_age_days({"created": date})`.
4. **Wire and print.** `main()`: `a["next_up"] = next_up(home, cfg, a["open"], …)`.
   `print_status()`: when items or done_milestones or warnings, print
   `\n■ Next up: N`, the first `NEXT_SHOWN` lines as
   `    {label:<…} {title}  {age}d  → {command}`, `(+N more)`, each done milestone line, each
   `⚠` warning. Nothing printed otherwise (R1).
5. **Skill + docs** (R10, R11), then `./check.sh`.
6. Save `plan.md`, set `stage: build` in intent.md.

## Tests

In `tests/test_sdlc.py`, with neutral titles.

- R4 `test_idea_entries_reads_after_lines` — quoted titles, multiple, none.
- R2 `test_next_up_is_empty_without_registers` and one per register alone; status prints no
  section with none (R1).
- R3 `test_next_up_skips_a_seed_an_open_change_builds` — `[building]` tag, and `idea:` in a
  worktree while main says `[seed]` (reuse the worktree fixture from
  `test_status_sees_changes_in_every_worktree_from_any_checkout`, :720).
- R4 `test_a_seed_waits_while_its_after_seed_is_open` — waiting hidden; after removal, labelled
  `next in series`.
- R5 `test_next_up_orders_by_rule` — fixtures firing all five; asserts order and single
  appearance of a seed that is both milestone-grouped and a bug.
- R6 commands per kind; R1 cap `(+N more)` with 7 seeds.
- R7 `test_a_milestone_with_nothing_left_says_so` — git repo with a `Close` commit whose intent's
  `idea:` names the grouped seed.
- R8 dangling `After:` and a two-seed loop → `⚠` lines; `check --strict` still exits 0.
- R9 existing status/check tests pass unchanged (`pytest -q` whole suite).
- R10/R11 `tests/test_skills.py` passes (allowed-tools unchanged); `test_defaults.py` shape of
  `templates/ideas.md`; `test_nothing_local.py`.

## Verification

```bash
./check.sh
uv run --group dev pytest tests/test_sdlc.py -q -k "next_up or idea_entries or status"
uv run --quiet --script scripts/sdlc.py status
```

Expect `■ Next up` with M1's "Evidence for this repo's retrospective" and M3's "Rework ignores
shared docs and the setup record" first, S nit themes if any, plain seeds by age, and
"M2 has nothing left in its groups"; earlier sections unchanged.

## Rollback

`git revert` of the change's commit. Nothing outside the repo; an `After:` line or `[bug]` tag a
host wrote stays harmless prose to an older script.
