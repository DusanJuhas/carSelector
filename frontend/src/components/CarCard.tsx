import { useTranslation } from 'react-i18next';
import type { Car } from '../types';
import { formatMoney } from '../utils/money';

export interface CarCardProps {
  car: Car;
  /** When provided, the card becomes clickable/keyboard-activatable and calls this with the car. */
  onSelect?: (car: Car) => void;
}

export function CarCard({ car, onSelect }: CarCardProps) {
  const { t } = useTranslation();
  const isHighScore = car.score !== null && car.score >= 90;

  return (
    <div
      role={onSelect ? 'button' : undefined}
      tabIndex={onSelect ? 0 : undefined}
      onClick={onSelect ? () => onSelect(car) : undefined}
      onKeyDown={
        onSelect
          ? (event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onSelect(car);
              }
            }
          : undefined
      }
      className={`relative flex flex-col overflow-hidden rounded-card border bg-panel shadow-card animate-fade-in ${
        car.topPick ? 'border-accent' : 'border-border'
      } ${onSelect ? 'cursor-pointer' : ''}`}
    >
      {car.topPick && (
        <div className="absolute left-2.5 top-2.5 z-10 rounded-full bg-accent px-2.5 py-1 text-[10.5px] font-bold uppercase tracking-wide text-accent-text">
          {t('car.topMatch')}
        </div>
      )}
      <div
        className="flex h-[140px] items-center justify-center bg-[repeating-linear-gradient(45deg,var(--color-panel-2),var(--color-panel-2)_10px,var(--color-border)_10px,var(--color-border)_20px)] px-3 text-center font-mono text-[11px] text-subtext"
      >
        {t('car.photoPlaceholder', { make: car.make, model: car.model })}
      </div>
      <div className="flex flex-col gap-2.5 p-4 pt-3.5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="text-[14.5px] font-bold text-text">
              {car.make} {car.model} {car.trim}
            </div>
            <div className="mt-0.5 text-[12.5px] text-subtext">{formatMoney(car.price)}</div>
          </div>
          {car.score !== null && (
            <div
              className={`shrink-0 rounded-full px-2.5 py-1 text-[15px] font-bold ${
                isHighScore ? 'bg-accent-soft text-accent' : 'text-subtext'
              }`}
            >
              {car.score}%
            </div>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {car.specs.map((spec) => (
            <span
              key={spec}
              className="rounded-full border border-border bg-panel-2 px-2.5 py-1 text-[11px] font-semibold text-subtext"
            >
              {spec}
            </span>
          ))}
        </div>
        {car.flag && (
          <div className="rounded-control bg-flag-bg px-2.5 py-1.5 text-[11.5px] text-flag">
            {car.flag}
          </div>
        )}
        {car.explanation && (
          <div className="text-[12px] italic leading-relaxed text-subtext">{car.explanation}</div>
        )}
      </div>
    </div>
  );
}
