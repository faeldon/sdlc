VERDICT: PASS

## Notes

I found no security finding at any severity. The change makes four small code edits, one skill-text edit and many test edits. None of them widens a trust boundary, and two of them narrow one.

**Trust boundaries the diff touches**

- **Autopilot's `--goal` text** (`plugins/factory/skills/autopilot/SKILL.md`). The goal is the person's own words, and the skill pastes it into a bash command. The old text only said "quote" it. That left room for double quotes, where `$`, backticks and `"` in the goal would still be expanded (tampering, and a path to running a command). The new text says to single-quote it, writing each `'` as `'\''`. That is the correct POSIX escape and closes the gap. The skill text is still the only control here. The input is the person's own words, given in their own session, so I don't treat it as hostile.
- **Issue bodies in `cmd_intake()`** (`scripts/sdlc.py:8077`). An issue body is untrusted text that anyone can file. `from_host` used to be true when the upstream marker appeared anywhere in the body. Now it is true only when the body opens with it. Someone could still put the marker first by hand and get the `Origin: host` label, but that was already true before. The effect is a label on a triage entry, nothing more, and the change makes spoofing harder, not easier.
- **`preflight --preview`** (`scripts/sdlc.py:8557`). It now refuses the clause flags instead of quietly ignoring them. This adds no new input path; it just refuses more.
- **`closing.py`'s `fix_trailers()` and `origin_trailer()`.** They now catch only `(OSError, ValueError)` instead of every `Exception`.
  - `_git()` already turns a failed command or a missing git into `None`.
  - A blob that isn't UTF-8 raises `UnicodeDecodeError`, which is a `ValueError`, so it is still caught.
  - The data they parse comes from the change's own branch. A coding error now stops the close where it used to be hidden. That is a robustness question, not something an attacker can use.
- **`retro.py`'s `_read_hosts()`.** A host path that is both listed and excluded with `!` is now skipped, so it is never read. That fits the privacy rule for host repos ("never read"). `excluded` is defined a few lines above, by `host_list()`, and it still goes into `known`, so discovery doesn't bring the path back in.
- **`run_state.uncarried()`.** It now gives a more accurate reason, plus a more precise mend message. Every default it reported before, it still reports, so nothing is let through.

**Secrets, dependencies, destructive operations**

- No secret, path or personal data appears in the code, the tests or the change's own files.
- No dependency was added.
- The change adds no deleting, overwriting, pushing or publishing step.

**What I checked**

- I read the non-test diff in full, `decisions.md` (D1 matches the `_read_hosts` edit), and the round-1 gate record (`GATE: PASS`, `./check.sh`, exit 0).
- I tested the spec's claim that nit 2026-11-21-20 is stale. With the module loaded, `_SCP_RE` matches `user@alias:org/repo.git` in prose, so a dotless ssh-alias remote is already redacted and retiring that nit is right.
- I checked that `_git()` catches only `CalledProcessError` and `FileNotFoundError`, and that it decodes as UTF-8 with no `errors=`. A bad blob therefore raises a `ValueError`, which the narrowed catch still handles.
