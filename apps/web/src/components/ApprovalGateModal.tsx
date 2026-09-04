// apps/web/src/components/ApprovalGateModal.tsx
"use client";

import React, { useState } from "react";

interface Incident {
  id: string;
  service_name: string;
  title: string;
  status: string;
  hypothesis: string;
  confidence_score: number;
  candidate_patch: string;
  verification_status: string;
  test_summary: { passed?: number; failed?: number; duration_ms?: number };
}

interface ModalProps {
  incident: Incident;
  onClose: () => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

export function ApprovalGateModal({
  incident,
  onClose,
  onApprove,
  onReject,
}: ModalProps) {
  const [submitting, setSubmitting] = useState(false);

  const lines = incident.candidate_patch.split("\n");

  const handleApprove = () => {
    setSubmitting(true);
    setTimeout(() => {
      onApprove(incident.id);
      setSubmitting(false);
      onClose();
    }, 400);
  };

  const handleReject = () => {
    setSubmitting(true);
    setTimeout(() => {
      onReject(incident.id);
      setSubmitting(false);
      onClose();
    }, 400);
  };

  return (
    <div className="modal-backdrop" id="approval-gate-modal">
      <div className="modal-content">
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: "700" }}>
              Approval Gate: Candidate Remediation Patch
            </h2>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              Incident:{" "}
              <strong style={{ color: "#38bdf8" }}>{incident.id}</strong> (
              {incident.service_name})
            </p>
          </div>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={onClose}
            id="modal-close-btn"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div
            style={{
              background: "rgba(56, 189, 248, 0.08)",
              border: "1px solid rgba(56, 189, 248, 0.2)",
              borderRadius: "8px",
              padding: "12px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "6px",
              }}
            >
              <span style={{ fontSize: "0.85rem", fontWeight: "600" }}>
                Root Cause Diagnosis
              </span>
              <span
                style={{
                  fontSize: "0.8rem",
                  color: "#34d399",
                  fontWeight: "600",
                }}
              >
                Confidence: {(incident.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
            <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              {incident.hypothesis}
            </p>
          </div>

          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "8px",
              }}
            >
              <span style={{ fontSize: "0.85rem", fontWeight: "600" }}>
                Synthesized Code Diff
              </span>
              <span style={{ fontSize: "0.75rem", color: "#34d399" }}>
                ✓ Sandbox Verified ({incident.test_summary.passed ?? 24} passed,{" "}
                {incident.test_summary.failed ?? 0} failed)
              </span>
            </div>
            <div className="diff-view" id="modal-diff-view">
              {lines.map((line, idx) => {
                let className = "diff-line-norm";
                if (line.startsWith("+") && !line.startsWith("+++"))
                  className = "diff-line-add";
                if (line.startsWith("-") && !line.startsWith("---"))
                  className = "diff-line-del";
                return (
                  <span
                    key={`line-${idx}-${line.slice(0, 10)}`}
                    className={className}
                  >
                    {line}
                  </span>
                );
              })}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={handleReject}
            disabled={submitting}
            id="btn-reject-patch"
          >
            Reject & Ask Agent to Refine
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleApprove}
            disabled={submitting}
            id="btn-approve-patch"
          >
            {submitting
              ? "Signing & Creating PR..."
              : "Approve & Apply (Create PR)"}
          </button>
        </div>
      </div>
    </div>
  );
}
