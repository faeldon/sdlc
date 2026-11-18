VERDICT: PASS

The change adds both paths to `[review] sensitive`, and `sdlc.py config` reads them back. I did not run `factory.py verdicts`, so the "same depth as before" outcome is unconfirmed. It is inferred from neither path existing yet.

## Notes
- **The deep review lists closing.py and landing.py** (`checks.md`): I expect this to pass. The `[review]` block in `.sdlc/config.toml` contains both `"scripts/closing.py"` and `"plugins/factory/scripts/landing.py"` in quoted form. My grep count of the two lines was 2.
- The comment above the list now says why. It names close, the push, the main lock and the landing as where a mistake costs a host's work or history.
- Neither path exists on this branch yet, so no current change's depth moves.
- The gate record `build/round-1.gate.md` reads `GATE: PASS`.

## Evidence
$ git diff
(the diff shows only `.sdlc/config.toml`: the comment extended, and the two entries added at the end of `sensitive`)
exit: 0

$ uv run --quiet --script scripts/sdlc.py config | grep -n -A12 -i sensitive
```
157:    "sensitive": [
...
163:      "scripts/closing.py",
164:      "plugins/factory/scripts/landing.py"
    ],
```
exit: 0

$ sed -n '/^\[review\]/,/^\]/p' .sdlc/config.toml | grep -cF -e '"scripts/closing.py"' -e '"plugins/factory/scripts/landing.py"'
2
exit: 0

$ head -5 .sdlc/work/158-list-risky-modules/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0
