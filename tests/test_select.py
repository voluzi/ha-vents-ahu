from dataclasses import replace

import pytest
from aiovents.registers import MODE, SPEED


@pytest.mark.parametrize(
    ("key", "field", "initial", "option", "register", "code"),
    [
        ("mode", "mode", "heat", "fan_only", MODE, 0),
        ("fan_mode", "speed", "medium", "low", SPEED, 1),
    ],
)
async def test_select_value_command_and_unavailability(
    hass, setup_entry, mock_vents, status, key, field, initial, option, register, code
):
    entity_id = f"select.vents_ahu_{key}"
    assert hass.states.get(entity_id).state == initial
    mock_vents.async_write_register.return_value = code
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": option},
        blocking=True,
    )
    mock_vents.async_write_register.assert_awaited_once_with(register, code)
    mock_vents.async_get_status.return_value = replace(status, **{field: None})
    await setup_entry.runtime_data.async_refresh()
    assert hass.states.get(entity_id).state == "unavailable"
