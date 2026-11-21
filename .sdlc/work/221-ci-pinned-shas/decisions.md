# Decisions

- [x] D1 (approver round 1, look): `.github/workflows/check.yml` and `.github/dependabot.yml` — the change touches a sensitive path. Check that the two pins, `11d5960a…` (checkout v4.4.0) and `d0cc045d…` (setup-uv v6.8.0), are what you want CI to run. Confirm Dependabot's weekly PRs are wanted. R4 can only be seen on the pushed commit's CI run. → decided: seen
- [x] R1 (person, restart): rewrite R4 as checkable outcomes and glob *.yaml too
