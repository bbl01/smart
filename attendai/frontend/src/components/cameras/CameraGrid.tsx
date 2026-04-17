/**
 * Сетка видеопотоков с IP-камер
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';
import { camerasApi } from '../../utils/api';
import { useDashboardStore } from '../../store';
import { RefreshCw, Wifi, WifiOff, AlertTriangle, Maximize2 } from 'lucide-react';

interface Camera {
  id: string;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'error' | 'maintenance';
  resolution?: string;
  snapshot_url?: string;
}

function CameraCard({ camera }: { camera: Camera }) {
  const { cameraStatuses } = useDashboardStore();
  const liveStatus = cameraStatuses[camera.id]?.status || camera.status;

  const isOnline = liveStatus === 'online';
  const isOffline = liveStatus === 'offline';
  const isError = liveStatus === 'error';

  return (
    <div className="relative rounded-lg overflow-hidden bg-gray-900 aspect-video group">
      {/* Video feed placeholder / snapshot */}
      {isOnline && camera.snapshot_url ? (
        <img
          src={camera.snapshot_url}
          alt={camera.name}
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gray-900">
          {isOffline && (
            <div className="text-center">
              <WifiOff className="w-6 h-6 text-gray-600 mx-auto mb-1" />
              <p className="text-gray-600 text-[10px] font-mono uppercase">НЕТ СИГНАЛА</p>
            </div>
          )}
          {isError && (
            <div className="text-center">
              <AlertTriangle className="w-5 h-5 text-red-500 mx-auto mb-1" />
              <p className="text-red-500 text-[10px] font-mono uppercase">ОШИБКА</p>
            </div>
          )}
          {isOnline && (
            // Симуляция видеопотока (в production — HLS/WebRTC)
            <div className="w-full h-full bg-gradient-to-b from-gray-900 to-gray-800 flex items-center justify-center">
              <div className="text-center">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mx-auto mb-1" />
                <p className="text-gray-500 text-[10px] font-mono">LIVE</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Top overlay */}
      <div className="absolute top-0 left-0 right-0 flex justify-between items-center p-1.5 bg-gradient-to-b from-black/60 to-transparent">
        <span className="text-[9px] font-mono text-white/70 bg-black/40 px-1.5 py-0.5 rounded">
          CAM-{camera.id.slice(-2).toUpperCase()}
        </span>
        {isOnline ? (
          <span className="flex items-center gap-1 text-[9px] font-semibold text-emerald-400 bg-black/40 px-1.5 py-0.5 rounded">
            <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
            LIVE
          </span>
        ) : (
          <span className={clsx(
            'text-[9px] font-semibold bg-black/40 px-1.5 py-0.5 rounded',
            isError ? 'text-red-400' : 'text-gray-400'
          )}>
            {liveStatus.toUpperCase()}
          </span>
        )}
      </div>

      {/* Bottom overlay */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-between items-center p-1.5 bg-gradient-to-t from-black/60 to-transparent">
        <span className="text-[9px] text-white/80">{camera.location}</span>
        {isOnline && (
          <span className="text-[9px] text-white/50 font-mono">
            {cameraStatuses[camera.id]?.persons_detected || 0} чел.
          </span>
        )}
      </div>

      {/* Hover actions */}
      <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
        <button
          className="bg-white/10 hover:bg-white/20 text-white p-1.5 rounded-lg transition-colors"
          title="Обновить"
          onClick={() => camerasApi.restart(camera.id).catch(() => {})}
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
        <button
          className="bg-white/10 hover:bg-white/20 text-white p-1.5 rounded-lg transition-colors"
          title="На весь экран"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

export default function CameraGrid() {
  const { data: cameras, isLoading } = useQuery({
    queryKey: ['cameras'],
    queryFn: () => camerasApi.list().then(r => r.data),
    refetchInterval: 15_000,
  });

  const onlineCount = cameras?.filter((c: Camera) => c.status === 'online').length ?? 0;
  const totalCount = cameras?.length ?? 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-white">Видеопотоки</h3>
          {totalCount > 0 && (
            <span className={clsx(
              'text-xs px-2 py-0.5 rounded-full font-medium',
              onlineCount === totalCount
                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                : 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
            )}>
              {onlineCount}/{totalCount} онлайн
            </span>
          )}
        </div>
        <Wifi className="w-4 h-4 text-gray-400" />
      </div>

      <div className="p-4">
        {isLoading ? (
          <div className="grid grid-cols-3 gap-2">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="aspect-video bg-gray-100 dark:bg-gray-700 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : cameras?.length ? (
          <div className="grid grid-cols-3 gap-2">
            {cameras.map((camera: Camera) => (
              <CameraCard key={camera.id} camera={camera} />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <Wifi className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">Камеры не подключены</p>
            <p className="text-xs mt-1">Добавьте камеры в разделе настроек</p>
          </div>
        )}
      </div>
    </div>
  );
}
