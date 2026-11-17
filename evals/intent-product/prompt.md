---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit]
---
/sdlc:intent Let a saved draft be reopened. Problem: drafts.py saves a draft and lists titles, but nothing gives a saved draft's text back, so it can't be reopened to keep writing. Outcome: drafts.reopen(title) returns the saved text, None for an unknown title. Affected: drafts.py only; nothing reads it yet. Constraints: save() and titles() unchanged. No open questions.
