---
id: 164
slug: prompts-in-files
kind: plan
created: 2026-11-18
updated: 2026-11-19
---

# 164 — The factory's agent prompts live in files, not code · plan

> Written after reading `factory.py`'s `_task`, `_task_prompt`, `_land_task`, `check_line`,
> `weigh_text`, `_land_diff`, the mend and recheck constants, and the tests that read a prompt.

## Files to change

- `plugins/factory/prompts/*.md` (new): `common.md` (`head`, `check`, `land-diff`, `weigh`,
  `weigh-bare`) and one file per task: `spec`, `build`, `fix`, `review`, `verify`, `rework`,
  `approve`, `decided`, `mend`, `resolve`, `train-resolve`, `land-fix`, `land-review`,
  `land-verify`. Each a `# <name>` title, a `>` note, then `## <part>` sections, one line each.
- `plugins/factory/scripts/factory.py`: add `PROMPTS_DIR` (`FACTORY_ROOT / "prompts"`, moved up
  beside the other paths), `PROMPT_PARTS` (file → part → placeholders), `TASK_PROMPTS` (task →
  the files it reads), `_prompt_file()` (read, split, validate: a refusal string or the parts),
  `prompt_refusal()` and `prompt_part(name, key, **values)` (`string.Template.substitute`).
  `_task()` validates the task's files first. Every f-string body in `_task_prompt`, `_land_task`,
  `check_line`, `weigh_text` and `_land_diff` becomes a `prompt_part()` call with the same joiners;
  `MEND`, `VERDICT_MEND`, `DECISION_MEND`, `VERIFY_MEND` and `RECHECK` are removed. `RECONSIDER`
  stays (filled as `${reconsider}`); every refusal string stays in code. Reused unchanged:
  `asked_changes()`, `reconsider_section()`, `read_ledger()`, `read_revision()`,
  `read_restart_words()`, `named_nits()`, `landing.train_names()`.
- `tests/test_prompts.py` (new): the golden cases (R2, R3), R4–R9, R11, and the no-prose scan (R1).
- `tests/prompts/*.txt` (new): the recorded copies, written by the unchanged script.
- `tests/test_factory.py`: `factory.RECHECK` → `factory.prompt_part("spec", "recheck")` (R10),
  the only edit.
- `plugins/factory/README.md`: where the prompts live, read only from the plugin, `${name}` and
  `$$` (R11).
- `landing.py` is not touched: `_land_task` lives in `factory.py`.

As built: `prompt_part(name, key, /, **values)` takes the file and part positionally, since
`train-resolve`'s `change` part has a `${name}` placeholder. `prompt_refusal()` checks the task's
own files before `common.md`, so a broken task file is named first. `PROMPTS_DIR` sits beside
`FACTORY_ROOT`. The R5 test also covers a missing folder, and `test_every_recorded_copy_is_a_case`
keeps the recordings and the cases in step.

Deliberately left in code, as data rather than prose: the `'none'`/`'nothing'` fill-ins of an
empty list, `"the base branch"` as `base`'s fallback (also the refusals' noun), and `cmd_agent`'s
screenshot suffix (the spec's "ask first").

## Work order

1. **Record.** Write `tests/test_prompts.py`'s cases against the unchanged script and record
   `tests/prompts/*.txt` (`SDLC_RECORD_PROMPTS=1`). Each case calls `_task()`/`_land_task()` on a
   change folder under `tmp_path` with a crafted `state`, the git and train boundaries
   monkeypatched to fixed values (`_base`, `_changed_paths`, `_irreversible`, `_conflicted`,
   `_git`, `read_train`, `current_branch`, `load_config`, `named_nits`, `read_ledger`,
   `landing.train_names`, `landing.land_verdict`, `landing.train_live`), so the commit ids are
   fixed and only the root and `FACTORY_SCRIPT` need a mark. The golden test passes on the old
   script. Stop point: tests only, green.
2. **Mechanism.** `PROMPTS_DIR`, `PROMPT_PARTS`, `_prompt_file()`, `prompt_part()`, the
   validation in `_task()`, with `common.md`; `check_line`, `weigh_text`, `_land_diff` moved. R5/
   R7/R8 tests red first, then green; golden cases stay green.
3. **Build loop tasks**, one file at a time (`spec`, `build`, `fix`, `review`, `verify`,
   `rework`, `approve`, `decided`, `mend`), golden cases green after each.
4. **Landing tasks** (`resolve`, `train-resolve`, `land-fix`, `land-review`, `land-verify`,
   `land-mend`), golden cases green.
5. **Remove the constants**, the R1 scan and R4 coverage test green; `test_factory.py`'s recheck
   line; README and its test.
6. **Cross-check (R3)** against the base branch's `scripts/` copy.

## Tests

- R1: `test_no_prompt_prose_in_the_script`.
- R2: `test_every_prompt_matches_its_recorded_copy`, one parametrised case per row of the spec's
  table.
- R3: the same test, `SDLC_FACTORY_UNDER_TEST` pointing at the base branch's script copy.
- R4: `test_every_prompt_part_is_rendered` (records `prompt_part()` calls across every case).
- R5: `test_a_prompt_file_that_doesnt_match_is_refused` (four shapes, plus a missing file),
  through `cmd_agent` with the fake `claude`.
- R6: `test_filled_text_is_never_read_as_a_placeholder`.
- R7: `test_a_crlf_prompt_file_gives_the_same_prompt` (`portable`).
- R8: `test_prompts_are_read_from_the_plugin_alone`.
- R9: `test_prompt_files_hold_no_path`.
- R10: the existing wording tests in `test_factory.py`, `test_land.py`, `test_train.py`.
- R11: `test_the_factory_readme_names_the_prompts_folder`.

## Rollback

`git revert` undoes all of it: the script reads the files at run time, writes nothing new, and
nothing outside the repo changes. A host's cached `sdlc-factory` is the version it installed until
it updates.
