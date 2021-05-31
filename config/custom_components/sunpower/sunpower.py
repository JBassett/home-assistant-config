from datetime import timedelta
import aiohttp

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class SunPowerDataUpdateCoordinator(DataUpdateCoordinator):
    
    def __init__(self, hass, logger, session, url):
        self.session = session
        self.url = url
        super().__init__(hass, logger, name="SunPower", update_interval=timedelta(seconds=30))

    async def _async_update_data(self):
        data = {}
        async with self.session.get(self.url) as response:
            json = await response.json()
            for device in json["devices"]:
                data[device["SERIAL"]] = device
            return data
