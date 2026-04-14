import { Handle, Position, NodeProps } from 'reactflow';
import { Play } from 'lucide-react';

export function StartNode({ data }: NodeProps) {
  return (
    <div className="rounded-lg border-2 border-accent-500 bg-accent-50 px-4 py-2 shadow-md dark:bg-accent-500/10">
      <Handle type="source" position={Position.Bottom} />
      <div className="flex items-center gap-2">
        <div className="rounded bg-accent-500 p-1">
          <Play className="h-4 w-4 text-white" />
        </div>
        <span className="font-semibold text-accent-700 dark:text-accent-300">{data.label}</span>
      </div>
    </div>
  );
}
