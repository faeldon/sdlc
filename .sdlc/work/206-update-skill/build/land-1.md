I resolved `tests/fixtures/close-output.json` by taking the `HEAD` side (the change landed before it) in every conflict hunk. I did not run a test, so the merge is checked only by the file parsing as JSON.

**What each side contributed**
- **`HEAD` (207's masked fixture):** `Sdlc-Runtime: plugin=<version>`, which I kept in every hunk.
- **206's side:** it had re-recorded the line as `plugin=1.11.0`, which I dropped. This follows the memory note to land 207 before 206, keep 207's masked fixture and drop 206's re-record. 206's own commit message says the same: it dropped the re-record because 207 fixes the release-bump breakage.

**Left short:** nothing in 206's spec is affected. The fixture was incidental to 206, not part of what it was built to do.

**Noticed and left alone:** nothing.

## Evidence

$ python3 (regex keeping the HEAD side of each conflict hunk in tests/fixtures/close-output.json)
exit: 0

$ grep -c '<<<<<<<\|>>>>>>>\|=======' tests/fixtures/close-output.json
0
exit: 1

$ grep -c 1.11.0 tests/fixtures/close-output.json
0
exit: 1

$ python3 -c "import json;json.load(open('tests/fixtures/close-output.json'))"
exit: 0
