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
        latest = self.ws.latest
        return latest is not None and latest.get("open", True)

class CurrentJobSynopsis(BryxSensor):
    
    name = "Bryx Current Job Synopsis"
    
    def __init__(self, ws):
        self.entity_id = "sensor.bryx_current_job_synopsis"
        self.ws = ws
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.has_job():
            return self.ws.latest.get('synopsis')
        return None

class CurrentJobAddress(BryxSensor):
    
    name = "Bryx Current Job Address"
    
    def __init__(self, ws):
        self.entity_id = "sensor.bryx_current_job_address"
        self.ws = ws
    
    @property
    def device_state_attributes(self):
        lj = self.ws.latest
        if self.has_job() and lj.get("gps") is not None:
            return {
                "gps": lj.get("gps")
            }
        return {}

    @property
    def state(self):
        lj = self.ws.latest
        if self.has_job():
            return lj.get("address")
        return None

class CurrentJobType(BryxSensor):
    
    name = "Bryx Current Job Type"
    
    def __init__(self, ws):
        self.entity_id = "sensor.bryx_current_job_type"
        self.ws = ws

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.has_job():
            return self.ws.latest.get('type')
        return None

class LatestJobTime(BryxSensor):
    name = "Bryx Latest Job Timestamp"
    device_class = DEVICE_CLASS_TIMESTAMP

    def __init__(self, ws):
        self.entity_id = "sensor.bryx_latest_job_time"
        self.ws = ws
    
    @property
    def device_state_attributes(self):
        latest = self.ws.latest
        if latest is None or latest.get("start") is None:
            return None

        return {
            "timestamp": latest["start"].timestamp()
        }

    @property
    def state(self):
        latest = self.ws.latest
        if latest is None or latest.get("start") is None:
            return None

        return latest["start"].isoformat()
