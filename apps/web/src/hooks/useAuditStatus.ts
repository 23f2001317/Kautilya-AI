// apps/web/src/hooks/useAuditStatus.ts
'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { AuditStatus } from '../types/audit';

export function useAuditStatus(pollIntervalMs: number = 10000) {
  const [auditStatus, setAuditStatus] = useState<AuditStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    try {
      const data = await api.getAuditStatus();
      setAuditStatus(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to verify audit ledger');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const triggerTamperTest = useCallback(async () => {
    try {
      await api.triggerTamperTest();
      await refetch();
    } catch (err: any) {
      setError(err.message || 'Tamper simulation failed');
    }
  }, [refetch]);

  useEffect(() => {
    refetch();
    if (pollIntervalMs > 0) {
      const timer = setInterval(refetch, pollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [refetch, pollIntervalMs]);

  return { auditStatus, isLoading, error, refetch, triggerTamperTest };
}
