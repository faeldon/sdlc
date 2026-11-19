# Decisions

- [x] D1 (builder round 1, default): Keep the agents' frontmatter `description:` lines on one line, though idea -81 names them. Going ahead unless told otherwise. → settled by the approver: the intent's Outcome asks each named line to wrap near 100 columns "as its file does", and its Constraints say "Rewrap only" and "No behaviour changes". Every agent file keeps its frontmatter `description:` on one line, and the harness reads that value, so wrapping it would change what Claude Code parses rather than rewrap prose. The round-1 code and security reviews both agree with this default, and `checks.md` leaves `description:` lines out on purpose.
  - OPTION: one line — matches every core and factory agent and skill, and keeps the YAML simple; those lines stay past 100
  - OPTION: wrap as a multi-line YAML value — meets -81 literally; no other agent in the repo does this, and it risks how Claude Code reads the description
  - WHY: no behaviour may change, and a frontmatter value the harness reads differs from a prose rewrap
- [x] R1 (person, fix): rewrap AGENTS.md:74, the line 169's edit made 113 columns, to under 100
