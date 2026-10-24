# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## O3 names the gates per tier and one more

The product doc's outcome line, rewritten as approved at spec; only reverting it could fail this.

```sh
grep -Fq 'Each change stops its person at the gates its tier passes and at most one' .sdlc/PRODUCT.md &&
  ! grep -Fq 'one at spec and one at ship' .sdlc/PRODUCT.md
```

## M2 tracks 007 by its number, and the direction doc still parses

A quoted title would read as a seed and vanish at the next retrospective. Parsed here with the
script's own `direction_items()` from this checkout's file: `sdlc.py retro` reads the main
checkout's, which holds the old line until this change lands.

```sh
uv run --quiet --group dev python -c '
import importlib.util
spec = importlib.util.spec_from_file_location("sdlc", "scripts/sdlc.py")
sdlc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdlc)
d = sdlc.direction_items(open(".sdlc/DIRECTION.md", encoding="utf-8").read())
m2 = next(i for i in d["items"] if i["id"] == "M2")
assert m2["groups"] == {"changes": ["007"], "seeds": ["Ship does its own landing edits"]}, m2["groups"]
assert d["problems"] == [], d["problems"]
'
```

## Nothing reads target_stops but the retired-keys table

```sh
test "$(grep -c target_stops scripts/sdlc.py)" = 1 && ! grep -q target_stops scripts/metrics.py
```
