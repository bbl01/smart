/**
 * Главная страница дашборда
 */
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../utils/api';
import { useDashboardStore } from '../store';
import { useWebSocket } from '../hooks/useWebSocket';
import MetricCard from '../components/dashboard/MetricCard';
import WeeklyChart from '../components/dashboard/WeeklyChart';
import LiveEventFeed from '../components/dashboard/LiveEventFeed';
import CameraGrid from '../components/cameras/CameraGrid';
import GroupsTable from '../components/analytics/GroupsTable';
import HeatmapChart from '../components/analytics/HeatmapChart';
import AlertBadge from '../components/shared/AlertBadge';
import {
  Users, UserCheck, ShieldAlert, Cpu,
  TrendingUp, TrendingDown, Minus
} from 'lucide-react';

export default function DashboardPage() {
  const { summary, setSummary, wsConnected, liveEvents } = useDashboardStore();
  useWebSocket();

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => analyticsApi.summary().then(r => r.data),
    refetchInterval: 30_000,
  });

  useEffect(() => {
    if (data) setSummary(data);
  }, [data, setSummary]);

  if (isLoading && !summary) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-500">Загрузка данных...</p>
        </div>
      </div>
    );
  }

  const attendanceRate = summary?.attendance_rate ?? 0;
  const prevRate = 66.2; // В реальном приложении — из API
  const delta = attendanceRate - prevRate;

  const DeltaIcon = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus;
  const deltaColor = delta > 0 ? 'text-emerald-600' : delta < 0 ? 'text-red-500' : 'text-gray-400';

  return (
    <div className="p-6 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            Обзор посещаемости
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {new Date().toLocaleDateString('ru-RU', {
              weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
            })}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full
            ${wsConnected
              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
              : 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            {wsConnected ? 'Система активна' : 'Нет соединения'}
          </div>

          {(summary?.alerts_today ?? 0) > 0 && (
            <AlertBadge count={summary?.alerts_today ?? 0} />
          )}
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Присутствует сейчас"
          value={summary?.present_now ?? 0}
          subtext={`из ${summary?.total_registered ?? 0} зарегистрированных`}
          icon={<UserCheck className="w-4 h-4" />}
          color="teal"
        />
        <MetricCard
          label="Посещаемость сегодня"
          value={`${attendanceRate}%`}
          subtext={
            <span className={`flex items-center gap-1 ${deltaColor}`}>
              <DeltaIcon className="w-3 h-3" />
              {Math.abs(delta).toFixed(1)}% vs вчера
            </span>
          }
          icon={<TrendingUp className="w-4 h-4" />}
          color="blue"
        />
        <MetricCard
          label="Распознавание"
          value="99.2%"
          subtext="Точность биометрии"
          icon={<Cpu className="w-4 h-4" />}
          color="purple"
        />
        <MetricCard
          label="Нарушения"
          value={summary?.alerts_today ?? 0}
          subtext="Неопознанные входы"
          icon={<ShieldAlert className="w-4 h-4" />}
          color="red"
          highlight={(summary?.alerts_today ?? 0) > 0}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <WeeklyChart />
        </div>
        <div>
          <HeatmapChart />
        </div>
      </div>

      {/* Camera Grid + Live Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <CameraGrid />
        </div>
        <div>
          <LiveEventFeed events={liveEvents.slice(0, 20)} />
        </div>
      </div>

      {/* Groups Table */}
      <GroupsTable />

    </div>
  );
}
