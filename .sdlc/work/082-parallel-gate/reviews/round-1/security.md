VERDICT: PASS

## Notes

**Trust boundaries in this diff.** The change only touches this repo's gate. No host installs any of it, and it adds no new untrusted input. I looked at three boundaries:
- **The new dependency** (`pytest-xdist`) and what it pulls in (`execnet`).
- **The privacy scan** in `tests/test_nothing_local.py`. This repo's rule that no local path or project name reaches GitHub depends on it. The risk here is that a narrower scan lets a leak through (information disclosure).
- **The change's own files**, which get committed and become public.

With STRIDE: the dependency is a tampering and supply-chain question, and the scan is an information-disclosure question. The diff has no authentication, no injection path and no destructive operation.

**Medium: this change's own gate record holds the author's home path and username**
- `.sdlc/work/082-parallel-gate/build/round-1.gate.md:104,106,122,124` contains lines like `Validating marketplace manifest: /Users/<user>/…/082-parallel-gate/...`.
- They come from `claude plugin validate`, and the record now saves that output even for a passing attempt (attempt 2).
- The builder's hand fix (D3) cleaned attempt 1, but attempt 2 was written afterwards and brought the path back.
- I confirmed it: `pytest tests/test_nothing_local.py` in this worktree now fails `test_nothing_in_the_repo_is_forbidden` on those four lines.
- **Why this isn't a CHANGE:** the gate stops it from landing, and what it exposes is a local username, not a secret.
- **Fix:** before landing, the record must hold no absolute path. That calls for the factory-side redaction below rather than more hand edits, because each new gate attempt writes the path again. It is also a red gate, so the code and test reviewers will see it.

- PREEXISTING: plugins/factory/scripts/factory.py:1210: `gate` copies the last `GATE_TAIL` lines of `check.sh`'s output into `build/round-<N>.gate.md`, which gets committed, without removing the checkout root or `$HOME`. So every gate record can publish the machine's home path. History already shows this: `git log --all -G'/Users/'` matches `a17dd91` (083's artifacts) and `90d71b9`. The fix is to replace the worktree root with `<path-to-clone>` and `Path.home()` with `~` in `tail` before writing it. The history copies would need a decision from the person (rewrite history or accept them).

**What the change does well**
- **The scan covers what can actually be published.** It moved from `rglob` to `git ls-files -z --cached --others --exclude-standard`. That lists exactly the files that could reach GitHub: tracked files, plus new untracked ones that aren't ignored. A new file is still read before its first commit. Using `-z` keeps odd filenames intact, and `check=True` means a failed git call turns the gate red rather than letting a silent empty scan pass.
- **Nothing that could ship was dropped from the scan.** The `SKIP_DIRS` list it replaced (`.git`, `.venv`, caches) is all covered by `.gitignore` or is outside the working tree. The worktree exclusion and the `LOCAL` and self exclusions are kept.
- **The new test is sound.** `test_an_ignored_file_is_not_read_but_an_untracked_one_is` checks both directions: an ignored file is skipped and an untracked one is read.
- **The scan is already earning its keep.** It now reads this change's untracked folder and caught the leak above, which is the behaviour the intent asked for.

**Dependency check**
- `pytest-xdist 3.8.0` and `execnet 2.1.2` are both well-established pytest-dev projects, pinned with sha256 hashes in `uv.lock`.
- Both install from pure-Python wheels, so no install scripts run.
- They are in the `dev` group only, so the plugin's PEP 723 block and what a host runs are unchanged.
- `execnet` starts its local workers with popen; it opens no network listener. It is justified because it is what runs the suite in parallel.

**CI and the gate**
- The Linux job in `check.yml` gains `-n auto`. No new secrets, permissions or triggers.
- `check.sh` keeps the comment that pytest's exit 5 ("no tests collected") is a red gate, and xdist keeps pytest's exit codes.
- Nothing here runs `run-cases` or any paid call.

**What I ran**
- `git status` and `git diff` (the whole diff, including `uv.lock`).
- Read `intent.md` and `decisions.md`, and the build round's report.
- `pytest -q tests/test_nothing_local.py`: 7 passed, 1 failed on the gate record above.
- A grep of the change folder for home paths.
- `git log --all -G'/Users/'` for leaks already in history.
- `git check-ignore` and `.gitignore` to confirm what the git-based scan excludes.
