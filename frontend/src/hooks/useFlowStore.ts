import { create } from 'zustand';
import { Connection, Edge, Node } from 'reactflow';
import type { ConversationFlow, FlowBlock } from '@/types/flow';
import { flowApi } from '@/services/api';
import { validateBlockConfig } from '@/services/validation';

// History state interface
interface HistoryState {
  past: Array<{ nodes: Node[]; edges: Edge[] }>;
  future: Array<{ nodes: Node[]; edges: Edge[] }>;
}

interface FlowState {
  currentFlow: ConversationFlow | null;
  nodes: Node[];
  edges: Edge[];
  isLoading: boolean;
  error: string | null;
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  lastSavedAt: number | null;
  hasUnsavedChanges: boolean;
  // Dirty tracking - только изменённые элементы
  dirtyNodes: Set<string>;
  dirtyEdges: Set<string>;
  // Undo/Redo history
  history: HistoryState;

  setCurrentFlow: (flow: ConversationFlow | null) => void;
  loadFlow: (flowId: number) => Promise<void>;
  createFlow: (name: string, description?: string) => Promise<void>;
  saveFlow: () => Promise<void>;
  autoSave: () => Promise<void>;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: any) => void;
  onEdgesChange: (changes: any) => void;
  onConnect: (connection: Connection) => void;
  addNode: (node: Node) => void;
  updateNode: (nodeId: string, data: any) => void;
  removeNode: (nodeId: string) => void;
  setSelectedNode: (node: Node | null) => void;
  setSelectedEdge: (edge: Edge | null) => void;
  updateEdge: (edgeId: string, data: any) => void;
  removeEdge: (edgeId: string) => void;
  setError: (error: string | null) => void;
  // Очистка ресурсов (для useEffect cleanup)
  cleanup: () => void;
  markAsUnsaved: () => void;
  markNodeDirty: (nodeId: string) => void;
  markEdgeDirty: (edgeId: string) => void;
  // Undo/Redo actions
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  addToHistory: () => void;
  _historyTimeout: ReturnType<typeof setTimeout> | null; // Internal ref for debouncing
}

const MAX_HISTORY_SIZE = 50;

