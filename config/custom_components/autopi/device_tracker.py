import logging

from .const import DOMAIN

from homeassistant.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_LATITUDE,
    ATTR_LONGITUDE
)

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker import (
    ATTR_BATTERY,
    ATTR_GPS,
    ATTR_GPS_ACCURACY,
    ATTR_LOCATION_NAME,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("async_setup_entry -> Start")
    autopi = hass.data[DOMAIN]['autopi']

    async_add_entities([
        DeviceTrackerSensor(autopi)
        ])
    _LOGGER.debug("async_setup_entry -> Complete")

class DeviceTrackerSensor(RestoreEntity, TrackerEntity):

    _last_state_attr = {}

    should_poll = False

    name = "Bolt"
    entity_id = "device_tracker.bolt"

    def __init__(self, autopi):
        self.autopi = autopi

    async def async_added_to_hass(self):
        self.autopi.register_callback(self.async_write_ha_state)
        state = await self.async_get_last_state()
        if state:
            self._last_state_attr = state.attributes
            self._last_lat = state.attributes.get('latitude')
            self._last_lon = state.attributes.get('longitude')

    async def async_will_remove_from_hass(self):
        self.autopi.remove_callback(self.async_write_ha_state)
    
    @property
    def unique_id(self):
        """Return the unique ID of this sensor."""
        return f"{self.autopi.webhook_id} - {self.entity_id}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.autopi.webhook_id)},
            "manufacturer": "Chevrolet",
            "model": "Bolt",
            "device_name": "BoltyMcBoltface",
            "sw_version": "2017",
        }

    @property
    def device_state_attributes(self):
        """Return device specific attributes."""
        attrs = {
            "latitude": self.latitude,
            "longitude": self.longitude
        }
        return attrs

    @property
    def latitude(self):
        """Return latitude value of the device."""
        if self.autopi.latest and 'lat' in self.autopi.latest:
            self._last_lat = self.autopi.latest['lat']
        return self._last_lat

    @property
    def longitude(self):
        """Return longitude value of the device."""
        if self.autopi.latest and 'lon' in self.autopi.latest:
            self._last_lon = self.autopi.latest['lon']
        return self._last_lon

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS
