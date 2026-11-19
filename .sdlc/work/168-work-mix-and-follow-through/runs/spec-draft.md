---
id: 168
slug: work-mix-and-follow-through
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 168 — The retrospective reports work mix, follow-through and time to users · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

What this spec takes as given, each checked in the code:

- `retro()` and `retro_report()` in `scripts/retro.py` both start from `sdlc.closed_changes()` over the window since `sdlc.last_retrospective()`. Each record carries `impact`, `ideas`, `reworks`, `close_at`, and `metrics`, which holds the `Close` commit's trailers. It does not carry the intent's `fixes:` line: `_change_record()` never reads it.
- `retro.py` already reads the register as it stood at a change's base (`_none_themes()`). It reads the main checkout's register too (`rankable_entries()`). Measuring (`closing.measure_change`), release and publish never read it, and `tests/test_nits.py::test_release_publish_and_measuring_never_read_the_register` holds them to that.
- A seed leaves the register in one of three ways. The `Close` commit can retire what the change's `idea:` and `fixes:` name, plus the nits its held `Retire` lines name (`closing.register_plan()`). `sdlc.py inbox-commit` can retire it with a reason: the commit's subject holds `Retire <id>, …`, and the reason goes on a `Reason <id>:` body line, or an `Sdlc-Retired:` trailer for a bug (`_inbox_commit()`). Or someone edits the register by hand. `retro-commit` refuses to remove an entry.
- The proposals a retrospective writes are recorded in two places. Its seeds are appended to the register in the `Retrospective YYYY-MM-DD` commit. Its milestones are in the direction doc of that commit. The intent titles it proposes are recorded nowhere: Step 7 of `skills/retro/SKILL.md` only reports them in the conversation.
- `templates/retro.md` is `[review] irreversible`. Its `{{window}}` value is filled by `render_report()`, the same way 162 appended lead time to `{{cycle}}`.

**R1. Each closed change gets one work class.** The class is the first rule below that applies, and each record in `retro`'s `changes` carries it as `work: {class, by, also}`:
1. `fix`: the intent's `fixes:` names a bug, its `reworks:` names a change, or a seed its `idea:` names was a `[bug]` in the register at the change's base.
2. `capability`: `impact:` is `major` or `minor`.
3. `process`: every path the change touched, besides its own change folder and the register, is under `.sdlc/` or is the configured process, review or policy doc. At least one such path is required.
4. `debt`: a seed it names was a `[nit]`, or has a `Theme:` among the guide's nit themes (`docs`, `refactor`, `robustness`, `tests`, `style`), or `impact:` is `patch` or `none`.

`by` names the signal that decided the class. `also` lists the other classes whose rules applied too.

`test_work_mix_classes_each_change_by_its_first_signal` builds a fixture with one change per rule, plus one with both `fixes:` and `impact: minor`. It fails if any class is wrong, or if the mixed change's `also` doesn't hold `capability`.

**R2. Work mix is counted, and a change no rule classes is left out.** `retro`'s JSON gains `work_mix: {n, unmeasured, classes, shares, mixed}`. `n` counts the classed changes, and `shares` gives each class against `n`, rounded to two places. `unmeasured` counts the changes no rule classes: an unreadable `impact:` with no other signal. These are in no share, and `shares` is null when `n` is 0. `mixed` counts the changes with a non-empty `also`.

`test_work_mix_counts_an_unreadable_impact_as_unmeasured_never_a_class` fails if such a change shows up in `classes` or `shares`.

**R3. The process rule compares normalised paths.** Each `--numstat` path is unquoted first (`indicators._unquote`). Each configured doc path is compared as `as_posix()`. A change that touched only its own folder is not process work.

`test_a_change_touching_only_the_process_is_process_work` covers both paths. One change edits only `.sdlc/SDLC.md`, and one edits a process doc whose name has a non-ASCII character. A third change touches only its own folder. The test fails if either of the first two isn't `process`, or if the third is.

**R4. Closed change records carry `fixes`.** `sdlc._change_record()` reads the intent's `fixes:` line as text (`frontmatter_list`), the same way `reworks:` is read. A missing line gives `[]`.

`test_a_closed_change_carries_its_fixes_line` fails without it.

**R5. Time to users is the median time from landing to release.** `retro`'s JSON gains `time_to_users: {n, median_days, unmeasured, why, releases}`. For each change in the window, the time runs from its `Close` commit (`close_at`) to the creation time of the first release tag that holds it (`_release_of()`), in days to one decimal place. A tag created before the `Close` commit counts as 0. `releases` is the number of release tags in the window (`sdlc._release_tags()`).

`test_time_to_users_is_the_median_from_close_to_the_first_release` uses a history with two releases and three changes released at known gaps. It fails if `median_days`, `n` or `releases` is off.

