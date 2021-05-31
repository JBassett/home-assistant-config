"""Support for plex webhooks."""
from datetime import timedelta
import json
import logging

import aiohttp
from aiohttp.web import Request, Response

from .const import (
    DOMAIN
)

from .sunpower import (
    SunPowerDataUpdateCoordinator
)

from homeassistant.const import (
    CONF_URL
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import aiohttp_client


_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup(hass, config):
    """Platform setup, do nothing."""
    return True

async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    url = entry.data[CONF_URL]
    _LOGGER.info("async_setup_entry for %s", url)

    session = aiohttp.ClientSession()
    async def async_update_data():
        async with session.get(url) as response:
            return await response.json()

    coordinator = SunPowerDataUpdateCoordinator(
        hass,
        _LOGGER,
        aiohttp_client.async_get_clientsession(hass),
        url
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN] = {
        'sunpower': coordinator
    }
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    _LOGGER.debug("setup complete")
    # Return boolean to indicate that initialization was successful.
    return True
