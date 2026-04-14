import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { clsx } from 'clsx';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastProps {
  id: string;
  message: string;
  type?: ToastType;
  duration?: number;
  onClose?: (id: string) => void;
}

const toastConfig = {
  success: {
    icon: CheckCircle,
    iconColor: 'text-green-500',
    iconBg: 'bg-green-50 dark:bg-green-900/20',
    borderColor: 'border-green-500 dark:border-green-600',
    title: 'Успех',
  },
  error: {
    icon: XCircle,
    iconColor: 'text-red-500',
    iconBg: 'bg-red-50 dark:bg-red-900/20',
    borderColor: 'border-red-500 dark:border-red-600',
    title: 'Ошибка',
  },
  warning: {
    icon: AlertTriangle,
    iconColor: 'text-yellow-500',
    iconBg: 'bg-yellow-50 dark:bg-yellow-900/20',
    borderColor: 'border-yellow-500 dark:border-yellow-600',
    title: 'Предупреждение',
  },
  info: {
    icon: Info,
    iconColor: 'text-blue-500',
    iconBg: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-500 dark:border-blue-600',
    title: 'Информация',
  },
};

export function Toast({ id, message, type = 'info', onClose }: ToastProps) {
  const config = toastConfig[type];
  const Icon = config.icon;

  return (
    <div
      role="alert"
      aria-live="polite"
      className={clsx(
        'flex items-start gap-3 rounded-lg border-l-4 bg-white px-4 py-3 shadow-lg dark:bg-gray-800',
        config.borderColor
      )}
    >
      {/* Icon */}
      <div className={clsx('rounded-full p-1', config.iconBg)}>
        <Icon className={clsx('h-4 w-4 flex-shrink-0', config.iconColor)} aria-hidden="true" />
      </div>

      {/* Message */}
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900 dark:text-white">{config.title}</p>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{message}</p>
      </div>

      {/* Close Button */}
      {onClose && (
        <button
          onClick={() => onClose(id)}
          className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
          aria-label="Закрыть уведомление"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
