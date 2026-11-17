DECISION: ESCALATE

**Why.** The build covers the intent's outcomes and tests them. A full pass unmarks an issue whose record is gone. It leaves alone an issue that an unpushed commit closes, and an issue a person labelled stays `dangling`. Round 2 passed and the gate passed (2338 tests). Two things still need the person. First, D1 is unticked, so the build relies on a default nobody has confirmed. Second, the change acts on hosts' published GitHub issues: it posts a new comment and removes the `triaged` label and parent, and nothing asked before.

**Open items**
- None open. The code reviewer's round-1 CHANGEs (F1 CONTRIBUTING.md, F2 REFERENCE.md) were fixed in round 2, and the second-round code review passed.
- Minor, written down only (code reviewer, F3): `scripts/sdlc.py:7853`. The new path runs for a tracker that has `unmark` but no `open_marks`, so a host with no records could now see an `open_numbers()` failure in close's `intake` report. Gate it on `hasattr(found, "open_marks")` as well.
- Minor (code reviewer, F4): every close now lists every open issue with its comments (`open_marks()`, limit 1000), even when no issue is labelled `triaged`. With no tracking ref it also reads the whole base-branch history.
- Minor (code reviewer, F5/F7/F8): wording and line wrapping in REFERENCE.md's marking paragraph.

**Decisions to confirm**
- D1: with no remote-tracking ref for the base branch, every commit on the base branch counts as unpushed. An issue that any commit there closes is then never unmarked. The other option was to unmark nothing at all. The code reviewer agreed with this default.

**For the person at ship**
- Look first at `unmark_withdrawn()` and `unpushed_closes()` in `scripts/sdlc.py` (around 7853 and 7920–7960).
  - Check the four conditions that must all hold before an issue is unmarked: still labelled `triaged`, core's newest comment on it is a mark, no record anywhere, no unpushed closer.
  - Check that a git failure means nothing is unmarked and is reported under `failed`.
- Then decide whether F3's early return should be gated on `open_marks`. As it stands, a host that has never used records could see a new failure line at close.
- Then look at the two new tests in `tests/test_archive.py`.

- IMPACT: patch — hosts get no new command or option. An issue whose register entry was withdrawn now leaves triage (with one comment) instead of showing as `dangling` forever.

- UNDONE: `skills/triage/SKILL.md`'s `dangling` bullet offers every dangling issue for triage again, one an unpushed commit closes included: it could say that one waits on the push. → seed: Triage's dangling bullet says an issue an unpushed commit closes waits on the push