export const useFlowStore = create<FlowState>((set, get) => ({
  currentFlow: null,
  nodes: [],
  edges: [],
  isLoading: false,
  error: null,
  selectedNode: null,
  selectedEdge: null,
  lastSavedAt: null,
  hasUnsavedChanges: false,
  dirtyNodes: new Set<string>(),
  dirtyEdges: new Set<string>(),
  history: {
    past: [],
    future: [],
  },
  _historyTimeout: null,

  setCurrentFlow: (flow) => set({
    currentFlow: flow,
    hasUnsavedChanges: false,
    dirtyNodes: new Set(),
    dirtyEdges: new Set(),
    history: { past: [], future: [] },
    _historyTimeout: null
  }),

  // Add current state to history with debouncing
  addToHistory: () => {
    const state = get();

    // Clear existing timeout
    if (state._historyTimeout) {
      clearTimeout(state._historyTimeout);
    }

    // Set new timeout
    const timeoutId = setTimeout(() => {
      const { nodes, edges, history } = get();
      const newPast = [...history.past, { nodes, edges }];

      // Limit history size
      const limitedPast = newPast.slice(-MAX_HISTORY_SIZE);

      set({
        history: {
          past: limitedPast,
          future: [], // Clear future when adding new state
        },
        _historyTimeout: null
      });
    }, 300); // Debounce for 300ms

    set({ _historyTimeout: timeoutId });
  },

  // Undo last action
  undo: () => {
    const { nodes, edges, history } = get();
    if (history.past.length === 0) return;

    const previousState = history.past[history.past.length - 1];
    const newPast = history.past.slice(0, -1);
    const newFuture = [...history.future, { nodes, edges }];

    set({
      nodes: previousState.nodes,
      edges: previousState.edges,
      history: {
        past: newPast,
        future: newFuture,
      },
      hasUnsavedChanges: true,
    });
  },

  // Redo next action
  redo: () => {
    const { nodes, edges, history } = get();
    if (history.future.length === 0) return;

    const nextState = history.future[history.future.length - 1];
    const newFuture = history.future.slice(0, -1);
    const newPast = [...history.past, { nodes, edges }];

    set({
      nodes: nextState.nodes,
      edges: nextState.edges,
      history: {
        past: newPast,
        future: newFuture,
      },
      hasUnsavedChanges: true,
    });
  },

  // Check if undo is available
  canUndo: () => {
    return get().history.past.length > 0;
  },

  // Check if redo is available
  canRedo: () => {
    return get().history.future.length > 0;
  },

  markNodeDirty: (nodeId) => {
    const { dirtyNodes } = get();
    if (!dirtyNodes.has(nodeId)) {
      set({ dirtyNodes: new Set(dirtyNodes).add(nodeId), hasUnsavedChanges: true });
    }
  },

  markEdgeDirty: (edgeId) => {
    const { dirtyEdges } = get();
    if (!dirtyEdges.has(edgeId)) {
      set({ dirtyEdges: new Set(dirtyEdges).add(edgeId), hasUnsavedChanges: true });
    }
  },

  loadFlow: async (flowId: number) => {
    set({ isLoading: true, error: null });
    try {
      const flow = await flowApi.getFlow(flowId);
      const nodes = flow.blocks?.map((block) => ({
        id: block.id.toString(),
        type: block.block_type,
        position: {
          x: block.position_x || 0,
          y: block.position_y || 0,
        },
        data: {
          id: block.id,
          label: block.label,
          config: block.config,
          blockType: block.block_type,
        },
      })) || [];

      const edges = flow.connections?.map((conn) => ({
        id: conn.id.toString(),
        source: conn.from_block_id.toString(),
        target: conn.to_block_id.toString(),
        label: conn.condition || undefined,
        data: { condition: conn.condition },
      })) || [];

      set({
        currentFlow: flow,
        nodes,
        edges,
        isLoading: false,
        history: { past: [], future: [] }, // Reset history on load
        _historyTimeout: null
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Не удалось загрузить сценарий. Проверьте подключение к серверу.';
      set({ error: errorMessage, isLoading: false });
      throw error; // Re-throw to allow caller to handle
    }
  },

  createFlow: async (name: string, description?: string) => {
    set({ isLoading: true, error: null });
    try {
      const flow = await flowApi.createFlow({ name, description, is_active: true });
      set({ currentFlow: flow, nodes: [], edges: [], isLoading: false, history: { past: [], future: [] }, dirtyNodes: new Set(), dirtyEdges: new Set(), _historyTimeout: null });
    } catch (error) {
      set({ error: 'Failed to create flow', isLoading: false });
    }
  },

  saveFlow: async () => {
    const { currentFlow, nodes, edges, dirtyNodes, dirtyEdges } = get();
    if (!currentFlow) {
      throw new Error('Сценарий не загружен. Сначала выберите или создайте сценарий.');
    }

    set({ isLoading: true, error: null });
    try {
      // 1. Параллельно: обновляем метаданные flow и получаем существующие соединения
      const [_, existingConnections] = await Promise.all([
        flowApi.updateFlow(currentFlow.id, {
          name: currentFlow.name,
          description: currentFlow.description,
        }),
        dirtyEdges.size > 0 ? flowApi.getConnections(currentFlow.id) : Promise.resolve([]),
      ]);

      // 2. Save ONLY dirty blocks (optimization) — последовательно из-за side effects (set node IDs)
      const nodesToSave = dirtyNodes.size > 0
        ? nodes.filter(n => dirtyNodes.has(n.id))
        : nodes; // Fallback to all nodes if empty (first save)

      for (const node of nodesToSave) {
        const blockData: Partial<FlowBlock> = {
          label: node.data.label,
          config: node.data.config,
          position_x: node.position.x,
          position_y: node.position.y,
        };

        if (typeof node.data.id === 'number') {
          await flowApi.updateBlock(node.data.id, blockData);
        } else {
          const newBlock = await flowApi.createBlock(currentFlow.id, {
            ...blockData,
            block_type: node.data.blockType,
          });
          // Update node ID in memory
          set({
            nodes: get().nodes.map(n =>
              n.id === node.id ? { ...n, data: { ...n.data, id: newBlock.id } } : n
            ),
          });
        }
      }

      // 3. Handle connections (only dirty edges or full sync if needed)
      if (dirtyEdges.size > 0) {
        // Удаляем и создаём соединения параллельно где возможно

        for (const conn of existingConnections) {
          const stillExists = edges.some(
            (e) =>
              Number(e.source) === conn.from_block_id &&
              Number(e.target) === conn.to_block_id
          );

          if (!stillExists) {
            await flowApi.deleteConnection(conn.id);
          }
        }

        // Create new connections
        for (const edge of edges) {
          const alreadyExists = existingConnections.some(
            (c) =>
              c.from_block_id === Number(edge.source) &&
              c.to_block_id === Number(edge.target)
          );

          if (!alreadyExists) {
            await flowApi.createConnection(currentFlow.id, {
              from_block_id: Number(edge.source),
              to_block_id: Number(edge.target),
              condition: edge.data?.condition || null,
            });
          }
        }
      }

      set({
        isLoading: false,
        lastSavedAt: Date.now(),
        hasUnsavedChanges: false,
        dirtyNodes: new Set(),
        dirtyEdges: new Set()
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Не удалось сохранить сценарий. Проверьте подключение к серверу.';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  autoSave: async () => {
    // Auto-save is the same as saveFlow but with auto-save specific behavior
    const { currentFlow } = get();
    if (!currentFlow || !get().hasUnsavedChanges) {
      return;
    }

    // Call saveFlow
    await get().saveFlow();
  },

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  onNodesChange: (changes) => {
    const hasSignificantChange = changes.some((change: any) =>
      change.type === 'position' || change.type === 'remove'
    );

    if (hasSignificantChange) {
      get().addToHistory();
    }

    changes.forEach((change: any) => {
      // Mark node as dirty when it changes (except selection changes)
      if (change.type === 'position' || change.type === 'remove') {
        get().markNodeDirty(change.id);
      }
    });

    set({
      nodes: changes.reduce((acc: Node[], change: any) => {
        const node = acc.find((n) => n.id === change.id);
        if (!node) return acc;

        const index = acc.indexOf(node);
        const newNode = { ...node };

        switch (change.type) {
          case 'position':
            newNode.position = change.position || newNode.position;
            break;
          case 'select':
            newNode.selected = change.selected;
            break;
          case 'remove':
            return acc.filter((n) => n.id !== change.id);
          default:
            return acc;
        }

        const newAcc = [...acc];
        newAcc[index] = newNode;
        return newAcc;
      }, get().nodes),
      hasUnsavedChanges: true,
    });
  },

  onEdgesChange: (changes) => {
    changes.forEach((change: any) => {
      // Mark edge as dirty when it changes (except selection changes)
      if (change.type === 'remove') {
        get().markEdgeDirty(change.id);
      }
    });

    set({
      edges: changes.reduce((acc: Edge[], change: any) => {
        if (change.type === 'remove') {
          return acc.filter((e) => e.id !== change.id);
        }
        if (change.type === 'select' || change.type === 'focus') {
          const edge = acc.find((e) => e.id === change.id);
          if (!edge) return acc;
          const index = acc.indexOf(edge);
          const newEdge = { ...edge, ...change };
          const newAcc = [...acc];
          newAcc[index] = newEdge;
          return newAcc;
        }
        return acc;
      }, get().edges),
      hasUnsavedChanges: true,
    });
  },

  onConnect: (connection) => {
    get().addToHistory();
    const edge: Edge = {
      id: `edge-${Date.now()}`,
      source: connection.source || '',
      target: connection.target || '',
      sourceHandle: connection.sourceHandle ?? undefined,
      targetHandle: connection.targetHandle ?? undefined,
    };
    get().markEdgeDirty(edge.id);
    set({ edges: [...get().edges, edge], hasUnsavedChanges: true });
  },

  addNode: (node) => {
    get().addToHistory();
    get().markNodeDirty(node.id);
    set({ nodes: [...get().nodes, node], hasUnsavedChanges: true });
  },

  updateNode: (nodeId, data) => {
    get().addToHistory();
    get().markNodeDirty(nodeId);
    set({
      nodes: get().nodes.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
      ),
      hasUnsavedChanges: true,
    });
  },

  removeNode: (nodeId) => {
    get().addToHistory();
    const newDirtyNodes = new Set(get().dirtyNodes);
    newDirtyNodes.add(nodeId);
    set({
      nodes: get().nodes.filter((node) => node.id !== nodeId),
      edges: get().edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId),
      hasUnsavedChanges: true,
      dirtyNodes: newDirtyNodes,
    });
  },

  setSelectedNode: (node) => set({ selectedNode: node }),

  setSelectedEdge: (edge) => set({ selectedEdge: edge }),

  updateEdge: (edgeId, data) => {
    get().addToHistory();
    get().markEdgeDirty(edgeId);
    set({
      edges: get().edges.map((edge) =>
        edge.id === edgeId ? { ...edge, data: { ...edge.data, ...data } } : edge
      ),
    });
  },

  removeEdge: (edgeId) => {
    get().addToHistory();
    get().markEdgeDirty(edgeId);
    set({
      edges: get().edges.filter((edge) => edge.id !== edgeId),
      hasUnsavedChanges: true,
    });
  },

  markAsUnsaved: () => {
    set({ hasUnsavedChanges: true });
  },

  // Очистка debounce-таймера истории (для вызова в useEffect cleanup)
  cleanup: () => {
    const { _historyTimeout } = get();
    if (_historyTimeout) {
      clearTimeout(_historyTimeout);
      set({ _historyTimeout: null });
    }
  },
  setError: (error) => set({ error }),
}));
