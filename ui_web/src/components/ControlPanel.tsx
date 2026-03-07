import type { ReactNode } from 'react';

import { Button } from './Button';
import { PathInput, TextInput } from './TextInput';
import { Select } from './Select';
import { Toggle } from './Toggle';
import { SourceType } from './types';

export interface ControlValues {
  scenario: string;
  sourceType: SourceType;
  cameraIndex: number;
  sourcePath: string;
  recordOutput: boolean;
  outputPath: string;
  preset: string;
  modelPath: string;
  runtimeMode: string;
  device: string;
  imgsz: number;
  conf: number;
  rescan: number;
  smallTarget: boolean;
  adaptiveScan: boolean;
  lockTracker: boolean;
  nightDetector: boolean;
  roiAssist: boolean;
  showGt: boolean;
  showTiming: boolean;
  showTrails: boolean;
}

interface ControlPanelProps {
  values: ControlValues;
  errors: Partial<Record<'sourcePath' | 'outputPath' | 'cameraIndex', string>>;
  expertEnabled: boolean;
  running: boolean;
  evaluating: boolean;
  onChange: (patch: Partial<ControlValues>) => void;
  onBrowseSource: () => void;
  onBrowseOutput: () => void;
  onBrowseModel: () => void;
  onApplyPreset: () => void;
  onLoadProfile: () => void;
  onSaveProfile: () => void;
  onEvaluate: () => void;
  onStart: () => void;
  onStop: () => void;
}

const scenarioOptions = [
  { value: 'default', label: 'Дневной (базовый)' },
  { value: 'small_target', label: 'Малые цели' },
  { value: 'night', label: 'Ночной режим' },
  { value: 'antiuav_thermal', label: 'Thermal / Anti-UAV' },
  { value: 'rpi_hailo', label: 'RPi + Hailo' },
  { value: 'custom', label: 'Пользовательский' },
];

const sourceTypeOptions = [
  { value: 'camera', label: 'Камера' },
  { value: 'video', label: 'Видео файл' },
  { value: 'folder', label: 'Папка кадров' },
];

const presetOptions = [
  { value: 'default', label: 'default' },
  { value: 'small_target', label: 'small_target' },
  { value: 'night', label: 'night' },
  { value: 'antiuav_thermal', label: 'antiuav_thermal' },
  { value: 'rpi_hailo', label: 'rpi_hailo' },
  { value: 'custom', label: 'custom' },
];

const modeOptions = [
  { value: 'research', label: 'research' },
  { value: 'operator', label: 'operator' },
  { value: 'embedded', label: 'embedded' },
];

const deviceOptions = [
  { value: 'mps', label: 'mps' },
  { value: 'cpu', label: 'cpu' },
  { value: 'hailo', label: 'hailo' },
];

