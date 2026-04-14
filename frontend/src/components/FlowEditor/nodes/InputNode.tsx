import { Handle, Position, NodeProps } from 'reactflow';
import { Edit3 } from 'lucide-react';

export function InputNode({ data }: NodeProps) {
  const variableName = data.config?.variable_name || 'input';
  const inputType = data.config?.input_type || 'text';

  const typeLabels: Record<string, string> = {
    text: 'Text',
    number: 'Num',
    email: 'Email',
    phone: 'Phone',
  };

  return (
    <div className="w-48 rounded-lg border-2 border-cyan-500 bg-cyan-50 px-4 py-3 shadow-md dark:bg-cyan-500/10">
      <Handle type="target" position={Position.Top} />
      <div className="mb-2 flex items-center gap-2">
        <div className="rounded bg-cyan-500 p-1">
          <Edit3 className="h-3 w-3 text-white" />
        </div>
        <span className="text-sm font-semibold text-cyan-700 dark:text-cyan-300">{data.label}</span>
      </div>
      <p className="truncate text-xs text-gray-600 dark:text-gray-400">
        {typeLabels[inputType]} → {variableName}
      </p>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
