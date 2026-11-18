# Decisions

- [x] D1 (builder round 1, default): Leave a host's own git config (`log.showSignature=true`) uncovered by `is_read()`? Options: leave it uncovered and say so at the table; make every `git log`/`git show` without `--no-show-signature` a non-read. Going ahead with leaving it uncovered: the command can't show it, and the other option would turn every git log read into a mend. → decided: the assumed default, confirmed when landing
