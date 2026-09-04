// apps/web/src/hooks/useTopology.ts
'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { TopologyData } from '../types/topology';

export function useTopology(pollIntervalMs: number = 8000) {
  const [topology, setTopology] = useState<TopologyData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    try {
      const data = await api.getTopology();
      setTopology(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load topology');
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

  return { topology, isLoading, error, refetch };
}
