import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor import DEVICE_CLASS_CONNECTIVITY

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("async_setup_entry -> Start")
    bryx_ws = hass.data[DOMAIN]['ws']
    async_add_entities([
        BryxConnection(bryx_ws),
        BryxOpenJob(bryx_ws)
        ])
    _LOGGER.debug("async_setup_entry -> Complete")

class BryxConnection(BinarySensorEntity):
    name = "Bryx Connected"
    device_class = DEVICE_CLASS_CONNECTIVITY

    def __init__(self, ws):
        self.entity_id = "binary_sensor.bryx_connection"
        self.ws = ws

    @property
    def unique_id(self):
        return f"{self.entity_id}"

    @property
    def is_on(self):
        return self.ws.ws_client != None and not self.ws.ws_client.closed
    
    async def async_update(self):
        await self.ws.ping()

    async def async_added_to_hass(self):
        _LOGGER.debug("BryxOpenJob -> added")
        self.ws.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self.ws.remove_callback(self.async_write_ha_state)

class BryxOpenJob(BinarySensorEntity):
    should_poll = False
    name = "Bryx Open Job"

    def __init__(self, ws):
        self.entity_id = "binary_sensor.bryx_open_job"
        self.ws = ws

    @property
    def unique_id(self):
        return f"{self.entity_id}"

    @property
    def is_on(self):
        return self.ws.latest is not None and self.ws.latest.get("open", False)

    async def async_added_to_hass(self):
        _LOGGER.debug("BryxOpenJob -> added")
        self.ws.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self.ws.remove_callback(self.async_write_ha_state)
