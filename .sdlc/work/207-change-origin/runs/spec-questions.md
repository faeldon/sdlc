
Resolved:
- **Values: are `host` and `self` enough?** Yes, two values (R1). A filed GitHub issue isn't its own
  origin: `closes:` and `Sdlc-Triaged` already record it, and the finding behind an issue came from
  a host or from here like any other. Findings from a retrospective, a review or a nit are `self`:
  they came from working on this repo.
- **Does the retro count seeds by origin?** No, only landed changes, as the Outcome says. A seed's
  `Origin:` reaches the count through the intent that takes it (R10). This is under *Alternatives
  rejected*.
- **Per-host breakdown?** Out of scope. The Constraints say the line never names a host, and an
  opaque label would need a gitignored mapping that the retrospective, which reads history alone,
  couldn't read.

Left for the person:
- **Every host, or this repo only?** The draft offers the line to every host: proposed on every
  intent, `self` when nothing points elsewhere, and named in Step 4's question. That way unknown
  and `self` can be told apart from now on. The cost is that a host whose changes always come from
  its own work gets `origin: self` and `, found here` on every change. The other choice is a config
  switch (see *Alternatives rejected*): no noise for hosts, but a new key and a setup question,
  which the intent's Constraints rule out unless you lift them. A third choice is proposing the
  line only when the account says `host`, which adds no noise but leaves `self` and unknown the
  same.
- **206 gets `origin: host` by hand before it ships?** It's a one-line edit on 206's own branch
  once this lands. Only you can say whether 206 should be the first data point or the window should
  start clean. It isn't part of this change's diff either way.
