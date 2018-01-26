"""
This component wouldn't be possible without the massive amount of inspiration I got from the following scripts:
https://github.com/cyberjunky/home-assistant-custom-components/blob/master/climate/toon.py
https://github.com/rvdvoorde/domoticz-homewizard

This component is far from done yet, but it'll do for now.
"""
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from homeassistant.components.climate import (ClimateDevice, PLATFORM_SCHEMA, SUPPORT_TARGET_TEMPERATURE)
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_PASSWORD,
                                 TEMP_CELSIUS, ATTR_TEMPERATURE)
import homeassistant.helpers.config_validation as cv

import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import logging
import voluptuous as vol

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Homewizard Thermostat'
DEFAULT_TIMEOUT = 2
BASE_URL = 'http://{0}/{1}/{2}'

ATTR_MODE = 'Heating'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    add_devices([homewizard(config.get(CONF_NAME), config.get(CONF_HOST), config.get(CONF_PASSWORD))])


class homewizard(ClimateDevice):
    """Representation of a Sensor."""

    def __init__(self, name, address, password):
        """Initialize the sensor."""
        self._name = name
        self._address = address
        self._password = password
        self._current_temp = None
        self._current_setpoint = None
        self._current_state = 'off'
        _LOGGER.debug("Init called")
        self.update()

    @staticmethod
    def connect(order):
        try:
            url = Request(order)
            response = urlopen(url, timeout=DEFAULT_TIMEOUT)

        except HTTPError as e:
            _LOGGER.exception("The server couldn\'t fulfill the request. Error code: ", e.code)
            return "error"

        except URLError as e:
            _LOGGER.exception("We failed to reach a server. Reason: ", e.reason)
            return "error"

        else:
            urloutput = response.read().decode("utf-8", "ignore")
            jsonoutput = json.loads(urloutput)
            return jsonoutput

    @property
    def should_poll(self):
        """Polling needed for thermostat."""
        _LOGGER.debug("Should_Poll called")
        return True

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.debug("Update called")
        getlist = self.connect(BASE_URL.format(self._address, self._password, "get-sensors"))
        if getlist != 'error':
            heatlink = dict(getlist['response']['heatlinks'][0])
            self._current_temp = round(heatlink['rte'], 1)
            self._current_setpoint = round(heatlink['tte'], 1)
            self._current_state = heatlink['heating']
            _LOGGER.debug("Update successful")
        else:
            _LOGGER.exception("Update failed")
            

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            ATTR_MODE: self._current_state
        }

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._current_setpoint

    @property
    def current_operation(self):
        """Return the current state of the thermostat."""
        state = self._current_state
        return state

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        else:
            settemp = self.connect(BASE_URL.format(self._address, self._password, "hl/0/settarget/" + str(temperature)))
            if settemp != 'error':
                _LOGGER.debug("Set temperature=%s", str(temperature))
            else:
                _LOGGER.exception("Error setting Heatlink")
        # Not sure if needed
        # self.update()