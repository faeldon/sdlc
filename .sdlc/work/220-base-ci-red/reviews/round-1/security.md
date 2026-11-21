VERDICT: PASS

## Notes

**Trust boundaries checked (STRIDE)**
- **What `gh run list` returns (network → core).** Workflow names, run URLs, `status` and `conclusion` come from GitHub, and they reach three places as text: `status`'s Problems, ship's WAIT question and the factory's landing signals.
  - Tampering / injection: no shell is involved. `_gh` passes an argv list and has no `shell=True`. Core builds strings from these values with f-strings and never runs them.
  - Names come only from runs whose `headSha` equals the base tip (`github.py` `ci()`), so they come from workflow files on the base branch. A forked PR's run on another sha can't put text there.
  - Malformed JSON, a non-list, non-dict rows, a timeout, an `OSError` or a non-zero exit all read as `unknown`. Core checks `state ∈ CI_STATES` before it trusts a reading (`base_ci()`), and it catches an exception the tracker raises.
- **Fail-open on unknown.** A `gh` that is unreachable or broken makes the red signal silent, and the auto-landing still approves itself. The intent says this outright ("A CI the tracker can't read is unknown, never red"), and this change adds a signal without removing a control, so it is not a weakened control. Info only.
- **Can a change lighten its own signal?** No. `base_ci()` gets `home` and the main checkout's `cfg`, and it reads the remote-tracking ref through local git. Nothing in the change's own tree can steer which tracker runs or which sha is read.
- **Arguments passed to `gh`.** `--commit <sha>` comes from `rev-parse --verify`, so it is a hex string. `--branch <trunk>` comes from the host's own `git.base`, and the host already controls it. That is not a new boundary.
- **The cache file.** `CI_CACHE` sits in the git common dir. It is written through a temp file and `os.replace`, with `newline="\n"`. A forged cache needs write access to `.git`, and that access already gives full control. A cache that won't parse, comes from another branch or sha, or is dated in the future is read again from the tracker.
- **Repudiation / information disclosure.**
  - `why` holds the last line of `gh`'s stderr and appears only in preflight's JSON. `gh` doesn't print tokens on stderr for `run list`, so this is low.
  - Only the branch, sha, run names, states and URLs reach the change's artifacts and output: no secrets, no personal data.
- **Denial of service.**
  - `status` waits at most `CI_TIMEOUT` (10 s) once per tip every 600 s.
  - A landing's preflights share one reading per 60 s.
  - `--limit 50` bounds how much output is parsed.
- **Destructive operations.** There are none. The only new write is the state cache, which is outside every checkout, and AGENTS.md now names it beside the update cache.
- **Dependencies.** None added.

**What is done well**
- `CI_RED`/`CI_FAILED` are kept apart from cancelled and skipped runs, so neither of those can raise a false red.
- The red reading is added after preflight's `problems` are built, so it can never refuse or change the exit code.
- `ci_problem` is in `cli_status()` and not in `analyze()`, so `vet --strict` is untouched.

**What I checked**
- I read the diff of `scripts/sdlc.py`, `scripts/trackers/github.py` and `plugins/factory/scripts/landing.py`, plus the intent, the spec and the gate record.
- The gate record `build/round-1.gate.md` is PASS (`./check.sh`, exit 0).
- There is no `decisions.md`, so no decision has been settled.
