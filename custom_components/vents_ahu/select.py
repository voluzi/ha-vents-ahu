"""Operating mode and fan speed selectors."""

from collections.abc import Mapping

from aiovents import Register
from aiovents.codec import register_name
from aiovents.registers import MODE, SPEED
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MODE_BY_OPTION, SPEED_BY_OPTION
from .coordinator import VentsConfigEntry
from .entity import VentsEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VentsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        [
            VentsSelect(
                entry,
                "mode",
                "Mode",
                "mdi:cached",
                MODE,
                {option.value: value for option, value in MODE_BY_OPTION.items()},
            ),
            VentsSelect(
                entry, "fan_mode", "Fan mode", "mdi:fan", SPEED, SPEED_BY_OPTION
            ),
        ]
    )


class VentsSelect(VentsEntity, SelectEntity):
    def __init__(
        self,
        entry: VentsConfigEntry,
        key: str,
        name: str,
        icon: str,
        register: Register,
        options: Mapping[str, int],
    ) -> None:
        super().__init__(entry, key, name)
        self._attr_icon = icon
        self._attr_options = list(options)
        self._register = register
        self._options = options
        self._options_by_value = {value: option for option, value in options.items()}

    @property
    def current_option(self) -> str | None:
        value = getattr(self.coordinator.data.status, register_name(self._register))
        return self._options_by_value.get(value)

    @property
    def available(self) -> bool:
        return super().available and self.current_option is not None

    async def async_select_option(self, option: str) -> None:
        if option not in self._options:
            raise ServiceValidationError("Unsupported option")
        await self.async_write(self._register, int(self._options[option]))
