# 148 — The factory's gate records redact the temp directory and the user's name

## Context

On 2026-11-18, the 140–143 landing train's first red tip quoted pytest's
`tmp_path = PosixPath('/private/var/folders/…/T/pytest-of-<username>/…')` in `land-1.gate.md`.
`_placeholders()` marks only the clone root (`<path-to-clone>`) and home (`<home>`), so the
username reached 141's and 143's commits, and `test_nothing_local` turned every later tip red for
the train's own records. The train was stopped. The fix marks the temp directory as `<tmp>`, and
the login name as `<user>` wherever it is a segment of a path that starts with a mark. Decided in
planning: the user's name is marked only inside a marked path, never in prose. Cleaning the
records already committed in 140, 141 and 143 is a one-off after 148 lands, outside this change.

## Changes

1. **`plugins/factory/scripts/factory.py`**
   - Beside `CLONE_MARK`/`HOME_MARK` (line ~262), add `TMP_MARK = "<tmp>"` and
     `USER_MARK = "<user>"`, extending the comment above them.
   - `_placeholders()` (line ~2688): add `(Path(tempfile.gettempdir()), TMP_MARK)` after home in
     the tuple. Fixed order: clone, clone, home, tmp. Home before tmp, so a home under the temp
     dir (as in the tests) reads `<home>`. A temp dir under home reads `<home>/…`, which leaks
     nothing. Then, for each match of `(<path-to-clone>|<home>|<tmp>)[^\s'"]*`, replace the login
     name where no letter or digit borders it (`(?<![A-Za-z0-9])name(?![A-Za-z0-9])`) with
     `USER_MARK`. The login name comes from `getpass.getuser()` in a small `_login()` helper that
     returns `None` on `OSError`/`KeyError`/`ImportError` (Windows with no env vars); nothing is
     marked then. Update the docstring. `import getpass, tempfile` at the top: both modules exist
     on every platform (`pwd` is imported inside `getpass`).
   - `is_read()` (line ~1397): also map `TMP_MARK` and `USER_MARK` to plain words, as it does the
     other two.
2. **`scripts/sdlc.py`**: the same in `_hand_placeholders()` (line ~2866), with its copies of the
   two marks beside `CLONE_MARK`/`HOME_MARK` (line ~2819). It is the pinned copy.
3. **`docs/REFERENCE.md:585`**: the sentence naming the marks adds the temp directory `<tmp>` and
   the user's name inside such a path `<user>`.
4. **Tests**
   - `tests/test_factory.py`, beside `test_the_gate_records_no_path_of_this_machine`: a new
     `test_the_gate_records_no_temp_path_or_user_name`. `monkeypatch.setattr(tempfile, "tempdir",
     str(tmp_path / "T"))`, HOME set to `tmp_path / "home"`, and `LOGNAME`/`USER` set to
     `drafter`. The gate's command echoes `<T>/pytest-of-drafter/popen-gw4/test_x0` and
     `drafter said hi`, then exits 1. Assert that the record holds
     `<tmp>/pytest-of-<user>/popen-gw4/test_x0` and still holds `drafter said hi` (prose
     untouched), and that neither the temp path's forms nor `pytest-of-drafter` appear.
   - The same test also asserts that `factory.is_read("ls <tmp>/pytest-of-<user>/x")` is True.
   - `tests/test_hand_gate.py`: add `TMP_MARK` and `USER_MARK` to
     `test_the_copies_are_the_factorys`'s names. Extend `test_the_placeholders_are_the_factorys`'s
     text with a temp-dir path holding the login name, with the same `tempfile.tempdir` and
     `LOGNAME`/`USER` patches, so both copies agree on it.
5. **`intent.md`**: strike both open questions with what was decided above, and add `plan.md`
   (this plan) to the folder at ship.

## Verification

- `uv run --group dev pytest -q tests/test_factory.py -k "gate_records or placeholders or home or is_read" tests/test_hand_gate.py tests/test_nothing_local.py tests/test_windows.py`
- The new test fails before the change (the username is in the record) and passes after.
- `./check.sh`: the full gate, including `test_windows.py`'s checks on top-level imports.
