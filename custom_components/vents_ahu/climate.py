"""Climate and power control."""

from typing import Any

from aiovents.registers import POWER_ON, SPEED, TARGET_TEMP
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MODE_BY_OPTION, OPTION_BY_MODE, OPTION_BY_SPEED, SPEED_BY_OPTION
from .coordinator import VentsConfigEntry
from .entity import VentsEntity, whole_value


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VentsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([VentsClimate(entry)])


class VentsClimate(VentsEntity, ClimateEntity):
    _attr_hvac_modes = [HVACMode.OFF, *MODE_BY_OPTION]
    _attr_fan_modes = list(SPEED_BY_OPTION)
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = TARGET_TEMP["min"]
    _attr_max_temp = TARGET_TEMP["max"]
    _attr_target_temperature_step = 1
    _attr_precision = PRECISION_WHOLE
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, entry: VentsConfigEntry) -> None:
        super().__init__(entry, "climate", None)

    @property
    def available(self) -> bool:
        return super().available and self.hvac_mode is not None

    @property
    def hvac_mode(self) -> HVACMode | None:
        status = self.coordinator.data.status
        if status.power_on is False:
            return HVACMode.OFF
        if status.power_on and status.mode is not None:
            return OPTION_BY_MODE[status.mode]
        return None

    @property
    def fan_mode(self) -> str | None:
        speed = self.coordinator.data.status.speed
        return OPTION_BY_SPEED[speed] if speed is not None else None

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.status.exhaust_in_temperature

    @property
    def current_humidity(self) -> int | None:
        return self.coordinator.data.status.current_humidity

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.status.target_temp

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
        elif hvac_mode in MODE_BY_OPTION:
            await self.coordinator.async_set_mode(MODE_BY_OPTION[hvac_mode])
        else:
            raise ServiceValidationError("Unsupported HVAC mode")

    async def async_turn_on(self) -> None:
        await self.async_write(POWER_ON, True)

    async def async_turn_off(self) -> None:
        await self.async_write(POWER_ON, False)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if fan_mode not in SPEED_BY_OPTION:
            raise ServiceValidationError("Unsupported fan mode")
        await self.async_write(SPEED, int(SPEED_BY_OPTION[fan_mode]))

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if ATTR_TEMPERATURE in kwargs:
            value = whole_value(
                float(kwargs[ATTR_TEMPERATURE]),
                translation_key="whole_temperature_required",
            )
            await self.async_write(TARGET_TEMP, value)
