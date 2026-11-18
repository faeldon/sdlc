# 141-board-landing-track-truth — entries

## [2026-11-18-49] [idea] Board says "builder is resolving a conflict" on a factory landing mid-rebase

Left undone by 141-board-landing-track-truth, carried forward when it landed: A shipped change whose landing rebase is stopped shows the hand-run `sdlc.py resolve` line as its next step while the factory's builder is resolving the conflict (`next_action()` puts `rebasing` first): a landing-aware line ("its builder is resolving a conflict: wait for it") would be truer. Left for a change of its own, since `PRECEDENCE` and `BOTH` pin the order.
See .sdlc/work/141-board-landing-track-truth/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-50] [idea] Landing track shows post-rebase `accept` as its own step after the gate

Left undone by 141-board-landing-track-truth, carried forward when it landed: `factory.py accept` run after a rebase (inside a landing round) records no step: the track stays at `gate`, which it runs beside. A `checks` position after the gate would need the record to say where it sits.
See .sdlc/work/141-board-landing-track-truth/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-51] [nit] `stop_text` types `stuck` and `untestable` as `list[str] = ()`.

Raised by the code review of 141-board-landing-track-truth, round 1: plugins/factory/scripts/factory.py:1956: `stop_text` types `stuck` and `untestable` as `list[str] = ()`. The annotation says list while the default is a tuple. `list[str] | tuple = ()` or `None` would match what callers pass.

Theme: style
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 141-board-landing-track-truth (correctness)

## [2026-11-18-52] [nit] `status`'s `needs_of` call for ready (shipped) changes builds a minimal `reading` dict by hand.

Raised by the code review of 141-board-landing-track-truth, round 1: scripts/sdlc.py:9986: `status`'s `needs_of` call for ready (shipped) changes builds a minimal `reading` dict by hand. A test pins the resulting output, so this is fine. If `needs_of` later reads more fields at `shipped`, this site is easy to miss.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 141-board-landing-track-truth (correctness)
