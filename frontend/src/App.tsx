import { useState, useEffect, useRef, useCallback } from 'react';
import { FlowEditor } from './components/FlowEditor/FlowEditor';
import { TemplateSelector } from './components/TemplateSelector';
import { GlobalMenuEditor } from './components/GlobalMenuEditor';
import { flowApi, templatesApi } from './services/api';
import type { ConversationFlow } from './types/flow';
import { Plus, Save, Trash2, Menu } from 'lucide-react';
import { ConfirmDialog, PromptDialog, ToastContainer } from './components/ui';
import { toast } from './components/ui';
import axios from 'axios';

function App() {
  const [currentView, setCurrentView] = useState<'flows' | 'globalMenu'>('flows');
  const [flows, setFlows] = useState<ConversationFlow[]>([]);
  const [selectedFlowId, setSelectedFlowId] = useState<number | undefined>(undefined);
  const [isCreating, setIsCreating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved');

  // Modal states
  const [createFlowModal, setCreateFlowModal] = useState(false);
  const [deleteFlowModal, setDeleteFlowModal] = useState<{ flowId: number; flowName: string } | null>(null);
  const [renameFlowModal, setRenameFlowModal] = useState<{ flowId: number; currentName: string } | null>(null);
  const [switchFlowModal, setSwitchFlowModal] = useState<{ fromId: number; toId: number } | null>(null);
  const [saveTemplateModal, setSaveTemplateModal] = useState(false);
  const flowActionRef = useRef<{ flowId?: number; flowName?: string }>({});

  useEffect(() => {
    loadFlows();
  }, []);

  // Предупреждение при выходе с несохраненными изменениями
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (saveStatus === 'unsaved') {
        e.preventDefault();
        e.returnValue = ''; // Chrome требует returnValue
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [saveStatus]);

  // Слушатель события сохранения из FlowEditor (Ctrl+S)
  useEffect(() => {
    const handleFlowEditorSave = async (event: Event) => {
      const customEvent = event as CustomEvent<{ flowId: number }>;
      const { flowId } = customEvent.detail;
      if (flowId === selectedFlowId) {
        await handleSaveFlow();
      }
    };

    window.addEventListener('flow-editor-save', handleFlowEditorSave);
    return () => window.removeEventListener('flow-editor-save', handleFlowEditorSave);
  }, [selectedFlowId]); //eslint-disable-line

  const loadFlows = useCallback(async () => {
    try {
      const data = await flowApi.getAllFlows();
      setFlows(data);
      if (data.length > 0 && !selectedFlowId) {
        // Выбрать первый активный flow, или первый если нет активных
        const activeFlow = data.find(f => f.is_active);
        setSelectedFlowId(activeFlow ? activeFlow.id : data[0].id);
      }
    } catch (err) {
      setError('Не удалось загрузить сценарии. Проверьте подключение к серверу.');
    }
  }, [selectedFlowId]);

  const handleCreateFlow = useCallback(async (name: string) => {
    if (!name) return;

    setIsCreating(true);
    try {
      const newFlow = await flowApi.createFlow({
        name,
        description: '',
        is_active: true,
      });
      setFlows(prev => [...prev, newFlow]);
      setSelectedFlowId(newFlow.id);
      toast.success('Сценарий успешно создан');
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorMsg = error.response?.data?.detail || error.message || 'Не удалось создать сценарий';
        toast.error(errorMsg);
      } else {
        toast.error('Не удалось создать сценарий');
      }
    } finally {
      setIsCreating(false);
    }
  }, []);

  const handleCreateFromTemplate = useCallback(async (templateId: number) => {
    setIsCreating(true);
    try {
      const response = await fetch(`/api/flows/from-template/${templateId}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to create flow from template');

      const newFlow = await response.json();
      setFlows(prev => [...prev, newFlow]);
      setSelectedFlowId(newFlow.id);
      toast.success('Сценарий создан из шаблона с блоками!');
    } catch (error: any) {
      toast.error('Не удалось создать сценарий: ' + error.message);
    } finally {
      setIsCreating(false);
    }
  }, []);

  const handleDeleteFlow = useCallback(async (flowId: number, flowName: string) => {
    const flow = flows.find(f => f.id === flowId);

    if (flow?.is_active) {
      toast.warning('Нельзя удалить активный сценарий. Сначала активируйте другой.');
      return;
    }

    // Store flow info and show modal
    flowActionRef.current = { flowId, flowName };
    setDeleteFlowModal({ flowId, flowName });
  }, [flows]);

  const confirmDeleteFlow = useCallback(async () => {
    const { flowId } = flowActionRef.current;
    if (!flowId) return;

    try {
      await flowApi.deleteFlow(flowId);
      setFlows(prev => prev.filter(f => f.id !== flowId));
      if (selectedFlowId === flowId) {
        setSelectedFlowId(undefined);
      }
      toast.success('Сценарий успешно удалён');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Неизвестная ошибка';
      toast.error('Не удалось удалить сценарий: ' + errorMessage);
    } finally {
      setDeleteFlowModal(null);
      flowActionRef.current = {};
    }
  }, [selectedFlowId]);

  const handleToggleActive = useCallback(async (flowId: number) => {
    try {
      await flowApi.activateFlow(flowId);
      // Обновить список flows
      await loadFlows();
      toast.success('Активный сценарий изменён');
    } catch (error: any) {
      toast.error('Не удалось изменить активный сценарий: ' + (error.response?.data?.detail || error.message));
    }
  }, [loadFlows]);

  const handleRenameFlow = useCallback((flowId: number, currentName: string) => {
    setRenameFlowModal({ flowId, currentName });
  }, []);

  const confirmRenameFlow = useCallback(async (newName: string) => {
    const { flowId } = flowActionRef.current;
    if (!flowId) return;

    try {
      const updated = await flowApi.updateFlow(flowId, { name: newName });
      setFlows(prev => prev.map(f => f.id === flowId ? updated : f));
      toast.success('Сценарий переименован');
    } catch (error: any) {
      toast.error('Не удалось переименовать: ' + (error.response?.data?.detail || error.message));
    } finally {
      setRenameFlowModal(null);
      flowActionRef.current = {};
    }
  }, []);

  const handleFlowChange = useCallback((newFlowId: number) => {
    if (saveStatus === 'unsaved' && selectedFlowId !== undefined) {
      // Store flow info and show modal
      flowActionRef.current = { flowId: selectedFlowId };
      setSwitchFlowModal({ fromId: selectedFlowId, toId: newFlowId });
    } else {
      setSelectedFlowId(newFlowId);
    }
  }, [saveStatus, selectedFlowId]);

  const confirmSwitchFlow = useCallback(() => {
    const { toId } = switchFlowModal || {};
    if (toId) {
      setSelectedFlowId(toId);
    }
    setSwitchFlowModal(null);
    flowActionRef.current = {};
  }, [switchFlowModal]);

  const handleSaveFlow = useCallback(async () => {
    if (!selectedFlowId) return;

    setIsSaving(true);
    setSaveStatus('saving');

    try {
      // Trigger save via the FlowEditor component
      // We need to access the store's saveFlow method
      const { useFlowStore } = await import('./hooks/useFlowStore');
      const saveFlow = useFlowStore.getState().saveFlow;
      await saveFlow();

      setSaveStatus('saved');
      toast.success('Сценарий успешно сохранён');
      setTimeout(() => {
        setSaveStatus('saved');
      }, 2000);
    } catch (error) {
      setSaveStatus('unsaved');
      const errorMessage = error instanceof Error ? error.message : 'Не удалось сохранить сценарий';
      toast.error(errorMessage);
      setTimeout(() => setSaveStatus('saved'), 3000);
    } finally {
      setIsSaving(false);
    }
  }, [selectedFlowId]);

  const handleSaveAsTemplate = useCallback(async (name: string, description: string) => {
    if (!selectedFlowId) return;

    const flow = flows.find(f => f.id === selectedFlowId);
    if (!flow) return;

    try {
      const { useFlowStore } = await import('./hooks/useFlowStore');
      const { nodes, edges } = useFlowStore.getState();

      // Собрать данные блоков
      const blocksData = {
        blocks: nodes.map(node => ({
          id: node.data.id || 0,
          block_type: node.data.blockType,
          label: node.data.label,
          config: node.data.config,
          position_x: node.position.x,
          position_y: node.position.y,
          position: 0
        }))
      };

      // Собрать данные связей
      const connectionsData = {
        connections: edges.map(edge => ({
          from_block_id: parseInt(edge.source) || 0,
          to_block_id: parseInt(edge.target) || 0,
          condition: edge.data?.condition || null
        }))
      };

      // Используем templatesApi вместо raw fetch
      await templatesApi.createTemplate({
        name,
        description,
        flow_id: selectedFlowId,
        blocks_data: JSON.stringify(blocksData),
        connections_data: JSON.stringify(connectionsData)
      });

      toast.success('Шаблон сохранён!');
    } catch (error: any) {
      const errorMessage = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : error.message || 'Неизвестная ошибка';
      toast.error('Не удалось сохранить шаблон: ' + errorMessage);
    } finally {
      setSaveTemplateModal(false);
    }
  }, [selectedFlowId, flows]);

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col" style={{ background: '#0A0A0A' }}>
      <header role="banner" aria-label="Заголовок приложения">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between px-4 md:px-6 py-3 md:py-4 gap-3 md:gap-0" style={{ background: '#111111', borderBottom: '1px solid #27272A' }}>
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-xl md:text-2xl font-bold" style={{ color: '#FFFFFF' }}>Bot Constructor</h1>
              <p className="text-xs md:text-sm hidden sm:block" style={{ color: '#71717A' }}>Визуальный редактор сценариев бота</p>
            </div>
            {/* Save status indicator - mobile */}
            <div role="status" aria-live="polite" aria-atomic="true" className="md:hidden">
              {saveStatus === 'saved' && (
                <span className="text-xs" style={{ color: '#22C55E' }}>✅</span>
              )}
              {saveStatus === 'saving' && (
                <span className="text-xs" style={{ color: '#3B82F6' }}>💾</span>
              )}
              {saveStatus === 'unsaved' && (
                <span className="text-xs" style={{ color: '#F59E0B' }}>⚠️</span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
            {/* Global Menu Button */}
            <button
              onClick={() => setCurrentView(currentView === 'flows' ? 'globalMenu' : 'flows')}
              className="flex items-center gap-1 md:gap-2 rounded-lg px-2 md:px-4 py-2 text-sm md:text-base flex-1 md:flex-none justify-center transition-all duration-200"
              style={{ background: '#1A1A1A', color: '#A1A1AA', border: '1px solid #27272A' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = '#222222'; e.currentTarget.style.color = '#FFFFFF'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = '#1A1A1A'; e.currentTarget.style.color = '#A1A1AA'; }}
              aria-label="Главное меню"
            >
              <Menu className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Главное меню</span>
            </button>
            <button
              onClick={handleSaveFlow}
              disabled={isSaving || !selectedFlowId || currentView !== 'flows'}
              className="save-button flex items-center gap-1 md:gap-2 rounded-lg px-2 md:px-4 py-2 text-sm md:text-base flex-1 md:flex-none justify-center transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ background: '#3B82F6', color: '#FFFFFF' }}
              onMouseEnter={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.background = '#2563EB'; }}
              onMouseLeave={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.background = '#3B82F6'; }}
              aria-label={isSaving ? 'Идёт сохранение...' : 'Сохранить текущий сценарий'}
            >
              <Save className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{isSaving ? 'Сохранение...' : 'Сохранить'}</span>
            </button>
            <button
              onClick={() => setCreateFlowModal(true)}
              disabled={isCreating}
              className="flex items-center gap-1 md:gap-2 rounded-lg px-2 md:px-4 py-2 text-sm md:text-base flex-1 md:flex-none justify-center transition-all duration-200"
              style={{ background: '#3B82F6', color: '#FFFFFF' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = '#2563EB'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = '#3B82F6'; }}
              aria-label={isCreating ? 'Создание нового сценария...' : 'Создать новый сценарий'}
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{isCreating ? 'Создание...' : 'Новый'}</span>
            </button>
            <TemplateSelector
              onSelect={handleCreateFromTemplate}
              buttonLabel="📋"
            />
            <button
              onClick={() => setSaveTemplateModal(true)}
              disabled={!selectedFlowId}
              className="hidden md:flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ background: '#F59E0B', color: '#FFFFFF' }}
              onMouseEnter={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.background = '#D97706'; }}
              onMouseLeave={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.background = '#F59E0B'; }}
              aria-label="Сохранить весь flow как шаблон"
            >
              💾 Шаблон
            </button>
            <a
              href="/admin"
              className="flex items-center gap-2 rounded-lg px-3 md:px-4 py-2 text-sm transition-all duration-200"
              style={{ background: '#1A1A1A', color: '#A1A1AA', border: '1px solid #27272A' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = '#222222'; e.currentTarget.style.color = '#FFFFFF'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = '#1A1A1A'; e.currentTarget.style.color = '#A1A1AA'; }}
              aria-label="Вернуться в админку"
            >
              <span className="hidden md:inline">← Назад</span>
              <span className="md:hidden">←</span>
            </a>
            {/* Save status indicator - desktop */}
            <div role="status" aria-live="polite" aria-atomic="true" className="hidden md:block">
              {saveStatus === 'saved' && (
                <span className="flex items-center text-sm" style={{ color: '#22C55E' }}>
                  ✅ Сохранено
                </span>
              )}
              {saveStatus === 'saving' && (
                <span className="flex items-center text-sm" style={{ color: '#3B82F6' }}>
                  💾 Сохранение...
                </span>
              )}
              {saveStatus === 'unsaved' && (
                <span className="flex items-center text-sm" style={{ color: '#F59E0B' }}>
                  ⚠️ Несохраненные изменения
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {currentView === 'flows' && (
          <aside role="complementary" aria-label="Список сценариев" className="w-64 border-r overflow-y-auto" style={{ background: '#111111', borderColor: '#27272A' }}>
            <div className="p-4">
              <h2 id="flows-heading" className="mb-4 text-lg font-semibold" style={{ color: '#FFFFFF' }}>Сценарии ({flows.length})</h2>
              {flows.length === 0 && (
                <div className="p-3 rounded text-sm" style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#FCD34D' }} role="alert">
                  <p className="font-medium mb-1">Нет сценариев</p>
                  <p>Создайте первый сценарий нажав "Новый сценарий"</p>
                </div>
              )}
              <div role="list" aria-labelledby="flows-heading" className="space-y-2 max-h-[calc(100vh-120px)] overflow-y-auto">
                {flows.map((flow) => (
                  <div
                    key={flow.id}
                    role="listitem"
                    className="relative rounded-lg border p-3 transition-all duration-200"
                    style={{
                      background: selectedFlowId === flow.id ? 'rgba(59, 130, 246, 0.1)' : '#1A1A1A',
                      borderColor: selectedFlowId === flow.id ? '#3B82F6' : '#27272A'
                    }}
                    onMouseEnter={(e) => { if (selectedFlowId !== flow.id) e.currentTarget.style.background = '#222222'; }}
                    onMouseLeave={(e) => { if (selectedFlowId !== flow.id) e.currentTarget.style.background = '#1A1A1A'; }}
                  >
                    <div
                      onClick={() => handleFlowChange(flow.id)}
                      onDoubleClick={() => handleRenameFlow(flow.id, flow.name)}
                      className="cursor-pointer"
                      role="button"
                      tabIndex={0}
                      aria-label={`Выбрать сценарий: ${flow.name}. Двойной клик для переименования`}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') handleFlowChange(flow.id);
                      }}
                    >
                      <div className="font-medium truncate pr-6" style={{ color: '#FFFFFF' }}>{flow.name}</div>
                      <div className="mt-1 flex items-center gap-2 text-xs" style={{ color: '#71717A' }}>
                        <span className="h-2 w-2 rounded-full" style={{ background: flow.is_active ? '#3B82F6' : '#71717A' }} aria-hidden="true" />
                        <span>{flow.is_active ? 'Активен' : 'Неактивен'}</span>
                      </div>
                      {flow.description && (
                        <div className="mt-1 text-xs truncate" style={{ color: '#71717A' }}>{flow.description}</div>
                      )}
                    </div>

                    {/* Кнопка удаления */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteFlow(flow.id, flow.name);
                      }}
                      className="absolute top-2 right-2 p-1 rounded transition-colors"
                      style={{ color: '#71717A' }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = '#EF4444'; e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = '#71717A'; e.currentTarget.style.background = 'transparent'; }}
                      aria-label={`Удалить сценарий: ${flow.name}`}
                    >
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    </button>

                    {/* Переключатель активного flow */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggleActive(flow.id);
                      }}
                      className="mt-2 w-full text-xs py-1.5 px-2 rounded flex items-center justify-center gap-1.5 transition-all duration-200"
                      style={{
                        background: flow.is_active ? 'rgba(59, 130, 246, 0.1)' : '#1A1A1A',
                        color: flow.is_active ? '#60A5FA' : '#A1A1AA',
                        border: '1px solid',
                        borderColor: flow.is_active ? 'rgba(59, 130, 246, 0.3)' : '#27272A'
                      }}
                      onMouseEnter={(e) => {
                        if (flow.is_active) {
                          e.currentTarget.style.background = 'rgba(59, 130, 246, 0.15)';
                        } else {
                          e.currentTarget.style.background = '#222222';
                          e.currentTarget.style.borderColor = '#3B82F6';
                          e.currentTarget.style.color = '#60A5FA';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (flow.is_active) {
                          e.currentTarget.style.background = 'rgba(59, 130, 246, 0.1)';
                        } else {
                          e.currentTarget.style.background = '#1A1A1A';
                          e.currentTarget.style.borderColor = '#27272A';
                          e.currentTarget.style.color = '#A1A1AA';
                        }
                      }}
                      aria-label={flow.is_active ? `Деактивировать сценарий: ${flow.name}` : `Активировать сценарий: ${flow.name}`}
                    >
                      {flow.is_active ? (
                        <>✅ Активен (клик для смены)</>
                      ) : (
                        <>⚪ Неактивен (клик для активации)</>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        )}

        <main role="main" aria-label="Редактор сценария" className="flex-1 overflow-hidden">
          {currentView === 'globalMenu' ? (
            <GlobalMenuEditor onBack={() => setCurrentView('flows')} />
          ) : selectedFlowId ? (
            <FlowEditor key={selectedFlowId} flowId={selectedFlowId} />
          ) : (
            <div className="flex h-full flex-col items-center justify-center p-8" style={{ background: '#0A0A0A' }}>
              <div className="text-center max-w-md">
                <p className="text-6xl mb-4" aria-hidden="true">🎯</p>
                <h3 className="text-xl font-semibold mb-2" style={{ color: '#FFFFFF' }}>Выберите или создайте сценарий</h3>
                <p className="text-sm mb-6" style={{ color: '#71717A' }}>
                  Слева вы можете видеть список всех сценариев. Нажмите "Новый сценарий" чтобы создать первый.
                </p>
                <div className="p-4 rounded text-left text-sm" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', color: '#93C5FD' }}>
                  <p className="font-medium mb-2">💡 Как начать:</p>
                  <ol className="list-decimal list-inside space-y-1 ml-2" style={{ color: '#A1A1AA' }}>
                    <li>Создайте новый сценарий</li>
                    <li>Перетащите блоки из палитры на холст</li>
                    <li>Соедините блоки линиями</li>
                    <li>Настройте свойства каждого блока справа</li>
                    <li>Сохраните изменения</li>
                  </ol>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Modals */}
      <PromptDialog
        isOpen={createFlowModal}
        onClose={() => setCreateFlowModal(false)}
        onSubmit={handleCreateFlow}
        title="Создать новый сценарий"
        placeholder="Введите название сценария..."
        required={true}
        validation={(value) => {
          if (value.length < 3) return 'Название должно содержать минимум 3 символа';
          if (value.length > 100) return 'Название не должно превышать 100 символов';
          return null;
        }}
      />

      {deleteFlowModal && (
        <ConfirmDialog
          isOpen={!!deleteFlowModal}
          onClose={() => setDeleteFlowModal(null)}
          onConfirm={confirmDeleteFlow}
          title="Удалить сценарий?"
          message={`⚠️ Удалить сценарий "${deleteFlowModal.flowName}"?\n\nЭто действие нельзя отменить.`}
          confirmLabel="Удалить"
          cancelLabel="Отмена"
          variant="danger"
        />
      )}

      {renameFlowModal && (
        <PromptDialog
          isOpen={!!renameFlowModal}
          onClose={() => setRenameFlowModal(null)}
          onSubmit={confirmRenameFlow}
          title="Переименовать сценарий"
          placeholder="Введите новое название..."
          defaultValue={renameFlowModal.currentName}
          required={true}
          validation={(value) => {
            if (value.length < 3) return 'Название должно содержать минимум 3 символа';
            if (value.length > 100) return 'Название не должно превышать 100 символов';
            return null;
          }}
        />
      )}

      {switchFlowModal && (
        <ConfirmDialog
          isOpen={!!switchFlowModal}
          onClose={() => setSwitchFlowModal(null)}
          onConfirm={confirmSwitchFlow}
          title="Несохраненные изменения"
          message="⚠️ У вас есть несохраненные изменения. Перейти к другому сценарию?"
          confirmLabel="Перейти"
          cancelLabel="Остаться"
          variant="warning"
        />
      )}

      {/* Save Template Modal - will be a multi-step modal */}
      {saveTemplateModal && (
        <PromptDialog
          isOpen={saveTemplateModal}
          onClose={() => setSaveTemplateModal(false)}
          onSubmit={(name) => handleSaveAsTemplate(name, '')}
          title="Сохранить как шаблон"
          placeholder="Название шаблона..."
          required={true}
          validation={(value) => {
            if (value.length < 3) return 'Название должно содержать минимум 3 символа';
            if (value.length > 100) return 'Название не должно превышать 100 символов';
            return null;
          }}
        />
      )}

      {/* Toast Notifications */}
      <ToastContainer />
    </div>
  );
}

export default App;
