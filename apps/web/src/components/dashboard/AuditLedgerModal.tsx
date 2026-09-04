// apps/web/src/components/dashboard/AuditLedgerModal.tsx
'use client';

import { useState } from 'react';
import type { AuditStatus } from '../../types/audit';

interface AuditLedgerModalProps {
  auditStatus: AuditStatus | null;
  onClose: () => void;
  onTamperTest: () => Promise<void>;
  onRefresh: () => Promise<void>;
}

export function AuditLedgerModal({
  auditStatus,
  onClose,
  onTamperTest,
  onRefresh,
}: AuditLedgerModalProps) {
  const [isTampering, setIsTampering] = useState(false);

  const handleTamper = async () => {
    setIsTampering(true);
    try {
      await onTamperTest();
    } finally {
      setIsTampering(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '850px' }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
              WORM Cryptographic Audit Ledger
            </h3>
            <span
              className={`badge ${auditStatus?.is_tampered ? 'badge-critical' : 'badge-resolved'}`}
            >
              {auditStatus?.is_tampered ? 'TAMPERED / INTEGRITY BREACH' : 'CRYPTOGRAPHICALLY VALID'}
            </span>
          </div>
          <button className="btn-ghost" onClick={onClose}>✕</button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            <div style={{ background: 'rgba(0,0,0,0.4)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Status</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: auditStatus?.is_tampered ? '#f87171' : '#34d399' }}>
                {auditStatus?.status.toUpperCase() || 'UNKNOWN'}
              </div>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.4)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Total Blocks</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
                {auditStatus?.total_entries || 0}
              </div>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.4)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Chain Head (SHA-256)</div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#cbd5e1', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {auditStatus?.chain_head.slice(0, 16)}...
              </div>
            </div>
          </div>

          {/* Audit explanation alert */}
          <div
            style={{
              background: auditStatus?.is_tampered ? 'rgba(239, 68, 68, 0.1)' : 'rgba(56, 189, 248, 0.08)',
              border: `1px solid ${auditStatus?.is_tampered ? 'rgba(239, 68, 68, 0.3)' : 'rgba(56, 189, 248, 0.2)'}`,
              borderRadius: '8px',
              padding: '10px 14px',
              fontSize: '0.78rem',
              color: auditStatus?.is_tampered ? '#fca5a5' : '#bae6fd',
              lineHeight: 1.4,
            }}
          >
            {auditStatus?.message || 'Every incident transition and remediation action is cryptographically chained via SHA-256 and locked under SOC2 WORM specifications.'}
          </div>

          {/* Blocks Table */}
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, marginBottom: '8px', color: '#e2e8f0' }}>
              Recent Cryptographic Blocks
            </div>
            <div
              style={{
                background: '#04060d',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                maxHeight: '260px',
                overflowY: 'auto',
              }}
            >
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem', textAlign: 'left', fontFamily: 'var(--font-mono)' }}>
                <thead>
                  <tr style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-subtle)' }}>
                    <th style={{ padding: '8px 12px' }}>#</th>
                    <th style={{ padding: '8px 12px' }}>Event</th>
                    <th style={{ padding: '8px 12px' }}>Actor</th>
                    <th style={{ padding: '8px 12px' }}>Prev Hash</th>
                    <th style={{ padding: '8px 12px' }}>Entry Hash</th>
                  </tr>
                </thead>
                <tbody>
                  {(auditStatus?.recent_blocks || []).map((block) => (
                    <tr key={block.entry_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <td style={{ padding: '8px 12px', color: '#38bdf8' }}>{block.entry_id}</td>
                      <td style={{ padding: '8px 12px', color: '#fff', fontWeight: 600 }}>{block.event_name}</td>
                      <td style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>{block.actor}</td>
                      <td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>{block.prev_hash}</td>
                      <td style={{ padding: '8px 12px', color: '#34d399' }}>{block.hash}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
          <button
            onClick={handleTamper}
            disabled={isTampering}
            className="btn btn-danger"
            style={{ fontSize: '0.76rem' }}
          >
            {isTampering ? 'Corrupting Block...' : '⚠ Simulate Tamper Test'}
          </button>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={onRefresh} className="btn btn-outline" style={{ fontSize: '0.76rem' }}>
              Re-verify Chain
            </button>
            <button onClick={onClose} className="btn btn-primary" style={{ fontSize: '0.76rem' }}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
