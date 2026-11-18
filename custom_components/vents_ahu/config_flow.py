"""Device setup, connection reconfiguration and polling options."""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from aiovents import AsyncVents, VentsConnectionError, VentsError, VentsValueError
from aiovents.codec import encode_password, normalize_device_id
from aiovents.const import DEFAULT_PASSWORD, DEFAULT_PORT, DEFAULT_TIMEOUT
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

if TYPE_CHECKING:
    import probatio as vol
else:
    try:
        import probatio as vol
    except ModuleNotFoundError:
        import voluptuous as vol

from .const import (
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    CONF_SETTINGS_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SETTINGS_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MAX_SETTINGS_INTERVAL,
    MIN_SCAN_INTERVAL,
    MIN_SETTINGS_INTERVAL,
)


def _connection_schema(
    defaults: Mapping[str, Any], *, reconfigure: bool = False
) -> vol.Schema:
    schema: dict[Any, Any] = {
        vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)): str,
        vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): vol.All(
            int, vol.Range(min=1, max=65535)
        ),
    }
    if not reconfigure:
        schema[vol.Required(CONF_DEVICE_ID)] = str
    password = (
        vol.Optional(CONF_PASSWORD)
        if reconfigure
        else vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD)
    )
    schema[password] = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
    if not reconfigure:
        schema[vol.Optional(CONF_NAME, default=DEFAULT_NAME)] = str
    return vol.Schema(schema)


async def _async_check_connection(data: dict[str, Any]) -> str | None:
    try:
        async with AsyncVents(
            data[CONF_HOST],
            data[CONF_DEVICE_ID],
            port=data[CONF_PORT],
            password=data[CONF_PASSWORD],
            timeout=DEFAULT_TIMEOUT,
        ) as client:
            await client.async_get_status()
    except VentsConnectionError:
        return "cannot_connect"
    except VentsError:
        return "unknown"
    return None


class VentsConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_connection_step("user", user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        return await self._async_connection_step("reconfigure", user_input, entry)

    async def _async_connection_step(
        self,
        step_id: str,
        user_input: dict[str, Any] | None,
        entry: ConfigEntry | None = None,
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if entry is not None:
            try:
                stored_id = normalize_device_id(entry.data[CONF_DEVICE_ID])
            except VentsValueError:
                return self.async_abort(reason="unique_id_mismatch")
            await self.async_set_unique_id(stored_id)
            self._abort_if_unique_id_mismatch()

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            password = user_input.get(
                CONF_PASSWORD,
                DEFAULT_PASSWORD if entry is None else entry.data[CONF_PASSWORD],
            )
            if entry is not None and password == "":
                password = entry.data[CONF_PASSWORD]
            device_id = None if entry is None else stored_id
            if entry is None:
                try:
                    device_id = normalize_device_id(user_input[CONF_DEVICE_ID].strip())
                except VentsValueError:
                    errors[CONF_DEVICE_ID] = "invalid_device_id"
            try:
                encode_password(password)
            except VentsValueError:
                errors[CONF_PASSWORD] = "invalid_password"
            if not host:
                errors[CONF_HOST] = "invalid_host"
            if (
                not isinstance(port, int)
                or isinstance(port, bool)
                or not 1 <= port <= 65535
            ):
                errors[CONF_PORT] = "invalid_port"
            if not errors:
                assert device_id is not None
                if entry is None:
                    await self.async_set_unique_id(device_id)
                    self._abort_if_unique_id_configured()
                data = {
                    CONF_HOST: host,
                    CONF_PORT: port,
                    CONF_DEVICE_ID: device_id,
                    CONF_PASSWORD: password,
                }
                if error := await _async_check_connection(data):
                    errors["base"] = error
                elif entry is not None:
                    return self.async_update_reload_and_abort(entry, data_updates=data)
                else:
                    title = (
                        user_input.get(CONF_NAME, DEFAULT_NAME).strip() or DEFAULT_NAME
                    )
                    return self.async_create_entry(title=title, data=data)

        defaults = entry.data if entry is not None else {}
        schema = _connection_schema(defaults, reconfigure=entry is not None)
        suggested = {
            key: value
            for key, value in (user_input or {}).items()
            if key != CONF_PASSWORD
        }
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return VentsOptionsFlow()


class VentsOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(
                        int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                    ),
                    vol.Required(
                        CONF_SETTINGS_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SETTINGS_INTERVAL, DEFAULT_SETTINGS_INTERVAL
                        ),
                    ): vol.All(
                        int,
                        vol.Range(min=MIN_SETTINGS_INTERVAL, max=MAX_SETTINGS_INTERVAL),
                    ),
                }
            ),
        )
