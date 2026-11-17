VERDICT: PASS

Every requirement has code, and a test that would fail without it, except two small gaps in R11 and R12 below.

## Notes

**Optional findings and nits**
- **Optional, R11:** the spec says "in both fixtures the run's `HOME` has no factory enabled, so both cases also check R4's wording." The new `intent-product` regex accepts either question form, and `asks-the-question` ends at `serving`, so no grader checks the endings. The existing `intent` case wasn't changed to check them either. The skills' test pins the wording, but a paid run wouldn't show a regression in R4's endings. Fix: end the regex with `then start plan mode\? \(yes / yes, without plan mode`, or accept this as an unmet part of R11.
- **Optional, R3:** `factory_enabled` uses `named[0] is True`. If a settings file lists two `sdlc-factory@` keys, for example from two marketplaces, the first one decides, even when a later one is `true`. That's harmless, but `any(v is True …)` would be more forgiving.
- **Nit:** in Step 0 of `skills/intent/SKILL.md`, the added sentence puts `Note git.base too:` on the same long line as the factory note. It reads fine, but the line is now over-long.
- **Unconfirmed, R12:** I checked the docs diffs only by their stat (README +5, REFERENCE +17, factory README +6), not their wording. `sdlc.py context` and ship's shown edits will settle it.

**Done well**
- `factory_enabled` is a small pure reader: files only, no subprocess, and any bad file or non-dict `enabledPlugins` is skipped. The `AttributeError` for non-object JSON is caught too.
- Step 4 keeps today's question word for word for hosts without the factory, and Step 5's split is a single sentence. The tests assert on the actual wording, including that `allowed-tools` holds no rule naming `factory`.
- The fixture's `settings.json` doesn't enable the factory, which matches the spec.

**Ran:** `./check.sh`. Ruff, the format check, pytest and `claude plugin validate --strict` all passed. The only output was the factory plugin's missing-icon warning, which doesn't affect the result. I didn't run the paid `run-cases`, and I didn't run `sdlc.py drift` on its own.
