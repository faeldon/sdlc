# Decisions

- [x] D1 (builder round 1, default): Home mark is `<home>` (the intent's first open question). It matches `<path-to-clone>`, and a bare `~` with nothing after it is impossible to guarantee once a path follows. Going ahead with `<home>` unless told otherwise. → decided: the assumed default, confirmed when landing
- [x] D2 (builder round 1, default): Paths only, no check against `.sdlc/terms.local` (second open question). That file is local to the main checkout, and a term found in a reply has no mark to put in its place. Going ahead with paths only unless told otherwise. → decided: the assumed default, confirmed when landing
- [x] D3 (builder round 1, default): The agents' prompts are unchanged (third open question). The script's replacement is the whole fix, because a prompt can't be enforced. Going ahead unless told otherwise. → decided: the assumed default, confirmed when landing
