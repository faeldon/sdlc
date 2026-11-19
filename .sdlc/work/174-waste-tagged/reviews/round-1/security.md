VERDICT: PASS

## Notes

**Trust boundaries the diff touches**

1. **The rows `factory.py` writes to `runs/costs.jsonl`.** The new values (`purpose`, `task`, `round`, `land`) come from the script's own state: `TASK_PURPOSE`, `loop_state` and `land_round()`. No prompt or reply goes into a row, so a row is still numbers and names only.
2. **What `spend_rows()` and `retro._cost()` read from git.** They read `costs.jsonl` and the new `ejections.jsonl` from each closed change's commit and each dropped change's branch tip. Text on a branch tip is controlled by whoever made the branch.
   - **Tampering:** a crafted row can only skew the figures. Odd values are already handled. A non-numeric `cost_usd` becomes `usd: null`. A boolean `duration_ms` counts as 0. An unknown `purpose` is `untagged`. A row with no session is skipped. A line that isn't JSON is skipped.
   - **Injection:** `role` and `model` are free strings, but they appear only in the JSON output, which `json.dumps` escapes. The Markdown report's new coverage lines hold only counts and the fixed reason phrases from `_cost_why()`, so row text never reaches the report.
   - **Information disclosure:** each change's own rows (`cost.changes`) are dropped without `--metrics`, as `spend.changes` already is.
3. **`_record_ejection()`.** It writes to a fixed path under the change's folder, opened with `encoding="utf-8"` and `newline="\n"`. The `cause` value comes from the train's own code. It runs before `_amend_record()`, so it goes through the landing's existing commit and nothing new commits.
4. **`metrics.runtime_trailer()`.** Capping each value at 64 characters bounds what a transcript can put on the trailer line. The cap applies after `_model_word()`, so a value still can't contain a `,` or `:` to break the format.

No secrets, dependencies, shell calls, `eval`, or new deletes or overwrites. `retro` is still read-only. No agent gets a new tool or permission.

**Info:**
- The builder can write in the change's folder, so it could add fake `costs.jsonl` rows. That would change whether a later run is tagged `rerun`, and so the waste share. It only skews a self-reported metric and crosses no boundary. The waste figure is a measurement, not a control, so I'm not asking for a fix.
- `purpose_of()` treats a row with no `task` (written before this change) as never matching. Old rows can't turn a new run into a `rerun`.

**What I checked:** I read `intent.md`, `spec.md`, `decisions.md` and the full code diff (`factory.py`, `landing.py`, `run_state.py`, `factory_records.py`, `retro.py`, `metrics.py`). The round-1 gate record is green, with plugin validation passing. I ran no tests myself.
