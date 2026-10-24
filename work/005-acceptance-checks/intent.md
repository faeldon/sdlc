---
id: 005
slug: acceptance-checks
tier: 2
impact: minor
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea: Acceptance checks kept in the change folder, run by ship
depends_on: [004]
serves: none
---

# 005 — Rerun a change's acceptance checks at ship

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Stage 4 says an acceptance check, one that only a deliberate revert could fail, is run once and
recorded in the change's `notes.md` as what ran and what it showed. Work continues after that:
review fixes, a rebase onto a `main` that moved, a factory round. By `/sdlc:ship`, nothing proves
the recorded outcome still holds. The record is pasted output, true at one moment, and ship never
looks at it again.

In 001 the only Important finding led to an edit of the very lines the recorded grep checked. The
check still held, but that was confirmed by reading the phrases, not by rerunning anything. In 003
the acceptance check ran in a scratch repo built by a script in the session's scratchpad, which
went nowhere and can't be rerun. The suite can't hold these checks either: that's what 001's
triage rule moved them out of, because every later run would pay for a check nothing can break by
accident.

## Outcome

- A change can keep its acceptance checks as files in its own folder, `work/NNN-slug/`, where they
  reach history with the folder and leave `main` with it at close, as `notes.md` does.
- `/sdlc:ship` reruns them against the diff it is about to commit, after the gate, and reports each
  one by name with its result. A failing one stops the ship the way a failing gate does.
- A change with no acceptance checks ships exactly as today.
- Stage 4 and the review say to keep the check in the folder rather than prose in `notes.md`. The
  review's "test only a revert can fail" finding points there too.
- This repo's own changes use it, and `./check.sh` passes.

## Affected

- **Area:** the change folder's layout, `/sdlc:ship`, `scripts/sdlc.py`, and the process and
  review docs.
- **Files & components:**
  - `scripts/sdlc.py`: a way to find and run a change's checks, and what `check` audits in a
    folder;
  - `skills/ship/SKILL.md`: a step, and its `allowed-tools`;
  - `defaults/SDLC.md` and `.sdlc/SDLC.md`, Stage 4;
  - `defaults/REVIEW.md` and `.sdlc/REVIEW.md`, Pass 1;
  - `plugins/factory/agents/reviewer-test.md`, which asks for a check "recorded in `notes.md`";
  - `docs/REFERENCE.md` (`work/` layout);
  - tests.
- **Downstream:**
  - every host's ship, through a new step;
  - the factory's builder and test reviewer, which write and judge checks;
  - `/sdlc:close`, which archives the folder as it stands;
  - `/sdlc:setup`'s drift, because a default changes.
- **Contracts:**
  - **Narrow `allowed-tools`:** ship can't list a rule for commands it doesn't know. Running a
    change's own checks means `sdlc.py` runs them, and that is code execution from a file an agent
    may have written.
  - **The gate is offline and deterministic.**
  - **The `work/` layout,** as `change_dirs()` and `TIER_ARTIFACTS` know it.
  - **The defaults track this repo's copies.**
  - **A skill's WAIT and `allowed-tools` are always Tier 2.**
  - **Depends on 004,** which adds ship's base step: the checks should run on the up-to-date
    branch.

## Constraints

- **Language-agnostic:** a host may have no pytest, so a check can't assume a test runner.
- **No silent execution:** whatever runs a change's checks shows what will run before it runs, or
  runs only what the person has already seen in the diff ship reviews. Ship's single approval isn't
  widened to cover new commands quietly.
- **Never in the suite:** the checks stay out of `tests/` and out of `commands.check`; a later
  change's ship doesn't rerun an earlier change's checks.
- **Offline, like the gate.**
- **Optional:** a change with no checks is unaffected, and a Tier 0 change has no folder at all.
- **Nothing local** in examples or fixtures.

## Open questions

- ~~What is a check on disk?~~ Resolved: a `## <name>` section in the change's `checks.md`
  holding one `sh` block; it passes when the block exits 0.
- ~~Where does a check run from?~~ Resolved: the change's checkout root, like the gate; a check
  that needs a fixture repo makes its own temporary directory, and one that leaves the tree
  changed fails.
- ~~How does `/sdlc:ship` run them, and how does the person see what will run?~~ Resolved:
  `sdlc.py checks` lists them (allowed, read-only), ship shows each command, then `sdlc.py accept`
  runs them with no allow rule, so the harness asks once with the list in view.
- ~~Does a failing check block the commit?~~ Resolved: yes, like a failing gate; the fix is to the
  code or to the check, both in the diff.
- ~~Does anything flag a prose record with no check file?~~ Resolved: no; prose can't be told
  from a check reliably.
- ~~How does the factory use them?~~ Resolved: the builder writes them; the test reviewer asks
  for them and runs each one itself, since the factory has no `sdlc.py`; ship enforces.
- ~~Is the prose record retired?~~ Resolved: kept in `notes.md` for a check that can't run, such
  as looking at a rendered page.
