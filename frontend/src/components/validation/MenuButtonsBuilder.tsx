import { useState } from 'react';
import { Plus, Trash2, GripVertical } from 'lucide-react';
import { clsx } from 'clsx';

export interface MenuButton {
  label: string;
  callback_data: string;
}

interface MenuButtonsBuilderProps {
  buttons: MenuButton[];
  onChange: (buttons: MenuButton[]) => void;
  maxButtons?: number;
}

export function MenuButtonsBuilder({
  buttons,
  onChange,
  maxButtons = 10,
}: MenuButtonsBuilderProps) {
  const [errors, setErrors] = useState<Record<number, string>>({});

  const validateButtons = (newButtons: MenuButton[]): Record<number, string> => {
    const newErrors: Record<number, string> = {};

    // Check for duplicate callback_data
    const callbackDataMap = new Map<string, number>();
    newButtons.forEach((btn, index) => {
      if (btn.callback_data) {
        const existingIndex = callbackDataMap.get(btn.callback_data);
        if (existingIndex !== undefined) {
          newErrors[index] = 'Callback data должен быть уникальным';
          newErrors[existingIndex] = 'Callback data должен быть уникальным';
        }
        callbackDataMap.set(btn.callback_data, index);
      }
    });

    return newErrors;
  };

  const handleAddButton = () => {
    if (buttons.length >= maxButtons) {
      return;
    }

    const newButtons = [
      ...buttons,
      { label: `Кнопка ${buttons.length + 1}`, callback_data: `button_${buttons.length + 1}` },
    ];
    const newErrors = validateButtons(newButtons);
    setErrors(newErrors);
    onChange(newButtons);
  };

  const handleRemoveButton = (index: number) => {
    const newButtons = buttons.filter((_, i) => i !== index);
    const newErrors = validateButtons(newButtons);
    setErrors(newErrors);
    onChange(newButtons);
  };

  const handleLabelChange = (index: number, value: string) => {
    const newButtons = [...buttons];
    newButtons[index].label = value;

    // Validate
    const newErrors = { ...errors };
    if (!value.trim()) {
      newErrors[index] = 'Label обязателен';
    } else if (value.length > 64) {
      newErrors[index] = 'Label не должен превышать 64 символа';
    } else {
      delete newErrors[index];
    }

    setErrors(newErrors);
    onChange(newButtons);
  };

  const handleCallbackDataChange = (index: number, value: string) => {
    const newButtons = [...buttons];
    newButtons[index].callback_data = value;

    // Validate
    const newErrors = validateButtons(newButtons);
    setErrors(newErrors);
    onChange(newButtons);
  };

  const getJsonPreview = () => {
    return JSON.stringify(buttons, null, 2);
  };

  return (
    <div className="space-y-3">
      {/* Buttons List */}
      <div className="space-y-2">
        {buttons.map((button, index) => (
          <div
            key={index}
            className={clsx(
              'relative rounded-lg border p-3 transition-colors',
              errors[index] ? 'border-red-500 bg-red-50 dark:bg-red-900/10' : 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800'
            )}
          >
            {/* Drag Handle */}
            <div className="absolute left-2 top-3 cursor-grab text-gray-400 hover:text-gray-600">
              <GripVertical className="h-4 w-4" />
            </div>

            {/* Button Number */}
            <div className="mb-2 ml-6 text-xs font-medium text-gray-500 dark:text-gray-400">
              Кнопка {index + 1}
            </div>

            {/* Label Input */}
            <div className="mb-2 ml-6">
              <label className="mb-1 block text-xs font-medium text-gray-700 dark:text-gray-300">
                Label (текст на кнопке)
                <span className="ml-1 text-red-500">*</span>
              </label>
              <input
                type="text"
                value={button.label}
                onChange={(e) => handleLabelChange(index, e.target.value)}
                placeholder="Текст кнопки"
                maxLength={64}
                className={clsx(
                  'w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2',
                  errors[index]
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500 dark:border-gray-600'
                )}
                aria-invalid={!!errors[index]}
              />
            </div>

            {/* Callback Data Input */}
            <div className="mb-2 ml-6">
              <label className="mb-1 block text-xs font-medium text-gray-700 dark:text-gray-300">
                Callback Data (уникальный ID)
                <span className="ml-1 text-red-500">*</span>
              </label>
              <input
                type="text"
                value={button.callback_data}
                onChange={(e) => handleCallbackDataChange(index, e.target.value)}
                placeholder="unique_button_id"
                className={clsx(
                  'w-full rounded-md border px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2',
                  errors[index]
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500 dark:border-gray-600'
                )}
                aria-invalid={!!errors[index]}
              />
            </div>

            {/* Error Message */}
            {errors[index] && (
              <p className="ml-6 mt-2 text-xs text-red-600 dark:text-red-400" role="alert">
                {errors[index]}
              </p>
            )}

            {/* Remove Button */}
            <button
              onClick={() => handleRemoveButton(index)}
              className="absolute right-2 top-2 rounded p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
              aria-label="Удалить кнопку"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Add Button */}
      {buttons.length < maxButtons && (
        <button
          onClick={handleAddButton}
          className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-300 px-4 py-3 text-sm font-medium text-gray-600 transition-colors hover:border-blue-500 hover:bg-blue-50 hover:text-blue-600 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-blue-900/20 dark:hover:text-blue-400"
        >
          <Plus className="h-4 w-4" />
          Добавить кнопку ({buttons.length}/{maxButtons})
        </button>
      )}

      {/* JSON Preview */}
      <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800">
        <div className="mb-2 flex items-center justify-between">
          <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
            JSON (для проверки)
          </label>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {buttons.length} кнопок
          </span>
        </div>
        <pre className="overflow-x-auto text-xs font-mono text-gray-800 dark:text-gray-200">
          {getJsonPreview()}
        </pre>
      </div>

      {/* Connection Help */}
      <div className="rounded-md border border-blue-200 bg-blue-50 p-3 dark:border-blue-900 dark:bg-blue-900/20">
        <p className="mb-2 text-xs font-semibold text-blue-900 dark:text-blue-300">
          ℹ️ Как подключить:
        </p>
        <p className="mb-1 text-xs text-blue-800 dark:text-blue-400">
          Создайте отдельное соединение для каждой кнопки.
        </p>
        <p className="text-xs text-blue-800 dark:text-blue-400">
          Условие подключения: <code className="rounded bg-blue-100 px-1 py-0.5 dark:bg-blue-900">menu_{"{callback_data}"}</code>
        </p>
        <p className="mt-1 text-xs text-blue-700 dark:text-blue-500">
          Например: для callback_data=<code className="rounded bg-blue-100 px-1 py-0.5 dark:bg-blue-900">"start"</code> условие=<code className="rounded bg-blue-100 px-1 py-0.5 dark:bg-blue-900">"menu_start"</code>
        </p>
      </div>
    </div>
  );
}
