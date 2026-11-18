# Vents AHU for Home Assistant

[![Marketplace and HACS: custom repository](https://img.shields.io/badge/Marketplace%20%2F%20HACS-custom%20repository-41BDF5)](#installation)
[![Latest GitHub release](https://img.shields.io/github/v/release/voluzi/ha-vents-ahu)](https://github.com/voluzi/ha-vents-ahu/releases/latest)
[![Tests](https://github.com/voluzi/ha-vents-ahu/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/voluzi/ha-vents-ahu/actions/workflows/test.yml)
[![Validation](https://github.com/voluzi/ha-vents-ahu/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/voluzi/ha-vents-ahu/actions/workflows/validate.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Control a compatible Vents or Blauberg air handling unit from Home Assistant
over your local network. Change ventilation settings, monitor temperatures and
humidity, and track when the filter needs replacing.

## Features

- Climate control with power, operating mode, fan speed, and temperature setpoint.
- Separate controls for operating mode, fan mode, and the six fan speed settings.
- Temperature, humidity, fan rotation, alarm, boost, and filter monitoring.

## Compatibility

Vents and Blauberg units are supported when their controller exposes the local
Vents AHU UDP register protocol. Look for that protocol on the exact controller
and firmware; models with a different control board or protocol are outside the
supported scope. A model name alone does not establish compatibility.

The integration requires Home Assistant **2025.4.4 or later** and uses
[`aiovents`](https://github.com/voluzi/aiovents) to communicate with the unit.
UDP defaults to port 4000. The protocol sends the device ID and password over
the local network without encryption.

## Installation

**Marketplace (Home Assistant 2026.11 or later)**

1. In **Settings → Marketplace**, select **Add from link** in the upper right.
   If prompted, connect your GitHub account. This adds the project as a
   [custom repository](https://www.home-assistant.io/integrations/marketplace/#custom-repositories).
2. Enter `https://github.com/voluzi/ha-vents-ahu`, select **Add**, and choose
   **Integration** if asked for a type.
3. Open **Vents AHU** and select **Install**. If setup does not open, go to
   **Settings → Devices & services → Add integration** and search for **Vents AHU**.
   Restart Home Assistant if prompted.

On an earlier supported Home Assistant version, add the same URL in
**HACS → Custom repositories** as an **Integration**, install it, then restart.

**Manual install**

1. Download `vents_ahu.zip` from the [latest release](https://github.com/voluzi/ha-vents-ahu/releases/latest)
   and extract it into `custom_components/vents_ahu/` under your Home Assistant
   configuration directory. If using the release source archive, copy its
   `custom_components/vents_ahu/` directory instead. The manifest should end up
   at `custom_components/vents_ahu/manifest.json`.
2. Restart Home Assistant and add **Vents AHU** in **Settings → Devices & services**.
   Home Assistant installs the Python dependency automatically.

## Configuration

| Field | What to enter |
| --- | --- |
| Host | The unit's local hostname or IP address |
| UDP port | The unit's UDP port; default 4000 |
| Device ID | The unit's ID, 1–16 ASCII characters; short IDs are padded on the right with zeroes |
| Password | The unit's configured password |
| Name | Optional display name; default **Vents AHU** |

Use **Reconfigure** to change the host, port, or password while keeping the
same device and entities. Leave the password blank to keep the current one.

Under **Configure**, the status poll defaults to 10 seconds (range 10–300)
and the fan settings poll defaults to 300 seconds (range 60–3600).

## Entities

Names below are shown without the device name prefix. The climate entity
uses the device name.

| Platform | Name | Description | Unit |
| --- | --- | --- | --- |
| Climate | Vents AHU | Power, operating mode, fan speed and setpoint; displays exhaust-in temperature and humidity | °C, % |
| Select | Mode | Auto, cool, heat, or fan only | — |
| Select | Fan mode | Low, medium, or high | — |
| Number | Target temp | Target temperature, 15–30 in whole degrees | °C |
| Number | Supply fan speed 1 | Low supply fan speed setting | % |
| Number | Supply fan speed 2 | Medium supply fan speed setting | % |
| Number | Supply fan speed 3 | High supply fan speed setting | % |
| Number | Exhaust fan speed 1 | Low exhaust fan speed setting | % |
| Number | Exhaust fan speed 2 | Medium exhaust fan speed setting | % |
| Number | Exhaust fan speed 3 | High exhaust fan speed setting | % |
| Sensor | Supply in | Incoming supply air temperature | °C |
| Sensor | Supply out | Outgoing supply air temperature | °C |
| Sensor | Exhaust in | Incoming exhaust air temperature | °C |
| Sensor | Exhaust out | Outgoing exhaust air temperature | °C |
| Sensor | Humidity | Current relative humidity | % |
| Sensor | Fan1 speed | Measured fan 1 rotation speed | rpm |
| Sensor | Fan2 speed | Measured fan 2 rotation speed | rpm |
| Sensor | Filter days remaining | Time until filter replacement is due | days |
| Binary sensor | Boost mode | Whether boost is active | — |
| Binary sensor | Alarm | Whether an alarm is active | — |
| Binary sensor | Filter replacement | Whether the filter needs replacing | — |
| Button | Reset filter | Reset the maintenance counter after replacing the filter | — |

## Actions

Use the standard Home Assistant actions; there are no integration-specific
actions. The climate entity supports `climate.turn_on`, `climate.turn_off`,
`climate.set_hvac_mode`, `climate.set_fan_mode`, and `climate.set_temperature`.
Selecting an operating mode on the climate entity also powers the unit on if
it is off. Use `select.select_option` for the select entities and
`number.set_value` for the setpoint or fan percentages (0–100 in whole steps).
Use `button.press` to reset the filter counter after replacing the filter.

## Diagnostics and troubleshooting

In **Settings → Devices & services**, open the integration entry's menu and
select **Download diagnostics**. The download includes status, settings, and
the timestamp of the last successful fan settings read. It redacts the host,
password, and device ID. Review the file and remove any remaining private
information before sharing it.

- **Setup times out:** Check the address, UDP port, device ID, and password.
  Incorrect credentials can look like an unreachable unit. Confirm that UDP
  traffic can pass between Home Assistant and the unit.
- **Entities become unavailable:** The integration attempts each status poll
  up to three times. A successful poll restores communication; entities whose
  register values are unsupported can remain unavailable.
- **The filter reset did not seem to work:** The unit does not acknowledge
  the reset. Check **Filter days remaining** and **Filter replacement** after
  the next poll.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local checks and [CHANGELOG.md](CHANGELOG.md)
for release notes. Report vulnerabilities privately as described in
[SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE).
