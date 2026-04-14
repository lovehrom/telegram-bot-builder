import { AlertTriangle, Info, CheckCircle } from 'lucide-react';
import { Modal } from './Modal';
import { clsx } from 'clsx';

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info' | 'success';
}

const variantConfig = {
  danger: {
    icon: AlertTriangle,
    iconColor: 'text-red-500',
    iconBg: 'bg-red-50 dark:bg-red-900/20',
    confirmButton: 'bg-red-600 hover:bg-red-700 focus:ring-red-500 text-white',
  },
  warning: {
    icon: AlertTriangle,
    iconColor: 'text-yellow-500',
    iconBg: 'bg-yellow-50 dark:bg-yellow-900/20',
    confirmButton: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500 text-white',
  },
  info: {
    icon: Info,
    iconColor: 'text-blue-500',
    iconBg: 'bg-blue-50 dark:bg-blue-900/20',
    confirmButton: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 text-white',
  },
  success: {
    icon: CheckCircle,
    iconColor: 'text-green-500',
    iconBg: 'bg-green-50 dark:bg-green-900/20',
    confirmButton: 'bg-green-600 hover:bg-green-700 focus:ring-green-500 text-white',
  },
};

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Подтвердить',
  cancelLabel = 'Отмена',
  variant = 'info',
}: ConfirmDialogProps) {
  const config = variantConfig[variant];
  const Icon = config.icon;

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      showCloseButton={true}
    >
      <div className="flex flex-col items-center text-center">
        {/* Icon */}
        <div className={clsx('mb-4 rounded-full p-3', config.iconBg)}>
          <Icon className={clsx('h-8 w-8', config.iconColor)} aria-hidden="true" />
        </div>

        {/* Message */}
        <p className="mb-6 text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
          {message}
        </p>

        {/* Buttons */}
        <div className="flex w-full gap-3">
          <button
            type="button"
            onClick={onClose}
            className={clsx(
              'flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 dark:focus:ring-offset-gray-800'
            )}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            className={clsx(
              'flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-800',
              config.confirmButton
            )}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </Modal>
  );
}
