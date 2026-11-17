# Notes

- [x] `factory.py land-fix --ask "<words>"` passes the person's words through a shell argument, as
  R8 specifies. Everywhere else, free text reaches an agent through `decisions.md`
  (`--revise R1`, `--words R1`), never on a command line, where a quote or `$(` in the words breaks
  the command or runs. A later change could write the ask to `decisions.md` as
  `- [x] R<n> (person, fix): …` and pass `--ask R<n>`.
  Done in round 2, as the person's `R2` asked: `--ask` takes the id of a ticked
  `- [x] R<k> (person, fix): …` line the land skill writes in `decisions.md`, never the words.

- [x] The person accepted the builder's rewrite of spec R8 (fix words through a ticked `(person, fix)` line in `decisions.md`; `land-fix --ask R<k>`) and the published additions as built (`unreviewed=` on `Sdlc-Landed` and `Sdlc-Totals`, `[land] moves`, the fourth answer), after the approver's escalation.
