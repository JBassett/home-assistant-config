import logging
import datetime

from .const import DOMAIN

from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
    ATTR_BATTERY_CHARGING
)

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("async_setup_entry -> Start")
    autopi = hass.data[DOMAIN]['autopi']

    async_add_entities([
        ChargingBinarySensor(autopi),
        ConnectionBinarySensor(autopi)
        ])
    _LOGGER.debug("async_setup_entry -> Complete")

class AutopiBinarySensor(RestoreEntity, BinarySensorEntity):

    _last_state = None

    should_poll = False

    async def async_added_to_hass(self):
        self.autopi.register_callback(self.async_write_ha_state)
        state = await self.async_get_last_state()
        if state:
            self._last_state = state.state

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
            "name": "BoltyMcBoltface",
            "sw_version": "2017",
        }

class ChargingBinarySensor(AutopiBinarySensor):
    
    name = "Bolt - Charging"
    entity_id = "binary_sensor.bolt_charging"
    _attr_device_class = ATTR_BATTERY_CHARGING

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        if self.autopi.latest and 'is_charging' in self.autopi.latest:
            self._last_state = STATE_ON if self.autopi.latest['is_charging'] else STATE_OFF
        return self._last_state == STATE_ON

class ConnectionBinarySensor(AutopiBinarySensor):
    should_poll = True
    name = "Bolt - Connected"
    entity_id = "binary_sensor.bolt_connected"
    _attr_device_class = DEVICE_CLASS_CONNECTIVITY

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return (datetime.datetime.utcnow() - self.autopi.update_time) < datetime.timedelta(seconds = 30)
