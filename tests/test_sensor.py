from dataclasses import replace

import pytest
from homeassistant.helpers import entity_registry as er


@pytest.mark.parametrize(
    ("key", "field", "value", "unit", "device_class", "state_class", "category"),
    [
        (
            "supply_in",
            "supply_in_temperature",
            -10.0,
            "°C",
            "temperature",
            "measurement",
            None,
        ),
        (
            "supply_out",
            "supply_out_temperature",
            20.0,
            "°C",
            "temperature",
            "measurement",
            None,
        ),
        (
            "exhaust_in",
            "exhaust_in_temperature",
            21.5,
            "°C",
            "temperature",
            "measurement",
            None,
        ),
        (
            "exhaust_out",
            "exhaust_out_temperature",
            5.0,
            "°C",
            "temperature",
            "measurement",
            None,
        ),
        ("humidity", "current_humidity", 45, "%", "humidity", "measurement", None),
        ("fan1_speed", "fan1_speed", 1250, "rpm", None, "measurement", None),
        ("fan2_speed", "fan2_speed", 1100, "rpm", None, "measurement", None),
        (
            "filter_days_remaining",
            "filter_days_remaining",
            30,
            "d",
            None,
            None,
            "diagnostic",
        ),
    ],
)
async def test_sensor_state_metadata_and_unavailability(
    hass,
    setup_entry,
    mock_vents,
    status,
    key,
    field,
    value,
    unit,
    device_class,
    state_class,
    category,
):
    entity_id = f"sensor.vents_ahu_{key}"
    state = hass.states.get(entity_id)
    assert float(state.state) == value
    assert state.attributes["unit_of_measurement"] == unit
    assert state.attributes.get("device_class") == device_class
    assert state.attributes.get("state_class") == state_class
    assert er.async_get(hass).async_get(entity_id).entity_category == category

    mock_vents.async_get_status.return_value = replace(status, **{field: None})
    await setup_entry.runtime_data.async_refresh()
    assert hass.states.get(entity_id).state == "unavailable"
