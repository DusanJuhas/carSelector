import { useTranslation } from 'react-i18next';
import type { SortOption } from '../types';

export interface SortControlProps {
  value: SortOption;
  onChange: (value: SortOption) => void;
}

const OPTIONS: SortOption[] = ['recommended', 'price_asc', 'price_desc', 'alpha', 'custom'];

export function SortControl({ value, onChange }: SortControlProps) {
  const { t } = useTranslation();

  return (
    <label className="flex items-center gap-2 text-[13px] text-subtext">
      {t('results.sortBy')}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as SortOption)}
        className="rounded-control border border-border bg-panel-2 px-2.5 py-1.5 text-[13px] font-semibold text-text"
      >
        {OPTIONS.map((option) => (
          <option key={option} value={option}>
            {t(`results.sort.${option}`)}
          </option>
        ))}
      </select>
    </label>
  );
}
