
Resolved:

- **Which workarounds history alone shows, and which need a record?**
  - From history alone:
    - commits on the base branch that no command made (R1);
    - records edited there by hand (R2);
    - restored register entries, since ids are never reused (`next_entry_ids()`) (R3);
    - fixes asked at landing, because `build/land-<n>.ask.md` stays in the change's commit (R6).
  - Need a record: ejections and stops. 174's `runs/ejections.jsonl` now holds them, extended with `train` so a stop counts once a train (R4).
- **Does the review bullet belong in `.sdlc/REVIEW.md` or `guide/review.md`?** In `.sdlc/REVIEW.md` alone. The guide's *context* dimension already covers docs going stale for every repo, and its failure-class slot is for a repo's own history.
- **Do setup's and uninstall's commits count as the loop's?** Yes. They are the plugin's own steps, pinned by subject (`SETUP_SUBJECTS`).
- **Does the committed report show the counts now?** No. The JSON carries them; S14 lays out the report.

Left for the person:

- **Does an ejection the train's loop makes itself, for a gate's fault, count as a workaround?** The spec counts every ejection, split by `cause`.
  - Counting all of them shows every stop the process didn't plan for (O3).
  - Counting only `review` and `refusal` would leave just the ones a person had to weigh (O4).
  - Either is a one-line filter in `_workarounds()`.
- **Should 174 add `train` itself, rather than this change extending its row?** Either way the row is the same. Adding it in 174 avoids a second edit to `_record_ejection()`, but widens 174, which is already specced.
