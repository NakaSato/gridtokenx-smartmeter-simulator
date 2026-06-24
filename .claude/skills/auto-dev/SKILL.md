---
name: Auto Dev
description: Autonomous development loop for a single task — plan, implement, test, summarize. Runs end-to-end without pausing except on hard blockers. Use when the user says "auto-dev <task>", "automatic development", "just build it", or wants a task driven start-to-finish.
---

## Auto Dev

Drive ONE development task from request to verified change with no hand-holding.
Fully autonomous: do not pause for approval on routine steps. Stop ONLY on a hard
blocker (see §Stop conditions). This is a gridtokenx superproject — every
`gridtokenx-*` service is its own Cargo workspace / submodule. Obey the root
CLAUDE.md, especially the **Test-First, Then Summarize** rule.

### Inputs

- The task = everything after `auto-dev` in the user prompt. If empty, ask the
  user for the task (the only allowed up-front question).
- Infer the target service(s) from the task. If ambiguous across services, pick
  the most likely and state the assumption — do not block.

### Loop

1. **Orient (graph first, cheap).**
   - `get_minimal_context(task="<task>")` then `semantic_search_nodes` /
     `query_graph` to locate the code. Use the MCP graph BEFORE Grep/Glob/Read.
   - Identify the owning service dir (`cd gridtokenx-<service>`). Read that
     service's `ARCHITECTURE.md` only if the change is non-trivial.

2. **Plan (brief, internal).**
   - Decide files to touch, the dependency direction (`server → api → logic →
     persistence → core` — never reverse), and which tests will prove it.
   - For a multi-file or cross-service change, spawn the `Plan` agent. For a
     bounded 1–2 file edit, just proceed.

3. **Implement.**
   - Match surrounding code style, naming, comment density. Follow CLAUDE.md
     conventions: `anyhow::Result` + `.context()`, `tracing` not `log`,
     `#[instrument(skip(secrets))]`, thin Axum handlers, `sqlx::query_as!`,
     no `.unwrap()` in production paths, all Solana access via Chain Bridge.
   - Never `cargo` from repo root — `cd` into the service first.

4. **Test-first verification (MANDATORY — do not skip, do not assume).**
   - Fast gate: `cd gridtokenx-<service> && cargo check`.
   - Narrowest tests covering the change, widening as needed:
     - one crate: `cargo test -p <crate>`
     - one test: `cargo test <name> -- --nocapture`
     - whole service: `cargo test`
   - Frontend submodules (`gridtokenx-trading`, `gridtokenx-explorer`):
     `npm test` / `npm run build`, not cargo.
   - Cross-service: `just test` / `just clippy`; integration needs `just orb-up`.
   - If a test fails: fix and re-run (max 3 focused attempts on the same
     failure, then stop and report — see §Stop conditions).
   - If infra/validator/broker is missing so tests can't run: say so explicitly,
     mark that path UNVERIFIED, continue with what CAN run. Never claim success
     without evidence.
   - If the change has no covering test, add one (or state plainly why not).

5. **Summarize (the Test-First rule's part 2).** Always end with the 3-part list:
   - **What to do** — the goal / intent.
   - **What actions** — concrete actions, files as `path:line`, commands run.
   - **What result** — real test output (pass/fail), what's verified vs pending,
     follow-ups.

### Fully-auto policy

- Do NOT ask for approval to edit code, run tests, or run read-only/build
  commands. Just do it and report.
- Do NOT commit, push, or open PRs unless the task explicitly asks. If it does,
  branch off main first, and end commit messages with the Co-Authored-By trailer
  per harness rules.
- Prefer parallel independent tool calls in one turn (graph queries, reads).

### Stop conditions (the only times you pause)

- Empty task and you can't infer one → ask once.
- Same test failure survives 3 focused fix attempts.
- A required external action only the user can do (interactive login, secrets,
  `git` interactive, a service that must be started by hand).
- A destructive or irreversible step the task did not clearly authorize
  (deleting files you didn't create, force-push, dropping a DB/migration,
  rewriting history).
- The change would touch a security-sensitive boundary (auth, key handling,
  Chain Bridge signing, mTLS) in a way the task didn't spell out.

When stopping, report: what's done, what's blocking, the exact command or
decision needed to unblock.

### Token efficiency

- Graph tools before file scanning. `detail_level="minimal"`, escalate only if
  insufficient. Use `rg`, never `grep`, when shelling out.
