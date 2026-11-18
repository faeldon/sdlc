
Resolved:
- **Placeholder syntax:** `string.Template` (`${name}`, `$$`). No current prompt text holds `$`. Python ≥ 3.11 (`requires-python` in `factory.py`) gives `get_identifiers()`/`is_valid()` for the refusal, and `substitute()` never re-reads filled values.
- **Where the files live:** `plugins/factory/prompts/`, beside `agents/`, located from the existing `FACTORY_ROOT`.
- **Host override:** none (R8). Agents stay predictable, the eval's scores stay tied to the plugin's text, and the reply shapes the script parses can't be broken by a host edit.
- **Conditionals:** the script keeps its `if`s and joiners. Each task's file holds named `## <part>` sections, and lists are computed in Python and filled as one value each. There are no fragment files and no logic in the files.
- **Whether `landing.py` assembles prompts:** it doesn't. `_land_task` is in `factory.py`, so `landing.py` needs no edit.

Left for the person:
- **The UI reviewers' screenshot suffix** (`cmd_agent`, "Screenshots: … Changed: …") is also prompt text, outside the functions the intent names.
  - Move it: put it in `review.md`/`land-review.md` as a `screenshots` part. That's one more R2 case, and every prompt then lives in a file.
  - Leave it: it stays in code, and this change stays within the intent's Affected list.
- **Add `plugins/factory/prompts/**` to `[review] sensitive`?** Every factory agent reads these files, so a wording edit would then get a full-depth review. That is a config edit on the base branch, separate from this change. Saying no means wording diffs get the normal review depth.
