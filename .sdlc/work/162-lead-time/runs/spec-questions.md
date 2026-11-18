
Resolved:
- **Where the start time lives:** a new `opened:` line, written by `new` itself (not the template), as `YYYY-MM-DDTHH:MMZ` UTC. `created:` stays a date for its readers and history.
- **Transcripts or run files at close:** run files and git first. The factory's `costs.jsonl` rows gain `started` and `ended`, and its `land-times.jsonl` rows gain `since`. Transcripts are only the fallback for older rows and for hand-built work.
- **"Agents working" for a hand-built change:** transcript turn and sub-agent time when read at close. Without transcripts, `lead` and `ready_wait` alone (`source=git`), never zeros.
- **Where it shows in the report:** inside the existing `{{cycle}}` value, so `templates/retro.md` isn't edited.
- **A hand-built change's ready time:** the ship commit's author date, as you chose.
- **A filed issue's lead time:** it starts at `new`. The wait from the filing stays out of scope, as you chose.
- **Recomputing 139–157:** dropped, as you chose (c). The fixture tests prove the arithmetic and each source. The intent's outcome line about it no longer applies.

Left for the person:
- None.
