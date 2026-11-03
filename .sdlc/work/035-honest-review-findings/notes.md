# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build differs from the spec

- **Ship writes `findings.md` complete before its WAIT, and Step 6 writes nothing to it.** The spec's
  Design had Step 6 write the approved dispositions, but the `Sdlc-Findings` line is drafted in
  Step 4, before the WAIT, so the file must already hold every disposition then. Step 3 writes
  each one as ship proposes it (Important `open`, a recorded nit or a pre-existing bug `recorded`,
  one gone since an earlier run `fixed`); a person's dismissal is an "edit the message" answer,
  and the file is rewritten and read back before the question is asked again.
- **An `open` finding is its own list, not a `problem`.** Spec R9 put it among `findings`'
  problems. Kept apart, so `check` can report a malformed file without flagging a review a stopped
  ship left waiting; `findings` still exits 1 on either, and `ship` refuses an open one (R11).
- **The template's title is `# Findings`,** like `checks.md` and `notes.md`, the shape
  `test_defaults.py` holds a change's working files to; spec and plan carry `NNN — TITLE`.
- **`findings` is a read-only command, so it joins `READ_ONLY`,** which puts its rule in
  `ALLOW_RULES`; this repo's `.claude/settings.json` gets it as 030 gave `preflight` its rule.
