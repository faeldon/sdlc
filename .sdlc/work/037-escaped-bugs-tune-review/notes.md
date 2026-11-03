# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build differs from the plan

- **The new retro tests sit in `tests/test_bugs.py`,** beside the escape tests already there and
  their `_bug`/`_close` fixtures, not in `test_retro.py`.
- **A fixed bug's `title` is null in `escaped`:** `Sdlc-Fixes` never carried it, and its entry is
  gone. Adding a title to the trailer was left out: titles hold spaces, the trailer is `key=value`
  words.
- **`guide/process.md`'s bugs paragraph** gained a clause on the review and the rate, beyond the
  plan's list; `record` was run after it.
- **The retro skill names `review.sensitive` and `review.irreversible`** (the loosening rule reads
  them from `config`), so `READS_CONFIG` lists them for retro.
- **On this repo's history:** no escapes, `rate` 0 over 10 changes against 0 over 20 (`flat`),
  `important` holds 035's F1, and 8 changes in the window predate `findings.md`.
