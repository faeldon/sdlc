VERDICT: PASS

The background JSON run finished, and it confirms what the report showed. I had said I couldn't see the JSON output, and now I have.

- **Coverage (R4, R6):**
  - Lead time is `{measured: 3, of: 14, greyed: True}` with `missing_because` of `closed before lead time was recorded` 8 and `no opened: line` 3. These sum to 11, which is `of - measured`.
  - Escapes, the person's minutes and spend are each 14 of 14 and not greyed.
- **Underneath (R8):**
  - `changed` is `{claude: None, models: False, plugin: None}`.
  - `claude` and `plugin` are null because no `Sdlc-Runtime` line exists yet in this history.
  - `models` is unchanged, `{opus: 13, sonnet: 13}` against `{opus: 7, sonnet: 7}`.
  - `recorded` is 0 and `unrecorded` is 14, and the previous window's `unrecorded` is 86.
- **Factory count (R10):** `process.window` holds `factory: 13` and `mode_unknown: 0`.

## Evidence
$ uv run --quiet --script scripts/sdlc.py retro | python3 -c "…" (finished in the background, run earlier)
{'measured': 3, 'of': 14, 'greyed': True} {'closed before lead time was recorded': 8, 'no opened: line': 3}
{'measured': 14, 'of': 14, 'greyed': False}
{'measured': 14, 'of': 14, 'greyed': False} {'measured': 14, 'of': 14, 'greyed': False}
{'window': {'claude': {}, 'models': {'opus': 13, 'sonnet': 13}, 'plugin': {}, 'recorded': 0, 'unrecorded': 14}, 'previous': {…, 'unrecorded': 86}, 'changed': {'claude': None, 'models': False, 'plugin': None}}
{'since': '2026-11-18', 'today': '2026-11-19', 'closed': 14, …, 'factory': 13, 'mode_unknown': 0}
exit: 0

The commands I ran earlier are listed in my previous reply's Evidence section.
