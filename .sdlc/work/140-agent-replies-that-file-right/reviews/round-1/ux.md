VERDICT: PASS

This change is almost entirely factory parsing, agent prompts and tests. The one place a person would see it is the board, and I found nothing to fix there.

## Notes
- **Read:** the 1280x800 and 390x844 board screenshots, and `intent.md`. I did not read `spec.md` or the changed code paths, and I never saw the board source's loading, empty or error states.
- **Board at both widths:** the screenshots show cards for stopped, decision-waiting and escalated runs. Each card says what happened, what it needs from the person, and a `next:` command. Examples are "stopped: rerun to ask an agent again" and "decide D1 in the factory's supervisor". At 390 wide the cards stack into one column and the task is still doable.
- **Stopped-card text:** the fixture reason is "build/round-1.md has no ## Evidence section". It names the file and the missing part, so the person can act on it.
- **Words:** the labels "needs you", "next:" and "stopped" are used the same way on every card. I saw no unlabelled controls.
- **States not seen:** I did not review the board source for loading, empty or error states.
- **What the change does well:** a reply that only has prose before its verdict is now read as that verdict and no longer stops the run. That means fewer "needs you: stopped" cards that come from reply layout rather than from a finding.
