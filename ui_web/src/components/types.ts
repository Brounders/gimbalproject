export type ThemeMode = 'dark' | 'light';

export type SessionStatus = 'idle' | 'running' | 'recording' | 'error';

export type SourceType = 'camera' | 'video' | 'folder';

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  id: number;
  ts: string;
  level: LogLevel;
  message: string;
}
