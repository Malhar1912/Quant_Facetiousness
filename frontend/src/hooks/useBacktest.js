import { useState, useCallback } from 'react';

const API = 'http://localhost:8000/api';

export function useBacktest() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState('');

  const runBacktest = useCallback(async (tickers, start, end, capital) => {
    setLoading(true);
    setError(null);
    setProgress('Initializing backtest engine...');
    try {
      const res = await fetch(`${API}/backtest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tickers, start, end, capital }),
      });
      if (!res.ok) throw new Error(`Backtest failed: ${res.statusText}`);
      const result = await res.json();
      setData(result);
      setProgress('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadLatest = useCallback(async () => {
    setLoading(true);
    setError(null);
    setProgress('Loading latest results...');
    try {
      const res = await fetch(`${API}/latest`);
      const result = await res.json();
      if (result.id) setData(result);
      setProgress('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadRun = useCallback(async (runId) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/runs/${runId}`);
      const result = await res.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, progress, runBacktest, loadLatest, loadRun };
}
