const navItems = [
  { label: 'Сессии', caption: 'Mission queue' },
  { label: 'Сценарии', caption: 'Profiles' },
  { label: 'Источники', caption: 'Capture map' },
  { label: 'Логи', caption: 'Diagnostics' },
  { label: 'Настройки', caption: 'System' },
];

interface SidebarProps {
  activeItem: string;
  onSelect: (item: string) => void;
}

export function Sidebar({ activeItem, onSelect }: SidebarProps) {
  return (
    <aside className="hidden w-[292px] shrink-0 px-4 pb-6 pt-4 xl:block">
      <div className="glass-card flex h-full flex-col rounded-[28px] p-4">
        <div className="mb-6 rounded-[24px] border border-[var(--color-border)] bg-[linear-gradient(160deg,color-mix(in_srgb,var(--color-accent)_18%,var(--color-surface-2)),var(--color-surface))] p-4 shadow-[var(--shadow-glow)]">
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-black/20 text-[var(--color-accent-2)]">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 4 4 8.4v7.2L12 20l8-4.4V8.4L12 4Z" stroke="currentColor" strokeWidth="1.6" />
                <path d="M12 4v16M4 8.4 12 13l8-4.6" stroke="currentColor" strokeWidth="1.6" />
              </svg>
            </div>
            <div>
              <p className="hero-kicker">Brounders</p>
              <p className="text-base font-semibold text-[var(--color-text)]">Aerial Console</p>
            </div>
          </div>
          <p className="text-sm text-[var(--color-text-muted)]">
            Интерфейс оператора для запуска сценариев, мониторинга захвата и контроля качества сопровождения.
          </p>
        </div>

        <div className="mb-5">
          <p className="section-label">Navigation</p>
          <nav className="space-y-2">
            {navItems.map((item) => {
              const active = item.label === activeItem;
              return (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => onSelect(item.label)}
                  className={`w-full rounded-2xl border px-3 py-3 text-left transition-all duration-quick ${
                    active
                      ? 'border-[color-mix(in_srgb,var(--color-accent)_44%,transparent)] bg-[linear-gradient(135deg,var(--color-accent-soft),color-mix(in_srgb,var(--color-surface-2)_92%,transparent))] text-[var(--color-text)] shadow-[var(--shadow-soft)]'
                      : 'border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_76%,transparent)] text-[var(--color-text-muted)] hover:-translate-y-0.5 hover:border-[var(--color-border-strong)] hover:text-[var(--color-text)]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium">{item.label}</span>
                    <span className={`h-2.5 w-2.5 rounded-full ${active ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-border-strong)]'}`} />
                  </div>
                  <p className="mt-1 text-xs opacity-80">{item.caption}</p>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="mt-auto space-y-3">
          <p className="section-label">Live bus</p>
          <div className="rounded-[22px] border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_86%,transparent)] p-4">
            <div className="flex items-center justify-between text-sm text-[var(--color-text)]">
              <span>Telemetry uplink</span>
              <span className="rounded-full bg-[var(--color-accent-soft)] px-2 py-1 text-xs text-[var(--color-accent)]">stable</span>
            </div>
            <div className="mt-4 space-y-3 text-sm text-[var(--color-text-muted)]">
              <div className="flex items-center justify-between">
                <span>Capture pipeline</span>
                <span className="text-[var(--color-text)]">ready</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Scenario cache</span>
                <span className="text-[var(--color-text)]">warm</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Operator latency</span>
                <span className="text-[var(--color-text)]">18 ms</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
