"""Poll status and settings at separate intervals and publish confirmed writes."""

import asyncio
import logging
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from time import monotonic

from aiovents import (
    AsyncVents,
    Mode,
    Register,
    RegisterValue,
    VentsError,
    VentsSettings,
    VentsStatus,
    VentsValueError,
)
from aiovents.codec import register_name
from aiovents.models import SETTINGS_REGISTERS
from aiovents.registers import MODE, POWER_ON
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SETTINGS_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SETTINGS_INTERVAL,
    DOMAIN,
    RETRY_DELAY,
    STATUS_READ_ATTEMPTS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VentsData:
    status: VentsStatus
    settings: VentsSettings | None


class VentsCoordinator(DataUpdateCoordinator[VentsData]):
    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: AsyncVents
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
            always_update=False,
        )
        self.client = client
        self._io_lock = asyncio.Lock()
        self._settings_interval = entry.options.get(
            CONF_SETTINGS_INTERVAL, DEFAULT_SETTINGS_INTERVAL
        )
        self._next_settings = 0.0
        self.last_settings_read: datetime | None = None

    async def _async_read_status(self) -> VentsStatus:
        for _ in range(STATUS_READ_ATTEMPTS - 1):
            try:
                return await self.client.async_get_status()
            except VentsError:
                await asyncio.sleep(RETRY_DELAY)
        try:
            return await self.client.async_get_status()
        except VentsError as exc:
            raise UpdateFailed("Unable to read Vents AHU status") from exc

    async def _async_update_data(self) -> VentsData:
        async with self._io_lock:
            status = await self._async_read_status()
            settings = self.data.settings if self.data is not None else None
            now = monotonic()
            if now >= self._next_settings:
                try:
                    settings = await self.client.async_get_settings()
                except VentsError as exc:
                    _LOGGER.warning("Unable to read Vents AHU settings: %s", exc)
                else:
                    self._next_settings = now + self._settings_interval
                    self.last_settings_read = datetime.now(UTC)
            return VentsData(status, settings)

    async def _async_write_locked(self, reg: Register, value: RegisterValue) -> None:
        try:
            confirmed = await self.client.async_write_register(reg, value)
        except VentsValueError as exc:
            raise ServiceValidationError(str(exc)) from exc
        except VentsError as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="command_failed"
            ) from exc

        if confirmed != value:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="command_failed"
            )

        data = self.data
        values = {register_name(reg): confirmed}
        if reg in SETTINGS_REGISTERS:
            data = replace(
                data, settings=(data.settings or VentsSettings()).updated(values)
            )
        else:
            data = replace(data, status=data.status.updated(values))
        self.async_set_updated_data(data)

    async def async_write(self, reg: Register, value: RegisterValue) -> None:
        async with self._io_lock:
            await self._async_write_locked(reg, value)
        await self.async_request_refresh()

    async def async_set_mode(self, mode: Mode) -> None:
        async with self._io_lock:
            await self._async_write_locked(MODE, int(mode))
            if self.data.status.power_on is False:
                await self._async_write_locked(POWER_ON, True)
        await self.async_request_refresh()

    async def async_reset_filter(self) -> None:
        async with self._io_lock:
            try:
                await self.client.async_reset_filter()
            except VentsError as exc:
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="command_failed"
                ) from exc
        await self.async_request_refresh()


type VentsConfigEntry = ConfigEntry[VentsCoordinator]
