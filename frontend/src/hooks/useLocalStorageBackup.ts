import { useCallback } from 'react';
import { Node, Edge } from 'reactflow';
import { logger } from '@/utils/logger';

export interface LocalStorageBackup {
  flowId: number;
  timestamp: number;
  nodes: Node[];
  edges: Edge[];
}

const STORAGE_KEY_PREFIX = 'flow-backup-';
const BACKUP_INTERVAL = 30000; // 30 seconds

export function useLocalStorageBackup() {
  const saveBackup = useCallback((flowId: number, nodes: Node[], edges: Edge[]) => {
    if (typeof window === 'undefined') return;

    try {
      const backup: LocalStorageBackup = {
        flowId,
        timestamp: Date.now(),
        nodes,
        edges,
      };

      const key = `${STORAGE_KEY_PREFIX}${flowId}`;
      localStorage.setItem(key, JSON.stringify(backup));
      logger.debug('[LocalStorageBackup] Backup saved for flow:', flowId);
    } catch (error) {
      logger.error('[LocalStorageBackup] Failed to save backup:', error);
    }
  }, []);

  const loadBackup = useCallback((flowId: number): LocalStorageBackup | null => {
    if (typeof window === 'undefined') return null;

    try {
      const key = `${STORAGE_KEY_PREFIX}${flowId}`;
      const data = localStorage.getItem(key);

      if (!data) return null;

      const backup: LocalStorageBackup = JSON.parse(data);
      logger.debug('[LocalStorageBackup] Backup loaded for flow:', flowId);

      return backup;
    } catch (error) {
      logger.error('[LocalStorageBackup] Failed to load backup:', error);
      return null;
    }
  }, []);

  const hasBackup = useCallback((flowId: number): boolean => {
    if (typeof window === 'undefined') return false;

    const key = `${STORAGE_KEY_PREFIX}${flowId}`;
    return !!localStorage.getItem(key);
  }, []);

  const getBackupTimestamp = useCallback((flowId: number): number | null => {
    const backup = loadBackup(flowId);
    return backup?.timestamp || null;
  }, [loadBackup]);

  const clearBackup = useCallback((flowId: number) => {
    if (typeof window === 'undefined') return;

    try {
      const key = `${STORAGE_KEY_PREFIX}${flowId}`;
      localStorage.removeItem(key);
      logger.debug('[LocalStorageBackup] Backup cleared for flow:', flowId);
    } catch (error) {
      logger.error('[LocalStorageBackup] Failed to clear backup:', error);
    }
  }, []);

  const clearAllBackups = useCallback(() => {
    if (typeof window === 'undefined') return;

    try {
      const keys = Object.keys(localStorage);
      keys.forEach((key) => {
        if (key.startsWith(STORAGE_KEY_PREFIX)) {
          localStorage.removeItem(key);
        }
      });
      logger.debug('[LocalStorageBackup] All backups cleared');
    } catch (error) {
      logger.error('[LocalStorageBackup] Failed to clear all backups:', error);
    }
  }, []);

  return {
    saveBackup,
    loadBackup,
    hasBackup,
    getBackupTimestamp,
    clearBackup,
    clearAllBackups,
    BACKUP_INTERVAL,
  };
}
