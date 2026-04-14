import { useEffect, useCallback } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  handler: (event: KeyboardEvent) => void;
  description: string;
  enabled?: boolean;
}

export interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[];
  isEnabled?: boolean;
  preventDefault?: boolean;
}

export function useKeyboardShortcuts({
  shortcuts,
  isEnabled = true,
  preventDefault = true,
}: UseKeyboardShortcutsOptions) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!isEnabled) return;

      // Проверка что пользователь не в input/textarea/contenteditable
      const target = event.target as HTMLElement;
      const isInputField =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable;

      // Пропускаем некоторые горячие клавиши даже в input fields
      const allowInInput = ['Escape'].some(key =>
        shortcuts.some(s => s.key.toLowerCase() === key.toLowerCase())
      );

      if (isInputField && !allowInInput) {
        return;
      }

      for (const shortcut of shortcuts) {
        if (shortcut.enabled === false) continue;

        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatch = shortcut.ctrlKey === undefined || event.ctrlKey === shortcut.ctrlKey;
        const shiftMatch = shortcut.shiftKey === undefined || event.shiftKey === shortcut.shiftKey;
        const altMatch = shortcut.altKey === undefined || event.altKey === shortcut.altKey;
        const metaMatch = shortcut.metaKey === undefined || event.metaKey === shortcut.metaKey;

        if (keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch) {
          if (preventDefault) {
            event.preventDefault();
            event.stopPropagation();
          }
          shortcut.handler(event);
          break;
        }
      }
    },
    [shortcuts, isEnabled, preventDefault]
  );

  useEffect(() => {
    if (!isEnabled) return;

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown, isEnabled]);
}

// Предустановленные сокращения для Flow Editor
export function useFlowEditorShortcuts({
  onSave,
  onUndo,
  onRedo,
  onDelete,
  onToggleHelp,
  isEnabled = true,
}: {
  onSave?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onDelete?: () => void;
  onToggleHelp?: () => void;
  isEnabled?: boolean;
}) {
  const shortcuts: KeyboardShortcut[] = [
    {
      key: 's',
      ctrlKey: true,
      handler: onSave || (() => {}),
      description: 'Сохранить изменения',
    },
    {
      key: 'z',
      ctrlKey: true,
      handler: onUndo || (() => {}),
      description: 'Отменить',
    },
    {
      key: 'z',
      ctrlKey: true,
      shiftKey: true,
      handler: onRedo || (() => {}),
      description: 'Повторить',
    },
    {
      key: 'y',
      ctrlKey: true,
      handler: onRedo || (() => {}),
      description: 'Повторить (альтернатива)',
    },
    {
      key: 'Delete',
      handler: onDelete || (() => {}),
      description: 'Удалить выбранный блок',
    },
    {
      key: 'Backspace',
      handler: onDelete || (() => {}),
      description: 'Удалить выбранный блок',
    },
    {
      key: '?',
      shiftKey: true,
      handler: onToggleHelp || (() => {}),
      description: 'Показать справку по горячим клавишам',
    },
    {
      key: '/',
      handler: onToggleHelp || (() => {}),
      description: 'Показать справку по горячим клавишам',
    },
    {
      key: 'Escape',
      handler: onToggleHelp || (() => {}),
      description: 'Закрыть диалог/модалку',
    },
  ];

  useKeyboardShortcuts({ shortcuts, isEnabled });

  return shortcuts;
}

// Константы для отображения горячих клавиш
export const KEY_LABELS: Record<string, string> = {
  Ctrl: '⌃',
  Cmd: '⌘',
  Shift: '⇧',
  Alt: '⌥',
  Delete: '⌫',
  Enter: '↵',
  Escape: 'Esc',
  '?': '?',
  '/': '/',
};

export function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];

  if (shortcut.ctrlKey) parts.push(KEY_LABELS.Ctrl);
  if (shortcut.shiftKey) parts.push(KEY_LABELS.Shift);
  if (shortcut.altKey) parts.push(KEY_LABELS.Alt);
  if (shortcut.metaKey) parts.push(KEY_LABELS.Cmd);

  parts.push(shortcut.key);

  return parts.join(' + ');
}
