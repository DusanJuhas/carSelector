"""Import every model so `Base.metadata` is fully populated - required for
Alembic autogenerate and for `Base.metadata.create_all()` to see all tables.
"""

from app.models.brand import Brand
from app.models.car_model import CarModel
from app.models.color import Color
from app.models.configuration import Configuration
from app.models.configuration_color import ConfigurationColor
from app.models.option_availability import OptionAvailability
from app.models.option_item import OptionItem
from app.models.powertrain import Powertrain
from app.models.price import Price
from app.models.source_document import SourceDocument
from app.models.trim import Trim

__all__ = [
    "Brand",
    "CarModel",
    "Color",
    "Configuration",
    "ConfigurationColor",
    "OptionAvailability",
    "OptionItem",
    "Powertrain",
    "Price",
    "SourceDocument",
    "Trim",
]
