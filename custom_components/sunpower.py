# https://github.com/home-assistant/home-assistant/blob/master/homeassistant/components/sensor/sma.py
# https://www.home-assistant.io/components/sensor.sma/
import asyncio
import requests
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'sunpower'
DEPENDENCIES = []

CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
      vol.Required(CONF_USERNAME): cv.string,
      vol.Required(CONF_PASSWORD): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

@asyncio.coroutine
def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Sunpower systems"""

    # Assign configuration variables. The configuration check takes care they are
    # present.
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    # Setup connection with devices/cloud
    sunpowerApi = SunpowerApi()
    if(sunpowerApi.authenticate()):
        # Add devices
        add_devices([SunpowerSensor(sunpowerApi)])

class SunpowerApi():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = ''

    def authenticate(self):
        authResponse = requests.post('https://monitor.us.sunpower.com/CustomerPortal/Auth/Auth.svc/Authenticate',
          data = {
            "username":username,
            "password":password,
            "isPersistent":false
          })

        authJson = authResponse.json()

        # Verify that passed in configuration works
        if authJson.StatusCode != 200:
            return false

        self.token = authJson.Payload.TokenID

        return true

    def getCurrentPower(self):
        if(self.token == ''):
            return None

        return requests.get('https://monitor.us.sunpower.com/CustomerPortal/CurrentPower/CurrentPower.svc/GetCurrentPower?id='+self.token).json().Payload.CurrentProduction

class SunpowerSensor(Entity):
    """Representation of Sunpower Sensor."""

    def __init__(self, sp):
        """Initialize a current power Sunpower."""
        self._name = 'Current Power'
        self._sunpower = sp
        self._state = None

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._station_data.get(ATTR_FREE_BIKES, None)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'kW'

    def update(self):
        """
        Fetch new state data for this entity.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self.sunpower.getCurrentPower()
