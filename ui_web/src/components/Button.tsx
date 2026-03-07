import { ButtonHTMLAttributes, PropsWithChildren } from 'react';

import { cn } from './utils';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends PropsWithChildren, ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'border-[color-mix(in_srgb,var(--color-accent)_55%,transparent)] bg-[linear-gradient(135deg,var(--color-accent),color-mix(in_srgb,var(--color-accent-2)_38%,var(--color-accent)))] text-[#04110d] shadow-[0_14px_40px_rgba(16,163,127,0.28)] hover:-translate-y-0.5 hover:brightness-110 active:translate-y-0 active:brightness-95 focus-visible:ring-[var(--color-accent)]',
  secondary:
    'border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_88%,transparent)] text-[var(--color-text)] hover:border-[var(--color-border-strong)] hover:bg-[var(--color-hover)] active:bg-[var(--color-active)] focus-visible:ring-[var(--color-accent)]',
  ghost:
    'border-transparent bg-transparent text-[var(--color-text)] hover:bg-[color-mix(in_srgb,var(--color-surface-2)_72%,transparent)] active:bg-[var(--color-active)] focus-visible:ring-[var(--color-accent)]',
  destructive:
    'border-[color-mix(in_srgb,var(--color-danger)_50%,transparent)] bg-[linear-gradient(135deg,var(--color-danger),color-mix(in_srgb,var(--color-danger)_65%,black))] text-white shadow-[0_14px_32px_rgba(239,68,68,0.24)] hover:-translate-y-0.5 hover:brightness-110 active:translate-y-0 active:brightness-95 focus-visible:ring-[var(--color-danger)]',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-9 px-3.5 text-xs',
  md: 'h-11 px-4.5 text-sm',
  lg: 'h-12 px-5.5 text-sm',
};

export function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-xl border font-medium tracking-[0.01em] transition-all duration-quick',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg)]',
        'disabled:cursor-not-allowed disabled:opacity-50',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/35 border-t-white" /> : null}
      {children}
    </button>
  );
}

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  children: React.ReactNode;
}

export function IconButton({ label, className, children, ...props }: IconButtonProps) {
  return (
    <button
      aria-label={label}
      title={label}
      className={cn(
        'inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_84%,transparent)]',
        'text-[var(--color-text-muted)] transition-all duration-quick hover:-translate-y-0.5 hover:border-[var(--color-border-strong)] hover:bg-[var(--color-hover)] hover:text-[var(--color-text)]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg)]',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
