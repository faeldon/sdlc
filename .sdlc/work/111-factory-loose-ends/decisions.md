# Decisions

- [x] D1 (builder round 1, default): Should the UI review's server retry on a new port, or have `[ui] serve` report the port it bound (`{port}` = 0)? Options: retry; report. Going ahead with retry, as the Approach says: it needs nothing from a host's serve command and adds no placeholder. → decided: the assumed default, confirmed when landing
- [x] D2 (builder round 1, default): Should the spec skill show `behind` and what `fresh` did next to the draft, or inside the approval question? Options: next to the draft; in the question. Going ahead with next to the draft, as the build skill does. The question's literal text stays the same, and once `fresh` has run, `behind` in the question would always be 0. → decided: the assumed default, confirmed when landing
