# Notes

- [x] The board could read the run lock (`sdlc-factory-train-run.lock`) to say a landing is running unattended, rather than inferring it from `runs/land-step.md` alone; the spec left the board unchanged. → seed: 2026-11-18-66
- [x] `test_a_killed_train_run_resumes` kills a process group, so it doesn't run on Windows; a Windows kill test would need `CREATE_NEW_PROCESS_GROUP` and `taskkill /T`. → seed: 2026-11-18-67
