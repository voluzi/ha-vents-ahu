from unittest.mock import patch

import pytest
import voluptuous as vol
from aiovents import VentsConnectionError, VentsError
from homeassistant import config_entries, data_entry_flow

from .conftest import CONFIG, DEVICE_ID, DOMAIN


async def user_step(hass, **overrides):
    return await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={**CONFIG, **overrides},
    )


async def test_user_flow_normalizes_device_id(hass, mock_vents):
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_setup", return_value=True
    ):
        result = await user_step(hass, device_id="  Fake-1  ", name="Example Vents")
        await hass.async_block_till_done()
    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Example Vents"
    assert result["result"].unique_id == DEVICE_ID
    assert result["data"] == CONFIG
    mock_vents.__aexit__.assert_awaited_once()


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("device_id", "", "invalid_device_id"),
        ("device_id", "   ", "invalid_device_id"),
        ("device_id", "x" * 17, "invalid_device_id"),
        ("device_id", "démo", "invalid_device_id"),
        ("password", "", "invalid_password"),
        ("password", "démo", "invalid_password"),
        ("password", "x" * 256, "invalid_password"),
    ],
)
async def test_invalid_credentials_never_contact_device(
    hass, mock_vents, field, value, error
):
    result = await user_step(hass, **{field: value})
    assert result["errors"] == {field: error}
    mock_vents.async_get_status.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "key"),
    [(VentsConnectionError, "cannot_connect"), (VentsError, "unknown")],
)
async def test_connection_test_failure_is_reported(hass, mock_vents, error, key):
    mock_vents.async_get_status.side_effect = error
    result = await user_step(hass)
    assert result["errors"] == {"base": key}
    mock_vents.__aexit__.assert_awaited_once()


async def test_duplicate_normalized_id_aborts_before_contact(hass, entry, mock_vents):
    result = await user_step(hass, device_id="Fake-1", host="other.example")
    assert result["reason"] == "already_configured"
    mock_vents.async_get_status.assert_not_awaited()


async def test_reconfigure_changes_connection_but_not_identity(
    hass, entry, mock_vents, reload_entry
):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    assert result["step_id"] == "reconfigure"
    assert "device_id" not in {key.schema for key in result["data_schema"].schema}
    new_data = {"host": "other.example", "port": 4001, "password": "new-fake-password"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], new_data)
    await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == DEVICE_ID
    assert entry.data == {**CONFIG, **new_data}
    reload_entry.assert_awaited_once_with(entry.entry_id)


async def test_reconfigure_aborts_for_mismatched_stored_device_id(
    hass, entry, mock_vents
):
    hass.config_entries.async_update_entry(entry, data={**CONFIG, "device_id": "fake"})
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    assert result["reason"] == "unique_id_mismatch"
    mock_vents.async_get_status.assert_not_awaited()


@pytest.mark.parametrize(
    ("scan_interval", "settings_interval"),
    [(10, 60), (300, 3600), (9, 60), (301, 60), (10, 59), (10, 3601)],
)
async def test_options_limits_and_reload(
    hass, setup_entry, reload_entry, scan_interval, settings_interval
):
    result = await hass.config_entries.options.async_init(setup_entry.entry_id)
    options = {"scan_interval": scan_interval, "settings_interval": settings_interval}
    if 10 <= scan_interval <= 300 and 60 <= settings_interval <= 3600:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], options
        )
        await hass.async_block_till_done()
        assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
        assert setup_entry.options == options
        reload_entry.assert_awaited_once_with(setup_entry.entry_id)
    else:
        with pytest.raises(vol.Invalid):
            result["data_schema"](options)
        reload_entry.assert_not_awaited()


@pytest.mark.parametrize("password_input", [{}, {"password": ""}])
async def test_reconfigure_keeps_password_when_field_is_empty(
    hass, entry, mock_vents, reload_entry, password_input
):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    form = result["data_schema"]({"host": "other.example", "port": 4001})
    assert "password" not in form
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**form, **password_input}
    )
    await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["host"] == "other.example"
    assert entry.data["password"] == CONFIG["password"]
    mock_vents.async_get_status.assert_awaited_once()
