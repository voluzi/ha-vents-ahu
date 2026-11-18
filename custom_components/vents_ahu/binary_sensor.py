"""Boost mode, alarm and filter replacement indicators."""

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VentsConfigEntry
from .entity import VentsEntity


@dataclass(frozen=True, kw_only=True)
class VentsBinarySensorDescription(BinarySensorEntityDescription):
    attribute: str


SENSORS = (
    VentsBinarySensorDescription(
        key="boost_mode",
        name="Boost mode",
        attribute="boost_mode",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:run-fast",
    ),
    VentsBinarySensorDescription(
        key="alarm",
        name="Alarm",
        attribute="alarm_indicator",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    VentsBinarySensorDescription(
        key="filter_replacement",
        name="Filter replacement",
        attribute="filter_indicator",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:air-filter",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VentsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(VentsBinarySensor(entry, description) for description in SENSORS)


class VentsBinarySensor(VentsEntity, BinarySensorEntity):
    entity_description: VentsBinarySensorDescription

    def __init__(
        self, entry: VentsConfigEntry, description: VentsBinarySensorDescription
    ) -> None:
        super().__init__(entry, description.key, str(description.name))
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        value: bool | None = getattr(
            self.coordinator.data.status, self.entity_description.attribute
        )
        return value

    @property
    def available(self) -> bool:
        return super().available and self.is_on is not None
