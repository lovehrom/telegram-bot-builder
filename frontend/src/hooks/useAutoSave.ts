import { useState, useCallback, useRef, useEffect } from 'react';
import { logger } from '@/utils/logger';

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';

export interface UseAutoSaveOptions {
  delay?: number; // задержка в мс перед сохранением (debounce) - опционально для будущего использования
  onSave: () => Promise<void>;
  onError?: (error: Error) => void;
  onSuccess?: () => void;
}

export interface UseAutoSaveReturn {
  saveStatus: SaveStatus;
  lastSavedAt: number | null;
  manualSave: () => Promise<void>;
  discardChanges: () => void;
}

export function useAutoSave({
  delay: _delay, // unused for now, will be used for debounce in future
  onSave,
  onError,
  onSuccess,
}: UseAutoSaveOptions): UseAutoSaveReturn {
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');
  const [lastSavedAt, setLastSavedAt] = useState<number | null>(null);
  const timeoutRef = useRef<number | null>(null);
  const isSavingRef = useRef(false);
  // Ref для хранения таймеров сброса статуса, чтобы чистить при размонтировании
  const resetTimerRef = useRef<number | null>(null);

  const clearPendingSave = useCallback(() => {
    if (timeoutRef.current !== null) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const performSave = useCallback(async () => {
    // Prevent concurrent saves
    if (isSavingRef.current) {
      logger.debug('[useAutoSave] Save already in progress, skipping...');
      return;
    }

    isSavingRef.current = true;
    setSaveStatus('saving');

    try {
      logger.debug('[useAutoSave] Saving...');
      await onSave();

      setSaveStatus('saved');
      setLastSavedAt(Date.now());
      logger.info('[useAutoSave] Saved successfully at:', new Date().toLocaleTimeString());

      if (onSuccess) {
        onSuccess();
      }

      // Сброс статуса через 2 секунды (таймер хранится в ref для очистки при размонтировании)
      if (resetTimerRef.current !== null) clearTimeout(resetTimerRef.current);
      resetTimerRef.current = window.setTimeout(() => {
        if (!isSavingRef.current) {
          setSaveStatus('idle');
        }
      }, 2000);
    } catch (error) {
      console.error('[useAutoSave] Save failed:', error);
      setSaveStatus('error');

      if (onError) {
        onError(error as Error);
      }

      // Сброс статуса через 3 секунды
      if (resetTimerRef.current !== null) clearTimeout(resetTimerRef.current);
      resetTimerRef.current = window.setTimeout(() => {
        if (!isSavingRef.current) {
          setSaveStatus('idle');
        }
      }, 3000);
    } finally {
      isSavingRef.current = false;
    }
  }, [onSave, onError, onSuccess]);

  const manualSave = useCallback(async () => {
    clearPendingSave();
    await performSave();
  }, [performSave, clearPendingSave]);

  const discardChanges = useCallback(() => {
    clearPendingSave();
    setSaveStatus('idle');
    logger.debug('[useAutoSave] Changes discarded');
  }, [clearPendingSave]);

  // Cleanup on unmount — чистим все таймеры
  useEffect(() => {
    return () => {
      clearPendingSave();
      if (resetTimerRef.current !== null) {
        clearTimeout(resetTimerRef.current);
        resetTimerRef.current = null;
      }
    };
  }, [clearPendingSave]);

  return {
    saveStatus,
    lastSavedAt,
    manualSave,
    discardChanges,
  };
}
