# 096 — notes

- [x] Deviation from R4: `groups` doesn't refuse a slug a closed or dropped change used. `new`
  doesn't refuse one (`_used()` reads only the open folders), so refusing it in `groups` would
  stop a batch `new` would create. `groups` refuses exactly what `new` would, plus the batch's own
  checks.
- [x] `groups` joined `READ_ONLY`, so its allow rule went into `.claude/settings.json` and the
  `set-up` and `product` eval fixtures' settings, which `readiness` reads as complete only with
  every read-only rule (`test_the_set_up_fixture_is_complete`).
