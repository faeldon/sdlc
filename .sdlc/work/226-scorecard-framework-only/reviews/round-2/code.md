VERDICT: PASS

Both changes kept last round were made, and nothing new turned up.

- The Hosts section (`docs/RETRO-SCORECARD.md:465`) now reads "The scorecard reaches hosts by way of the plugin, and each part goes where a host already finds its kind:". It has no seed ids and no future tense.
- A grep for `S<n>` ids and `(S…)` parentheticals finds nothing left in the prose. The "captured (S10, 175)" parentheticals and the lead-time "(S1)" are gone.

## Notes
- Done well: the Status lines now state the current state directly, and the plan table and the "S1/S10 done" lists are removed.
- I did not re-run the gate. Its record at `build/round-*.gate.md` ends with "Validation passed" (the last round-file I tailed). I ran no tests.
