import { useState, useCallback } from 'react';

const API = `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/trading`;

export function useRealtime() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const start30Days = useCallback(async (tickers, capital) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/start-30days`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          tickers, 
          initial_capital: capital,
          interval_seconds: 3600 
        }),
      });
      if (!res.ok) throw new Error(`Failed to start trading: ${res.statusText}`);
      const result = await res.json();
      setStatus(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const stop30Days = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/stop-30days`, { method: 'POST' });
      if (!res.ok) throw new Error(`Failed to stop trading: ${res.statusText}`);
      const result = await res.json();
      setStatus(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/30days-status`);
      const result = await res.json();
      setStatus(result);
      return result;
    } catch (err) {
      setError(err.message);
    }
  }, []);

  return { status, loading, error, start30Days, stop30Days, getStatus };
}
