# UI/UX System Design Specification
## Kautilya AI (Omni Graph AI)

This document outlines the visual system, user interactions, components, and layout architecture for the Kautilya AI "Command Center" dashboard interface.

---

### 1. Theme & Color Palette

Kautilya AI uses an **Enterprise SRE Dark Mode** design system. The goal is to provide high legibility in high-stress, low-light triage environments, calling immediate visual attention to anomalous components using neon alerts.

```
+---------------------------------------------------------------------------------+
|  BACKGROUND (Slate-950)                                                         |
|  #090D16                                                                        |
|                                                                                 |
|  +--------------------+   +--------------------+   +--------------------+       |
|  | PANEL (Slate-900)  |   | PANEL (Slate-900)  |   | PANEL (Slate-900)  |       |
|  | #0F172A            |   | #0F172A            |   | #0F172A            |       |
|  +--------------------+   +--------------------+   +--------------------+       |
|                                                                                 |
|  Accents:                                                                       |
|  [ NEON RED: #EF4444 ]   [ NEON AMBER: #F59E0B ]   [ NEON EMERALD: #10B981 ]    |
|  Critical Alerts         Warnings/Degraded         Healthy Status               |
|                                                                                 |
|  [ NEON BLUE: #3B82F6 ]  [ NEON PURPLE: #8B5CF6 ]  [ BORDER: #1E293B ]          |
|  Agent Activity          Graph Selections          Grid Lines                   |
+---------------------------------------------------------------------------------+
```

#### Color Design Tokens
* **Base Background:** `#090D16` (Deep slate black)
* **Surface Background (Panels):** `#0F172A` (Slate-900)
* **Surface Hover:** `#1E293B` (Slate-800)
* **Borders / Grid Lines:** `#334155` (Slate-700) or `#1E293B` (Slate-800)
* **Status Colors:**
  * **Critical / Inactive:** `#EF4444` (Neon Red, glow index: `rgba(239, 68, 68, 0.45)`)
  * **Warning / Degraded:** `#F59E0B` (Neon Amber, glow index: `rgba(245, 158, 11, 0.45)`)
  * **Healthy / Active:** `#10B981` (Neon Emerald, glow index: `rgba(16, 185, 129, 0.45)`)
* **Interactive Accents:**
  * **Agent Processing:** `#3B82F6` (Neon Blue)
  * **Selected Entity:** `#8B5CF6` (Neon Purple)

---

### 2. Typography
Typography must prioritize code readability, hierarchy, and density.

* **Primary Font (UI Headers, labels, body text):** *Inter* or *Geist Sans*. Clean, sans-serif design optimized for text sizing down to 10px.
* **Secondary Font (Monospace - Logs, Code patches, Cypher queries, Terminal outputs):** *JetBrains Mono* or *Geist Mono*. High distinction between characters (e.g., `0` vs `O`, `l` vs `1`).

---

### 3. Dynamic Topology Graph (React Flow / Cytoscape)

The central interface feature is the real-time interactive system graph.

```
       [Service Node (billing-service)]
       +-------------------------------+
       | (o) healthy | v1.4.2          |
       +-------------------------------+
                       |
                       | (pulsing downstream traffic flow)
                       v
       [Service Node (payment-gateway)]
       +-------------------------------+
       | (X) CRITICAL | v1.4.3         | <=== PULSING RED BLAST RADIUS
       +-------------------------------+
```

#### 3.1. Node Specifications
* **Alert Node (PagerDuty/Alertmanager):** Octagonal shape. Neon red border with a subtle inner glow. Icon matches alert type (e.g., database, disk, latency).
* **Service Node (Microservice/API):** Rounded rectangle. Displays service name, active version tag (`v1.2.0`), and small sparklines representing active throughput.
* **Infrastructure Node (Database/Queue/Cache):** Cylindrical or grid shape. Displays database memory usage, queue length, or connection pool statistics.

