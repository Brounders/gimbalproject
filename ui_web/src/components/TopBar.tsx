import { BadgeStatus } from './BadgeStatus';
import { IconButton } from './Button';
import { SessionStatus } from './types';

interface TopBarProps {
  scenarioLabel: string;
  status: SessionStatus;
  expertMode: boolean;
  onToggleExpert: () => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  isRecording: boolean;
}

export function TopBar({
  scenarioLabel,
  status,
  expertMode,
  onToggleExpert,
  theme,
  onToggleTheme,
  isRecording,
}: TopBarProps) {
  return (
    <header className="sticky top-0 z-30 px-4 pb-3 pt-4 lg:px-6">
      <div className="glass-card rounded-[26px] px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-[var(--color-border)] bg-[linear-gradient(135deg,color-mix(in_srgb,var(--color-accent)_24%,var(--color-surface-2)),color-mix(in_srgb,var(--color-accent-2)_14%,var(--color-surface)))] text-[var(--color-accent-2)] shadow-[var(--shadow-glow)]">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 3 3 8l9 5 9-5-9-5Z" stroke="currentColor" strokeWidth="1.6" />
                <path d="M5 11.5 12 15l7-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                <path d="M8 14.8V18l4 2 4-2v-3.2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <p className="hero-kicker">Mission control</p>
              <h1 className="text-xl font-semibold text-[var(--color-text)]">Система сопровождения БПЛА</h1>
              <p className="text-sm text-[var(--color-text-muted)]">Активный сценарий: {scenarioLabel}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {isRecording ? <span className="signal-pill text-xs">Запись в архив</span> : null}
            {expertMode ? (
              <span className="rounded-full border border-[color-mix(in_srgb,var(--color-accent)_45%,transparent)] bg-[var(--color-accent-soft)] px-3 py-1.5 text-xs font-medium text-[var(--color-accent)]">
                Эксперт
              </span>
            ) : null}
            <BadgeStatus status={status} />
            <button
              type="button"
              onClick={onToggleExpert}
              className="rounded-full border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_84%,transparent)] px-4 py-2 text-xs font-medium text-[var(--color-text)] transition-all duration-quick hover:-translate-y-0.5 hover:border-[var(--color-border-strong)] hover:bg-[var(--color-hover)]"
            >
              {expertMode ? 'Скрыть экспертный слой' : 'Открыть экспертный слой'}
            </button>
            <IconButton label="Сменить тему" onClick={onToggleTheme}>
              {theme === 'dark' ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M12 3v2m0 14v2M5.6 5.6l1.4 1.4m10 10 1.4 1.4M3 12h2m14 0h2M5.6 18.4 7 17m10-10 1.4-1.4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                  <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.6" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z" stroke="currentColor" strokeWidth="1.6" />
                </svg>
              )}
            </IconButton>
            <IconButton label="Системные заметки">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M6 4.8h12A1.2 1.2 0 0 1 19.2 6v12A1.2 1.2 0 0 1 18 19.2H6A1.2 1.2 0 0 1 4.8 18V6A1.2 1.2 0 0 1 6 4.8Z" stroke="currentColor" strokeWidth="1.6" />
                <path d="M8 9h8M8 12.5h8M8 16h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </IconButton>
            <IconButton label="Настройки оператора">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 15.3a3.3 3.3 0 1 0 0-6.6 3.3 3.3 0 0 0 0 6.6Z" stroke="currentColor" strokeWidth="1.6" />
                <path d="m19.4 15-1 1.8 1 1.7-1.8 1-1.7-1H14l-1 1.7h-2l-1-1.7H8.1l-1.7 1-1.8-1 1-1.7-1-1.8-1.8-.9v-2l1.8-.9 1-1.8-1-1.7 1.8-1 1.7 1H10l1-1.7h2l1 1.7h1.9l1.7-1 1.8 1-1 1.7 1 1.8 1.8.9v2l-1.8.9Z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
              </svg>
            </IconButton>
          </div>
        </div>
      </div>
    </header>
  );
}
