import { useTranslation } from 'react-i18next';
import type { Car } from '../types';
import { CarCard } from './CarCard';

export interface ResultsGridProps {
  cars: Car[];
}

export function ResultsGrid({ cars }: ResultsGridProps) {
  const { t } = useTranslation();

  if (cars.length === 0) {
    return (
      <div className="px-5 py-10 text-center text-[13px] text-subtext">
        {t('results.emptyState')}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(230px,1fr))] gap-4">
      {cars.map((car) => (
        <CarCard key={car.id} car={car} />
      ))}
    </div>
  );
}
