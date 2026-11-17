# Notes

- [x] `file` is on R1's plain-read list, but `file -C -m <magic>` compiles a magic file and writes → seed: 2026-11-18-1
  `<magic>.mgc`. A later change could give `file` its own condition (no `-C`) the way `sort` has
  one; left as the spec lists it here.
- [x] `is_read()` keeps a descriptor digit before a redirection (`2>&1`, `2>/dev/null`) as an → dropped: no condition in `is_read()` counts arguments today, and the extra token can only make a command a non-read (at most one mend), never the reverse.
  argument of its command, since `shlex` drops the spacing that tells `x 2>f` from `x 2 >f`. It
  never makes a non-read a read (the redirection is judged on its own), but a program condition
  that counts arguments would see one more.