**R6. A change not yet released is counted apart and never read as zero.** It is in `unmeasured`, with `why: {"unreleased": k}`. A change whose tag time can't be read is counted under `why`'s `"no date"`. With nothing released, `median_days` is null.

`test_an_unreleased_change_is_counted_apart_from_time_to_users` fails if an unreleased change moves the median or is missing from `why`.

**R7. Follow-through scores the seeds the last retrospective added.** The seeds are the entry ids in the register at the last `Retrospective` commit that weren't there at its first parent. Both registers are read at `work_rel()` through `git show`. Each seed gets the first verdict that holds:
- `done`: a change closed in the window names it on `idea:` or `fixes:` (`ref_matches()`).
- `dropped`: a commit in the window has `Retire` in its subject and names the seed's id there.
- `carried`: it is still in the main checkout's register.
- `vanished`: none of the above.

`test_follow_through_scores_the_last_retrospective_s_seeds` uses a retrospective that added four seeds: one built by a later change, one retired with `inbox-commit`, one still open, and one deleted by hand. It fails unless the verdicts are `done`, `dropped`, `carried` and `vanished`, and unless seeds that were already in the register before that commit are left out.

**R8. Follow-through scores the milestones open at the last retrospective.** The milestones come from the direction doc in that commit, open there. Each gets the first verdict that holds:
- struck in the current doc: `Done` gives `done`; `Dropped` or `Revised` gives `dropped`.
- missing from the current doc: `vanished`.
- every row `_milestone_verdicts()` gives for it is `closed` or `shipped`, and there is at least one row: `done`.
- it holds an `unknown` change row: unmeasured.
- otherwise: `carried`.

`test_follow_through_scores_the_milestones_open_at_the_last_retrospective` fails if one is wrong.

**R9. Follow-through is reported as a share, with what it couldn't measure.** `retro`'s JSON gains `follow_through: {since, n, share, unmeasured, missing, seeds, milestones}`. `seeds` and `milestones` each hold `n`, the four verdict counts and `rows`, each row with its `id` and `verdict`, plus `change` where one decided it. `share` is (done + dropped) / `n`, where `n` covers seeds and milestones together. `unmeasured` counts the milestones R8 couldn't score. `missing` names each source that couldn't be read, and always holds the proposed intent titles, which nothing records. With no earlier retrospective, `since` is null, `n` is 0, `share`, `seeds` and `milestones` are null, and `missing` says why.

`test_without_an_earlier_retrospective_follow_through_is_unmeasured_not_zero` fails if any of that reads 0 instead of null.

**R10. The report shows the three figures under `## Window`.** They follow the window paragraph in `{{window}}`'s value, one sentence each, and each gives its `n` and what it left out. The template is not edited. `retro_report()` computes the figures with the same function `retro()` uses.

`test_the_report_shows_the_value_figures_in_its_window` fails if any sentence is missing. `test_retro_and_its_report_show_the_same_figures` is extended and fails if the report and the JSON disagree. It still fails if the report runs a host command.

**R11. `bg` counts any lone `&`.** This answers nit 2026-11-18-64. In `metrics._shell()`, a lone `&` anywhere outside quotes and heredoc bodies is a background command. `&&`, `>&`, `<&`, `&>`, `|&` and `\&` are not.

`test_a_command_ending_in_a_lone_ampersand_goes_to_the_background` gains these cases, and fails on any of them:
- `"a &\nb"` → True
- `"sleep 5 & echo hi"` → True
- `"make &> log"` → False
- `"cat <&3"` → False
- `"a |& b"` → False
- `"echo 'a & b'"` → False

**R12. `uvx` and `npx` resolve to the program and the words after it.** This answers nit 2026-11-18-65. In `metrics._program()`, the program is the first word after `uvx`/`npx` that doesn't start with `-`, and the segment runs from that word on.

`test_a_test_run_is_known_by_its_program` gains `npx --yes pnpm test` → True and `uvx --quiet tox` → True. The first fails today, because `[…][:1] + words[2:]` gives `pnpm pnpm test`.

**R13. `HAND_GATE_RE` accepts a quoted path.** This answers nit 2026-11-18-97. `HAND_GATE_RE` takes an optional quote after `.py`, the same way `FACTORY_CHECK_RE` does.

`test_a_test_run_is_known_by_its_program` gains `uv run --quiet --script '/a b/scripts/sdlc.py' gate 012` → True. `test_a_hand_gate_is_counted_as_a_check` gains the same quoted form. Both fail today.

**R14. The docs say what the figures are.** `docs/REFERENCE.md` *Retrospectives* names the three keys, their rules and what each leaves out. Step 0 of `skills/retro/SKILL.md` gains one bullet naming them. `scripts/metrics.py`'s docstring says what `bg=` counts. `docs/RETRO-SCORECARD.md` marks work mix, time to users and follow-through as captured, with S2, S13 and S12. A review checks these; no test does.

## Design

**One function for the Value band.** `value_band(home, cfg, since, changes, bases, paths)` goes in `scripts/retro.py` and returns `{work_mix, time_to_users, follow_through}`. `retro()` spreads it into its output. `retro_report()` passes it to `render_report()` through a new `value: dict | None = None` parameter. Since one function feeds both, the JSON and the report can't drift apart. `retro()` keeps each change's paths from the rows `_change_rows()` already returns, as `paths: {name: [path]}`, so no diff runs twice. `retro_report()` keeps them from its existing `_change_rows()` call instead of only `[0]`.

**Work mix: `_work_mix(home, cfg, changes, bases, paths)`.**
- The registers at each base are read once and cached. That cache is factored out of `_none_themes()` into `_register_at(home, base, cache)`, which both functions use.
- The rules are a fixed tuple in precedence order (`WORK_CLASSES`). Each rule is a small predicate over the record, its seeds' entries and its paths.
- `DEBT_THEMES` is the guide's nit-theme list, `guide/process.md` *Nits*. Those are the plugin's own words for small technical debt, so no host config is needed.
- The process rule takes `sdlc.HOST_DIR + "/"` as one prefix. It also takes `cfg["docs"]` `process`, `review` and `policy` where set and repo-relative.
- It leaves out paths that start with `sdlc.CHANGE_FOLDERS`, the register (`work_rel()/INBOX`) and `sdlc.MANIFEST`, the same exclusion `_rework()` makes.
- When a change has no base, its paths come from its last commit alone, as its size does. The process rule then reads those.
- The class goes onto each record as `work`. It's a label like `tier`, not a measured number, so `_lean()` keeps it.

**Time to users: `_time_to_users(home, cfg, since, changes)`.**
- One `git for-each-ref refs/tags/<pattern> --format=%(refname:short)%00%(creatordate:iso-strict)` call maps each tag to its time.
- Each change's release is `rec["release"]` when `retro()` has already set it. Otherwise it comes from `_release_of()`.
- The gap is `tag time - datetime.fromisoformat(close_at)`, as a `timedelta` in days.
- It reads no register, and none of release's or publish's code changes.

**Follow-through: `_follow_through(home, cfg, since, changes, trunk)`.**
- Seeds: `git show <since>:<work_rel>/inbox.md` and `<since>^:…` go through `sdlc.parse_entries()`, and the new seeds are the ids in the first that aren't in the second.
- Retired ids come from one `git log --first-parent --format=%s <since>..<trunk>`. Each subject is split on `"; "`, and only a part starting with `Retire ` is read, as ids separated by commas.
- Milestones: `git show <since>:<docs.direction>` goes through `sdlc.direction_items()`. The open milestones in it are passed to `sdlc._milestone_verdicts()` with the window's history. The current doc's items come from `sdlc._direction_text()`.
- A register or direction doc that `git show` can't read at the retrospective goes into `missing`, and its kind is null, never zero.

**The report.** `render_report()` appends three sentences to `values["window"]`:
- `Work mix: capability 4 (40%), fix 3 (30%), debt 2 (20%), process 1 (10%), of 10 classed changes; 1 not classed.`
- `Time to users: a median 2.3 days from landing to release, over 8 changes; 2 not yet released. 3 releases in the window.`
- `Follow-through on the retrospective of 2026-11-18: 5 of 8 done or dropped (62%), seeds 3 of 5 and milestones 2 of 3; intent titles aren't recorded.`

Each one names what it left out, the same way the window sentence names `unmeasured`. With `value` None, as from an old caller, nothing is appended.

**The nits.**
- R11: the `bg` regex becomes `(?<![&>|<\\])&(?![&>])`, searched over `bare`. Quoted text and heredoc bodies are already neutralised there.
- R12: `_program()` finds the index of the first word that isn't a flag and slices from it.
- R13: `HAND_GATE_RE` becomes `scripts/sdlc\.py['"]?\s+gate(?:\s|$)`. Each regex gets a comment saying it matches the other's quoting.

`metrics.py` stays pure.

## Contracts touched

