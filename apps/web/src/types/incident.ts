// apps/web/src/types/incident.ts
/** Strict TypeScript models for autonomous SRE incidents and governance workflows. */

export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low';

export type IncidentStatus =
  | 'triaging'
  | 'patch_ready'
  | 'approved'
  | 'rejected'
  | 'resolved';

export interface TestSummary {
  passed: number;
  failed: number;
  duration_ms: number;
  retries?: number;
  verifier_log?: string;
}

export interface Incident {
  id: string;
  service_name: string;
  title: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  hypothesis: string;
  confidence_score: number;
  candidate_patch: string;
  verification_status: 'pending' | 'passed' | 'failed';
  test_summary: TestSummary;
  impacted_services: string[];
  pr_url?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface ApprovalPayload {
  signer_id: string;
  signature: string;
  comments?: string;
}

export interface RejectionPayload {
  signer_id: string;
  reason: string;
}
