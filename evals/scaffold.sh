#!/bin/sh
# Builds a case's host repo in the empty workspace: fixtures/base committed on main, then, for a
# named fixture, its `change/` added on the branch its `branch` file names, uncommitted as a change
# is before /sdlc:ship, or committed with the message in its `commit` file. A fixture with a
# `worktree` file is moved into .claude/worktrees/<branch>, leaving the workspace on main, as
# /sdlc:close finds it. A fixture with an `extends` file gets that fixture's `change/` first, then
# its own on top. `fresh` is the base alone. Plain sh and git only: a scaffold runs outside
# the sandbox, with a minimal PATH.
#
# With `--sandbox`, which only the cases pass, it also readies uv in the run's temporary home,
# where the agent's sandbox has no network: a uv config there (read by every uv the run starts)
# makes uv use a Python it installed itself, never macOS's /usr/bin/python3 shim, which can't run
# in the sandbox, and an offline cache in the workspace, warmed here by running the script once.
# Never without the flag: the tests run this with the person's own HOME.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
commit() { git -c user.name=eval -c user.email=eval@example.invalid commit -q "$@"; }
git init -q -b main
cp -R "$here/fixtures/base/." .
git add -A
commit -m "Start"
if [ "$2" = --sandbox ]; then
  echo ".uv-cache/" >> .git/info/exclude
  mkdir -p "$HOME/.config/uv"
  printf 'cache-dir = "%s/.uv-cache"\npython-preference = "only-managed"\n' "$(pwd)" \
    > "$HOME/.config/uv/uv.toml"
  uv python install --quiet 3.12
  uv run --quiet --script "$here/../scripts/sdlc.py" config > /dev/null
  printf 'offline = true\n' >> "$HOME/.config/uv/uv.toml"
fi
[ "$1" = fresh ] && exit 0
src="$here/fixtures/$1"
[ -f "$src/branch" ] || { echo "no fixture $1" >&2; exit 1; }
branch="$(cat "$src/branch")"
git checkout -q -b "$branch"
[ -f "$src/extends" ] && cp -R "$here/fixtures/$(cat "$src/extends")/change/." .
cp -R "$src/change/." .
[ -f "$src/commit" ] || exit 0
git add -A
commit -m "$(cat "$src/commit")"
[ -f "$src/worktree" ] || exit 0
git checkout -q main
git worktree add -q ".claude/worktrees/$branch" "$branch"
