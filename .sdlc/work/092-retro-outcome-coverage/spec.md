---
id: 092
slug: retro-outcome-coverage
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 092 — Retro checks its goals and the work against the outcomes · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

**Assumptions, checked in the code:**
- `direction_items()` and `product_items()` are both `doc_items()` (`scripts/sdlc.py:5888–5979`).
  Its `problems` become `retro-commit` refusals (`scripts/retro.py:1200`), so anything this change
  reports must stay out of `problems`.
- `_product()` (`scripts/retro.py:146`) runs only when there is a product doc. `retro()` already
  works out each closed change's start (`bases`, `scripts/retro.py:720–726`) from `_change_base()`,
  which is `Sdlc-Base`: where the base branch was when close merged the change. The register on
  the base branch at that commit still holds the change's seeds, because ship deletes them on the
  change's branch and the deletion only reaches the base branch at the merge.
- `next_up()` reads `direction_items()` for a milestone's `id`, `name`, `title`, `status` and
  `groups` only (`scripts/sdlc.py:6116–6170`). `board.py` doesn't read the direction doc.
- `TEMPLATE_READS` has no entry for `direction.md`, so no host's override of it is checked.

**Requirements:**

1. **R1. A goal cites outcomes with a trailing `(O1, O3)`.** `direction_items()` gives every item a
   `serves` list. For a goal it is the outcome ids in a parenthetical at the end of its title, or,
   for an open goal whose line wraps, at the end of its last indented continuation line (D1), as
   text and in order. The list is `[]` when there is no parenthetical, or when the parenthetical
   holds anything other than `O<n>` ids. The goal's `title` and `name` are unchanged, so the
   parenthetical stays in `title` as it does today. Test:
   `test_a_goal_cites_the_outcomes_at_the_end_of_its_line` in `tests/test_retro.py` covers
   `- G6. … (O2)`, `- G7. … (O1, O3, O6)`, a struck goal with a citation, `(see below)` (gives
   `[]`) and no parenthetical (gives `[]`).
2. **R2. A milestone cites outcomes, its goal, or both, on a `Serves:` line.** The line sits in the
   milestone's body beside `Groups:`, for example `Serves: G7, O4`. Its `serves` list is the
   `G<n>`/`O<n>` tokens of the first such line under that heading, and any other words are ignored.
   A `Serves:` line outside a milestone (under a goal, or in the product doc) is ignored. Test:
   `test_a_milestone_cites_on_its_serves_line` (first line wins, other words ignored, nothing read
   outside a milestone, `Groups:` read exactly as before beside it).
3. **R3. Citations never add a problem.** A doc with no citations, a malformed one, or one naming
   an id neither doc holds gives the same `problems` as before. So `retro-commit` never refuses
   because of a citation. Test: `test_citations_never_add_a_problem` runs `doc_items()` over each
   case. `test_retro_commit_takes_an_uncited_goal` runs `retro-commit` on a new direction doc with
   an uncited open goal and milestone, and it commits.
4. **R4. A doc without citations reads as before.** For a direction doc with no citation,
   `direction_items()` returns what it returns today, except that each item also has
   `serves: []`. `status`'s Next up is identical too. Tests: the existing
   `test_the_templates_example_parses_to_its_ids` and `tests/test_next_up.py` still pass
   unchanged. `test_next_up_is_the_same_with_and_without_serves_lines` shows a `Serves:` line under
   a milestone changes nothing in `next_up()`'s output.
5. **R5. `product.uncited` names the open goals and milestones that reach no open outcome.** With
   a product doc, `retro`'s `product` block gets `uncited`. It has one row per open goal or
   milestone whose citations reach no open outcome, in direction-doc order. Each row is
   `{id, kind, name, title, serves, reaches, why}`:
   - `reaches` is the outcome ids it cites, plus, for a milestone, those of each goal it cites.
   - `why` is `none` when it cites nothing, `closed` when everything it reaches is a struck
     outcome, and `unknown` when it cites only ids neither doc holds.

   An item that reaches at least one open outcome is not listed. A struck item is never listed.
   Test: `test_retro_names_goals_and_milestones_that_reach_no_open_outcome` uses a fixture repo with
   one item of each `why`, a milestone covered only through its goal (not listed), and a struck
   uncited goal (not listed).
