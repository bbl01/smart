/**
 * График посещаемости за неделю / месяц / семестр
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { analyticsApi } from '../../utils/api';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

const PERIODS = [
  { label: '7 дней', weeks: 1 },
  { label: '30 дней', weeks: 4 },
  { label: 'Семестр', weeks: 16 },
];

// Кастомный тултип
function CustomTooltip({ active, payload, label }: Record<string, unknown>) {
  if (!active || !payload || !(payload as unknown[]).length) return null;
  const data = payload as Array<{ value: number }>;
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg px-3 py-2 shadow-lg text-xs">
      <p className="text-gray-500 dark:text-gray-400 mb-1">
        {format(parseISO(label as string), 'd MMMM', { locale: ru })}
      </p>
      <p className="font-semibold text-blue-600 dark:text-blue-400">
        {data[0]?.value ?? 0} чел.
      </p>
    </div>
  );
}

export default function WeeklyChart() {
  const [activePeriod, setActivePeriod] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'weekly', PERIODS[activePeriod].weeks],
    queryFn: () => analyticsApi.weekly(PERIODS[activePeriod].weeks).then(r => r.data),
  });

  const chartData = data
    ? data.labels.map((label: string, i: number) => ({
        date: label,
        value: data.values[i],
        label: format(parseISO(label), 'dd.MM'),
      }))
    : [];

  const avg = chartData.length
    ? Math.round(chartData.reduce((s: number, d: { value: number }) => s + d.value, 0) / chartData.length)
    : 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-800 dark:text-white">
            Посещаемость по дням
          </h3>
          {avg > 0 && (
            <p className="text-xs text-gray-400 mt-0.5">
              Среднее: {avg} чел/день
            </p>
          )}
        </div>
        <div className="flex gap-1">
          {PERIODS.map((p, i) => (
            <button
              key={p.label}
              onClick={() => setActivePeriod(i)}
              className={`text-xs px-3 py-1 rounded-md transition-colors
                ${activePeriod === i
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="h-48 flex items-center justify-center">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={190}>
          <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
            <defs>
              <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: '#9CA3AF' }}
              axisLine={false}
              tickLine={false}
              interval={activePeriod === 0 ? 0 : 'preserveStartEnd'}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#9CA3AF' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            {avg > 0 && (
              <ReferenceLine
                y={avg}
                stroke="#93C5FD"
                strokeDasharray="4 4"
                label={{ value: `Ср: ${avg}`, fill: '#93C5FD', fontSize: 10 }}
              />
            )}
            <Area
              type="monotone"
              dataKey="value"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#blueGrad)"
              dot={{ r: 3, fill: '#3B82F6', strokeWidth: 0 }}
              activeDot={{ r: 5, fill: '#2563EB' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
