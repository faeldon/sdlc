# Decisions

- [x] D1 (builder round 1, default): Don't read flow-mapping `uses:` (`- { uses: a/b@v4 }`), the intent's open question. Going ahead without it unless told otherwise. → settled by the approver: The intent's Approach leaves flow-mapping `uses:` out. Its Affected section says nothing outside `tests/test_ci.py` reads the check. The intent also notes that no workflow here writes that form, and the behaviour reviewer found the default consistent with the Approach.
  - OPTION: leave it out — no workflow here uses that form and the check stays simple; a pin written that way would not be checked at all
  - OPTION: read it too — covers every form; adds a pattern for a form nobody writes here
  - WHY: no workflow in this repo uses that form, and the intent's Approach doesn't include it
