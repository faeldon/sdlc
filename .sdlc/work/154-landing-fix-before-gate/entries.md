# 154-landing-fix-before-gate — entries

## [2026-11-18-80] [nit] `any((folder / "reviews" / f"land-{n}").iterdir())` raises if the round's folder is missing; `land_round` presumably only counts existing folders, so it is safe today.

Raised by the code review of 154-landing-fix-before-gate, round 1: plugins/factory/scripts/factory.py:5880: `any((folder / "reviews" / f"land-{n}").iterdir())` raises if the round's folder is missing; `land_round` presumably only counts existing folders, so it is safe today. Guarding with `.is_dir()` would make that explicit

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 154-landing-fix-before-gate (correctness)
