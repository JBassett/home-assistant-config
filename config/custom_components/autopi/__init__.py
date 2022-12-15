"""Support for plex webhooks."""
import json
import logging

import aiohttp
from aiohttp.web import Request, Response

from .const import (
    DOMAIN
)

from .autopi import (
    Autopi
)

from homeassistant.const import (
    CONF_NAME,
    CONF_WEBHOOK_ID
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS = "sensor", "binary_sensor", "device_tracker"

async def handle_webhook(hass, webhook_id, request):
    """Handle webhook callback."""
    _LOGGER.debug('Got Autopi webhook.')

    data = {}
    
    try:
        data = await request.json()
    except ValueError:
        _LOGGER.warn('Issue decoding webhook: ' + part.text())
        return Response(status=400)
    
    hass.data[DOMAIN]['autopi'].update(data)
    _LOGGER.debug(hass.data[DOMAIN]['autopi'].latest)

    return Response(status=200)

async def async_setup(hass, config):
    """Platform setup, do nothing."""
    return True

async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    name = entry.data[CONF_NAME]
    webhook_id = entry.data[CONF_WEBHOOK_ID]
    _LOGGER.info("async_setup_entry for %s with webhook(%s)", name, webhook_id)

    autopi = Autopi(webhook_id)

    hass.data[DOMAIN] = {
        'autopi': autopi
    }
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    hass.components.webhook.async_register(
        DOMAIN, f"AutoPi: {name}", webhook_id, handle_webhook
    )

    _LOGGER.debug("setup complete")
    # Return boolean to indicate that initialization was successful.
    return True

# Temps are converting when restoring
# Location not restoring
