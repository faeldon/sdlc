---
id: 057
slug: robustness-nits
tier: 1
impact: patch
stage: shipped
created: 2026-11-13
updated: 2026-11-13
shipped: 2026-11-13
idea: 2026-10-26-7
depends_on:
serves: [O2]
---

# 057 — Pay down the robustness nits

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Eight `[robustness]` nits are open in `.sdlc/work/inbox.md`. Ships from 019 through 044 approved
them unfixed. The 2026-10-26 retrospective marked their paydown `Priority: high`. When it raised
this seed the theme had five nits, which is the process doc's threshold for one paydown change. It
has eight now.

The seed also named 2026-10-25-18 (a change sized from an intent committed early). That nit is no
longer in the register.

Each one is a place where `status`, `close --check`, `retro`, release or a skill reports something
false, or reports it late:

- **2026-10-25-13:** `next_up` labels a seed "next in series" when none of its `After:` titles is
  in the register. A mistyped title gets that label as well as its `⚠` warning. It should be
  checked against the titles history has shipped.
- **2026-10-25-14:** `_after_loops` follows only the first `After:` title a waiting seed is
  waiting on. Two seeds that wait on each other through a later title are never reported.
- **2026-10-25-17:** a release whose commit or `prepare` fails puts back a file that after-bump
  staged as untracked. `report["untracked"]` was taken at after-bump, so the report never names
  that file and it is left behind unmentioned.
- **2026-10-26-1:** `/sdlc:intent` copies a seed's `Issue:` numbers onto `closes:`, and `sync`
  makes each a sub-issue. The issue's "Taken on by" comment waits for the next `mark-triaged` or
  for close, so its filer hears nothing while the change is built.
- **2026-10-27-4:** `close --check` writes no `refs/sdlc/base/<branch>`, so `_change_base` falls
  back to the intent rule. Its `reaches` preview can then list fewer skills than the close
  reports.
- **2026-11-04-2:** `_review_at` drops `_findings_from_text`'s problems. A `findings.md` from
  history that no longer parses quietly has fewer findings and fewer Important ones, while `state`
  still says `file`. Retro then pairs an escaped bug with a review that looks lighter than it was.
- **2026-11-04-5:** `/sdlc-factory:review` proposes each bug's `Severity:` from the process doc's
  words. When the host's doc has no bugs section, those words come from `sdlc`'s guide, which the
  factory's cached copy can't read.
- **2026-11-08-2:** `last_touched()` counts every dirty path in a checkout. For a change folder in
  the main checkout, any unrelated edit there makes the change read as in flight, and `status`
  then never recommends it.

## Outcome

- Each nit has a test in `tests/` that fails on today's code and passes after the fix. The one
  exception is 2026-11-04-5, whose fix is skill text:
  - A seed whose `After:` names nothing in the register or in history gets its `⚠` warning and no
    "next in series" label.
  - A loop through a seed's second or later `After:` title is listed and warned about.
  - A release that fails after after-bump staged a new file names that file in `untracked`.
  - A seed's `Issue:` numbers carried onto `closes:` get their "Taken on by" comment when intent
    syncs, not at the next marking.
  - `close --check` previews `reaches` from the base branch's tip and matches the close's own
    report.
  - A `findings.md` from history that doesn't parse carries `review.problems` in retro's output
    instead of shrinking the counts.
  - The factory's review leaves `Severity:` for `/sdlc:bug` to ask when the host's process doc has
    no words for it. Ship confirms this by reading the skill text.
  - A dirty file outside a main-checkout change's folder doesn't make it read as touched.
- `/sdlc:ship` retires all eight nits by id, and deletes seed 2026-10-26-7.
- `./check.sh` passes.
- **Moves O2:** what `status`, `close --check`, `retro` and a failed release tell a host is true:
  - no seed reads as ready when its `After:` is broken;
  - no stalled change hides as in flight;
  - no file a failed release left behind goes unnamed;
  - no review reads as lighter than it was.

## Affected

- **Area:** `scripts/sdlc.py`: `next_up` and `_after_loops`, `cmd_release`'s `restore()` and its
  `untracked` report, `sync` and `mark_issues()`, `cmd_close`'s `--check` path into
  `_change_base`, `_review_at`, and `last_touched()`. Two skill files are also affected:
  `skills/intent/SKILL.md` and `plugins/factory/skills/review/SKILL.md`.
- **Files & components:** `scripts/sdlc.py`, the two skills, the tests for status, release, close,
  retro and intake, and `.sdlc/work/inbox.md`.
- **Downstream:**
  - Hosts reading `status`'s `Next up` and touched lines, `close --check`, `/sdlc:retro`'s
    bug-escape pairing, and a failed `/sdlc:release`.
  - The people who filed a GitHub issue that a seed carries.
  - `review.problems` is a new key in retro's output, and nothing reads an old meaning of it.
- **Contracts:**
  - Bad input is reported, never raised.
  - A tracker never reads `.sdlc/work/`, so core still decides each issue's comment through
    `recorded_issues()`.
  - The record is committed before the issue is told.
  - `_release_refusals()` is not loosened.
  - The factory still never imports or calls `sdlc.py`.

## Constraints

- No meaning of an existing config key, frontmatter key, trailer or file changes.
- 2026-10-26-1 must not make intent post to GitHub before its WAIT's yes. Intent's question names
  opening the issue, and the comment would ride on that same yes.
- Windows rules hold for any new subprocess call or write: `encoding="utf-8"` and `newline="\n"`.

## Open questions

- ~~Can 2026-10-26-1 be fixed without changing what intent's WAIT approves? For example, could
  `sync` run `mark_issues()` for `closes:` numbers that are already recorded? If the question's
  wording has to change, this change becomes Tier 2, or that nit is split back out.~~ Resolved:
  yes. `sync` runs `mark_issues()` for the change's own `closes:` numbers. That is the same kind
  of write as the sub-issue link it already makes behind intent's yes, and `mark-triaged` already
  comments on an uncommitted `closes:`. The question is unchanged, so this stays Tier 1.
- ~~For 2026-10-25-13, which shipped titles count? Every `idea:` in history's intents, or only
  those of `Close` commits on `main`'s first-parent line?~~ Resolved: the `Close` commits' ones
  (`closed_changes()`), matched with `same_ref()`, which are the titles the `⚠` warning already
  used, so the label and the warning can't disagree.

## Approach

There is one commit, with one fix and one test per nit, in the order listed. Plan mode reads each
function before it is changed. The 2026-10-26-1 fix is decided first, because it alone could change
the tier.

The nits taken in, each retired by `/sdlc:ship`: 2026-10-25-13, 2026-10-25-14, 2026-10-25-17,
2026-10-26-1, 2026-10-27-4, 2026-11-04-2, 2026-11-04-5 and 2026-11-08-2.
