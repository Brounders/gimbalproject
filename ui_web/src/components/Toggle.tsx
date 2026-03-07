import { cn } from './utils';

interface ToggleProps {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
  description?: string;
  disabled?: boolean;
}

export function Toggle({ checked, onChange, label, description, disabled }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        'flex w-full items-center justify-between rounded-2xl border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_86%,transparent)] px-3.5 py-3 text-left',
        'transition-all duration-quick hover:-translate-y-0.5 hover:border-[var(--color-border-strong)]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg)]',
        'disabled:cursor-not-allowed disabled:opacity-50',
      )}
    >
      <span>
        <span className="block text-sm font-medium text-[var(--color-text)]">{label}</span>
        {description ? <span className="block text-xs text-[var(--color-text-muted)]">{description}</span> : null}
      </span>
      <span
        className={cn(
          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-quick',
          checked ? 'bg-[linear-gradient(135deg,var(--color-accent),var(--color-accent-2))]' : 'bg-[var(--color-border)]',
        )}
      >
        <span
          className={cn(
            'inline-block h-[18px] w-[18px] transform rounded-full bg-white transition-transform duration-quick',
            checked ? 'translate-x-6' : 'translate-x-1',
          )}
        />
      </span>
    </button>
  );
}
