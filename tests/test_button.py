from dataclasses import replace

from homeassistant.helpers import entity_registry as er


async def test_filter_reset_refreshes_filter_sensors(
    hass, setup_entry, mock_vents, status
):
    entity_id = "button.vents_ahu_reset_filter"
    assert er.async_get(hass).async_get(entity_id).entity_category == "config"

    async def reset():
        mock_vents.async_get_status.return_value = replace(
            status, filter_days_remaining=90
        )

    mock_vents.async_reset_filter.side_effect = reset
    await hass.services.async_call(
        "button", "press", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    mock_vents.async_reset_filter.assert_awaited_once()
    assert hass.states.get("sensor.vents_ahu_filter_days_remaining").state == "90"
