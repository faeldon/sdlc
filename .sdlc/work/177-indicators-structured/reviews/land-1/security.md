VERDICT: PASS

## Notes

**Trust boundaries the change touches**

1. **The output of a host's `retro.indicators` commands.** The commands come from the host's own `.sdlc/config.toml`. Their stdout is now parsed by `indicators.host_rows()` and written into a committed report through `_indicators_text()`.
   - **Tampering and injection:** each row's `name` and `unit` must be a single line with no `\n` or `\r`, and their length is capped at `NAME_MAX` and `UNIT_MAX`. `cell()` escapes `\` and `|`, so a crafted name can't break the table or add a fake header that `report_rows()` would read back next time. Values must be finite non-boolean numbers, and they are written by `number()`, never as raw text. A command's raw output and stderr never reach the report when it fails, times out or is cut short. The command string is wrapped in a code span by `_code()`, and its fence is longer than any backtick run inside it. Any HTML in a name lands in committed Markdown, which GitHub sanitizes. Info only.
   - **Denial of service:** output is still capped at `EVIDENCE_LIMIT` (20,000 characters) and `EVIDENCE_TIMEOUT` (60s) by the unchanged `_evidence()`. I probed `host_rows()` directly:
     - An integer with 5,000 digits is rejected cleanly ("line 1 isn't a JSON object"), because Python raises `ValueError` and the code catches it.
     - Nesting about 9,980 deep inside an extra key parses without a `RecursionError`.
   - **Elevation of privilege:** none. `_evidence()` still runs each command with `sdlc._sh()`, with no `shell=True` added.
2. **The last retrospective's report, read back from git.** `_last_rows()` runs `git show <since sha>:<report_rel(date)>`. Both parts come from the repo's own `Retrospective` commit and the date-derived path, passed as an argv list, so nothing is injected. `report_rows()` only parses numbers from that text, and a malformed cell becomes `None`.
3. **The scope of command execution has widened.** `retro_report()` used to read history only. It now runs `retro.indicators`, so `sdlc.py retro --report` and `retro-commit` run host commands too. This is the same trust level as `sdlc.py retro`, which already ran them in the architecture pass, from the same config. `retro` and `retro-commit` are not in `READ_ONLY`, so `ALLOW_RULES` doesn't cover them and no model runs them unasked. The new docstring on `retro_report` says this honestly. `cmd_retro`'s own docstring still says "Writes nothing", which is true of the script but not necessarily of a host's command. That was already the case before this change.

**Medium:** none. **Low:** none.

- NIT: scripts/retro.py:2527: `cmd_retro`'s docstring says "Writes nothing, and reads nothing outside the repo", but with `--report` it now also runs the host's `retro.indicators`, so it could say so as `retro_report`'s docstring does {docs S low}

**Done well**
- Failed, timed-out and truncated output is never parsed as rows.
- Duplicate `(name, unit)` pairs are refused.
- An integer too large for a float is handled through `OverflowError` in `_finite()`.
- `.sdlc/function-heat.py` prints only function names and numbers through `json.dumps`.
- No new dependency was added.

**What I checked and ran**
- Read `intent.md`, the code diff (`scripts/indicators.py`, `scripts/retro.py`, `scripts/sdlc.py`, `.sdlc/function-heat.py`, the template and the skills) and `build/land-1.md`. The landing's conflict resolution only merged the `cost` and `indicators` parameters, which adds no security exposure.
- Checked `READ_ONLY` and `ALLOW_RULES` in `sdlc.py`, and every caller of `retro_report()`.
- Probed `host_rows()` with a 5,000-digit integer and with nesting 5,000 and 9,980 deep.
- There is no `build/land-1.gate.md` in the change folder, so I couldn't read this landing round's gate result. The resolver's evidence shows `tests/test_retro.py` passing (189) and `ruff check` clean. I didn't run the gate myself.
