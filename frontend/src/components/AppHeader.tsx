import { useTranslation } from 'react-i18next';

export interface AppHeaderProps {
  requirementsCount: number;
  onRestart: () => void;
  onToggleDrawer: () => void;
}

export function AppHeader({ requirementsCount, onRestart, onToggleDrawer }: AppHeaderProps) {
  const { t } = useTranslation();

  return (
    <div className="flex shrink-0 items-center justify-between border-b border-border px-7 py-4.5">
      <div className="flex flex-col gap-0.5">
        <div className="text-xl font-bold tracking-tight text-text">{t('header.brand')}</div>
        <div className="text-[12.5px] text-subtext">{t('header.tagline')}</div>
      </div>
      <div className="flex items-center gap-2.5">
        <button
          type="button"
          onClick={onRestart}
          className="rounded-control border border-border px-3.5 py-2 text-[13px] text-subtext"
        >
          {t('header.restart')}
        </button>
        <button
          type="button"
          onClick={onToggleDrawer}
          className="flex items-center gap-2 rounded-control border border-border bg-panel-2 px-3.5 py-2 text-[13px] font-semibold text-text"
        >
          {t('header.technicalRequirements')}
          <span className="rounded-full bg-accent px-[7px] py-0.5 text-[11px] font-bold text-accent-text">
            {requirementsCount}
          </span>
        </button>
      </div>
    </div>
  );
}
