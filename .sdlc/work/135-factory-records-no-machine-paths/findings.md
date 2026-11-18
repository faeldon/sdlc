# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.

## F1. [important] [correctness] `is_read()` tokenises the command with shlex `punctuation_chars`, so `<` and `>` in a mark become redirects.

plugins/factory/scripts/factory.py:1348: `is_read()` tokenises the command with shlex `punctuation_chars`, so `<` and `>` in a mark become redirects. Now that `cmd_agent` files `<home>` in place of `~`, a read that names a home path and prints output but has no `exit:` line is judged a non-read. `read_evidence()` (`:1379`) then reports a missing exit, and the run spends a mend it used to not need. Probed directly: `is_read("ls ~/.nvm/bin")` is True, `is_read("ls <home>/.nvm/bin")` is False. Fix: in `is_read()`, before tokenising, swap the marks for plain words, e.g. `command.replace(HOME_MARK, "HOME").replace(CLONE_MARK, "CLONE")`. Probed: `ls <home>/.nvm/bin` then reads True, and a redirect written after the swap stays a non-read. Add a test that a reply whose read command names the home path and prints a line, with no `exit:`, passes `read_evidence()` as it did before.

Evidence: plugins/factory/scripts/factory.py:1348
Class: code review, round 1
Disposition: fixed
By: code

## F2. [pre-existing] [correctness] the same tokenisation makes `git -C <path-to-clone> status` a non-read, since `CLONE_MARK` already has `<`/`>` in it.

plugins/factory/scripts/factory.py:1348: the same tokenisation makes `git -C <path-to-clone> status` a non-read, since `CLONE_MARK` already has `<`/`>` in it. The fix above covers both marks, so it can be filed with this change or on its own.

Evidence: plugins/factory/scripts/factory.py:1348
Class: code review, round 1
Disposition: recorded
By: code
