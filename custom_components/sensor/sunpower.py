# https://github.com/home-assistant/home-assistant/blob/master/homeassistant/components/sensor/sma.py
# https://www.home-assistant.io/components/sensor.sma/
import asyncio
import re
import requests
import logging
import voluptuous as vol
from datetime import timedelta
from datetime import datetime
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_interval
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'sunpower'
DEPENDENCIES = []

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'

# CONFIG_SCHEMA = vol.Schema({
#     DOMAIN: vol.Schema({
#       vol.Required(CONF_USERNAME): cv.string,
#       vol.Required(CONF_PASSWORD): cv.string,
#     })
# }, extra=vol.ALLOW_EXTRA)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Sunpower systems"""

    # Assign configuration variables. The configuration check takes care they are
    # present.
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    # Setup connection with devices/cloud
    sunpowerApi = SunpowerApi(username=username, password=password)
    if(sunpowerApi.authenticate()):
        sunpowerApi.updateData()
        def callUpdate(event_time):
            sunpowerApi.updateData()
        track_time_interval(hass, callUpdate, MIN_TIME_BETWEEN_UPDATES)
        # Add devices
        add_devices([
            SunpowerCurrentProductionSensor(api=sunpowerApi),
            SunpowerCurrentConsumptionSensor(api=sunpowerApi),
            SunpowerCurrentProductionEnergySensor(api=sunpowerApi),
            SunpowerCurrentConsumptionEnergySensor(api=sunpowerApi)], True)
    else:
        _LOGGER.error("Issue authenticating with Sunpower, check credentials and try again.")

class SunpowerApi():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = ''
        self.currentProduction = None
        self.currentConsumption = None
        self.currentProductionEnergy = None
        self.currentConsumptionEnergy = None

    def authenticate(self):
        data = {
          'username':self.username,
          'password':self.password,
          'isPersistent':False
        }
        authResponse = requests.post('https://monitor.us.sunpower.com/CustomerPortal/Auth/Auth.svc/Authenticate',json=data)

        authJson = authResponse.json()

        _LOGGER.debug("Authenticate:\n%s", authJson)

        # Verify that passed in configuration works
        if authJson['StatusCode'] != '200':
            return False

        self.token = authJson['Payload']['TokenID']
        # Refresh 20 minutes before our token expires
        self.refreshTime = datetime.now() + timedelta(minutes = (authJson['Payload']['ExpiresInMinutes'] - 20))
        _LOGGER.debug("Going to refresh again at %s", self.refreshTime)

        return True

    def updateData(self):
        if(self.token == ''):
            return False
        if(self.refreshTime < datetime.now()):
            _LOGGER.debug("Time to refresh token.")
            if(not self.authenticate()):
                _LOGGER.error("Issue refreshing token with Sunpower!")
                return
            else:
                _LOGGER.debug("Token refreshed!")

        response = requests.get('https://monitor.us.sunpower.com/CustomerPortal/SystemInfo/SystemInfo.svc/getRealTimeNetDisplay?id='+self.token).json()
        _LOGGER.debug("getRealTimeNetDisplay:\n%s", response)
        self.currentProduction = response['Payload']['CurrentProduction']['value']
        self.currentConsumption = response['Payload']['CurrentConsumption']['value']

        day = datetime.now().strftime('%Y-%m-%dT00:00:00')
        response = requests.get('https://monitor.us.sunpower.com/CustomerPortal/SystemInfo/SystemInfo.svc/getHourlyEnergyData?timestamp='+day+'&tokenId='+self.token).json()
        _LOGGER.debug("getHourlyEnergyData:\n%s", response)
        match = re.search('\,(?P<produced>[0-9\.]*)\,(?P<used>[0-9\.]*)\,(?P<unknown>[0-9\.]*)$', response['Payload'])
        self.currentProductionEnergy = float(match.group('produced') or 0)
        self.currentConsumptionEnergy = float(match.group('used') or 0)

    def getCurrentProduction(self):
        return self.currentProduction
    def getCurrentConsumption(self):
        return self.currentConsumption
    def getCurrentProductionEnergy(self):
        return self.currentProductionEnergy
    def getCurrentConsumptionEnergy(self):
        return self.currentConsumptionEnergy

class SunpowerCurrentProductionSensor(Entity):
    """Representation of Current Power."""

    def __init__(self, api):
        """Initialize a current production sensor."""
        self._name = 'Sunpower Current Production'
        self._sunpower = api
        self._state = None

    @property
    def name(self):
        """Return the display name of this sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._sunpower.getCurrentProduction()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'kW'

    @property
    def icon(self):
         return 'mdi:battery-charging-100'

class SunpowerCurrentConsumptionSensor(Entity):
    """Representation of Current Power."""

    def __init__(self, api):
        """Initialize a current production sensor."""
        self._name = 'Sunpower Current Consumption'
        self._sunpower = api
        self._state = None

    @property
    def name(self):
        """Return the display name of this sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._sunpower.getCurrentConsumption()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'kW'

    @property
    def icon(self):
         return 'mdi:battery-10'

class SunpowerCurrentProductionEnergySensor(Entity):
    """Representation of Current Power."""

    def __init__(self, api):
        """Initialize a current production sensor."""
        self._name = 'Sunpower Energy Production'
        self._sunpower = api
        self._state = None

    @property
    def name(self):
        """Return the display name of this sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._sunpower.getCurrentProductionEnergy()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'kWh'

    @property
    def icon(self):
         return 'mdi:battery-charging-90'

class SunpowerCurrentConsumptionEnergySensor(Entity):
    """Representation of Current Power."""

    def __init__(self, api):
        """Initialize a current production sensor."""
        self._name = 'Sunpower Energy Consumption'
        self._sunpower = api
        self._state = None

    @property
    def name(self):
        """Return the display name of this sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._sunpower.getCurrentConsumptionEnergy()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'kWh'

    @property
    def icon(self):
         return 'mdi:battery-50'
