DECISION: READY

**Why:** Every requirement in the intent has a named test, and all four round-1 reviewers (code, behaviour, ui, ux) gave `VERDICT: PASS`. The code reviewer's two notes are nits. The build follows the intent's Approach and `plan.md`, and the gate record passed. Nothing in the reviews suggests the spec was wrong.

**Open items:**
- NIT (code reviewer): `docs/REFERENCE.md:249` has a line that runs past the paragraph's wrap.
- NIT (code reviewer): `scripts/sdlc.py` `_park_deadline_at()` runs a `git show` for each build-stage change inside the status loop. It should be read once before the loop, as `_gate_jobs_at()` is.

**Decisions to confirm:**
- SETTLED: D1: The intent's Approach says to refuse `[park] exit` of 0 and 1, and its *Contracts* line names `[park] exit` and accepts the narrowing. The code reviewer confirmed the refusal sits in `_park()` with the other bad `[park]` values, so the person approved this before the build.
- SETTLED: D2: The intent's Outcome allows `park --clear` to remove an unvouched record. The code reviewer found the change limited to records the ledger never vouched for. `verdicts` already treats such a record as a stop to rerun, so no real park is lost.

**For the person at ship:**
- Look first at `plugins/factory/scripts/factory.py`: `_park()`, `busy_of()`'s `clean()` and `cmd_park(clear=True)`.
- Then look at `scripts/factory_records.py`: `capped_park` and `park`, copies pinned to the factory's original by `tests/test_modules.py`.
- Then look at `scripts/sdlc.py`: `_park_deadline_at()`, and the board's read of the park.
- The one published interface touched is the `[park] exit` config key. The person approved narrowing it in `intent.md`, under *Contracts* and *Approach*. It is unreleased, so no host loses a value.

- IMPACT: none — `[park]` is unreleased (222 ships it new), so nobody holding the previous release sees a change.

- UNDONE: `factory_records.read_park()` (and `factory.py`'s) take `RESOURCE:` and `HOLDER:` as written, so a hand-edited `runs/parked.md` with an ESC in it still reaches `status` and the board: `busy_of()` now cleans what the gate writes, but a reader-side strip would cover a forged record too. Out of 229's scope (the busy answer only). → seed: Strip control characters in read_park() on the reader side
