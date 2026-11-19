VERDICT: PASS

## Notes

Round 2 covers the reworked paths: `plugins/factory/scripts/landing.py` and `tests/test_train.py`.

**The kept change from round 1 is done.** It was this, quoted from round 1:

> [correctness] plugins/factory/scripts/factory.py:4431: `judged = landing.checks_sha(folder)[:16]` raises `TypeError` when the change's `checks.md` was removed after `--begin`.

- `checks_clearance()` (landing.py:937) now returns `step: "accept"` when `sha is None`. It returns before it reads the record, giving the reason "checks.md is gone, so there is nothing to judge".
- So `_land_task` refuses `land-checks` before `factory.py:4431` can index `None`.
- `test_land_checks_refuses_outside_a_changed_train_change` has a new case for it. The builder's evidence shows the `TypeError` before the fix.
- One gap remains: if `checks.md` is deleted between `_task` and the hash on the next line, the crash can still happen. Only a hand-run command can hit that window, and the worst outcome is a traceback. It is not a security issue, so I'm not raising it.

**The nit from round 1 is done.** `read_only_command()` (landing.py:846) now refuses three kinds of grep option that follow symlinks:
- the short options `-R`, `-S` and `-O`, alone or bundled (`-rnS`);
- the long option `--dereference-recursive`, written in full;
- plain `-r` still passes. That is safe because GNU `-r` follows only the symlinks named on the command line, BSD `-r` follows none by default, and `_path_refusal` already checks every path on the command line.

A false positive, such as `-eRS` where `RS` is the pattern, is refused. That is the safe direction.

**One small gap is left.** GNU grep accepts a shortened long option as long as it is unambiguous. So `--dereference`, or even `--der`, means the same as `--dereference-recursive` and gets past the exact-match check. Exploiting it would need a changed acceptance check that the approver also judged harmless, and it could only read files outside the checkout into the check's output. That makes it Low.
- NIT: plugins/factory/scripts/landing.py:876: GNU grep accepts unambiguous long-option prefixes, so `--der`/`--dereference` passes the exact `GREP_FOLLOWS_LONG` match and still follows symlinks while recursing; refuse any `--` word that is a prefix of `--dereference-recursive` (length ≥ 3), or refuse every grep long option not on a short allow-list {robustness S med}

**Trust boundaries, rechecked for this rework.** The untrusted input here is a `checks.md` edited after the person's yes, which the train runs unattended only if it clears. The rework only makes the read-only list stricter and turns a crash into a refusal. Neither change opens a new path to run something. The STRIDE effects in the reworked code:
- **Tampering and elevation of privilege:** these still go through both the list and the approver's `CHECKS: HARMLESS`, which needs the hash to match. Nothing here loosened that.
- **Information disclosure:** this is the grep symlink path, now covered except for the shortened option above.

**What I checked and ran:**
- Read the round-2 diff of `landing.py`, the `factory.py` lines 4410–4440, and the builder's round-2 report.
- Read the gate record `build/round-2.gate.md`: PASS, exit 0. The builder's report gives 3386 passed and 29 skipped.
- Ran `uv run --group dev pytest -q tests/test_train.py -k "read_only or land_checks_refuses"`: 51 passed.
