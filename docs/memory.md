# Active Context Ledger & System Memory
## Kautilya AI (Omni Graph AI)

This file serves as the single source of truth for the active context, architectural decisions, and project state for Kautilya AI. All development agents (Claude Code, Cursor, Copilots) and engineers must read this file at the start of a coding session and update it before completing a task.

---

### 1. Project Quick Reference

| System Param | Value |
|---|---|
| **Project Code Name** | Kautilya AI (Omni Graph AI) |
| **System Language** | Python 3.11+, TypeScript, Rust (optional/future) |
| **Databases** | Neo4j Enterprise v5+, PostgreSQL 16 (pgvector), Redis 7.2 |
| **Agent Framework** | LangGraph, Model Context Protocol (MCP) |
| **Hosting Targets** | AWS EKS, Local Docker Compose (Development) |
| **Relay Communication** | mTLS gRPC / Secure WebSocket Polling |

---

### 2. Current Sprint Focus & Backlog

#### 2.1. Active Goals (In-Progress)
* [x] Initialize the Turborepo monorepo structure in `/apps` and `/packages`.
* [x] Create the `docker-compose.yml` for local developer dependency setups.
* [x] Define Pydantic models for incoming telemetry event ingestion payloads in `/apps/api`.
* [x] Implement Redis SET NX deduplication & idempotency dependency in `/apps/api/src/core/idempotency.py`.
* [x] Create Neo4j asynchronous topology client & constraint bootstrapper in `/packages/graph-core/src/neo4j_client.py`.
* [x] Create pgvector runbook embedding model & upsert logic in `/packages/graph-core/src/pgvector_client.py`.
* [x] Define LangGraph `AgentState` schema in `/packages/agents/src/state.py`.
* [x] Implement MCP tool integrations (Cypher and GitHub diff inspection) in `/packages/agents/src/tools/mcp_clients.py`.
* [x] Implement modular reasoning nodes (Triage, Blast Radius, Coder, Verifier) in `/packages/agents/src/nodes/`.
* [x] Wire cyclic self-healing StateGraph with fail-closed retry bounds in `/packages/agents/src/graph/workflow.py`.

#### 2.2. Next Up (Sprint Backlog)
* [ ] Implement Docker-in-Docker / microVM sandbox runner in `/packages/sandbox-runner`.
* [ ] Connect the LangGraph verifier node to real isolated ephemeral containers.

---

