"""Shared device identity and register commands."""

from aiovents import Register, RegisterValue
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN
from .coordinator import VentsConfigEntry, VentsCoordinator


def whole_value(value: float, *, translation_key: str) -> int:
    if not value.is_integer():
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key=translation_key
        )
    return int(value)


class VentsEntity(CoordinatorEntity[VentsCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, entry: VentsConfigEntry, key: str, name: str | None) -> None:
        super().__init__(entry.runtime_data)
        device_id = entry.data[CONF_DEVICE_ID]
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=entry.title,
            manufacturer="Vents",
            model="AHU",
        )

    async def async_write(self, reg: Register, value: RegisterValue) -> None:
        await self.coordinator.async_write(reg, value)
