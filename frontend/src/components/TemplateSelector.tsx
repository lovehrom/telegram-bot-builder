import { useState, useEffect, useRef } from 'react';

interface Template {
  id: number;
  name: string;
  description?: string;
  is_system: boolean;
}

interface TemplateSelectorProps {
  onSelect: (templateId: number) => void;
  buttonLabel?: string;
}

export function TemplateSelector({
  onSelect,
  buttonLabel = '📋 Из шаблона'
}: TemplateSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Загрузить шаблоны при открытии dropdown
    if (isOpen && templates.length === 0) {
      setLoading(true);
      setError(null);
      fetch('/api/templates/')
        .then(r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`);
          return r.json();
        })
        .then(data => {
          setTemplates(data);
          setLoading(false);
        })
        .catch(err => {
          console.error('Failed to load templates:', err);
          setError('Не удалось загрузить шаблоны. Попробуйте позже.');
          setLoading(false);
        });
    }
  }, [isOpen, retryCount]);

  useEffect(() => {
    // Закрыть при клике вне
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-medium"
      >
        {buttonLabel}
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-96 overflow-y-auto">
          <div className="p-2">
            {loading ? (
              <div className="text-gray-500 text-center py-4">
                Загрузка шаблонов...
              </div>
            ) : error ? (
              <div className="p-4 text-center">
                <div className="text-red-500 mb-2 text-sm">{error}</div>
                <button
                  onClick={() => setRetryCount(c => c + 1)}
                  className="text-blue-500 underline text-sm hover:text-blue-700"
                >
                  Попробовать снова
                </button>
              </div>
            ) : templates.length === 0 ? (
              <div className="text-gray-500 text-center py-4">
                Нет доступных шаблонов
              </div>
            ) : (
              templates.map(template => (
                <button
                  key={template.id}
                  onClick={() => {
                    onSelect(template.id);
                    setIsOpen(false);
                  }}
                  className="w-full text-left p-3 hover:bg-gray-100 rounded-lg transition group mb-1"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-gray-800 flex items-center gap-2">
                        {template.name}
                        {template.is_system && (
                          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                            Системный
                          </span>
                        )}
                      </div>
                      {template.description && (
                        <div className="text-sm text-gray-500 mt-1">
                          {template.description}
                        </div>
                      )}
                    </div>
                    <span className="text-gray-400 group-hover:text-blue-500 ml-2">→</span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
