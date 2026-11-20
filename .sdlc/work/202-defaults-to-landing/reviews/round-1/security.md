VERDICT: PASS

## Notes

**Trust boundaries the change touches.** It reads a new kind of approver line, `- CONFIRM: D<n>: <reason>`, from `decision.md`. That is model output. It also reads `closes:` from the change's `intent.md`, and the landing's question now shows the approver's reason text and the default's first `- OPTION:`.

**Weighing the threats (STRIDE)**
- **Could the approver claim a yes that isn't the person's?** No. A CONFIRM never ticks the ledger (`cmd_decisions` adds it only to `weighed`). The line stays open and is shown under "Assumed decisions to confirm", so only the landing's yes, which the person gives, confirms it. That meets the "never ticked on an agent's word" constraint.
- **Could this let a change approve itself?** No. `land_signals()` (landing.py:580-584) still raises both "decisions still open or assumed" and "assumed decisions to confirm" for any open default. A batch holding a carried default is therefore never `clear`, and never lands as `Sdlc-Landed: by=auto`. This matches the intent's constraint.
- **Does the "never CONFIRM on a sensitive change" bar rest on the prompt alone?** No, the script enforces it. `run_state.uncarried()` checks a READY decision against the ledger and against `no_confirm_why()`. The cases it catches are a default with no line, one that is ESCALATED, one named twice, or a CONFIRM the bar forbids. Each becomes a problem, so `loop_state` sets `next: stop`. It is mended once, and after that it is a `rerun` stop for the person. It is never `done`. So it fails closed.
- **Is the sensitive list trustworthy?** Yes. It comes from `run["sensitive"]`, which `depth()` builds from the base branch's `[review] sensitive` (`_review_list(root, base, …)`), so a change can't edit it to loosen its own review.
- **Injection:** The approver's reason text is inserted into the landing dialog and into the `mend` prompt (`${problems}`) as plain strings. No shell, no `eval`, no HTML, no path is built from it. The board builds its page with `textContent`, and that part is unchanged.

**Medium/Low (no CHANGE)**
- **Low:** `intent_closes()` (factory.py) reads `closes:` from the change's own `intent.md`, on its branch. The builder can edit that file, unlike `[review] sensitive`, which is read from the base branch. A build that dropped `closes:` would make CONFIRM available for a change that closes an issue.
  - Exposure is small. The carried default is still a landing signal and is shown in the person's question, and preflight's own `closes` signal reads the same file. So the only effect is skipping the `/sdlc-factory:decide` stop; the person's approval is not bypassed.
  - Possible hardening: read `closes:` from the intent as committed at `stage: spec`, or from the fork point.
- **Info:** The landing dialog shows the approver's CONFIRM reason as "(the approver: …)". It is labelled as the approver's, never the person's, which is the right framing for model text.

**Nits**
- NIT: plugins/factory/scripts/factory.py:1973: `intent_closes()` reads `closes:` from the branch's own intent.md while the sensitive bar is read from the base branch; read it from the fork point so a build can't widen what it may carry {robustness S low}

**Done well**
- CONFIRM keeps the line open, so the landing, ship and `decide` all keep showing it as assumed.
- An id given conflicting SETTLED/ESCALATED/CONFIRM lines is reported as named twice, never resolved silently.
- The bar is enforced in two places: the prompt (`weigh-no-confirm`) and the script check (`uncarried()`).

**What I checked:** I read intent.md and the full diff of factory.py, landing.py, run_state.py, the approver agent, the prompts and the skills. I traced `land_signals()` for auto-landing, `depth()` for where the sensitive list comes from, and the stop and mend path in `loop_state()`. The gate record `build/round-1.gate.md` is PASS (`./check.sh`, exit 0). I ran no tests myself.
