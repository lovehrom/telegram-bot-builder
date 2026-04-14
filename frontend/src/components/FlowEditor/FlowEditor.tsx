import { useCallback, useEffect, useMemo, useState, memo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Connection,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useFlowStore } from '@/hooks/useFlowStore';
import { useFlowEditorShortcuts } from '@/hooks/useKeyboardShortcuts';
import { BlockPalette } from './BlockPalette';
import { BlockProperties } from './properties/BlockProperties';
import { EdgeProperties } from './properties/EdgeProperties';
import { StartNode } from './nodes/StartNode';
import { EndNode } from './nodes/EndNode';
import { TextNode } from './nodes/TextNode';
import { VideoNode } from './nodes/VideoNode';
import { ImageNode } from './nodes/ImageNode';
import { DelayNode } from './nodes/DelayNode';
import { ConfirmationNode } from './nodes/ConfirmationNode';
import { CourseMenuNode } from './nodes/CourseMenuNode';
import { QuizNode } from './nodes/QuizNode';
import { DecisionNode } from './nodes/DecisionNode';
import { MenuNode } from './nodes/MenuNode';
import { PaymentGateNode } from './nodes/PaymentGateNode';
import { ActionNode } from './nodes/ActionNode';
import { InputNode } from './nodes/InputNode';
import { RandomNode } from './nodes/RandomNode';
import { FlowEditorTour } from '../onboarding/Tour';
import { KeyboardShortcutsDialog } from '../keyboard/KeyboardShortcuts';
import { Blocks, Settings, X } from 'lucide-react';

const nodeTypes = {
  start: StartNode,
  end: EndNode,
  text: TextNode,
  video: VideoNode,
  image: ImageNode,
  delay: DelayNode,
  confirmation: ConfirmationNode,
  course_menu: CourseMenuNode,
  quiz: QuizNode,
  decision: DecisionNode,
  menu: MenuNode,
  payment_gate: PaymentGateNode,
  action: ActionNode,
  input: InputNode,
  random: RandomNode,
};

interface FlowEditorProps {
  flowId?: number;
}

