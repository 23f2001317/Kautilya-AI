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

#### 2.1. Completed Sprint Goals
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
* [x] Formulate structured Pydantic `RootCauseHypothesis` and tool failure recovery in `/packages/agents/src/nodes/triage_node.py`.
* [x] Implement ephemeral sandbox runner and runtime detector in `/packages/sandbox-runner`.
* [x] Connect LangGraph verifier node to isolated ephemeral execution sandbox in `/packages/agents/src/nodes/verifier_mock_node.py`.
* [x] Implement incident management and HITL approval gate API in `/apps/src/api/incidents.py`.
* [x] Implement real-time WebSocket state synchronization in `/apps/src/api/websockets.py`.
* [x] Implement interactive Slack webhook action callbacks in `/apps/src/api/slack.py`.
* [x] Build Next.js 15 SRE Command Center dashboard with topology viewer and Approval Gate modal in `/apps/web`.
* [x] Build egress-only Customer Relay Proxy in `/apps/relay`.
* [x] Implement sensitive credential and PII log scrubber in `/packages/security/src/scrubber.py`.
* [x] Implement immutable SHA-256 WORM audit ledger in `/packages/security/src/worm_logger.py`.
* [x] Implement KMS envelope encryption provider in `/packages/security/src/kms.py`.
* [x] Build multi-plane remediation orchestrator in `/apps/src/core/orchestrator.py` bridging Ingestion, Graph, Agent, Sandbox, and Audit planes.
* [x] Connect Ingestion webhooks in `/apps/src/api/webhooks.py` to trigger orchestrator and Customer Relay task queue.
* [x] Build Customer Relay task dispatch API in `/apps/src/api/tasks.py` supporting `/tasks/poll` and `/tasks/{id}/result`.
* [x] Connect Next.js Command Center to live REST endpoints and WebSocket events with 1-click test alert ingestion.
* [x] Provide shared TypeScript definitions in `/packages/shared-types/src/index.ts`.
* [x] Validate entire 5-plane journey in `/apps/tests/test_end_to_end_flow.py`.

#### 2.2. Next Up (Sprint Backlog)
* [ ] Integrate production Kubernetes cluster deployment manifests with AWS KMS secret operator.
* [ ] Connect live Neo4j database instance to frontend WebSocket topology streaming.

---

