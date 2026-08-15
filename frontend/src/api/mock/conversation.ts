import type { ConversationTurn } from '../../types';

// Scripted demo conversation for the first frontend prototype (no backend yet).
// Mirrors the "1a — friendly, warm-light" concept in doc/gui/AI Car Finder Concepts2.html.
// Real conversations will come from POST /api/conversation once the backend exists —
// this module is the only place that knows the shortlist is currently scripted.
//
// Written directly in Czech rather than routed through src/i18n/ resources: this data
// simulates what the backend's AI layer will eventually generate dynamically in whatever
// language it's prompted in, not static UI chrome — see src/i18n/config.ts for the
// distinction between the two.

export const INTRO_MESSAGE =
  'Ahoj! Řekněte mi, jak budete své nové auto využívat — kde jezdíte, kdo s vámi jezdí, ' +
  'co je pro vás nejdůležitější — a já to přetavím do konkrétních parametrů a vyberu vám ' +
  'reálné vozy k porovnání.';

export const CONVERSATION_SCRIPT: ConversationTurn[] = [
  {
    userText:
      'Jsme čtyřčlenná rodina a skoro každý víkend jezdíme na hory lyžovat. Potřebuju auto, ' +
      'které neklouže na zasněžené silnici a vejdou se do něj lyžařské bagy.',
    assistantText:
      'Rozumím — pravidelné výlety do hor s rodinou znamenají, že kluzké silnice a lyžařská ' +
      'výbava hrají velkou roli. Ve výběru upřednostním pohon 4×4, dostatek zavazadlového ' +
      'prostoru a výbavu pro chladné počasí.',
    stageName: 'výlety do hor',
    requirements: [
      { label: 'Pohon', value: 'Pohon všech kol (4×4)', source: '„neklouže na zasněžené silnici“', changed: true },
      { label: 'Počet míst', value: '5 míst', source: '„čtyřčlenná rodina“', changed: true },
      { label: 'Zavazadlový prostor', value: 'Velký zavazadlový prostor, střešní nosič', source: '„vejdou se lyžařské bagy“', changed: true },
      { label: 'Výbava pro zimu', value: 'Zimní balíček výbavy', source: '„hory... zasněžená silnice“', changed: true },
    ],
    cars: [
      { id: 'subaru-outback-wilderness', make: 'Subaru', model: 'Outback Wilderness', price: { amount: 811000, currency: 'CZK' }, score: 93, specs: ['4×4', '5 míst', 'Combi, velký kufr'], flag: null },
      { id: 'volvo-xc60', make: 'Volvo', model: 'XC60', price: { amount: 1149000, currency: 'CZK' }, score: 88, specs: ['4×4', '5 míst', 'Prémiová výbava'], flag: null },
      { id: 'toyota-rav4-adventure', make: 'Toyota', model: 'RAV4 Adventure', price: { amount: 780000, currency: 'CZK' }, score: 86, specs: ['4×4', '5 míst'], flag: null },
      { id: 'skoda-kodiaq-4x4', make: 'Škoda', model: 'Kodiaq 4x4', price: { amount: 884000, currency: 'CZK' }, score: 81, specs: ['4×4', '7 míst'], flag: null },
    ],
  },
  {
    userText:
      'Většinu času vlastně jezdím po městě — s parkováním je to tady náročné a chtěl/a bych ' +
      'něco úsporného na palivo.',
    assistantText:
      'Zaznamenáno — každodenní jízda po městě mění priority. Ve výběru teď zvýhodním ' +
      'úspornost provozu a snazší parkování, pohon 4×4 beru už jen jako výhodu navíc, ne ' +
      'jako nutnost.',
    stageName: 'dojíždění po městě',
    requirements: [
      { label: 'Pohon', value: '4×4 — volitelně, není nutnost', source: '„většinu času jezdím po městě“', changed: true },
      { label: 'Počet míst', value: '5 míst', source: '„čtyřčlenná rodina“', changed: false },
      { label: 'Zavazadlový prostor', value: 'Velký zavazadlový prostor, střešní nosič', source: '„vejdou se lyžařské bagy“', changed: false },
      { label: 'Výbava pro zimu', value: 'Zimní balíček výbavy', source: '„hory... zasněžená silnice“', changed: false },
      { label: 'Karoserie', value: 'Kompaktní, snadné parkování', source: '„s parkováním je to náročné“', changed: true },
      { label: 'Spotřeba', value: 'Hybrid nebo elektromobil', source: '„úsporné na palivo“', changed: true },
    ],
    cars: [
      { id: 'toyota-corolla-cross-hybrid-awd', make: 'Toyota', model: 'Corolla Cross Hybrid AWD', price: { amount: 700000, currency: 'CZK' }, score: 95, specs: ['Hybrid', '4×4', 'Kompaktní'], flag: null },
      { id: 'honda-cr-v-hybrid', make: 'Honda', model: 'CR-V Hybrid', price: { amount: 804000, currency: 'CZK' }, score: 90, specs: ['Hybrid', '4×4'], flag: null },
      { id: 'kia-niro-hybrid', make: 'Kia', model: 'Niro Hybrid', price: { amount: 645000, currency: 'CZK' }, score: 84, specs: ['Hybrid', 'Kompaktní'], flag: null },
      { id: 'hyundai-kona-electric', make: 'Hyundai', model: 'Kona Electric', price: { amount: 773000, currency: 'CZK' }, score: 79, specs: ['Elektromobil', 'Kompaktní'], flag: null },
    ],
  },
  {
    userText: 'Rozpočet mám zhruba 705 000 – 752 000 Kč a bezpečnost je pro mě naprostá priorita — máme dvě malé děti.',
    assistantText:
      'Perfektní — vyfiltroval/a jsem auta ve vašem rozpočtu 705 000 – 752 000 Kč a ' +
      'bezpečnostní hodnocení jsem posunul/a na první místo v žebříčku. Tady je vaše ' +
      'nejlepší volba.',
    stageName: 'rozpočet a bezpečnost',
    requirements: [
      { label: 'Pohon', value: '4×4 — volitelně, není nutnost', source: '„většinu času jezdím po městě“', changed: false },
      { label: 'Počet míst', value: '5 míst', source: '„čtyřčlenná rodina“', changed: false },
      { label: 'Zavazadlový prostor', value: 'Velký zavazadlový prostor, střešní nosič', source: '„vejdou se lyžařské bagy“', changed: false },
      { label: 'Výbava pro zimu', value: 'Zimní balíček výbavy', source: '„hory... zasněžená silnice“', changed: false },
      { label: 'Karoserie', value: 'Kompaktní, snadné parkování', source: '„s parkováním je to náročné“', changed: false },
      { label: 'Spotřeba', value: 'Hybrid nebo elektromobil', source: '„úsporné na palivo“', changed: false },
      { label: 'Rozpočet', value: '705 000 – 752 000 Kč', source: '„rozpočet zhruba 705 000–752 000 Kč“', changed: true },
      { label: 'Bezpečnost', value: 'Nejvyšší hodnocení nárazových testů, senzory na zadních sedadlech', source: '„dvě malé děti... naprostá priorita“', changed: true },
    ],
    cars: [
      { id: 'toyota-corolla-cross-hybrid-awd-2', make: 'Toyota', model: 'Corolla Cross Hybrid AWD', price: { amount: 700000, currency: 'CZK' }, score: 97, specs: ['Hybrid', '4×4', '5* bezpečnost'], flag: null, topPick: true },
      { id: 'kia-niro-hybrid-2', make: 'Kia', model: 'Niro Hybrid', price: { amount: 645000, currency: 'CZK' }, score: 89, specs: ['Hybrid', '5* bezpečnost'], flag: null },
      { id: 'honda-cr-v-hybrid-2', make: 'Honda', model: 'CR-V Hybrid', price: { amount: 804000, currency: 'CZK' }, score: 72, specs: ['Hybrid', '4×4'], flag: 'Nad rozpočtem o ~52 000 Kč' },
      { id: 'hyundai-kona-electric-2', make: 'Hyundai', model: 'Kona Electric', price: { amount: 773000, currency: 'CZK' }, score: 68, specs: ['Elektromobil'], flag: 'Omezený dojezd v mrazu' },
    ],
  },
];
