import { useCallback, useEffect, useMemo, useState } from 'react';

import { Card } from './components/Card';
import { ControlPanel, ControlValues } from './components/ControlPanel';
import { LogViewer } from './components/LogViewer';
import { Sidebar } from './components/Sidebar';
import { StatCardItem, StatsGrid } from './components/StatsGrid';
import { Tabs } from './components/Tabs';
import { ThemeMode, LogEntry, SessionStatus } from './components/types';
import { TopBar } from './components/TopBar';
import { VideoPanel } from './components/VideoPanel';
import { toCssVars } from './theme/tokens';

const STORAGE_KEY = 'uav-tracker-ui-v2';

const defaultValues: ControlValues = {
  scenario: 'night',
  sourceType: 'camera',
  cameraIndex: 0,
  sourcePath: '',
  recordOutput: true,
  outputPath: 'runs/gui_output.mp4',
  preset: 'night',
  modelPath: 'runs/detect/runs/drone_bird_probe_fast/weights/best.pt',
  runtimeMode: 'research',
  device: 'mps',
  imgsz: 640,
  conf: 0.3,
  rescan: 6,
  smallTarget: false,
  adaptiveScan: true,
  lockTracker: true,
  nightDetector: true,
  roiAssist: true,
  showGt: true,
  showTiming: true,
  showTrails: true,
};

const scenarioLabelMap: Record<string, string> = {
  default: 'Дневной (базовый)',
  small_target: 'Малые цели',
  night: 'Ночной режим',
  antiuav_thermal: 'Thermal / Anti-UAV',
  rpi_hailo: 'RPi + Hailo',
  custom: 'Пользовательский',
};

interface Toast {
  id: number;
  tone: 'info' | 'success' | 'warn' | 'error';
  text: string;
}

interface RuntimeMetrics {
  fps: number;
  quality: number;
  evalScore: number;
  target: string;
  performance: string;
  mode: string;
  lockScore: number;
  frameTimeMs: number;
}

