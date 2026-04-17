/**
 * Таблица посещаемости по группам
 */
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../../utils/api';
import { clsx } from 'clsx';
import { TrendingDown, TrendingUp, AlertTriangle } from 'lucide-react';

interface GroupStat {
  id: string;
  name: string;
  present: number;
  total: number;
  rate: number;
  status: 'good' | 'warning' | 'critical';
}

function RateBar({ rate }: { rate: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={clsx(
            'h-full rounded-full transition-all',
            rate >= 75 ? 'bg-emerald-500' :
            rate >= 50 ? 'bg-amber-500' : 'bg-red-500'
          )}
          style={{ width: `${rate}%` }}
        />
      </div>
      <span className={clsx(
        'text-xs font-mono font-medium w-10 text-right',
        rate >= 75 ? 'text-emerald-600 dark:text-emerald-400' :
        rate >= 50 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'
      )}>
        {rate}%
      </span>
    </div>
  );
}

function StatusBadge({ status }: { status: GroupStat['status'] }) {
  return (
    <span className={clsx(
      'inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full',
      status === 'good' && 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
      status === 'warning' && 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      status === 'critical' && 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    )}>
      {status === 'good' && <TrendingUp className="w-2.5 h-2.5" />}
      {status === 'warning' && <TrendingDown className="w-2.5 h-2.5" />}
      {status === 'critical' && <AlertTriangle className="w-2.5 h-2.5" />}
      {status === 'good' ? 'Норма' : status === 'warning' ? 'Внимание' : 'Критично'}
    </span>
  );
}

export default function GroupsTable() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'groups'],
    queryFn: () => analyticsApi.groups().then(r => r.data),
    refetchInterval: 60_000,
  });

  const groups: GroupStat[] = data?.groups ?? [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-white">
          Посещаемость по группам
        </h3>
        {data?.period && (
          <span className="text-xs text-gray-400">
            {data.period.from} — {data.period.to}
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-50 dark:border-gray-700">
              <th className="text-left px-5 py-2.5 text-xs font-medium text-gray-400 uppercase tracking-wide">Группа</th>
              <th className="text-left px-3 py-2.5 text-xs font-medium text-gray-400 uppercase tracking-wide">Присутствуют</th>
              <th className="text-left px-3 py-2.5 text-xs font-medium text-gray-400 uppercase tracking-wide w-48">Посещаемость</th>
              <th className="text-left px-3 py-2.5 text-xs font-medium text-gray-400 uppercase tracking-wide">Статус</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-gray-50 dark:border-gray-700">
                  {[...Array(4)].map((_, j) => (
                    <td key={j} className="px-5 py-3">
                      <div className="h-3 bg-gray-100 dark:bg-gray-700 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : groups.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center py-8 text-gray-400 text-sm">
                  Нет данных
                </td>
              </tr>
            ) : (
              groups.map(group => (
                <tr
                  key={group.id}
                  className="border-b border-gray-50 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                >
                  <td className="px-5 py-3">
                    <span className="font-medium text-gray-800 dark:text-gray-200">
                      {group.name}
                    </span>
                  </td>
                  <td className="px-3 py-3 font-mono text-xs text-gray-600 dark:text-gray-400">
                    {group.present} / {group.total}
                  </td>
                  <td className="px-3 py-3 w-48">
                    <RateBar rate={group.rate} />
                  </td>
                  <td className="px-3 py-3">
                    <StatusBadge status={group.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
