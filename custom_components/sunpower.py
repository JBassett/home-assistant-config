# https://github.com/home-assistant/home-assistant/blob/master/homeassistant/components/sensor/sma.py
# https://www.home-assistant.io/components/sensor.sma/
import asyncio
import requests
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'hello_state'
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
    
    sitesResponse = requests.get('https://monitor.us.sunpower.com/CustomerPortal/SiteList/SiteList.svc/SiteList?id='+token)
    sitesJson = sitesResponse.json() # Not sure how to handle multiple sites.... soooo yeah.

    # Add devices
    for site in sitesJson.Payload:
        
        add_devices(SunpowerSensor(site) for site in sitesJson.Payload)

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
    
    def update(self):
        if(self.token == '')
            return
        
        requests.get('https://monitor.us.sunpower.com/CustomerPortal/CurrentPower/CurrentPower.svc/GetCurrentPower?id='+self.token)

class SunpowerSensor(Entity):
    """Representation of Sunpower Sensor."""

    def __init__(self, site):
        """Initialize an AwesomeLight."""
        self._light = light
        self._name = light.name
        self._state = None
        self._brightness = None

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the light.

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        self._light.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        self._light.turn_on()

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self._light.turn_off()

    def update(self):
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._light.update()
        self._state = self._light.is_on()
        self._brightness = self._light.brightness