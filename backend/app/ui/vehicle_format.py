"""Display labels for a vehicle's powertrain figures, shared by the detail
dialog (`app/ui/components/vehicle_detail_modal.py`) and its PDF export
(`app/ui/vehicle_pdf.py`) so both show the same numbers the same way.
"""

from app.schemas.vehicle import PowertrainSpec
from app.ui.i18n import t


def consumption_label(powertrain: PowertrainSpec) -> str | None:
    """Args:
        powertrain: Spec to read consumption fields from.

    Returns:
        e.g. `"5.4–6.1 l/100 km"` or `"5.4 l/100 km"` (min==max), or
        `None` if either field is missing.
    """
    if powertrain.consumption_min is None or powertrain.consumption_unit is None:
        return None
    unit = t(f"vehicleDetail.enums.consumptionUnit.{powertrain.consumption_unit.value}")
    if powertrain.consumption_max is not None and powertrain.consumption_max != powertrain.consumption_min:
        value = f"{powertrain.consumption_min}–{powertrain.consumption_max}"
    else:
        value = f"{powertrain.consumption_min}"
    return f"{value} {unit}"


def power_label(powertrain: PowertrainSpec) -> str | None:
    """Args:
        powertrain: Spec to read power fields from.

    Returns:
        e.g. `"110 kW (150 k)"`, or `None` if `power_kw` is missing.
    """
    if powertrain.power_kw is None:
        return None
    hp = f" ({powertrain.power_hp} k)" if powertrain.power_hp is not None else ""
    return f"{powertrain.power_kw} kW{hp}"


def co2_label(powertrain: PowertrainSpec) -> str | None:
    """Args:
        powertrain: Spec to read CO2 fields from.

    Returns:
        e.g. `"120–135 g/km"` or `"120 g/km"`, or `None` if
        `co2_min_g_km` is missing.
    """
    if powertrain.co2_min_g_km is None:
        return None
    if powertrain.co2_max_g_km is not None and powertrain.co2_max_g_km != powertrain.co2_min_g_km:
        value = f"{powertrain.co2_min_g_km}–{powertrain.co2_max_g_km}"
    else:
        value = f"{powertrain.co2_min_g_km}"
    return f"{value} g/km"
