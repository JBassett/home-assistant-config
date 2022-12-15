import voluptuous as vol
import uuid 

from homeassistant import config_entries

from .const import (
    DOMAIN
)

from homeassistant.const import (
    CONF_NAME,
    CONF_WEBHOOK_ID
)


class AutpPiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, info):
        if info is not None:
            # TODO: Validate username and password
            name = info[CONF_NAME]
            webhook_id = info[CONF_WEBHOOK_ID]
            return self.async_create_entry(
                title = name,
                data={
                    CONF_NAME: name,
                    CONF_WEBHOOK_ID: webhook_id
                }
            )
        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_WEBHOOK_ID, default=str(uuid.uuid4())): str
            })
        )
