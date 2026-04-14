import { Handle, Position, NodeProps } from 'reactflow';
import { GitBranch } from 'lucide-react';

export function DecisionNode({ data }: NodeProps) {
  return (
    <div className="w-48 rounded-lg border-2 border-gold-600 bg-gold-100 px-4 py-3 shadow-md dark:bg-gold-600/10">
      <Handle type="target" position={Position.Top} />
      <div className="mb-2 flex items-center gap-2">
        <div className="rounded bg-gold-600 p-1">
          <GitBranch className="h-3 w-3 text-white" />
        </div>
        <span className="text-sm font-semibold text-gold-700 dark:text-gold-200">{data.label}</span>
      </div>
      <p className="truncate text-xs text-gray-600 dark:text-gray-400">
        {data.config?.variable || 'No variable...'}
      </p>
      <p className="text-xs text-gray-500">
        {data.config?.operator || 'equals'} {data.config?.value || ''}
      </p>
      <Handle type="source" position={Position.Bottom} id="true" />
      <Handle type="source" position={Position.Bottom} id="false" />
    </div>
  );
}
