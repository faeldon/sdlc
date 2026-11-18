DECISION: READY

**Why.** All four reviewers (code, behaviour, ui, ux) passed in round 1, and the gate passed at build `087b5a74c434`. The code reviewer ran `./check.sh` again and it passed. Every outcome in the intent has code and a named test, and the only things left are two minor notes recorded in `findings.md` (F1, F2) and two follow-ups written down in `notes.md`. In two places the build doesn't do what the intent asked: the decision line on a building card, and where an early stop is recorded. In both, following the intent would make the board say something untrue, which goes against its main aim (O6). `plan.md` and the build report explain both, and I settle both below from the code.

**Open items**
- No change is still open. F1 (a type annotation on `stop_text`, from code) and F2 (the hand-built `reading` dict in `status`, from code) are minor notes, recorded and needing no action.

**Decisions to confirm**
- No blocking decision is unticked.
- SETTLED: D1: `cmd_ask` at `plugins/factory/scripts/factory.py:1916` refuses any change not at `stage: test`, with the message "a run still building asks its own blocking decisions, through the session running it". So a building card that said `/sdlc-factory:decide NNN for D1` would send the person to a command that refuses them, which breaks O6. The code also bears out the intent's own claim only at `test`. The behaviour reviewer agreed in round 1, and option 3, extending `decide`, is left for a change of its own.
- SETTLED: D2: `runs/stopped.md` has a fixed shape, `STOPPED: (mend|rerun|ship)` (`FACTORY_STOPPED_RE`, `scripts/sdlc.py:4355`). `needs_of()` treats that file as a run waiting on the person (`sdlc.py:4532`). Writing it for an early stop, while the approver is still about to decide, would put the card in Needs you and hide its track. Recording the reason in `step.md` keeps the card true, and `stop_text()` still carries the reason into `stopped.md` when a real stop is written. The behaviour reviewer checked both cases in round 1.
- SETTLED: D3: the intent says both `accept` and `cases` "record a landing step". Two named steps meet that and keep the card's label true while cases run. The board test checks each one (`LANDS["checks"]`, `LANDS["cases"]`), and so does `test_accept_and_cases_record_their_landing_step` in `test_land.py`.
- SETTLED: D4: this is the same question as D1, raised again by the ux reviewer, and the same code answers it: `factory.py:1916`, and the record at `board.py:755` that `decide` refuses a build in progress. The ux reviewer passed with this default.

**For the person at ship**
- Look at `next_action()` and `column()` in `scripts/board.py` first: the decision line on a building card (D1/D4), and the stopped-landing check that now comes before `close`.
- Then look at `needs_of()` and `factory_land_stop()` in `scripts/sdlc.py`. This is where the intent's open question was answered "yes, `status` agrees too", so `status`'s "What needs me" section now lists stopped landings.
- Last, look at the plain stop lines in `factory.py`: `_amend_plain()`, and `_land_refused()` / `_close_stopped()`, which now record the plain line before the raw text.

- IMPACT: patch — the board and `status` now show a factory landing truthfully: the card stays during a rebase, the landing steps appear, the stop lines are plain, and rounds are labelled `B` and `L`. No command, record file name or config key changes, so no one has to do anything differently.

**Each undone item's disposition**
- UNDONE: A shipped change whose landing rebase is stopped shows the hand-run `sdlc.py resolve` line as its next step while the factory's builder is resolving the conflict (`next_action()` puts `rebasing` first): a landing-aware line ("its builder is resolving a conflict: wait for it") would be truer. Left for a change of its own, since `PRECEDENCE` and `BOTH` pin the order. → seed: Board says "builder is resolving a conflict" on a factory landing mid-rebase
- UNDONE: `factory.py accept` run after a rebase (inside a landing round) records no step: the track stays at `gate`, which it runs beside. A `checks` position after the gate would need the record to say where it sits. → seed: Landing track shows post-rebase `accept` as its own step after the gate

**How to recover.** The prompt names no irreversible paths, so I've given no `- RECOVER:` lines. Per `plan.md`, `git revert` undoes the whole change.
