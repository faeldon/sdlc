"""`uv run --script`, as the skills run a script, for the tests that start one in a subprocess:
the adoption tests and the train's handed-off close. Not a test module: imported by those that
need it, as `train_driver.py` is."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

# uv's own error when it couldn't reach the package index, printed before the script runs.
UNREACHED = re.compile(r"error: (request failed after|failed to fetch|failed to download)", re.I)
# uv's words, run `--offline`, for a dependency its cache doesn't hold. Several, since uv has
# worded it more than one way, and a wording it adds later should skip, not fail the gate.
UNCACHED = re.compile(
    r"network (was|is) disabled|offline|not found in the cache|no solution found", re.I
)


def uv_script(
    script: Path, cwd: Path, args, env: dict, timeout: float | None = None
) -> subprocess.CompletedProcess:
    """`uv run --script`, as the skills run it. When uv can't reach the package index (no network,
    as on a gate whose machine lost its DNS), the script never ran, so it runs once more from the
    packages uv's cache holds; with none there, the test skips naming the network. With the
    network up nothing changes: a dependency the script doesn't declare still fails it."""

    def run(*flags: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["uv", "run", "--quiet", *flags, "--script", str(script), *args],
            cwd=cwd, capture_output=True, encoding="utf-8", env=env, timeout=timeout,
        )  # fmt: skip

    ran = run()
    if ran.returncode == 0 or not UNREACHED.match(ran.stderr):
        return ran
    cached = run("--offline")
    if cached.returncode != 0 and UNCACHED.search(cached.stderr):
        first = ran.stderr.splitlines()[0]
        pytest.skip(f"no network: the package index can't be reached ({first}), and uv's cache "
                    "lacks the script's dependencies")  # fmt: skip
    return cached
