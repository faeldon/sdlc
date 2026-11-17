# Notes

- [x] `sdlc.py gate` (the hand gate) takes no `gate_jobs` slot, by the spec's boundary: sharing → seed: 2026-11-17-63
  the slots would make `sdlc-factory-gate-<k>.lock` a contract across the two plugins. A later
  seed if hand gates and factory gates are found fighting for cores.
- [x] `/sdlc-factory:spec` gets `start`'s new `base` and `behind` keys but doesn't show them, and → seed: 2026-11-17-64
  doesn't run `fresh`: a spec drafted alone may still read old code.
