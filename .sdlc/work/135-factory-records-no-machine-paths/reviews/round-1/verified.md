The filed reply is scrubbed at line 3387 before `read_evidence()` reads it, and I reproduced the defect directly.

- KEPT: code: C1: plugins/factory/scripts/factory.py:1348: `is_read()` tokenises `<home>` as a redirect, so a read that names a home path and has no `exit:` line is judged a non-read and costs a mend

## Notes
- I ran `is_read("ls ~/.nvm/bin")`, which returned True, and `is_read("ls <home>/.nvm/bin")`, which returned False.
- I read `_placeholders()`, which files `<home>` in place of the home directory, and its call at line 3387, which scrubs the reply before `read_evidence()` sees it.
- I did not run the repo's test suite.
