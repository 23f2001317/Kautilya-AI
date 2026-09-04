// apps/web/src/components/AgentTerminal.tsx
"use client";

import React from "react";

interface LogEntry {
  timestamp: string;
  source: string;
  message: string;
}

const DEFAULT_LOGS: LogEntry[] = [
  {
    timestamp: "19:54:10",
    source: "INGEST",
    message:
      "CanonicalAlert received: High Latency & Thread Pool Exhaustion on auth-service",
  },
  {
    timestamp: "19:54:12",
    source: "TRIAGE",
    message:
      "Identified culprit commit c0ffee123 throttled DB pool (max_connections=2)",
  },
  {
    timestamp: "19:54:14",
    source: "BLAST_RADIUS",
    message:
      "Neo4j query complete: 2 downstream services impacted (payment-api, web-frontend)",
  },
  {
    timestamp: "19:54:16",
    source: "CODER",
    message:
      "Synthesized remediation patch v2 (max_connections=50, pool_timeout=30)",
  },
  {
    timestamp: "19:54:18",
    source: "SANDBOX",
    message:
      "DinD runner executed 24 integration tests: 24 passed, 0 failed in 1420ms",
  },
  {
    timestamp: "19:54:19",
    source: "GOVERNANCE",
    message: "Waiting for human approval gate signature...",
  },
];

export function AgentTerminal({ logs = DEFAULT_LOGS }: { logs?: LogEntry[] }) {
  return (
    <div className="terminal-box" id="agent-terminal-feed">
      {logs.map((log, index) => (
        <div
          key={`log-${index}-${log.timestamp}`}
          style={{ marginBottom: "6px" }}
        >
          <span style={{ color: "#64748b", marginRight: "8px" }}>
            [{log.timestamp}]
          </span>
          <span
            style={{ color: "#a855f7", fontWeight: "600", marginRight: "8px" }}
          >
            [{log.source}]
          </span>
          <span
            style={{ color: log.source === "SANDBOX" ? "#34d399" : "#e2e8f0" }}
          >
            {log.message}
          </span>
        </div>
      ))}
    </div>
  );
}
