I've finished the checks and am writing up the security review now.

VERDICT: PASS

The change opens no Critical or High hole. The one security fix it makes, refusing every prefix of `--dereference-recursive` on grep, works on GNU grep and on macOS's BSD grep, and it only makes the read-only list stricter, as the spec says it must.

- PREEXISTING: plugins/factory/scripts/landing.py:795: the grep refusals cover GNU grep and BSD grep only. If a host's `grep` on `PATH` is ugrep, `grep -r --dereference-files keep .` is allowed and follows links to files outside the checkout. This change didn't add or touch that gap, but it is in the same function. Fix: refuse `--dereference-files` and its prefixes too, or check every word against a list of such long options.

## Notes

**Trust boundaries the diff touches**
1. **Agent replies to `decisions.md`** (`question_lines()`, `raised_decisions()`, `cmd_decisions()`). Agent output is untrusted and ends up in the ledger the person decides from.
   - The new folding joins indented lines onto the ledger line with spaces, so no newline gets in and an agent can't add a fake `- [x] … → decided:` line of its own.
   - The new matching by options only merges raises from the same source, which is one agent's report for one round, and of the same kind. One agent therefore can't hide another's decision, or a blocking one behind a default. The worst case is an agent merging two of its own questions by giving them identical options, and that is in its own power already.
   - Ledgers written before this change still match on their first line alone (`alone`/`first`), and the test proves a rerun writes nothing.
   - Info: within one source, a re-raised `[blocking]` question reworded with identical options now matches the existing line. If the person has already answered it, the reworded one counts as answered too. That is the point of the change (D1 records the choice), so it is not a finding.
2. **The unattended train's read-only list** (`read_only_command()`). The rule `len(name) >= 5 and GREP_FOLLOWS_LONG.startswith(name)` refuses `--der` and anything longer, and still refuses `=value`.
   - On BSD grep (checked: `/usr/bin/grep`), `--de` fails as "ambiguous" and `--der` as "unrecognized". GNU grep's `--de` is ambiguous between `--devices` and `--dereference-recursive`, so leaving it allowed is safe: grep exits without searching.
   - BSD grep has no long option that follows links, and `-S`, `-O` and `-R` are still refused as short flags.
3. **The skill description and the docstrings** are text only; nothing reads them for security.

**What I checked and ran**
- Read `intent.md`, `decisions.md`, the gate record (`round-1.gate.md`: PASS, `./check.sh` exit 0) and the full diff. There is no `spec.md` because this is a Tier 1 change.
- Ran `pytest tests/test_train.py -k read_only`: 55 passed.
- Ran BSD grep with `--der` and `--de` to confirm both fail before any search.
- The diff adds no dependency, no secret, no push or other destructive step, and no `subprocess`.

**What is done well**
- The new tests cover both directions: commands that must still pass (`--directories=skip`, `--de`) and commands that must be refused (`--der`, `--dereference`, `--dereference-recursive=x`).
- The `read_only_command()` docstring now says the path rule can't see a link a program meets while walking the tree itself.

- NIT: plugins/factory/scripts/landing.py:883: the threshold `len(name) >= 5` counts the leading `--`, while the comment above `GREP_FOLLOWS_LONG` says "three or more characters after its `--`". Writing it as `len(name) - 2 >= 3`, or naming the constant, would make the two read the same. {style S low}
