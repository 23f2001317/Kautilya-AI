// apps/web/src/types/audit.ts
/** Strict TypeScript models for WORM cryptographic audit ledger verification. */

export interface AuditBlock {
  entry_id: number;
  timestamp: string;
  event_name: string;
  actor: string;
  hash: string;
  prev_hash: string;
}

export interface AuditStatus {
  status: 'valid' | 'tampered';
  is_tampered: boolean;
  message: string;
  total_entries: number;
  chain_head: string;
  recent_blocks: AuditBlock[];
}
