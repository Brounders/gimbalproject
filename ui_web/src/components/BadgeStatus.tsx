import { SessionStatus } from './types';
import { cn } from './utils';

interface BadgeStatusProps {
  status: SessionStatus;
}

const labels: Record<SessionStatus, string> = {
  idle: 'Idle',
  running: 'Running',
  recording: 'Recording',
  error: 'Error',
};

const tone: Record<SessionStatus, string> = {
  idle: 'border-[var(--color-border)] text-[var(--color-text-muted)] bg-[color-mix(in_srgb,var(--color-surface-2)_88%,transparent)]',
  running: 'border-[color-mix(in_srgb,var(--color-success)_35%,transparent)] text-[var(--color-success)] bg-[color-mix(in_srgb,var(--color-success)_15%,transparent)]',
  recording: 'border-[color-mix(in_srgb,var(--color-danger)_35%,transparent)] text-[var(--color-danger)] bg-[color-mix(in_srgb,var(--color-danger)_15%,transparent)]',
  error: 'border-[color-mix(in_srgb,var(--color-danger)_40%,transparent)] text-[var(--color-danger)] bg-[color-mix(in_srgb,var(--color-danger)_20%,transparent)]',
};

export function BadgeStatus({ status }: BadgeStatusProps) {
  return (
    <span className={cn('inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.12em]', tone[status])}>
      <span
        className={cn(
          'h-1.5 w-1.5 rounded-full',
          status === 'recording' ? 'animate-pulse bg-[var(--color-danger)]' : 'bg-current',
        )}
      />
      {labels[status]}
    </span>
  );
}
