import enum


class FuelType(str, enum.Enum):
    petrol = "petrol"
    diesel = "diesel"
    mild_hybrid = "mild_hybrid"
    phev = "phev"
    electric = "electric"


class Drivetrain(str, enum.Enum):
    fwd = "fwd"
    rwd = "rwd"
    awd = "awd"


class ConsumptionUnit(str, enum.Enum):
    l_100km = "l_100km"
    kwh_100km = "kwh_100km"


class ColorFinish(str, enum.Enum):
    solid = "solid"
    metallic = "metallic"
    pearlescent = "pearlescent"


class OptionCategory(str, enum.Enum):
    equipment = "equipment"
    package = "package"
    warranty = "warranty"
    service = "service"


class AvailabilityStatus(str, enum.Enum):
    standard = "standard"
    optional = "optional"
    unavailable = "unavailable"


class DocumentType(str, enum.Enum):
    price_list = "price_list"
    brochure = "brochure"
