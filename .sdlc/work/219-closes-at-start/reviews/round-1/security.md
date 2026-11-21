VERDICT: PASS

## Notes

**Trust boundary.** The untrusted input is the change's own `intent.md`, which any agent with Edit can rewrite during a build. The control this change adds is a ledger file in the git common dir, which those Edit and Write tools can't reach. Through STRIDE:
- **Tampering (the main threat):** a build drops `closes:` to escape the CONFIRM bar and the landing's `issue` signal. This is now closed: what a change closes is the ledger's record plus the working copy, so editing the intent can only add issues.
- **Spoofing and elevation:** a forged `closes` row can only add issues, which makes the rules stricter. The new rows have no `record` or `sha256`. Both `vouched()` and core's `vouched_in()` (`scripts/factory_records.py:981`) compare whole rows, so a `closes` row can never vouch for a record.
- **Denial of service:** `record_closes()` appends only a value it hasn't seen. A build that keeps changing `closes:` adds a few short lines at most.
- **Information disclosure, repudiation:** nothing new. The rows hold a folder name and an issue list, written with `json.dumps`, so nothing can be injected into them.

**Every reader goes through the union.** I grepped all four places that read what a change closes:
- the approver's prompt (`_task_prompt`, `factory.py:4703`)
- the script's own CONFIRM check (`run_state.py:198`, through `uncarried()` and `no_confirm_why()`)
- the landing signal (`landing.py:599`, which also keeps preflight's reading, so it can only fire more often)
- `no_confirm_why()` itself

No reader in the factory still reads only the intent's own `closes:`. Autopilot's `closes()` calls are about issues already closed on the base branch, which is a different question.

**D1 (record in `agent` too) is right for security.** Autopilot never runs `start`. Recording only there would have left unprotected exactly the runs 216's D9 depends on. The recording runs after the refusals and before `claude` starts, and a failure to write it is a refusal, so the check fails closed.

**What it still doesn't protect against.** A shell command can reach the git common dir and delete or truncate the ledger, which would erase the `closes` rows. The README's ledger paragraph (unchanged) already says the ledger doesn't protect against this. Erasing the ledger would also un-vouch the run's gate and build records and stop the run. A change that was already mid-run before this lands has no recorded row until its next `start` or `agent` call. Both are Low.

- NIT: plugins/factory/scripts/factory.py:5095: in `cmd_agent`, `_record_land()` runs before `record_closes()`, so if the ledger append fails, the landing step is recorded for an agent that is then refused. Recording `closes:` first would make the refusal leave nothing behind. {robustness S low}

**What's done well.** The ledger append was split into `_append_ledger()`, so the new row is written under the same lock, the same way, as every other ledger line. Unreadable lines are skipped, and parsing `closes:` items errs towards including more (`#12` and `12` are both kept).

**What I checked.** I read the intent, the plan, `decisions.md`, the full diff and the gate record. Attempt 1 failed in `test_prompts.py` because the new ledger read wasn't stubbed there. The diff stubs `recorded_closes` in `test_prompts.py`, and attempt 2 passed: 3950 passed, 29 skipped, and the plugin validated. I ran only read-only greps; I didn't run the tests myself.
