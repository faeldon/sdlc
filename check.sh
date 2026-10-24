#!/usr/bin/env bash
# Everything that says whether this plugin is correct. Fail-fast: a step that fails stops the rest,
# so a green finish means every step ran and passed.
set -euo pipefail
cd "$(dirname "$0")"

uv run --quiet --group dev ruff check .
uv run --quiet --group dev ruff format --check .
# No tolerance for pytest's exit 5 ("no tests collected"): discovery breaking is a red gate.
uv run --quiet --group dev pytest -q
# The sdlc plugin and the marketplace live in one folder here, so one validate covers both. The
# optional factory is a plugin of its own.
claude plugin validate --strict .
claude plugin validate --strict plugins/factory
