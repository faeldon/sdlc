VERDICT: PASS

## Notes

This change has no Critical, High or Medium findings. It is mostly renames: `sdlc.py check` becomes `sdlc.py vet`, the factory's verifier becomes the arbiter, and many words in the docs change. It also makes two small additions to what the board shows. None of it opens a new way in, and no control is weakened.

**Trust boundaries the diff touches, checked with STRIDE**

- **Permission rules (elevation of privilege).** In `.claude/settings.json`, `READ_ONLY`/`ALLOW_RULES` in `scripts/sdlc.py` and the `allowed-tools` of each skill, the `check` rule becomes a `vet` rule for the same read-only command. Nothing that writes was added to `READ_ONLY`, and no rule got wider.
- **Removing `check` with no alias (denial of service, spoofing).** A host's CI that still runs `sdlc.py check --strict` now fails with argparse's error and a non-zero exit. It fails loudly; it never passes by mistake. `docs/REFERENCE.md:341` tells hosts about it.
- **The arbiter agent (elevation of privilege).** `plugins/factory/agents/arbiter.md` keeps the verifier's tools (`Read, Grep, Glob, Bash`) and still says it is read-only. `agent_name()` builds the `--agent` value only from the fixed `ROLES`/`TASK_ROLE` tables, so no outside text can choose an agent. `.sdlc/config.toml`'s `[review] sensitive` named no renamed path, so the change doesn't make its own review lighter.
- **`RENAMED` (tampering).** The old names are mapped to the new ones only where history is read: `runs/mended`, `costs.jsonl` roles, `*.sessions`, `STEP:` lines and `Sdlc-Role` trailers. In `mended()` and `land_mended()`, an old `verifier <round>` line becomes `arbiter <round>`, so "mended once a round" still holds across the rename. An old record can't be used to get a second mend.
- **Board gate line (information disclosure, cross-site scripting).** The card now shows the gate's command and one summary line from the end of its output. `gate_summary()` takes it from the tail that `cmd_gate()` and `factory.py` already write into the committed `build/gate.md` record.
  - **Escaping:** `h()` adds child text with `document.createTextNode`, so output that looks like HTML can't run as script.
  - **What is shown:** the command comes from the base branch's `[commands] check` setting. The board serves only `127.0.0.1`.

**Info**

- Despite its docstring, the "masked" tail in `gate_summary()` (`scripts/sdlc.py:3361`) is only path-placeholdered by `factory_records.placeholders()`; nothing redacts secrets. If a host's gate prints a secret on its last runner-count or failing line, the board card shows that line. It is already in the committed gate record, and the page is served only to `127.0.0.1`, so nothing new is exposed. A host whose test output can hold secrets should mask them in its own `[commands] check`.
- The new tail parsing in `read_gate_attempts()` and `read_gate_file()` only reads lines indented by four spaces after the heading. Gate output can't forge a record line such as `Verdict:`, so the protection from indenting the output still holds.
- `- NIT: scripts/sdlc.py:3361: the docstring says the tail is "already masked", but `placeholders()` only swaps checkout paths; say "path-placeholdered" so no reader assumes secrets are redacted {docs S med}`

**Done well**

- The old step names are mapped once, in `RENAMED`, with a copy pinned by tests. The `verified.md` record, `[commands] check` and `check.sh` keep their names, so nothing in history is read differently.
- Removing `check` with no alias makes old callers fail loudly rather than quietly.

**What I checked:** `intent.md`, `decisions.md`, the gate record `build/round-1.gate.md` (PASS, `./check.sh`, exit 0), and the diffs of `scripts/sdlc.py`, `scripts/board.py`, `scripts/board.html`, `scripts/factory_records.py`, `scripts/retro.py`, `plugins/factory/scripts/factory.py`, `landing.py`, `run_state.py`, `.claude/settings.json`, `skills/setup/`, and the arbiter and approver agents. I also read `.sdlc/config.toml`'s risk paths and searched with `git grep` for callers of `sdlc.py check`; it is left only in the REFERENCE.md note on the rename and in the term test. I ran no tests; the gate's record covers them.
