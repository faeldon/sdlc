# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build differs from the spec and plan

- **`slice` leaves out `.sdlc/work/`** even from the least-recently-changed list: the change
  folders and the register are the process's records, not code to review. Found by a test.
- **`factory.py` keeps trailer values as text**, where `metrics.parse_trailers` turns a digits-only
  value into a number (`introduced_by=002` becomes `2`). The pinned test compares them as text on
  real shapes (`NNN-slug`); `names_change()` reads either.
- **`score` writes `<run>.md` beside the run folder** (`.sdlc/reports/eval-<date>-<n>.md`), so the
  next eval finds the last one by name; runs order by date, then their number within the day.
- **`slice` caps the sensitive and the stale lists at `--limit`, never the paths named.**
- **No new agents:** both skills prompt the existing code and security reviewers ("Replay…", "No
  change…"); their `PREEXISTING:` line is what the review turns into proposed bugs.
- **The review's report names the reviewer** that raised each problem in its body, so the person
  picking at `/sdlc:bug` sees whose finding it was.
