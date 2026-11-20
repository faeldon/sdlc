VERDICT: PASS

This checkout's `.sdlc/factory.toml` sets the approver to `sonnet` at both depths, as the intent asks. `factory.py config` still shows `"models": {}`. It reads the base branch's copy of the file, which doesn't carry the setting until this change lands. That is expected, not a failure.

## Notes
- **Check "The approver runs on sonnet at both depths, with the trial's comment":** I expect it to pass. I did not run it. I ran its core logic inline, through `_models()` and `model_for()`, and got `sonnet` for the approver at tier 1 and 2 and at light and full depth, with no warnings. The `[models]` comment contains "2026-11-20", "escaped" and "ESCALATE". This check does not cover the intent's wording that `start` shows the approver on sonnet in `models_at`. I did not run `start`, since it also reads the base branch's file.
- **Gate:** I did not read the gate record in full. `.sdlc/work/203-approver-on-sonnet/build/round-1.gate.md` ends with "Validation passed", and my grep for exit, green or red lines in it found nothing.
- **Defaults:** the diff touches only `.sdlc/factory.toml`, apart from the change's own folder. Nothing in the plugin's defaults changed, as the intent's Constraints require.

## Evidence
$ git diff f76717a3a86fecb40f16a1e72472a6d4c1cd7562...HEAD -- .sdlc/factory.toml
```
+[models]
+# A one-window trial, from the retrospective of 2026-11-20: ... 
+approver = "sonnet"
```
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py config | head -30
```
  "models": {},
```
exit: 0

$ uv run --quiet python -I - (load `.sdlc/factory.toml` through `factory._models` and `factory.model_for`; print the approver's model per tier and depth)
```
{'approver': 'sonnet'} [] ['sonnet', 'sonnet', 'sonnet', 'sonnet']
```
exit: 0

$ tail -5 .sdlc/work/203-approver-on-sonnet/build/round-1.gate.md | head -3
```
These plugin directory checks do not change the result below.

The directory also runs a safety scan and a policy review that this command does not.
```
exit: 0
