"""Diagnostics with connection credentials and device identity removed."""

from dataclasses import asdict
from enum import IntEnum
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID
from .coordinator import VentsConfigEntry

TO_REDACT = {CONF_HOST, CONF_PASSWORD, CONF_DEVICE_ID, "unique_id"}


def _serialize(items: list[tuple[str, Any]]) -> dict[str, Any]:
    return {
        key: value.name if isinstance(value, IntEnum) else value for key, value in items
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: VentsConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    last_read = coordinator.last_settings_read
    return {
        "entry": async_redact_data(
            {
                "data": entry.data,
                "options": entry.options,
                "unique_id": entry.unique_id,
            },
            TO_REDACT,
        ),
        "last_update_success": coordinator.last_update_success,
        "last_settings_read": last_read.isoformat() if last_read is not None else None,
        "data": asdict(coordinator.data, dict_factory=_serialize),
    }
