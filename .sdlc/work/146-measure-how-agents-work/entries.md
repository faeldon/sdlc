# 146-measure-how-agents-work — entries

## [2026-11-18-64] [nit] `bg` only looks for a trailing `&` at the end of the whole command.

Raised by the code review of 146-measure-how-agents-work, round 1: scripts/metrics.py:306: `bg` only looks for a trailing `&` at the end of the whole command. A multi-line command that backgrounds a middle line, such as `a &\nb`, isn't counted. The spec calls every count a lower bound, so this is allowed. Saying so in the docstring or adding a test would settle it.

Theme: tests
Paths: scripts/metrics.py
Cost: S
Value: low
Raised by: 146-measure-how-agents-work (correctness)

## [2026-11-18-65] [nit] the `uvx`/`npx` branch builds the program list with `[...][:1] + words[2:]`, and that is only correct when the program is the first non-flag word.

Raised by the code review of 146-measure-how-agents-work, round 1: scripts/metrics.py:261: the `uvx`/`npx` branch builds the program list with `[...][:1] + words[2:]`, and that is only correct when the program is the first non-flag word. A short comment would help the next reader.

Theme: style
Paths: scripts/metrics.py
Cost: S
Value: low
Raised by: 146-measure-how-agents-work (correctness)
