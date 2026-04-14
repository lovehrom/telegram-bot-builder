/**
 * Logger utility with environment-based logging
 * Logs only in development mode
 */

const isDevelopment = import.meta.env.DEV || process.env.NODE_ENV === 'development';

export const logger = {
  log: (...args: any[]) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.log('[Dev]', ...args);
    }
  },
  debug: (...args: any[]) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.debug('[Debug]', ...args);
    }
  },
  error: (...args: any[]) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.error('[Error]', ...args);
    } else {
      // In production, send errors to error tracking service
      // Example: Sentry.captureMessage(args.join(' '));
    }
  },
  warn: (...args: any[]) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.warn('[Warn]', ...args);
    }
  },
  info: (...args: any[]) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.info('[Info]', ...args);
    }
  },
};
