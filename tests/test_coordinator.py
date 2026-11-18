from dataclasses import replace
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from aiovents import VentsConnectionError
from aiovents.registers import SUPPLY_FAN_SPEED_1, TARGET_TEMP
from homeassistant.exceptions import HomeAssistantError


async def test_status_failure_retries_in_cycle_and_recovers(
    hass, setup_entry, mock_vents, status
):
    coordinator = setup_entry.runtime_data
    failure = VentsConnectionError("No response")
    mock_vents.async_get_status.side_effect = [failure, failure, status]
    await coordinator.async_refresh()
    assert hass.states.get("climate.vents_ahu").state == "heat"
    mock_vents.async_get_status.side_effect = [failure] * 3
    await coordinator.async_refresh()
    assert hass.states.get("climate.vents_ahu").state == "unavailable"

    mock_vents.async_get_status.side_effect = None
    await coordinator.async_refresh()
    assert hass.states.get("climate.vents_ahu").state == "heat"


async def test_settings_failure_keeps_previous_values_and_retries_next_poll(
    hass, entry, mock_vents, settings
):
    hass.config_entries.async_update_entry(
        entry, options={"scan_interval": 20, "settings_interval": 60}
    )
    with patch(
        "custom_components.vents_ahu.coordinator.monotonic", return_value=1000
    ) as clock:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coordinator = entry.runtime_data
        assert coordinator.update_interval == timedelta(seconds=20)
        clock.return_value = 1059
        await coordinator.async_refresh()
        mock_vents.async_get_settings.assert_awaited_once()

        clock.return_value = 1060
        mock_vents.async_get_settings.side_effect = VentsConnectionError
        await coordinator.async_refresh()
        assert coordinator.last_update_success
        assert coordinator.data.settings == settings

        clock.return_value = 1080
        mock_vents.async_get_settings.side_effect = None
        mock_vents.async_get_settings.return_value = replace(
            settings, supply_fan_speed_1=35
        )
        await coordinator.async_refresh()
        assert coordinator.data.settings.supply_fan_speed_1 == 35


async def test_confirmed_values_are_published_before_refresh(
    hass, setup_entry, mock_vents
):
    coordinator = setup_entry.runtime_data
    mock_vents.async_write_register.side_effect = [21, 38]

    observed = []

    async def observe_refresh():
        observed.append(
            (
                float(hass.states.get("number.vents_ahu_target_temp").state),
                float(hass.states.get("number.vents_ahu_supply_fan_speed_1").state),
            )
        )

    with patch.object(
        coordinator, "async_request_refresh", AsyncMock(side_effect=observe_refresh)
    ):
        await coordinator.async_write(TARGET_TEMP, 21)
        await coordinator.async_write(SUPPLY_FAN_SPEED_1, 38)
    assert observed == [(21, 25), (21, 38)]
    assert coordinator.data.settings.exhaust_fan_speed_1 == 30


async def test_unconfirmed_write_fails_without_updating_state(
    hass, setup_entry, mock_vents
):
    mock_vents.async_write_register.return_value = 23

    with pytest.raises(HomeAssistantError) as error:
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.vents_ahu_target_temp", "value": 24},
            blocking=True,
        )

    assert error.value.translation_key == "command_failed"
    assert float(hass.states.get("number.vents_ahu_target_temp").state) == 22
