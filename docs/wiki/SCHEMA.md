# Wiki Schema

This file tells the LLM how to maintain the Smart Meter Simulator wiki. It is the key configuration file that makes the wiki disciplined rather than chaotic.

## Purpose

This wiki is a **persistent, compounding knowledge base** for the GridTokenX Smart Meter Simulator project. It lives between raw source code and the LLM agent — already synthesized, already cross-referenced, already current.

## Directory Structure

```
docs/wiki/
├── SCHEMA.md              ← This file (wiki maintenance conventions)
├── index.md               ← Content-oriented catalog of all wiki pages
├── log.md                 ← Append-only chronological record of changes
├── entities/              ← Concrete things: classes, services, components
├── concepts/              ← Abstract ideas: algorithms, protocols, patterns
├── protocols/             ← Communication protocols and data formats
├── markets/               ← Market mechanisms, tariffs, economic models
├── integration/           ← External systems and infrastructure
└── reference/             ← Specifications, benchmarks, constants
```

## Page Conventions

### Naming
- **Kebab-case filenames**: `state-estimation.md`, `vpp-dispatch.md`
- **Title-case H1**: `# State Estimation`
- **One concept per file** — if a file exceeds ~200 lines, split it

### Frontmatter (YAML)
Every page MUST start with:

```yaml
---
title: "Human-Readable Title"
category: entities|concepts|protocols|markets|integration|reference
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/core/engine.py", "docs/architecture/simulation-engine.md"]
tags: [core, engine, simulation]
related: [[another-page]], [[yet-another]]
---
```

### Page Structure
1. **Summary** — 2-3 sentence overview (what is this?)
2. **Details** — technical deep-dive (how does it work?)
3. **Key Parameters** — table of configuration/constants
4. **Relationships** — links to related pages, dependencies
5. **Known Issues** — caveats, edge cases, TODOs

### Cross-References
- Use `[[page-name]]` syntax for internal links (Obsidian-compatible)
- Every page must have inbound links (no orphans)
- Update cross-references when creating new pages

## Workflows

### Ingest (New Source Added)
1. Read the new source (code file, doc, spec)
2. Identify which existing wiki pages need updating
3. Create new pages for new concepts/entities
4. Update `index.md` with new entries
5. Append entry to `log.md` with format: `## [YYYY-MM-DD] ingest | Source Name`
6. Flag any contradictions or stale claims found

### Query (Answer a Question)
1. Search `index.md` for relevant pages
2. Read and synthesize an answer
3. **File the answer back as a new wiki page** if it's substantial (analysis, comparison, decision record)
4. Update `log.md`: `## [YYYY-MM-DD] query | Question Summary`

### Lint (Health Check)
Run periodically. Check for:
- **Contradictions** — conflicting claims between pages
- **Stale claims** — outdated by newer sources
- **Orphan pages** — no inbound links
- **Missing pages** — concepts mentioned but not documented
- **Data gaps** — where a web search could fill in

### Update (Code Changed)
1. Identify affected wiki pages via `sources` frontmatter
2. Update pages to reflect new behavior
3. Note changes in `log.md`: `## [YYYY-MM-DD] update | What Changed`
4. Update `updated` date in frontmatter

## Conventions

- **Code blocks** use language-specific syntax highlighting
- **Tables** for parameter lists, comparisons, benchmarks
- **Mermaid diagrams** for flows and architectures (when helpful)
- **No duplication** — if something is documented elsewhere, link to it
- **Cite sources** — every claim should be traceable to code or docs
- **English language** — all content in English

## Scale Targets

- ~100-200 wiki pages for full project coverage
- ~10-15 pages touched per ingest operation
- Index file stays under 500 lines (summarize, don't enumerate)
- Log file is append-only (never trim)
