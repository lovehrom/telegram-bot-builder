import { Handle, Position, NodeProps } from 'reactflow';
import { Image } from 'lucide-react';

export function ImageNode({ data }: NodeProps) {
  return (
    <div className="w-48 rounded-lg border-2 border-brand-500 bg-brand-50 px-4 py-3 shadow-md dark:bg-brand-500/10">
      <Handle type="target" position={Position.Top} />
      <div className="mb-2 flex items-center gap-2">
        <div className="rounded bg-brand-500 p-1">
          <Image className="h-3 w-3 text-white" />
        </div>
        <span className="text-sm font-semibold text-brand-700 dark:text-brand-300">{data.label}</span>
      </div>
      <p className="truncate text-xs text-gray-600 dark:text-gray-400">
        {data.config?.caption || 'Отправить фото пользователю'}
      </p>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
