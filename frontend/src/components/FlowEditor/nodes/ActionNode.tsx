import { Handle, Position, NodeProps } from 'reactflow';
import { Zap } from 'lucide-react';

export function ActionNode({ data }: NodeProps) {
  const actionType = data.config?.action_type || 'set_variable';
  const variableName = data.config?.variable_name;

  const actionLabels: Record<string, string> = {
    set_variable: 'Set',
    increment: 'Inc',
    decrement: 'Dec',
  };

  return (
    <div className="w-48 rounded-lg border-2 border-purple-500 bg-purple-50 px-4 py-3 shadow-md dark:bg-purple-500/10">
      <Handle type="target" position={Position.Top} />
      <div className="mb-2 flex items-center gap-2">
        <div className="rounded bg-purple-500 p-1">
          <Zap className="h-3 w-3 text-white" />
        </div>
        <span className="text-sm font-semibold text-purple-700 dark:text-purple-300">{data.label}</span>
      </div>
      <p className="truncate text-xs text-gray-600 dark:text-gray-400">
        {actionLabels[actionType]}: {variableName || 'variable'}
      </p>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
