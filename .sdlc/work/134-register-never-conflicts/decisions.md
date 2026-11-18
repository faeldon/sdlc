# Decisions

- [x] D1 (builder round 1, default): Should drop refuse when `entries.md` holds only `Retire` lines? Options: refuse on entries only; refuse on any line. Going ahead with entries only: a drop retires nothing, so losing those lines is what should happen. → decided: the assumed default, confirmed when landing
- [x] D2 (builder round 1, default): Should `held_entries()` accept `>` note lines and the `# ` title before the first entry? Options: accept them; accept only `Retire` and blank lines. Going ahead with accepting them; any other stray line is refused, naming its line. → decided: the assumed default, confirmed when landing
