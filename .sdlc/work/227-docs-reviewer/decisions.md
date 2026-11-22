# Decisions

- [x] R1 (person, revise): R4: also join whenever the diff touches any path outside tests/ and the change folder, so no diff loses the check code's Context pass gave it. R12: state each doc edit as something a test or grep checks (the guide row text, the REFERENCE key, the README table, the FEATURES entry, the build skill sentence, the AGENTS.md agent list), so no requirement is untestable.
- [x] D1 (builder round 1, default): Ship asks for the `Docs review:` line only when the change has a `findings.md`. Going ahead with that unless told otherwise. → decided: the assumed default, confirmed when landing
  - OPTION: only when `findings.md` exists — a change with none keeps shipping as today (the code already treats such a change as older than the file); a ship without the file never shows whether the docs review ran
  - OPTION: always, as the security and behaviour checks do — the same rule for every pass; any hand-built change with no `findings.md` is refused, since this pass applies to almost every diff (83 tests failed this way, the new-to-close adoption flow among them)
  - WHY: the docs pass applies to nearly every diff, unlike the other passes, so the same rule would make `findings.md` effectively required at every ship, which no requirement asks for
