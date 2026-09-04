# Kautilya AI — Mock & Fixture Audit (MOCK_AUDIT.md)

This audit identifies all instances of mock, fixture, hardcoded, or canned data across the Kautilya AI codebase. Each entry specifies the exact file location, line number, the mock pattern identified, and the planned real implementation replacing it.

---

## 1. Frontend Mock & Fixture Sources (`apps/web/src/**`)

| ID | File & Line | Identified Mock / Fixture Pattern | Planned Real Implementation Replacement |
|---|---|---|---|
| **FE-01** | `apps/web/src/app/page.tsx`:32–55 | `INITIAL_INCIDENTS` array hardcoded in component state. | Remove inline array. Fetch incidents exclusively from `GET /incidents` persisted in database. |
| **FE-02** | `apps/web/src/app/page.tsx`:62–83 | `logs` state initialized with 4 canned entries with static timestamps (`19:54:xx`). | Initialize logs empty. Populate logs purely from real WebSocket broadcast events (`agent_thought`, `node_transition`, `sandbox_output`). |
| **FE-03** | `apps/web/src/app/page.tsx`:114 | `new Date().toLocaleTimeString()` formatting causing timestamp format jumps mid-stream. | Standardize on ISO-8601 timestamps provided directly by the backend telemetry payload and format uniformly. |
| **FE-04** | `apps/web/src/app/page.tsx`:190–194 | `handleApprove` local fallback hardcoding `pr_url: "https://github.com/repo/pull/1"`. | Fail visibly with UI toast/error state if approval or PR creation API fails; do not inject dummy PR URLs. |
| **FE-05** | `apps/web/src/app/page.tsx`:223–247 | `handleTriggerSimulatedAlert` sends identical hardcoded auth-service alert payload and uses `setTimeout(1000)`. | Connect to `POST /api/alerts/simulate` which dynamically generates varied service incidents (auth, payments, cache, database) and triggers the real LangGraph pipeline without artificial `setTimeout`. |
| **FE-06** | `apps/web/src/app/page.tsx`:426–440 | "Autonomous Guardrail Status" panel uses static hardcoded HTML checks. | Query `GET /api/audit/verify` and system health checks to render live verifiable ledger status, chain head hash, and retry status. |
| **FE-07** | `apps/web/src/components/TopologyGraph.tsx`:15–48 | `const NODES: Node[] = [...]` hardcoded static 4-node topology. | Fetch topology dynamically from `GET /api/topology` backed by live Neo4j Cypher queries or persistent topology storage. |
| **FE-08** | `apps/web/src/components/TopologyGraph.tsx`:102–130 | Hardcoded SVG `<line>` elements with static coordinates. | Dynamically render edges based on topological relationships (`CALLS`, `DEPENDS_ON`) from live query results. |
| **FE-09** | `apps/web/src/components/ApprovalGateModal.tsx`:62, 66, 70 | Fallback defaults `passed ?? 24`, `failed ?? 0`, `duration_ms ?? 1420.5`. | Remove fallbacks. Display only real metrics parsed from actual sandbox test runner outputs; display loading skeleton or error state if absent. |

---

## 2. Backend Mock & Fixture Sources (`apps/src/**`)

