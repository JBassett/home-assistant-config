"""Bryx 911 support"""
import aiohttp
import asyncio
import functools
from functools import partial
import json
import logging
import sys
import uuid 

import requests.exceptions
from time import sleep

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    TYPE_UPDATE_PUSH,
    TYPE_ACK,
    TYPE_INITAL_JOBS,
    CONF_USER,
    CONF_PASS
)

_LOGGER = logging.getLogger(__package__)

# https://github.com/jjlawren/python-plexwebsocket/blob/master/plexwebsocket.py
# https://docs.aiohttp.org/en/stable/client_quickstart.html#websockets
class BryxWebsocket:
    def __init__(self, username, password):
        self._running = False
        self._username = username
        self._password = password
        self._api_key = None
        self._device_id = str(uuid.uuid1())

        self.session = aiohttp.ClientSession()
        self.ws_client = None
        self._callbacks = set()
        self.message_id = 0
        self.last_job_update = {}
        self.jobs = {}
    
    async def login(self):
        _LOGGER.debug('login -> Begin')
        async with self.session.post(
            "https://bryx911.com/api/2.2/authorization/",
            json = {
                'email': self._username,
                'password': self._password,
                'deviceId': self._device_id,
                'deviceName': 'Home Assistant',
                'canUseForLocation': False
            }
        ) as resp:
            json_response = await resp.json()
            _LOGGER.debug("Auth response: %s", json_response)
            self._api_key = json_response['apiKey']
            _LOGGER.info("Using apiKey: %s", self._api_key)
        _LOGGER.debug("login -> Finish")

    async def listen(self):
        _LOGGER.debug("listen -> Begin")
        self._running = True
        while self._running:
            try:
                await self.login()
                async with self.session.ws_connect(
                    f"wss://bryx911.com/api/2.2/ws?apiKey={self._api_key}",
                    heartbeat=15
                ) as ws:
                    self.ws_client = ws
                    request = {
                        "type": 0,
                        "topic" : "jobs",
                        "id" : self.message_id,
                        "params" : {
                            "fastForwardMode" : "reset"
                        },
                        "version" : 0
                    }
                    self.message_id = self.message_id + 1
                    await self.ws_client.send_json(request)
                    _LOGGER.debug("start -> inital request sent")

                    await self.receiveMessages()

            except Exception as error:
                _LOGGER.exception("Unexpected exception occurred: %s", error)

        _LOGGER.debug("listen -> Finish")

    def close(self):
        self._running = False

    async def ping(self):
        if self.ws_client == None:
            _LOGGER.error("Trying to ping a dead websocket!")
            return
        self.message_id = self.message_id + 1
        request = {
            "id" : self.message_id,
            "type" : 8
        }
        await self.ws_client.send_json(request)
    
    async def ack(self, ack_id):
        self.message_id = self.message_id + 1
        request = {
            "id": self.message_id,
            "type": TYPE_ACK,
            "topic": "jobs",
            "data": {
                "type": "ack",
                "updateIds": [ack_id]
            }
        }
        await self.ws_client.send_json(request)

    async def receiveMessages(self):
        while self.ws_client != None:
            message = await self.ws_client.receive()
            if message.type == aiohttp.WSMsgType.TEXT:
                try:
                    await self.handleMessage(message)
                except:
                    _LOGGER.warn("Issue handling message! %s", sys.exc_info()[0])

            elif message.type == aiohttp.WSMsgType.CLOSED:
                _LOGGER.warning("AIOHTTP websocket connection closed")
                self.ws_client = None
                break

            elif message.type == aiohttp.WSMsgType.ERROR:
                _LOGGER.error("AIOHTTP websocket error")
                self.ws_client = None
                break

            for callback in self._callbacks:
                callback()

    async def handleMessage(self, message):
        msg = message.json()
        if msg.get("topic") == "jobs":
            job = None
            if msg.get("type") == TYPE_UPDATE_PUSH:
                _LOGGER.info("Got push: %s", msg)
                job = msg["data"].get("job")
                await self.ack(msg["data"].get("id"))
            elif msg.get("type") == TYPE_INITAL_JOBS:
                try:
                    if not msg["initialData"]["open"]:
                        job = msg["initialData"]["closed"][0]
                    else:
                        job = msg["initialData"]["open"][0]
                        for j in msg["initialData"]["open"]:
                            self.jobs[j["id"]] = j
                except Exception as error:
                    _LOGGER.warn("Unable to get last job: %s", error)
                    job = None
            
            if job != None:
                self.last_job_update = job
                
                if job["disposition"] != "closed":
                    self.jobs[job["id"]] = job
                elif job["id"] in self.jobs:
                    del self.jobs[job["id"]]
        else:
            _LOGGER.debug("Got message: %s", msg)

    def register_callback(self, callback):
        """Register callback, called when job changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

async def async_setup(hass, config):
    """Platform setup, do nothing."""
    return True

async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    _LOGGER.info("async_setup_entry for user: %s", entry.data[CONF_USER])
    websocket = BryxWebsocket(entry.data[CONF_USER], entry.data[CONF_PASS])
    hass.data[DOMAIN] = {
        'ws': websocket
    }

    hass.loop.create_task(websocket.listen())
    
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    _LOGGER.debug("setup complete")
    # Return boolean to indicate that initialization was successful.
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info("async_unload_entry -> Begin for user: %s", entry.data[CONF_USER])

    binary = await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")
    sensor = await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    _LOGGER.info("async_unload_entry -> Complete for user: %s", entry.data[CONF_USER])
    return binary and sensor
