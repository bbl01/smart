/**
 * Карточка метрики для дашборда
 */
import { ReactNode } from 'react';
import { clsx } from 'clsx';

type Color = 'blue' | 'teal' | 'purple' | 'red' | 'amber' | 'green';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: ReactNode;
  icon: ReactNode;
  color?: Color;
  highlight?: boolean;
}

const colorMap: Record<Color, { bg: string; icon: string; value: string }> = {
  blue:   { bg: 'bg-blue-50 dark:bg-blue-900/20',   icon: 'text-blue-600 dark:text-blue-400',   value: 'text-blue-700 dark:text-blue-300' },
  teal:   { bg: 'bg-teal-50 dark:bg-teal-900/20',   icon: 'text-teal-600 dark:text-teal-400',   value: 'text-teal-700 dark:text-teal-300' },
  purple: { bg: 'bg-violet-50 dark:bg-violet-900/20', icon: 'text-violet-600 dark:text-violet-400', value: 'text-violet-700 dark:text-violet-300' },
  red:    { bg: 'bg-red-50 dark:bg-red-900/20',     icon: 'text-red-600 dark:text-red-400',     value: 'text-red-700 dark:text-red-300' },
  amber:  { bg: 'bg-amber-50 dark:bg-amber-900/20', icon: 'text-amber-600 dark:text-amber-400', value: 'text-amber-700 dark:text-amber-300' },
  green:  { bg: 'bg-emerald-50 dark:bg-emerald-900/20', icon: 'text-emerald-600 dark:text-emerald-400', value: 'text-emerald-700 dark:text-emerald-300' },
};

export default function MetricCard({
  label,
  value,
  subtext,
  icon,
  color = 'blue',
  highlight = false,
}: MetricCardProps) {
  const colors = colorMap[color];

  return (
    <div
      className={clsx(
        'rounded-xl border p-4 transition-shadow',
        'bg-white dark:bg-gray-800',
        highlight
          ? 'border-red-200 dark:border-red-800 shadow-sm shadow-red-100 dark:shadow-red-900/20'
          : 'border-gray-100 dark:border-gray-700',
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          {label}
        </p>
        <div className={clsx('w-7 h-7 rounded-lg flex items-center justify-center', colors.bg)}>
          <span className={colors.icon}>{icon}</span>
        </div>
      </div>

      <div className={clsx('text-2xl font-semibold tabular-nums', colors.value)}>
        {value}
      </div>

      {subtext && (
        <div className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
          {subtext}
        </div>
      )}
    </div>
  );
}
