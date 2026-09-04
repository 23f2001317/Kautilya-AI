// apps/web/src/hooks/useWebSocketFeed.ts
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

export interface FeedLogEntry {
  id: string;
  timestamp: string;
  source: string;
  message: string;
  correlation_id?: string;
}

interface WebSocketOptions {
  url?: string;
  onIncidentEvent?: (eventType: string, data: any) => void;
}

export function useWebSocketFeed(options?: WebSocketOptions) {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [logs, setLogs] = useState<FeedLogEntry[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const onIncidentEventRef = useRef(options?.onIncidentEvent);

  useEffect(() => {
    onIncidentEventRef.current = options?.onIncidentEvent;
  }, [options?.onIncidentEvent]);

  const defaultUrl =
    typeof window !== 'undefined'
      ? `ws://${window.location.hostname}:8000/ws/incidents`
      : 'ws://localhost:8000/ws/incidents';

  const wsUrl = options?.url || defaultUrl;

  const appendLog = useCallback((source: string, message: string, correlation_id?: string) => {
    const entry: FeedLogEntry = {
      id: `log-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toISOString(),
      source,
      message,
      correlation_id,
    };
    setLogs((prev) => [...prev.slice(-150), entry]);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setConnectionStatus('connecting');
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        appendLog('SYSTEM', 'Secure WebSocket telemetry feed established with Kautilya Control Plane');

        // Keep-alive heartbeat to prevent silent disconnects
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ event: 'ping' }));
          }
        }, 15000);

        (ws as any)._pingInterval = pingInterval;
      };

      ws.onmessage = (evt) => {
        try {
          const payload = JSON.parse(evt.data);
          // Ignore ack/pong events for logs
          if (payload.event === 'ack') return;
          const eventType = payload.event_type ?? payload.event;
          const { data } = payload;

          if (eventType === 'agent_thought') {
            appendLog(data.source || 'AGENT', data.message, data.correlation_id);
          } else if (eventType === 'incident_created') {
            appendLog('ORCHESTRATOR', `New incident ${data.incident_id} detected on service ${data.service}`, data.correlation_id);
            onIncidentEventRef.current?.(eventType, data);
          } else if (eventType === 'incident_updated') {
            appendLog('GRAPH', `Incident ${data.incident_id} transition to ${data.status.toUpperCase()}`, data.correlation_id);
            onIncidentEventRef.current?.(eventType, data);
          } else if (eventType === 'incident_resolved') {
            appendLog('GOVERNANCE', `Remediation approved by ${data.signer}. Automated PR dispatched: ${data.pr_url}`);
            onIncidentEventRef.current?.(eventType, data);
          }
        } catch {
          // Plain text log fallback
          appendLog('STREAM', String(evt.data));
        }
      };

      ws.onclose = () => {
        if ((ws as any)._pingInterval) {
          clearInterval((ws as any)._pingInterval);
        }
        setConnectionStatus('disconnected');
        wsRef.current = null;
        // Exponential backoff with jitter: min 1s, max 10s
        const backoffMs = Math.min(
          1000 * Math.pow(2, reconnectAttemptsRef.current) + Math.random() * 500,
          10000
        );
        reconnectAttemptsRef.current += 1;
        reconnectTimerRef.current = setTimeout(connect, backoffMs);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      setConnectionStatus('disconnected');
      reconnectTimerRef.current = setTimeout(connect, 3000);
    }
  }, [wsUrl, appendLog]);

  const clearLogs = useCallback(() => setLogs([]), []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        if ((wsRef.current as any)._pingInterval) {
          clearInterval((wsRef.current as any)._pingInterval);
        }
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.onopen = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { connectionStatus, logs, clearLogs };
}
