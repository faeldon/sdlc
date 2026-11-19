
Resolved:

- **What is the row shape?** JSON Lines. Each row needs `name` and a numeric `value`, may have `unit`, and is identified by `(name, unit)`. Other keys are kept as `extra`, unrendered, so a host can extend the shape without the plugin judging it. `band` is left out on purpose (see *Alternatives rejected*). This is a proposal: your yes to the spec settles it.

Left for you:

- **The report runs `retro.indicators`, and only that** (*Contracts touched*, first bullet). This overturns the pinned "the report runs no host command". A yes to this spec takes it. With a no, the table can't be in the report: R4–R9 go, and the figures stay in `retro`'s JSON only.
- **Does setup offer the key on every update, or only when it isn't set?** The draft offers it only when `retro.indicators` is empty, and only when setup reaches its drafts (a first setup, or a repo that isn't `complete`). Asking on every update would mean adding a `readiness` item. That item would hold `complete` false until the key is set, so a host that wants no indicators would be asked on every update, since an empty list records no "none". To ask once and remember the answer, `load_config` would have to tell an unset key from an explicit `indicators = []`, which is a new distinction in how config is read.
