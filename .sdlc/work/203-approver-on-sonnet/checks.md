# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The approver runs on sonnet at both depths, with the trial's comment

Only a revert of `.sdlc/factory.toml`'s `[models]` entry or its comment could fail it. The check
reads this checkout's file through `factory.py`'s own `_models()` and `model_for()`, since
`factory.py config` reads the base branch's copy, which holds the setting only once it lands.

```sh
uv run --quiet python -I - <<'PY'
import importlib.util, tomllib
from pathlib import Path
spec = importlib.util.spec_from_file_location("factory", "plugins/factory/scripts/factory.py")
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
text = Path(".sdlc/factory.toml").read_text(encoding="utf-8")
models, warnings = f._models(tomllib.loads(text).get("models", {}))
assert not warnings, warnings
for tier in (1, 2):
    for level in ("light", "full"):
        got = f.model_for("approver", {"models": models}, tier, level)
        assert got == "sonnet", (tier, level, got)
for word in ("2026-11-20", "escaped", "ESCALATE"):
    assert word in text, f"the trial's comment lacks {word!r}"
PY
```