- **Retro is read-only but for its report** (`AGENTS.md`, *Retrospectives*). Every new read goes through `sdlc._git` (`show`, `log`, `for-each-ref`) or reads files. Nothing is written, and `retro_report()` gains no host command (R10's test).
- **Release, publish and measuring never read the register** (`test_release_publish_and_measuring_never_read_the_register`). Only `retro.py` reads the register, and it already did. `cmd_release`, `cmd_publish` and `measure_change` are untouched. Time to users reads tags and `Close` commits only.
- **The metrics trailer format is extended, never redefined** (`scripts/metrics.py`'s docstring). No trailer key is added or renamed. `bg=` keeps its meaning (commands that went to the background, as a lower bound) but now recognises more shapes, so a `Close` commit after this change can count higher than one before it for the same behaviour. The docstring says when that started.
- **`[review] irreversible` templates.** `templates/retro.md` is not edited. The figures come in through `{{window}}`, so a host's overridden template still gets them, and `TEMPLATE_READS` and `breaking` don't change.
- **Modules loaded by path.** The new functions are retro's and live in `retro.py`, calling shared helpers as `sdlc.<name>`. `metrics.py` imports nothing new.
- **`HISTORY_WORK` is named only where history is read, for good.** Follow-through reads the register at `work_rel()` only. A retrospective whose register lived at the old `work/` gets `missing`, not a new reader of `HISTORY_WORK`.
- **Ids by `names_change()` and `ref_matches()`, never by prefix.** Seed verdicts use `ref_matches()` and `same_ref()`. Milestone rows come from `_milestone_verdicts()`, which uses `names_change()`.
- **Frontmatter read as text.** `fixes:` is read with `frontmatter_list()`, never through YAML.
- **The scripts run on Windows.** No new subprocess call, `open()` or `write_text`. Configured doc paths are compared `as_posix()` and git's paths are unquoted, which is the *path compared as text between two sources* failure class in `.sdlc/REVIEW.md` (R3).
- **Nothing about a project.** The fixtures use neutral slugs (`reopen-drafts`, `draft-sync`).

No invariant needs to change.

## Alternatives rejected

- **A new `{{value}}` placeholder in `templates/retro.md`.** That's the irreversible path. It would also make the plugin read a new template key, which counts as `breaking` and needs a `TEMPLATE_READS` entry, before S14 has designed the scorecard page. S14 gets to place the Value band; this change only puts the numbers in.
- **Splitting a mixed change across classes, e.g. half fix and half capability.** Shares would stop adding up to changes, and "n" would stop meaning changes. `also` and `mixed` keep the overlap visible without that.
- **A host config key mapping themes to classes.** It would mean a new key, `READS_CONFIG`, setup's question and a `drift` entry, all for a refinement the intent didn't ask for. The guide's own nit themes and the `.sdlc/`-only path rule are host-neutral already.
- **Close writing the work class as a trailer.** Measuring would have to read the register for seed tags, which the contract forbids. It would also only cover changes closed from now on, while retro can class every change in history.
- **Treating a retired seed as vanished**, as `direction.milestones` does for a grouped seed. A retirement is a reasoned decision, recorded by `inbox-commit`, and the scorecard counts "dropped" as follow-through kept. Vanished is kept for a seed that left with no record.
- **Finding the commit that removed each seed by diffing every commit that touched the register.** It's exact, but costs two `git show` calls per commit. The rules in R7 reach the same verdicts from records history already holds.
- **Including still-unreleased changes in the median, measured up to today.** That mixes waiting time that has ended with waiting time that hasn't. They're counted apart in `why` instead. A figure for the oldest wait wasn't asked for.
- **Reading the old `work/inbox.md` for an early retrospective.** That would add a fourth reader of `HISTORY_WORK`.

## Verification

- `./check.sh` exits 0 and runs ruff check, ruff format --check, `pytest -n auto` and `claude plugin validate --strict`, with nothing failing or skipped beyond today's skips.
- `uv run --group dev pytest -q tests/test_retro.py tests/test_metrics.py tests/test_nits.py tests/test_sdlc.py -n auto` passes, including every test R1–R13 names.
- `uv run --group dev pytest -q -m portable` passes, as CI's Windows job runs it.
- From this repo's main checkout, `uv run --quiet --script scripts/sdlc.py retro | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['work_mix'], d['time_to_users'], d['follow_through'])"` prints three dicts:
  - `work_mix.n + work_mix.unmeasured` equals `len(changes)`.
  - `time_to_users.n` plus the counts in its `why` equals `len(changes)`.
  - `follow_through.since` is the date of the newest `Retrospective` commit, and `missing` names the intent titles.
- `git status --porcelain` is unchanged afterwards.
- `uv run --quiet --script scripts/sdlc.py retro --report` prints `## Window` with the three sentences after the window paragraph. Every other section is as before. Nothing is written.

**Boundaries.**
- **Always:** each figure gives its `n` and its unmeasured count, and missing data is null, never zero. The JSON and the report come from one function.
- **Asks first:** any edit to `templates/` or `defaults/`, a new config key, or a change to what `direction.milestones` reports.
- **Never:** a new trailer, a register read from measuring, release or publish, writing anything from `retro`, or reading `HISTORY_WORK`.

