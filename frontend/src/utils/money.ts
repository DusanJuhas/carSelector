import type { Money } from '../types';

/**
 * 'cs-CZ' is the only locale wired in today, matching the fixed UI
 * language in src/i18n/config.ts. Kept as an explicit parameter (not
 * hardcoded inline) so a future language switcher can pass the active
 * locale instead of adding a second formatting path.
 */
export function formatMoney(money: Money, locale = 'cs-CZ'): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: money.currency,
    maximumFractionDigits: 0,
  }).format(money.amount);
}
