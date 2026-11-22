# Decisions

- [x] D1 (builder round 1, default): Refuse `[park] exit = 0` and `= 1` with a warning (the value is dropped and nothing parks), rather than only warning and still parking on it. Going ahead with refusing unless told otherwise. → settled by the approver: The intent's Approach says to refuse `[park] exit` of 0 and 1, and its *Contracts* line names `[park] exit` and accepts the narrowing. The code reviewer confirmed the refusal sits in `_park()` with the other bad `[park]` values, so the person approved this before the build.
  - OPTION: refuse with a warning — a red check can never become a wait; a host that set 1 gets no parks until it changes the value
  - OPTION: warn only, still park — the host's value is honoured; every ordinary red gate becomes a wait, the problem the nit raised
  - WHY: the intent's Approach says refuse, and other bad `[park]` values are already handled this way.
- [x] D2 (builder round 1, default): `park --clear` removes an unvouched record even before its recorded deadline. Going ahead unless told otherwise. → settled by the approver: The intent's Outcome allows `park --clear` to remove an unvouched record. The code reviewer found the change limited to records the ledger never vouched for. `verdicts` already treats such a record as a stop to rerun, so no real park is lost.
  - OPTION: remove whatever its deadline — no reader takes it as a park, so nothing real is lost
  - OPTION: remove only once expired, and name the `rm` in the refusal — keeps the old rule; the person still has to delete a record that never counted
  - WHY: `verdicts` already treats an unvouched record as a stop to rerun, never a wait.
