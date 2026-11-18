from dataclasses import replace

import pytest


@pytest.mark.parametrize(
    ("key", "field", "expected", "device_class"),
    [
        ("boost_mode", "boost_mode", "off", "running"),
        ("alarm", "alarm_indicator", "on", "problem"),
        ("filter_replacement", "filter_indicator", "off", "problem"),
    ],
)
async def test_binary_sensor_state_and_unavailability(
    hass, setup_entry, mock_vents, status, key, field, expected, device_class
):
    entity_id = f"binary_sensor.vents_ahu_{key}"
    state = hass.states.get(entity_id)
    assert state.state == expected
    assert state.attributes["device_class"] == device_class
    mock_vents.async_get_status.return_value = replace(status, **{field: None})
    await setup_entry.runtime_data.async_refresh()
    assert hass.states.get(entity_id).state == "unavailable"