### 3. Active File Pointers
Use these file links to inspect active work areas:
* [Monorepo Config](file:///d:/workshops/Kautilya-AI/package.json) (Root package.json)
* [Ingestion App Config](file:///d:/workshops/Kautilya-AI/apps/api/pyproject.toml) (FastAPI app config)
* [Idempotency Core](file:///d:/workshops/Kautilya-AI/apps/api/src/core/idempotency.py) (Redis SET NX deduplication)
* [Webhook Endpoints](file:///d:/workshops/Kautilya-AI/apps/api/src/api/webhooks.py) (Datadog & GitHub ingestors)
* [Neo4j Graph Client](file:///d:/workshops/Kautilya-AI/packages/graph-core/src/neo4j_client.py) (Knowledge graph manager)
* [pgvector Storage](file:///d:/workshops/Kautilya-AI/packages/graph-core/src/pgvector_client.py) (Vector embedding storage)
* [Agent State](file:///d:/workshops/Kautilya-AI/packages/agents/src/state.py) (LangGraph TypedDict schema)
* [MCP Tool Interfaces](file:///d:/workshops/Kautilya-AI/packages/agents/src/tools/mcp_clients.py) (Cypher & Git diff tools)
* [Triage Node](file:///d:/workshops/Kautilya-AI/packages/agents/src/nodes/triage_node.py) (Root cause hypothesis generator)
* [Blast Radius Node](file:///d:/workshops/Kautilya-AI/packages/agents/src/nodes/blast_radius_node.py) (Topological impact tracer)
* [Coder Node](file:///d:/workshops/Kautilya-AI/packages/agents/src/nodes/coder_node.py) (Remediation patch generator)
* [Verifier Node](file:///d:/workshops/Kautilya-AI/packages/agents/src/nodes/verifier_mock_node.py) (Sandbox test simulator)
* [Incident State Graph](file:///d:/workshops/Kautilya-AI/packages/agents/src/graph/workflow.py) (Cyclic self-healing workflow)
* [Local Dev Compose](file:///d:/workshops/Kautilya-AI/infra/docker/docker-compose.dev.yml) (Docker configurations)
* [GitHub CI Workflow](file:///d:/workshops/Kautilya-AI/.github/workflows/ci.yml) (CI configuration)

---

### 4. Completed Features & Implementation Checklist

```
+-------------------------------------------------------------+
| IMPLEMENTATION ROADMAP STATUS                               |
+-------------------------------------------------------------+
| [x] Phase 0: Foundation                                     |
| [x] Phase 1: Ingestion & Knowledge Graph                    |
| [/] Phase 2: Agentic Reasoning (In Progress)                |
| [ ] Phase 3: Sandbox & Verification                         |
| [ ] Phase 4: Human-in-the-Loop & UI                         |
| [ ] Phase 5: Enterprise Hardening                           |
+-------------------------------------------------------------+
```

---

### 5. Architectural Decision Records (ADRs)

| ADR ID | Date | Title | Status | Decided By | Summary / Rationale |
|---|---|---|---|---|---|
| **ADR-001** | 2026-08-27 | Egress-Only Relay Agent | **Approved** | Principal Architect | The Customer VPC Relay agent will query the control plane via long-polling WebSocket/gRPC rather than establishing inbound proxy tunnels. This completely bypasses enterprise firewall restrictions on inbound traffic. |
| **ADR-002** | 2026-08-27 | Neo4j for Topology | **Approved** | Lead PM | Neo4j will store the system dependency layout over traditional relational systems because of graph traversal performance requirements and dynamic schema models. |
| **ADR-003** | 2026-08-27 | LangGraph for Agents | **Approved** | Lead AI Engineer | LangGraph is selected over LangChain AgentExecutor due to the requirement for deterministic state loops, cyclic logic, and explicit verification loops. |
| **ADR-004** | 2026-08-27 | LangGraph Cyclic Self-Healing for SRE Remediation | **Approved** | Principal AI Engineer | Implemented cyclic LangGraph StateGraph connecting Triage, Blast Radius, Coder, and Verifier nodes. Conditional verification loops allow autonomous self-healing retries (up to 3 attempts) while enforcing a strict fail-closed boundary on persistent test failures. |

---

### 6. Known Technical Debt & Guardrails

* **ponytail: local-docker-auth (Ceiling: Local Dev Setup only):** The local Neo4j/Postgres Docker Compose uses default credentials. Production deployment must replace default variables with AWS KMS keys.
* **ponytail: single-thread-mcp (Ceiling: Max 10 concurrent requests):** Custom MCP servers run on a single-threaded Python process. A gRPC-backed pool is required to scale concurrently for heavy incident workloads.

---

### 7. Instructions for AI Update Loops

When completing a ticket, debugging a bug, or refactoring code, the AI agent **MUST** perform the following update loop:

1. **Read `memory.md` first:** Check active file pointers, technical debt boundaries, and recent ADRs before writing new code.
2. **Execute coding task:** Write the minimal code that works, ensuring it conforms to `/docs/rules.md`.
3. **Log changes in `memory.md`:**
   * Update the status of any checkboxes in Section 2 or 4.
   * If a new architectural pattern is introduced, write a new row to the ADR table in Section 5.
   * If any shortcuts or temporary configurations were implemented, add a `ponytail:` note in Section 6 naming the upgrade path and ceiling constraints.
   * Update active file pointers in Section 3 to highlight new directories.
4. **Commit ledger alongside code:** Ensure your commit includes both the code edits and the updated `memory.md` file.
