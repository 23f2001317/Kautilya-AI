# Security Architecture & Boundaries
## Kautilya AI (Omni Graph AI)

Kautilya AI handles sensitive client code, telemetry metrics, and executes automated scripts within client networks. This document details the security layers, sandbox restrictions, fail-safe boundaries, and compliance tracking configurations.

---

### 1. Zero-Trust Customer Relay Proxy

The orchestration engine must interface with customer source code and internal databases without requiring the customer to compromise their network perimeter security.

```
       +------------------------------------+
       |         VENDOR CLOUD CONTROL       |
       |  (Hosts UI, Agent State Machine)   |
       +-----------------+------------------+
                         ^
                         | (Outbound HTTPS/gRPC over mTLS)
                         | No Inbound Ports Allowed!
       +-----------------+------------------+
       |         CUSTOMER FIREWALL WALL     |
       +-----------------+------------------+
                         v
       +-----------------+------------------+
       |        CUSTOMER RELAY PROXY        |
       |  (Polls work queue, runs sandbox)  |
       +------------------------------------+
```

#### Egress-Only Communication Protocol
* **No Open Inbound Ports:** The customer's network firewall is configured to block all inbound TCP/UDP ports from the internet.
* **Polling Architecture:** The Customer Relay Proxy running in the Customer VPC initiates all communication outbound to the Kautilya AI Control Plane.
* **Tunnels:** It establishes a persistent connection using long-polling HTTPS or an outbound gRPC tunnel secured with Mutual TLS (mTLS) with pinned client/server certificates.
* **State Operations:** When a telemetry event triggers an incident analysis run, the central Control Plane posts a task to a Redis-backed queue. The Relay Proxy polls the queue, downloads the task instructions, fetches logs and code locally, and posts execution updates back to the Control Plane.

---

### 2. Fail-Closed API Gateway

All instructions originating from the AI Agent (Reasoning Plane) must pass through a strict Policy Enforcement Engine housed in the API Gateway.

* **LLM Confidence Gate:** The gateway validates the agent's self-reported and metadata-calculated confidence scores. If the confidence falls below the predefined threshold (e.g., `< 90%`), execution is denied, and the task immediately transitions to `Escalated` (requesting human intervention).
* **Execution Boundary:** The agent cannot execute commands containing wildcard variables or raw shell injections. The gateway checks commands against a whitelist of approved utility structures (e.g., `git checkout`, `pytest`, `npm install`).
* **Timeout-Gate:** If an agent operation stalls or fails to respond within a specific timeout lease (e.g., maximum 60 seconds), the gateway invalidates the operation's session token and locks out the execution run.
* **Panic Switch:** System administrators can trigger a global API Gateway override, immediately disconnecting all active relay proxies, terminating active runners, and returning the agent system to a passive monitoring state.

---

### 3. Hardened Sandbox Isolation

Remediation scripts and compilation checks run inside isolated Docker-in-Docker (DinD) or Sysbox container environments to mitigate the risk of arbitrary code execution.

* **Read-Only Root Filesystem:** Sandbox containers are executed with a read-only root (`/`) filesystem. Write operations are restricted to specific, transient workspace directories (e.g., `/tmp`, `/app/src`).
* **Resource Limits:** Strict CPU, memory, and disk I/O quotas are enforced at the container runtime level:
  * Maximum 2 CPU Cores
  * Maximum 4GB RAM
  * Maximum 5GB ephemeral disk storage
* **Zero Egress (Network Isolation):** During the execution phase of tests or patch verification scripts, the container's network interface is disabled (`--network none`) or restricted to a private, non-routable loopback network. This prevents third-party packages from leaking environment variables or exfiltrating data.
* **User Privileges:** The process inside the container runs as a non-root `sandbox` user (`UID 10001`). System administrative capabilities (`CAP_SYS_ADMIN`, `CAP_NET_ADMIN`) are disabled.

---

### 4. Compliance & Audit Trails

To comply with SOC2, ISO 27001, and HIPAA standards, Kautilya AI implements persistent logging and automated secrets management.

#### 4.1. Secrets Management
* **Encryption Key Management:** All sensitive variables, API tokens, and git credentials are encrypted at rest using **AWS KMS** or local envelope encryption keys.
* **Relay-Side Decryption:** Decryption keys are loaded into memory on the Customer Relay Proxy only during execution and are never written to disk or sent to the central Control Plane.

#### 4.2. Zero-Log Policy for Sensitive Variables
* **Sanitization Engine:** A logging interceptor sanitizes stdout, stderr, and network payloads before writing records.
* **Scrubbing Rules:** Regex filters identify and replace patterns matching authorization tokens, API keys, passwords, database URLs, and environment configuration dumps with `[REDACTED]`.

#### 4.3. Immutable Auditing (WORM Storage)
* **Storage Target:** Incident post-mortems, step-by-step agent logs, executed code patches, and terminal outputs are exported to an Amazon S3 bucket.
* **S3 Object Lock:** The bucket is configured with S3 Object Lock in **Compliance Mode** with a retention period of 7 years. Once written, the log files cannot be edited, overwritten, or deleted by any system user, administrator, or agent, ensuring an untampered audit trail for security compliance reviews.
