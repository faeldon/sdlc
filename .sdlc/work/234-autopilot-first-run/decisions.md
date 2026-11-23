# Decisions

- [x] D1 (builder round 1, default): Leave `enabled = true` on main after the M25 run until a later change turns it off? Going ahead with leaving it on: this change adds no off-switch. → decided: the assumed default, confirmed
  - OPTION: leave it on, a later change turns it off — this change stays the one-file settings edit it set out to be; autopilot stays enabled between runs, but nothing runs until someone runs `--begin`
  - OPTION: a follow-up change turns it off right after the run — nothing is enabled that nobody planned; one more small change
  - OPTION: turn it off in the retrospective that reads what the run landed — the decision is made with the evidence; the setting stays on until then
  - WHY: the intent leaves this open, and autopilot still needs a person to approve its single WAIT before it begins, so leaving it on starts nothing.
