"""Temperature, humidity, fan speed and filter countdown sensors."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VentsConfigEntry
from .entity import VentsEntity


@dataclass(frozen=True, kw_only=True)
class VentsSensorDescription(SensorEntityDescription):
    attribute: str


SENSORS = (
    *(
        VentsSensorDescription(
            key=key,
            name=key.replace("_", " ").capitalize(),
            attribute=f"{key}_temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        )
        for key in ("supply_in", "supply_out", "exhaust_in", "exhaust_out")
    ),
    VentsSensorDescription(
        key="humidity",
        name="Humidity",
        attribute="current_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    *(
        VentsSensorDescription(
            key=f"fan{index}_speed",
            name=f"Fan{index} speed",
            attribute=f"fan{index}_speed",
            icon="mdi:fan",
            native_unit_of_measurement="rpm",
            state_class=SensorStateClass.MEASUREMENT,
        )
        for index in (1, 2)
    ),
    VentsSensorDescription(
        key="filter_days_remaining",
        name="Filter days remaining",
        attribute="filter_days_remaining",
        icon="mdi:air-filter",
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VentsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(VentsSensor(entry, description) for description in SENSORS)


class VentsSensor(VentsEntity, SensorEntity):
    entity_description: VentsSensorDescription

    def __init__(
        self, entry: VentsConfigEntry, description: VentsSensorDescription
    ) -> None:
        super().__init__(entry, description.key, str(description.name))
        self.entity_description = description

    @property
    def native_value(self) -> int | float | None:
        value: int | float | None = getattr(
            self.coordinator.data.status, self.entity_description.attribute
        )
        return value

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None
