import { Button } from './Button';

interface VideoPanelProps {
  isActive: boolean;
  statusText: string;
  sourceLabel: string;
  onRunDemo: () => void;
  onOpenFile: () => void;
}

export function VideoPanel({ isActive, statusText, sourceLabel, onRunDemo, onOpenFile }: VideoPanelProps) {
  if (!isActive) {
    return (
      <div className="relative flex min-h-[430px] flex-col justify-between overflow-hidden rounded-[26px] border border-dashed border-[var(--color-border)] bg-[linear-gradient(180deg,color-mix(in_srgb,var(--color-surface-2)_92%,transparent),color-mix(in_srgb,var(--color-surface)_96%,transparent))] p-6">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(124,232,255,0.1),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(16,163,127,0.1),transparent_28%)]" />
        <div className="relative">
          <p className="hero-kicker">Visual stream</p>
          <h3 className="mt-3 text-[28px] font-semibold leading-tight text-[var(--color-text)]">Видео-сцена пока не активна</h3>
          <p className="mt-3 max-w-xl text-sm text-[var(--color-text-muted)]">
            После запуска сессии здесь появится живой монитор с телеметрией, ретикулой цели и статусом захвата в реальном времени.
          </p>
        </div>

        <div className="relative grid gap-4 lg:grid-cols-[1.4fr_1fr]">
          <div className="rounded-[24px] border border-[var(--color-border)] bg-black/20 p-4">
            <div className="mb-3 flex items-center justify-between text-xs uppercase tracking-[0.16em] text-[var(--color-accent-2)]">
              <span>Ready state</span>
              <span>preview offline</span>
            </div>
            <div className="scan-surface flex min-h-[220px] items-center justify-center rounded-[22px] border border-white/5">
              <div className="reticle opacity-55">
                <span className="reticle-dot" />
              </div>
            </div>
          </div>

          <div className="space-y-3 rounded-[24px] border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_82%,transparent)] p-4">
            <div>
              <p className="section-label">Next steps</p>
              <ol className="space-y-2 text-sm text-[var(--color-text-muted)]">
                <li>1. Выбери сценарий и источник в панели управления.</li>
                <li>2. При необходимости загрузи demo или реальный видеофайл.</li>
                <li>3. Запусти сессию и наблюдай поток захвата.</li>
              </ol>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" onClick={onOpenFile}>
                Открыть файл
              </Button>
              <Button variant="primary" onClick={onRunDemo}>
                Запустить демо
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="scan-surface relative min-h-[430px] rounded-[26px] border border-[var(--color-border)] shadow-[var(--shadow-glow)]">
      <div className="absolute left-5 top-5 flex flex-wrap items-center gap-3">
        <span className="signal-pill text-xs">{statusText}</span>
        <span className="rounded-full border border-white/10 bg-black/35 px-3 py-2 text-xs uppercase tracking-[0.14em] text-white/84">
          {sourceLabel}
        </span>
      </div>

      <div className="absolute right-5 top-5 rounded-[18px] border border-white/10 bg-black/30 px-4 py-3 text-right text-xs text-white/80 backdrop-blur">
        <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--color-accent-2)]">Target lock</p>
        <p className="mt-2 text-lg font-semibold text-white">72%</p>
        <p className="text-white/60">scan to focus</p>
      </div>

      <div className="absolute inset-0 flex items-center justify-center">
        <div className="reticle">
          <span className="reticle-dot" />
        </div>
      </div>

      <div className="absolute bottom-5 left-5 grid gap-3 sm:grid-cols-3">
        <TelemetryPill label="Tracking mode" value="LOCK-FOCUS" />
        <TelemetryPill label="Telemetry" value="uplink stable" />
        <TelemetryPill label="Frame feed" value="active" />
      </div>
    </div>
  );
}

function TelemetryPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[18px] border border-white/10 bg-black/28 px-4 py-3 backdrop-blur">
      <p className="text-[10px] uppercase tracking-[0.16em] text-[var(--color-accent-2)]">{label}</p>
      <p className="mt-2 text-sm font-medium text-white">{value}</p>
    </div>
  );
}
