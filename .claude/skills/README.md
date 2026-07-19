# DriveWise AI — Claude Code Skills

Project-level [Agent Skills](https://code.claude.com/docs/en/skills) generated from `main.md` (challenge spec) and `architecture.md`. Claude Code loads each one **on demand** when a task matches its description, so the team gets consistent, project-aware help without bloating every session's context (that's what `CLAUDE.md` is for).

## Install

Copy the four skill folders into your repo's `.claude/skills/` directory and commit them — everyone who clones the repo then gets them automatically:

```
your-repo/
└── .claude/
    └── skills/
        ├── drivewise-architecture/SKILL.md
        ├── drivewise-data-model/SKILL.md
        ├── drivewise-ai-recommendations/SKILL.md
        └── drivewise-scraper/SKILL.md
```

If you unzip the provided archive at the repo root, it already places them there. In a running Claude Code session, run `/reload-skills` to pick them up (a brand-new top-level `.claude/skills/` may need a session restart), and `/skills` to confirm they're listed.

## The skills

| Skill | Triggers when you're working on… |
|---|---|
| `drivewise-architecture` | where code belongs, layer boundaries, stack choices, data flow |
| `drivewise-data-model` | the PostgreSQL schema, SQLAlchemy models, Pydantic schemas, queries |
| `drivewise-ai-recommendations` | requirement extraction, ranking logic, recommendation explanations |
| `drivewise-scraper` | collecting/cleaning external vehicle data into the catalog |

You can also invoke any of them explicitly, e.g. `/drivewise-data-model`.

## Keeping them honest

The skills defer to the repo as source of truth in this order: `CLAUDE.md` → `docs/api-contract.md` → the skill. If you change a layer boundary, a table, or an endpoint, update the matching skill in the same change so it doesn't drift.
