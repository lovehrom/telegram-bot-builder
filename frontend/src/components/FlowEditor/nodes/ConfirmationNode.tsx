import { Handle, Position, NodeProps } from 'reactflow';
import { CheckCircle } from 'lucide-react';

export function ConfirmationNode({ data }: NodeProps) {
  return (
    <div className="w-48 rounded-lg border-2 border-gold-500 bg-gold-50 px-4 py-3 shadow-md dark:bg-gold-500/10">
      <Handle type="target" position={Position.Top} />
      <div className="mb-2 flex items-center gap-2">
        <div className="rounded bg-gold-500 p-1">
          <CheckCircle className="h-3 w-3 text-white" />
        </div>
        <span className="text-sm font-semibold text-gold-700 dark:text-gold-300">{data.label}</span>
      </div>
      <p className="truncate text-xs text-gray-600 dark:text-gray-400">
        {data.config?.text || 'Кнопки Да/Нет'}
      </p>
      <Handle type="source" position={Position.Bottom} id="confirm" />
      <Handle type="source" position={Position.Bottom} id="cancel" />
    </div>
  );
}
