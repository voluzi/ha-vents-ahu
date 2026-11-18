import pytest
from aiovents import VentsConnectionError, VentsValueError
from aiovents.registers import EXHAUST_FAN_SPEED_2, TARGET_TEMP
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er


@pytest.mark.parametrize(
    (
        "key",
        "current",
        "value",
        "register",
        "unit",
        "device_class",
        "category",
        "limits",
    ),
    [
        ("target_temp", 22, 25, TARGET_TEMP, "°C", "temperature", None, (15, 30)),
        (
            "exhaust_fan_speed_2",
            50,
            55,
            EXHAUST_FAN_SPEED_2,
            "%",
            None,
            "config",
            (0, 100),
        ),
    ],
)
async def test_number_metadata_and_command(
    hass,
    setup_entry,
    mock_vents,
    key,
    current,
    value,
    register,
    unit,
    device_class,
    category,
    limits,
):
    entity_id = f"number.vents_ahu_{key}"
    state = hass.states.get(entity_id)
    assert float(state.state) == current
    assert state.attributes["unit_of_measurement"] == unit
    assert state.attributes.get("device_class") == device_class
    assert (state.attributes["min"], state.attributes["max"]) == limits
    assert state.attributes["step"] == 1
    assert er.async_get(hass).async_get(entity_id).entity_category == category
    mock_vents.async_write_register.return_value = value
    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": value}, blocking=True
    )
    mock_vents.async_write_register.assert_awaited_once_with(register, value)


async def test_missing_settings_only_disable_settings_entities(hass, entry, mock_vents):
    mock_vents.async_get_settings.side_effect = VentsConnectionError
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("number.vents_ahu_supply_fan_speed_1").state == "unavailable"
    assert float(hass.states.get("number.vents_ahu_target_temp").state) == 22


@pytest.mark.parametrize(
    ("device_error", "service_error"),
    [
        (VentsValueError, ServiceValidationError),
        (VentsConnectionError, HomeAssistantError),
    ],
)
async def test_device_errors_are_reported_to_service_caller(
    hass, setup_entry, mock_vents, device_error, service_error
):
    mock_vents.async_write_register.side_effect = device_error("Rejected")
    with pytest.raises(service_error) as error:
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.vents_ahu_target_temp", "value": 24},
            blocking=True,
        )
    assert type(error.value) is service_error


async def test_fractional_value_does_not_send_write(hass, setup_entry, mock_vents):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.vents_ahu_exhaust_fan_speed_2", "value": 24.5},
            blocking=True,
        )
    mock_vents.async_write_register.assert_not_awaited()
