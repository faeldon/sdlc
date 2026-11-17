#!/bin/sh
# serve.sh <fixture> <port>: the board this checkout's own scripts/sdlc.py serves on <port>, over
# a scratch repo built inside <fixture>, the copy of changes/ that `factory.py shots` made for this
# shot (`[ui] serve` in .sdlc/factory.toml). Runs until stopped.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
sh "$here/build.sh" "$1" "$1/drafts"
cd "$1/drafts"
exec uv run --quiet --script "$here/../../../scripts/sdlc.py" board --port "$2"
