// apps/web/src/hooks/useIncidents.ts
'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { Incident } from '../types/incident';

export function useIncidents(pollIntervalMs: number = 5000) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    try {
      const data = await api.getIncidents();
      setIncidents(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load incidents');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
    if (pollIntervalMs > 0) {
      const timer = setInterval(refetch, pollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [refetch, pollIntervalMs]);

  return { incidents, isLoading, error, refetch, setIncidents };
}
