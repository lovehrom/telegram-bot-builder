import { Handle, Position, NodeProps } from 'reactflow';
import { Shuffle } from 'lucide-react';

export function RandomNode({ data }: NodeProps) {
  const mode = data.config?.mode || 'equal';
  const branches = data.config?.branches || [];
  const weights = data.config?.weights || {};

  const count = mode === 'equal' ? branches.length : Object.keys(weights).length;

  return (
    <div className="w-48 rounded-lg border-2 border-orange-500 bg-orange-50 px-4 py-3 shadow-md dark:bg-orange-500/10">
      <Handle type="target" position={Position.Top} />
      <div className="mb-2 flex items-center gap-2">
        <div className="rounded bg-orange-500 p-1">
          <Shuffle className="h-3 w-3 text-white" />
        </div>
        <span className="text-sm font-semibold text-orange-700 dark:text-orange-300">{data.label}</span>
      </div>
      <p className="truncate text-xs text-gray-600 dark:text-gray-400">
        {mode === 'equal' ? 'Equal' : 'Weighted'} ({count} paths)
      </p>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
