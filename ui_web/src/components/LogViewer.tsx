import { useEffect, useMemo, useRef, useState } from 'react';

import { Button } from './Button';
import { LogEntry, LogLevel } from './types';

interface LogViewerProps {
  logs: LogEntry[];
}

const levels: Array<LogLevel | 'all'> = ['all', 'debug', 'info', 'warn', 'error'];

export function LogViewer({ logs }: LogViewerProps) {
  const [filter, setFilter] = useState<LogLevel | 'all'>('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const viewportRef = useRef<HTMLDivElement | null>(null);

  const visibleLogs = useMemo(() => {
    if (filter === 'all') return logs;
    return logs.filter((log) => log.level === filter);
  }, [filter, logs]);

  useEffect(() => {
    if (!autoScroll || !viewportRef.current) return;
    viewportRef.current.scrollTop = viewportRef.current.scrollHeight;
  }, [visibleLogs, autoScroll]);

  const onCopy = async () => {
    const content = visibleLogs.map((log) => `[${log.ts}] [${log.level.toUpperCase()}] ${log.message}`).join('\n');
    await navigator.clipboard.writeText(content);
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1 rounded-full border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_82%,transparent)] p-1">
          {levels.map((level) => {
            const active = level === filter;
            return (
              <button
                key={level}
                type="button"
                onClick={() => setFilter(level)}
                className={`rounded px-2.5 py-1 text-xs font-medium transition-colors duration-quick ${
                  active
                    ? 'rounded-full bg-[linear-gradient(135deg,color-mix(in_srgb,var(--color-accent)_18%,var(--color-surface)),var(--color-surface))] text-[var(--color-text)]'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
                }`}
              >
                {level.toUpperCase()}
              </button>
            );
          })}
        </div>
        <div className="flex items-center gap-2">
          <label className="inline-flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(event) => setAutoScroll(event.target.checked)}
              className="h-4 w-4 rounded border-[var(--color-border)] bg-[var(--color-surface-2)]"
            />
            Автоскролл
          </label>
          <Button size="sm" variant="secondary" onClick={onCopy}>
            Копировать
          </Button>
        </div>
      </div>
      <div
        ref={viewportRef}
        className="max-h-[320px] overflow-auto rounded-[22px] border border-[var(--color-border)] bg-[linear-gradient(180deg,color-mix(in_srgb,var(--color-surface-2)_92%,transparent),color-mix(in_srgb,var(--color-surface)_92%,transparent))] p-4 font-mono text-xs leading-relaxed"
      >
        {visibleLogs.length === 0 ? (
          <p className="text-[var(--color-text-muted)]">Пока нет записей для выбранного фильтра.</p>
        ) : (
          visibleLogs.map((log) => (
            <p key={log.id} className="mb-2 whitespace-pre-wrap break-words rounded-xl border border-transparent px-2 py-1 text-[var(--color-text)] hover:border-[var(--color-border)]">
              <span className="text-[var(--color-text-muted)]">[{log.ts}]</span>{' '}
              <span
                className={
                  log.level === 'error'
                    ? 'text-[var(--color-danger)]'
                    : log.level === 'warn'
                    ? 'text-[var(--color-warning)]'
                    : log.level === 'debug'
                    ? 'text-[var(--color-text-muted)]'
                    : 'text-[var(--color-success)]'
                }
              >
                [{log.level.toUpperCase()}]
              </span>{' '}
              {log.message}
            </p>
          ))
        )}
      </div>
    </div>
  );
}
