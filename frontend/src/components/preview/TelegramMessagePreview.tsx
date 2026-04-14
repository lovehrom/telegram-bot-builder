import { Bot } from 'lucide-react';

export interface TelegramMessagePreviewProps {
  type: 'text' | 'image' | 'video' | 'menu';
  content: {
    text?: string;
    photoUrl?: string;
    videoUrl?: string;
    caption?: string;
    buttons?: Array<{ label: string; callback_data: string }>;
    parseMode?: 'HTML' | 'Markdown';
  };
  mode?: 'light' | 'dark';
}

export function TelegramMessagePreview({
  type,
  content,
  mode = 'light',
}: TelegramMessagePreviewProps) {
  const isDark = mode === 'dark';

  // Telegram colors
  const bgColor = isDark ? '#1c1c1d' : '#ffffff';
  const textColor = isDark ? '#ffffff' : '#000000';
  const secondaryBgColor = isDark ? '#2b2b2c' : '#f0f0f0';
  const bubbleColor = isDark ? '#2b2b2c' : '#ffffff';

  // Parse HTML/Markdown formatting (simple version)
  const parseText = (text: string, parseMode: 'HTML' | 'Markdown' = 'HTML') => {
    if (!text) return '';

    let parsed = text;

    if (parseMode === 'HTML') {
      parsed = parsed
        .replace(/<b>/g, '<strong>')
        .replace(/<\/b>/g, '</strong>')
        .replace(/<i>/g, '<em>')
        .replace(/<\/i>/g, '</em>')
        .replace(/<u>/g, '<u>')
        .replace(/<\/u>/g, '</u>')
        .replace(/<s>/g, '<s>')
        .replace(/<\/s>/g, '</s>')
        .replace(/<code>/g, '<code style="background: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 3px; font-family: monospace;">')
        .replace(/<\/code>/g, '</code>')
        .replace(/<pre>/g, '<pre style="background: rgba(0,0,0,0.1); padding: 8px; border-radius: 4px; overflow-x: auto;">')
        .replace(/<\/pre>/g, '</pre>');
    } else {
      // Markdown
      parsed = parsed
        .replace(/\*([^*]+)\*/g, '<strong>$1</strong>')
        .replace(/_([^_]+)_/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code style="background: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 3px; font-family: monospace;">$1</code>')
        .replace(/```([\s\S]*?)```/g, '<pre style="background: rgba(0,0,0,0.1); padding: 8px; border-radius: 4px; overflow-x: auto;">$1</pre>');
    }

    return parsed;
  };

  const renderButtons = () => {
    if (!content.buttons || content.buttons.length === 0) return null;

    return (
      <div className="mt-3 flex flex-wrap gap-2">
        {content.buttons.map((button, index) => (
          <button
            key={index}
            className="rounded-lg bg-[#64b5ef] px-4 py-2 text-sm font-medium text-white hover:bg-[#5a9ede] transition-colors"
            style={{ backgroundColor: '#64b5ef' }}
          >
            {button.label}
          </button>
        ))}
      </div>
    );
  };

  return (
    <div
      className="mx-auto max-w-md rounded-lg shadow-lg"
      style={{
        backgroundColor: bgColor,
        color: textColor,
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 border-b p-4" style={{ borderColor: secondaryBgColor }}>
        <div
          className="flex h-10 w-10 items-center justify-center rounded-full bg-[#64b5ef] text-white"
          style={{ backgroundColor: '#64b5ef' }}
        >
          <Bot className="h-5 w-5" />
        </div>
        <div>
          <div className="text-sm font-semibold">Your Bot</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">bot</div>
        </div>
      </div>

      {/* Message Content */}
      <div className="p-4">
        {/* Text/Image/Video */}
        {type === 'text' && content.text && (
          <div
            className="rounded-lg p-3 text-sm shadow-sm"
            style={{ backgroundColor: bubbleColor, border: 'none' }}
            dangerouslySetInnerHTML={{ __html: parseText(content.text, content.parseMode) }}
          />
        )}

        {type === 'image' && (
          <div className="space-y-2">
            {content.photoUrl && (
              <div className="rounded-lg overflow-hidden shadow-sm">
                <img
                  src={content.photoUrl}
                  alt="Preview"
                  className="w-full"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect width="100" height="100" fill="%23ccc"/%3E%3Ctext x="50" y="50" text-anchor="middle" dy=".3em" fill="%23666"%3ENo Image%3C/text%3E%3C/svg%3E';
                  }}
                />
              </div>
            )}
            {content.caption && (
              <div className="text-sm opacity-70" style={{ backgroundColor: bubbleColor }}>
                {content.caption}
              </div>
            )}
          </div>
        )}

        {type === 'video' && (
          <div className="space-y-2">
            <div className="flex aspect-video items-center justify-center rounded-lg bg-gray-200 dark:bg-gray-700">
              <p className="text-sm text-gray-500">🎬 Видео превью недоступно</p>
            </div>
            {content.caption && (
              <div className="text-sm opacity-70" style={{ backgroundColor: bubbleColor }}>
                {content.caption}
              </div>
            )}
          </div>
        )}

        {type === 'menu' && (
          <div className="space-y-2">
            {content.text && (
              <div
                className="rounded-lg p-3 text-sm shadow-sm"
                style={{ backgroundColor: bubbleColor }}
                dangerouslySetInnerHTML={{ __html: parseText(content.text, content.parseMode) }}
              />
            )}
            {renderButtons()}
          </div>
        )}

        {/* Buttons for all types */}
        {type !== 'menu' && renderButtons()}

        {/* Timestamp */}
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
