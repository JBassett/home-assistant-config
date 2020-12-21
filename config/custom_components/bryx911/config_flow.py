import voluptuous as vol
import uuid 

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_USER,
    CONF_PASS,
    CONF_DEVICE_ID
)


class BryxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, info):
        if info is not None:
            # TODO: Validate username and password
            username = info[CONF_USER]
            password = info[CONF_PASS]
            device_id = info[CONF_DEVICE_ID]
            return self.async_create_entry(
                title = username,
                data={
                    CONF_USER: username,
                    CONF_PASS: password,
                    CONF_DEVICE_ID: device_id
                }
            )
        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema({
                vol.Required(CONF_USER): str,
                vol.Required(CONF_PASS): str,
                vol.Required(CONF_DEVICE_ID, default=str(uuid.uuid1())): str
            })
        )
