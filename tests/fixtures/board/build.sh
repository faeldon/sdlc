#!/bin/sh
# build.sh <changes> <dir>: a scratch repo at <dir>, new, for `sdlc.py board` to show. Each folder
# of <changes> becomes a change on its own branch, in its own worktree under .claude/worktrees/,
# and each change `gates` names gets a current hand-gate record (`sdlc.py gate`) that passes or
# fails as it says. The commits are the scratch repo's alone, by a `fixture` identity; <changes>
# is only read. The board fixture's data for the UI review (`[ui] fixture` in .sdlc/factory.toml),
# and for tests/test_board.py.
set -eu
changes=$(cd "$1" && pwd)
dir=$2
here=$(cd "$(dirname "$0")" && pwd)
sdlc="$here/../../../scripts/sdlc.py"
if [ -e "$dir" ]; then
  echo "build.sh: $dir already exists; it builds only a new repo" >&2
  exit 1
fi

g() {
  git -c user.name=fixture -c user.email=fixture@example.invalid -c commit.gpgsign=false "$@"
}

mkdir -p "$dir/.sdlc"
cd "$dir"
g init -q -b main
# The hand gate fails where a change leaves a RED file, and passes elsewhere.
printf '[commands]\ncheck = "test ! -e RED"\n' > .sdlc/config.toml
printf '.claude/\n' > .gitignore
printf '# Drafts\n\nA repo whose board shows a change in every state.\n' > README.md
g add -A
g commit -q -m "A repo of drafts"

for src in "$changes"/[0-9]*-*/; do
  name=$(basename "$src")
  tree=".claude/worktrees/$name"
  g worktree add -q -b "$name" "$tree" main
  mkdir -p "$tree/.sdlc/work"
  cp -R "${src%/}" "$tree/.sdlc/work/$name"
  verdict=$(sed -n "s/^$name //p" "$changes/gates")
  if [ "$verdict" = fail ]; then
    printf 'red\n' > "$tree/RED"
  fi
  g -C "$tree" add -A
  g -C "$tree" commit -q -m "$name"
  if [ -n "$verdict" ]; then
    (cd "$tree" && uv run --quiet --script "$sdlc" gate "$name" > /dev/null) || true
  fi
done
