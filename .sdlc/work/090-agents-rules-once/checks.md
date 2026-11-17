# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## AGENTS.md is markedly shorter than its 517 lines

Only putting the feature-by-feature Architecture section back would take it past 320 lines. The
cap was 300 when the map was drawn; the rules 091, 093 and 094 added to `main` while it was built
came to a few lines more, so it leaves room for those, not for the old section.

```sh
test "$(wc -l < AGENTS.md)" -lt 320
```

## Every function AGENTS.md points at exists

The map's pointers replace the text it cut, so each `name()` it names must be defined in the
plugin's scripts (`as_posix()` and `open()`, named by the Windows invariant, are Python's own). A
rename that leaves a pointer behind fails it as surely as a revert would.

```sh
grep -o '`[A-Za-z_][A-Za-z0-9_]*()`' AGENTS.md | tr -d '`()' | sort -u | grep -vxE 'as_posix|open' | while read -r f; do grep -qE "def $f\(" scripts/*.py scripts/trackers/*.py plugins/factory/scripts/*.py || { echo "AGENTS.md names $f(), defined nowhere"; exit 1; }; done
```

## Ship's context pass asks whether a line is already said elsewhere

Only removing the third question from step 4 would fail it.

```sh
grep -q 'already said in another context doc, or in the docstring of the code it is about' skills/ship/SKILL.md && grep -q 'propose a pointer there, never the line' skills/ship/SKILL.md
```
