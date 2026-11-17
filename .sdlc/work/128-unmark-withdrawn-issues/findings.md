# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.

## F1. [important] [context] docs/CONTRIBUTING.md:199-201 and :222-225: the tracker section says `unmark()` is called only by `sync`, and that `closed_by()` is read only on its own, by `_unpushed()`.

docs/CONTRIBUTING.md:199-201 and :222-225: the tracker section says `unmark()` is called only by `sync`, and that `closed_by()` is read only on its own, by `_unpushed()`. Now a full marking pass (close and `mark-triaged`) also calls `unmark()` through `unmark_withdrawn()` (sdlc.py:7920), and reads `closed_by()` over the unpushed commits to decide it. Say so: the full pass sends back an issue whose record went, with a comment, unless an unpushed commit closes it, and it reads `closed_by()` for that. Also name `unmark_withdrawn()` beside `withdraw_issues()`, and drop "`sync`'s" from the `mark-triaged` and `sync` list.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: fixed
By: code

## F2. [important] [context] docs/REFERENCE.md, the `intake` sentence (about line 430): "an issue labelled `triaged` that nothing records anymore and the marking didn't label".

docs/REFERENCE.md, the `intake` sentence (about line 430): "an issue labelled `triaged` that nothing records anymore and the marking didn't label". `cmd_intake` and `github.py`'s `dangling()` (line 303) don't check who labelled an issue. They list every open `triaged` issue no record holds. An issue whose `unmark()` failed stays labelled and so stays dangling, which the sentence denies. Replace the clause with: "an issue labelled `triaged` that nothing records anymore, which includes one whose send-back failed, or that waits on that push."

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: fixed
By: code

## F3. [nit] [correctness] the early return now runs for any full pass on a tracker with `unmark`, even with no records.

scripts/sdlc.py:7853: the early return now runs for any full pass on a tracker with `unmark`, even with no records. For a tracker with `unmark` but no `open_marks`, that calls `open_numbers()`, and its failure is listed in close's `intake` report. Gate the new path on `hasattr(found, "open_marks")` too, so a host with no records sees nothing new.

Evidence: scripts/sdlc.py:7853
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F4. [nit] [cost] every close now lists every open issue with its comments (`open_marks()`, limit 1000), even when no issue is labelled `triaged`.

scripts/sdlc.py:7920-7960: every close now lists every open issue with its comments (`open_marks()`, limit 1000), even when no issue is labelled `triaged`. A `found.dangling(set(records))` call (one label-filtered listing) could be the gate before that listing. The no-tracking-ref case also reads the base branch's whole history in `unpushed_closes()`. D1 chose that deliberately, so I accept it; it's worth a sentence in the docstring about cost.

Evidence: scripts/sdlc.py:7920-7960
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F5. [nit] [correctness] the `sdlc.py sync` line in the same paragraph runs past the file's usual wrap width.

docs/REFERENCE.md: the `sdlc.py sync` line in the same paragraph runs past the file's usual wrap width. Rewrap the paragraph.

Evidence: docs/REFERENCE.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F6. [nit] [correctness] `skills/triage/SKILL.md:55` ("Offer each to be triaged again, as if new") now also offers a dangling issue an unpushed commit closes.

`skills/triage/SKILL.md:55` ("Offer each to be triaged again, as if new") now also offers a dangling issue an unpushed commit closes. This is the builder's own note in `notes.md`; agreed, and it isn't a context doc, so no CHANGE. A one-line "waits on the push" would do.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F7. [nit] [correctness] docs/REFERENCE.md (the marking paragraph): "(every commit on it, with no remote-tracking ref)" is hard to parse.

docs/REFERENCE.md (the marking paragraph): "(every commit on it, with no remote-tracking ref)" is hard to parse. Say "(with no remote-tracking ref, every commit on it counts)".

Evidence: reviews/round-2/code.md
Class: code review, round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F8. [nit] [correctness] docs/REFERENCE.md (the `sync` sentence at the end of that paragraph): the line runs about 150 columns and splits the `sdlc.py` / `sync` code span across the break.

docs/REFERENCE.md (the `sync` sentence at the end of that paragraph): the line runs about 150 columns and splits the `sdlc.py` / `sync` code span across the break. It renders correctly; this is wrapping only.

Evidence: reviews/round-2/code.md
Class: code review, round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F9. [nit] [correctness] a host with no records and a tracker with `unmark` now lists every open issue with its comments (`open_marks()`, limit 1000) on each close and `mark-triaged`, where it used to return at once.

scripts/sdlc.py:7853: a host with no records and a tracker with `unmark` now lists every open issue with its comments (`open_marks()`, limit 1000) on each close and `mark-triaged`, where it used to return at once. The listing is needed when a record went and left no records behind, so the cost is intended. A cheaper gate would be `found.dangling(set(records))` first, which lists only open `triaged` issues, and list in full only when that is non-empty. Round 1 raised this and it is still open.

Evidence: scripts/sdlc.py:7853
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F10. [nit] [correctness] the early return also doesn't check `hasattr(found, "open_marks")`.

scripts/sdlc.py:7853: the early return also doesn't check `hasattr(found, "open_marks")`. A tracker with `unmark` but no `open_marks` lists `open_numbers()` for nothing, and a failure there lands in close's report. This is round 1's F3, still open.

Evidence: scripts/sdlc.py:7853
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F11. [nit] [correctness] scripts/sdlc.py, `unmark_withdrawn()` around the `closing is None` branch: the two failure paths (git unreadable, and an exception from `unpushed_closes()`) have no test.

scripts/sdlc.py, `unmark_withdrawn()` around the `closing is None` branch: the two failure paths (git unreadable, and an exception from `unpushed_closes()`) have no test. The "nothing is unmarked on a guess" constraint depends on them. A test that makes `_git` return None for the log, and asserts the issue keeps its label and the report carries the failure, would pin it.

Evidence: reviews/land-1/code.md
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F12. [nit] [correctness] the `sync` sentence is about 140 columns, so the paragraph's rewrap is not finished, though round 2's build note says it was.

docs/REFERENCE.md:433: the `sync` sentence is about 140 columns, so the paragraph's rewrap is not finished, though round 2's build note says it was. The parenthetical "(every commit on it, with no remote-tracking ref)" is still hard to parse; "with no remote-tracking ref, every commit on it counts" reads better.

Evidence: docs/REFERENCE.md:433
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
