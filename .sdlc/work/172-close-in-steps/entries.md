# 172-close-in-steps — entries

Retire 2026-11-18-100: taken in by 172-close-in-steps
Retire 2026-11-19-2: taken in by 172-close-in-steps
Retire 2026-11-19-3: taken in by 172-close-in-steps
Retire 2026-11-19-4: taken in by 172-close-in-steps

## [2026-11-19-26] [nit] `measure.errors` holds the raw exception text.

Raised by the security review of 172-close-in-steps, round 1: scripts/closing.py:396: `measure.errors` holds the raw exception text. In the plugin's own repo, a child after a handoff passes it up unchanged. It's local stdout only, but if a future reader of the run files puts a path or a line of content in a message, that text lands in close's report, so say in the docstring that the message is meant for the person running close and must never become a trailer

Theme: docs
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 172-close-in-steps (contract)
