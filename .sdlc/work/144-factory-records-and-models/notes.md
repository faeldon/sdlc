# Notes

- [x] A gate record that quotes a line in a shape `test_nothing_local` refuses keeps every later → seed: 2026-11-18-61
  gate red: `factory.py gate` files the output's tail into `build/round-<N>.gate.md`, which the next
  run's scan reads. Seen on this change's round 1, where the builder's report quoted a red test's
  output holding the fixture's `work/<number>*` glob and the gate's record quoted the scan's
  report of it; both copies were rewritten as `work/NNN*` by hand. Filing gate output (and a
  builder's Evidence) with `PATTERNS`' shapes defused would close it for any number, not only the
  change's own, which this change rewrites.
