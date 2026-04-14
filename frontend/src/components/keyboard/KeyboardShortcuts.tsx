import { X, Keyboard } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { KeyboardShortcut, formatShortcut } from '@/hooks/useKeyboardShortcuts';

interface KeyboardShortcutsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  shortcuts: KeyboardShortcut[];
  title?: string;
}

export function KeyboardShortcutsDialog({
  isOpen,
  onClose,
  shortcuts,
  title = '⌨️ Горячие клавиши',
}: KeyboardShortcutsDialogProps) {
  // Группировка сокращений по категориям
  const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
    if (shortcut.enabled === false) return acc;

    const key = shortcut.key.toLowerCase();

    // Группировка
    if (key === 's' && shortcut.ctrlKey) {
      acc.file = acc.file || [];
      acc.file.push(shortcut);
    } else if (key === 'z' || key === 'y') {
      acc.edit = acc.edit || [];
      acc.edit.push(shortcut);
    } else if (key === 'delete' || key === 'backspace') {
      acc.edit = acc.edit || [];
      acc.edit.push(shortcut);
    } else if (key === '?' || key === '/' || key === 'escape') {
      acc.help = acc.help || [];
      acc.help.push(shortcut);
    } else {
      acc.other = acc.other || [];
      acc.other.push(shortcut);
    }

    return acc;
  }, {} as Record<string, KeyboardShortcut[]>);

  const categoryTitles: Record<string, string> = {
    file: '💾 Файл',
    edit: '✏️ Редактирование',
    help: '❓ Справка',
    other: '🔧 Другое',
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="md">
      <div className="space-y-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Используйте горячие клавиши для быстрого доступа к функциям редактора:
        </p>

        <div className="space-y-4">
          {Object.entries(groupedShortcuts).map(([category, categoryShortcuts]) => (
            <div key={category}>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                {categoryTitles[category] || category}
              </h3>
              <div className="space-y-2">
                {categoryShortcuts.map((shortcut, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 rounded-lg bg-gray-50 dark:bg-gray-800"
                  >
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {shortcut.description}
                    </span>
                    <kbd className="px-2 py-1 text-xs font-mono bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded shadow-sm">
                      {formatShortcut(shortcut)}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
          <p className="text-xs text-blue-800 dark:text-blue-300">
            <Keyboard className="inline-block h-3 w-3 mr-1" />
            <strong>Подсказка:</strong> Нажмите <kbd className="px-1 py-0.5 text-xs font-mono bg-blue-100 dark:bg-blue-800 rounded">?</kbd> или <kbd className="px-1 py-0.5 text-xs font-mono bg-blue-100 dark:bg-blue-800 rounded">Shift + ?</kbd> чтобы открыть эту справку в любое время.
          </p>
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={onClose}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          <X className="h-4 w-4" />
          Закрыть
        </button>
      </div>
    </Modal>
  );
}

// Floating button для открытия справки
interface KeyboardShortcutButtonProps {
  onClick: () => void;
  showLabel?: boolean;
}

export function KeyboardShortcutButton({ onClick, showLabel = false }: KeyboardShortcutButtonProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors"
      aria-label="Показать горячие клавиши"
      title="Показать горячие клавиши (?)"
    >
      <Keyboard className="h-4 w-4 text-gray-600 dark:text-gray-300" />
      {showLabel && (
        <span className="text-sm text-gray-700 dark:text-gray-300">Горячие клавиши</span>
      )}
      <kbd className="px-1.5 py-0.5 text-xs font-mono bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded">
        ?
      </kbd>
    </button>
  );
}
