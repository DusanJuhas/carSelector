import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Car } from '../types';
import { CarCard } from './CarCard';

export interface ResultsGridProps {
  cars: Car[];
  onSelectCar?: (car: Car) => void;
  /** Enables drag-to-reorder ("Moje pořadí" sort mode) on the cards below. */
  reorderable?: boolean;
  /** Called with every card's id in its new order once a drag completes. Required when `reorderable` is true. */
  onReorder?: (orderedIds: string[]) => void;
}

export function ResultsGrid({ cars, onSelectCar, reorderable = false, onReorder }: ResultsGridProps) {
  const { t } = useTranslation();
  const [draggedId, setDraggedId] = useState<string | null>(null);

  if (cars.length === 0) {
    return (
      <div className="px-5 py-10 text-center text-[13px] text-subtext">
        {t('results.emptyState')}
      </div>
    );
  }

  const handleDrop = (targetId: string) => {
    if (!onReorder || draggedId === null || draggedId === targetId) return;
    const ids = cars.map((car) => car.id);
    const fromIndex = ids.indexOf(draggedId);
    const toIndex = ids.indexOf(targetId);
    if (fromIndex === -1 || toIndex === -1) return;
    ids.splice(fromIndex, 1);
    ids.splice(toIndex, 0, draggedId);
    onReorder(ids);
    setDraggedId(null);
  };

  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(230px,1fr))] gap-4">
      {cars.map((car) => (
        <div
          key={car.id}
          draggable={reorderable}
          onDragStart={reorderable ? () => setDraggedId(car.id) : undefined}
          onDragOver={reorderable ? (event) => event.preventDefault() : undefined}
          onDrop={reorderable ? () => handleDrop(car.id) : undefined}
          onDragEnd={reorderable ? () => setDraggedId(null) : undefined}
          className={reorderable ? 'relative cursor-grab active:cursor-grabbing' : 'relative'}
          title={reorderable ? t('results.dragHint') : undefined}
        >
          {reorderable && (
            <div
              aria-hidden="true"
              className="absolute right-2 top-2 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-panel-2/90 text-[13px] text-subtext"
            >
              ⠿
            </div>
          )}
          <CarCard car={car} onSelect={onSelectCar} />
        </div>
      ))}
    </div>
  );
}
