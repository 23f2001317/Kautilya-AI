// apps/web/src/components/dashboard/Header.tsx
'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldAlert, Terminal, AlertTriangle, ShieldCheck, Activity, Zap, Play, Settings } from 'lucide-react';
import type { ConnectionStatus } from '../../hooks/useWebSocketFeed';
import type { AuditStatus } from '../../types/audit';

interface HeaderProps {
  wsStatus: ConnectionStatus;
  auditStatus: AuditStatus | null;
  activeCount: number;
  onOpenAudit: () => void;
  onSimulate: (archetype?: string) => Promise<void>;
  isSimulating: boolean;
  onOpenConfig?: () => void;
}

export function Header({
  wsStatus,
  auditStatus,
  activeCount,
  onOpenAudit,
  onSimulate,
  isSimulating,
  onOpenConfig,
}: HeaderProps) {
  const [showSimMenu, setShowSimMenu] = useState(false);

  const archetypes = [
    { id: 'db_pool', name: 'Database Pool Saturation', service: 'Any Service' },
    { id: 'redis_cache', name: 'Cache Eviction Surge', service: 'Any Service' },
    { id: 'gateway_timeout', name: 'Gateway Timeout & Latency', service: 'Any Service' },
    { id: 'memory_leak', name: 'Worker Memory Growth', service: 'Any Service' },
  ];

  const handleSelectSim = async (archId: string) => {
    setShowSimMenu(false);
    await onSimulate(archId);
  };

  return (
    <header
      className="glass-panel"
      style={{
        padding: '20px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '20px',
        position: 'relative',
        zIndex: 9999,
      }}
    >
      {/* Brand & Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.2) 0%, rgba(14, 165, 233, 0.1) 100%)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
          }}
        >
          <img src="/logo.jpg" alt="Kautilya AI Logo" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1
              style={{
                fontSize: '1.05rem',
                fontWeight: 600,
                letterSpacing: '-0.01em',
                color: 'var(--text-primary)',
              }}
            >
              Kautilya AI
            </h1>
            <span
              className="badge"
              style={{
                fontSize: '0.68rem',
                padding: '1px 7px',
              }}
            >
              SRE Console
            </span>
          </div>
          <p
            style={{
              fontSize: '0.76rem',
              color: 'var(--text-muted)',
              marginTop: '1px',
            }}
          >
            Autonomous Incident Remediation & Governance
          </p>
        </div>
      </div>

      {/* Actions & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
        {/* Active Incidents Counter */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: '8px',
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.78rem',
          }}
        >
          <span style={{ color: 'var(--text-secondary)' }}>Active Queue</span>
          <span
            style={{
              fontWeight: 600,
              color: activeCount > 0 ? 'var(--color-primary)' : 'var(--text-muted)',
            }}
          >
            {activeCount}
          </span>
        </div>

        {/* Audit Ledger Trigger */}
        <button
          type="button"
          onClick={onOpenAudit}
          className="btn btn-outline"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 14px',
            fontSize: '0.78rem',
            color: auditStatus?.is_tampered ? '#ef4444' : '#10b981',
            borderColor: auditStatus?.is_tampered ? 'rgba(239,68,68,0.3)' : 'rgba(16,185,129,0.3)',
            background: auditStatus?.is_tampered ? 'rgba(239,68,68,0.05)' : 'rgba(16,185,129,0.05)',
          }}
        >
          {auditStatus?.is_tampered ? <AlertTriangle size={14} /> : <ShieldCheck size={14} />}
          <span>Ledger {auditStatus?.is_tampered ? 'Tampered' : 'Verified'}</span>
        </button>

        {onOpenConfig && (
          <button
            type="button"
            onClick={onOpenConfig}
            className="btn btn-outline"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              fontSize: '0.78rem',
            }}
          >
            <Settings size={14} />
            <span>Settings</span>
          </button>
        )}

        {/* Progressive Disclosure: Simulation Dropdown */}
        <div style={{ position: 'relative' }}>
          <button
            type="button"
            onClick={() => setShowSimMenu(!showSimMenu)}
            disabled={isSimulating}
            className="btn btn-primary"
            style={{
              fontSize: '0.78rem',
              padding: '6px 14px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Play size={12} />
            <span>{isSimulating ? 'Injecting...' : 'Simulate Alert'}</span>
          </button>

          <AnimatePresence>
            {showSimMenu && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                transition={{ duration: 0.15 }}
                className="glass-panel"
                style={{
                  position: 'absolute',
                  top: 'calc(100% + 8px)',
                  right: 0,
                  width: '260px',
                  zIndex: 60,
                  padding: '6px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '2px',
                  boxShadow: '0 12px 32px rgba(0, 0, 0, 0.6)',
                }}
              >
                <div
                  style={{
                    padding: '6px 10px',
                    fontSize: '0.7rem',
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  Select Scenario
                </div>
                {archetypes.map((arch) => (
                  <button
                    key={arch.id}
                    type="button"
                    onClick={() => handleSelectSim(arch.id)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      gap: '2px',
                      padding: '8px 10px',
                      borderRadius: '6px',
                      background: 'transparent',
                      border: 'none',
                      textAlign: 'left',
                      cursor: 'pointer',
                      color: 'var(--text-primary)',
                      transition: 'background-color 0.12s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'var(--bg-active)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'transparent';
                    }}
                  >
                    <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>{arch.name}</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{arch.service}</span>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Telemetry Stream Dot */}
        <div
          title={`WebSocket telemetry: ${wsStatus}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 10px',
            fontSize: '0.74rem',
            color: 'var(--text-muted)',
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: wsStatus === 'connected' ? 'var(--color-accent)' : '#fb7185',
            }}
          />
          <span>{wsStatus}</span>
        </div>
      </div>
    </header>
  );
}
