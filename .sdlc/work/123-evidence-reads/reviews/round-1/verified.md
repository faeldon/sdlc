All four are confirmed. C1, C2 and C4 repeat the same defect for the digit-target redirect or for awk, and C3 is separate.

- C1: `awk 'BEGIN{system ("rm f")}'` returns True from `is_read()`.
- C2 and C4: `cat a >2`, `cat a > 1`, `echo hi >> 1` and `cat a 2>1` all return True. Each writes a file named by a digit. `cat a &>1` also returns True, and C4 says a bare digit should pass only after `>&` or `&>`. The spec's "a descriptor (`2>&1`)" fits the `>&` form only. `&>1` writes a file, so the digit-target pass should be limited to `>&`.
- C3: `rg --pre ./x y` returns True.

None of these paths are untouched by the change, and there are no repeats.

- KEPT: code: C1: plugins/factory/scripts/factory.py:1060: `system(` is matched as a literal substring, so `awk 'BEGIN{system ("rm f")}'` passes `is_read()`
- KEPT: code: C2: plugins/factory/scripts/factory.py:1155: any all-digit redirect target is accepted, so `cat a >2` and `cat a > 1` pass while writing a file named `2` or `1`
- KEPT: code: C3: plugins/factory/scripts/factory.py:168: `rg` is a plain read, but `rg --pre ./x y` runs an arbitrary program and passes
- KEPT: test: C4: tests/test_factory.py: `cat a > 2`, `cat a >2` and `echo hi >> 1` need `NON_READS` rows, with `cat a 2>&1` kept as a `READS` row

## Notes
I loaded `factory.py` by path and ran `is_read()` on the commands above. I ran no tests and none of the `checks.md` commands.

`cat a 2>1` also passes. The tokenizer probably yields `2`, `>` and `1`, so it is the same defect as C2 and a fix should cover it.
