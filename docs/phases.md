# Implementation Roadmap & Phases
## Kautilya AI (Omni Graph AI)

This document maps out the roadmap for implementing the Kautilya AI platform, organized into six chronological phases.

---

### Phase 0: Foundation (Monorepo & Workspace Environment)
The objective is to establish the monorepo tooling, linting rules, pre-commit hooks, and a local multi-container development environment containing all primary databases and brokers.

#### Deliverables & Implementation Tasks
* Initialize the monorepo using **Turborepo** with packages for backend, frontend, database schemas, and shared utilities.
* Configure TypeScript, ESLint, Python virtual environments, `ruff` formatting, and `mypy` configurations.
* Create a local `docker-compose.yml` defining Neo4j Enterprise (local dev license), PostgreSQL 16 with the `pgvector` extension, Redis, and a local Apache Kafka broker.
* Establish standard CI workflow templates for Github Actions (building, checking typing, and testing).

#### Definition of Done (DoD)
* Running `docker compose up` successfully provisions and runs Neo4j, PostgreSQL, Redis, and Kafka.
* `npm run lint` and `npm run test` pass successfully at the root directory level.
* Pre-commit hooks successfully block commits that contain lint errors, typing failures, or hardcoded secrets.

---

### Phase 1: Telemetry Ingestion & Knowledge Graph
Develop the event-driven ingestion system, define the Neo4j schema for tracking system topography, and build the graph sync pipeline.

#### Deliverables & Implementation Tasks
* Build a FastAPI ingestion service with endpoints for Datadog, Prometheus, Alertmanager, and PagerDuty webhooks.
* Implement Kafka event producers inside the FastAPI ingestion service to route normalized alerts.
* Design the Neo4j schema mapping service architecture (Nodes: `Service`, `Database`, `Pod`, `KubernetesNode`, `Alert`, `APIEndpoint`).
* Build a Kafka consumer job (Python) that updates the Neo4j graph nodes and edges in real-time when telemetry alerts are received.

#### Definition of Done (DoD)
* Webhook ingestion endpoint successfully handles high-throughput mock alert payloads with a processing latency of < 50ms.
* Receiving a test alert event (e.g., "CPU Spike on billing-service pod-4") dynamically adds an `Alert` node in Neo4j and connects it to the corresponding `Pod` node via an `ACTIVE_ALERT` edge.
* Integrated unit tests assert that graph traversals successfully query parent dependencies up to 3 levels deep.

---

### Phase 2: Agentic Reasoning (LangGraph & Planners)
Assemble the core AI reasoning loop using LangGraph to analyze incident data, determine the failure root cause, and generate a remediation plan.

#### Deliverables & Implementation Tasks
* Configure a LangGraph state machine tracking states: `Ingested`, `Triaging`, `LocatingCode`, `AnalyzingSandbox`, `PatchReady`, `Failed`.
* Implement a system planner using Claude 3.5 Sonnet / GPT-4o to analyze the alert, look up Neo4j topology, and fetch semantic logs from pgvector.
* Build custom Model Context Protocol (MCP) servers allowing the agent to retrieve code symbols, fetch log context, and view file trees.
* Create error correction loops allowing the agent to refine its triage hypothesis if initial logs or metrics conflict.

#### Definition of Done (DoD)
* The LangGraph workflow compiles successfully without deadlocks or infinite loops.
* The agent receives an incident alert payload, traverses the graph, queries logs, and outputs a structured JSON root-cause hypothesis (e.g., "DB pool exhausted in auth-service").
* Integration tests verify the system can recover from simulated LLM tool-calling failures.

---

### Phase 3: Ephemeral Sandboxing & Patch Verification
Implement the execution pipeline that provisions hardened sandboxes, clones repository code, applies patches, and runs automated tests.

#### Deliverables & Implementation Tasks
* Develop the sandbox-executor service that creates isolated Docker-in-Docker (DinD) runners on demand.
* Build libraries that automate git operations: cloning target branches, creating patch branches, and generating code diffs.
* Build a verification engine inside the sandbox that detects the application runtime (Python, Node.js, Go) and executes test commands (`pytest`, `npm test`, etc.).
* Implement logic to parse test outputs, compile errors, or validation warnings, returning them to the reasoning loop for patch iteration.

#### Definition of Done (DoD)
* Running the sandbox executor spins up a Docker container, executes a mock test suite, and tears down the container within 10 seconds.
* The agent is able to successfully write a patch file, execute the sandbox, and retrieve a structured output indicating tests passed or failed.
* The sandbox correctly disables outbound network access during test runs to enforce security.

---

### Phase 4: Human-in-the-Loop Governance & UI Command Center
Build the frontend dashboard and messaging integrations to allow engineers to review, approve, or reject proposed fixes.

#### Deliverables & Implementation Tasks
* Build the Next.js visual dashboard showing active incidents, the system dependency graph (React Flow), and real-time agent execution terminal logs.
* Implement the Approval Gate Modal displaying the candidate diff, test validation reports, confidence level, and actionable approval buttons.
* Create WebSockets interfaces between the Next.js frontend and the FastAPI backend for real-time dashboard state synchronization.
* Build the Slack integration that maps active incidents to interactive Slack messages with "Approve", "Reject", and "Ask Agent to Refine" actions.

#### Definition of Done (DoD)
* Next.js dashboard renders the Neo4j active alert topography and updates node colors instantly when alerts change.
* Clicking "Approve & Apply" in the UI triggers a webhook callback that completes the Git PR and resolves the incident.
* Interactive buttons in Slack successfully trigger callback handlers in the backend gateway.

---

### Phase 5: Enterprise Hardening & Security compliance
Implement the secure customer gateway boundary, high-availability data replication, secrets manager integration, and compliance logs.

#### Deliverables & Implementation Tasks
* Build the egress-only **Customer Relay Proxy** that runs inside a private network, polling the central control plane via secure WebSocket/gRPC (mTLS).
* Set up AWS KMS keys for encrypting secrets and environment variables both at rest and in transit.
* Implement a logging scrubbing library to strip out authorization headers, passwords, and sensitive variables from all database records.
* Build the log persistence engine that writes execution logs and LLM trace histories to AWS S3 buckets configured with Object Lock in Compliance mode (WORM storage).

#### Definition of Done (DoD)
* The Customer Relay Proxy runs locally, fetches work items from the control plane, executes them locally, and uploads results without requiring inbound firewall rules.
* Proof of concept showing that logs written to the WORM storage bucket cannot be edited, overwritten, or deleted by any system user, meeting SOC2 criteria.
* Load testing verifies system responsiveness under a continuous stream of 2,000 requests per minute with no memory leaks or connection dropouts.
