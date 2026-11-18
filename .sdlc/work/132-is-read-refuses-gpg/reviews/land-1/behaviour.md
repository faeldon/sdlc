VERDICT: PASS

The change does what the intent's Approach asks. `is_read()` now refuses `--show-signature` and any `--format`/`--pretty` value holding `%G`, and every read the intent names stays a read. I found nothing that fails, so there is no CHANGE and no DECISION. Main has no commits past the rebase base `3c65ea1`, so the diff under review is the whole change.

## Notes

- **Spec:** Tier 1, so the intent's Approach is the spec. There is no `spec.md`.
- **checks.md:** absent, so there are no acceptance checks to read.
- **Gate:** `build/round-1.gate.md` is `GATE: PASS` (`./check.sh`, exit 0, tree unchanged). I did not run the gate again.
- **Decision D1** (`log.showSignature=true` in a host's git config left uncovered) is ticked and settled. I have not raised it again. The code comment says it is uncovered.
- **Abbreviations:** git 2.56 rejects every shorter spelling of `--show-signature`, `--format` and `--pretty` (exit 128, `unrecognized argument`). The exact-name matches in `GIT_RUNS` and `GIT_FORMATS` are therefore correct for this git.
- **One `is_read()` case judged a read, and it is harmless:** `git log --show-sig` returns True. Git refuses that spelling before anything runs, so no gpg is started. This is not a gap.
- **Not verified here:** that `%G` actually runs gpg. I had no signed commit, so I rely on the round-1 reviewer's probe for that.
- **Comment nit (already F1 in `findings.md`, minor):** the `_git_reads()` comment says a `%G` value "as the next word" runs gpg, but git does not accept the separate-word form. The refusal is harmless over-refusal, so this is not a CHANGE.
- **Worktree state:** the only untracked files are `build/land-1.gate.md` and `runs/reviewer-behaviour.sessions`, both written by the factory run before this review. I wrote nothing to the worktree. My probes ran from a `/tmp` scratch directory, which I removed.

## Evidence

$ ls -la .sdlc/work/132-is-read-refuses-gpg/ .sdlc/work/132-is-read-refuses-gpg/build/; git log --oneline -n 5; git diff --stat 3c65ea17dccda103d65fada9cf66311be7ecaef1...HEAD
```
ad9dba6 is_read() refuses git's signature options that run gpg
3c65ea1 File 2026-11-18-16
...
 plugins/factory/scripts/factory.py | 26 +++++--
 tests/test_factory.py              | 14 ++++
 15 files changed, 339 insertions(+), 5 deletions(-)
```
exit: 0

$ cat intent.md; cat spec.md; cat checks.md; cat decisions.md
```
# 132 — is_read() refuses git's signature options that run gpg
... ## Approach
`--show-signature` added to `GIT_RUNS` with its shortest abbreviation; a check in `_git_reads()`
refusing a `--format`/`--pretty`/`format:` value that holds `%G`; table rows; the comment fixed.
...
- [x] D1 (builder round 1, default): Leave a host's own git config (`log.showSignature=true`) uncovered ...
```
exit: 0
(spec.md and checks.md do not exist; `cat` printed nothing for them, and `ls` lists neither.)

$ cat .sdlc/work/132-is-read-refuses-gpg/build/round-1.gate.md
```
GATE: PASS
## Attempt 1
Verdict: PASS
Command: ./check.sh
Exit: 0
Tree: unchanged
```
exit: 0

$ git diff 3c65ea17dccda103d65fada9cf66311be7ecaef1...HEAD -- plugins/factory/scripts/factory.py tests/test_factory.py
```
+GIT_RUNS = (("--ext-diff", ...), ("--textconv", ...), ("--show-signature", len("--show-signature")))
+GIT_FORMATS = ("--format", "--pretty")
+        if name in GIT_FORMATS:
+            value = arg.split("=", 1)[1] if "=" in arg else " ".join(rest[k + 1 : k + 2])
+            if "%G" in value:
+                return False
... (NON_READS gains 11 rows; READS gains 3)
```
exit: 0

$ git log --oneline 3c65ea17dccda103d65fada9cf66311be7ecaef1..main; git rev-parse --abbrev-ref HEAD main
```
132-is-read-refuses-gpg
main
```
exit: 0 (the log is empty: main has no commits past the base)

$ cat .sdlc/work/132-is-read-refuses-gpg/findings.md; cat .sdlc/work/132-is-read-refuses-gpg/reviews/round-1/code.md
```
## F1. [nit] [correctness] ... in git 2.56, `--format` without `=` is unrecognised ...
## F2. [nit] ... ("--show-signature", len("--show-signature")) ...
## F3. [nit] ... a literal `%%G` is also refused.
VERDICT: PASS
...
```
exit: 0

$ grep -n "def is_read" -A 40 plugins/factory/scripts/factory.py; ls .sdlc/work/132-is-read-refuses-gpg/ | grep -E "^(spec|checks)\.md$"; grep -n "def test_.*read" tests/test_factory.py
```
1314:def is_read(command: str) -> bool:
...
1397:def test_a_read_is_only_what_the_script_can_tell_changes_nothing() -> None:
```
exit: 0 (the `ls | grep` for spec.md/checks.md matched nothing: exit 1 from grep, shown as exit: 1 in the earlier read of the same check)

$ git -C r log --show-signature -1; git -C r log --show-sig -1; git -C r log --show-si -1; git -C r show --show-signature HEAD; git -C r log --form=%H -1; git -C r log --format=%H -1; git -C r log --pre=%H -1; git -C r log --form=%G? -1; git -C r log --pretty=%G? -1; git -C r log --no-show-signature -1   (scratch repo /tmp/behave-132.EorI/r, one empty commit)
```
--show-signature: exit 0 | --show-sig: exit 128 "fatal: unrecognized argument: --show-sig"
--show-si: exit 128 | show --show-signature: exit 0 | --form=%H: exit 128 | --format=%H: exit 0 (prints hash)
--pre=%H: exit 128 | --form=%G?: exit 128 | --pretty=%G?: exit 0 (prints N) | --no-show-signature: exit 0
```
exit: 0 for the loop. (The first attempt of this loop passed each command as one unsplit word and failed on that; it is not evidence.)

$ python3 -I -B probe.py plugins/factory/scripts/factory.py   (loads factory.py by path; calls is_read on 21 commands)
```
is_read=False want=False git log --show-signature
is_read=False want=False git show --show-signature HEAD
is_read=False want=False git -C . log -1 --show-signature --oneline
is_read=False want=False git log --format=%G?
is_read=False want=False git log --pretty=format:'%h %GS'
is_read=False want=False git show -s --format='%GG' HEAD
is_read=False want=False git log --format %G?
is_read=False want=False git -c log.showSignature=true log
is_read=True  want=True  git log --format=%H %s
is_read=True  want=True  git show HEAD
is_read=True  want=True  git log --no-show-signature -1
is_read=True  want=True  git log --format=%h -1
is_read=True  want=False git log --show-sig     <-- git rejects this spelling; no gpg runs
...
mismatches: 1
```
exit: 0

$ python3 -I -B evid.py plugins/factory/scripts/factory.py   (read_evidence on replies ending in each command, no exit: line)
```
$ git log --show-signature -1 -> ['probe: `git log --show-signature -1` has no `exit:` line']
$ git log --format=%G? -1 -> ['probe: `git log --format=%G? -1` has no `exit:` line']
$ git log --format=%H -1 -> accepted (no problem)
$ git show HEAD -> accepted (no problem)
```
exit: 0

$ rm -rf /tmp/behave-132.EorI; git status --short
```
?? .sdlc/work/132-is-read-refuses-gpg/build/land-1.gate.md
?? .sdlc/work/132-is-read-refuses-gpg/runs/reviewer-behaviour.sessions
```
exit: 0
