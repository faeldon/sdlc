# Decisions

- [x] D1 (builder round 1, default): Should a hook-refused command go under the behaviour reviewer's `## Notes` rather than a new *Not run* section? Going ahead with `## Notes` unless told otherwise. → settled by the approver: `plan.md` puts the hook-refused command under `## Notes` because the behaviour reviewer's prompt has no *Not run* section and Notes already holds "anything you couldn't run and why". The behaviour reviewer's third grep check confirms the sentence is in the prompt, and the script doesn't read that heading.
  - OPTION: `## Notes` — that prompt already sends "anything you couldn't run and why" there; the script doesn't read it
  - OPTION: a new `## Not run` section — easier to scan; one more heading in the prompt, which nothing reads
  - WHY: the prompt already has a home for commands that didn't run
- [x] D2 (builder round 1, default): The intent's open question: should `exit: blocked` count as "refused by a hook"? Going ahead with no: listing it outside the evidence is enough. → settled by the approver: the intent's Constraints say an `exit:` with no number still fails, so `exit: blocked` is not read. `EXIT_RE` and the parametrised test, which still rejects `exit: nonzero` and `exit: not run`, bear this out.
  - OPTION: no — the evidence still always needs a code; a refused command is never presented as a result
  - OPTION: read `exit: blocked` — fewer stopped runs; a word becomes something the script accepts as evidence, which the intent's constraint rules out
  - WHY: the intent's constraint that an `exit:` with no number still fails
