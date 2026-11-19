VERDICT: PASS

The wrap-only edits, the `check.sh` note and the `heat()` comment all do what intent.md asks. The land-3 conflict in AGENTS.md was resolved correctly. I ran no tests and did not rerun the gate: its record (`build/land-3.gate.md`) says `GATE: PASS`.

## Notes
- The rebase kept base 172's new wording ("the board, close and retro reach `factory_records.py`") and 173's 100-column re-wrap. No conflict markers are left in AGENTS.md or the factory README.
- Added lines in the diff stay within 100 columns. The README lines still over 100 are a diagram, table rows and a file listing, all outside what intent.md names.
- The `check.yml` change only re-wraps comments. The `check.sh` comment answers nit -76. The `heat()` comment answers nit -108.
- NIT: plugins/factory/README.md:51: diagram and table rows run past 100 columns, which a prose re-wrap can't fix; leave them {style M low}
- Done well: the rewrap is faithful, and the land-3 resolution preserved both sides' intent.
