# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## Retro prints what the script before the move printed

The base's plugin files, unpacked from git into a temporary folder and run by `uv run --script`
there, and this checkout's print the same `retro --report`, byte for byte, and the same `retro` and
`retro --metrics` JSON over the same repo but for `prose.sdlc_py_lines`, the one figure the move
exists to change: the move changed no other output, and `retro.py` loads from a copy of the
plugin's folder.

```sh
t=$(mktemp -d) && git archive "$(git merge-base HEAD main)" scripts templates guide defaults skills agents .claude-plugin | tar -x -C "$t" && uv run --quiet --script "$t/scripts/sdlc.py" retro --report > "$t/old" && uv run --quiet --script scripts/sdlc.py retro --report | cmp - "$t/old" && for a in "" --metrics; do uv run --quiet --script "$t/scripts/sdlc.py" retro $a | jq -S 'del(.prose.sdlc_py_lines)' > "$t/old" && uv run --quiet --script scripts/sdlc.py retro $a | jq -S 'del(.prose.sdlc_py_lines)' | cmp - "$t/old" || exit 1; done
```
