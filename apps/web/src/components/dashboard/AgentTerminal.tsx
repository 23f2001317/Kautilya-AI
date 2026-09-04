// apps/web/src/components/dashboard/AgentTerminal.tsx
'use client';

import { useEffect, useRef, useState } from 'react';
import type { FeedLogEntry } from '../../hooks/useWebSocketFeed';

interface AgentTerminalProps {
  logs: FeedLogEntry[];
  onClearLogs: () => void;
}

export function AgentTerminal({ logs, onClearLogs }: AgentTerminalProps) {
  const [filterSource, setFilterSource] = useState<string>('ALL');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const sources = ['ALL', 'INGEST', 'TRIAGE', 'CODER', 'SANDBOX', 'GOVERNANCE'];

  const filteredLogs = logs.filter((l) => {
    if (filterSource === 'ALL') return true;
    return l.source.toUpperCase().includes(filterSource);
  });

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [filteredLogs.length, autoScroll]);

  const copyToClipboard = () => {
    const text = filteredLogs
      .map((l) => `[${l.timestamp}] [${l.source}] ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text);
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: '24px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
      }}
    >
      {/* Title & Controls Bar */}
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
            Telemetry & Reasoning Stream
          </h2>
          <span
            className="badge"
            style={{
              fontSize: '0.7rem',
              padding: '1px 8px',
            }}
          >
            {filteredLogs.length} events
          </span>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setAutoScroll((prev) => !prev)}
            className="btn btn-outline"
            style={{
              padding: '4px 10px',
              fontSize: '0.74rem',
              color: autoScroll ? 'var(--color-primary)' : 'var(--text-muted)',
            }}
          >
            Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
          </button>
          <button
            type="button"
            onClick={copyToClipboard}
            className="btn btn-outline"
            style={{ padding: '4px 10px', fontSize: '0.74rem' }}
          >
            Copy
          </button>
          <button
            type="button"
            onClick={onClearLogs}
            className="btn btn-outline"
            style={{ padding: '4px 10px', fontSize: '0.74rem' }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Source Filter Tabs */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        {sources.map((src) => (
          <button
            key={src}
            type="button"
            onClick={() => setFilterSource(src)}
            style={{
              padding: '3px 10px',
              fontSize: '0.72rem',
              fontWeight: 600,
              borderRadius: '6px',
              border: '1px solid',
              borderColor: filterSource === src ? 'var(--color-primary)' : 'var(--border-subtle)',
              background: filterSource === src ? 'rgba(56, 189, 248, 0.08)' : 'transparent',
              color: filterSource === src ? 'var(--color-primary)' : 'var(--text-muted)',
              cursor: 'pointer',
              transition: 'all 0.12s ease',
            }}
          >
            {src}
          </button>
        ))}
      </div>

      {/* Terminal View */}
      <div
        ref={scrollRef}
        style={{
          background: '#04060a',
          border: '1px solid var(--border-subtle)',
          borderRadius: '10px',
          padding: '18px',
          minHeight: '180px',
          maxHeight: '260px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.78rem',
          lineHeight: 1.6,
        }}
      >
        {filteredLogs.length === 0 ? (
          <div
            style={{
              color: 'var(--text-muted)',
              textAlign: 'center',
              padding: '30px 0',
            }}
          >
            No active stream events recorded.
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <div
              key={`${log.timestamp}-${index}`}
              style={{
                display: 'flex',
                alignItems: 'baseline',
                gap: '12px',
                borderBottom: '1px solid rgba(255, 255, 255, 0.02)',
                paddingBottom: '4px',
              }}
            >
              <span
                style={{
                  color: 'var(--text-muted)',
                  fontSize: '0.72rem',
                  whiteSpace: 'nowrap',
                }}
              >
                {new Date(log.timestamp).toLocaleTimeString([], { hour12: false })}
              </span>
              <span
                style={{
                  color: 'var(--color-primary)',
                  fontWeight: 600,
                  fontSize: '0.72rem',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  background: 'rgba(56, 189, 248, 0.08)',
                  whiteSpace: 'nowrap',
                }}
              >
                {log.source}
              </span>
              <span
                style={{
                  color: 'var(--text-secondary)',
                  wordBreak: 'break-word',
                  flex: 1,
                }}
              >
                {log.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
