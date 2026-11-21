
I settled these open questions from the code or the intent:

- **Does the script write the preview for every skill, or only where a script already words the
  question?** Only where a script already words the question: `preflight` (as the new
  `--preview`), the factory's `start` and `agent --task spec`, and `land-check`'s `shown`. The
  intent's Outcome says the same. The rest is model-drafted prose, which `sdlc.py` never writes
  (AGENTS.md, *Mechanism vs. judgment*). Rendering it would mean saving drafts to disk before the
  yes.
- **Does a WAIT with nothing to preview need one?** No WAIT has nothing to preview. All 20 write
  or run something that can be named. A retirement previews the entry and its reason, which idea's
  Step 3 already shows. Publish previews the commits and the command. So no WAIT is exempt, and
  the test covers all 20.
- **Where does the factory spec draft's preview come from?** From `agent --task spec`'s reply
  JSON, not from `start`. `start` runs in Step 0, before the draft exists.
- **Who writes ship's preview, given the commit message is never on disk?** The skill puts the
  message first, as it will be committed. `preflight --preview`'s findings, paths and stamp line
  follow, as printed.

These are left for you:

- **How long can a preview be before it's cut, and what does the cut part say?** The draft says
  40 lines. The kept part is the "approving part" each skill's row names, and the last line is
  `… <k> more lines in <path>`, or `… <k> more lines, shown above` when nothing is on disk yet.
  - A lower limit (20 or so) fits a phone's dialog, but more previews get cut.
  - A higher one (80 or so) cuts less, but the yes option may scroll inside the dialog, which is
    part of the problem this change fixes.
  - I don't know of a documented limit on `AskUserQuestion`'s `preview`. If the harness has one,
    it should decide the number.
- **Widening the AGENTS.md *Skills* invariant to require the preview.** Approving this spec
  approves that policy edit (R13). Saying no would keep the preview as advice in CONTRIBUTING.md
  alone, with no test checking it.
- **Adding `sdlc:update` to the change's scope.** The intent's list of skills left it out, but it
  is in `GATED` and has a WAIT. The spec includes it so the test can cover every WAIT.
