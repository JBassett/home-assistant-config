import logging
from datetime import (
    datetime,
    timedelta
)

from homeassistant.const import (
    DEVICE_CLASS_TIMESTAMP
)

from homeassistant.components.calendar import (
    ENTITY_ID_FORMAT,
    CalendarEventDevice,
    calculate_offset,
    is_offset_reached,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__package__)

async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("calendar.async_setup_entry -> Start")
    bryx_ws = hass.data[DOMAIN]['ws']
    async_add_entities([
        BryxCalendarEventDevice(bryx_ws)
        ])
    _LOGGER.debug("calendar.async_setup_entry -> Complete")

class BryxCalendarEventDevice(CalendarEventDevice):
    def __init__(self, ws):
        self._ws = ws

    def to_event(self, job):
        return {
            "start": {"dateTime": job["start"].isoformat()},
            "end": {"dateTime": job["end"].isoformat()},
            "summary": job.get("type") + " - " + job.get("synopsis"),
            "location": job.get("address"),
            "description": job.get("synopsis")
        }

    @property
    def name(self):
        """Return the name of the entity."""
        return "Bryx911 Jobs"

    @property
    def event(self):
        """Return the next upcoming event."""
        if self._ws.latest is not None:
            return self.to_event(self._ws.latest)
        return None

    async def async_get_events(self, hass, start_date, end_date):
        """Return calendar events within a datetime range."""
        events = []
        for job_id in self._ws.jobs:
            job = self._ws.jobs[job_id]
            events.append(self.to_event(job))
        return events
    
    async def async_added_to_hass(self):
        self._ws.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._ws.remove_callback(self.async_write_ha_state)
