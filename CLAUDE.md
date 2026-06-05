# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The **GridTokenX Smart Meter Simulator** — a standalone GridLAB-D (GLM) grid + AMI
simulator. It parses a `.glm` topology into a native grid model, generates per-meter
energy readings with Python device models (PV via `pvlib`, ZIP loads), runs an approximate
feeder solver each tick, and serves it all over a FastAPI REST API with a Next.js dashboard.

This is its **own git repository and sub-project**, separate from the parent
`gridtokenx-coresystem` Rust monorepo. The parent's `CLAUDE.md` (Rust/Cargo/Solana
conventions) **does not apply here** — this project is Python + TypeScript. `proto/oracle.proto`
defines the Protocol v4 telemetry contract for feeding readings into the parent's Oracle Bridge.

## Repository layout

This is a monorepo of two independently-developed apps, **each with its own `CLAUDE.md` —
read the one for the half you're touching before working in it**:

- **`backend/`** — Python 3.11+ FastAPI simulator, package manager **uv**. See
  [`backend/CLAUDE.md`](backend/CLAUDE.md) for commands, architecture, and conventions. The
  simulation engine, GLM parser, device models, and solver all live here.
- **`frontend/`** — Next.js 16 / React 19 dashboard (map, 3D topology, telemetry). See
  [`frontend/CLAUDE.md`](frontend/CLAUDE.md) and `frontend/AGENTS.md` — **Next.js 16 has
  breaking changes vs. older versions; consult `node_modules/next/dist/docs/` before writing
  frontend code.**

## Running locally (two processes)

```bash
# Backend — REST API on http://localhost:8082 (docs at /docs)
cd backend && uv run app

# Frontend — dashboard on http://localhost:3000
cd frontend && npm install && npm run dev
```

Quick backend sanity checks without the server:

```bash
cd backend
uv run cli --mode validate-topology          # validate the configured .glm, exit 1 if invalid
uv run cli --mode standalone --meters 20      # headless simulation loop
```

## Docker (single combined image)

The root `Dockerfile` builds **all three pieces into one image**, unlike the two-process local
flow: stage 1 builds the Next.js UI with **bun**, stage 2 compiles the `backend/src/rust_sim`
PyO3 crate to a `.so`, stage 3 assembles the Python backend with `uv` and copies in the built
UI + Rust lib. The container entrypoint is `uv run start` and it serves on port **8080**
(note: local dev uses **8082**). The Rust crate is an optional accelerator and is **not** on the
active Python code path — see `backend/CLAUDE.md`.

## Skills

- **`glm-topology-authoring`** (`.claude/skills/`) — invoke when creating, editing, or debugging
  `.glm` topology files. It documents exactly which GLM object types and fields this backend's
  subset parser actually reads. Reach for it on any "validate-topology" error or grid-model change.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
| ------ | ---------- |
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
