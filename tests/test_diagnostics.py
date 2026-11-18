import json

from custom_components.vents_ahu.diagnostics import async_get_config_entry_diagnostics

from .conftest import CONFIG


async def test_diagnostics_redacts_connection_details_and_preserves_state(
    hass, setup_entry
):
    diagnostics = await async_get_config_entry_diagnostics(hass, setup_entry)
    encoded = json.dumps(diagnostics)
    for key in ("host", "password", "device_id"):
        assert CONFIG[key] not in encoded
    assert diagnostics["last_update_success"]
    assert diagnostics["last_settings_read"]
    assert diagnostics["data"]["status"]["mode"] == "HEATING"
    assert diagnostics["data"]["status"]["speed"] == "MEDIUM"
    assert diagnostics["data"]["settings"]["supply_fan_speed_1"] == 25
