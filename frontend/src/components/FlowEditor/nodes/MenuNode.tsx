import { Handle, Position, NodeProps } from 'reactflow';
import { List } from 'lucide-react';

export function MenuNode({ data }: NodeProps) {
  return (
    <div className="w-48 rounded-lg border-2 border-accent-500 bg-accent-50 px-4 py-3 shadow-md dark:bg-accent-500/10">
      <Handle type="target" position={Position.Top} />
      <div className="mb-2 flex items-center gap-2">
        <div className="rounded bg-accent-500 p-1">
          <List className="h-3 w-3 text-white" />
        </div>
        <span className="text-sm font-semibold text-accent-700 dark:text-accent-300">{data.label}</span>
      </div>
      <p className="truncate text-xs text-gray-600 dark:text-gray-400">
        {data.config?.text || 'No text...'}
      </p>
      <p className="mt-1 text-xs text-gray-500">
        {data.config?.buttons?.length || 0} buttons
      </p>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
