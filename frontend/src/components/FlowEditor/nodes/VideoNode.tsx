import { Handle, Position, NodeProps } from 'reactflow';
import { Video } from 'lucide-react';

export function VideoNode({ data }: NodeProps) {
  return (
    <div className="w-48 rounded-lg border-2 border-brand-600 bg-brand-100 px-4 py-3 shadow-md dark:bg-brand-600/10">
      <Handle type="target" position={Position.Top} />
      <div className="mb-2 flex items-center gap-2">
        <div className="rounded bg-brand-600 p-1">
          <Video className="h-3 w-3 text-white" />
        </div>
        <span className="text-sm font-semibold text-brand-700 dark:text-brand-200">{data.label}</span>
      </div>
      <p className="truncate text-xs text-gray-600 dark:text-gray-400">
        {data.config?.caption || 'No caption...'}
      </p>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
