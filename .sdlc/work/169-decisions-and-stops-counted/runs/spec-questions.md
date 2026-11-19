Resolved from the code:
- **What makes a stop spurious (the intent's open question).** Only "mended away" is in committed records. `runs/mended` is committed, and the run clears those stops without the person. "Cleared on the next reading with no change" leaves nothing in history, because `runs/stopped.md` is removed and `runs/step.md` overwritten. So `spurious_stops` counts mends, and the other reading is listed under `unmeasured` as needing a factory stop log.
- **Idea -92 versus the intent's "an after-gate stop's way on names its skill."** Factory stops already name their skill (`WAYS` in `factory.py`). The idea's text is about `metrics`' `after_gate` stops, which record no skill, so the spec adds `Sdlc-AfterGate` (R11–R12) and leaves `factory.py` alone.
- **Nits -86 and -87.** Both are fixed, not just answered: R13 and R14.
- **Where the records are read.** At each closed change's own commit (`rec["sha"]`), through `factory_records` with `show` and `listing`, as close's measure step reads them.

Left for you:
- **Overturned approver calls.** No record shape exists: the decide skill never asks, and an overturn by hand is free-form. The spec reports it as unmeasured. The other choice is to define a shape for the person's answer on a settled line, which means a decide-skill change and is best filed as a seed.
- **Landing-confirmed defaults and the kept-default rate.** The spec keeps them out of the rate and reports them beside it as `confirmed`. Counting them as kept would make the rate say "agents could have decided these" for defaults the person never looked at one by one.
- **Auto-landed share's denominator.** The spec uses every factory change, with ones shipped by hand counted as `shipped`. The other choice is to count only changes `/sdlc-factory:land` landed, which matches the scorecard's "share of landings" word for word but hides factory changes taken off the landing path.
