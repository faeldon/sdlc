
**Open questions resolved**

- *Is the purpose written when the run starts, or derived by `retro`?* Both, split by what can be known when. `cmd_agent` knows the task, role and round, so it writes the purpose. An ejection or a drop happens after the row exists, so `retro` derives it from `runs/ejections.jsonl` (new, R4) and the `Drop` record. This is what the intent's Outcome already asks for ("counts as waste without its row being rewritten").
- *Does a mend count as waste?* Drafted as yes. The person's own seed text and the scorecard's waste list both name mends. The spec reports `mend` as its own part, so a reader can take it out of the share. Confirm at approval; if the answer is no, only `WASTE` changes.

**Left for the person**

- **When an ejected change lands later, is its first landing's spend waste?** The draft says only the ejected attempt's landing-task rows (resolve, landing review, verify, mend, fix) are waste (`ejected`), and the build's rows count as `build`, since that work landed.
  - Choosing "none of it" would make ejections free in the waste share, which would hide what a red train costs.
  - Choosing "all of it, build included" would count a landed change's build as waste, so the share would rise with every ejection whatever its cause.
- **Does `train --stop` count as an ejection?** The draft records it with `cause: stop` and counts it under `ejected`, because that landing work is redone too. If a stop shouldn't count, because it isn't the change's fault, the reader can leave out rows from `cause: stop` and keep the record.
- **Is a restart's escalated run waste?** It is left out of waste in this change: its rounds keep their written purposes, and it shows as an escalation in `autonomy`. Counting it would need a rule for which of the restarted run's rounds were thrown away.