6. **R6. `product.none_themes` groups the `none` changes by their seeds' themes.** It has one row
   per theme: `{theme, changes, recurring}`. `changes` lists change names in close order. Rows are
   ordered by count descending, then theme. Where the theme comes from:
   - A change's themes are the `Theme:` lines of the seeds its `idea:` names. Each seed is looked up
     with `ref_matches()` in the register as it stood at the change's base (`bases`), read with one
     `git show` per distinct base.
   - A change counts once under each distinct theme it has.
   - A change with no seed, no base, no register at its base, or no `Theme:` line counts under
     `NO_THEME` (`(no theme)`).

   `none` and every other existing key of `product` is unchanged. Test:
   `test_none_changes_are_grouped_by_their_seeds_themes` uses a fixture with two themed seeds
   shipped as `serves: none` changes and one change with no seed. It fails if a seed's theme is read
   from today's register (where ship has deleted it) rather than the change's base.
7. **R7. A theme recurs at `NONE_THEME_RECURS` (3) changes in the window.** `recurring` is true
   when a theme other than `(no theme)` has at least that many changes. `(no theme)` never recurs,
   because there is no theme to propose an outcome for. Test:
   `test_a_theme_recurs_at_three_none_changes` (2 → false, 3 → true, three themeless → false).
8. **R8. The template asks for citations.** `templates/direction.md`'s fenced example shows a goal
   with `(O1)` and a milestone with `Serves: G1`. Its Goals and Milestones prompts ask for them.
   Tests: `test_the_templates_example_parses_to_its_ids` is extended to assert G1's and M1's
   `serves`. `tests/test_defaults.py`'s shape tests still pass. `test_the_template_itself_holds_no_items`
   still passes.
9. **R9. The retro skill uses the new fields and changes nothing it may write.**
   `skills/retro/SKILL.md` Step 0 describes `serves`, `uncited` and `none_themes`:
   - Pass 4 names each `uncited` item with its `why`. For each `recurring` theme it proposes a new
     outcome line numbered from `product.next_ids`, with a short bold name, or gives its reason for
     not doing so under Dropped findings.
   - Pass 5 drafts every goal with its outcome citation and every milestone with a `Serves:` line.
   - The Step 5 WAIT question is unchanged: its product-doc form already covers outcome lines.

   Tests: the existing `tests/test_skills.py` invariants (one WAIT, rules, `READS_CONFIG`) and
   `test_the_retro_keeps_evidence_and_the_product_docs_prose_out_of_what_it_writes` still pass. A
   new `test_the_retro_skill_names_the_coverage_fields` asserts that `uncited`, `none_themes`,
   `recurring` and `Serves:` appear in `SKILL.md`.
10. **R10.** `docs/REFERENCE.md`'s paragraph on goals and milestones (around line 765) states both
    citation forms and that an uncited item is reported, never refused. `./check.sh` passes.

## Design

**Reading citations: `doc_items()`.** Both forms are read here, so `status`, `retro` and
`retro-commit` share one reader and nobody re-parses.
- Every item gets `"serves": []`.
- For a goal, a new `CITES_RE = re.compile(r"\((O\d+(?:\s*,\s*O\d+)*)\)\s*$")` is matched against
  the item's title, and the ids are split on commas. The struck form's title already excludes the
  `~~` and the status, so struck goals parse the same way.
- For a milestone, `SERVES_RE = re.compile(r"^Serves:\s*(.+)$")` is read under the current
  milestone, exactly as `GROUPS_RE` is: first line only, with `current` reset at any heading.
  `re.findall(r"\b[GO]\d+\b", …)` takes the ids.
- Ids are kept as text, like every other id.
- Nothing is appended to `problems` (R3).

**Coverage: `_product()`.** It gains two parameters, `direction` (the `direction_items()` dict
`retro()` already builds) and `bases` (already built). `retro()` passes both. Two new helpers in
`scripts/retro.py` keep `_product()` short:

- `_uncited(direction_items, product_items) -> list[dict]` works as follows:
  - Open outcome ids are `open_o` and every outcome id is `all_o`. Goals are indexed by id.
  - For each open goal, `reaches` is its `serves`.
  - For each open milestone, `reaches` is its `O` ids plus the `serves` of each `G` id it names
    that the doc holds, at any status, de-duplicated in order.
  - `why` follows R5. A milestone citing an unknown `G` id counts as citing an unknown id.
- `_none_themes(home, changes, bases) -> list[dict]` works as follows:
  - It takes the `serves == ["none"]` changes and groups their bases.
  - For each base it reads `sdlc._git(home, "show", f"{base}:{sdlc.work_rel(home)}/{sdlc.INBOX}")`
    once, parses it with `sdlc.parse_entries()`, and caches the result by sha.
  - For each change, it matches each `sdlc.ideas_of(rec)` reference with `sdlc.ref_matches()` and
    takes `sdlc.entry_theme()`.
  - It builds the rows and `recurring` from `NONE_THEME_RECURS = 3`, a module constant beside
    `RATE_MIN_CHANGES`. `NO_THEME` is `sdlc.NO_THEME`, the label status already uses.
  - A failed `git show` (None) is an empty register, never an error.
  - Only the work path is read, never `HISTORY_WORK`: retro reads only where the folder is now
    (AGENTS.md).

Returned beside the old keys: `"uncited": …, "none_themes": …`.

