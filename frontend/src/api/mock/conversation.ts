import type { ConversationTurn } from '../../types';

// Scripted demo conversation for the first frontend prototype (no backend yet).
// Mirrors the "1a — friendly, warm-light" concept in doc/gui/AI Car Finder Concepts2.html.
// Real conversations will come from POST /api/conversation once the backend exists —
// this module is the only place that knows the shortlist is currently scripted.

export const INTRO_MESSAGE =
  "Hi! Tell me about how you'll use your next car — where you drive, who's riding along, " +
  "what matters most — and I'll translate that into the right specs and shortlist real cars for you.";

export const CONVERSATION_SCRIPT: ConversationTurn[] = [
  {
    userText:
      "We're a family of 4 and head to the mountains almost every weekend for skiing. I need something that won't slip on snowy roads and can fit our ski bags.",
    assistantText:
      "Got it — weekly mountain trips with the family means slippery roads and ski gear are a big factor. I'm prioritizing all-wheel drive, real cargo room, and cold-weather readiness in your shortlist.",
    stageName: 'mountain trips',
    requirements: [
      { label: 'Drivetrain', value: 'All-wheel drive (4x4)', source: '"won\'t slip on snowy roads"', changed: true },
      { label: 'Seating', value: '5 seats', source: '"family of 4"', changed: true },
      { label: 'Cargo', value: 'Large cargo area, roof-rack ready', source: '"fit our ski bags"', changed: true },
      { label: 'Climate readiness', value: 'Cold-weather package', source: '"mountains... snowy roads"', changed: true },
    ],
    cars: [
      { id: 'subaru-outback-wilderness', make: 'Subaru', model: 'Outback Wilderness', price: '$34,500', score: 93, specs: ['AWD', '5 seats', 'Wagon cargo'], flag: null },
      { id: 'volvo-xc60', make: 'Volvo', model: 'XC60', price: '$48,900', score: 88, specs: ['AWD', '5 seats', 'Premium'], flag: null },
      { id: 'toyota-rav4-adventure', make: 'Toyota', model: 'RAV4 Adventure', price: '$33,200', score: 86, specs: ['AWD', '5 seats'], flag: null },
      { id: 'skoda-kodiaq-4x4', make: 'Škoda', model: 'Kodiaq 4x4', price: '$37,600', score: 81, specs: ['AWD', '7 seats'], flag: null },
    ],
  },
  {
    userText:
      "Actually most of my driving is around the city — parking is tight and I'd like something efficient on fuel.",
    assistantText:
      "Noted — daily city driving changes things. I'm dialing up fuel efficiency and easier parking, and treating all-wheel drive as a nice-to-have rather than a must.",
    stageName: 'city commuting',
    requirements: [
      { label: 'Drivetrain', value: 'AWD — optional, not required', source: '"most of my driving is around the city"', changed: true },
      { label: 'Seating', value: '5 seats', source: '"family of 4"', changed: false },
      { label: 'Cargo', value: 'Large cargo area, roof-rack ready', source: '"fit our ski bags"', changed: false },
      { label: 'Climate readiness', value: 'Cold-weather package', source: '"mountains... snowy roads"', changed: false },
      { label: 'Body type', value: 'Compact, easy to park', source: '"parking is tight"', changed: true },
      { label: 'Efficiency', value: 'Hybrid or electric', source: '"efficient on fuel"', changed: true },
    ],
    cars: [
      { id: 'toyota-corolla-cross-hybrid-awd', make: 'Toyota', model: 'Corolla Cross Hybrid AWD', price: '$29,800', score: 95, specs: ['Hybrid', 'AWD', 'Compact'], flag: null },
      { id: 'honda-cr-v-hybrid', make: 'Honda', model: 'CR-V Hybrid', price: '$34,200', score: 90, specs: ['Hybrid', 'AWD'], flag: null },
      { id: 'kia-niro-hybrid', make: 'Kia', model: 'Niro Hybrid', price: '$27,450', score: 84, specs: ['Hybrid', 'Compact'], flag: null },
      { id: 'hyundai-kona-electric', make: 'Hyundai', model: 'Kona Electric', price: '$32,900', score: 79, specs: ['Electric', 'Compact'], flag: null },
    ],
  },
  {
    userText: "Budget's around $30–32k, and safety is non-negotiable — we have two young kids.",
    assistantText:
      "Perfect — I've filtered to your $30–32k range and pushed safety ratings to the top of the ranking. Here's your best match.",
    stageName: 'budget & safety',
    requirements: [
      { label: 'Drivetrain', value: 'AWD — optional, not required', source: '"most of my driving is around the city"', changed: false },
      { label: 'Seating', value: '5 seats', source: '"family of 4"', changed: false },
      { label: 'Cargo', value: 'Large cargo area, roof-rack ready', source: '"fit our ski bags"', changed: false },
      { label: 'Climate readiness', value: 'Cold-weather package', source: '"mountains... snowy roads"', changed: false },
      { label: 'Body type', value: 'Compact, easy to park', source: '"parking is tight"', changed: false },
      { label: 'Efficiency', value: 'Hybrid or electric', source: '"efficient on fuel"', changed: false },
      { label: 'Budget', value: '$30,000 – $32,000', source: '"budget\'s around $30-32k"', changed: true },
      { label: 'Safety', value: 'Top crash-test rating, rear-seat sensors', source: '"two young kids... non-negotiable"', changed: true },
    ],
    cars: [
      { id: 'toyota-corolla-cross-hybrid-awd-2', make: 'Toyota', model: 'Corolla Cross Hybrid AWD', price: '$29,800', score: 97, specs: ['Hybrid', 'AWD', '5-star safety'], flag: null, topPick: true },
      { id: 'kia-niro-hybrid-2', make: 'Kia', model: 'Niro Hybrid', price: '$27,450', score: 89, specs: ['Hybrid', '5-star safety'], flag: null },
      { id: 'honda-cr-v-hybrid-2', make: 'Honda', model: 'CR-V Hybrid', price: '$34,200', score: 72, specs: ['Hybrid', 'AWD'], flag: 'Over budget by ~$2,200' },
      { id: 'hyundai-kona-electric-2', make: 'Hyundai', model: 'Kona Electric', price: '$32,900', score: 68, specs: ['Electric'], flag: 'Limited cold-weather range' },
    ],
  },
];
