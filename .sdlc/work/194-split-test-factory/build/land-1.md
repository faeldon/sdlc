`tests/test_factory.py` is resolved: it stays deleted, and 193's three new tests now live in `tests/test_factory_decisions.py`. The conflict was modify/delete. 194's split removed the file while 193 added tests to it.

- **From 194:** I took the split as built. The whole file is gone and its tests stay in the module files.
- **From 193:** I added its `REWORDED`, `REWORDED_TEXT` and `REWORDED_SUBS` constants and its three tests to `tests/test_factory_decisions.py`. They sit just before `test_options_fill_a_bare_line_once`, where 193 had them in the old file. The tests are:
  - `test_a_question_in_sub_bullets_keeps_every_line_and_its_options`
  - `test_a_ledger_holding_a_question_s_first_line_is_matched`
  - `test_a_decision_reraised_with_the_same_alternatives_lands_once`

  The block is unchanged from 193, and the helpers it uses (`_change`, `_build_report`, `_run`, `PAGING` and the rest) were already available in that file.
- **Not kept:** nothing.
- **Noticed, left alone:**
  - 193's changes to `tests/test_skills.py` and `tests/test_train.py` did not conflict.
  - `_ledger_text` is not in that file's imports, so it must be defined locally there. I did not check this separately; the 82 passing tests cover it.

## Evidence

$ git show e3726c22:tests/test_factory.py | sed -n 812,879p > /tmp/blk.txt; python3 (inserted the block before test_options_fill_a_bare_line_once); rm tests/test_factory.py
exit: 0

$ uv run --group dev ruff format --check tests/test_factory_decisions.py
1 file already formatted
exit: 0

$ uv run --group dev pytest -q tests/test_factory_decisions.py
82 passed in 38.57s
exit: 0
