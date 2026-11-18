VERDICT: PASS

The new `## Hosts` section in `docs/RETRO-SCORECARD.md` matches the three Hosts items in `notes.md`. It sits between *Insights* and *Seeds to build it*, and the seed ids it cites (S14, S15, S1) exist in the doc.

## Notes
- **Numbers, page, questions and meanings:** the section places them in `sdlc.py retro`, `templates/retro.md` (host-overridable), a `guide/` file a host extends, and REFERENCE.md's *Retrospectives*.
- **Simplicity and debt index:** it says Simplicity means the process's own overhead in a host, and that the debt index comes from the host's `retro.indicators`.
- **Lead time:** a host on local numbering has no issue and `created:` is date-only, so S1 has `new` record a timestamp.
- **What a host leaves out:** the skills' cases are omitted, and the page says "no factory changes" rather than zeros.
- **checks.md, "The scorecard doc holds the framework":** I expect it to pass. The section headings and the S16 and R6 markers are still present; the diff only adds a section.
- **checks.md, "CONTRIBUTING's layout lists the doc":** I expect it to pass. The `docs/RETRO-SCORECARD.md` row is in the diff.
- I did not run `checks.md`, per the rules. I did not rerun the whole suite; `round-1.gate.md` is the gate's record.

## Evidence

$ git diff 5ddb17a6db671d07b3f6329c6321ed00d62e8aa9...HEAD --stat
26 files changed, 1429 insertions(+) (includes docs/RETRO-SCORECARD.md +511, docs/CONTRIBUTING.md +1)
exit: 0

$ grep -n -A40 -i '^## Hosts' docs/RETRO-SCORECARD.md
423:## Hosts … lines 425–445 as read above (four-part placement, Simplicity, debt index, lead time, leaves-out)
exit: 0

$ grep -n -i -B1 -A8 'hosts' .sdlc/work/159-retro-scorecard-doc/notes.md
lines 37–51: the three Hosts items, each ticked and linked to a seed
exit: 0

$ cat .sdlc/work/159-retro-scorecard-doc/checks.md
two checks, as listed in Notes
exit: 0

$ git diff 5ddb17a6db671d07b3f6329c6321ed00d62e8aa9...HEAD -- docs/CONTRIBUTING.md
+| `docs/RETRO-SCORECARD.md` | the framework `/sdlc:retro` reports against … |
exit: 0

$ grep -n -i 'S14\|S15' docs/RETRO-SCORECARD.md
S14 at 474, S15 at 475, plus the references at 74, 425 and 508
exit: 0