export default function App() {
  const [activeSidebar, setActiveSidebar] = useState('Сессии');
  const [theme, setTheme] = useState<ThemeMode>('dark');
  const [expertMode, setExpertMode] = useState(false);
  const [showExpertPrompt, setShowExpertPrompt] = useState(false);
  const [expertPassword, setExpertPassword] = useState('');
  const [activeTab, setActiveTab] = useState<'status' | 'logs'>('status');

  const [values, setValues] = useState<ControlValues>(defaultValues);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>('idle');
  const [evaluating, setEvaluating] = useState(false);
  const [metrics, setMetrics] = useState<RuntimeMetrics>({
    fps: 0,
    quality: 0,
    evalScore: 0,
    target: '-',
    performance: '-',
    mode: '-',
    lockScore: 0,
    frameTimeMs: 0,
  });
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([
    { id: 1, ts: now(), level: 'info', message: 'Интерфейс готов.' },
    { id: 2, ts: now(), level: 'debug', message: 'Подсказка: Space = Старт/Пауза, Esc = Стоп.' },
  ]);

  const isRunning = sessionStatus === 'running' || sessionStatus === 'recording';

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as { theme?: ThemeMode; values?: ControlValues; activeSidebar?: string };
      if (parsed.theme === 'dark' || parsed.theme === 'light') setTheme(parsed.theme);
      if (parsed.values) setValues({ ...defaultValues, ...parsed.values });
      if (parsed.activeSidebar) setActiveSidebar(parsed.activeSidebar);
    } catch {
      // ignore invalid persisted state
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ theme, values, activeSidebar }));
  }, [theme, values, activeSidebar]);

  useEffect(() => {
    const vars = toCssVars(theme);
    const root = document.documentElement;
    Object.entries(vars).forEach(([key, value]) => root.style.setProperty(key, value));
    root.setAttribute('data-theme', theme);
  }, [theme]);

  const errors = useMemo(() => {
    const next: Partial<Record<'sourcePath' | 'outputPath' | 'cameraIndex', string>> = {};
    if (values.sourceType !== 'camera' && !values.sourcePath.trim()) {
      next.sourcePath = 'Укажи путь к видео или папке кадров.';
    }
    if (values.sourceType === 'camera' && (Number.isNaN(values.cameraIndex) || values.cameraIndex < 0)) {
      next.cameraIndex = 'Номер камеры должен быть 0 или больше.';
    }
    if (values.recordOutput && !values.outputPath.trim()) {
      next.outputPath = 'Укажи путь сохранения видео.';
    }
    return next;
  }, [values]);

  const pushToast = useCallback((tone: Toast['tone'], text: string) => {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    setToasts((prev) => [...prev, { id, tone, text }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 2600);
  }, []);

  const pushLog = useCallback((level: LogEntry['level'], message: string) => {
    setLogs((prev) => [...prev, { id: Date.now() + prev.length, ts: now(), level, message }]);
  }, []);

  const updateValues = useCallback((patch: Partial<ControlValues>) => {
    setValues((prev) => ({ ...prev, ...patch }));
  }, []);

  useEffect(() => {
    if (!isRunning) return;
    const timer = window.setInterval(() => {
      setMetrics((prev) => {
        const fpsBase = values.sourceType === 'camera' ? 28 : 36;
        const fps = clamp(fpsBase + jitter(9), 8, 95);
        const quality = clamp((values.imgsz / 640) * 70 + values.conf * 35 + jitter(8), 8, 100);
        const frameTimeMs = clamp(1000 / fps + jitter(1.8), 8, 120);
        const lockScore = clamp(prev.lockScore + jitter(0.06), 0, 1);
        return {
          ...prev,
          fps,
          quality,
          frameTimeMs,
          lockScore,
          target: lockScore > 0.55 ? `ID ${Math.max(1, Math.round(10 + jitter(8)))}` : '-',
          mode: lockScore > 0.55 ? 'LOCK-FOCUS' : 'SCAN',
          performance: frameTimeMs < 20 ? 'Высокая' : frameTimeMs < 35 ? 'Средняя' : 'Низкая',
        };
      });
    }, 900);
    return () => window.clearInterval(timer);
  }, [isRunning, values.sourceType, values.imgsz, values.conf]);

  const runStart = useCallback(() => {
    if (Object.keys(errors).length > 0) {
      pushToast('warn', 'Запуск заблокирован: исправь ошибки в форме.');
      pushLog('warn', 'Запуск отменён: невалидные входные параметры.');
      return;
    }
    const nextStatus: SessionStatus = values.recordOutput ? 'recording' : 'running';
    setSessionStatus(nextStatus);
    setMetrics((prev) => ({ ...prev, target: '-', mode: 'SCAN' }));
    pushToast('success', nextStatus === 'recording' ? 'Сессия запущена с записью.' : 'Сессия запущена.');
    pushLog(
      'info',
      `Старт: scenario=${values.scenario} source=${
        values.sourceType === 'camera' ? `camera:${values.cameraIndex}` : values.sourcePath || '-'
      } device=${values.device} imgsz=${values.imgsz} conf=${values.conf.toFixed(2)}`,
    );
  }, [errors, pushLog, pushToast, values]);

  const runStop = useCallback(() => {
    if (!isRunning && !evaluating) return;
    setSessionStatus('idle');
    setEvaluating(false);
    pushToast('info', 'Сессия остановлена.');
    pushLog('info', 'Остановка выполнена.');
  }, [evaluating, isRunning, pushLog, pushToast]);

  const runEvaluate = useCallback(() => {
    if (isRunning) {
      pushToast('warn', 'Сначала останови активную сессию.');
      return;
    }
    if (Object.keys(errors).length > 0) {
      pushToast('warn', 'Оценка заблокирована: исправь ошибки в форме.');
      return;
    }
    setEvaluating(true);
    pushLog('info', 'Оценка запущена...');

    window.setTimeout(() => {
      setEvaluating(false);
      setMetrics((prev) => ({
        ...prev,
        evalScore: clamp(58 + jitter(35), 0, 100),
        quality: clamp(50 + jitter(30), 0, 100),
      }));
      pushToast('success', 'Оценка завершена. Отчёт сохранён в runs/evaluations.');
      pushLog('info', 'Оценка завершена: отчёт сформирован.');
    }, 1300);
  }, [errors, isRunning, pushLog, pushToast]);

  const onBrowseSource = useCallback(() => {
    pushToast('info', 'В web-версии подключи системный file picker через backend bridge.');
    pushLog('debug', 'Action: browse source');
  }, [pushLog, pushToast]);

  const onBrowseOutput = useCallback(() => {
    pushToast('info', 'Выбери путь сохранения через backend bridge.');
    pushLog('debug', 'Action: browse output');
  }, [pushLog, pushToast]);

  const onBrowseModel = useCallback(() => {
    pushToast('info', 'Выбери .pt/.hef модель через backend bridge.');
    pushLog('debug', 'Action: browse model');
  }, [pushLog, pushToast]);

  const onApplyPreset = useCallback(() => {
    pushToast('success', `Preset ${values.preset} применён.`);
    pushLog('info', `Preset applied: ${values.preset}`);
  }, [pushLog, pushToast, values.preset]);

  const onLoadProfile = useCallback(() => {
    pushToast('info', 'Загрузка профиля: подключи API выбора YAML.');
    pushLog('debug', 'Action: load profile');
  }, [pushLog, pushToast]);

  const onSaveProfile = useCallback(() => {
    pushToast('success', 'Профиль сохранён в local storage (демо).');
    pushLog('info', 'Profile saved (demo storage).');
  }, [pushLog, pushToast]);

  const onRunDemo = useCallback(() => {
    updateValues({
      sourceType: 'video',
      sourcePath: 'test_videos/ir_batch/IR_DRONE_010.mp4',
      scenario: 'night',
    });
    pushLog('info', 'Демо источник установлен: IR_DRONE_010.mp4');
    pushToast('info', 'Демо источник выбран. Нажми Старт.');
  }, [pushLog, pushToast, updateValues]);

  const onToggleExpert = useCallback(() => {
    if (expertMode) {
      setExpertMode(false);
      pushLog('info', 'Экспертный режим скрыт.');
      return;
    }
    setExpertPassword('');
    setShowExpertPrompt(true);
  }, [expertMode, pushLog]);

  const onConfirmExpertPassword = useCallback(() => {
    if (expertPassword !== '0000') {
      pushToast('error', 'Неверный пароль экспертного режима.');
      pushLog('warn', 'Отказ во входе в экспертный режим.');
      return;
    }
    setExpertMode(true);
    setShowExpertPrompt(false);
    pushToast('success', 'Экспертный режим включен.');
    pushLog('info', 'Экспертный режим включен.');
  }, [expertPassword, pushLog, pushToast]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || target?.isContentEditable) return;

      if (event.code === 'Space') {
        event.preventDefault();
        if (isRunning) runStop();
        else runStart();
      }

      if (event.code === 'Escape') {
        if (isRunning || evaluating) {
          event.preventDefault();
          runStop();
        }
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [evaluating, isRunning, runStart, runStop]);

  const statsItems = useMemo<StatCardItem[]>(
    () => [
      {
        key: 'fps',
        label: 'FPS',
        value: isRunning ? metrics.fps.toFixed(1) : '-',
        hint: `Frame ${metrics.frameTimeMs.toFixed(1)} ms`,
      },
      {
        key: 'quality',
        label: 'Качество',
        value: isRunning || evaluating ? `${metrics.quality.toFixed(0)}%` : '-',
        hint: `Lock score ${metrics.lockScore.toFixed(2)}`,
      },
      {
        key: 'eval',
        label: 'Оценка',
        value: metrics.evalScore > 0 ? `${metrics.evalScore.toFixed(0)}%` : '-',
        hint: evaluating ? 'Выполняется...' : 'Последний отчёт',
      },
      {
        key: 'state',
        label: 'Состояние',
        value: evaluating ? 'Оценка' : statusRu(sessionStatus),
        hint: `Режим ${metrics.mode}`,
      },
      {
        key: 'target',
        label: 'Цель',
        value: metrics.target,
        hint: isRunning ? 'ID lock/active' : 'Нет цели',
      },
      {
        key: 'perf',
        label: 'Производительность',
        value: isRunning ? metrics.performance : '-',
        hint: `Device ${values.device}`,
      },
      {
        key: 'runtime',
        label: 'Runtime mode',
        value: values.runtimeMode,
        hint: `imgsz ${values.imgsz} / conf ${values.conf.toFixed(2)}`,
      },
      {
        key: 'source',
        label: 'Источник',
        value: values.sourceType === 'camera' ? `Камера ${values.cameraIndex}` : values.sourceType,
        hint: values.sourceType === 'camera' ? 'Live capture' : trimText(values.sourcePath, 38),
      },
    ],
    [evaluating, isRunning, metrics, sessionStatus, values],
  );

  const sourceSummary = values.sourceType === 'camera' ? `Камера ${values.cameraIndex}` : trimText(values.sourcePath, 42);
  const heroState = evaluating ? 'Оценка' : statusRu(sessionStatus);
  const validationState = Object.keys(errors).length > 0 ? 'Нужна проверка' : 'Готово к запуску';

  return (
    <div className="app-shell min-h-screen bg-[var(--color-bg)] text-[var(--color-text)]">
      <div className="flex min-h-screen">
        <Sidebar activeItem={activeSidebar} onSelect={setActiveSidebar} />

        <div className="min-w-0 flex-1">
          <TopBar
            scenarioLabel={scenarioLabelMap[values.scenario] || values.scenario}
            status={sessionStatus}
            expertMode={expertMode}
            onToggleExpert={onToggleExpert}
            theme={theme}
            onToggleTheme={toggleTheme}
            isRecording={sessionStatus === 'recording'}
          />

          <main className="space-y-5 px-4 pb-6 lg:px-6">
            <section className="glass-card hero-panel rounded-[30px] p-5 lg:p-6">
              <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_420px]">
                <div className="relative">
                  <p className="hero-kicker">Aerial tracking command center</p>
                  <h2 className="mt-3 max-w-3xl text-3xl font-semibold leading-tight text-[var(--color-text)] lg:text-4xl">
                    Современная операторская консоль для сопровождения БПЛА, оценки захвата и запуска сценариев в одном окне.
                  </h2>
                  <p className="mt-4 max-w-2xl text-sm text-[var(--color-text-muted)] lg:text-base">
                    Интерфейс собран как единая mission-control сцена: крупный статус, ясные сигналы, быстрые сценарные действия и
                    читаемая телеметрия без визуального шума.
                  </p>

                  <div className="mt-5 flex flex-wrap gap-2">
                    <span className="hero-chip">{scenarioLabelMap[values.scenario] || values.scenario}</span>
                    <span className="hero-chip">{sourceSummary || 'Источник не выбран'}</span>
                    <span className="hero-chip">{values.runtimeMode} / {values.device}</span>
                    <span className="hero-chip">{validationState}</span>
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <HeroMetric label="Состояние" value={heroState} hint={`Sidebar: ${activeSidebar}`} />
                  <HeroMetric label="FPS" value={isRunning ? metrics.fps.toFixed(1) : '-'} hint={`${metrics.frameTimeMs.toFixed(1)} ms/frame`} />
                  <HeroMetric
                    label="Качество"
                    value={isRunning || evaluating ? `${metrics.quality.toFixed(0)}%` : '-'}
                    hint={`Lock ${metrics.lockScore.toFixed(2)}`}
                  />
                  <HeroMetric label="Источник" value={values.sourceType === 'camera' ? `CAM ${values.cameraIndex}` : values.sourceType.toUpperCase()} hint={trimText(values.outputPath, 28)} />
                </div>
              </div>
            </section>

            <div className="grid gap-5 xl:grid-cols-[390px_minmax(0,1fr)]">
              <Card
                title="Панель управления"
                subtitle="Подготовка миссии, запуск и экспертные параметры сопровождения."
                className="order-2 xl:order-1"
              >
                <ControlPanel
                  values={values}
                  errors={errors}
                  expertEnabled={expertMode}
                  running={isRunning}
                  evaluating={evaluating}
                  onChange={updateValues}
                  onBrowseSource={onBrowseSource}
                  onBrowseOutput={onBrowseOutput}
                  onBrowseModel={onBrowseModel}
                  onApplyPreset={onApplyPreset}
                  onLoadProfile={onLoadProfile}
                  onSaveProfile={onSaveProfile}
                  onEvaluate={runEvaluate}
                  onStart={runStart}
                  onStop={runStop}
                />
              </Card>

              <Card
                title="Видео и телеметрия"
                subtitle="Живая сцена захвата с акцентом на статус потока и ритм отслеживания."
                className="order-1 xl:order-2"
              >
                <VideoPanel
                  isActive={isRunning}
                  statusText={sessionStatus === 'recording' ? 'RECORDING' : 'RUNNING'}
                  sourceLabel={values.sourceType === 'camera' ? `CAM ${values.cameraIndex}` : values.sourceType.toUpperCase()}
                  onRunDemo={onRunDemo}
                  onOpenFile={onBrowseSource}
                />
              </Card>
            </div>

            <Card
              title="Статус и журнал"
              subtitle="Ключевые метрики, диагностические сообщения и история событий в одном пространстве."
            >
              <Tabs
                activeTab={activeTab}
                onChange={(id) => setActiveTab(id as 'status' | 'logs')}
                tabs={[
                  {
                    id: 'status',
                    label: 'Статус',
                    content: <StatsGrid items={statsItems} />,
                  },
                  {
                    id: 'logs',
                    label: 'Журнал',
                    content: <LogViewer logs={logs} />,
                  },
                ]}
              />
            </Card>
          </main>
        </div>
      </div>

      {showExpertPrompt ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-4">
          <div className="w-full max-w-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-card">
            <h3 className="text-base font-semibold">Режим эксперта</h3>
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">Введите пароль для доступа к тонким настройкам.</p>
            <input
              autoFocus
              type="password"
              value={expertPassword}
              onChange={(event) => setExpertPassword(event.target.value)}
              className="mt-3 h-10 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 text-sm"
              placeholder="Пароль"
              onKeyDown={(event) => {
                if (event.key === 'Enter') onConfirmExpertPassword();
              }}
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowExpertPrompt(false)}
                className="rounded-md px-3 py-2 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
              >
                Отмена
              </button>
              <button
                type="button"
                onClick={onConfirmExpertPassword}
                className="rounded-md bg-[var(--color-accent)] px-3 py-2 text-sm font-medium text-white"
              >
                Подтвердить
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-[min(360px,calc(100%-2rem))] flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`toast pointer-events-auto rounded-md border px-3 py-2 text-sm shadow-card ${toastClassByTone(toast.tone)}`}
          >
            {toast.text}
          </div>
        ))}
      </div>
    </div>
  );
}

