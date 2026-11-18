"""Target temperature and configured fan speeds."""

from dataclasses import dataclass

from aiovents import Register
from aiovents.codec import register_name
from aiovents.models import SETTINGS_REGISTERS
from aiovents.registers import TARGET_TEMP
from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VentsConfigEntry
from .entity import VentsEntity, temperature_setpoint, whole_value


@dataclass(frozen=True, kw_only=True)
class VentsNumberDescription(NumberEntityDescription):
    register: Register


NUMBERS = (
    VentsNumberDescription(
        key="target_temp",
        name="Target temp",
        icon="mdi:thermostat",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        register=TARGET_TEMP,
    ),
    *(
        VentsNumberDescription(
            key=register_name(register),
            name=register_name(register).replace("_", " ").capitalize(),
            icon=f"mdi:fan-speed-{register_name(register)[-1]}",
            native_unit_of_measurement=PERCENTAGE,
            entity_category=EntityCategory.CONFIG,
            register=register,
        )
        for register in SETTINGS_REGISTERS
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VentsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(VentsNumber(entry, description) for description in NUMBERS)


class VentsNumber(VentsEntity, NumberEntity):
    entity_description: VentsNumberDescription
    _attr_native_step = 1

    def __init__(
        self, entry: VentsConfigEntry, description: VentsNumberDescription
    ) -> None:
        super().__init__(entry, description.key, str(description.name))
        self.entity_description = description
        self._attr_native_min_value = description.register["min"]
        self._attr_native_max_value = description.register["max"]

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data
        if self.entity_description.register == TARGET_TEMP:
            return data.status.target_temp
        if data.settings is None:
            return None
        value: int | None = getattr(data.settings, self.entity_description.key)
        return value

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None

    async def async_set_native_value(self, value: float) -> None:
        register = self.entity_description.register
        if register == TARGET_TEMP:
            setpoint = temperature_setpoint(float(value), self.unit_of_measurement)
        else:
            setpoint = whole_value(
                float(value), translation_key="whole_number_required"
            )
        await self.async_write(register, setpoint)
