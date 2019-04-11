# https://github.com/home-assistant/home-assistant/blob/master/homeassistant/components/sensor/sma.py
# https://www.home-assistant.io/components/sensor.sma/
import re
import requests
import logging
import voluptuous as vol
from datetime import timedelta
from datetime import datetime
from homeassistant.const import (CONF_PASSWORD, CONF_USERNAME, CONF_MONITORED_CONDITIONS)
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_interval

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'sunpower'
DEPENDENCIES = []

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

SENSORS = {
    'energyProduction': ['Sunpower Energy Production', 'energyProduction', 'kWh', 'mdi:battery-charging-90'],
    'energyConsumption': ['Sunpower Energy Consumption', 'energyConsumption', 'kWh', 'mdi:battery-50'],
    'powerProduction': ['Sunpower Power Production', 'powerProduction', 'kW', 'mdi:battery-charging-90'],
    'powerConsumption': ['Sunpower Power Consumption', 'powerConsumption', 'kW', 'mdi:battery-50']
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_MONITORED_CONDITIONS): vol.All(cv.ensure_list, [vol.In(SENSORS)])
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
        add_devices([SunpowerSensor(api=sunpowerApi, config=SENSORS[sensor]) for sensor in config.get(CONF_MONITORED_CONDITIONS)], True)
    else:
        _LOGGER.error("Issue authenticating with Sunpower, check credentials and try again.")

class SunpowerApi():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = ''
        self.energyProduction = None
        self.energyConsumption = None
        self.powerProduction = None
        self.powerConsumption = None

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

        # response = requests.get('https://monitor.us.sunpower.com/CustomerPortal/SystemInfo/SystemInfo.svc/getRealTimeNetDisplay?id='+self.token).json()
        # _LOGGER.debug("getRealTimeNetDisplay:\n%s", response)
        # self.powerProduction = response['Payload']['CurrentProduction']['value']
        # self.powerConsumption = response['Payload']['CurrentConsumption']['value']

        day = datetime.now().strftime('%Y-%m-%dT00:00:00')
        response = requests.get('https://monitor.us.sunpower.com/CustomerPortal/SystemInfo/SystemInfo.svc/getHourlyEnergyData?timestamp='+day+'&tokenId='+self.token).json()
        _LOGGER.debug("getHourlyEnergyData:\n%s", response)
        match = re.search('\,(?P<produced>[0-9\.]*)\,(?P<used>[0-9\.]*)\,(?P<unknown>[0-9\.]*)$', response['Payload'])
        if(match is not None):
            self.energyProduction = float(match.group('produced') or 0)
            self.energyConsumption = float(match.group('used') or 0)

        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00')
        response = requests.get('https://monitor.us.sunpower.com/CustomerPortal/SystemInfo/SystemInfo.svc/getEnergyData?&startDateTime='+day+'&endDateTime='+tomorrow+'&interval=minute&guid='+self.token).json()
        _LOGGER.debug("getEnergyData:\n%s", response)
        if(response['Payload'] is not None):
            self.powerProduction = 12 * response['Payload']['series']['data'][-1]['ep']
            self.powerConsumption = 12 * response['Payload']['series']['data'][-1]['eu']

class SunpowerSensor(Entity):

    def __init__(self, api, config):
        """Initialize a current production sensor."""
        self._name = config[0]
        self._stateAttribute = config[1]
        self._unit = config[2]
        self._icon = config[3]
        self._sunpower = api
        self._state = None
    @property
    def name(self):
        """Return the display name of this sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return getattr(self._sunpower, self._stateAttribute)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
         return self._icon