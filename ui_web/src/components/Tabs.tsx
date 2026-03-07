import { ReactNode } from 'react';

import { cn } from './utils';

export interface TabItem {
  id: string;
  label: string;
  content: ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
}

export function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div>
      <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-surface-2)_82%,transparent)] p-1">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onChange(tab.id)}
              className={cn(
                'rounded-full px-4 py-2 text-sm font-medium transition-all duration-quick',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]',
                isActive
                  ? 'bg-[linear-gradient(135deg,color-mix(in_srgb,var(--color-accent)_22%,var(--color-surface)),var(--color-surface))] text-[var(--color-text)] shadow-[var(--shadow-soft)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]',
              )}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      <div>{tabs.find((tab) => tab.id === activeTab)?.content}</div>
    </div>
  );
}
