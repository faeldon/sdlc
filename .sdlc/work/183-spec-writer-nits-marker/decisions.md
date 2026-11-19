# Decisions

- [x] D1 (builder round 1, default): Should the spec prompt only say how to write the nits the intent names, without handing the spec-writer a list of open nits on the change's paths? Going ahead with "only those the intent names" unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: only those the intent names — matches the constraint "never takes a nit in unasked", and needs no new script code; the spec-writer doesn't see other nits on the same paths
  - OPTION: hand it the open nits on the change's paths, as `sdlc.py nits --touching` gives the core skill — the same offer `/sdlc:spec` makes; needs `factory.py` to run it and add it to the prompt, which the intent rules out ("wording only")
  - WHY: the intent's Constraints ("Wording only", "only those the intent's Problem or the person names"), and the spec-writer can only read files, not run commands
