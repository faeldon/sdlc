# Decisions

- [x] D1 (builder round 1, default): With no remote-tracking ref for the base branch, count every commit on the base branch as unpushed, so an issue any commit there closes is never unmarked. Options: whole base branch; unmark nothing at all. Going ahead with the whole base branch unless told otherwise: it stays cautious and still unmarks in a repo with no fetched remote. → decided: the assumed default, confirmed when landing
