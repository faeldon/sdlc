
Open questions resolved:
- **Which of the 31 nits has the code already moved past?** Only 2026-11-21-20. `_SCP_RE` already
  matches a dotless host, and `tests/test_upstream.py:447` pins it (nit 2026-11-21-21). The other
  30 still apply as written, and each was checked at the file and line the nit names.
- **2026-11-21-8: check the factory row, or retire?** Retire it as `wontfix`. Both plugins install
  from the one `sdlc` marketplace (`UPDATE_MARKETPLACE`; `cmd_update`'s steps are
  `sdlc-factory@sdlc`). So when sdlc is read from a folder, the factory is too, and `_stale()`
  skips `local_source` installs anyway.
- **2026-11-21-30: refuse the flags, or document that they're ignored?** Refuse them. That matches
  the refusal `cli_preflight()` already gives without `--question`, and ship's skill runs
  `--preview` with no flags.

Left for you:
- None blocking. The change is held for you anyway, because R2 edits `scripts/closing.py`
  (`[review] sensitive`). The decision to check there: narrowing `fix_trailers()` and
  `origin_trailer()` to `(OSError, ValueError)` means a coding error in either now stops a close
  before its `Close` commit (a rerun resumes) instead of quietly dropping the trailer. If you would
  rather close never stop on these, keep `except Exception` and retire 2026-11-21-5 as `wontfix`.
