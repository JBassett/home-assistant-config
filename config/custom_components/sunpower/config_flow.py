import voluptuous as vol
import uuid 

from homeassistant import config_entries

from .const import (
    DOMAIN
)

from homeassistant.const import (
    CONF_URL
)


class AutpPiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, info):
        if info is not None:
            # TODO: Validate username and password
            url = info[CONF_URL]
            return self.async_create_entry(
                title = "Home Solar",
                data={
                    CONF_URL: url
                }
            )
        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema({
                vol.Required(CONF_URL): str
            })
        )
