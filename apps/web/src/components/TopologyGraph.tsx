// apps/web/src/components/TopologyGraph.tsx
"use client";

import React from "react";

interface Node {
  id: string;
  label: string;
  type: "service" | "database" | "frontend";
  status: "alert" | "impacted" | "healthy";
  x: number;
  y: number;
}

const NODES: Node[] = [
  {
    id: "web",
    label: "web-frontend",
    type: "frontend",
    status: "impacted",
    x: 60,
    y: 70,
  },
  {
    id: "payment",
    label: "payment-api",
    type: "service",
    status: "impacted",
    x: 220,
    y: 70,
  },
  {
    id: "auth",
    label: "auth-service",
    type: "service",
    status: "alert",
    x: 380,
    y: 70,
  },
  {
    id: "db",
    label: "user-database",
    type: "database",
    status: "healthy",
    x: 380,
    y: 190,
  },
];

export function TopologyGraph({
  selectedService,
}: { selectedService: string }) {
  const getStatusColor = (status: Node["status"]) => {
    switch (status) {
      case "alert":
        return "#ef4444";
      case "impacted":
        return "#f59e0b";
      case "healthy":
        return "#10b981";
      default:
        return "#38bdf8";
    }
  };

  return (
    <div
      style={{
        width: "100%",
        height: "260px",
        background: "#050811",
        borderRadius: "8px",
        position: "relative",
        overflow: "hidden",
        border: "1px solid var(--border-color)",
      }}
    >
      <svg
        role="img"
        aria-label="System dependency topology graph"
        width="100%"
        height="100%"
        viewBox="0 0 500 250"
        style={{ display: "block" }}
      >
        <title>System Dependency Topology Graph</title>
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="22"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
          </marker>
        </defs>

        {/* Edges */}
        <line
          x1="120"
          y1="70"
          x2="220"
          y2="70"
          stroke="#475569"
          strokeWidth="2"
          strokeDasharray="4"
          markerEnd="url(#arrow)"
        />
        <line
          x1="280"
          y1="70"
          x2="380"
          y2="70"
          stroke="#f59e0b"
          strokeWidth="2"
          markerEnd="url(#arrow)"
        />
        <line
          x1="380"
          y1="95"
          x2="380"
          y2="170"
          stroke="#ef4444"
          strokeWidth="2"
          markerEnd="url(#arrow)"
        />

        {/* Nodes */}
        {NODES.map((node) => {
          const isTarget = node.label === selectedService;
          const color = getStatusColor(node.status);
          return (
            <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
              {node.status === "alert" && (
                <circle
                  r="30"
                  fill="none"
                  stroke={color}
                  strokeWidth="1.5"
                  opacity="0.4"
                >
                  <animate
                    attributeName="r"
                    values="24;36;24"
                    dur="2s"
                    repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    values="0.8;0.1;0.8"
                    dur="2s"
                    repeatCount="indefinite"
                  />
                </circle>
              )}
              <rect
                x="-50"
                y="-20"
                width="100"
                height="40"
                rx="8"
                fill="#0f172a"
                stroke={isTarget ? "#38bdf8" : color}
                strokeWidth={isTarget ? "2.5" : "1.5"}
                style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.5))" }}
              />
              <text
                textAnchor="middle"
                y="4"
                fill="#f8fafc"
                fontSize="11"
                fontFamily="var(--font-mono)"
                fontWeight="600"
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
