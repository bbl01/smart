/**
 * Тепловая карта посещаемости по дням/парам
 */
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../../utils/api';
import { clsx } from 'clsx';

const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'];
const LESSONS = [1, 2, 3, 4, 5, 6, 7, 8];

function getColor(value: number | undefined): string {
  if (!value) return 'bg-gray-100 dark:bg-gray-700';
  if (value < 40) return 'bg-blue-100 dark:bg-blue-900/30';
  if (value < 55) return 'bg-blue-200 dark:bg-blue-800/40';
  if (value < 65) return 'bg-blue-300 dark:bg-blue-700/50';
  if (value < 75) return 'bg-blue-400 dark:bg-blue-600/70';
  if (value < 85) return 'bg-blue-500 dark:bg-blue-500/80';
  return 'bg-blue-600 dark:bg-blue-400';
}

export default function HeatmapChart() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'heatmap'],
    queryFn: () => analyticsApi.heatmap().then(r => r.data),
    refetchInterval: 300_000,
  });

  const heatData: Record<string, number> = data?.data ?? {};

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-5">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-white">
          Активность по расписанию
        </h3>
        <p className="text-xs text-gray-400 mt-0.5">
          {data?.month && `${data.month}/${data.year}`}
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-1.5">
          {DAYS.map(d => (
            <div key={d} className="flex gap-1">
              {LESSONS.map(l => (
                <div key={l} className="w-6 h-6 rounded bg-gray-100 dark:bg-gray-700 animate-pulse" />
              ))}
            </div>
          ))}
        </div>
      ) : (
        <>
          {/* Column headers (lesson numbers) */}
          <div className="flex gap-1 mb-1 ml-7">
            {LESSONS.map(l => (
              <div key={l} className="w-6 text-center text-[9px] text-gray-400 font-mono">
                {l}
              </div>
            ))}
          </div>

          {/* Rows */}
          <div className="space-y-1">
            {DAYS.map((day, di) => (
              <div key={day} className="flex items-center gap-1">
                <span className="w-6 text-[10px] text-gray-400 text-right font-medium">
                  {day}
                </span>
                {LESSONS.map(lesson => {
                  const key = `${di}_${lesson}`;
                  const value = heatData[key];
                  return (
                    <div
                      key={lesson}
                      className={clsx(
                        'w-6 h-6 rounded cursor-default transition-opacity hover:opacity-75 relative group',
                        getColor(value)
                      )}
                      title={value ? `${day}, пара ${lesson}: ${value}%` : 'Нет данных'}
                    >
                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1
                        hidden group-hover:block z-10 pointer-events-none">
                        <div className="bg-gray-800 text-white text-[9px] px-1.5 py-1 rounded whitespace-nowrap">
                          {value ? `${value}%` : '—'}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-1.5 mt-3">
            <span className="text-[10px] text-gray-400">Низкая</span>
            <div className="flex gap-0.5">
              {['bg-gray-100', 'bg-blue-200', 'bg-blue-300', 'bg-blue-400', 'bg-blue-500', 'bg-blue-600'].map((c, i) => (
                <div key={i} className={clsx('w-4 h-3 rounded-sm', c)} />
              ))}
            </div>
            <span className="text-[10px] text-gray-400">Высокая</span>
          </div>
        </>
      )}
    </div>
  );
}
