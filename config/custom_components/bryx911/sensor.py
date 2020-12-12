import logging
from datetime import datetime

from homeassistant.const import (
    DEVICE_CLASS_TIMESTAMP
)
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("async_setup_entry -> Start")
    bryx_ws = hass.data[DOMAIN]['ws']
    async_add_entities([
        CurrentJobSynopsis(bryx_ws),
        CurrentJobAddress(bryx_ws),
        CurrentJobType(bryx_ws),
        LatestJobTime(bryx_ws)
        ])
    _LOGGER.debug("async_setup_entry -> Complete")

class BryxSensor(Entity):

    should_poll = False

    async def async_added_to_hass(self):
        self.ws.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self.ws.remove_callback(self.async_write_ha_state)

    def has_job(self) -> bool:
        return self.ws.last_job_update.get('disposition', 'closed') != 'closed'

class CurrentJobSynopsis(BryxSensor):
    
    name = "Bryx Current Job Synopsis"
    
    def __init__(self, ws):
        self.entity_id = "sensor.bryx_current_job_synopsis"
        self.ws = ws
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.has_job():
            return self.ws.last_job_update.get('synopsis')
        return None

class CurrentJobAddress(BryxSensor):
    
    name = "Bryx Current Job Address"
    
    def __init__(self, ws):
        self.entity_id = "sensor.bryx_current_job_address"
        self.ws = ws
    
    @property
    def device_state_attributes(self):
        lj = self.ws.last_job_update
        if self.has_job() and lj.get('centroid') is not None:
            return {
                "gps": lj['centroid'].get('coordinates')
            }
        return {}

    @property
    def state(self):
        lj = self.ws.last_job_update
        if self.has_job() and lj.get('address') is not None:
            return lj['address'].get('original')
        return None

class CurrentJobType(BryxSensor):
    
    name = "Bryx Current Job Type"
    
    def __init__(self, ws):
        self.entity_id = "sensor.bryx_current_job_type"
        self.ws = ws
    
    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        if self.has_job() and self.ws.last_job_update.get('type') is not None:
            return {
                "code": self.ws.last_job_update['type'].get('code'),
                "section": self.ws.last_job_update['type'].get('section')
            }
        return {}

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.has_job():
            return self.ws.last_job_update.get('type', {}).get('description')
        return None

class LatestJobTime(BryxSensor):
    name = "Bryx Latest Job Timestamp"
    device_class = DEVICE_CLASS_TIMESTAMP

    def __init__(self, ws):
        self.entity_id = "sensor.bryx_latest_job_time"
        self.ws = ws
    
    @property
    def device_state_attributes(self):
        return {
            "timestamp": self.ws.last_job_update.get('ts')
        }

    @property
    def state(self):
        ts = self.ws.last_job_update.get('ts')
        return None if ts is None else datetime.fromtimestamp(ts).isoformat()
