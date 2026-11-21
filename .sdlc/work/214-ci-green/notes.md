# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## What the build found

- The intent expected a missing `encoding="utf-8"` in a script. There was none: the 0x97 came from
  two tests copying `templates/spec.md` with a bare `write_text`, and the script's own UTF-8 read
  was right. The fix went to the tests, and `test_windows.py` now scans portable tests' bodies.
- The Linux failure was no race. It fails on every Linux run: Linux refuses a bind over a TIME_WAIT
  left by a socket without `SO_REUSEADDR`, even from one that sets it, and macOS allows it.
  Reproduced and fixed in a `python:3.12-slim` and a `uv` container.
- The mend and upstream failures were the `claude` and `gh` fixtures, shebang scripts Windows can't
  run. No portable test used either before; both now stand in for the call in-process.
- Windows itself can't be run here: the Windows job on the landing's push is the proof for the
  hand-gate, mend, upstream and encoding fixes.

## Left undone

- [x] Say when CI on the base branch is red, in a landing's look or in `status`, so the local gate → seed: 2026-11-21-36
  isn't the only word (the intent's third open question; a seed of its own).
- [x] 275 `read_text`/`write_text` calls in non-portable tests and helpers name no encoding. They → seed: 2026-11-21-37
  don't run on Windows today; a test moved into `portable` gets caught by the new check, but a
  helper it calls doesn't.
- [x] A hand-gate record written before this change names a build hashed the old way, so a green → dropped: `docs/REFERENCE.md` already says so, and the release's changelog is drawn from the change's impact.
  hand gate reads stale once after the update and wants `sdlc.py gate` rerun. Worth a line in the
  release notes.
