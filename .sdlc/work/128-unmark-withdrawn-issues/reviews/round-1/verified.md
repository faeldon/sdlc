- KEPT: code: C1: docs/CONTRIBUTING.md:199-201 and :222-225: the tracker section still says `unmark()` is called only by `sync` and that `closed_by()` is read only on its own. A full marking pass now calls `unmark()` through `unmark_withdrawn()` (sdlc.py:7920) and reads `closed_by()` over the unpushed commits, so the doc is stale because of this change. The file isn't in the diff, so it hasn't been updated.
- KEPT: code: C2: docs/REFERENCE.md:430: the new sentence says `intake` lists an issue "the marking didn't label". `dangling()` (github.py:303) only filters open `triaged` issues against `recorded`, and never checks who labelled them. An issue whose `unmark()` failed stays labelled and so stays dangling, which the sentence denies.

## Notes
I read the diff, `unmark_withdrawn`, `dangling()`, and the CONTRIBUTING and REFERENCE passages. I ran no tests.

C1 is listed under `untouched`, but the code it names is this change's own new call path. The problem is how the change uses the tracker, not old code, so I kept it.
