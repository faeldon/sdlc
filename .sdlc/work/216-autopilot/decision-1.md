DECISION: ESCALATE

## Why
The last round (3) is all `VERDICT: PASS` with no open CHANGE, and the gate is green. Ten open defaults remain. They touch policy, scope, a published config interface and security. The diff also touches the sensitive paths `landing.py` and `closing.py`, so none can be carried with `CONFIRM`. Most of them are departures from the approved spec, and only the person can decide those.

## Open items
- None. The round-3 reviewers (code, test, behaviour, security) raised no unresolved CHANGE.

## Decisions to confirm
- ESCALATED: D1: the weight tables are named `*_weights`, which departs from the spec's table names. This is a published `[autopilot]` config interface, so the person decides the naming, not the approver.
- ESCALATED: D2: R17's rerun of the approver after autopilot answers open calls is not built. This changes who approves what at `done`, and the spec approved R17 as written.
- ESCALATED: D3: a spent debt or risk budget stops new waves, intents and trains, but changes already opened go on to `stage: test`. This is budget policy, and R27 and the dry run disagree.
- ESCALATED: D4: `--level` is defined as the highest tier autopilot opens. This is a scope decision, and the intent doesn't define "level".
- ESCALATED: D5: autopilot disposes of undone notes and nits as the approver proposed, with no person's landing yes. This is a policy call about what the run's single yes covers.
- SETTLED: D6: R13 reads `Close` commits through `factory.closes()`. `plan.md` and the build explain it, no `sdlc.py` command prints them, and it adds no published surface and changes no behaviour.
- ESCALATED: D7: this is the same call as D2, raised again by the code reviewer. It stays with the person alongside D2.
- ESCALATED: D8: whether the default `guards` include `[review] sensitive`. This is security policy, and in this repo the sensitive paths include the run's own code.
- ESCALATED: D9: whether seeds carrying an `Issue:` line are candidates only when named in `--seeds`. Public, outsider-written text would reach a build unseen, which is a policy and security call.
- ESCALATED: D10: whether `--by autopilot` is documented as protection against accidental inheritance only, not a boundary against a same-user process. This is a security-posture choice, and the spec's R2 defines the check this way.

## Every other reason you escalate for
- ESCALATED: look: `plugins/factory/README.md` (*The approvals*) and `spec.md` *Contracts touched* — under autopilot a spec and an intent are written and built on with only the run's yes. The spec says this needs the person's explicit decision, and the build follows it. The person should confirm they approved that promise change.

## For the person at ship
- Look first at `plugins/factory/scripts/autopilot.py`, `autopilot_running()` and `take_markers()` in `factory.py`, and the sensitive paths `landing.py` and `closing.py`.
- The spec's *Contracts touched* names the one-WAIT-per-run contract. Check it against the factory README wording.
- Config keys in `[autopilot]` are new, so D1's table names are worth a look.

- IMPACT: minor — adds `/sdlc-factory:autopilot`, `sdlc.py status --json` and `[autopilot]` config as new capabilities; nothing existing changes for a holder of the previous release.

## Undone items
- UNDONE: The board shows nothing of `opened_by: autopilot` or a run under way: `status` does; the board's is seed 2026-11-21-34, which waits on this change. → dropped: already tracked as seed 2026-11-21-34.
- UNDONE: `next_up`'s cheap-nits lines (`rule: nits`) carry no seed id, so autopilot never takes them, though `READY_RULES` lists them. → seed: Let autopilot take cheap-nits lines from `next_up`
- UNDONE: `test_autopilot_end_to_end` drives the loop in process with `run_step` stood in for, as the train's tests do. Since round 1, `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` runs a real `run_step` child under the lock, but no test runs the whole loop's subprocesses with a stand-in `claude`. → seed: Test the whole autopilot loop with subprocess steps and a stand-in `claude`
- UNDONE: The retrospective's overturn rate for autopilot's calls (the spec's question 6) is left for a later seed, as the intent's resolution says. → seed: Retro overturn rate for autopilot's calls
