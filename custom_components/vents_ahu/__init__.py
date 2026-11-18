"""Native local polling integration for Vents air handling units."""

from functools import partial

from aiovents import AsyncVents
from aiovents.const import DEFAULT_TIMEOUT
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, PLATFORMS
from .coordinator import VentsConfigEntry, VentsCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: VentsConfigEntry) -> bool:
    client = AsyncVents(
        entry.data[CONF_HOST],
        entry.data[CONF_DEVICE_ID],
        port=entry.data[CONF_PORT],
        password=entry.data[CONF_PASSWORD],
        timeout=DEFAULT_TIMEOUT,
    )
    ready = False
    try:
        coordinator = VentsCoordinator(hass, entry, client)
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        entry.async_on_unload(
            entry.add_update_listener(partial(_async_options_updated, entry.options))
        )
        ready = True
    finally:
        if not ready:
            await client.async_close()
    return True


async def _async_options_updated(
    previous_options: object, hass: HomeAssistant, entry: VentsConfigEntry
) -> None:
    if entry.options != previous_options:
        await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: VentsConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_shutdown()
        await entry.runtime_data.client.async_close()
        return True
    return False
