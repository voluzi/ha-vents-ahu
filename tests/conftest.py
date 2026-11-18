from importlib.util import find_spec
from unittest.mock import AsyncMock, patch

import pytest
from aiovents import FanSpeed, Mode, VentsSettings, VentsStatus

from custom_components.vents_ahu.const import DOMAIN

DEVICE_ID = "Fake-10000000000"
CONFIG = {
    "host": "vents-ahu.example",
    "port": 4000,
    "device_id": DEVICE_ID,
    "password": "fake-password",
}

if find_spec("pytest_homeassistant"):
    from pytest_homeassistant.common import MockConfigEntry
else:
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def custom_integration(enable_custom_integrations):
    yield


@pytest.fixture
def status():
    return VentsStatus(
        power_on=True,
        mode=Mode.HEATING,
        speed=FanSpeed.MEDIUM,
        target_temp=22,
        supply_in_temperature=-10.0,
        supply_out_temperature=20.0,
        exhaust_in_temperature=21.5,
        exhaust_out_temperature=5.0,
        current_humidity=45,
        fan1_speed=1250,
        fan2_speed=1100,
        boost_mode=False,
        alarm_indicator=True,
        filter_indicator=False,
        filter_days_remaining=30,
    )


@pytest.fixture
def settings():
    return VentsSettings(25, 45, 65, 30, 50, 70)


@pytest.fixture
def mock_vents(status, settings):
    with patch("custom_components.vents_ahu.AsyncVents", autospec=True) as factory:
        client = factory.return_value
        client.async_get_status.return_value = status
        client.async_get_settings.return_value = settings
        client.__aenter__.return_value = client
        with patch("custom_components.vents_ahu.config_flow.AsyncVents", factory):
            yield client


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, title="Vents AHU", unique_id=DEVICE_ID, data=CONFIG
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def reload_entry():
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload",
        new_callable=AsyncMock,
    ) as reload:
        yield reload


@pytest.fixture
async def setup_entry(hass, entry, mock_vents):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
