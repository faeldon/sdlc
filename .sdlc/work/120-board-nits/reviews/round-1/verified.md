- KEPT: ux: C1: plugins/factory/scripts/factory.py:1990: `WAYS_WHY["mend"]` is new text in this diff and says "mends it once", the word intent 120 removes from the needs-you line. Reword it in plain terms, for example "Rerunning /sdlc-factory:build {id} asks an agent again, once, for the reply in its shape".

## Notes
I read `intent.md` and the `factory.py` diff. I ran no tests. The line is 1990, not 1985 as the change says; `"mend"` starts at 1988 and "mends it once" is on 1990. The same text is the drawer's body from `stop_text()`, so the jargon does reach a person. Nothing was uncertain.
