
- **Resolved: does a red base stop an auto landing?** Yes. The intent's Outcome says the landing shows it "as a signal", and its Downstream line says "a new signal can stop a batch that was `clear`". In `land_signals()`, any signal makes `clear` false (`cmd_land_check()`, `landing.py`). R9.
- **Resolved: which commit counts as the tip?** The remote-tracking ref (`refs/remotes/<release.remote>/<git.base>`), read locally as `_unpushed()` does. CI never ran on unpushed commits.
- **Resolved: what is red?** A completed run concluded `failure`, `timed_out` or `startup_failure`. Anything else that can't be read is `unknown`, from the intent's Constraints. R1.
- **Partly resolved: where the reading lives and how often it refreshes.** The code points to `UPDATE_CACHE`'s pattern, and this spec follows it: `sdlc-ci.json` in the git common dir, read again every 10 minutes for `status` and every 60 s for a landing. **Left for you:**
  - **Approve the policy edit in Contracts:** `status` and `preflight` write that cache with no WAIT. This is the spec's design and the only way `status` can show a fresh reading.
  - **Or keep the "one write" rule:** the landing reads fresh and writes nothing. `status` then shows nothing, or only a reading another command cached, and the first Outcome is lost or weakened.
- **Left open: which runs count, every workflow on the tip or a configured one.** This spec counts every workflow run on the tip's sha.
  - **No key (this spec):** no new config key, no `READS_CONFIG`, `setup`/drift or REFERENCE change. The cost is that a flaky optional workflow turns the base red.
  - **A configured list** (e.g. `[ci] workflows`): a new config key, with its default, docs, drift record and setup question. Better for a host with many workflows, but more than the intent asked for.
