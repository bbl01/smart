import { Bell } from 'lucide-react';
interface Props { count: number }
export default function AlertBadge({ count }: Props) {
  return (
    <div className="flex items-center gap-1 bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400 text-xs font-medium px-2.5 py-1 rounded-full">
      <Bell className="w-3 h-3" />
      {count} {count === 1 ? 'уведомление' : 'уведомлений'}
    </div>
  );
}