#### 3.2. Edge Interactions & Blast-Radius Animations
* **Healthy Connections:** Static or slowly moving light-gray/emerald dots along the connector lines indicating traffic.
* **Incident Propagation:** If a component fails, the connector edges downstream of that component turn into **pulsing, thick neon red lines** (`#EF4444`) with a CSS animation velocity relative to the severity of downstream traffic latency:
  
  ```css
  @keyframes blast-pulse {
    0% { stroke-dashoffset: 24; }
    100% { stroke-dashoffset: 0; stroke-width: 3px; filter: drop-shadow(0 0 4px #EF4444); }
  }
  ```

---

### 4. Layout Architecture

#### 4.1. Live Incident Canvas (Split Screen Dashboard)
The standard user view is divided into two primary vertical panels:

```
+------------------------------------------+------------------------------------------+
|  TOPOLOGY CANVAS                         |  AGENT STATE TERMINAL                    |
|  (Interactive Zoom/Pan Graph)            |  (Interactive Console Log & Shell View)  |
|                                          |                                          |
|  [Alert] ---> [Billing] ---> [Database]  |  [10:42:01] Ingested alert PD-482        |
|                  | (pulsing red)         |  [10:42:05] Querying topology graph...   |
|                  v                       |  [10:42:09] Found root cause: DB Lock    |
|               [Payment]                  |  [10:42:15] Spinning up DinD sandbox...  |
|                                          |  [10:42:25] Sandbox test output:         |
|  +------------------------------------+  |  >> Running pytest...                    |
|  | Graph Controls (Zoom, Pan, Fit)   |  |  >> 14 passed, 1 failed (db_timeout)     |
|  +------------------------------------+  |  [10:42:31] Applying patch diff...       |
+------------------------------------------+------------------------------------------+
```

* **Left Panel (Topology Canvas - 60% Width):**
  * Displays the interactive node graph.
  * Allows click-to-expand to inspect telemetry parameters, traces, or associated alerts on any node.
* **Right Panel (Agent State Terminal - 40% Width):**
  * Displays the active steps of the LangGraph state machine.
  * Outputs raw sandbox execution shell files, compiler errors, and LLM reasoning steps.
  * Includes a toggle to switch from "User Mode" (simplified markdown summary) to "SRE Mode" (detailed logs, bash outputs, and raw Cypher queries).

#### 4.2. Approval Gate Modal
A full-screen modal overlay triggered when the agent completes verification of a patch. The layout is divided into three blocks:

```
+-------------------------------------------------------------------------------------+
|  PROPOSED REMEDIATION PATCH                                          [ Close X ]    |
+-------------------------------------------------------------------------------------+
|  Incident ID: KAI-902  |  Target Repo: backend-auth  |  Confidence Score: 94%       |
+-------------------------------------------------------------------------------------+
|  CODE PATCH DIFF (Left)             |  VERIFICATION SUMMARY (Right)                 |
|  ```diff                            |  - Sandbox Target: Python-3.11-Alpine         |
|  - max_connections = 20             |  - Test Suites Executed: unit, integration     |
|  + max_connections = 150            |  - Test Results: 42/42 passed (100% success)  |
|  ```                                |  - Impact on dependencies: None detected      |
+-------------------------------------------------------------------------------------+
|  ACTION BAR:                                                                        |
|  [ REJECT & DISCARD ]     [ ITERATE / REFINE ]      [ APPROVE & PUSH TO GITHUB ]    |
+-------------------------------------------------------------------------------------+
```

1. **Meta Header:** Shows incident title, affected repository path, confidence score (rendered as a radial indicator colored green/amber), and sandbox runtime info.
2. **Left Column (Code Diff):** A syntax-highlighted code editor (JetBrains Mono) showing the file diff in git style format (green lines added, red lines removed).
3. **Right Column (Verification Summary):** Checklist of actions performed inside the sandbox, including test logs, build duration, and security checks.
4. **Footer Action Bar:** Fixed-position buttons:
  * **Approve & Apply:** Creates a pull request on GitHub, signs it with a cryptographic key, auto-merges (if rules allow), and marks the incident resolved.
  * **Iterate / Ask Agent to Refine:** Opens a text box where the SRE can provide instructions to the agent (e.g., "Use 100 connections instead of 150, and update the config file comments").
  * **Reject & Discard:** Closes the incident, tears down resources, and marks the suggestion as incorrect (providing reinforcement learning data).
