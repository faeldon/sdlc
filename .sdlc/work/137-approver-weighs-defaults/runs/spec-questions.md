
**Open questions resolved**

- *May the approver settle a default at all, or only recommend?* The intent's own Outcome answers it: it may settle, as its own mark, never as the person's (R5–R7). Recommend-only is under Alternatives rejected.
- *Should `decide` take every change, one at a time, or only the one named?* Only the one named, as the Outcome says (`/sdlc-factory:decide NNN`, "one change's open decisions"). It is also the build skill's one-change-per-dialog rule.
- *Where do the alternatives come from?* The agent that raised the default, two to four of them, its own first (R1, R4). For a default raised without them, the approver gives them when it escalates it (R3, R5). `decide` asks an old or bare line with the default alone (R15).
- *Does `/sdlc:ship` show the alternatives too?* Yes: ship already shows every open default, and its `factory.md` now shows the `OPTION`/`WHY` lines under each, with settled lines as their own list (R12). The text is already in the ledger, so it costs nothing.
- *Does the supervisor's `decide` step keep working?* Yes, unchanged (R16). They share the ledger mark and nothing more (Alternatives rejected).

**Left for the person**

- *Does a default the approver settled still keep the landing from passing itself?* The draft says **yes** (R9): a settled default is a landing signal, so the person sees the approver's calls in the landing's one question before anything lands. Escalations get fewer, but a batch holding a settled default never lands without asking. Answering **no** means dropping R9's signal: a READY batch whose only open items the approver settled lands `by=auto`. That moves O6 further, and puts an agent's call on `main` without a person seeing it, recorded as `auto`, never as theirs.
- *Agreement with 136.* 136 isn't in this worktree, so this draft couldn't check that the two agree on what an escalation means. If 136 reads the approver's escalations by its `Decisions to confirm` lines, it should read R5's `- ESCALATED: D<n>:` lines instead. Whichever lands second should check that.
- *Superseded defaults at the landing.* R8's switch to `open` also stops the landing listing a superseded default as "assumed" and signalling it, which it does today. That looks like what 105 R7 meant, but it is a behaviour change to the landing's signals. Say if it should be split out.
