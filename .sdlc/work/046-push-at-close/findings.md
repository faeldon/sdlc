# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.

## F1. [important] [context] Six lines still said only publish pushes

The bug, idea and triage skills' "Only `/sdlc:publish` pushes", the `[release] remote` comment in
docs/REFERENCE.md and in `CONFIG_KEYS`, and the release section's comment in sdlc.py. Corrected in
this run.

Evidence: skills/bug/SKILL.md:168, skills/idea/SKILL.md:162, skills/triage/SKILL.md:216, docs/REFERENCE.md:59, scripts/sdlc.py:258, scripts/sdlc.py:3935
Class: an invariant loosened while the sentences restating it elsewhere were left as they were
Disposition: fixed

## F2. [important] [correctness] Close lists push in done when the remote refused it

`push()` sets `push_failed` but returns None, so the loop appends `push` to `done` either way; the
close skill reads `push` in `done` as "main is on the remote", and would say the issues close
when they don't. Release appends it only on success; the test pins the wrong behaviour.

Evidence: scripts/sdlc.py:3461, scripts/sdlc.py:3505, skills/close/SKILL.md:109, tests/test_push.py:153
Class: a never-refusing step reporting its outcome through a channel that can't say it failed
Disposition: fixed
By: fresh

## F3. [important] [correctness] Close's push plan lists the branch's commits, not what the push sends

The plan reads `origin/main..<branch>`, but the push sends `main`. A dropped branch can sit behind
`main` (close checks behind only for shipped), so `main`'s other unpushed commits go unlisted; a
rerun after the Close commit labels it `(new)` and leaves out `main` past the branch. The yes then
covers less than the push sends. No test covers a dropped change's push.

Evidence: scripts/sdlc.py:3369, scripts/sdlc.py:3344, scripts/sdlc.py:3464, skills/close/SKILL.md:71
Class: what the WAIT shows computed from a different ref than the write acts on
Disposition: fixed
By: fresh

## F4. [important] [correctness] publish --check can't tell the skill which question to ask

`--check` returns before any step's `done_already()` runs, so nothing says the tag is out, main is
pushed, or the publish command ran. The skill can't pick the push-only question, a push-only run
would also run a `release.publish` its question never named, and R6's "nothing to publish" has no
code.

Evidence: scripts/sdlc.py:4766, scripts/sdlc.py:4771, skills/publish/SKILL.md:64, .sdlc/work/046-push-at-close/spec.md:31
Class: a requirement with no code, and a WAIT whose wording depends on state the script doesn't report
Disposition: fixed
By: fresh

## F5. [nit] [correctness] R3 says push: null; the code returns an off plan, and pushes without a tracking ref

`_push_plan` returns `{on: false, …, off_because}`, and with no tracking ref keeps the push on with
`unpushed: null`. Skills and tests follow the code; the spec doesn't.

Evidence: scripts/sdlc.py:4664, .sdlc/work/046-push-at-close/spec.md:20
Class: the design moved during the build and its requirement wasn't updated
Disposition: fixed
By: fresh

## F6. [nit] [correctness] A push can wait on a credential prompt

`_push` goes through `_git_err`, which leaves stdin open and doesn't set `GIT_TERMINAL_PROMPT=0`.
Close and release now push by default on GitHub hosts, so an HTTPS remote with no credential
helper may ask rather than fail into `push_failed`. Publish always pushed this way. Raised by the
fresh reviewer as unsure; confirmed only by reading, not by a run.

Evidence: scripts/sdlc.py:4341, scripts/sdlc.py:4613
Class: a non-interactive step running a command that can ask
Disposition: fixed
By: fresh
