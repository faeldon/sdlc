# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The factory's tests are split, none past 2,000 lines, sharing one helper module

Only a revert brings back the one file or a second copy of the loaded `factory.py`.

```sh
test ! -e tests/test_factory.py &&
test -f tests/factory_helpers.py &&
for f in loop decisions depth eval agent gate ui; do
  test -f "tests/test_factory_$f.py" &&
  test "$(wc -l < "tests/test_factory_$f.py")" -le 2000 &&
  grep -q '^from factory_helpers import' "tests/test_factory_$f.py" &&
  ! grep -q 'factory_under_test' "tests/test_factory_$f.py" || exit 1
done &&
grep -q '^def claude' tests/conftest.py
```
