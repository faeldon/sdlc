# Decisions

- [x] D1 (builder round 1, default): Should `plugins/factory/scripts/factory.py`'s `_free_port()` (the UI review's dev server) be fixed here or filed as its own seed? Options: this change; a seed of its own. Going ahead with a seed of its own, which I haven't filed: that server is an outside command given `{port}`, so it can't bind 0 itself. Fixing it needs a different design (retry, or let the command report its port), and it's outside this intent's Affected files. → decided: a seed of its own, filed as 2026-11-17-19
