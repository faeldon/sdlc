VERDICT: PASS

## Notes

This change moves code without changing what it does. Every copy of the factory-record parsing now lives in one module, `scripts/factory_records.py`. I found no Critical or High issue. Nothing in the diff opens a new way for untrusted data to get in, and none of it can reach anything it couldn't reach before.

**Where untrusted data enters, and what I checked:**
- **The files a factory run leaves in a change folder** (decision, ledger, rounds, gate records, `runs/*.jsonl`): agents write these, so I treated them as untrusted. The new module only parses them, with regexes and `json.loads`. Each parsed row is type-checked before use (`isinstance` on dicts, ints, floats and strings, with `bool` excluded), and a bad line is skipped. Nothing it reads ever reaches a shell, `eval` or a template. It doesn't import `subprocess`, `os.system` or anything from `sdlc.py`.
- **Close's measure step, which reads git history:** `_branch_files()` keeps git in `closing.py` and runs it through `sdlc._git` with an argument list, never a shell. The `show`/`listing` callables build `branch:folder/rel` from names the module fixes (`runs`, `reviews`, `build`, `decision.md`, `costs.jsonl`). No path from a record ever goes back into git.
  - `session_roles` now uses a recursive `ls-tree -r` listing where the old code used a non-recursive one. The `len(parts) != 2` filter keeps the old meaning: only direct children of `runs/` are read.
- **Loading the module:** `_load_factory_records()` loads it from `PLUGIN_DIR / "scripts"`, the plugin's own folder, the same way `metrics.py` is loaded. A host repo can't plant a module there.
- **The board:** the diff adds no `innerHTML`, and doesn't touch the bind address or any write path. The board still serves only `127.0.0.1` and still builds its page with `textContent`.
- **Secrets and the path scrubber:** `placeholders()`, `_terms()` and `DEFUSE` moved over unchanged, so committed records still have the clone, home and temp paths, the login name and local terms masked. `_terms()` still skips a line that won't compile as a regex.
- **Dependencies:** none added. The module uses only the standard library (`getpass`, `json`, `re`, `tempfile`, `time`, `pathlib`).
- **Destructive operations:** none added. The module writes nothing.

**Low/Info (not nits, nothing to fix):** `_terms()` compiles regexes from the host's own gitignored `.sdlc/terms.local`, so a pathological pattern could make the scrubber slow. That file belongs to the person and was read the same way before this change, so it isn't new exposure.

**What's done well:** git reads come in as callables, so the module stays pure and can be tested without git. Moving everything into one module also shrinks the code that handles agent-written files to a single file, and the new test in `tests/test_modules.py` stops anything else in core from opening those files its own way.

**Gate:** the record at `build/round-1.gate.md` is `GATE: PASS`, with `./check.sh` exiting 0 and the tree unchanged. I didn't run the gate myself. I read the module's imports and every file read in it, the full `closing.py` diff and the module loader in `sdlc.py`, and scanned the `board.py` and `sdlc.py` diffs for HTML sinks, binds, writes and subprocess calls.
