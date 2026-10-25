# 021 — Rework ignores shared docs and the setup record

## Context

`retro()` pairs two changes as rework when they closed within `REWORK_DAYS` of each other and
share a file. The first retrospective's 12 pairs all came from `defaults/SDLC.md` and
`.sdlc/setup.json`, files nearly every change edits, so the signal said nothing. Measured on this
repo's history, `scripts/sdlc.py` is a hub in the same way: 10 of 14 changes in the current window
touch it, which makes 45 pairs and no follow-up fixes. File-level pairing on a file most changes
touch carries no information, whatever kind of file it is. Decided: a computed exclusion with no
config key and no named files. A file touched by **more than a third** of the window's changes
stops counting, but only once the window holds **at least 6 changes**: below that, the two
changes of any pair are already more than a third, so every shared file still counts, as today.
(Planned as 5; the first test showed a 5-change window could never pair, so the minimum is
derived from the share.)

## Changes

**`scripts/sdlc.py`**
- Next to `REWORK_DAYS` (~line 3658), add two constants with one comment line each, in the
  existing style: `REWORK_COMMON_SHARE = 1 / 3`.
- In `retro()` (~4315–4375), once `touched` is built for both closed and dropped changes (the
  window is `len(changes) + len(dropped)`), count each file across `touched.values()` with
  `Counter`. When `window * REWORK_COMMON_SHARE >= 2`, `common` is every file whose count
  is `> window * REWORK_COMMON_SHARE`; otherwise it's empty. Both pairing loops (closed→closed and
  dropped→closed) intersect `touched[a] & touched[b]` and then subtract `common`. The existing
  `every_change` exclusion stays as it is.
- Return a new key `rework_common`: `[{"file": f, "changes": k}]`, most-touched first, then by
  name. This lets the person see why a pair didn't count, and it doubles as a churn signal for
  the architecture pass.

**`tests/test_retro.py`**, next to `test_sharing_only_the_docs_every_change_updates_is_not_rework`
- New test: six changes over one week (one dropped), five touching `NEWS.md`, two pairs sharing
  code. Expect exactly one pair, on `["src/drafts.py"]`, and
  `rework_common == [{"file": "NEWS.md", "changes": 5}]`.
- New test: five changes all sharing one file still pair on it (under the minimum), and
  `rework_common == []`.
- A dropped change counts toward the window and has the common files subtracted too. Fold this
  into the first test or add a short third one.
- Add `"rework_common"` to the key set in `test_it_reports_every_key_and_writes_nothing`.

**Docs**
- `defaults/SDLC.md` and `.sdlc/SDLC.md`, Rework bullet (identical wording in both, per the
  mirror rule): add one sentence saying retro leaves out the files more than a third of the
  window's changes touch, once there are six, because sharing them says nothing. Then run
  `uv run --quiet --script scripts/sdlc.py record` from the worktree so `.sdlc/setup.json` matches.
- `skills/retro/SKILL.md`: on the `rework` bullet (~line 51), add `rework_common`. In the
  Process pass, say what was left out. In the Architecture pass, a file in `rework_common` is a
  file most changes touch, which is worth naming there.
- `docs/REFERENCE.md` ~line 449: one clause that rework leaves out the files most changes touch.

**`work/021-rework-shared-files/intent.md`**: strike the three open questions with what was
decided (computed, > 1/3 with at least 6; yes, reported as `rework_common`), and update Approach
to match. Save this plan as `work/021-rework-shared-files/plan.md`.

## Verification

- `uv run --group dev pytest tests/test_retro.py -q`, then `./check.sh` (ruff, format, full
  pytest, `claude plugin validate --strict`, the drift gate).
- `uv run --quiet --script scripts/sdlc.py retro`, then read `rework` and `rework_common`. In the
  current window, `rework_common` should list `scripts/sdlc.py`, `.sdlc/setup.json`,
  `defaults/SDLC.md` and `tests/test_skills.py`, and `rework` should hold only pairs on files
  touched by 4 or fewer of the 14 changes.
- Rerun the scratch tally (`scratchpad/freq.py`) to confirm that window 1 (001–006) would have
  left out `defaults/SDLC.md`, `.sdlc/setup.json` and `scripts/sdlc.py`, which settles the
  intent's first Outcome bullet.
