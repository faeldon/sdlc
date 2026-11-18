# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## Help and usage errors match the base

The move is checked once against the scripts as they were before it (R3, R4, R5): a later change
may rightly change a help line, so this is no test in the suite, and only a revert of the move to
something else could fail it now. It runs both copies of each script, writing only under a temp
dir, and prints any line that differs.

```sh
export SDLC_OWN_SCRIPT=off
tmp=$(mktemp -d)
git archive "$(git merge-base HEAD main)" scripts plugins/factory/scripts | tar -x -C "$tmp"
bad=0
same() {
  s=$1; shift
  uv run --quiet --script "$tmp/$s" "$@" >"$tmp/a" 2>&1; echo "exit $?" >>"$tmp/a"
  uv run --quiet --script "$s" "$@" >"$tmp/b" 2>&1; echo "exit $?" >>"$tmp/b"
  cmp -s "$tmp/a" "$tmp/b" || { echo "DIFF: $s $*"; diff "$tmp/a" "$tmp/b"; bad=1; }
}
for s in scripts/sdlc.py plugins/factory/scripts/factory.py; do
  same "$s" --help
  for c in $(uv run --quiet --script "$tmp/$s" --help | grep -o '{[^}]*}' | head -1 | tr -d '{}' | tr , ' '); do
    same "$s" "$c" --help
  done
done
same scripts/sdlc.py nosuch
same scripts/sdlc.py ship
same scripts/sdlc.py new x --tier 3
same scripts/sdlc.py resolve --continue --abort
same scripts/sdlc.py cases compare
same scripts/sdlc.py preflight 001 --nits
same scripts/sdlc.py run-cases
same plugins/factory/scripts/factory.py
same plugins/factory/scripts/factory.py nosuch
same plugins/factory/scripts/factory.py start 1
same plugins/factory/scripts/factory.py land 001
same plugins/factory/scripts/factory.py resolve 001
same plugins/factory/scripts/factory.py land-fix 001 --ask x --commit
rm -rf "$tmp"
exit $bad
```

## The loaded modules are not in the diff

The scripts register the modules' commands on their behalf (R8), so `closing.py`, `retro.py`,
`board.py` and `landing.py` stay out of this change; only an edit to one of them here could fail it.

```sh
test -z "$(git diff "$(git merge-base HEAD main)" --name-only -- scripts/closing.py scripts/retro.py scripts/board.py plugins/factory/scripts/landing.py)"
```
