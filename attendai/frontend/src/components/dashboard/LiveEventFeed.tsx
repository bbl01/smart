/**
 * Лента событий распознавания в реальном времени
 */
import { useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import { UserCheck, ShieldAlert, Camera, Bell } from 'lucide-react';
import type { LiveEvent } from '../../store';

interface Props {
  events: LiveEvent[];
}

function EventRow({ event }: { event: LiveEvent }) {
  const isKnown = event.type === 'face_detected' && event.is_known;
  const isUnknown = event.type === 'face_detected' && !event.is_known;
  const isAlert = event.type === 'alert';
  const isCamera = event.type === 'camera_status';

  const Icon = isKnown ? UserCheck : isUnknown ? ShieldAlert : isCamera ? Camera : Bell;

  const iconClass = clsx(
    'w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0',
    isKnown && 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
    isUnknown && 'bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
    isAlert && 'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    isCamera && 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
  );

  const time = new Date(event.timestamp).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return (
    <div className="flex items-start gap-2.5 py-2.5 border-b border-gray-50 dark:border-gray-700/50 last:border-0">
      <div className={iconClass}>
        <Icon className="w-3.5 h-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        {isKnown && (
          <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
            {event.person_name || `ID: ${event.person_id?.slice(0, 8)}`}
          </p>
        )}
        {isUnknown && (
          <p className="text-xs font-medium text-amber-700 dark:text-amber-400">
            Неизвестное лицо
          </p>
        )}
        {(isAlert || isCamera) && (
          <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
            {event.message || event.status}
          </p>
        )}
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] text-gray-400 font-mono">{time}</span>
          {event.camera_id && (
            <span className="text-[10px] text-gray-400">
              CAM-{event.camera_id.slice(-2)}
            </span>
          )}
          {event.confidence !== undefined && (
            <span className={clsx(
              'text-[10px] font-medium',
              event.confidence >= 0.9 ? 'text-emerald-500' :
              event.confidence >= 0.6 ? 'text-amber-500' : 'text-red-500'
            )}>
              {(event.confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function LiveEventFeed({ events }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [events.length]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-white">
          Live-события
        </h3>
        <span className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-full px-2 py-0.5">
          {events.length}
        </span>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-1"
        style={{ maxHeight: 360 }}
      >
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-400">
            <Camera className="w-8 h-8 mb-2 opacity-30" />
            <p className="text-xs">Ожидание событий...</p>
          </div>
        ) : (
          events.map(event => <EventRow key={event.id} event={event} />)
        )}
      </div>
    </div>
  );
}
