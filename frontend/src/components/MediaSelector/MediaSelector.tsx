import { useState, useEffect } from 'react';

interface MediaItem {
  id: number;
  file_id: string;
  file_type: string;
  file_name: string | null;
  description: string | null;
  uploaded_at: string;
}

interface MediaSelectorProps {
  fileType: 'photo' | 'video';
  value: string;
  onChange: (fileId: string) => void;
  className?: string;
}

export default function MediaSelector({ fileType, value, onChange, className = '' }: MediaSelectorProps) {
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMedia();
  }, [fileType]);

  const loadMedia = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/media?type=${fileType}`);
      if (!response.ok) {
        throw new Error('Failed to load media');
      }
      const data = await response.json();
      setMedia(data);
    } catch (err) {
      setError('Не удалось загрузить список файлов');
      console.error('Failed to load media:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`media-selector ${className}`}>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        Выберите {fileType === 'photo' ? 'фото' : 'видео'}
      </label>

      {loading && (
        <div className="text-sm text-gray-500">Загрузка...</div>
      )}

      {error && (
        <div className="text-sm text-red-500 mb-2">{error}</div>
      )}

      {!loading && (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        >
          <option value="">-- Выберите файл --</option>
          {media.map((item) => (
            <option key={item.id} value={item.file_id}>
              {item.file_name || item.description || `${item.file_type} #${item.id}`}
            </option>
          ))}
        </select>
      )}

      {value && (
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Выбран: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">{value.substring(0, 30)}...</code>
        </div>
      )}

      <div className="mt-2">
        <button
          type="button"
          onClick={loadMedia}
          className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          🔄 Обновить список
        </button>
        <span className="mx-2 text-gray-300">|</span>
        <a
          href="/admin/tables/media-library"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          ➕ Добавить файл
        </a>
      </div>
    </div>
  );
}
