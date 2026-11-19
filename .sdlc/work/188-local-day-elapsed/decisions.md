# Decisions

- [x] D1 (builder round 1, default): Keep `new` stamping `created:` as the local day (the intent's open question). Going ahead with local unless told otherwise. → settled by the approver: the intent's own Approach (intent.md, line 66) fixes the measurement and leaves the stamp alone, and none of its Outcomes needs `new` to change. The built code (`scripts/closing.py: _day_start()`) follows this and changes nothing about what a host's `created:` means. Moving `new` to stamp in UTC would change a host-facing date and would need its own change, which the person can still start from the intent's open question.
  - OPTION: local day, measured from local midnight — what a host's dates mean today; this fix makes elapsed correct with no change to `new`
  - OPTION: stamp `created:` in UTC — every date in the record on one clock; changes what an intent's date means for every host, and older intents would mix the two
  - WHY: the intent's Approach fixes the measurement rather than the stamp, and changing the stamp would change what a host's dates mean.
