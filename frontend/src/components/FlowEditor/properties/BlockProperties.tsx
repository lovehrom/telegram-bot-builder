import { useState, useEffect, useCallback, useMemo, lazy, Suspense } from 'react';
import { Node } from 'reactflow';
import { useFlowStore } from '@/hooks/useFlowStore';
import { Trash2 } from 'lucide-react';
import { MenuButtonsBuilder } from '@/components/validation/MenuButtonsBuilder';
import { TelegramMessagePreview } from '@/components/preview/TelegramMessagePreview';
import { clsx } from 'clsx';

// Lazy load MediaSelector
const MediaSelector = lazy(() => import('@/components/MediaSelector/MediaSelector'));

interface BlockPropertiesProps {
  node: Node;
  onDelete: () => void;
}

function BlockProperties({ node, onDelete }: BlockPropertiesProps) {
  const { updateNode } = useFlowStore();
  const [localConfig, setLocalConfig] = useState<Record<string, any>>(node?.data?.config || {});
  const [activeTab, setActiveTab] = useState<'edit' | 'preview'>('edit');

  // Reset state when node changes (only when node.id changes)
  useEffect(() => {
    setLocalConfig(node?.data?.config || {});
    setActiveTab('edit');
  }, [node?.id]);

  const handleConfigChange = useCallback((key: string, value: any) => {
    setLocalConfig(prev => {
      const newConfig = { ...prev, [key]: value };
      if (node?.id) {
        updateNode(node.id, { config: newConfig });
      }
      return newConfig;
    });
  }, [updateNode, node?.id]);

  const getBlockTitle = useCallback((blockType: string) => {
    const titles: Record<string, string> = {
      start: '🚀 Стартовый блок',
      text: '📝 Текстовый блок',
      video: '🎬 Видео блок',
      image: '🖼️ Изображение',
      delay: '⏱️ Задержка',
      confirmation: '✅ Подтверждение',
      course_menu: '📚 Меню курсов',
      quiz: '❓ Блок викторины',
      decision: '🔀 Блок условия',
      menu: '📋 Блок меню',
      payment_gate: '💳 Проверка оплаты',
      create_payment: '💳 Создать платёж',
      action: '⚡ Действие с переменными',
      input: '📝 Ввод данных',
      random: '🎲 Случайный выбор',
      end: '🏁 Конец flow',
    };
    return titles[blockType] || `⚙️ ${blockType}`;
  }, []);

  const getBlockDescription = useCallback((blockType: string) => {
    const descriptions: Record<string, string> = {
      start: 'Точка входа в сценарий. Всегда первый блок.',
      text: 'Отправляет текстовое сообщение пользователю.',
      video: 'Отправляет видео файл пользователю.',
      image: 'Отправляет изображение пользователю.',
      delay: 'Задержка перед переходом к следующему блоку.',
      confirmation: 'Показывает кнопки подтверждения (Да/Нет).',
      course_menu: 'Меню выбора курсов с проверкой оплаты.',
      quiz: 'Задаёт вопрос с вариантами ответов для проверки знаний.',
      decision: 'Разветвляет flow в зависимости от условия.',
      menu: 'Отображает кнопки для навигации по flow.',
      payment_gate: 'Проверяет, оплатил ли пользователь доступ к контенту.',
      create_payment: 'Создаёт платёжный инвойс пользователю.',
      action: 'Установка, увеличение или уменьшение переменных.',
      input: 'Запрашивает ввод данных от пользователя с валидацией.',
      random: 'Случайный выбор следующего блока (равные или взвешенные шансы).',
      end: 'Завершает диалог и отправляет финальное сообщение.',
    };
    return descriptions[blockType] || '';
  }, []);

  const getBlockColor = useCallback((blockType: string) => {
    const colors: Record<string, string> = {
      start: 'green',
      text: 'blue',
      video: 'purple',
      image: 'pink',
      delay: 'gray',
      confirmation: 'teal',
      course_menu: 'amber',
      quiz: 'yellow',
      decision: 'orange',
      menu: 'indigo',
      payment_gate: 'pink',
      create_payment: 'rose',
      action: 'violet',
      input: 'cyan',
      random: 'amber',
      end: 'red',
    };
    return colors[blockType] || 'gray';
  }, []);

  const colorClasses: Record<string, { bg: string; border: string; text: string }> = useMemo(() => ({
    green: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800' },
    blue: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800' },
    purple: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-800' },
    yellow: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800' },
    orange: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-800' },
    indigo: { bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-800' },
    pink: { bg: 'bg-pink-50', border: 'border-pink-200', text: 'text-pink-800' },
    red: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-800' },
    gray: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-800' },
  }), []);

  const blockType = node.data?.blockType || 'text';
  const blockColor = getBlockColor(blockType);
  const colorClass = colorClasses[blockColor];

  return (
    <div className="flex flex-col h-full" role="region" aria-label="Панель свойств блока">
      <div className="p-4 border-b bg-gray-50 dark:bg-gray-900 shrink-0">
        <div className="flex items-center justify-between pb-3">
          <div className="flex-1">
            <h2 id="properties-title" className="text-lg font-semibold">⚙️ Свойства</h2>
            <p className="text-xs text-gray-500">Тип: {blockType}</p>
          </div>
          <button
            onClick={onDelete}
            className="rounded p-1 text-red-500 hover:bg-red-50"
            title="Удалить блок"
            aria-label="Удалить выбранный блок"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700" role="tablist" aria-label="Вкладки редактора">
        <div className="flex gap-4 px-4">
          <button
            onClick={() => setActiveTab('edit')}
            role="tab"
            aria-selected={activeTab === 'edit'}
            aria-controls="properties-tab-panel"
            id="edit-tab"
            className={clsx(
              'border-b-2 pb-2 text-sm font-medium transition-colors',
              activeTab === 'edit'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            )}
          >
            ✏️ Редактирование
          </button>
          {['text', 'image', 'video', 'menu'].includes(blockType) && (
            <button
              onClick={() => setActiveTab('preview')}
              role="tab"
              aria-selected={activeTab === 'preview'}
              aria-controls="properties-tab-panel"
              id="preview-tab"
              className={clsx(
                'border-b-2 pb-2 text-sm font-medium transition-colors',
                activeTab === 'preview'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              )}
            >
              👁️ Предпросмотр
            </button>
          )}
        </div>
      </div>

      {/* Tab Content */}
      <div
        id="properties-tab-panel"
        role="tabpanel"
        aria-labelledby={activeTab === 'preview' ? 'preview-tab' : 'edit-tab'}
        tabIndex={0}
        className="flex-1 overflow-y-auto p-4"
      >
        {activeTab === 'preview' && ['text', 'image', 'video', 'menu'].includes(blockType) ? (
          <div className="space-y-4">
            <TelegramMessagePreview
              type={blockType as any}
              content={{
                text: localConfig.text,
                photoUrl: localConfig.photo_file_id,
                videoUrl: localConfig.video_file_id,
                caption: localConfig.caption,
                buttons: localConfig.buttons,
                parseMode: localConfig.parse_mode,
              }}
            />
            <div className="rounded-md border border-blue-200 bg-blue-50 p-3 dark:border-blue-900 dark:bg-blue-900/20" role="note">
              <p className="text-xs text-blue-900 dark:text-blue-300">
                💡 Это preview показывает как сообщение будет выглядеть в Telegram.
                Некоторые функции (например, inline keyboard) могут отличаться в зависимости от настроек бота.
              </p>
            </div>
          </div>
        ) : (
          <form className="space-y-4" role="form" aria-label="Свойства блока" aria-labelledby="properties-title">
        {/* Block Info */}
        <div className={`p-3 rounded-lg border ${colorClass.bg} ${colorClass.border}`} role="region" aria-label="Описание блока">
          <h4 className={`font-semibold mb-1 ${colorClass.text}`}>
            {getBlockTitle(blockType)}
          </h4>
          <p className={`text-sm ${colorClass.text} opacity-80`}>
            {getBlockDescription(blockType)}
          </p>
        </div>

        {/* Label */}
        <div>
          <label htmlFor="block-label-input" className="mb-1 block text-sm font-medium text-gray-700">
            Название блока
            <span className="ml-2 text-xs text-gray-500">(отображается на диаграмме)</span>
          </label>
          <input
            id="block-label-input"
            type="text"
            value={node.data?.label || ''}
            onChange={(e) => updateNode(node.id, { label: e.target.value })}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Введите название..."
            aria-describedby="block-label-help"
          />
          <p id="block-label-help" className="text-xs text-gray-500 mt-1">Это название будет отображаться на блоке в диаграмме</p>
        </div>

        {/* Type-specific config */}
        {blockType === 'text' && (
          <>
            <div>
              <label htmlFor="text-message-input" className="mb-1 block text-sm font-medium text-gray-700">
                Текст сообщения
                <span className="ml-2 text-xs text-red-500" aria-label="обязательное поле">*</span>
              </label>
              <textarea
                id="text-message-input"
                value={localConfig.text || ''}
                onChange={(e) => handleConfigChange('text', e.target.value)}
                rows={4}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Введите текст сообщения..."
                aria-required="true"
                aria-describedby="text-message-help"
              />
              <p id="text-message-help" className="text-xs text-gray-500 mt-1">
                Поддерживается HTML: <code className="text-xs bg-gray-100 px-1 rounded">&lt;b&gt;жирный&lt;/b&gt;</code>, <code className="text-xs bg-gray-100 px-1 rounded">&lt;i&gt;курсив&lt;/i&gt;</code>
              </p>
            </div>
            <div>
              <label htmlFor="text-parse-mode" className="mb-1 block text-sm font-medium text-gray-700">
                Форматирование
              </label>
              <select
                id="text-parse-mode"
                value={localConfig.parse_mode || 'HTML'}
                onChange={(e) => handleConfigChange('parse_mode', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                aria-describedby="text-parse-mode-help"
              >
                <option value="HTML">HTML</option>
                <option value="Markdown">Markdown</option>
              </select>
              <p id="text-parse-mode-help" className="text-xs text-gray-500 mt-1">Выберите формат текста</p>
            </div>
          </>
        )}

        {blockType === 'video' && (
          <>
            <Suspense fallback={<div className="text-sm text-gray-500">Загрузка выбора медиа...</div>}>
              <MediaSelector
                fileType="video"
                value={localConfig.video_file_id || ''}
                onChange={(value: string) => handleConfigChange('video_file_id', value)}
              />
            </Suspense>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Описание к видео
                <span className="ml-2 text-xs text-gray-500">(опционально)</span>
              </label>
              <textarea
                value={localConfig.caption || ''}
                onChange={(e) => handleConfigChange('caption', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Введите описание..."
              />
            </div>
          </>
        )}

        {blockType === 'image' && (
          <>
            <Suspense fallback={<div className="text-sm text-gray-500">Загрузка выбора медиа...</div>}>
              <MediaSelector
                fileType="photo"
                value={localConfig.photo_file_id || ''}
                onChange={(value: string) => handleConfigChange('photo_file_id', value)}
              />
            </Suspense>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Подпись к изображению
                <span className="ml-2 text-xs text-gray-500">(опционально)</span>
              </label>
              <textarea
                value={localConfig.caption || ''}
                onChange={(e) => handleConfigChange('caption', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Введите подпись..."
              />
            </div>
          </>
        )}

        {blockType === 'delay' && (
          <div>
            <label htmlFor="delay-seconds" className="mb-1 block text-sm font-medium text-gray-700">
              Задержка (секунды)
            </label>
            <input
              id="delay-seconds"
              type="number"
              min="1"
              value={localConfig.delay_seconds || 5}
              onChange={(e) => handleConfigChange('delay_seconds', parseInt(e.target.value))}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        )}

        {blockType === 'confirmation' && (
          <>
            <div>
              <label htmlFor="confirmation-message" className="mb-1 block text-sm font-medium text-gray-700">
                Текст подтверждения
              </label>
              <textarea
                id="confirmation-message"
                value={localConfig.text || ''}
                onChange={(e) => handleConfigChange('text', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Вы уверены?"
              />
            </div>
            <div>
              <label htmlFor="confirmation-yes" className="mb-1 block text-sm font-medium text-gray-700">
                Текст кнопки "Да"
              </label>
              <input
                id="confirmation-yes"
                type="text"
                value={localConfig.yes_text || 'Да'}
                onChange={(e) => handleConfigChange('yes_text', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="confirmation-no" className="mb-1 block text-sm font-medium text-gray-700">
                Текст кнопки "Нет"
              </label>
              <input
                id="confirmation-no"
                type="text"
                value={localConfig.no_text || 'Нет'}
                onChange={(e) => handleConfigChange('no_text', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </>
        )}

        {blockType === 'course_menu' && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Название переменной для курса
            </label>
            <input
              type="text"
              value={localConfig.course_var || ''}
              onChange={(e) => handleConfigChange('course_var', e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="selected_course"
            />
          </div>
        )}

        {blockType === 'quiz' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Вопрос
              </label>
              <textarea
                value={localConfig.question || ''}
                onChange={(e) => handleConfigChange('question', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Введите вопрос..."
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Варианты ответов (по одному на строку)
              </label>
              <textarea
                value={(localConfig.options || []).join('\n')}
                onChange={(e) => handleConfigChange('options', e.target.value.split('\n').filter(Boolean))}
                rows={4}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Вариант 1&#10;Вариант 2&#10;Вариант 3"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Правильный ответ (номер варианта)
              </label>
              <input
                type="number"
                min="1"
                value={localConfig.correct_answer || 1}
                onChange={(e) => handleConfigChange('correct_answer', parseInt(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </>
        )}

        {blockType === 'decision' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Название переменной
              </label>
              <input
                type="text"
                value={localConfig.variable || ''}
                onChange={(e) => handleConfigChange('variable', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="user_choice"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Условие
              </label>
              <select
                value={localConfig.condition || 'equals'}
                onChange={(e) => handleConfigChange('condition', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="equals">Равно</option>
                <option value="not_equals">Не равно</option>
                <option value="contains">Содержит</option>
                <option value="greater">Больше</option>
                <option value="less">Меньше</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Значение
              </label>
              <input
                type="text"
                value={localConfig.value || ''}
                onChange={(e) => handleConfigChange('value', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Значение для сравнения"
              />
            </div>
          </>
        )}

        {blockType === 'menu' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Текст сообщения
              </label>
              <textarea
                value={localConfig.text || ''}
                onChange={(e) => handleConfigChange('text', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Выберите действие..."
              />
            </div>
            <MenuButtonsBuilder
              buttons={localConfig.buttons || []}
              onChange={(buttons) => handleConfigChange('buttons', buttons)}
            />
          </>
        )}

        {blockType === 'payment_gate' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Название переменной для проверки
              </label>
              <input
                type="text"
                value={localConfig.payment_var || ''}
                onChange={(e) => handleConfigChange('payment_var', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="is_paid"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Текст если оплачено
              </label>
              <textarea
                value={localConfig.paid_message || ''}
                onChange={(e) => handleConfigChange('paid_message', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Оплата подтверждена!"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Текст если не оплачено
              </label>
              <textarea
                value={localConfig.unpaid_message || ''}
                onChange={(e) => handleConfigChange('unpaid_message', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Требуется оплата"
              />
            </div>
          </>
        )}

        {blockType === 'create_payment' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Сумма (рубли)
              </label>
              <input
                type="number"
                min="1"
                value={localConfig.amount || 100}
                onChange={(e) => handleConfigChange('amount', parseInt(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Описание платежа
              </label>
              <textarea
                value={localConfig.description || ''}
                onChange={(e) => handleConfigChange('description', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Оплата курса..."
              />
            </div>
          </>
        )}

        {blockType === 'action' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Название переменной
              </label>
              <input
                type="text"
                value={localConfig.variable || ''}
                onChange={(e) => handleConfigChange('variable', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="user_name"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Действие
              </label>
              <select
                value={localConfig.action_type || 'set'}
                onChange={(e) => handleConfigChange('action_type', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="set">Установить значение</option>
                <option value="increment">Увеличить на</option>
                <option value="decrement">Уменьшить на</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Значение
              </label>
              <input
                type="text"
                value={localConfig.value || ''}
                onChange={(e) => handleConfigChange('value', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Значение"
              />
            </div>
          </>
        )}

        {blockType === 'input' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Текст запроса
              </label>
              <textarea
                value={localConfig.prompt || ''}
                onChange={(e) => handleConfigChange('prompt', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Введите ваше имя..."
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Название переменной для сохранения
              </label>
              <input
                type="text"
                value={localConfig.variable || ''}
                onChange={(e) => handleConfigChange('variable', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="user_name"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Тип валидации
              </label>
              <select
                value={localConfig.validation || 'any'}
                onChange={(e) => handleConfigChange('validation', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="any">Любой текст</option>
                <option value="number">Число</option>
                <option value="email">Email</option>
                <option value="phone">Телефон</option>
              </select>
            </div>
          </>
        )}

        {blockType === 'random' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Режим выбора
              </label>
              <select
                value={localConfig.mode || 'equal'}
                onChange={(e) => handleConfigChange('mode', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="equal">Равные шансы</option>
                <option value="weighted">Взвешенные шансы</option>
              </select>
            </div>
            {localConfig.mode === 'weighted' && (
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Веса (через запятую)
                </label>
                <input
                  type="text"
                  value={(localConfig.weights || []).join(', ')}
                  onChange={(e) => handleConfigChange('weights', e.target.value.split(',').map(Number))}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="30, 30, 40"
                />
              </div>
            )}
          </>
        )}

        {blockType === 'end' && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Финальное сообщение
            </label>
            <textarea
              value={localConfig.message || ''}
              onChange={(e) => handleConfigChange('message', e.target.value)}
              rows={3}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Спасибо за использование бота!"
            />
          </div>
        )}
          </form>
        )}
      </div>
    </div>
  );
}

export { BlockProperties };
export default BlockProperties;
