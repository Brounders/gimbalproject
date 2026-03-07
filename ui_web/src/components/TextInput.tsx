import { InputHTMLAttributes } from 'react';

import { Button } from './Button';
import { cn } from './utils';

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export function TextInput({ label, error, hint, id, className, ...props }: TextInputProps) {
  const fieldId = id || `input-${Math.random().toString(16).slice(2)}`;
  return (
    <div className="space-y-1.5">
      {label ? (
        <label className="block text-xs font-medium text-[var(--color-text-muted)]" htmlFor={fieldId}>
          {label}
        </label>
      ) : null}
      <input
        id={fieldId}
        className={cn(
          'h-11 w-full rounded-xl border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_88%,transparent)] px-3.5 text-sm text-[var(--color-text)]',
          'placeholder:text-[var(--color-text-muted)] outline-none transition-all duration-quick hover:border-[var(--color-border-strong)] hover:bg-[var(--color-hover)]',
          'focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg)]',
          'disabled:cursor-not-allowed disabled:opacity-50',
          error ? 'border-[var(--color-danger)]' : '',
          className,
        )}
        {...props}
      />
      {error ? <p className="text-xs text-[var(--color-danger)]">{error}</p> : null}
      {!error && hint ? <p className="text-xs text-[var(--color-text-muted)]">{hint}</p> : null}
    </div>
  );
}

interface PathInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  onBrowse: () => void;
  browseLabel?: string;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  hint?: string;
}

export function PathInput({
  label,
  value,
  onChange,
  onBrowse,
  browseLabel = 'Выбрать...',
  placeholder,
  disabled,
  error,
  hint,
}: PathInputProps) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-medium text-[var(--color-text-muted)]">{label}</label>
      <div className="grid grid-cols-[1fr_auto] gap-2">
        <TextInput
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          error={error}
          aria-label={label}
        />
        <Button type="button" variant="secondary" onClick={onBrowse} disabled={disabled}>
          {browseLabel}
        </Button>
      </div>
      {error ? <p className="text-xs text-[var(--color-danger)]">{error}</p> : null}
      {!error && hint ? <p className="text-xs text-[var(--color-text-muted)]">{hint}</p> : null}
    </div>
  );
}
