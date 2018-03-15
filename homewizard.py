from homeassistant.components.climate import (ClimateDevice, PLATFORM_SCHEMA, SUPPORT_TARGET_TEMPERATURE, STATE_AUTO)
from homeassistant.const import (CONF_HOST, CONF_PASSWORD, TEMP_CELSIUS, ATTR_TEMPERATURE)
import homeassistant.helpers.config_validation as cv

import requests
import json
import logging
import voluptuous as vol

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15
BASE_URL = 'http://{0}/{1}/{2}'

ATTR_PUMP = 'pump'
ATTR_DHW = 'dhw'
ATTR_WATER_TEMP = 'water_temperature'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Heatlink thermostat."""
    _LOGGER.debug("Heatlink config: %s" % config)

    add_devices(
        [Heatlink(config.get(CONF_HOST), config.get(CONF_PASSWORD))],
        True
    )

    return True

class Heatlink(ClimateDevice):
    """Representation of a Heatlink thermostat."""
    def __init__(self, hostname, password):
        """Setup Homewizard details"""
        self._hostname = hostname
        self._password = password

        """Initialize the thermostat."""
        self._name = 'Heatlink'
        self._current_temperature = None
        self._target_temperature = None
        self._pump = None
        self._dhw = None
        self._heating = None
        self._water_temperature = None

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def name(self):
        """Return the name of the heatlink, if any."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def current_operation(self):
        """Return the current state of the thermostat."""
        return STATE_AUTO

    @staticmethod
    def _call_client(url):
        """Call the Homewizard API"""
        try:
            client = requests.get(url, timeout=DEFAULT_TIMEOUT)
        except:
            _LOGGER.error("Error calling client: %s", client.status_code)
            return False

        return json.loads(client.text)

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._call_client(BASE_URL.format(
            self._hostname, 
            self._password, 
            'hl/0/settarget/' + str(temperature)
        ))

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            ATTR_PUMP: (self._pump and 'on' or 'off'),
            ATTR_DHW: (self._dhw and 'on' or 'off'),
            ATTR_WATER_TEMP: self._water_temperature,
        }

    def _refresh(self):
        """Refresh the state attributes."""
        attributes = self._call_client(BASE_URL.format(
            self._hostname, 
            self._password, 
            'get-sensors'
        ))
        response = attributes['response']['heatlinks'][0];

        self._name = response['name']
        self._current_temperature = round(response['rte'], 1)
        self._pump = response['pump']
        self._dhw = response['dhw']
        self._heating = response['heating']
        self._water_temperature = round(response['wte'], 1)

        tte = round(response['tte'], 1)
        rsp =  round(response['rsp'], 1)

        if int(tte) is 0:
            self._target_temperature = rsp
        else:
            self._target_temperature = tte

        return True

    def update(self):
        """Update the state."""
        retries = 3
        while retries > 0:
            try:
                self._refresh()
                break
            except (OSError,
                    requests.exceptions.ReadTimeout) as exp:
                retries -= 1
                if retries == 0:
                    raise exp
                if not self._retry():
                    raise exp
                _LOGGER.error("Heatlink update failed, Retrying - Error: %s", exp)

    def _retry(self):
        """Retry to update state"""
        try:
            self._refresh()
        except:
            return False
       
        return True
