// apps/web/src/components/dashboard/IncidentFeed.tsx
'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle, Clock, XCircle } from 'lucide-react';
import type { Incident, IncidentStatus } from '../../types/incident';

interface IncidentFeedProps {
  incidents: Incident[];
  selectedService: string | null;
  onSelectIncident: (incident: Incident) => void;
  isLoading: boolean;
}

export function IncidentFeed({
  incidents,
  selectedService,
  onSelectIncident,
  isLoading,
}: IncidentFeedProps) {
  const [filter, setFilter] = useState<'all' | 'active' | 'resolved'>('all');

  const filtered = incidents.filter((inc) => {
    if (selectedService && inc.service_name !== selectedService) {
      return false;
    }
    if (filter === 'active') {
      return inc.status === 'triaging' || inc.status === 'patch_ready';
    }
    if (filter === 'resolved') {
      return inc.status === 'resolved' || inc.status === 'approved';
    }
    return true;
  });

  const getStatusBadge = (status: IncidentStatus) => {
    switch (status) {
      case 'triaging':
        return <span className="badge badge-triaging"><Clock size={10} style={{marginRight: 4}}/> Triaging</span>;
      case 'patch_ready':
        return <span className="badge badge-ready"><AlertCircle size={10} style={{marginRight: 4}}/> Patch Ready</span>;
      case 'approved':
      case 'resolved':
        return <span className="badge badge-resolved"><CheckCircle size={10} style={{marginRight: 4}}/> Resolved</span>;
      case 'rejected':
        return <span className="badge badge-rejected"><XCircle size={10} style={{marginRight: 4}}/> Rejected</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: '24px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
      }}
    >
      {/* Title & Filter Tabs */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h2
            style={{
              fontSize: '0.95rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
            }}
          >
            Incident Queue
          </h2>
          <span
            className="badge"
            style={{
              fontSize: '0.7rem',
              padding: '1px 8px',
            }}
          >
            {filtered.length}
          </span>
        </div>

        {/* Filter Pills */}
        <div
          style={{
            display: 'flex',
            background: 'var(--bg-subtle)',
            padding: '2px',
            borderRadius: '8px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {(['all', 'active', 'resolved'] as const).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              style={{
                padding: '4px 12px',
                fontSize: '0.74rem',
                fontWeight: 600,
                background: filter === f ? 'var(--bg-active)' : 'transparent',
                color: filter === f ? 'var(--text-primary)' : 'var(--text-muted)',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                textTransform: 'capitalize',
                transition: 'all 0.12s ease',
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Selected Service Scope Filter Tag */}
      {selectedService && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 12px',
            background: 'rgba(56, 189, 248, 0.05)',
            border: '1px solid rgba(56, 189, 248, 0.2)',
            borderRadius: '8px',
            fontSize: '0.76rem',
          }}
        >
          <span style={{ color: 'var(--color-primary)' }}>
            Filtered by service: <strong>{selectedService}</strong>
          </span>
        </div>
      )}

      {/* Incidents List */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          maxHeight: '480px',
          overflowY: 'auto',
          paddingRight: '4px',
        }}
      >
        {isLoading && (
          <div
            style={{
              padding: '40px 0',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontSize: '0.82rem',
            }}
          >
            Loading incident feed...
          </div>
        )}

        {!isLoading && filtered.length === 0 && (
          <div
            style={{
              padding: '48px 0',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontSize: '0.82rem',
            }}
          >
            No incidents found in this view.
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {filtered.map((inc, idx) => (
            <motion.div
              key={inc.id}
              initial={{ opacity: 0, x: -20, height: 0 }}
              animate={{ opacity: 1, x: 0, height: 'auto' }}
              exit={{ opacity: 0, scale: 0.9, height: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.05 }}
              onClick={() => onSelectIncident(inc)}
              className="glass-panel"
              style={{
                padding: '16px 20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                cursor: 'pointer',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                transition: 'background-color 0.15s ease, border-color 0.15s ease',
                marginBottom: '12px'
              }}
              whileHover={{ 
                scale: 1.01, 
                backgroundColor: 'var(--bg-active)',
                borderColor: 'var(--border-muted)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '12px',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--color-primary)',
                        fontWeight: 600,
                      }}
                    >
                      {inc.service_name}
                    </span>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        color: 'var(--text-muted)',
                      }}
                    >
                      • {inc.severity}
                    </span>
                  </div>
                  <h3
                    style={{
                      fontSize: '0.86rem',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      lineHeight: 1.4,
                    }}
                  >
                    {inc.title}
                  </h3>
                </div>
                <div>{getStatusBadge(inc.status)}</div>
              </div>

              {/* Hypothesis Summary */}
              {inc.hypothesis && (
                <p
                  style={{
                    fontSize: '0.78rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.5,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {inc.hypothesis}
                </p>
              )}

              {/* Footer metadata */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingTop: '8px',
                  borderTop: '1px solid rgba(255, 255, 255, 0.04)',
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                }}
              >
                <span>ID: {inc.id.slice(0, 12)}</span>
                {inc.confidence_score > 0 && (
                  <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                    Confidence: {Math.round(inc.confidence_score * 100)}%
                  </span>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
