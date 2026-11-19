
**Open questions**

I answered one from the brief and the code, set defaults for the other two, and found two new questions only you can settle.

**Answered:**
- **Is the inventory read from `docs/FEATURES.md`, or built from the code and checked against it?** Built from the code (`COMMANDS`, `CONFIG_KEYS`, the skill folders, and `factory.py`'s `@command` names). `tests/test_feature_map.py` checks FEATURES.md against the same code. The intent's own constraint decides this: "built from the code, never kept by hand".

**Defaults I chose, which you can change:**
- **What is N, the windows unused before an item is a retire candidate?** I used `RETIRE_AFTER = 3`. Windows where an item had no record don't count toward the run.
  - A smaller N names candidates sooner, but one quiet window can be noise. In this repo a window is about two releases.
  - A larger N waits longer before naming a candidate.
- **Do hosts get a copy of either map from setup?** I designed for no: it would add to every host's footprint and to what `drift` has to track under `irreversible` paths.
  - Yes would mean a `defaults/` copy, a `[docs]` key, a `sdlc.py record` run, and a migration for hosts that already ran setup.

**Only you can decide:**
- **Can core read the factory's skill folders and `factory.py`'s command names?** This is a new crossing that AGENTS.md's factory paragraph would have to list.
  - Yes keeps R3, and the inventory covers both plugins.
  - No drops R3, and the inventory is core only.
- **Should `surface` appear in a host's retro?** The scorecard says the plugin's own surface "is this repo's measure alone". This draft reports skill, command and key use, and the footprint, in hosts too, and limits only growth to this repo, because use in a host is what O5 most needs.
  - If you'd rather follow the scorecard, the whole `surface` block is `null` in a host with a `why`, and the scorecard's sentence stands.
