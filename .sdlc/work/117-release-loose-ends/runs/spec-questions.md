
**Open questions resolved:**
- *Adoption commit: setup.json's first record, or the first commit adding `.sdlc/config.toml`?* The first commit adding `.sdlc/config.toml`. setup.json is rewritten on every `record` and holds no date, while config.toml is what makes a repo set up (`cmd_record` refuses without it).
- *Should release push the notes ref too?* No. Only publish's `run_command()` writes `refs/notes/sdlc`; release writes only `refs/notes/sdlc-prepared`, so release has nothing on that ref to push.

**Open questions for you:**
- **A. Should publish fetch the remote's notes in `--check`, before the question?**
  - If yes: the question can tell a second clone the upload is already done. But a ref is then written before the WAIT, which means naming a fifth exception in AGENTS.md's *Writes before a WAIT*.
  - If no (what the spec does): the read before the question stays write-free. A second clone may be asked "…then run `<command>`?", and after the yes the run skips it and reports `publish command (already done)`.
- **B. May AGENTS.md's "one shape" invariant gain a second exception, `templates/changelog.md`?**
  - If yes (what the spec does): the heading is a real template, as the intent asks.
  - If no: use a `release.changelog_heading` config key with `{version}` and `{date}` instead, which needs no new template and no invariant edit, but gives a host only the heading line to change.