### 3. Active File Pointers
Use these file links to inspect active work areas:
* [Monorepo Config](file:///d:/workshops/Kautilya-AI/package.json) (Root package.json)
* [Shared Types](file:///d:/workshops/Kautilya-AI/packages/shared-types/src/index.ts) (Shared TypeScript interfaces)
* [Remediation Orchestrator](file:///d:/workshops/Kautilya-AI/apps/src/core/orchestrator.py) (Cross-plane remediation coordinator)
* [Customer Relay Tasks API](file:///d:/workshops/Kautilya-AI/apps/src/api/tasks.py) (Egress polling and task results)
* [Idempotency Core](file:///d:/workshops/Kautilya-AI/apps/src/core/idempotency.py) (Redis SET NX deduplication)
* [Webhook Endpoints](file:///d:/workshops/Kautilya-AI/apps/src/api/webhooks.py) (Datadog & GitHub ingestors)
* [Incident & HITL API](file:///d:/workshops/Kautilya-AI/apps/src/api/incidents.py) (Approval gate endpoints)
* [WebSocket Hub](file:///d:/workshops/Kautilya-AI/apps/src/api/websockets.py) (Real-time live streaming)
* [Slack Integration](file:///d:/workshops/Kautilya-AI/apps/src/api/slack.py) (Interactive button actions)
* [Command Center UI](file:///d:/workshops/Kautilya-AI/apps/web/src/app/page.tsx) (Next.js 15 App Router Dashboard)
* [Approval Gate Modal](file:///d:/workshops/Kautilya-AI/apps/web/src/components/ApprovalGateModal.tsx) (Diff review & approval)
* [Topology Viewer](file:///d:/workshops/Kautilya-AI/apps/web/src/components/TopologyGraph.tsx) (Dynamic graph component)
* [Agent Terminal](file:///d:/workshops/Kautilya-AI/apps/web/src/components/AgentTerminal.tsx) (Real-time thought ledger)
* [Sandbox Runner](file:///d:/workshops/Kautilya-AI/packages/sandbox-runner/src/runner.py) (Ephemeral execution engine)
* [Runtime Detector](file:///d:/workshops/Kautilya-AI/packages/sandbox-runner/src/detector.py) (Python/Node/Go detector)
* [Git Ops Manager](file:///d:/workshops/Kautilya-AI/packages/sandbox-runner/src/git_ops.py) (Unified diff patch applier)
* [Agent State & Schema](file:///d:/workshops/Kautilya-AI/packages/agents/src/state.py) (RootCauseHypothesis & AgentState)
* [Incident State Graph](file:///d:/workshops/Kautilya-AI/packages/agents/src/graph/workflow.py) (Cyclic self-healing workflow)
* [Verifier Node](file:///d:/workshops/Kautilya-AI/packages/agents/src/nodes/verifier_mock_node.py) (Sandbox test executor)
* [Customer Relay Proxy](file:///d:/workshops/Kautilya-AI/apps/relay/src/relay_agent.py) (Egress-only outbound worker)
* [Log Scrubber](file:///d:/workshops/Kautilya-AI/packages/security/src/scrubber.py) (Credential & PII redaction)
* [WORM Audit Ledger](file:///d:/workshops/Kautilya-AI/packages/security/src/worm_logger.py) (Cryptographic SHA-256 chain)
* [KMS Encryption](file:///d:/workshops/Kautilya-AI/packages/security/src/kms.py) (Envelope encryption provider)
* [Neo4j Graph Client](file:///d:/workshops/Kautilya-AI/packages/graph-core/src/neo4j_client.py) (Knowledge graph manager)
* [pgvector Storage](file:///d:/workshops/Kautilya-AI/packages/graph-core/src/pgvector_client.py) (Vector embedding storage)

---

### 4. Completed Features & Implementation Checklist

```
+-------------------------------------------------------------+
| IMPLEMENTATION ROADMAP STATUS                               |
+-------------------------------------------------------------+
| [x] Phase 0: Foundation                                     |
| [x] Phase 1: Ingestion & Knowledge Graph                    |
| [x] Phase 2: Agentic Reasoning                              |
| [x] Phase 3: Sandbox & Verification                         |
| [x] Phase 4: Human-in-the-Loop & UI                         |
| [x] Phase 5: Enterprise Hardening                           |
| [x] End-to-End Cross-Plane Orchestration                    |
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
| **ADR-005** | 2026-09-03 | Pluggable Ephemeral Sandbox Runtime Architecture | **Approved** | Lead Architect | Designed a pluggable `SandboxRuntime` interface supporting `DockerSandboxRuntime` (hardened container with `--network none`) and `LocalEphemeralSandboxRuntime` (temporary directory isolation with network sinks and strict 10s execution guards). This ensures local developer testability and CI compatibility when Docker daemons are unavailable. |
| **ADR-006** | 2026-09-03 | Cryptographic Approval Gate & Slack Webhooks | **Approved** | Security Lead | Remediation PR creation requires cryptographic approval signatures via Next.js Approval Gate Modal or Slack interactive button callbacks before merging. |
| **ADR-007** | 2026-09-03 | Tamper-Evident SHA-256 WORM Audit Ledger | **Approved** | Compliance Officer | Audit entries are cryptographically chained using SHA-256 block hashes ($H_n = \text{SHA-256}(H_{n-1} + \text{data}_n)$) conforming to SOC2 and S3 Object Lock Compliance WORM criteria, enabling instant detection of altered or inserted records. |
| **ADR-008** | 2026-09-03 | Autonomous Multi-Plane Orchestration & Egress Task Dispatch | **Approved** | Lead Architect | Connected Ingestion (Plane 1) directly to LangGraph (Plane 3), Neo4j (Plane 2), and Sandbox (Plane 4) via `RemediationOrchestrator`. Provided an egress-only `/tasks/poll` and `/tasks/{id}/result` task dispatch bridge so Customer Relay Proxies operate securely without open ports while maintaining unbroken SHA-256 WORM audit trails. |


---

### 6. Known Technical Debt & Guardrails

* **ponytail: local-docker-auth (Ceiling: Local Dev Setup only):** The local Neo4j/Postgres Docker Compose uses default credentials. Production deployment must replace default variables with AWS KMS keys.
* **ponytail: single-thread-mcp (Ceiling: Max 10 concurrent requests):** Custom MCP servers run on a single-threaded Python process. A gRPC-backed pool is required to scale concurrently for heavy incident workloads.
* **ponytail: pluggable-sandbox-runtime (Ceiling: Local Dev host without Docker daemon):** Fallback to `LocalEphemeralSandboxRuntime` uses process and filesystem sandboxing. Production requires hardened DinD or microVMs (sysbox / Firecracker).
* **ponytail: in-memory-incident-store (Ceiling: Single API instance):** In-memory dictionary store in `incidents.py` handles local development; upgrade path is Redis-backed PostgreSQL ORM for distributed multi-region deployments.

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
