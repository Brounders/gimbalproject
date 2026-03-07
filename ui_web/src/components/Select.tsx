import { SelectHTMLAttributes } from 'react';

import { cn } from './utils';

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: SelectOption[];
  error?: string;
  hint?: string;
}

export function Select({ label, options, className, error, hint, id, ...props }: SelectProps) {
  const fieldId = id || `select-${Math.random().toString(16).slice(2)}`;
  return (
    <div className="space-y-1.5">
      {label ? (
        <label className="block text-xs font-medium text-[var(--color-text-muted)]" htmlFor={fieldId}>
          {label}
        </label>
      ) : null}
      <select
        id={fieldId}
        className={cn(
          'h-11 w-full rounded-xl border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_88%,transparent)] px-3.5 text-sm text-[var(--color-text)]',
          'outline-none transition-all duration-quick hover:border-[var(--color-border-strong)] hover:bg-[var(--color-hover)]',
          'focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg)]',
          'disabled:cursor-not-allowed disabled:opacity-50',
          className,
        )}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? <p className="text-xs text-[var(--color-danger)]">{error}</p> : null}
      {!error && hint ? <p className="text-xs text-[var(--color-text-muted)]">{hint}</p> : null}
    </div>
  );
}
