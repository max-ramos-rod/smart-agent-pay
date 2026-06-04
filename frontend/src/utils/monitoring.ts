import * as Sentry from "@sentry/react";

const dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;

export const initMonitoring = () => {
  if (!dsn) return;

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.2,
    replaysOnErrorSampleRate: 1.0,
    replaysSessionSampleRate: 0,
  });
};

export const captureError = (error: unknown, context?: Record<string, unknown>) => {
  if (!dsn) return;
  Sentry.captureException(error, { extra: context });
};
