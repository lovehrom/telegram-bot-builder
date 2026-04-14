import { create } from 'zustand';
import { Toast, type ToastProps } from './Toast';

interface ToastStore {
  toasts: Omit<ToastProps, 'onClose'>[];
  addToast: (toast: Omit<ToastProps, 'id' | 'onClose'> & { id?: string }) => string;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

export const useToastStore = create<ToastStore>((set, get) => ({
  toasts: [],
  addToast: (toast) => {
    const id = toast.id || `toast-${Date.now()}-${Math.random()}`;
    const newToast = { ...toast, id };
    set((state) => ({
      toasts: [...state.toasts, newToast],
    }));

    // Auto-remove after duration
    const duration = toast.duration || 5000;
    setTimeout(() => {
      get().removeToast(id);
    }, duration);

    return id;
  },
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },
  clearAll: () => {
    set({ toasts: [] });
  },
}));

// Convenience functions
export const toast = {
  success: (message: string, duration?: number) => {
    useToastStore.getState().addToast({ message, type: 'success', duration });
  },
  error: (message: string, duration?: number) => {
    useToastStore.getState().addToast({ message, type: 'error', duration });
  },
  warning: (message: string, duration?: number) => {
    useToastStore.getState().addToast({ message, type: 'warning', duration });
  },
  info: (message: string, duration?: number) => {
    useToastStore.getState().addToast({ message, type: 'info', duration });
  },
};

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-4 right-4 z-[100] flex max-w-md flex-col gap-3"
      aria-label="Уведомления"
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          {...toast}
          onClose={toast.id ? removeToast : undefined}
        />
      ))}
    </div>
  );
}