export function ControlPanel({
  values,
  errors,
  expertEnabled,
  running,
  evaluating,
  onChange,
  onBrowseSource,
  onBrowseOutput,
  onBrowseModel,
  onApplyPreset,
  onLoadProfile,
  onSaveProfile,
  onEvaluate,
  onStart,
  onStop,
}: ControlPanelProps) {
  const sourcePlaceholder = values.sourceType === 'folder' ? '/path/to/frame-folder' : '/path/to/video.mp4';

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <QuickChip label="Scenario" value={values.scenario} />
        <QuickChip label="Runtime" value={`${values.runtimeMode} / ${values.device}`} />
      </div>

      <Section
        eyebrow="Mission source"
        title="Сценарий, источник и захват"
        description="Подготовь входной поток и рабочий профиль перед запуском."
      >
        <Select
          label="Сценарий"
          options={scenarioOptions}
          value={values.scenario}
          onChange={(event) => onChange({ scenario: event.target.value })}
        />

        <div className="grid gap-3 sm:grid-cols-2">
          <Select
            label="Источник"
            options={sourceTypeOptions}
            value={values.sourceType}
            onChange={(event) => onChange({ sourceType: event.target.value as SourceType })}
          />
          <TextInput
            label="Номер камеры"
            type="number"
            min={0}
            max={16}
            value={String(values.cameraIndex)}
            disabled={values.sourceType !== 'camera'}
            error={errors.cameraIndex}
            onChange={(event) => onChange({ cameraIndex: Number(event.target.value || 0) })}
          />
        </div>

        <PathInput
          label="Файл / Папка"
          value={values.sourcePath}
          onChange={(next) => onChange({ sourcePath: next })}
          onBrowse={onBrowseSource}
          disabled={values.sourceType === 'camera'}
          error={errors.sourcePath}
          placeholder={values.sourceType === 'camera' ? 'Для камеры путь не нужен' : sourcePlaceholder}
        />
      </Section>

      <Section
        eyebrow="Output"
        title="Запись и экспорт"
        description="Настрой, нужно ли сохранять размеченный поток и куда писать результат."
      >
        <Toggle
          label="Сохранять видео"
          description="Включает запись размеченного потока на диск"
          checked={values.recordOutput}
          onChange={(next) => onChange({ recordOutput: next })}
        />

        <PathInput
          label="Куда сохранить"
          value={values.outputPath}
          onChange={(next) => onChange({ outputPath: next })}
          onBrowse={onBrowseOutput}
          browseLabel="Куда сохранить"
          disabled={!values.recordOutput}
          error={errors.outputPath}
          placeholder="/runs/gui_output.mp4"
        />
      </Section>

      <Section
        eyebrow="Launch"
        title="Операции сессии"
        description="Запускай рабочий поток, тестируй качество и быстро останавливай текущую сцену."
      >
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <Button type="button" variant="secondary" onClick={onEvaluate} disabled={running || evaluating} loading={evaluating}>
            Оценка
          </Button>
          <Button type="button" variant="primary" size="lg" onClick={onStart} disabled={running || evaluating}>
            Старт
          </Button>
          <Button type="button" variant="destructive" size="lg" onClick={onStop} disabled={!running && !evaluating}>
            Стоп
          </Button>
        </div>
      </Section>

      {expertEnabled ? (
        <Section
          eyebrow="Expert"
          title="Тонкая настройка контура"
          description="Управляй профилями, моделью и диагностическими флагами без выхода из консоли."
        >
          <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
            <Select
              label="Preset"
              options={presetOptions}
              value={values.preset}
              onChange={(event) => onChange({ preset: event.target.value })}
            />
            <div className="grid grid-cols-3 gap-2 self-end">
              <Button type="button" size="sm" onClick={onApplyPreset} title="Применить выбранный preset">
                Применить
              </Button>
              <Button type="button" size="sm" variant="ghost" onClick={onLoadProfile}>
                Загрузить
              </Button>
              <Button type="button" size="sm" variant="ghost" onClick={onSaveProfile}>
                Сохранить
              </Button>
            </div>
          </div>

          <PathInput
            label="Модель"
            value={values.modelPath}
            onChange={(next) => onChange({ modelPath: next })}
            onBrowse={onBrowseModel}
            browseLabel="Модель"
          />

          <div className="grid gap-3 sm:grid-cols-2">
            <Select
              label="Mode"
              options={modeOptions}
              value={values.runtimeMode}
              onChange={(event) => onChange({ runtimeMode: event.target.value })}
            />
            <Select
              label="Device"
              options={deviceOptions}
              value={values.device}
              onChange={(event) => onChange({ device: event.target.value })}
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <TextInput
              label="imgsz"
              title="Размер входа YOLO. Больше = выше точность, ниже FPS"
              type="number"
              min={160}
              step={32}
              value={String(values.imgsz)}
              onChange={(event) => onChange({ imgsz: Number(event.target.value || 640) })}
            />
            <TextInput
              label="conf"
              title="Порог уверенности YOLO"
              type="number"
              min={0.01}
              max={0.99}
              step={0.01}
              value={String(values.conf)}
              onChange={(event) => onChange({ conf: Number(event.target.value || 0.3) })}
            />
            <TextInput
              label="rescan"
              title="Интервал full-frame пересканов в lock режиме"
              type="number"
              min={1}
              max={60}
              value={String(values.rescan)}
              onChange={(event) => onChange({ rescan: Number(event.target.value || 6) })}
            />
          </div>

          <div className="grid gap-2 sm:grid-cols-2">
            <Toggle label="Малые цели" checked={values.smallTarget} onChange={(next) => onChange({ smallTarget: next })} />
            <Toggle label="Adaptive scan" checked={values.adaptiveScan} onChange={(next) => onChange({ adaptiveScan: next })} />
            <Toggle label="Lock tracker" checked={values.lockTracker} onChange={(next) => onChange({ lockTracker: next })} />
            <Toggle label="Night detector" checked={values.nightDetector} onChange={(next) => onChange({ nightDetector: next })} />
            <Toggle label="ROI assist" checked={values.roiAssist} onChange={(next) => onChange({ roiAssist: next })} />
            <Toggle label="Показывать GT" checked={values.showGt} onChange={(next) => onChange({ showGt: next })} />
            <Toggle label="Показывать timing" checked={values.showTiming} onChange={(next) => onChange({ showTiming: next })} />
            <Toggle label="Показывать траектории" checked={values.showTrails} onChange={(next) => onChange({ showTrails: next })} />
          </div>
        </Section>
      ) : null}
    </div>
  );
}

function Section({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="control-section space-y-4 rounded-[24px] p-4">
      <div>
        <p className="section-label">{eyebrow}</p>
        <h3 className="text-base font-semibold text-[var(--color-text)]">{title}</h3>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">{description}</p>
      </div>
      {children}
    </section>
  );
}

function QuickChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_82%,transparent)] px-4 py-3">
      <p className="text-[10px] uppercase tracking-[0.16em] text-[var(--color-accent-2)]">{label}</p>
      <p className="mt-2 text-sm font-medium text-[var(--color-text)]">{value}</p>
    </div>
  );
}
