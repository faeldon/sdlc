
**Resolved from the code**

- **Should the nudge ask `drift`, or should setup re-record the version?** The nudge asks `drift`, and only when the recorded version is behind. `drift()` already compares against the last record's hashes, so leaving the record behind loses nothing. `readiness`'s `complete` already uses the same rule, so the two can't disagree once both call `drift_pending()`. No write is added, which keeps the constraint that setup writes nothing before its question. The cost: while the record is behind, `status` and the hook run drift's local reads (Contracts touched, *Updates*). If you'd rather keep the hook to a strict file read, the other way is a record written behind a question (Alternatives rejected).
- **If setup re-records, is it a question or a named exception?** No longer applies: setup doesn't re-record.
- **Does the hook print the setup line every time, or only when there's no release line?** Only when there's no release line. `update_report()`'s steps end with `/sdlc:setup`, so a release line already leads to setup, and the hook stays one line.

**Left for you**

- **Which skills pass `■ Setup` on?** The spec picks `/sdlc:status` and intent's Step 0 (R10).
  - **These two only:** two prose edits. The person hears it at session start (the hook), when they ask what needs them, and when new work starts.
  - **Every skill that runs `status`:** `spec`, `ship` and `idea` also get the rule and the test. The line then also lands mid-ship and mid-spec, where it is unrelated to the task.
- **Is the hook's extra cost while the record is behind acceptable?** That cost is local reads plus one cached git call, at every session start, until a release changes something and setup records. If not, the other way is to write the record on setup's `complete` stop. That needs a question, and it leaves a one-file commit for every release that changed nothing.
