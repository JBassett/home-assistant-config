"""Support for interacting with Eve Online's API"""
from datetime import timedelta
import logging
import random

import voluptuous as vol

from homeassistant.components.http import HomeAssistantView
from homeassistant.const import (CONF_NAME, CONF_FILENAME)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['esipy==v1.0.0']

_LOGGER = logging.getLogger(__name__)

AUTH_CALLBACK_NAME = 'api:eve_online'
AUTH_CALLBACK_PATH = '/api/eve_online'

CONF_CLIENT_ID = 'client_id'
CONF_CLIENT_SECRET = 'client_secret'

CONFIGURATOR_DESCRIPTION = 'To link your Eve Online account, ' \
                           'click the link, login, and authorize:'
CONFIGURATOR_LINK_NAME = 'Link Eve Online account'
CONFIGURATOR_SUBMIT_CAPTION = 'I authorized successfully'

DEFAULT_CACHE_PATH = '.eve-online-token-cache'
DEFAULT_NAME = 'Eve Online'
DOMAIN = 'eve_online'

ICON = 'mdi:space-invaders'

SCAN_INTERVAL = timedelta(seconds=30)

SCOPE = 'esi-skills.read_skillqueue.v1'

DOMAIN = 'eve_online'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_CLIENT_SECRET): cv.string
    })
})

def request_configuration(hass, config, add_entities, security):
    """Request Eve Online authorization."""
    configurator = hass.components.configurator
    hass.data[DOMAIN] = configurator.request_config(
        DEFAULT_NAME, lambda _: None,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=security.get_auth_uri(scopes=SCOPE),
        description=CONFIGURATOR_DESCRIPTION,
        submit_caption=CONFIGURATOR_SUBMIT_CAPTION)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Eve Online platform."""
    from esipy import EsiSecurity
    from esipy.cache import FileCache
    from esipy import EsiApp
    from esipy import EsiClient

    callback_url = '{}{}'.format(hass.config.api.base_url, AUTH_CALLBACK_PATH)

    # creating the security object using the app
    security = EsiSecurity(
        redirect_uri=callback_url,
        client_id=config.get(CONF_CLIENT_ID),
        secret_key=config.get(CONF_CLIENT_SECRET),
        cache=FileCache(path=hass.config.path(filename)), #TODO: Make me configurable
    )

    is_token_expired = security.is_token_expired()
    if is_token_expired:
        _LOGGER.info("no token; requesting authorization")
        hass.http.register_view(EveOnlineAuthCallbackView(config, add_entities, security))
        request_configuration(hass, config, add_entities, security)
        return
    if hass.data.get(DOMAIN):
        configurator = hass.components.configurator
        configurator.request_done(hass.data.get(DOMAIN))
        del hass.data[DOMAIN]

    _LOGGER.info('Successfully Authenticated')
    _LOGGER.debug(security.verify())

    #TODO: add actual sensors!
    # get_characters_character_id_skillqueue
    # https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/spotify/media_player.py
    # https://kyria.github.io/EsiPy/
    
    # we get the character informations
    cdata = security.verify()

    esi_app = EsiApp()
    app = esi_app.get_latest_swagger

    client = EsiClient(
        security=security
    )

    skill_queue = app.op['get_characters_character_id_skillqueue'](
        character_id='BLA'
    )

    response = client.request(skill_queue)
    _LOGGER.debug(response)


class EveOnlineAuthCallbackView(HomeAssistantView):
    """Eve Online Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME

    def __init__(self, config, add_entities, security):
        """Initialize."""
        self.config = config
        self.add_entities = add_entities
        self.security = security

    @callback
    def get(self, request):
        """Receive authorization token."""
        hass = request.app['hass']
        self.security.auth(request.query['code'])
        hass.async_add_job(setup_platform, hass, self.config, self.add_entities)

