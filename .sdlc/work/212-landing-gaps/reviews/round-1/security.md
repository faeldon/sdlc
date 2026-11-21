VERDICT: PASS

## Notes

No Critical or High findings. This change only makes the read-only list stricter, and I found no way past it.

**Trust boundary.** A changed `checks.md` command comes from model output, so it is untrusted. If `read_only_command()` passes it and the approver agrees, `train --run` runs it with no person watching. The two STRIDE threats that matter here are information disclosure (reading outside the checkout) and elevation (running an arbitrary program while claiming to be read-only).

- **Stricter only.** Every new check either adds another way to refuse or adds a new early refusal. Nothing that was refused before is let through now, so the intent's constraint holds.
- **ugrep's link-following options are covered.** I ran ugrep 7.8.4 (the same binary the builder used) to test it.
  - `-R`/`-S` are already caught by `GREP_FOLLOWS`.
  - `--dereference-recursive`, `--dereference-files` and the undocumented `--dereference` are caught by the prefix rule.
  - `-d`/`--directories=dereference-recurse` is caught as a substring of the option word, or as a word on its own. That covers glued values, separate values and bundled forms like `-rd`.
  - ugrep rejects abbreviated action values (`-d deref` and `-d dereference` both exit 2), so the full-string match is enough.
- **ugrep's program-running options are covered.** ugrep's `--help` lists `--filter`, `--pager`, `--view`, `--save-config` and `--config`/`---`, and none of them has a short form. ugrep also rejects prefixes of them: `--filt=`, `--filte=`, `--pag=` and `--vie=` all exit 2. So the exact-name match on `GREP_REFUSED_LONG` is enough.
  - The builder found that `--filter='txt:touch ran'` ran `touch` and that the old list let it through. That was a real hole, and refusing it is the right fix. I agree with D1's default.
- **Quoting tricks.** `shlex.split(posix=True)` strips quotes the same way `sh` does, so a word like `"--fil"ter=…` is read as `--filter=…` and refused. `$`, `\` and backticks are still refused outside single quotes, double quotes included.
- **Remaining paths are low risk.**
  - `-Q` (ugrep's query interface, which can open an editor) needs a terminal. With stdin closed it exits 2 ("no ANSI terminal keyboard detected"), so it can't do anything unattended, and `--view` is refused anyway.
  - `--include-from`, `--exclude-from`, `--ignore-files=FILE` and `-f FILE` are covered by the existing path rule on option values.
  - ugrep loads `.ugrep` automatically only when it is run as `ug`, and `ug` isn't on `READ_ONLY_PROGRAMS`.
- **D2 (refuse the bare word `dereference-recurse` anywhere).** This fails safe: the worst case is that a check grepping for that literal text needs a person. I agree with the default.
- **The readiness test** only tests: it deletes a fixture's `decision.md` and reads the train's next step. Nothing it does reaches past the test repo. The builder's evidence shows that changing the cause to `review` makes it fail.
- **No other copies of the grep rules.** `git grep` finds them nowhere outside `landing.py` and the tests, so no pinned copy needed updating.

**What I checked and ran.**
- Read the intent, `decisions.md`, the builder's report and the diff.
- Read the gate record `build/round-1.gate.md`: PASS, `./check.sh` exit 0.
- Ran the ugrep 7.8.4 binary through `ARGV0=ugrep` in a fresh temp directory. I tried prefixes of every refused option and the action values, and read its `--help` for options that run programs, follow links or use a config file.
- An earlier probe that ran `rm -rf *` after `cd` into a temp directory was blocked by a safety check before it ran. Nothing was deleted. I used a fresh `mktemp -d` directory instead, so there is nothing for you to clean up there.

- PREEXISTING: plugins/factory/scripts/landing.py:816: `GREP_FOLLOWS` refuses `-O` (BSD's follow-links flag) for every grep, so ugrep's harmless `-O EXT` (search by file extension) is refused too. This is overly strict, not a hole.
- NIT: plugins/factory/scripts/landing.py:925: a GNU or BSD grep refusal of `--config` or `---…` says "makes ugrep …", which may confuse a person reading it on a host without ugrep. "makes grep (ugrep) …" would be clearer {docs S low}
