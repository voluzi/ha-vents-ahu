"""Integration constants and option mappings."""

from aiovents import FanSpeed, Mode
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import Platform

DOMAIN = "vents_ahu"
DEFAULT_NAME = "Vents AHU"
CONF_DEVICE_ID = "device_id"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 10
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 300

CONF_SETTINGS_INTERVAL = "settings_interval"
DEFAULT_SETTINGS_INTERVAL = 300
MIN_SETTINGS_INTERVAL = 60
MAX_SETTINGS_INTERVAL = 3600

STATUS_READ_ATTEMPTS = 3
RETRY_DELAY = 0.08

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

MODE_BY_OPTION = {
    HVACMode.AUTO: Mode.AUTO,
    HVACMode.COOL: Mode.COOLING,
    HVACMode.HEAT: Mode.HEATING,
    HVACMode.FAN_ONLY: Mode.VENTILATION,
}
OPTION_BY_MODE = {mode: option for option, mode in MODE_BY_OPTION.items()}
SPEED_BY_OPTION = {
    "low": FanSpeed.LOW,
    "medium": FanSpeed.MEDIUM,
    "high": FanSpeed.HIGH,
}
OPTION_BY_SPEED = {speed: option for option, speed in SPEED_BY_OPTION.items()}
