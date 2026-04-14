import { useState, useEffect, useCallback, useMemo, memo } from 'react';
import { Edge } from 'reactflow';
import { useFlowStore } from '@/hooks/useFlowStore';
import { Trash2, X } from 'lucide-react';

interface EdgePropertiesProps {
  edge: Edge | null;
  onClose: () => void;
}

const conditionLabels: Record<string, string> = {
  correct: 'Правильный ответ ✅',
  wrong: 'Неправильный ответ ❌',
  paid: 'Оплачено 💳',
  unpaid: 'Не оплачено 💸',
  true: 'Условие верно ✓',
  false: 'Условие ложно ✗',
};

function EdgeProperties({ edge, onClose }: EdgePropertiesProps) {
  const { updateEdge, removeEdge } = useFlowStore();
  const [localCondition, setLocalCondition] = useState('');

  useEffect(() => {
    if (edge) {
      setLocalCondition(edge.data?.condition || '');
    }
  }, [edge]);

  if (!edge) {
    return (
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">🔗 Соединение</h2>
        </div>
        <p className="text-sm text-gray-500">Выберите соединение для редактирования</p>
      </div>
    );
  }

  const handleConditionChange = useCallback((value: string) => {
    setLocalCondition(value);
    if (edge) {
      updateEdge(edge.id, { condition: value });
    }
  }, [edge, updateEdge]);

  const handleDelete = useCallback(() => {
    if (edge) {
      removeEdge(edge.id);
      onClose();
    }
  }, [edge, removeEdge, onClose]);

  const getAvailableConditions = useCallback(() => {
    // Based on source node type, return available conditions
    return [
      { value: '', label: 'Без условия (всегда)' },
      { value: 'correct', label: 'Правильный ответ ✅' },
      { value: 'wrong', label: 'Неправильный ответ ❌' },
      { value: 'paid', label: 'Оплачено 💳' },
      { value: 'unpaid', label: 'Не оплачено 💸' },
      { value: 'true', label: 'Условие верно ✓' },
      { value: 'false', label: 'Условие ложно ✗' },
      { value: 'menu_start', label: 'Кнопка "Начать"' },
    ];
  }, []);

  const currentLabel = useMemo(() =>
    conditionLabels[localCondition] || localCondition || 'Без условия',
    [localCondition]
  );

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b bg-gray-50 dark:bg-gray-900 shrink-0">
        <div className="flex items-center justify-between pb-3">
          <div className="flex-1">
            <h2 className="text-lg font-semibold">🔗 Соединение</h2>
            <p className="text-xs text-gray-500">Условие перехода</p>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
            title="Закрыть"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {/* Current condition display */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded">
            <h4 className="font-semibold text-sm text-blue-800 mb-1">Текущее условие</h4>
            <p className="text-sm text-blue-700">{currentLabel}</p>
          </div>

          {/* Condition selector */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Условие перехода
            </label>
            <select
              value={localCondition}
              onChange={(e) => handleConditionChange(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {getAvailableConditions().map((cond) => (
                <option key={cond.value} value={cond.value}>
                  {cond.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Когда это условие выполняется, переход произойдёт по этому соединению
            </p>
          </div>

          {/* Custom condition input */}
          {localCondition && !conditionLabels[localCondition] && (
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Пользовательское условие
              </label>
              <input
                type="text"
                value={localCondition}
                onChange={(e) => handleConditionChange(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="menu_button_name"
              />
              <p className="text-xs text-gray-500 mt-1">
                Для кнопок меню: menu_название_кнопки
              </p>
            </div>
          )}

          {/* Help section */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-900">
            <div className="font-bold mb-2">💡 Для разных блоков разные варианты:</div>
            <ul className="space-y-1 ml-2">
              <li>📝 <strong>Викторина</strong> — правильный/неправильный ответ</li>
              <li>✓ <strong>Да/Нет</strong> — истина/ложь</li>
              <li>💳 <strong>Оплата</strong> — оплачено/нет</li>
              <li>📋 <strong>Меню</strong> — название кнопки</li>
              <li>📚 <strong>Курс</strong> — номер курса (например: course_1)</li>
            </ul>
          </div>

          {/* Delete button */}
          <button
            onClick={handleDelete}
            className="flex items-center gap-2 w-full px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            Удалить соединение
          </button>
        </div>
      </div>
    </div>
  );
}

// Custom comparison function for EdgeProperties
const arePropsEqual = (prevProps: EdgePropertiesProps, nextProps: EdgePropertiesProps) => {
  return prevProps.edge === nextProps.edge && prevProps.onClose === nextProps.onClose;
};

export const EdgePropertiesMemo = memo(EdgeProperties, arePropsEqual);
EdgePropertiesMemo.displayName = 'EdgeProperties';

// Export as both for backward compatibility
export { EdgeProperties };
export default EdgePropertiesMemo;
