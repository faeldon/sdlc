# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The Waves section names every entry open at writing exactly once

The ids stay in the doc after their entries retire, so only a deliberate edit of the plan fails it.

```sh
w=$(awk '/^### Waves/{f=1} f' docs/RETRO-SCORECARD.md) && test -n "$w" && for id in 2026-10-24-6 2026-10-25-1 2026-10-25-23 2026-10-25-3 2026-10-26-10 2026-10-26-11 2026-10-26-13 2026-10-27-10 2026-11-10-2 2026-11-13-1 2026-11-18-100 2026-11-18-101 2026-11-18-103 2026-11-18-104 2026-11-18-105 2026-11-18-107 2026-11-18-108 2026-11-18-109 2026-11-18-64 2026-11-18-65 2026-11-18-66 2026-11-18-67 2026-11-18-68 2026-11-18-69 2026-11-18-70 2026-11-18-71 2026-11-18-74 2026-11-18-75 2026-11-18-76 2026-11-18-77 2026-11-18-78 2026-11-18-79 2026-11-18-80 2026-11-18-81 2026-11-18-82 2026-11-18-83 2026-11-18-84 2026-11-18-85 2026-11-18-86 2026-11-18-87 2026-11-18-88 2026-11-18-89 2026-11-18-90 2026-11-18-91 2026-11-18-92 2026-11-18-93 2026-11-18-95 2026-11-18-96 2026-11-18-97 2026-11-18-98 2026-11-18-99 2026-11-19-1 2026-11-19-2 2026-11-19-3 2026-11-19-4 2026-11-19-5 2026-11-19-6 2026-11-19-7 2026-11-19-8 2026-11-19-9 ; do n=$(printf '%s\n' "$w" | grep -oE "(^|[^0-9-])$id([^0-9]|$)" | wc -l); test "$n" -eq 1 || { echo "$id named $n times"; exit 1; }; done
```

## The suggested order gave way to the waves, and S17 joined the Data table

The old section's heading and the new row are text only a revert brings back or takes out.

```sh
! grep -q '^### Suggested order' docs/RETRO-SCORECARD.md && grep -q '^| \*\*S17\*\* | Comment health' docs/RETRO-SCORECARD.md && grep -q '^| \*\*S5\*\* .*2026-10-25-3' docs/RETRO-SCORECARD.md && grep -q '^#### Wave 6' docs/RETRO-SCORECARD.md
```
