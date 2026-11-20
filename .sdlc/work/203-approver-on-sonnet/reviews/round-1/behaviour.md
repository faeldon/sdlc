VERDICT: PASS

`.sdlc/factory.toml` now sets `approver = "sonnet"` under `[models]`. It has a comment naming the 2026-11-20 retrospective and what the next one reads: READY changes that escaped, and ESCALATEs the person found empty. No plugin defaults were touched.

There is one gap against the spec's outcome. It says `factory.py config` shows `approver` on sonnet in `models_at`. In this worktree it can't, because `config` reads `[models]` from the base branch's file, so it prints `"models": {}` and a warning saying so. I used `factory.py`'s own `_models()` and `model_for()` on this checkout's file instead. They return sonnet for the approver at tier 1 and 2, light and full, with no warnings. The `config` output should be re-read after landing.

## Notes
- The one check in `checks.md` (the approver runs on sonnet at both depths, with the trial's comment) I expect to pass. It reads this checkout's file through `_models()` and `model_for()`, which is the same path I ran. The words "2026-11-20", "escaped" and "ESCALATE" are all in the comment.
- I did not run the suite. The gate record `build/round-1.gate.md` ends in "Validation passed".

## Evidence
$ git status --short; git diff HEAD -- .sdlc/factory.toml
```
 M .sdlc/factory.toml
?? .sdlc/work/203-approver-on-sonnet/
(diff adds the [models] section with approver = "sonnet" and the trial comment)
```
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py config | grep -i -B2 -A8 models
```
  "models": {},
  "warnings": [
    "models is read from the base branch's .sdlc/factory.toml: this checkout's [models] applies once it lands"
  ]
```
exit: 0

$ uv run --quiet python -I -c "<_models() and model_for() on this checkout's .sdlc/factory.toml>"
```
{'approver': 'sonnet'} []
['sonnet', 'sonnet', 'sonnet', 'sonnet']
```
exit: 0

$ tail -3 .sdlc/work/203-approver-on-sonnet/build/round-1.gate.md
```
    The directory also runs a safety scan and a policy review that this command does not.
    
    ✔ Validation passed
```
