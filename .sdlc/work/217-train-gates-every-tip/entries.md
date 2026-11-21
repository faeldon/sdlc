# 217-train-gates-every-tip — entries

## [2026-11-21-44] [nit] the `# fmt: skip` on the parametrize decorator exists only to keep the table on one line; a plain `ids=` list would format normally

Raised by the test review of 217-train-gates-every-tip, round 1: tests/test_train.py:1546: the `# fmt: skip` on the parametrize decorator exists only to keep the table on one line; a plain `ids=` list would format normally

Theme: style
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 217-train-gates-every-tip (correctness)
