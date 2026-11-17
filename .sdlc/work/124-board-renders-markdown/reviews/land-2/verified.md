- KEPT: ui: C1: scripts/board.html:138: `.md .md-h1` is 20px and the drawer title (`.d-head h3`, line 113) is 15px. An `intent.md` opening with `# 124 — …` therefore outranks the drawer title.
- KEPT: ux: C2: scripts/board.html:323: the task checkbox is a disabled input with no `aria-label` and no wrapping label. The item's text is a sibling, so a screen reader announces only "checked checkbox".

## Notes
I read the CSS at lines 112–145 and `mdList` at lines 291–326, and grepped for `aria-label` and `md-task`. The only `aria-label` uses are on other elements, never on the task checkbox. I ran no tests and did not render the page. For C1, a render would show whether the drawer title appears above the file view at the point the `#` heading shows. That does not change the computed font sizes.
