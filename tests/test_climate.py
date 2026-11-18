from dataclasses import replace
from unittest.mock import call

import pytest
from aiovents import Mode
from aiovents.registers import MODE, POWER_ON, SPEED, TARGET_TEMP
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

ENTITY = {"entity_id": "climate.vents_ahu"}


async def command(hass, service, **data):
    await hass.services.async_call(
        "climate", service, {**ENTITY, **data}, blocking=True
    )


@pytest.mark.parametrize(
    ("power", "mode", "expected"),
    [
        (True, Mode.COOLING, "cool"),
        (True, Mode.AUTO, "auto"),
        (True, Mode.VENTILATION, "fan_only"),
        (False, None, "off"),
        (None, Mode.HEATING, "unavailable"),
        (True, None, "unavailable"),
    ],
)
async def test_climate_state_and_availability(
    hass, setup_entry, mock_vents, status, power, mode, expected
):
    mock_vents.async_get_status.return_value = replace(
        status, power_on=power, mode=mode
    )
    await setup_entry.runtime_data.async_refresh()
    state = hass.states.get(ENTITY["entity_id"])
    assert state.state == expected
    if expected != "unavailable":
        assert state.attributes["current_temperature"] == 21.5
        assert state.attributes["current_humidity"] == 45
        assert state.attributes["temperature"] == 22
        assert state.attributes["target_temp_step"] == 1
        assert state.attributes["fan_mode"] == "medium"


async def test_mode_command_sets_mode_then_powers_up(
    hass, setup_entry, mock_vents, status
):
    mock_vents.async_get_status.return_value = replace(status, power_on=False)
    await setup_entry.runtime_data.async_refresh()
    mock_vents.async_write_register.side_effect = [Mode.COOLING, True]
    await command(hass, "set_hvac_mode", hvac_mode="cool")
    assert mock_vents.async_write_register.await_args_list == [
        call(MODE, 2),
        call(POWER_ON, True),
    ]


async def test_mode_change_while_on_and_power_commands(hass, setup_entry, mock_vents):
    mock_vents.async_write_register.side_effect = [Mode.AUTO, False, True]
    await command(hass, "set_hvac_mode", hvac_mode="auto")
    await command(hass, "set_hvac_mode", hvac_mode="off")
    await command(hass, "turn_on")
    assert mock_vents.async_write_register.await_args_list == [
        call(MODE, 3),
        call(POWER_ON, False),
        call(POWER_ON, True),
    ]


async def test_fan_and_whole_temperature_commands(hass, setup_entry, mock_vents):
    mock_vents.async_write_register.side_effect = [3, 24]
    await command(hass, "set_fan_mode", fan_mode="high")
    await command(hass, "set_temperature", temperature=24)
    with pytest.raises(ServiceValidationError) as error:
        await command(hass, "set_temperature", temperature=24.5)
    assert error.value.translation_key == "whole_temperature_required"
    assert mock_vents.async_write_register.await_args_list == [
        call(SPEED, 3),
        call(TARGET_TEMP, 24),
    ]


@pytest.mark.parametrize(("fahrenheit", "celsius"), [(74, 23), (75, 24)])
async def test_climate_rounds_converted_setpoint(
    hass, setup_entry, mock_vents, fahrenheit, celsius
):
    hass.config.units = US_CUSTOMARY_SYSTEM
    mock_vents.async_write_register.return_value = celsius
    await command(hass, "set_temperature", temperature=fahrenheit)
    mock_vents.async_write_register.assert_awaited_once_with(TARGET_TEMP, celsius)
