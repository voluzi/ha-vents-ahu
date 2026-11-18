from aiovents import VentsConnectionError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er

from .conftest import DEVICE_ID


async def test_registry_contract_and_unload(hass, setup_entry, mock_vents):
    entities = er.async_entries_for_config_entry(
        er.async_get(hass), setup_entry.entry_id
    )
    assert {item.entity_id: item.unique_id for item in entities} == {
        "climate.vents_ahu": f"{DEVICE_ID}_climate",
        **{
            f"{platform}.vents_ahu_{key}": f"{DEVICE_ID}_{key}"
            for platform, keys in {
                "binary_sensor": ("boost_mode", "alarm", "filter_replacement"),
                "button": ("reset_filter",),
                "select": ("mode", "fan_mode"),
                "number": (
                    "target_temp",
                    "supply_fan_speed_1",
                    "supply_fan_speed_2",
                    "supply_fan_speed_3",
                    "exhaust_fan_speed_1",
                    "exhaust_fan_speed_2",
                    "exhaust_fan_speed_3",
                ),
                "sensor": (
                    "supply_in",
                    "supply_out",
                    "exhaust_in",
                    "exhaust_out",
                    "humidity",
                    "fan1_speed",
                    "fan2_speed",
                    "filter_days_remaining",
                ),
            }.items()
            for key in keys
        },
    }
    assert len({item.device_id for item in entities}) == 1
    assert entities[0].device_id is not None
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    assert setup_entry.state is ConfigEntryState.NOT_LOADED
    mock_vents.async_close.assert_awaited_once()
    assert await hass.config_entries.async_setup(setup_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("climate.vents_ahu").state == "heat"


async def test_initial_failure_retries_and_closes_transport(hass, entry, mock_vents):
    mock_vents.async_get_status.side_effect = VentsConnectionError
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert mock_vents.async_get_status.await_count == 3
    mock_vents.async_close.assert_awaited_once()
