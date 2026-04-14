import { useState, useRef, useEffect } from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';
import { Modal } from './Modal';
import { clsx } from 'clsx';

export interface PromptDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (value: string) => void;
  title: string;
  placeholder?: string;
  defaultValue?: string;
  validation?: (value: string) => string | null; // error message or null
  required?: boolean;
  label?: string;
  maxLength?: number;
}

export function PromptDialog({
  isOpen,
  onClose,
  onSubmit,
  title,
  placeholder = '?????????????? ????????????????...',
  defaultValue = '',
  validation,
  required = false,
  label,
  maxLength = 100,
}: PromptDialogProps) {
  const [value, setValue] = useState(defaultValue);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset state when dialog opens
  useEffect(() => {
    if (isOpen) {
      setValue(defaultValue);
      setError(null);
      // Focus input after animation
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [isOpen, defaultValue]);

  const handleSubmit = () => {
    // Check required
    if (required && !value.trim()) {
      setError('?????? ???????????????????????? ????????');
      return;
    }

    // Run custom validation
    if (validation) {
      const validationError = validation(value);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    onSubmit(value.trim());
    onClose(); // ???? FIX: Close dialog after successful submit
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !error) {
      handleSubmit();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      showCloseButton={true}
    >
      <div className="flex flex-col">
        {/* Input Field */}
        <div className="mb-4">
          {label && (
            <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
              {label}
              {required && <span className="ml-1 text-red-500">*</span>}
            </label>
          )}
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={value}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              maxLength={maxLength}
              className={clsx(
                'w-full rounded-lg border px-4 py-3 pr-10 text-sm bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white',
                error
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 dark:border-gray-600'
              )}
              aria-invalid={!!error}
              aria-describedby={error ? 'prompt-error' : undefined}
            />
            {/* Character count */}
            {maxLength > 0 && (
              <span className="absolute bottom-3 right-3 text-xs text-gray-400">
                {value.length}/{maxLength}
              </span>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div
              id="prompt-error"
              className="mt-2 flex items-center gap-2 text-sm text-red-600 dark:text-red-400"
              role="alert"
              aria-live="assertive"
            >
              <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className={clsx(
              'flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 dark:focus:ring-offset-gray-800'
            )}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={required && !value.trim()}
            className={clsx(
              'flex flex-1 items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed dark:disabled:bg-gray-600'
            )}
          >
            <CheckCircle className="h-4 w-4" aria-hidden="true" />
            OK
          </button>
        </div>
      </div>
    </Modal>
  );
}
