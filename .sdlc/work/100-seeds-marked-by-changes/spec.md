---
id: 100
slug: seeds-marked-by-changes
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 100 — Open changes mark their seeds without editing the register · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. `/sdlc:intent` no longer edits the register when it opens a change from a seed, in a single run or a batch. `skills/intent/SKILL.md` Step 5 sets `idea:` (and `fixes:` / `closes:` as now) and stops there: it has no instruction to retag an entry `[building]`, to write a `Building in .sdlc/work/NNN-slug/.` line, or to `Edit` the register. `batch.md` Step 5.3 writes only the intent and its frontmatter lines. A test in `tests/test_skills.py` fails if either file still says `becomes \`[building]\``, `Building in .sdlc/work/` or `Edit\` each entry`. The existing `test_intent_takes_a_theme_s_seeds_as_one_change` changes to match: it keeps the `idea: [..]` list and "`sdlc.py ship` deletes each entry by it", and drops the `Edit` assertion.
2. R2. An inbox commit on the base branch while a change is open does not stop the change's rebase. The test opens a change whose intent names a seed (`idea:`), with the seed as the register's last entry. It then runs `inbox-commit` from the main checkout to file a new entry right after the seed, and runs `sdlc.py base` on the change. The rebase must succeed with no conflict and with the register on the change's branch matching the base branch's. A control in the same test applies the old tag edit on a second branch and asserts that rebase does conflict, so the test can't pass vacuously.
3. R3. `status`'s `next_up` returns `building`: one item per register entry being built (`id`, `title`, `kind`, `change`). An entry counts when an open change names it on its `idea:` or `fixes:` line (`_open_claims()`), and `change` is that change's folder name. A legacy `[building]` tag that no open change names also counts, with `change: null`. Plain `status` prints `N being built` beside `N waiting on earlier seeds`. `status --all` lists each one as `<id> <title> — NNN-slug`, or `— tagged [building]` for a legacy tag. Tests in `tests/test_next_up.py` fail if an untagged `[idea]` named by an open change is missing from `building`, appears among the candidates, or carries the wrong `change`.
4. R4. `sdlc.py bugs` and `sdlc.py nits` (and so `preflight`'s nits) give each entry a `building` key: the folder name of the open change whose `idea:` or `fixes:` names it, or `null`. Tests in `tests/test_bugs.py` and the nits tests fail if a bug named by an open change's `fixes:` reads `null`, or if an unnamed one doesn't.
5. R5. `sdlc.py groups` keeps refusing an id an open change holds, naming that change (`<slug>: <id> is taken by NNN-slug`), with no tag on the entry. A test fails if `groups` accepts an untagged `[idea]` named by an open change's `idea:`.
6. R6. `sdlc.py ship` still deletes each seed named on the `idea:` line, whatever its tag. A test fails if ship leaves behind an untagged `[idea]` entry that `idea:` names, by id or by quoted title.
7. R7. A dropped change gives its seed back without any edit. Once the change is stamped `stage: dropped`, its seed leaves `next_up`'s `building` and comes back as a candidate, `groups` accepts its id, and `inbox-commit` may retire it with a reason. A test fails if any of those still treats the seed as taken.
8. R8. History's `[building]` tags still read as before, for good. An entry tagged `[building]` counts as being built: `next_up` leaves it out of the candidates, `inbox-commit` refuses to retire it, and `groups` refuses it. `check --strict` reports one with nothing behind it as an orphan idea and stays quiet when a change folder or an open change's `idea:` covers it. `check` raises nothing for an untagged entry an open change names. The existing tests (`test_orphan_building_idea_is_flagged`, `test_building_idea_*`, `test_inbox_commit_retires_by_the_entry_s_kind`, the `test_next_up.py` tagged cases) keep passing unchanged. One new test covers the untagged-but-named case in `check`.
9. R9. The docs say what the code does. `guide/process.md` changes in three places: `[building]` is "the tag older versions wrote on an idea a change was building, still read as being built"; Stage 1 says intent sets `idea:` and no longer tags the entry; and the `check` paragraph is kept. `templates/inbox.md`'s note says an open change's `idea:` marks a seed taken, and keeps naming `` `[building]` `` as the older tag, so `test_the_inbox_note_defines_seed_and_its_kinds` holds. `docs/REFERENCE.md` (*`.sdlc/work/` and worktrees*) says a seed is being built when an open change names it, or when it carries the legacy tag, and that `status`, `bugs` and `nits` show which change. `skills/idea/SKILL.md`'s retire rule names the `idea:` line first and the tag as legacy. `sdlc.py drift` reports nothing once `sdlc.py record` has run from this checkout.

## Design

**What marks a seed taken.** An open change's `idea:` and `fixes:` lines do, and nothing else is written. `_open_claims(home)` (sdlc.py, beside `cmd_inbox_commit`) already reads them from every open folder via `change_dirs()`, skipping `shipped` and `dropped`. It stays the one reader. `next_up`, `cmd_groups`, `_inbox_commit` and `retro.py` already call it or the same `ideas_of()`/`fixes` lines. This change adds two callers, `cmd_bugs` and `_nits_report`, and adds no new reader. `is_building()` stays as is, the legacy reader, and every place that checks it keeps doing so alongside the claims. A claim is matched to an entry by `ref_matches()`, as everywhere else, never by title alone and never by prefix.

**Why this removes the conflict.** Today intent edits the seed's heading and inserts a body line on the change's branch. Any base-branch commit that touches nearby lines (filing a new entry after the last one, retiring a neighbour, updating the seed) then conflicts when `base` rebases the branch. With no register edit on the branch until ship, the branch's register is the base branch's register as of branching, and a rebase replays nothing onto it. Ship still deletes the seed on the branch (`_seed_lines()` / `_drop_seed()`, matched by `idea:`, tag-blind already). That deletion still runs on the branch, but later than today's tag edit. A conflict is now possible only if the base branch edits that same entry between ship and close, and `inbox-commit` already refuses to *retire* a claimed entry there.

**`next_up` (R3).** It already computes `named` from `open_changes` and leaves those entries out. It also builds a title → folder map from `_open_claims(home)`. Pairing the claims with folder names is cheaper than threading names through `open_changes`, and it is the same reader `groups` uses. It returns `building` as a list in register order. `print_status` prints the count line next to the existing `waiting` line, and `status --all` prints the list. The status skill's line 131 flag (orphan `[building]` idea) is unchanged. Its *Next up* paragraph gains half a sentence: being-built seeds are counted, and listed under `--all`.

**`bugs` / `nits` (R4).** Each command reads `_open_claims(main_root(root))` once and sets `entry["building"]` to the first change whose ref `ref_matches` the entry. It is set in `cmd_bugs` and `_nits_report`, not in `bug_entries()` / `nit_entries()`, which `retro`, `check` and `status` share and which should stay free of a folder walk.

**`groups` (R5).** No logic change: `holders` from `_open_claims` already refuses with the change's name. The `entry["status"] == "building"` branch stays for legacy tags.

**Drop (R7).** Nothing to do, and the code shows why. `cmd_drop()` stamps and commits only the change's folder and `STATE_FILES`. `skills/drop/SKILL.md` never mentions the register, and `_drop_record()` lands a `Drop` merge that keeps the base branch's tree. So today the `[building]` tag dies with the dropped branch and never reaches the base branch. After this change there is no tag at all. `stage: dropped` takes the change out of `_open_claims()`, and every reader sees the seed open again.

**Board.** `scripts/board.py` doesn't read the register (it matches no `inbox`, `register` or `idea` reference). Its cards are changes, which already carry their number. Nothing changes there, and the intent's "the board" bullet needs no work.

**Edge cases.**
- A seed named by two open changes: `groups` already refuses the second change at intent. If it happens anyway (hand edits), `building`/`bugs`/`nits` report the first claim in `change_dirs()` order, and `inbox-commit`'s refusal names the first, as now.
- An `idea:` naming a seed by quoted title (older intents): `ref_matches` handles it, as in `check`'s `linked`.
- A legacy `[building]` entry that an open change also names: it counts as being built once, with that change's name.
- A `fixes:` naming a nit: it is claimed like a bug, and `nits` shows the change.

**Boundaries.**
- *Always:* read "taken" from `_open_claims()` and the legacy tag. Ship deletes by `idea:`. Every reader added is read-only.
- *Ask first:* any write to the register from a change's branch other than ship's deletion. Any new refusal in `inbox-commit` (see the open question on updates).
- *Never:* write or strip `[building]` anywhere, on either branch. Migrate existing tagged entries on a host's base branch. Change `stage:`, `cmd_drop` or the board. Add a register write to `status`, `bugs`, `nits` or `groups`.

## Contracts touched

- **The register is committed on its own only by `inbox-commit`, on the base branch, so an entry never rides on a change's branch** (AGENTS.md, *The register*). Intent's tag edit was exactly such a ride. Removing it moves the design closer to this invariant. Ship's deletion of the seed is the one register edit left on a branch, and it is unchanged.
- **A file the plugin writes changes meaning: always Tier 2.** `[building]` goes from "written by intent" to "written by nothing, read for good". It is not a shim: per AGENTS.md (*Releasing*), a path kept to read what history holds gets no `.sdlc/deprecations.toml` entry and no `RETIRED_KEYS` line. It is not `breaking` under *Setup*, since the plugin reads nothing new and misreads nothing old.
- **`defaults/`, `guide/`, `templates/`** (`test_defaults.py`; `[review] irreversible = templates/`). The `templates/inbox.md` note keeps the doc shape and keeps naming `[building]`. A host's existing register keeps the old note text: it becomes stale prose, not a misread. The `guide/process.md` edit is the guide's own wording, not mirrored into `.sdlc/SDLC.md` (memory: guide edits stay in guide). The change runs `scripts/sdlc.py record` from its own checkout so `drift` is clean.
- **Skills** (`test_skills.py`). Intent still uses `Edit` for `intent.md`, so no `allowed-tools` rule goes unused. `batch.md` stays a side file with no gate or commit. No new bash.
- **Read-only commands.** `status`, `bugs`, `nits` and `groups` stay in `READ_ONLY` and write nothing. The new `building` keys are additions to their JSON, not redefinitions.
- **Metrics / release never read the register** (`test_release_publish_and_measuring_never_read_the_register`): untouched.
- **The base branch is never named `main` in a git call.** R2's test uses `trunk`/`cmd_base`. **Windows:** R2 uses only git and the script in-process, so it is marked `portable`. Any new `write_text` passes `newline="\n"`.
- **Context docs** (`docs.context`): `docs/REFERENCE.md` is edited (R9). README.md, AGENTS.md and CONTRIBUTING.md don't describe the tag (AGENTS.md says "every entry is a seed, and its tag is its kind", which stays true).

## Alternatives rejected

- **Keep the tag, but write it on the base branch through `inbox-commit` when intent opens the change.** That would make the base branch's register show the tag, but it adds a commit to the base branch for every change opened. It is also the very kind of base-branch register commit that conflicts with a branch that later deletes the entry at ship, and a dropped change would then need a second commit to untag. The claim already exists in the change's frontmatter.
- **Keep the branch-side tag and teach `resolve` to auto-merge register conflicts.** That treats the symptom: every run still stops at `base`, and a resolver for prose entries is new code that can lose an edit, against O2.
- **Strip legacy `[building]` tags from a host's register in a migration.** That rewrites a host's committed file for no reader's benefit. History's tags read correctly as they are.
- **Mark taken entries inside `bug_entries()` / `nit_entries()`.** These are shared by `retro`, `check` and `status`, and adding a folder walk there costs every caller. Doing it in the two commands that print is enough.
- **Show being-built seeds as full lines in plain `status`.** Each one is already an open change listed at the top of `status`, so a count suffices there and `--all` gives the list.

## Verification

```bash
uv run --group dev pytest -q tests/test_next_up.py tests/test_bugs.py tests/test_groups.py tests/test_sdlc.py tests/test_skills.py tests/test_defaults.py
uv run --quiet --script scripts/sdlc.py drift     # prints nothing to propose for this repo
uv run --quiet --script scripts/sdlc.py status    # ■ Next up ends with "N being built" while 100 is open, and 2026-11-17-41 is not a candidate
uv run --quiet --script scripts/sdlc.py status --all   # lists "2026-11-17-41 <title> — 100-seeds-marked-by-changes"
uv run --quiet --script scripts/sdlc.py bugs      # every bug carries "building": null or a folder name
uv run --group dev pytest -q -m portable          # R2's rebase test runs here too
./check.sh                                        # ruff, format, pytest -n auto, plugin validate --strict: all green
```

Healthy output: every named test passes, including the R2 control that asserts the old tag edit *does* conflict; `drift` is empty; `check --strict` reports no orphan idea for 2026-11-17-41 even though it carries no tag.
