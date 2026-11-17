DECISION: ESCALATE

**Why.** Both reviewers passed round 1 with no Critical or Required findings. The gate is green (`./check.sh`, 2209 passed). Every requirement from R1 to R12 has code and a test that fails without it, and the person had already settled both open questions in `intent.md`. I'm escalating anyway, for two reasons. First, the change adds a write that leaves the machine: publish now pushes `refs/notes/sdlc` to a host's `release.remote`, and after the yes it fetches into a new local ref, `refs/notes/sdlc-remote`. Second, it widens the published host contract: a new template a host can override (`templates/changelog.md` in `TEMPLATE_READS` and `DOC_TEMPLATES`), new report keys (`notes_push_failed`, `notes_fetch_failed`, `push notes` in `done` and `will_run`), and a second exception to a stated AGENTS.md invariant. Both were approved in the intent, but they touch a published interface and a remote, so a person should look before this lands.

**Open items.** No CHANGE is open. These are non-blocking reviewer notes:
- reviewer-test: no test makes the notes fetch fail, so `notes_fetch_failed` and the "publish goes on with local notes" path are untested. The builder also says so.
- reviewer-code: no new test covers R6's "neither commit" case, where the hint stays `<the commit that released it>`. The code keeps it.
- reviewer-code (nit): in `unreleased()`, `later = last and adopt and last != adopt` holds a string or None rather than a bool.

**Decisions to confirm.** None. There is no `decisions.md`. Questions A and B, and the adoption-commit question, were decided in `intent.md`: fetch after the yes, `templates/changelog.md` as the second verbatim exception, and the first commit adding `.sdlc/config.toml`.

**For the person at ship.**
1. Look first at `cmd_publish` in `scripts/sdlc.py`:
   - Where `_fetch_notes` runs: it should run only with a command, never under `--check`, and before the step loop.
   - The notes push after the loop: it should go through `_push()`, never forced, and a refusal should not change the exit code.
   - That a fetch failure is reported, not fatal.
2. Then check that `with_changelog` without the marker produces exactly today's bytes. The builder pinned an existing CRLF quirk (`\n\r\n`) rather than fixing it.
3. Then read the AGENTS.md "one shape" bullet edit and the `EXCEPTIONS` entry in `tests/test_defaults.py`.
4. Last, the publish skill's *Out of scope* line, which now says publish pushes its notes.

- IMPACT: minor — hosts can newly mark where releases go in the changelog, override the section template, and use `__version__` as a version line. A second clone now skips an upload already made. With no marker or override, output is byte-identical.

`notes.md` doesn't exist, so there are no undone items to dispose of.

**How to recover**
- RECOVER: templates/changelog.md: `git revert <the change's commit>` restores the old f-string, and the plugin's template renders exactly the same bytes, so the plugin's default never wrote different text into a host's changelog. A section a host's own override already wrote into a released changelog, its tag message, or a hosted release created with `--notes-from-tag` can't be reverted. Fix forward: the host edits its `CHANGELOG` by hand and corrects the hosted release's text. Tags already pushed stay as they are. Per `plan.md`'s Rollback, the notes this change pushes come off a remote with `git push <remote> :refs/notes/sdlc`, and the local mirror with `git update-ref -d refs/notes/sdlc-remote`.
