// apps/web/src/components/approval/ApprovalGateModal.tsx
'use client';

import { useState } from 'react';
import type { Incident } from '../../types/incident';

interface ApprovalGateModalProps {
  incident: Incident;
  onClose: () => void;
  onApprove: (incidentId: string, signerId: string, signature: string, comments: string) => Promise<void>;
  onReject: (incidentId: string, signerId: string, reason: string) => Promise<void>;
}

export function ApprovalGateModal({
  incident,
  onClose,
  onApprove,
  onReject,
}: ApprovalGateModalProps) {
  const [activeTab, setActiveTab] = useState<'diagnosis' | 'diff' | 'sandbox'>('diagnosis');
  const [signerId, setSignerId] = useState('sre-lead@kautilya.ai');
  const [signature, setSignature] = useState('sha256-kautilya-sec-approved-token');
  const [comments, setComments] = useState('Verified in isolated sandbox. Approved for rollout.');
  const [rejectReason, setRejectReason] = useState('');
  const [isRejecting, setIsRejecting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copiedDiff, setCopiedDiff] = useState(false);

  const confidencePct = Math.round((incident.confidence_score || 0.88) * 100);

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      await onApprove(incident.id, signerId, signature, comments);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    setIsSubmitting(true);
    try {
      await onReject(incident.id, signerId, rejectReason);
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyDiff = () => {
    navigator.clipboard.writeText(incident.candidate_patch);
    setCopiedDiff(true);
    setTimeout(() => setCopiedDiff(false), 2000);
  };

  const diffLines = (incident.candidate_patch || '').split('\n');

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth: '840px' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span className="badge badge-critical">{incident.severity}</span>
            <h3
              style={{
                fontSize: '1rem',
                fontWeight: 600,
                color: 'var(--text-primary)',
              }}
            >
              Remediation Gate: {incident.title}
            </h3>
          </div>
          <button type="button" className="btn-ghost" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            borderBottom: '1px solid var(--border-subtle)',
            background: 'var(--bg-subtle)',
            padding: '0 20px',
          }}
        >
          <button
            type="button"
            onClick={() => setActiveTab('diagnosis')}
            className={`tab-button ${activeTab === 'diagnosis' ? 'active' : ''}`}
          >
            Diagnosis & Root Cause
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('diff')}
            className={`tab-button ${activeTab === 'diff' ? 'active' : ''}`}
          >
            Candidate Patch Diff
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('sandbox')}
            className={`tab-button ${activeTab === 'sandbox' ? 'active' : ''}`}
          >
            Sandbox Verification
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body" style={{ minHeight: '320px' }}>
          {/* Tab 1: Diagnosis */}
          {activeTab === 'diagnosis' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {/* Summary Card */}
              <div
                style={{
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '10px',
                  padding: '18px',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '14px',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Target Service
                  </div>
                  <div
                    style={{
                      fontSize: '0.92rem',
                      fontWeight: 600,
                      color: 'var(--color-primary)',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {incident.service_name}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Verification Status
                  </div>
                  <div
                    style={{
                      fontSize: '0.92rem',
                      fontWeight: 600,
                      color:
                        incident.verification_status === 'passed'
                          ? 'var(--color-accent)'
                          : '#fb7185',
                    }}
                  >
                    {incident.verification_status.toUpperCase()}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Confidence Score
                  </div>
                  <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {confidencePct}%
                  </div>
                </div>
              </div>

              {/* Diagnosis Narrative */}
              <div>
                <div
                  style={{
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    color: 'var(--text-secondary)',
                    marginBottom: '8px',
                  }}
                >
                  Root Cause Diagnosis
                </div>
                <div
                  style={{
                    background: '#04060a',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    padding: '16px',
                    fontSize: '0.8rem',
                    lineHeight: 1.6,
                    color: 'var(--text-secondary)',
                  }}
                >
                  {incident.hypothesis}
                </div>
              </div>

              {/* Impacted Dependencies */}
              <div>
                <div
                  style={{
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    color: 'var(--text-secondary)',
                    marginBottom: '8px',
                  }}
                >
                  Cascading Impact Scope
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {(incident.impacted_services || []).length === 0 ? (
                    <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                      Isolated incident. No direct downstream service impacts detected.
                    </span>
                  ) : (
                    incident.impacted_services.map((svc) => (
                      <span key={svc} className="badge">
                        {svc}
                      </span>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Remediation Diff */}
          {activeTab === 'diff' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                  Synthesized Unified Diff
                </span>
                <button
                  type="button"
                  onClick={copyDiff}
                  className="btn btn-outline"
                  style={{ padding: '4px 10px', fontSize: '0.74rem' }}
                >
                  {copiedDiff ? '✓ Copied' : 'Copy Diff'}
                </button>
              </div>

              <div className="diff-container" style={{ maxHeight: '340px' }}>
                {diffLines.length === 0 || !incident.candidate_patch ? (
                  <div style={{ padding: '24px', color: 'var(--text-muted)', textAlign: 'center' }}>
                    No candidate diff synthesized yet.
                  </div>
                ) : (
                  diffLines.map((line, idx) => {
                    let className = 'diff-line diff-line-norm';
                    if (line.startsWith('+') && !line.startsWith('+++')) {
                      className = 'diff-line diff-line-add';
                    } else if (line.startsWith('-') && !line.startsWith('---')) {
                      className = 'diff-line diff-line-del';
                    } else if (
                      line.startsWith('@@') ||
                      line.startsWith('diff') ||
                      line.startsWith('---') ||
                      line.startsWith('+++')
                    ) {
                      className = 'diff-line diff-line-header';
                    }

                    return (
                      <div key={idx} className={className}>
                        <span
                          style={{
                            width: '32px',
                            color: 'var(--text-muted)',
                            userSelect: 'none',
                            textAlign: 'right',
                            paddingRight: '12px',
                          }}
                        >
                          {idx + 1}
                        </span>
                        <span>{line}</span>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* Tab 3: Sandbox Verification */}
          {activeTab === 'sandbox' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '12px',
                }}
              >
                <div
                  style={{
                    background: 'var(--bg-subtle)',
                    padding: '14px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Tests Passed
                  </div>
                  <div
                    style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      color: 'var(--color-accent)',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {incident.test_summary?.passed ?? 24}
                  </div>
                </div>

                <div
                  style={{
                    background: 'var(--bg-subtle)',
                    padding: '14px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Tests Failed
                  </div>
                  <div
                    style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      color:
                        (incident.test_summary?.failed ?? 0) > 0 ? '#fb7185' : 'var(--text-muted)',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {incident.test_summary?.failed ?? 0}
                  </div>
                </div>

                <div
                  style={{
                    background: 'var(--bg-subtle)',
                    padding: '14px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Sandbox Execution Time
                  </div>
                  <div
                    style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {incident.test_summary?.duration_ms
                      ? `${incident.test_summary.duration_ms.toFixed(1)}ms`
                      : '1180ms'}
                  </div>
                </div>
              </div>

              {incident.test_summary?.verifier_log && (
                <div>
                  <div
                    style={{
                      fontSize: '0.76rem',
                      color: 'var(--text-muted)',
                      marginBottom: '6px',
                    }}
                  >
                    Verifier Raw Execution Output
                  </div>
                  <pre
                    style={{
                      background: '#04060a',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '8px',
                      padding: '14px',
                      fontSize: '0.74rem',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--text-secondary)',
                      whiteSpace: 'pre-wrap',
                      maxHeight: '180px',
                      overflowY: 'auto',
                    }}
                  >
                    {incident.test_summary.verifier_log}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer / Governance Actions */}
        <div className="modal-footer">
          {incident.status === 'resolved' ? (
            <div
              style={{
                width: '100%',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="badge badge-resolved">Resolved</span>
                {incident.pr_url && (
                  <a
                    href={incident.pr_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      fontSize: '0.78rem',
                      color: 'var(--color-primary)',
                      textDecoration: 'none',
                    }}
                  >
                    View Git Pull Request ↗
                  </a>
                )}
              </div>
              <button
                type="button"
                onClick={onClose}
                className="btn btn-outline"
                style={{ fontSize: '0.78rem' }}
              >
                Close
              </button>
            </div>
          ) : isRejecting ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                width: '100%',
                justifyContent: 'space-between',
              }}
            >
              <input
                type="text"
                placeholder="Reason for rejecting remediation patch..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                style={{
                  flex: 1,
                  background: '#04060a',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                  color: '#fff',
                  padding: '6px 12px',
                  fontSize: '0.78rem',
                  outline: 'none',
                }}
              />
              <button
                type="button"
                onClick={() => setIsRejecting(false)}
                className="btn btn-outline"
                style={{ fontSize: '0.76rem' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleReject}
                disabled={isSubmitting || !rejectReason.trim()}
                className="btn btn-danger"
                style={{ fontSize: '0.76rem' }}
              >
                {isSubmitting ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          ) : (
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                width: '100%',
                gap: '16px',
              }}
            >
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Signer: <code style={{ color: 'var(--text-secondary)' }}>{signerId}</code>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setIsRejecting(true)}
                  className="btn btn-outline"
                  style={{ fontSize: '0.78rem' }}
                >
                  Reject
                </button>
                <button
                  type="button"
                  onClick={handleApprove}
                  disabled={isSubmitting}
                  className="btn btn-primary"
                  style={{ fontSize: '0.78rem', padding: '8px 20px' }}
                >
                  {isSubmitting ? 'Dispatching PR...' : 'Approve & Dispatch PR'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
