# Decisions

- [ ] D1 (builder round 1, default): Run CI's Linux job with `-n auto` too, and leave Windows serial? Going ahead with that: the Linux runners have 2 to 4 cores, which still helps, and the Windows job passes either way.
- [ ] D2 (builder round 1, default): Scan through git rather than adding `.sdlc/reports` to the skip list? Going ahead with git, as the Approach says, because it covers any ignored local output, not just that folder.
- [ ] D3 (builder round 1, default): Is it acceptable to edit the factory's gate record by hand to remove a home path? Going ahead: the file ships in this public repo, and only the copied output changed, not the attempt's record lines. The lasting fix is the `factory.py gate` change in notes.md.