function FlowEditor({ flowId }: FlowEditorProps) {
  const {
    nodes,
    edges,
    isLoading,
    error,
    selectedNode,
    selectedEdge,
    loadFlow,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    removeNode,
    setSelectedNode,
    setSelectedEdge,
    undo,
    redo,
    canUndo,
    canRedo,
  } = useFlowStore();

  // Tour state
  const [runTour, setRunTour] = useState(false);

  // Keyboard shortcuts dialog state
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false);

  // Mobile panels state
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const [isPropertiesOpen, setIsPropertiesOpen] = useState(false);

  // Load flow on mount and check for tour
  useEffect(() => {
    if (flowId) {
      loadFlow(flowId);
    }

    // Check if user has seen the tour
    const hasSeenTour = localStorage.getItem('flowEditorTourSeen');
    if (!hasSeenTour && flowId) {
      // Show tour after a short delay
      setTimeout(() => {
        setRunTour(true);
      }, 1000);
    }

    // Очистка debounce-таймера истории при unmount
    return () => {
      useFlowStore.getState().cleanup();
    };
  }, [flowId, loadFlow]);

  const handleTourComplete = () => {
    setRunTour(false);
    localStorage.setItem('flowEditorTourSeen', 'true');
  };

  const handleTourSkip = () => {
    setRunTour(false);
    localStorage.setItem('flowEditorTourSeen', 'true');
  };

  const handleNodesChange: OnNodesChange = useCallback(
    (changes) => {
      onNodesChange(changes);
    },
    [onNodesChange]
  );

  const handleEdgesChange: OnEdgesChange = useCallback(
    (changes) => {
      onEdgesChange(changes);
    },
    [onEdgesChange]
  );

  const handleConnect: OnConnect = useCallback(
    (connection: Connection) => {
      onConnect(connection);
    },
    [onConnect]
  );

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node);
    },
    [setSelectedNode]
  );

  const handleDeleteNode = useCallback(() => {
    if (selectedNode) {
      removeNode(selectedNode.id);
      setSelectedNode(null);
    }
  }, [selectedNode, removeNode, setSelectedNode]);

  // Keyboard shortcuts handlers (must be after handleDeleteNode)
  const handleSaveFlow = useCallback(async () => {
    if (!flowId) return;
    // Call the App's handleSaveFlow via window event or direct import
    const event = new CustomEvent('flow-editor-save', { detail: { flowId } });
    window.dispatchEvent(event);
  }, [flowId]);

  const handleUndo = useCallback(() => {
    if (canUndo()) {
      undo();
    }
  }, [undo]); // remove canUndo from deps since it's called inside

  const handleRedo = useCallback(() => {
    if (canRedo()) {
      redo();
    }
  }, [redo]); // remove canRedo from deps since it's called inside

  const handleDelete = useCallback(() => {
    if (selectedNode) {
      handleDeleteNode();
    } else if (selectedEdge) {
      // Удаление edge через store action для корректного undo/redo
      const store = useFlowStore.getState();
      store.removeEdge(selectedEdge.id);
      setSelectedEdge(null);
    }
  }, [selectedNode, selectedEdge, handleDeleteNode, setSelectedEdge]);

  // Memoize keyboard shortcuts config
  const shortcutsConfig = useMemo(() => ({
    onSave: handleSaveFlow,
    onUndo: handleUndo,
    onRedo: handleRedo,
    onDelete: handleDelete,
    onToggleHelp: () => setShowKeyboardShortcuts(true),
    isEnabled: !!flowId,
  }), [handleSaveFlow, handleUndo, handleRedo, handleDelete, flowId]);

  // Keyboard shortcuts hook
  useFlowEditorShortcuts(shortcutsConfig);

  const handleEdgeClick = useCallback(
    (_event: React.MouseEvent, edge: Edge) => {
      setSelectedEdge(edge);
      setSelectedNode(null); // Deselect node when edge is selected
    },
    [setSelectedEdge, setSelectedNode]
  );

  // Add labels to edges based on conditions
  const edgesWithLabels = useMemo(() => {
    return edges.map((edge) => ({
      ...edge,
      label: edge.data?.condition || '',
      labelStyle: { fontSize: 10, fontWeight: 600 },
      labelBgStyle: { fill: '#fff', color: '#000' },
    }));
  }, [edges]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: '#0A0A0A' }}>
        <div className="text-lg" style={{ color: '#A1A1AA' }}>Загрузка...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: '#0A0A0A' }}>
        <div style={{ color: '#FCA5A5' }}>{error}</div>
      </div>
    );
  }

  return (
    <div className="flow-editor-container flex h-full relative">
      {/* Mobile Toggle Buttons */}
      <div className="md:hidden fixed top-20 left-4 z-30 flex flex-col gap-2">
        <button
          onClick={() => setIsPaletteOpen(!isPaletteOpen)}
          className="p-3 bg-brand-500 text-white rounded-lg shadow-lg hover:bg-brand-600 transition-colors"
          aria-label={isPaletteOpen ? 'Закрыть палитру блоков' : 'Открыть палитру блоков'}
          aria-expanded={isPaletteOpen}
        >
          {isPaletteOpen ? <X className="h-5 w-5" /> : <Blocks className="h-5 w-5" />}
        </button>
      </div>

      <div className="md:hidden fixed top-20 right-4 z-30 flex flex-col gap-2">
        {(selectedNode || selectedEdge) && (
          <button
            onClick={() => setIsPropertiesOpen(!isPropertiesOpen)}
            className="p-3 bg-gold-600 text-white rounded-lg shadow-lg hover:bg-gold-700 transition-colors"
            aria-label={isPropertiesOpen ? 'Закрыть панель свойств' : 'Открыть панель свойств'}
            aria-expanded={isPropertiesOpen}
          >
            {isPropertiesOpen ? <X className="h-5 w-5" /> : <Settings className="h-5 w-5" />}
          </button>
        )}
      </div>

      {/* Block Palette - Responsive */}
      <div
        className={`
          block-palette w-64 border-r bg-gray-800 border-gray-700 overflow-y-auto
          fixed md:relative z-20 h-full transition-transform duration-300 ease-in-out
          ${isPaletteOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
        role="complementary"
        aria-label="Палитра блоков"
        aria-describedby="palette-help"
      >
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-white">🧩 Блоки</h2>
            <p id="palette-help" className="text-xs text-gray-400 mt-1">Нажмите чтобы добавить</p>
          </div>
          <button
            onClick={() => setIsPaletteOpen(false)}
            className="md:hidden p-1 hover:bg-gray-700 rounded text-gray-300"
            aria-label="Закрыть палитру"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <BlockPalette onAddNode={addNode} />
      </div>

      {/* Overlay for mobile palette */}
      {isPaletteOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-10"
          onClick={() => setIsPaletteOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Canvas */}
      <div
        className="flex-1 h-full overflow-hidden relative react-flow practice-task"
        style={{ border: '1px solid #27272A', background: '#0A0A0A' }}
        role="main"
        aria-label="Холст редактора сценариев"
        aria-describedby="canvas-help"
      >
        <div className="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur rounded-lg shadow p-3 border border-gray-200 max-w-sm hidden md:block">
          <p id="canvas-help" className="text-xs text-gray-600">
            💡 Кликайте на блоки слева чтобы добавить • Перетащите от одного блока к другому чтобы соединить • Кликните на линию чтобы настроить переход
          </p>
        </div>
        {/* Mobile help text */}
        <div className="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur rounded-lg shadow p-3 border border-gray-200 max-w-sm md:hidden">
          <p className="text-xs text-gray-600">
            💡 Нажмите 🧩 для блоков, ⚙️ для свойств
          </p>
        </div>
        <ReactFlow
          nodes={nodes}
          edges={edgesWithLabels}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={handleConnect}
          onNodeClick={handleNodeClick}
          onEdgeClick={handleEdgeClick}
          nodeTypes={nodeTypes}
          fitView
          aria-label="Диаграмма сценария"
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>

      {/* Properties Panel - Responsive */}
      <div
        className={`
          properties-panel w-80 border-l flex flex-col h-full overflow-hidden
          fixed md:relative right-0 z-20 transition-transform duration-300 ease-in-out
          ${isPropertiesOpen ? 'translate-x-0' : 'translate-x-full md:translate-x-0'}
        `}
        style={{ background: '#111111', borderColor: '#27272A' }}
        role="complementary"
        aria-label="Панель свойств"
        aria-live="polite"
      >
        <div className="p-4 flex justify-between items-center" style={{ borderBottom: '1px solid #27272A' }}>
          <h2 className="text-lg font-semibold" style={{ color: '#FFFFFF' }}>⚙️ Свойства</h2>
          <button
            onClick={() => setIsPropertiesOpen(false)}
            className="md:hidden p-1 rounded"
            style={{ color: '#A1A1AA' }}
            aria-label="Закрыть свойства"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          {selectedEdge ? (
            <EdgeProperties
              edge={selectedEdge}
              onClose={() => {
                setSelectedEdge(null);
                setIsPropertiesOpen(false);
              }}
            />
          ) : selectedNode && selectedNode.data && selectedNode.data.blockType ? (
            <BlockProperties
              node={selectedNode}
              onDelete={handleDeleteNode}
            />
          ) : (
            <div className="flex flex-col h-full items-center justify-center text-gray-400 p-4">
              <h2 className="mb-1 text-lg font-semibold">⚙️ Свойства</h2>
              <p className="text-sm text-center">Выберите блок для редактирования</p>
            </div>
          )}
        </div>
      </div>

      {/* Overlay for mobile properties */}
      {isPropertiesOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-10"
          onClick={() => setIsPropertiesOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Tour */}
      <FlowEditorTour
        run={runTour}
        onComplete={handleTourComplete}
        onSkip={handleTourSkip}
      />

      {/* Keyboard Shortcuts Dialog */}
      <KeyboardShortcutsDialog
        isOpen={showKeyboardShortcuts}
        onClose={() => setShowKeyboardShortcuts(false)}
        shortcuts={[
          {
            key: 's',
            ctrlKey: true,
            handler: handleSaveFlow,
            description: 'Сохранить изменения',
          },
          {
            key: 'z',
            ctrlKey: true,
            handler: handleUndo,
            description: 'Отменить',
          },
          {
            key: 'z',
            ctrlKey: true,
            shiftKey: true,
            handler: handleRedo,
            description: 'Повторить',
          },
          {
            key: 'y',
            ctrlKey: true,
            handler: handleRedo,
            description: 'Повторить (альтернатива)',
          },
          {
            key: 'Delete',
            handler: handleDelete,
            description: 'Удалить выбранное',
          },
          {
            key: 'Backspace',
            handler: handleDelete,
            description: 'Удалить выбранное',
          },
          {
            key: '?',
            shiftKey: true,
            handler: () => setShowKeyboardShortcuts(true),
            description: 'Показать справку',
          },
          {
            key: '/',
            handler: () => setShowKeyboardShortcuts(true),
            description: 'Показать справку',
          },
        ]}
      />
    </div>
  );
}

// Custom comparison function for FlowEditor
const arePropsEqual = (prevProps: FlowEditorProps, nextProps: FlowEditorProps) => {
  return prevProps.flowId === nextProps.flowId;
};

export const FlowEditorMemo = memo(FlowEditor, arePropsEqual);
FlowEditorMemo.displayName = 'FlowEditor';

// Export as both for backward compatibility
export { FlowEditor };
export default FlowEditorMemo;
