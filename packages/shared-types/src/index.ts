// packages/shared-types/src/index.ts
/**
 * Shared TypeScript definitions across Kautilya AI monorepo.
 */

export type AlertSource = "datadog" | "github" | "prometheus" | "pagerduty";
export type AlertSeverity = "critical" | "high" | "medium" | "low" | "info";
export type IncidentStatus = "triaging" | "patch_ready" | "approved" | "rejected" | "resolved";

export interface CanonicalAlert {
  id: string;
  source: AlertSource;
  external_id: string;
  service_name: string;
  title: string;
  severity: AlertSeverity;
  description: string;
  raw_payload: Record<string, unknown>;
  timestamp: string;
}

export interface Incident {
  id: string;
  service_name: string;
  title: string;
  severity: AlertSeverity;
  status: IncidentStatus;
  hypothesis: string;
  confidence_score: number;
  candidate_patch: string;
  verification_status: string;
  test_summary: {
    passed?: number;
    failed?: number;
    duration_ms?: number;
    retries?: number;
  };
  impacted_services: string[];
  pr_url?: string | null;
  created_at?: string;
  resolved_at?: string | null;
}

export interface RelayTask {
  task_id: string;
  task_type: string;
  payload: Record<string, unknown>;
  assigned_at: string;
}

export interface RelayResult {
  task_id: string;
  status: string;
  output: Record<string, unknown>;
  signature: string;
}
