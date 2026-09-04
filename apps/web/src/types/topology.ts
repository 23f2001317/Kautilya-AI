// apps/web/src/types/topology.ts
/** Strict TypeScript models for dynamic microservice topology and blast radius graphs. */

export type NodeHealthStatus = 'healthy' | 'alert' | 'impacted';

export interface TopologyNode {
  id: string;
  name: string;
  label: string;
  type: string;
  tier: string;
  status: NodeHealthStatus;
  criticality: 'critical' | 'high' | 'medium' | 'low';
  x?: number;
  y?: number;
}

export interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
}

export interface TopologyData {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  total_nodes: number;
  total_edges: number;
  active_alerts: string[];
}
