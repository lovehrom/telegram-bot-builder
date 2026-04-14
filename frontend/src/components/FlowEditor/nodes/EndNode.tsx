import { Handle, Position, NodeProps } from 'reactflow';
import { Square } from 'lucide-react';

export function EndNode({ data }: NodeProps) {
  return (
    <div className="rounded-lg border-2 border-brand-700 bg-brand-50 px-4 py-2 shadow-md dark:bg-brand-700/10">
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center gap-2">
        <div className="rounded bg-brand-700 p-1">
          <Square className="h-4 w-4 text-white" />
        </div>
        <span className="font-semibold text-brand-700 dark:text-brand-300">{data.label}</span>
      </div>
    </div>
  );
}
