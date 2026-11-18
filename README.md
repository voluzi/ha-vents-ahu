# Vents AHU for Home Assistant

Control a compatible Vents or Blauberg air handling unit directly from Home Assistant over local
UDP. Requires Home Assistant 2025.4.4 or later. The integration uses the unit's Vents AHU protocol.

## Installation

After `aiovents==0.1.0` and the integration have been released, add `voluzi/ha-vents-ahu` to HACS
as a custom repository of type **Integration**. Download **Vents AHU** and restart Home
Assistant. Then go to **Settings → Devices & services → Add integration → Vents AHU**.

Enter the host, UDP port (4000 by default), device ID, and the unit's password. The optional name
defaults to **Vents AHU**. IDs shorter than 16 ASCII characters are padded on the right with
zeroes. An incorrect device ID or password can appear as a connection timeout.

Use **Reconfigure** to change the host, port, or password without changing entity identity. Leave
the password field empty to keep the current password. Under **Configure**, set the status poll
to 10–300 seconds (default 10) and the fan settings poll to 60–3600 seconds (default 300).

## Entities

- **Climate**: power, operating mode, fan speed, and a whole temperature setpoint from 15 to 30 °C.
  It reports `off` when powered off and powers on when a running HVAC mode is selected. The
  climate card uses the exhaust-in temperature and current humidity.
- **Selects and numbers**: separate operating mode, fan mode, and target temperature controls;
  six supply and exhaust fan speed settings (0–100%).
- **Sensors**: four air temperatures in °C, humidity in %, two fan speeds in rpm, and filter
  days remaining. The air temperature sensors retain one decimal place.
- **Binary sensors**: boost mode, alarm, and filter replacement.
- **Reset filter**: press after replacing the filter. The device does not acknowledge the
  command, so check the countdown and replacement indicator after the next poll.

An unsupported value is shown as unavailable on its entity. If the device cannot be reached,
the integration retries the status poll before marking the entities unavailable.

## Migrating from the MQTT bridge

1. Export the old entity IDs from the Home Assistant entity registry. Review automations,
   scripts, scenes, and dashboards for references. The registry is the source of truth for
   renamed entities and area prefixes.
2. Install the native integration alongside the bridge. Compare readings and controls, check
   availability and recovery, and test the filter reset only when replacement is due.
3. Find references to the old power switch before removing it. Change actions to
   `climate.turn_on` and `climate.turn_off` targeting the native climate entity. Update any
   switch state triggers or conditions to account for climate states, including `off` and
   `unavailable`.
4. Stop the bridge, then clear its retained MQTT discovery messages using the exact topics
   recorded for that device. Delete the old MQTT device so its entity IDs are free. Keep the
   bridge deployment configuration available for rollback.
5. Rename native entities to match the exported IDs where there is an equivalent. You can
   first give the native device the old device name and use **Recreate entity IDs**; compare the
   result to the export and fix renamed or area-prefixed IDs by hand. Check Developer Tools →
   Statistics for any conflicts and verify the updated automations and dashboards.

To roll back, free the reused IDs by removing or renaming the native entities and restore the
bridge deployment. The bridge republishes its MQTT discovery messages. Compare the resulting
entities against the inventory.

## Local development

The integration test workflow installs `aiovents==0.1.0` from PyPI. That version has not
been published yet, so run the tests with the local library checkout for now.

With the sibling `aiovents` checkout available, use Python 3.13:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements_test.txt -e ../aiovents
ruff check .
ruff format --check .
mypy --strict custom_components
pytest -q --disable-socket --allow-unix-socket
```

The test harness loads the integration with a fake client. CI also checks the minimum supported
Home Assistant version, hassfest, and HACS metadata.

MIT license.
