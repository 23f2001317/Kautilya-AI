# Engineering Guidelines & AI Agent Guardrails
## Kautilya AI (Omni Graph AI)

This document establishes the code quality, design constraints, and safety guidelines for the Kautilya AI monorepo. These guidelines must be enforced by automated CI/CD checks and adhered to by all developers and AI agents (Cursor, Claude, etc.) operating in this codebase.

---

### 1. Coding Standards

#### 1.1. Python (Backend & Agent Services)
* **Standards:** Adhere strictly to PEP8. Force formatting using `black` and linting using `ruff`.
* **Typing:** Strict static typing is mandatory. All functions must contain type hints for all arguments and return values. Run `mypy --strict` on pre-commit.
* **Data Modeling:** Use **Pydantic v2** for configuration, API request/response validation, and settings management.
* **Asynchronous Programming:** Prefer async/await syntax (`asyncio`) for network-bound and I/O-bound operations. 

#### 1.2. TypeScript & React (Frontend Services)
* **Standards:** Strict TypeScript is required. The `strict` flag must be set to `true` in `tsconfig.json`. Casting with `as any` is strictly forbidden.
* **React Architecture:** Use Next.js App Router. Follow the React Server Components (RSC) pattern:
  * Fetch data in Server Components by default.
  * Use Client Components (`"use client"`) only when there is active user state, hooks (e.g., `useState`, `useEffect`), browser-only APIs, or WebSocket listeners.
* **Styling:** Use standard CSS classes or tailwind utility classes. Do not define inline styles unless dynamic rendering requires it.

---

### 2. Forbidden Antipatterns

#### 2.1. No Raw Cypher/SQL Queries
* **Database Access:** Direct string interpolation of variables into Cypher or SQL query strings is forbidden to prevent SQL/Cypher injection.
* **Standard Implementation:** 
  * For Neo4j: Use parameterized queries passed through the official Neo4j driver interface or utilize a designated Object Graph Mapper (OGM).
  * For PostgreSQL: Use SQLAlchemy ORM with typed session models or use parameterized SQL queries with bind parameters.

#### 2.2. No Bypassing the Fail-Closed Gateway
* **Gateway Rule:** No worker, agent, or service within the customer network or vendor cloud may bypass the API Gateway's authentication, rate-limiting, and evaluation filters.
* **Execution Rules:** The agent reasoning engine cannot trigger changes in the Customer VPC without sending a signed execution request through the gateway, which validates confidence levels, permissions, and session leases.

#### 2.3. No Synchronous Distributed Pipelines
* **Pipeline Rule:** Do not use synchronous REST or gRPC calls for cross-service workflow execution. If Service A triggers an action in Service B, it must place an event on the message broker (Kafka/RabbitMQ). This prevents cascading failures and keeps services loosely coupled.

---

### 3. AI Agent Guardrails (For Cursor / Claude Code / Copilots)

> [!IMPORTANT]
> When executing autonomous changes in this repository, AI agents must abide by the following guidelines. Failure to do so will result in automated PR rejection.

#### 3.1. Secrets & Credentials
* **No Hardcoding:** Never write API keys, database credentials, JWT secrets, or environment-specific private configuration values directly to code files.
* **Configuration:** Fetch all secrets using environment variables or integration clients for AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault.

#### 3.2. Incremental Database Migrations
* **No Direct Schema Updates:** Never modify database schema definitions or past migration scripts directly.
* **Migration Strategy:** Database changes must be performed through new, incremental migration files generated via `alembic` (Python/Postgres) or Liquibase/Neo4j migration engines.
* **Rollbacks:** Every new migration script must include a valid rollback (`down`) path.

#### 3.3. Module Size and Scope
* **File Length Limit:** Keep files under **300 lines of code (LOC)**. 
* **SRP Enforcement:** Adhere to the Single Responsibility Principle. If a file exceeds 300 lines, split the logic into smaller, testable sub-modules, helper utilities, or separate class definitions.

---

### 4. System Resiliency & Fault Tolerance

#### 4.1. Ingestion Idempotency Keys
* **Idempotency Requirements:** All webhook payloads, telemetry events, and API execution calls must include a unique `Idempotency-Key` UUID.
* **Caching:** The API Gateway and Celery workers must cache processed idempotency keys in Redis for a minimum of 24 hours. Duplicate requests with the same key must return the cached response immediately without executing the operation twice.

#### 4.2. Circuit Breakers & Timeout Strategies
* **Outbound Call Guardrails:** Every external HTTP, gRPC, or database call must execute within a defined timeout (e.g., maximum 5 seconds for normal APIs, 30 seconds for LLMs).
* **Circuit Breakers:** Wrap external integration clients in circuit breakers. If an integration (e.g., Datadog, Slack, OpenAI) fails more than 5 times consecutively, the circuit must open, immediately returning a degraded/fallback response for subsequent calls to prevent resource starvation.

#### 4.3. Exponential Backoff with Jitter
* **Retry Strategy:** Failed transient network requests or database connections must be retried using exponential backoff:
  
  $$\text{Backoff Delay} = \text{Base Delay} \times 2^{\text{Attempt}} + \text{Jitter}$$
  
* **Random Jitter:** Jitter must be a random value between 0 and 1000ms added to the delay to prevent synchronized retry storms ("thundering herd" problem) hitting backend systems.
