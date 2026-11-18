I added `scripts/closing.py` and `plugins/factory/scripts/landing.py` to `[review] sensitive` in `.sdlc/config.toml`. I didn't write a test for this: it's two config lines, so an acceptance check in `checks.md` covers it instead. The work is left uncommitted for `/sdlc:ship`.

**What changed:**
- **The list:** both paths are in, quoted exactly as 153's spec greps for them (its R10 and its Verification step).
- **The comment above the list** now also names close, the push, the main lock and the factory's landing, "where a mistake costs a host's work or history". I wrapped it to stay within 100 characters a line.
- **No `plan.md`:** this is a Tier 1 change touching one file.

**Checked:**
- **The acceptance check** looks inside the `[review]` table for both quoted paths. It fails against the file as committed (`HEAD`), passes on the edited file, and `sdlc.py accept 158` runs it as passing without changing the tree.
- **Reading the list:** `sdlc.py config` returns a `review.sensitive` list that ends with the two new paths.
- **No review depth moves:** `depth()` reads the list from the base branch and only raises the depth when a change's diff touches a listed path. Neither file exists yet, and no open change branch (153 or 158) touches either path, so every open change keeps the depth it has. This change doesn't touch a listed path either.
- **Audit and tests:** `sdlc.py check --strict` reports 0 problems. No test reads this repo's own `[review]` list, since every test builds its own config. I ran `tests/test_risk.py` and `tests/test_config_resolution.py` by name: 47 passed. I didn't run the whole suite; the gate does that.

**Shown only after landing:** the outcome "`git show main:.sdlc/config.toml | grep` finds both lines" can only be true once this is on `main`. `checks.md` proves the same lines on the change's own tree, and 153's Verification step greps `main` before its build starts.

Nothing is left in `notes.md`, and I raised no decisions.

## Evidence

$ git show HEAD:.sdlc/config.toml | sed -n '/^\[review\]/,/^\]/p' | grep -qF '"scripts/closing.py"'
exit: 1

$ sh -c "<the checks.md sh block>"
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 158
"name": "The deep review lists closing.py and landing.py", "exit": 0, "passed": true, "left": []
"passed": true, "problems": []
exit: 0

$ uv run --quiet --script scripts/sdlc.py config | python3 -c 'import json,sys; print(json.load(sys.stdin)["review"]["sensitive"])'
['.claude-plugin/', '.claude/settings.json', 'scripts/trackers/', 'check.sh', '.github/workflows/', 'scripts/closing.py', 'plugins/factory/scripts/landing.py']
exit: 0

$ for b in <open change branches>; do git diff --name-only $(git merge-base main $b) $b -- scripts/closing.py plugins/factory/scripts/landing.py | wc -l; done
153-risky-code-in-its-own-modules 0
158-list-risky-modules 0
exit: 0

$ ls scripts/closing.py plugins/factory/scripts/landing.py
ls: plugins/factory/scripts/landing.py: No such file or directory
ls: scripts/closing.py: No such file or directory
exit: 1

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
    none ✅
exit: 0

$ uv run --group dev pytest -q tests/test_risk.py tests/test_config_resolution.py
47 passed in 1.97s
exit: 0
