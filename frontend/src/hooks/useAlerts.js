/* ═══════════════════════════════════════════════════════════════════════
   useAlerts Hook — Real WebSocket alerts from backend
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useEffect, useCallback, useRef } from 'react';
import { getApiBaseUrl } from '../lib/api';

function resolveSeverity(value) {
  const normalized = String(value || '').toLowerCase();
  if (normalized === 'critical' || normalized === 'high') return 'CRITICAL';
  if (normalized === 'medium' || normalized === 'warning') return 'WARNING';
  return 'INFO';
}

function mapSocketAlert(payload) {
  const severity = resolveSeverity(payload?.severity);
  const timestamp = new Date().toISOString();
  const fallbackMessage = payload?.event
    ? `Event: ${payload.event}`
    : 'New monitoring alert received.';

  return {
    id: payload?.violation_id || payload?.id || crypto.randomUUID(),
    severity,
    message: payload?.summary || fallbackMessage,
    platform: payload?.platform || null,
    morphScore: payload?.morph_score ?? null,
    url: payload?.source_url || null,
    timestamp,
    read: false,
  };
}

function getWsUrl(token) {
  const apiBase = getApiBaseUrl();
  const wsBase = apiBase.startsWith('https://')
    ? apiBase.replace('https://', 'wss://')
    : apiBase.replace('http://', 'ws://');
  if (!token) {
    return `${wsBase}/ws/alerts`;
  }
  return `${wsBase}/ws/alerts?token=${encodeURIComponent(token)}`;
}

export function useAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);
  const reconnectRef = useRef(null);
  const heartbeatRef = useRef(null);

  useEffect(() => {
    let active = true;
    const token = localStorage.getItem('verilens_access_token') || localStorage.getItem('access_token');

    const connect = () => {
      if (!active) return;

      const socket = new WebSocket(getWsUrl(token));
      socketRef.current = socket;

      socket.onopen = () => {
        setConnected(true);
        if (heartbeatRef.current) {
          clearInterval(heartbeatRef.current);
        }
        heartbeatRef.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send('ping');
          }
        }, 20000);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const alert = mapSocketAlert(payload);
          setAlerts((prev) => [alert, ...prev].slice(0, 100));
        } catch (error) {
          console.error('Invalid websocket alert payload:', error);
        }
      };

      socket.onerror = () => {
        setConnected(false);
      };

      socket.onclose = () => {
        setConnected(false);
        if (heartbeatRef.current) {
          clearInterval(heartbeatRef.current);
          heartbeatRef.current = null;
        }
        if (active) {
          reconnectRef.current = setTimeout(connect, 3000);
        }
      };
    };

    connect();

    return () => {
      active = false;
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current);
      }
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.close();
      }
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

