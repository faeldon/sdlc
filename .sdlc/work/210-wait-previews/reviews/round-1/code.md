VERDICT: PASS

The change meets all 13 requirements. The gate record `build/round-1.gate.md` is green, and I ran no tests myself.

## Notes
- NIT: scripts/sdlc.py:8308: R7 says `--preview` takes the same clause flags as `--question`. They parse, but `cmd_ship_preview` ignores them without saying so. Refuse them with `--preview`, as the code already refuses clause flags without `--question`, or say in the help text that they are ignored. {robustness S low}
- NIT: skills/ship/SKILL.md:Step 5: the cut applies to `--preview`'s output alone, but the commit message goes in the same preview ahead of it. A long message can push the dialog past 40 lines, and nothing says which part to cut. Say that the message counts toward the 40. {docs S low}
- Open defaults D1 (ship's line budget raised from 475 to 480) and D2 (`start`'s preview skips the scaffold `spec.md`) are the builder's. Both look reasonable.
- Done well:
  - `build_preview` is built from the same inputs as `build_question`, so the two can't disagree.
  - `_readable_findings` is shared, so `--question` and `--preview` refuse a bad `findings.md` the same way.
  - `_diff_rows` is reused instead of a second `git diff` call.
  - `PREVIEW_LINES` and `_preview_cut` are pinned equal across both scripts.
  - `--question` and `--preview` together are refused.
