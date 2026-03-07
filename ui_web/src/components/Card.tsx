import { PropsWithChildren, ReactNode } from 'react';

import { cn } from './utils';

interface CardProps extends PropsWithChildren {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
}

export function Card({ title, subtitle, actions, className, children }: CardProps) {
  return (
    <section
      className={cn(
        'glass-card rounded-[24px] p-5 transition-colors duration-quick',
        className,
      )}
    >
      <header className="mb-5 flex items-start justify-between gap-3">
        <div>
          <p className="section-label">Control block</p>
          <h2 className="text-[var(--font-section)] font-semibold leading-tight text-[var(--color-text)]">{title}</h2>
          {subtitle ? <p className="mt-1 max-w-2xl text-sm text-[var(--color-text-muted)]">{subtitle}</p> : null}
        </div>
        {actions}
      </header>
      {children}
    </section>
  );
}