**Why the change's base, not today's register.** Ship deletes the seeds on the change's branch, so
the register at `Close^` and on today's base branch no longer holds them. At the change's base
(`Sdlc-Base`: the base branch's tip when close merged), the register still does, with whatever
`Theme:` a retrospective gave it up to then. That is the latest theme the seed ever had on the base
branch. Before `Sdlc-Base`, `_change_base()` falls back to the parent of the first commit holding
the intent. That is earlier, but still after the seed was filed.

**Template.** In `templates/direction.md`:
- The note's fenced example becomes `- G1. No one loses a draft (O1)`, with `Serves: G1` under M1
  beside its `Groups:` line. The note gets one sentence: a goal ends with the outcomes it answers
  to, a milestone's `Serves:` line names its goal or outcomes, and `sdlc.py retro` reports an open
  one that reaches none.
- The Goals prompt adds "ending with the outcomes it answers to, `(O1, O3)`". The Milestones prompt
  adds "a `Serves:` line naming the goal it reaches (and so its outcomes) or the outcomes
  themselves".
- No new heading, so `TEMPLATE_READS` is untouched.

**Skill.** In `skills/retro/SKILL.md`:
- Step 0's `direction` and `product` bullets name the new fields.
- Pass 4 adds: name each `uncited` item as `G7 (…)` with its `why`, and for each `recurring` theme,
  either propose `- O<next>. **<name>.** …` covering that work, or give the reason it isn't an aim
  under Dropped findings. A `(no theme)` group is named as a count only.
- Pass 5 adds: every goal drafted ends with its citation, and every milestone has a `Serves:` line,
  an outcome proposed in pass 4 included.
- Step 4 already drafts new outcome lines from `product.next_ids`, and Step 5's question already
  names outcome lines, so neither changes.

**Edge cases:**
- No product doc: `product` is null, so neither field exists. The direction doc's `serves` is
  still read.
- A direction doc with no ids: no items, so `uncited` is `[]`.
- A milestone citing a struck goal still reaches that goal's outcomes. Whether the milestone should
  outlive its goal is pass 5's judgment, not a count.
- A product doc with no open outcomes: every cited open item is `closed` or `unknown`, and every
  uncited one is `none`.

## Contracts touched

- **Retrospectives (AGENTS.md):** `retro` stays read-only, and the only new git call is `git show`.
  `retro-commit` still writes only the direction doc, the register, the product doc and its report.
  Its refusals are unchanged, because citations never reach `problems` (R3). Uncited items are
  reported in `retro`'s JSON and judged by the skill, as the intent's Constraints require.
- **Product doc prose is the person's:** the skill proposes outcome lines only, behind the existing
  WAIT. Users, problem, measures and bets are untouched (SKILL.md's Out of scope, unchanged).
- **A new JSON field is added beside the old:** `uncited` and `none_themes` are new keys, and
  `none`, `unlinked`, `unserved`, `stale` and `outcomes` keep their shape. `serves` is a new key on
  every `doc_items()` item. Nothing reads items by equality of the whole dict, except
  `product_items()`'s empty-doc test, whose `items` stays `[]`.
- **Frontmatter and ids are read as text:** the citation ids are regex tokens, never ints.
- **Never match an entry by title alone:** seeds are looked up with `ref_matches()`, id to id and
  quoted title to title.
- **One shape for the shipped docs:** the template keeps its title, its `>` note (the example fenced
  inside it) and `##` sections with every `<…>` prompt inside one. `templates/` is `irreversible` in
  this repo's `[review]`, so ship adds `How to recover:`. A host overriding `direction.md` in
  `.sdlc/templates/` keeps its own prompts and loses nothing, since the citation is optional. That
  is why no `TEMPLATE_READS` entry is added: one would make `drift` call every such override
  `breaking`.
- **`status` reads `direction_items()` for Next up:** its reading is unchanged (R4).
- **`guide/` and `defaults/` are untouched,** so `sdlc.py record` doesn't need to run.
  `guide/process.md`'s sentence on goal and milestone forms stays true, because citations are
  optional.
- **No invariant needs to move.**

## Alternatives rejected

- **A citation on the milestone heading, `### M12. Each rule is said once (G7)`.** It would land in
  the milestone's `title`, which status shows in Next up when there's no bold name (`next_up()`'s
  `m['name'] or m['title']`), and a heading is the item's name, not its links. A body line beside
  `Groups:` is the form milestones already use for links.
- **A `Serves:` line under each goal.** Goals are one-line list items with no body, and this repo's
  goals already end `(O2)`. Reading the habit that exists means no doc has to change shape.
- **Milestones that cite only goals (or only outcomes).** A milestone like M15 answers to an
  outcome with no goal between, and forcing one would invent a goal. Allowing either form on one
  line costs one regex.
- **Recording a theme in `intent.md`.** It is a new frontmatter key on every intent, asked at every
  intent, for one retro reading, and history's intents would still have none. The seed's `Theme:`
  is already where themes live, and history keeps it.
- **Reading the theme from today's register or `Close^`.** Ship has deleted the seed by then, so
  every `none` change would read as `(no theme)`.
- **`retro-commit` refusing an uncited open item.** The intent's Constraints rule this out for
  existing docs ("reported, never refused"). Refusing only *new* ones would make the commit diff
  two docs' item sets for a check the person already sees at the WAIT. If the reported list
  doesn't shrink over a retrospective or two, refusing is a later change.
- **Recurrence across two retrospectives.** It needs the previous window's `none` changes and
  their themes: a second walk and a second set of register reads for each retro. One window at
  three changes catches the case the intent cites (8 of 27), and the person still decides.
- **Putting uncited items in `doc_items()`'s `problems`.** Problems refuse the commit.

## Verification

```bash
uv run --group dev pytest tests/test_retro.py tests/test_next_up.py tests/test_skills.py tests/test_defaults.py -q
./check.sh
uv run --quiet --script scripts/sdlc.py retro | python3 -c 'import json,sys; p=json.load(sys.stdin)["product"]; print(json.dumps({k: p[k] for k in ("uncited","none_themes","none","unserved")}, indent=1))'
uv run --quiet --script scripts/sdlc.py status
```

Healthy output:
- The pytest run passes, with the new tests named in R1–R9 among them. `./check.sh` ends green
  (ruff, the format check, pytest and `claude plugin validate --strict`).
- On this repo, `product.uncited` lists M10–M15 with `why: none`, because none has a `Serves:`
  line yet; this repo's next retrospective adds them. It does not list G6, G7 or G8, which already
  end `(O…)`. `product.none_themes` is a list (empty or short, since the window began today), and
  `product.none` is the same list it printed before the change.
- `status`'s Next up reads the same before and after.