| ID | File & Line | Identified Mock / Fixture Pattern | Planned Real Implementation Replacement |
|---|---|---|---|
| **BE-01** | `apps/src/api/incidents.py`:51–75 | `_INCIDENT_STORE` in-memory dictionary pre-seeded with `inc-auth-01` fixture. | Replace with real SQLite/SQLAlchemy persistence (`kautilya.db`) so incidents persist across server restarts. |
| **BE-02** | `apps/src/api/incidents.py`:109–111 | `mock_pr_url = f"https://github.com/kautilya-ai/repo/pull/{...}"` string template. | Integrate real GitHub API client (`httpx` / REST) with `GITHUB_TOKEN` and real git branch/commit creation. Fail explicitly if credentials are missing or API fails. |
| **BE-03** | `apps/src/core/orchestrator.py`:116 | Confidence score fallback literal `0.94`. | Derive confidence score strictly from the LangGraph triage node output (`RootCauseHypothesis.confidence_score`). |
| **BE-04** | `apps/src/core/orchestrator.py`:127 | Fallback impacted services literal `["payment-api", "web-frontend"]`. | Derive impacted services strictly from the graph traversal result in `blast_radius_step`. |
| **BE-05** | `apps/src/core/orchestrator.py`:135–139 | Hardcoded test summary `{"passed": 24, "failed": 0, "duration_ms": 1420.5}`. | Extract genuine test summary from `VerificationReport` produced by the sandbox runner execution. |
| **BE-06** | `apps/src/core/orchestrator.py` & `apps/src/api/websockets.py` | Missing real-time streaming of intermediate agent node steps (triage, blast radius, coder, verifier). | Add LangGraph streaming / execution callbacks that emit real `agent_thought` events with unique correlation IDs over WebSockets. |
| **BE-07** | Missing Endpoint | No endpoint for audit ledger verification. | Implement `GET /api/audit/verify` that runs `audit_ledger.verify_integrity()` and returns verification status and recent chain blocks. |
| **BE-08** | Missing Endpoint | No endpoint for live topology graph data. | Implement `GET /api/topology` executing Cypher queries against Neo4j (with persistent graph fallback) returning active nodes, blast radius, and alert highlights. |
| **BE-09** | Missing Endpoint | No simulation endpoint for generating varied realistic alerts. | Implement `POST /api/alerts/simulate` supporting multiple distinct incident archetypes (Database Pool Starvation, Redis Cache Eviction, HTTP Gateway Timeout, Memory Leak). |

---

## 3. Agent & Tool Mock Sources (`packages/agents/**` & `packages/sandbox-runner/**`)

| ID | File & Line | Identified Mock / Fixture Pattern | Planned Real Implementation Replacement |
|---|---|---|---|
| **AG-01** | `packages/agents/src/nodes/triage_node.py`:36–48 | Fixed narrative ("Commit throttled database connection pool...") and hardcoded `confidence_score=0.94` for all alerts. | Dynamically generate diagnosis hypothesis, failure category, and confidence score based on the alert's actual service, metrics, and culprit commit diff. |
| **AG-02** | `packages/agents/src/nodes/coder_node.py`:30–50 | Hardcoded `diff --git a/src/db/pool.py` patch regardless of incident nature. | Dynamically synthesize targeted code/config patches specific to the service, file, and diagnosed root cause. |
| **AG-03** | `packages/agents/src/nodes/verifier_mock_node.py`:49–56, 73–92 | String check `"max_connections: int = 20"` overriding actual test results; simulation branch emitting canned strings. | Use genuine test execution results from `EphemeralSandboxService` (`passed_tests`, `failed_tests`, `duration_ms`, `exit_code`). |
| **AG-04** | `packages/agents/src/tools/mcp_clients.py`:30–50 | `execute_cypher_query` returns hardcoded 3-edge list. | Execute real Cypher queries via `Neo4jManager` with persistent topology repository fallback. |
| **AG-05** | `packages/agents/src/tools/mcp_clients.py`:65–81 | `fetch_github_commit_diff` returns hardcoded diff. | Inspect real commit diff from local git repository or GitHub API. |
| **AG-06** | `packages/agents/src/tools/mcp_clients.py`:96–106 | `query_runbook_embeddings` returns hardcoded SOP dict. | Query real pgvector runbook embeddings or match semantic runbook catalog. |
| **AG-07** | `packages/agents/src/tools/mcp_clients.py`:121–125 | `fetch_service_logs` returns hardcoded log lines. | Query real service logs or dynamically generated container error streams. |
| **AG-08** | `apps/relay/src/relay_agent.py`:53–58 | `_default_local_handler` returns hardcoded `tests_passed: 24`. | Invoke real local sandbox execution within the customer relay boundary. |

---

## 4. Execution Order Checklist

- [ ] **Step 1:** Audit Complete (`MOCK_AUDIT.md` verified).
- [ ] **Step 2:** Backend Real-Data Wiring (BE-01 through BE-09, AG-01 through AG-08).
- [ ] **Step 3:** Frontend Component Architecture & Real Data Layer (FE-01 through FE-09).
- [ ] **Step 4:** Premium UI/UX Redesign (Design tokens, semantic colors, timeline ledger, interactive topology graph, tabbed approval modal).
- [ ] **Step 5:** Acceptance Pass & Verification (All 14 acceptance criteria satisfied).
