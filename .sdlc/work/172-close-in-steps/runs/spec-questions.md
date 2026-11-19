
Open questions resolved:
- **Shared state object or today's locals** (intent): a `@dataclass` `_Close` passed to module-level step functions. The reasons are under *Alternatives rejected*, first bullet. The code shows the closures already share mutable `report`, `kept` and `captured`, and that `own` was quietly rebound (harmless, and fixed by separate fields).
- **How to make -3 visible:** a `measure.errors` entry in close's report. Not stderr: `_handoff()` drops a handed-off child's stderr when its report parses, and in this repo close always runs as a handed-off child. Not the coverage word either: it's a documented trailer value.
- **How to make -100 exact:** `math.floor(round(x * 100, 6)) / 100`. Spending accumulates float noise, so `Decimal` from the float's text isn't enough.

Left for you:
- **R14:** should this change also correct `docs/REFERENCE.md` §Metrics? It currently says a factory change's `source=git` line keeps `ready_wait`, and the code doesn't. I couldn't read 162's D1 from this worktree. The intent says D1 was answered and changes no code, so I've assumed it kept the code as it is. If D1 said otherwise, -2 isn't "answered" and needs a code change. If you say no to R14, the docs keep contradicting the code.
- **The 40/100-line limits in R1/R2:** these are my choice of a checkable meaning for "short". Tighten or loosen them if you want different numbers.
