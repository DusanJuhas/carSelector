import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import cs from './locales/cs.json';
import en from './locales/en.json';

/**
 * Only Czech ships in the UI today (`lng`/`fallbackLng` below are both
 * fixed to 'cs' — no language switcher exists yet). The `en` resource
 * bundle is kept in sync so adding a switcher later is just wiring a
 * `SUPPORTED_LANGUAGES` picker to `i18n.changeLanguage`, not redoing the
 * translation-key plumbing across every component.
 */
export const SUPPORTED_LANGUAGES = ['cs', 'en'] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

void i18n.use(initReactI18next).init({
  resources: {
    cs: { translation: cs },
    en: { translation: en },
  },
  lng: 'cs',
  fallbackLng: 'cs',
  interpolation: { escapeValue: false },
});

export default i18n;
