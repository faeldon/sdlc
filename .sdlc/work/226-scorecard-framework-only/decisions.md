# Decisions

- [x] D1 (builder round 1, default): Keep the seed ids that sit outside the Status lines? The Speed Diagnostics say "captured (S10, 175)" twice, and *Hosts* says "when S14 and S15 build it" and "(S1)". Going ahead with keeping them, as the intent's constraint says, with a follow-up in `notes.md`. → superseded by D4
  - OPTION: keep them — follows the word-for-word constraint; four ids still point at nothing
  - OPTION: reword them now — the doc has no dead ids; goes past the constraint and the outcome's list
  - WHY: the constraint is the person's explicit words, and the outcome names only the Status lines
- [x] D2 (builder round 1, default): Should this repo have a release rule of its own besides *Release due*? Going ahead with none. → decided: the assumed default, confirmed
  - OPTION: none — the guide's rule applies, and `SDLC.md` holds no restatement of it; nothing makes a release happen before a retrospective
  - OPTION: "release before each retrospective" — gives `time_to_users` a release to measure; another rule of this repo's own to maintain
  - WHY: the intent's outcome says this repo releases on *Release due*, as the guide says
- [x] D3 (builder round 1, default): Should a metric still marked *not captured* get a seed? Going ahead with the Status line saying so and no seeds filed. → decided: the assumed default, confirmed
  - OPTION: just say so — the scorecard is the record, and nothing is filed without the person
  - OPTION: file a seed for each — seven gaps become visible in the register; the register fills with work nobody has chosen
  - WHY: filing seeds is the person's or the retrospective's call, not this change's
- [x] D4 (builder round 2, default): Remove the seed ids that sit outside the Status lines too, keeping the rest of each sentence. This is now built, following the reviewers' kept changes. → decided: the assumed default, confirmed
  - OPTION: remove them — no ids in the doc point at nothing; four sentences lose a short note, which strays slightly from the word-for-word rule
  - OPTION: keep them — follows the word-for-word rule exactly; four ids would still point at nothing
  - WHY: the Problem names ids that point at nothing as the defect, and removing them is the smaller deviation
