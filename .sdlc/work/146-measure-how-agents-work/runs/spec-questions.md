
**Open questions resolved**

- **Which behaviours make the starting set?** The intent's six, each tied to a decision retro
  makes:
  - `edits=` and `shell_edits=`: does a model or prompt use the edit tools (the Fable builder's 28
    inline `str.replace` edits);
  - `bg=`: does 140's "nothing in the background" rule hold, and bug 2026-11-18-26's pattern;
  - `tool_errors=`: a model fighting its tools;
  - `test_runs=`: how a role checks its work;
  - `broke=`: edits that break the build, as the shell edit that left `sdlc.py` unparseable did.

  Nothing else is added (Boundaries: ask first).
- **How is each behaviour recognised?**
  - A shell edit and a test run: by the command, as `is_read()` reads commands, with named shapes
    and stated lower bounds.
  - `bg=`: by the tool's own result (`toolUseResult.backgroundTaskId`, read in a recorded
    transcript), plus a trailing `&`.
  - `broke=`: by the result's output, after an edit.
- **Every tool or only the top few?** Every tool, one `Sdlc-Calls` line per role. A cut hides the
  rare call that matters, and `Sdlc-Role` can't hold names that contain `:`. This is a default you
  can overturn at review.

**Open questions left for you**

- **Backfill of 139–143.** Seed 2026-11-18-40's comparison depends on it, and those transcripts are
  deleted after about 30 days. Your options:
  - **(a) No backfill.** The Fable comparison stays a one-off hand reading, and retro's model groups
    start with the changes after this one.
  - **(b) A read-only `sdlc.py measure <NNN> --agents`.** It prints a closed change's role counts
    from the transcripts still on the machine. It commits nothing and retro never reads it. It's
    cheap, and enough for the seed's evaluation if run within the month. It is a new subcommand,
    with its own `READ_ONLY` entry and test, so it is scope beyond the intent unless you add it.
  - **(c) A committed backfill record**, such as a `Measure NNN-slug` commit carrying the trailers.
    Retro would then compare 139–143 with everything else. But it is a new commit kind that
    `closed_changes()` and retro must learn to read, and a larger change, better as its own.

  My lean is (b), added to this change only if you say so.
