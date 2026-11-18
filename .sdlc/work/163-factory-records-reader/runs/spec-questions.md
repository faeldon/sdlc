
**Resolved**
- *The module's name and boundary.* `scripts/factory_records.py`, bound in `sdlc.py` as `factory_records`. It holds both the parsing and the readers that open a change folder's files on disk. It is pure like `metrics.py`: no subprocess and no `sdlc` binding. Reads from git history come in through `show` and `listing` callables, so the git calls stay with their owners: close's adapters in `closing.py` and `history_samples` in the board. This follows from `metrics.py`'s precedent in AGENTS.md and from `_factory_files` already being built on `sdlc._git(… "show" …)`.
- *Whether `board.py` reads it directly or through `sdlc`'s binding.* Through the binding, as `sdlc.factory_records.<name>`. `sdlc.py` loads the module eagerly because `status` needs it on every run (`print_status`'s reading at `sdlc.py:10016–10053`), and one load means one module object for stand-ins.
- *Whether `seen_stage`, `needs_of` and `column` move.* They stay in `sdlc.py`, along with `answered`, `decide_step`, `BY_STAGE` and `FACTORY_STOP_NEEDS`. They are core's rules over fields and read no record (`seen_stage` reads `findings.md` and git). R4 pins this.
- *`_hand_placeholders`, which the intent lists.* It moves as `placeholders(text, root, main)`. Its one `git worktree list` call stays in `sdlc.py`, so the module stays pure.
- *Slot and `[ui]` copies.* Out of scope: they copy `factory.toml` and the gate locks, not a run's records.

**Left for you**
- *Add `scripts/factory_records.py` to `[review] sensitive`?* Its parsers feed close's measure trailers.
  - **Yes:** every future change to a record's shape gets full-depth review with the security reviewer, even when it doesn't touch `closing.py`.
  - **No (my lean):** it's treated like `metrics.py`, which isn't listed either. This change is reviewed at full depth anyway, because it touches `closing.py`.
- *Byte-identical check for `/state.json`.* R8 relies on the existing board tests plus a review that no expected value changed in the `tests/` diff.
  - **Accept that:** no new work.
  - **Add a recorded snapshot:** a `/state.json` and `status --all` snapshot from the base branch, diffed in the build with clock fields masked. It's stronger evidence but a one-off script for this change only.
