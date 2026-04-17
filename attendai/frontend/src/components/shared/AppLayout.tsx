/**
 * Основной лейаут с сайдбаром и шапкой
 */
import { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { useAuthStore } from '../../store';
import {
  LayoutDashboard, Users, ClipboardList, Video,
  BarChart2, FileText, Settings, LogOut, Bell, Menu
} from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Обзор', path: '/', icon: LayoutDashboard },
  { label: 'Посещаемость', path: '/attendance', icon: ClipboardList },
  { label: 'Персоны', path: '/persons', icon: Users },
  { label: 'Камеры', path: '/cameras', icon: Video },
  { label: 'Аналитика', path: '/analytics', icon: BarChart2 },
  { label: 'Отчёты', path: '/reports', icon: FileText },
];

const BOTTOM_ITEMS = [
  { label: 'Настройки', path: '/settings', icon: Settings },
];

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const initials = user?.full_name
    ?.split(' ')
    .slice(0, 2)
    .map(n => n[0])
    .join('')
    .toUpperCase() ?? 'АД';

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">

      {/* Sidebar */}
      <aside className="w-52 flex-shrink-0 bg-white dark:bg-gray-800 border-r border-gray-100 dark:border-gray-700 flex flex-col">

        {/* Logo */}
        <div className="h-14 flex items-center px-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
              <svg viewBox="0 0 14 14" fill="none" className="w-3.5 h-3.5">
                <rect x="1" y="1" width="5" height="5" rx="1.5" fill="white" opacity="0.9"/>
                <rect x="8" y="1" width="5" height="5" rx="1.5" fill="white" opacity="0.6"/>
                <rect x="1" y="8" width="5" height="5" rx="1.5" fill="white" opacity="0.6"/>
                <rect x="8" y="8" width="5" height="5" rx="1.5" fill="white" opacity="0.9"/>
              </svg>
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-900 dark:text-white leading-none">
                AttendAI
              </div>
              <div className="text-[9px] text-gray-400 uppercase tracking-wider mt-0.5">
                Smart Attendance
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-3 px-2 overflow-y-auto">
          <div className="space-y-0.5">
            {NAV_ITEMS.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) => clsx(
                  'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                )}
              >
                <item.icon className="w-4 h-4 flex-shrink-0" />
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Bottom nav */}
        <div className="py-3 px-2 border-t border-gray-100 dark:border-gray-700 space-y-0.5">
          {BOTTOM_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => clsx(
                'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              )}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </NavLink>
          ))}

          {/* User */}
          <div className="flex items-center gap-2 px-3 py-2 mt-1">
            <div className="w-7 h-7 rounded-full bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-400
              flex items-center justify-center text-[11px] font-semibold flex-shrink-0">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                {user?.full_name}
              </p>
              <p className="text-[10px] text-gray-400 capitalize">{user?.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="text-gray-400 hover:text-red-500 transition-colors"
              title="Выйти"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700
          flex items-center justify-between px-6 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 lg:hidden">
              <Menu className="w-5 h-5" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
