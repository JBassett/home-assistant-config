import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_API_KEY
)


class BryxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, info):
        if info is not None:
            api_key = info[CONF_API_KEY]
            return self.async_create_entry(
                title = api_key,
                data={CONF_API_KEY: api_key}
            )
        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str})
        )
