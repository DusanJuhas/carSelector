"""Czech UI copy, ported verbatim from the former frontend's
`src/i18n/locales/cs.json`. Czech is the only language that ever shipped
(the React app's `en.json` existed but was never wired to a switcher) - see
`doc/prompt/CLAUDE.md`'s language convention. No i18n library: a plain
nested dict plus a small lookup/pluralization helper is enough for one
fixed language and keeps the UI layer dependency-free.
"""

STRINGS: dict = {
    "header": {
        "brand": "Rovis",
        "tagline": "Popište svůj životní styl. Najdeme vám auto.",
        "restart": "Restartovat",
        "technicalRequirements": "Technické požadavky",
    },
    "chat": {
        "typePlaceholder": "Napište odpověď…",
        "send": "Odeslat",
        "sending": "Přemýšlím…",
        "aiNotConfigured": (
            "AI vrstva zatím není nastavená (chybí API klíč) — konverzace funguje, "
            "ale bez rozpoznávání požadavků a doporučení."
        ),
        "genericError": "Něco se nepovedlo. Zkuste to prosím znovu.",
    },
    "results": {
        "title": {
            "one": "{count} shoda pro vás",
            "few": "{count} shody pro vás",
            "other": "{count} shod pro vás",
        },
        "browsingTitle": {
            "one": "{count} vůz v katalogu",
            "few": "{count} vozy v katalogu",
            "other": "{count} vozů v katalogu",
        },
        "updated": "Aktualizováno podle vaší poslední zprávy",
        "startPrompt": "Začněte konverzaci a AI vám katalog zúží podle vašich potřeb.",
        "emptyState": "Zatím nic nevyhovuje vašim požadavkům — zkuste je v konverzaci upravit.",
        "loadMore": "Načíst další",
        "loadingMore": "Načítám další…",
        "loadingCatalog": "Načítám katalog…",
        "catalogError": "Nepodařilo se načíst katalog vozů.",
        "sortBy": "Seřadit podle",
        "sort": {
            "recommended": "Doporučeno",
            "price_asc": "Cena: od nejnižší",
            "price_desc": "Cena: od nejvyšší",
            "alpha": "Abecedně",
            "custom": "Moje pořadí",
        },
        "dragHint": "Přetáhněte pro změnu pořadí",
        "filters": {
            "all": "Vše",
            "brand": "Výrobce",
            "fuelType": "Druh motoru",
            "drivetrain": "Pohon",
        },
    },
    "car": {
        "photoPlaceholder": "fotka auta — {make} {model}",
        "topMatch": "Nejlepší shoda",
    },
    "requirements": {
        "subtitle": "Běžný jazyk, převedený na technické specifikace.",
        "empty": "Zatím nebyly zachyceny žádné požadavky.",
    },
    "vehicleDetail": {
        "close": "Zavřít",
        "loading": "Načítám detail vozu…",
        "error": "Nepodařilo se načíst detail vozu.",
        "sections": {
            "powertrain": "Motor a pohon",
            "colors": "Barvy",
            "standardEquipment": "Standardní výbava",
            "optionalEquipment": "Volitelná výbava",
            "priceHistory": "Historie ceny",
        },
        "fields": {
            "fuelType": "Palivo",
            "transmission": "Převodovka",
            "drivetrain": "Pohon",
            "power": "Výkon",
            "consumption": "Spotřeba",
            "co2": "Emise CO₂",
            "noData": "Údaj není k dispozici",
        },
        "priceHistory": {
            "current": "aktuální",
            "lowestPrice30d": "nejnižší cena za 30 dní: {price}",
        },
        "noColors": "Žádné barevné varianty nejsou k dispozici.",
        "noOptionalEquipment": "Žádná volitelná výbava není k dispozici.",
        "enums": {
            "fuelType": {
                "petrol": "Benzín",
                "diesel": "Nafta",
                "hybrid": "Hybrid",
                "mild_hybrid": "Mild hybrid",
                "phev": "Plug-in hybrid",
                "electric": "Elektromobil",
            },
            "drivetrain": {
                "fwd": "Pohon předních kol",
                "rwd": "Pohon zadních kol",
                "awd": "Pohon všech kol (4×4)",
            },
            "consumptionUnit": {
                "l_100km": "l/100 km",
                "kwh_100km": "kWh/100 km",
            },
            "colorFinish": {
                "solid": "Uni",
                "metallic": "Metalíza",
                "pearlescent": "Perleťová",
            },
            "optionCategory": {
                "equipment": "Výbava",
                "package": "Balíček",
                "warranty": "Záruka",
                "service": "Servis",
            },
        },
    },
}


def t(path: str, **kwargs: object) -> str:
    """Looks up one string by dotted path and formats it.

    Args:
        path: Dotted key path into `STRINGS`, e.g. `"chat.send"` or
            `"vehicleDetail.enums.fuelType.petrol"`.
        **kwargs: Values to interpolate into the string via `str.format`,
            e.g. `t("car.photoPlaceholder", make="Mazda", model="CX-5")`.

    Returns:
        The formatted string.

    Raises:
        KeyError: `path` doesn't resolve to a string in `STRINGS`.
    """
    node: object = STRINGS
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"No i18n string at {path!r}")
        node = node[part]
    if not isinstance(node, str):
        raise KeyError(f"{path!r} is not a leaf string")
    return node.format(**kwargs) if kwargs else node


def plural_key(count: int) -> str:
    """Picks the Czech plural form key for a count.

    Czech distinguishes exactly three forms for this kind of count: 1 (`one`),
    2-4 (`few`), and 0 or 5+ (`other`) - the fourth i18next form (`many`, for
    fractional counts) never applies here since these are always integer
    item counts.

    Args:
        count: The number being displayed (e.g. a result count).

    Returns:
        `"one"`, `"few"`, or `"other"` - a key under `results.title`/
        `results.browsingTitle` in `STRINGS`.
    """
    if count == 1:
        return "one"
    if 2 <= count <= 4:
        return "few"
    return "other"


def t_count(path: str, count: int) -> str:
    """Looks up a pluralized string (one with `one`/`few`/`other` sub-keys)
    and formats it with `count`.

    Args:
        path: Dotted path to the pluralized group, e.g. `"results.title"`.
        count: The count to pick a plural form for and interpolate.

    Returns:
        The formatted string for `count`'s plural form.
    """
    return t(f"{path}.{plural_key(count)}", count=count)
