"""Reset the filter replacement countdown and clear the associated alarm."""

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VentsConfigEntry
from .entity import VentsEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VentsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([VentsFilterReset(entry)])


class VentsFilterReset(VentsEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:air-filter"

    def __init__(self, entry: VentsConfigEntry) -> None:
        super().__init__(entry, "reset_filter", "Reset filter")

    async def async_press(self) -> None:
        await self.coordinator.async_reset_filter()
