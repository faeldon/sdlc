# 170-trust-band — entries

## [2026-11-19-21] [nit] `_none_reason()`'s `(\s+\S+=\S*)+$` backtracks badly on a hand-written `Sdlc-Coverage` with many `a=b=c` tokens; use `(\s+[^\s=]+=\S*)+$`

Raised by the security review of 170-trust-band, round 1: scripts/retro.py:384: `_none_reason()`'s `(\s+\S+=\S*)+$` backtracks badly on a hand-written `Sdlc-Coverage` with many `a=b=c` tokens; use `(\s+[^\s=]+=\S*)+$`

Theme: robustness
Paths: scripts/retro.py
Cost: S
Value: med
Raised by: 170-trust-band (contract)

## [2026-11-19-22] [nit] `runtime_trailer()` puts no limit on how long a version or model value can be, so an odd transcript value makes a very long trailer line; capping each value (e.g.

Raised by the security review of 170-trust-band, round 1: scripts/metrics.py:1700: `runtime_trailer()` puts no limit on how long a version or model value can be, so an odd transcript value makes a very long trailer line; capping each value (e.g. 64 chars) would bound it

Theme: robustness
Paths: scripts/metrics.py
Cost: S
Value: low
Raised by: 170-trust-band (contract)
