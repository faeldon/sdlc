---
id: 148
slug: gate-records-redact-tmp
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: [O6]
---

# 148 — The factory's gate records redact the temp directory, as they do the home directory

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`_placeholders()` in `plugins/factory/scripts/factory.py` writes the main checkout's root as
`<path-to-clone>` and the home directory as `<home>` in every record the factory commits, but not
the temp directory. On 2026-11-18 the 140–143 landing train's first red tip failed in a test
using `tmp_path`, and pytest's output, `tmp_path = PosixPath('/private/var/folders/…/T/pytest-of-
<username>/…')`, was recorded in `land-1.gate.md` for 140, 141 and 143. `train --eject` and the
re-stack amended those records into each change's commit. On the re-stacked tip,
`test_nothing_local::test_nothing_in_the_repo_is_forbidden` matched the username in 141's and
143's records, so the tip was red because of the train's own records, not any change's code. The
bisection would have ejected 141 and 143 for it, so the train was stopped and nothing landed. Any
host whose gate prints a temp path leaks the machine's layout into history the same way, and any
host with a check like `test_nothing_local` gets a red gate that never clears.

## Outcome

- `_placeholders()` writes the temp directory (`tempfile.gettempdir()`, as given and resolved, for
  example macOS's `/private/var/folders/…`) as a mark of its own, `<tmp>`, beside
  `<path-to-clone>` and `<home>`.
- A test runs a gate whose command prints a path under the temp directory, and finds neither that
  path nor the user's name in `land-<n>.gate.md`.
- **Moves O6:** a train ejects a change for what the change broke, never for what the train's own
  records quote.

## Affected

- **Area:** the factory's committed records.
- **Files & components:** `plugins/factory/scripts/factory.py` (`_placeholders()`, used for gate
  records and filed replies) and `tests/test_factory.py`.
- **Downstream:** every factory host's committed gate records and filed replies. The records that
  already hold the path, in 140, 141 and 143, aren't cleaned by this fix, because it only redacts
  new output. Those branches still have to be cleaned before they land.
- **Contracts:** AGENTS.md's *Nothing about a project or a workspace* (`tests/test_nothing_local.py`).

## Constraints

- Only marks are rewritten, never a verdict, an exit code or a failing test's name.
- The order of marks stays the most specific first: the clone root, then the home directory and
  the temp directory, whichever path is longer first.
- A path printed under the temp directory still reads as a path, `<tmp>/pytest-of-…`.

## Open questions

- ~~Does `<tmp>` alone go far enough? pytest names its folder `pytest-of-<username>`, so the
  username still appears under `<tmp>`. Should the login name be redacted as a path segment too,
  and how, without rewriting short names that occur in ordinary words?~~ Resolved: the login name
  is written `<user>` only inside a path a mark begins, where no letter or digit borders it;
  prose is never rewritten.
- ~~Should cleaning the existing records in 140, 141 and 143 be part of this change, or done by
  hand on each branch before they land again?~~ Resolved: a one-off after 148 lands, outside this
  change.

## Approach

Add `(Path(tempfile.gettempdir()), TMP_MARK)` to `_placeholders()`'s list, ordered longest first.
Then add a test for a gate command that prints `$TMPDIR/pytest-of-$USER/x`, asserting the record
holds `<tmp>` and neither the path nor the user's name.
