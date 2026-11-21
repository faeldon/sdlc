# Decisions

- [x] D1 (builder round 1, default): Accept that the hook runs drift's local file reads (plus one cached git call) at session start while a repo's setup record is behind, beyond the intent's "a file read". Going ahead with it unless told otherwise. → decided: the assumed default, confirmed when landing
  - OPTION: accept it — no new write, the cost only applies until setup next records, and it's the same work `status` already does; a current record is still one file read
  - OPTION: have setup re-record on its `complete` stop — keeps the hook to one file read, but adds a write before a WAIT and a commit for every release that changed nothing
  - WHY: the spec's Contracts section flags this for the person to accept, and its Alternatives rejects re-recording
