VERDICT: PASS

## Notes

**Trust boundaries the diff touches**
- A `checks.md` that a landing agent changed after the person's yes. This is text a model wrote, and the train's loop now runs it unattended through `sh -c`.
- The approver's reply on that file, which is also model output.
- The base branch's `[commands] build`, `build_when` and `[review] sensitive`.
- The new records committed with the change: `build/land-<n>.build.md`, `build/land-<n>.checks.md`, and the check output that goes into `build/land-accept.md`.

**What I checked with STRIDE**
- **Tampering and elevation (a changed check runs unattended).** This needs both the person-approved hash or the script's read-only list and a current HARMLESS from the approver. The approver's word alone never runs a check: `checks_clearance()` builds `off_list` before it reads the record.
- **Re-reads close the gaps.** `_run_plan()` works out the clearance again just before `accept` (`_clearance_now()`). The `Judged:` hash is taken before the approver session starts, so a file edited during it reads as stale and goes back to `checks`.
- **Commands come from the real parser.** They come from `sdlc.py preflight` (`acceptance()`), the same parser `accept` runs them with, so the list judges the text that executes.
- **An older train state is safe.** One without `checks_sha` counts every check as changed.
- **The build and gate inputs can't be edited by the change.** `commands.build`, `build_when` and the sensitive list are read from `<base>:.sdlc/config.toml` through `_base_command()`, never from the checkout.
- **A build round never runs the build.** `--build` without `--land` is refused.
- **The `land-checks` task can't run out of turn.** `_land_task()` refuses unless the train names `checks` for this change, and `cmd_agent` refuses any role but `approver`.
- **Approver replies stay out of review parsing.** They are filed under `build/`, not `reviews/land-<n>/`, so they are never read as a review.

**I probed `read_only_command()` directly against a scratch checkout with a symlink pointing out of it:**
- `grep -r . link/`, `cat link/f`, `grep -rf link/f .` and `git diff --no-index link/f x` are refused, as is the symlink case.
- `--output-indicator-new=x` is refused (over-refusal, which is fine), as are `&` inside double quotes and an open quote.
- Git does not accept abbreviated long options here: `git log --outp=x` and `--ext-d` fail with "unrecognized argument". So the prefix refusal of `--output`, `--ext-diff` and `--textconv` holds.
- `tail -f x` passes the list, but `sdlc.py accept` runs each check with `stdin=DEVNULL` and `CHECK_TIMEOUT`, so a check that hangs is bounded.

**Medium: `grep -R` follows symlinks the path rule never sees** (`plugins/factory/scripts/landing.py:866`)
- `read_only_command("grep -R . .", co)` returns None, and with a symlink `link -> /outside` under the checkout, `grep -R` reads through it.
- `cmd_accept` copies the last 80 lines of each check's output into `build/land-accept.md`. That file is committed with the change and pushed when `git.push` is set.
- So a landing agent that adds an out-pointing symlink and a `grep -R …` check could copy files from outside the checkout into a committed record, if the approver judges it HARMLESS. The approver is shown the commands, not the tree's symlinks.
- Rated Medium, not High: the same agent's code already runs unattended in the tip's gate through the change's own tests, so this adds no new capability. It does break R5's stated promise that "a symlink out of it is refused".
- Fix: refuse grep's symlink-following flags, by checking each short-option cluster for `R` plus the long forms `--dereference-recursive`, and BSD's `-S` and `-O`. Better, refuse recursive grep altogether (`-r`/`-R`/`--recursive`), since GNU and BSD treat symlinks differently.

**Low: a builder can forge a build record.** It could hand-write a `BUILD: PASS` attempt in `build/land-<n>.build.md` with the stacked commit's hash, and `_read_builds()` would believe it. Gate and accept records already work this way, and the agent could equally make the test suite pass, so this is not raised as a CHANGE.

- PREEXISTING: plugins/factory/scripts/landing.py:2180: gate/build/accept records are trusted by the hash they state, which any agent that can write in the change's folder can write; a script-side signature or a record kept outside the tree would close it

- NIT: plugins/factory/scripts/landing.py:866: `grep -R` (and BSD `-S`/`-O`) passes the read-only list and follows a symlink out of the checkout; refuse recursive grep's symlink-following flags, or recursive grep entirely {robustness S med}
- NIT: plugins/factory/scripts/landing.py:842: the docstring says a symlink out is refused "for a word naming an existing path"; say that a program walking the tree itself is not covered {docs S low}

**Done well:**
- Checking the list before the approver means a paid model answer can never clear a command off the list.
- The clearance is worked out again just before `accept` runs.
- Glued short-option values are path-checked (D1).
- Base-branch-only config is reused through `_base_command()`.
- No new dependency, and no secret in the code or the new prompt.

**What I ran:** the gate record (`build/round-1.gate.md`) is PASS. I read the diffs of `landing.py` and `factory.py`, plus `sdlc.py`'s `cmd_accept`. I probed `read_only_command()` with the cases above, and probed git's handling of abbreviated options in a scratch repo under `/tmp`. I didn't run the gate.
