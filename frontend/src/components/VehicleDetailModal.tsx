import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useVehicleDetail } from '../hooks/useVehicleDetail';
import { formatMoney } from '../utils/money';

export interface VehicleDetailModalProps {
  configurationId: string;
  onClose: () => void;
}

export function VehicleDetailModal({ configurationId, onClose }: VehicleDetailModalProps) {
  const { t } = useTranslation();
  const { detail, isLoading, error } = useVehicleDetail(configurationId);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const consumptionLabel = (() => {
    if (!detail || detail.powertrain.consumptionMin === null || detail.powertrain.consumptionUnit === null) {
      return null;
    }
    const unit = t(`vehicleDetail.enums.consumptionUnit.${detail.powertrain.consumptionUnit}`);
    const { consumptionMin, consumptionMax } = detail.powertrain;
    const value =
      consumptionMax !== null && consumptionMax !== consumptionMin
        ? `${consumptionMin}–${consumptionMax}`
        : `${consumptionMin}`;
    return `${value} ${unit}`;
  })();

  const powerLabel = (() => {
    if (!detail || detail.powertrain.powerKw === null) return null;
    const hp = detail.powertrain.powerHp !== null ? ` (${detail.powertrain.powerHp} k)` : '';
    return `${detail.powertrain.powerKw} kW${hp}`;
  })();

  const co2Label = (() => {
    if (!detail || detail.powertrain.co2MinGKm === null) return null;
    const { co2MinGKm, co2MaxGKm } = detail.powertrain;
    const value = co2MaxGKm !== null && co2MaxGKm !== co2MinGKm ? `${co2MinGKm}–${co2MaxGKm}` : `${co2MinGKm}`;
    return `${value} g/km`;
  })();

  return (
    <>
      <div onClick={onClose} className="fixed inset-0 z-30 bg-black/40" />
      <div className="fixed inset-0 z-40 flex items-center justify-center p-4" onClick={onClose}>
        <div
          onClick={(event) => event.stopPropagation()}
          className="max-h-[85vh] w-full max-w-[640px] overflow-y-auto rounded-card border border-border bg-panel p-6 shadow-card animate-fade-in"
        >
          {isLoading && (
            <div className="px-5 py-10 text-center text-[13px] text-subtext">{t('vehicleDetail.loading')}</div>
          )}
          {error && !isLoading && (
            <div className="px-5 py-10 text-center text-[13px] text-subtext">{t('vehicleDetail.error')}</div>
          )}
          {detail && !isLoading && !error && (
            <>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[18px] font-bold text-text">
                    {detail.make} {detail.model} {detail.trim}
                  </div>
                  <div className="mt-0.5 text-[14px] text-subtext">{formatMoney(detail.price)}</div>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  aria-label={t('vehicleDetail.close')}
                  className="shrink-0 rounded-control border border-border bg-panel-2 px-3 py-1.5 text-[13px] font-semibold text-text"
                >
                  {t('vehicleDetail.close')}
                </button>
              </div>

              <div className="mt-5">
                <div className="mb-2 text-[13px] font-bold uppercase tracking-wide text-subtext">
                  {t('vehicleDetail.sections.powertrain')}
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 rounded-control bg-panel-2 p-3.5 text-[13px]">
                  <DetailField label={t('vehicleDetail.fields.fuelType')} value={t(`vehicleDetail.enums.fuelType.${detail.powertrain.fuelType}`)} />
                  <DetailField label={t('vehicleDetail.fields.drivetrain')} value={t(`vehicleDetail.enums.drivetrain.${detail.powertrain.drivetrain}`)} />
                  <DetailField label={t('vehicleDetail.fields.transmission')} value={detail.powertrain.transmission} noData={t('vehicleDetail.fields.noData')} />
                  <DetailField label={t('vehicleDetail.fields.power')} value={powerLabel} noData={t('vehicleDetail.fields.noData')} />
                  <DetailField label={t('vehicleDetail.fields.consumption')} value={consumptionLabel} noData={t('vehicleDetail.fields.noData')} />
                  <DetailField label={t('vehicleDetail.fields.co2')} value={co2Label} noData={t('vehicleDetail.fields.noData')} />
                </div>
              </div>

              <div className="mt-5">
                <div className="mb-2 text-[13px] font-bold uppercase tracking-wide text-subtext">
                  {t('vehicleDetail.sections.colors')}
                </div>
                {detail.colors.length === 0 ? (
                  <div className="text-[12.5px] text-subtext">{t('vehicleDetail.noColors')}</div>
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {detail.colors.map((color) => (
                      <span
                        key={color.name}
                        className="rounded-full border border-border bg-panel-2 px-2.5 py-1 text-[11.5px] font-semibold text-subtext"
                      >
                        {color.name}
                        {color.finishType && ` · ${t(`vehicleDetail.enums.colorFinish.${color.finishType}`)}`}
                        {color.surcharge.amount > 0 && ` · +${formatMoney(color.surcharge)}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-5">
                <div className="mb-2 text-[13px] font-bold uppercase tracking-wide text-subtext">
                  {t('vehicleDetail.sections.standardEquipment')}
                </div>
                <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-[12.5px] text-text">
                  {detail.standardEquipment.map((item) => (
                    <li key={item} className="list-inside list-disc">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-5">
                <div className="mb-2 text-[13px] font-bold uppercase tracking-wide text-subtext">
                  {t('vehicleDetail.sections.optionalEquipment')}
                </div>
                {detail.optionalEquipment.length === 0 ? (
                  <div className="text-[12.5px] text-subtext">{t('vehicleDetail.noOptionalEquipment')}</div>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    {detail.optionalEquipment.map((option) => (
                      <div key={option.name} className="flex items-center justify-between gap-3 text-[12.5px]">
                        <span className="text-text">
                          {option.name}{' '}
                          <span className="text-subtext">
                            ({t(`vehicleDetail.enums.optionCategory.${option.category}`)})
                          </span>
                        </span>
                        <span className="shrink-0 text-subtext">{formatMoney(option.surcharge)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-5">
                <div className="mb-2 text-[13px] font-bold uppercase tracking-wide text-subtext">
                  {t('vehicleDetail.sections.priceHistory')}
                </div>
                <div className="flex flex-col gap-1.5">
                  {detail.priceHistory.map((point) => (
                    <div key={point.validFrom} className="flex items-center justify-between gap-3 text-[12.5px]">
                      <span className="text-subtext">
                        {point.validFrom} – {point.validTo ?? t('vehicleDetail.priceHistory.current')}
                      </span>
                      <span className="text-text">
                        {formatMoney(point.price)}
                        {point.lowestPrice30d && (
                          <span className="ml-1.5 text-subtext">
                            ({t('vehicleDetail.priceHistory.lowestPrice30d', { price: formatMoney(point.lowestPrice30d) })})
                          </span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

interface DetailFieldProps {
  label: string;
  value: string | null;
  noData?: string;
}

function DetailField({ label, value, noData }: DetailFieldProps) {
  return (
    <div>
      <div className="text-[10.5px] font-bold uppercase tracking-wide text-subtext">{label}</div>
      <div className="mt-0.5 font-semibold text-text">{value ?? noData}</div>
    </div>
  );
}
