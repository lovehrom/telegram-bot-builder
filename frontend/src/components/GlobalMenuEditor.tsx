import { useState, useEffect } from 'react';
import { Plus, Trash2, Save, ArrowLeft } from 'lucide-react';
import { toast } from './ui';

interface GlobalMenuButton {
  label: string;
  action_type: 'launch_flow' | 'callback';
  target_flow_name?: string;
  target_callback?: string;
}

interface GlobalMenuData {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  buttons: GlobalMenuButton[];
}

interface Flow {
  id: number;
  name: string;
  is_active: boolean;
}

interface GlobalMenuEditorProps {
  onBack: () => void;
}

export function GlobalMenuEditor({ onBack }: GlobalMenuEditorProps) {
  const [menuData, setMenuData] = useState<GlobalMenuData | null>(null);
  const [flows, setFlows] = useState<Flow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const availableCallbacks = [
    { value: 'show_progress', label: '📊 Показать прогресс' },
    { value: 'show_help', label: '❓ Показать справку' },
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const menuResponse = await fetch('/api/global-menu');
      if (menuResponse.ok) {
        const menu = await menuResponse.json();
        setMenuData(menu);
      }

      const flowsResponse = await fetch('/api/flows');
      if (flowsResponse.ok) {
        const flowsData = await flowsResponse.json();
        setFlows(flowsData);
      }
    } catch (error) {
      toast.error('Не удалось загрузить данные');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddButton = () => {
    if (!menuData) return;

    const newButton: GlobalMenuButton = {
      label: `Кнопка ${menuData.buttons.length + 1}`,
      action_type: 'launch_flow',
      target_flow_name: flows.length > 0 ? flows[0].name : undefined,
    };

    setMenuData({
      ...menuData,
      buttons: [...menuData.buttons, newButton],
    });
  };

  const handleRemoveButton = (index: number) => {
    if (!menuData) return;

    setMenuData({
      ...menuData,
      buttons: menuData.buttons.filter((_, i) => i !== index),
    });
  };

  const handleButtonChange = (index: number, field: keyof GlobalMenuButton, value: string) => {
    if (!menuData) return;

    const newButtons = [...menuData.buttons];
    newButtons[index] = {
      ...newButtons[index],
      [field]: value,
    };

    if (field === 'action_type') {
      if (value === 'launch_flow') {
        newButtons[index].target_flow_name = flows.length > 0 ? flows[0].name : undefined;
        newButtons[index].target_callback = undefined;
      } else {
        newButtons[index].target_callback = 'show_progress';
        newButtons[index].target_flow_name = undefined;
      }
    }

    setMenuData({
      ...menuData,
      buttons: newButtons,
    });
  };

  const handleSave = async () => {
    if (!menuData) return;

    setIsSaving(true);
    try {
      const response = await fetch('/api/global-menu', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          buttons: menuData.buttons,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save');
      }

      const updated = await response.json();
      setMenuData(updated);
      toast.success('Главное меню сохранено!');
    } catch (error) {
      toast.error('Не удалось сохранить главное меню');
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center" style={{ background: '#0A0A0A' }}>
        <div style={{ color: '#71717A' }}>Загрузка...</div>
      </div>
    );
  }

  if (!menuData) {
    return (
      <div className="flex h-full items-center justify-center" style={{ background: '#0A0A0A' }}>
        <div style={{ color: '#EF4444' }}>Не удалось загрузить главное меню</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col" style={{ background: '#0A0A0A' }}>
      {/* Header */}
      <header className="flex items-center justify-between border-b px-6 py-4" style={{ background: '#111111', borderBottom: '1px solid #27272A' }}>
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="flex items-center gap-2 rounded-lg px-4 py-2 transition-all"
            style={{ background: '#27272A', color: '#A1A1AA' }}
            onMouseEnter={(e) => { e.currentTarget.style.background = '#3F3F46'; e.currentTarget.style.color = '#FFFFFF'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = '#27272A'; e.currentTarget.style.color = '#A1A1AA'; }}
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Назад</span>
          </button>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: '#FFFFFF' }}>Главное меню</h1>
            <p className="text-sm" style={{ color: '#71717A' }}>
              Настройте кнопки главного меню бота
            </p>
          </div>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2 rounded-lg px-6 py-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ background: '#3B82F6', color: '#FFFFFF' }}
          onMouseEnter={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.background = '#2563EB'; }}
          onMouseLeave={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.background = '#3B82F6'; }}
        >
          <Save className="h-4 w-4" />
          <span>{isSaving ? 'Сохранение...' : 'Сохранить'}</span>
        </button>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-auto p-6" style={{ background: '#0A0A0A' }}>
        <div className="mx-auto max-w-4xl">
          {/* Help Box */}
          <div className="mb-6 rounded-lg border p-4" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
            <h3 className="mb-2 font-semibold" style={{ color: '#60A5FA' }}>💡 Как это работает:</h3>
            <ul className="list-inside list-disc space-y-1 text-sm" style={{ color: '#93C5FD' }}>
              <li>Добавьте кнопки, которые будут показываться в главном меню бота</li>
              <li><strong>Запустить flow:</strong> кнопка запускает выбранный сценарий</li>
              <li><strong>Колбэк:</strong> кнопка выполняет встроенную функцию (прогресс, справка)</li>
            </ul>
          </div>

          {/* Buttons List */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold" style={{ color: '#FFFFFF' }}>
              Кнопки меню ({menuData.buttons.length})
            </h2>

            {menuData.buttons.length === 0 ? (
              <div className="rounded-lg border-2 border-dashed p-12 text-center" style={{ background: '#111111', borderColor: '#27272A' }}>
                <p className="mb-4" style={{ color: '#71717A' }}>
                  Нет кнопок. Добавьте первую кнопку ниже.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {menuData.buttons.map((button, index) => (
                  <div
                    key={index}
                    className="rounded-lg border p-4"
                    style={{ background: '#111111', borderColor: '#27272A' }}
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <h3 className="font-medium" style={{ color: '#FFFFFF' }}>
                        Кнопка {index + 1}
                      </h3>
                      <button
                        onClick={() => handleRemoveButton(index)}
                        className="rounded p-2 transition-colors"
                        style={{ color: '#71717A' }}
                        onMouseEnter={(e) => { e.currentTarget.style.color = '#EF4444'; e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.color = '#71717A'; e.currentTarget.style.background = 'transparent'; }}
                        title="Удалить кнопку"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>

                    {/* Label */}
                    <div className="mb-3">
                      <label className="mb-1 block text-sm font-medium" style={{ color: '#A1A1AA' }}>
                        Текст на кнопке <span style={{ color: '#EF4444' }}>*</span>
                      </label>
                      <input
                        type="text"
                        value={button.label}
                        onChange={(e) => handleButtonChange(index, 'label', e.target.value)}
                        placeholder="Например: 📚 Курсы"
                        maxLength={64}
                        className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2"
                        style={{ background: '#1A1A1A', borderColor: '#27272A', color: '#FFFFFF' }}
                        onFocus={(e) => { e.currentTarget.style.borderColor = '#3B82F6'; e.currentTarget.style.boxShadow = '0 0 0 2px rgba(59, 130, 246, 0.2)'; }}
                        onBlur={(e) => { e.currentTarget.style.borderColor = '#27272A'; e.currentTarget.style.boxShadow = 'none'; }}
                      />
                    </div>

                    {/* Action Type */}
                    <div className="mb-3">
                      <label className="mb-1 block text-sm font-medium" style={{ color: '#A1A1AA' }}>
                        Тип действия <span style={{ color: '#EF4444' }}>*</span>
                      </label>
                      <select
                        value={button.action_type}
                        onChange={(e) =>
                          handleButtonChange(index, 'action_type', e.target.value as 'launch_flow' | 'callback')
                        }
                        className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2"
                        style={{ background: '#1A1A1A', borderColor: '#27272A', color: '#FFFFFF' }}
                        onFocus={(e) => { e.currentTarget.style.borderColor = '#3B82F6'; }}
                        onBlur={(e) => { e.currentTarget.style.borderColor = '#27272A'; }}
                      >
                        <option value="launch_flow">🚀 Запустить flow (сценарий)</option>
                        <option value="callback">⚡ Колбэк (встроенная функция)</option>
                      </select>
                    </div>

                    {/* Target */}
                    {button.action_type === 'launch_flow' ? (
                      <div>
                        <label className="mb-1 block text-sm font-medium" style={{ color: '#A1A1AA' }}>
                          Выберите flow <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <select
                          value={button.target_flow_name || ''}
                          onChange={(e) => handleButtonChange(index, 'target_flow_name', e.target.value)}
                          className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2"
                          style={{ background: '#1A1A1A', borderColor: '#27272A', color: '#FFFFFF' }}
                          onFocus={(e) => { e.currentTarget.style.borderColor = '#3B82F6'; }}
                          onBlur={(e) => { e.currentTarget.style.borderColor = '#27272A'; }}
                        >
                          <option value="">-- Выберите flow --</option>
                          {flows.map((flow) => (
                            <option key={flow.id} value={flow.name}>
                              {flow.name} {flow.is_active ? '✅' : '⚪'}
                            </option>
                          ))}
                        </select>
                        {flows.length === 0 && (
                          <p className="mt-1 text-xs" style={{ color: '#71717A' }}>
                            Нет доступных flows. Создайте их сначала в редакторе.
                          </p>
                        )}
                      </div>
                    ) : (
                      <div>
                        <label className="mb-1 block text-sm font-medium" style={{ color: '#A1A1AA' }}>
                          Выберите функцию <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <select
                          value={button.target_callback || ''}
                          onChange={(e) => handleButtonChange(index, 'target_callback', e.target.value)}
                          className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2"
                          style={{ background: '#1A1A1A', borderColor: '#27272A', color: '#FFFFFF' }}
                          onFocus={(e) => { e.currentTarget.style.borderColor = '#3B82F6'; }}
                          onBlur={(e) => { e.currentTarget.style.borderColor = '#27272A'; }}
                        >
                          <option value="">-- Выберите функцию --</option>
                          {availableCallbacks.map((cb) => (
                            <option key={cb.value} value={cb.value}>
                              {cb.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Add Button */}
            {menuData.buttons.length < 10 && (
              <button
                onClick={handleAddButton}
                className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-3 text-sm font-medium transition-colors"
                style={{ background: '#111111', borderColor: '#27272A', color: '#A1A1AA' }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#3B82F6'; e.currentTarget.style.color = '#60A5FA'; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#27272A'; e.currentTarget.style.color = '#A1A1AA'; }}
              >
                <Plus className="h-4 w-4" />
                Добавить кнопку ({menuData.buttons.length}/10)
              </button>
            )}
          </div>

          {/* Preview */}
          {menuData.buttons.length > 0 && (
            <div className="mt-8 rounded-lg border p-4" style={{ background: '#111111', borderColor: '#27272A' }}>
              <h3 className="mb-3 font-semibold" style={{ color: '#FFFFFF' }}>📱 Предпросмотр:</h3>
              <div className="space-y-2">
                {menuData.buttons.map((button, index) => (
                  <div
                    key={index}
                    className="rounded px-4 py-2 text-center text-sm font-medium"
                    style={{ background: '#3B82F6', color: '#FFFFFF' }}
                  >
                    {button.label}
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs" style={{ color: '#71717A' }}>
                Так кнопки будут выглядеть в боте
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
