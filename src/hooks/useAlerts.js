/* ═══════════════════════════════════════════════════════════════════════
   useAlerts Hook — Simulated WebSocket real-time alert system
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useEffect, useCallback, useRef } from 'react';
import { generateAlert, generateInitialAlerts } from './useMockData';

export function useAlerts() {
  const [alerts, setAlerts] = useState(() => generateInitialAlerts(8));
  const [connected, setConnected] = useState(false);
  const intervalRef = useRef(null);

  // Simulate WebSocket connection
  useEffect(() => {
    const connectTimer = setTimeout(() => setConnected(true), 1500);

    // Simulate incoming alerts every 6-15 seconds
    intervalRef.current = setInterval(() => {
      if (Math.random() > 0.35) {
        const newAlert = generateAlert();
        setAlerts(prev => [newAlert, ...prev].slice(0, 100));
      }
    }, 8000);

    return () => {
      clearTimeout(connectTimer);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const markRead = useCallback((id) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, read: true } : a));
  }, []);

  const markAllRead = useCallback(() => {
    setAlerts(prev => prev.map(a => ({ ...a, read: true })));
  }, []);

  const unreadCount = alerts.filter(a => !a.read).length;
  const criticalCount = alerts.filter(a => a.severity === 'CRITICAL' && !a.read).length;

  return { alerts, connected, unreadCount, criticalCount, markRead, markAllRead };
}

