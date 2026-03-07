export interface StatCardItem {
  key: string;
  label: string;
  value: string;
  hint?: string;
}

interface StatsGridProps {
  items: StatCardItem[];
}

const accentByKey: Record<string, string> = {
  fps: 'from-[var(--color-accent)]/18 to-transparent',
  quality: 'from-[var(--color-accent-2)]/18 to-transparent',
  eval: 'from-[var(--color-warning)]/18 to-transparent',
  state: 'from-[var(--color-success)]/18 to-transparent',
  target: 'from-[var(--color-accent-2)]/14 to-transparent',
  perf: 'from-[var(--color-accent)]/14 to-transparent',
  runtime: 'from-[var(--color-accent-2)]/14 to-transparent',
  source: 'from-[var(--color-warning)]/14 to-transparent',
};

export function StatsGrid({ items }: StatsGridProps) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <article
          key={item.key}
          className={`metric-card relative overflow-hidden rounded-[22px] border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_86%,transparent)] p-4 shadow-[var(--shadow-soft)]`}
        >
          <div className={`absolute inset-0 bg-gradient-to-br ${accentByKey[item.key] || 'from-white/5 to-transparent'} opacity-100`} />
          <div className="relative">
            <div className="mb-6 flex items-start justify-between gap-3">
              <p className="text-xs uppercase tracking-[0.14em] text-[var(--color-text-muted)]">{item.label}</p>
              <span className="rounded-full border border-[var(--color-border)] px-2 py-1 text-[10px] uppercase tracking-[0.16em] text-[var(--color-accent-2)]">
                live
              </span>
            </div>
            <p className="text-[28px] font-semibold leading-none text-[var(--color-text)]">{item.value}</p>
            {item.hint ? <p className="mt-3 text-xs text-[var(--color-text-muted)]">{item.hint}</p> : null}
          </div>
        </article>
      ))}
    </div>
  );
}
