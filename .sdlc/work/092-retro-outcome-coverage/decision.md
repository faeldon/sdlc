DECISION: ESCALATE

**Why.** The build looks finished and clean. The gate passed (`./check.sh`, 1916 tests, validate green), and round 1's code review is `VERDICT: PASS` with only Optional notes. It says every requirement from R1 to R10 has code and a test that fails without it. It still has to come to you because two decisions in `decisions.md` are unticked, and the build relies on both. One of them, D1, goes beyond the spec's R1, and `plan.md` records that. The change also edits `templates/direction.md`, which is an `irreversible` path in this repo, and it changes a published interface: the direction doc's form and `retro`'s JSON.

**Open items**
- None of them blocks anything. The code reviewer left three Optional notes:
  - Re-wrap the over-long `direction` bullet in Step 0 of `skills/retro/SKILL.md`.
  - Amend spec R1 to match D1 if you confirm D1.
  - The `why` asymmetry between a milestone citing an unknown goal and one citing a known goal that has no citations follows D2, so no change is needed.
- There is no `notes.md`, so nothing undone was carried forward.

**Decisions to confirm**
- **D1:** an open goal's citation is also read from its indented continuation lines, not only the first line. That goes beyond R1. A struck goal's wrapped lines are never read, and `title` stays the first line. The reason for the default: without it, this repo's own G6–G8 show up as uncited and the spec's Verification fails. If you confirm it, amend R1 in `spec.md` to match.
- **D2:** there are two `why` cases the spec left open:
  - A milestone that cites only a goal, where that goal cites nothing, gets `none`.
  - Citations that mix a struck outcome with an unknown id get `unknown`, since a typo is the likelier thing to show.

**For the person at ship**
1. Start with `_goal_cites()` and `CITES_RE`/`SERVES_RE` in `doc_items()` in `scripts/sdlc.py`. Check that no new item reaches `problems`, that `Groups:` and `current` handling is unchanged, and that a struck goal's wrapped reason is never read as a citation. This is the D1 code.
2. Then read `_none_themes()` in `scripts/retro.py`. It should read the register only from each change's base, with one `git show` per base, only under the work path, and treat a failed `show` as an empty register.
3. Then `_uncited()` against D2.
4. Then look at `templates/direction.md`. It's irreversible here, so ship needs a `How to recover:` line, and the shape tests must hold.
5. The reviewer ran only the targeted tests. The full `./check.sh` came from the builder and the gate, and both passed.

- IMPACT: minor — hosts can now cite outcomes on goals (`(O1, O3)`) and milestones (`Serves:`), and `retro` reports new `product.uncited` and `product.none_themes` fields. Both are added alongside the old output, and an uncited doc reads as before.