function now(): string {
  return new Date().toLocaleTimeString('ru-RU', { hour12: false });
}

function jitter(range: number): number {
  return (Math.random() * 2 - 1) * range;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function statusRu(status: SessionStatus): string {
  if (status === 'running') return 'В работе';
  if (status === 'recording') return 'Запись';
  if (status === 'error') return 'Ошибка';
  return 'Ожидание';
}

function trimText(text: string, limit: number): string {
  if (!text) return '-';
  return text.length > limit ? `${text.slice(0, limit)}...` : text;
}

function toastClassByTone(tone: Toast['tone']): string {
  if (tone === 'success') return 'border-[color-mix(in_srgb,var(--color-success)_35%,var(--color-border))] bg-[var(--color-surface)] text-[var(--color-text)]';
  if (tone === 'warn') return 'border-[color-mix(in_srgb,var(--color-warning)_45%,var(--color-border))] bg-[var(--color-surface)] text-[var(--color-text)]';
  if (tone === 'error') return 'border-[color-mix(in_srgb,var(--color-danger)_45%,var(--color-border))] bg-[var(--color-surface)] text-[var(--color-text)]';
  return 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]';
}

function HeroMetric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <article className="glass-card hero-metric rounded-[24px] p-4">
      <p className="text-[10px] uppercase tracking-[0.16em] text-[var(--color-accent-2)]">{label}</p>
      <p className="mt-4 text-[30px] font-semibold leading-none text-[var(--color-text)]">{value}</p>
      <p className="mt-3 text-xs text-[var(--color-text-muted)]">{hint}</p>
    </article>
  );
}
