import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_USER,
    CONF_PASS
)


class BryxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, info):
        if info is not None:
            # TODO: Validate username and password
            username = info[CONF_USER]
            password = info[CONF_PASS]
            return self.async_create_entry(
                title = username,
                data={
                    CONF_USER: username,
                    CONF_PASS: password
                }
            )
        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema({
                vol.Required(CONF_USER): str,
                vol.Required(CONF_PASS): str
            })
        )
