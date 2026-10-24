---
# milestone: tracker
# project: [Roadmap]
# assignees: tracker
---

# Project

> Which issue fields the sdlc plugin fills on each change's issue, and where each one's values
> come from. Uncomment a field in the frontmatter above to turn it on; one left commented out is
> off. Each value is one of:
>
> ```
> tracker          the tracker's own list (GitHub: open milestones, the owner's projects,
>                  people who can be assigned)
> [a, "b c"]       a fixed list: only these
> any other text   a command, run from the repo root, printing one value per line;
>                  {field} is the field's name
> ```
>
> A field that's on is mirrored exactly: the intent's frontmatter decides it, and edits made on
> the issue itself are overwritten at the next sync. The sections below say how to choose.

## Milestones

<Which milestone a change goes in: by release, by quarter, or something else. What decides it.>

## Projects

<Which project a change belongs on, when there is more than one.>

## Assignees

<Who is assigned: whoever opens it, an owner per area of the repo, a rota. Who to ask when unsure.>
