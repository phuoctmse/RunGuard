import { useEffect, useState, useCallback } from 'react';
import { fetchIncidents } from '../api/client';
import type { Incident } from '../types';

const POLL_INTERVAL = 10_000;

export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchIncidents();
      setIncidents(data);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_INTERVAL);
    return () => clearInterval(timer);
  }, [load]);

  return { incidents, loading, error, refresh: load };
}
