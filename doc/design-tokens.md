# Design tokens — Rovis (AI Car Finder)

Zdroj: `doc/gui/AI Car Finder Concepts2.html`, varianta **1a — Friendly, warm-light**.
Tyto tokeny se používají ve frontendu přes Tailwind v4 `@theme` blok v `src/index.css`.

## Barvy (OKLCH)

| Token         | Hodnota                        | Použití                                  |
|---------------|---------------------------------|-------------------------------------------|
| `bg`          | `oklch(0.975 0.012 75)`         | pozadí aplikace                            |
| `panel`       | `oklch(0.995 0.004 75)`         | pozadí karet, panelů, drawer               |
| `panel-2`     | `oklch(0.95 0.015 75)`          | druhotné pozadí (chip pozadí, spec tagy)   |
| `text`        | `oklch(0.27 0.02 55)`           | primární text                              |
| `subtext`     | `oklch(0.52 0.02 55)`           | sekundární text, popisky                   |
| `border`      | `oklch(0.9 0.015 70)`           | oddělovače, rámečky                        |
| `accent`      | `oklch(0.58 0.15 250)`          | primární akce, aktivní stavy, top-match    |
| `accent-soft` | `oklch(0.58 0.15 250 / 0.14)`   | jemné zvýraznění (flash, badge pozadí)     |
| `accent-text` | `oklch(0.99 0.005 75)`          | text na accent pozadí                      |
| `flag`        | `oklch(0.55 0.15 40)`           | varovné štítky (over budget, apod.)        |
| `flag-bg`     | `oklch(0.55 0.15 40 / 0.12)`    | pozadí varovného štítku                    |
| `ai-bubble`   | `oklch(0.95 0.035 235)`         | pozadí bubliny asistenta v chatu           |

## Radius

| Token         | Hodnota | Použití                         |
|---------------|---------|----------------------------------|
| `radius`      | `18px`  | karty, drawer                    |
| `radius-sm`   | `10px`  | tlačítka, chipy, bubliny         |

## Stín

| Token         | Hodnota                              |
|---------------|----------------------------------------|
| `card-shadow` | `0 6px 18px oklch(0.4 0.02 60 / 0.12)` |

## Layout konvence (z konceptu)

- Chat sloupec: pevná šířka `400px`
- Výsledkový grid: `repeat(auto-fill, minmax(230px, 1fr))`
- Requirements drawer: `360px`, vysouvá se zprava přes `translateX`

Varianta **1b — Premium, dark** není v tomto prototypu implementována; tokeny pro ni zůstávají
zdokumentované ve zdrojovém konceptu pro budoucí dark-mode variantu.
