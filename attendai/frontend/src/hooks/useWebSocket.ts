/**
 * Хук для WebSocket подключения к live-ленте событий.
 * Автоматически переподключается при обрыве.
 */
import { useCallback, useEffect, useRef } from 'react';
import { createWebSocket } from '../utils/api';
import { useDashboardStore } from '../store';
import type { LiveEvent } from '../store';

const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  const { addLiveEvent, updateCameraStatus, setWsConnected } = useDashboardStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = createWebSocket();
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectAttempts.current = 0;
      setWsConnected(true);
      console.log('[WS] Подключено к AttendAI Live Feed');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        console.warn('[WS] Неверный JSON:', event.data);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      console.log('[WS] Соединение закрыто');
      scheduleReconnect();
    };

    ws.onerror = (err) => {
      console.error('[WS] Ошибка:', err);
      ws.close();
    };
  }, []);

  const handleMessage = useCallback((data: Record<string, unknown>) => {
    switch (data.type) {
      case 'face_detected': {
        const event: LiveEvent = {
          id: crypto.randomUUID(),
          type: 'face_detected',
          camera_id: data.camera_id as string,
          person_id: data.person_id as string | undefined,
          person_name: data.person_name as string | undefined,
          confidence: data.confidence as number | undefined,
          is_known: data.is_known as boolean,
          timestamp: data.timestamp as string || new Date().toISOString(),
        };
        addLiveEvent(event);
        break;
      }

      case 'camera_status': {
        updateCameraStatus(data.camera_id as string, {
          status: data.status as 'online' | 'offline' | 'error',
        });
        break;
      }

      case 'alert': {
        const event: LiveEvent = {
          id: crypto.randomUUID(),
          type: 'alert',
          message: data.message as string,
          timestamp: new Date().toISOString(),
        };
        addLiveEvent(event);
        break;
      }

      case 'heartbeat':
        // Молча обрабатываем heartbeat
        break;
    }
  }, [addLiveEvent, updateCameraStatus]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
      console.warn('[WS] Превышено количество попыток переподключения');
      return;
    }

    const delay = RECONNECT_DELAY * Math.min(reconnectAttempts.current + 1, 5);
    reconnectAttempts.current++;
    console.log(`[WS] Переподключение через ${delay}ms (попытка ${reconnectAttempts.current})`);

    reconnectTimer.current = setTimeout(connect, delay);
  }, [connect]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    wsRef.current = null;
    setWsConnected(false);
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  return { sendMessage, disconnect };
}
