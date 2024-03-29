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
from datetime import (
    datetime,
    timedelta
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    TYPE_UPDATE_PUSH,
    TYPE_JOB_SUB,
    TYPE_JOB_UNSUB,
    TYPE_ACK,
    TYPE_INITAL_JOBS,
    CONF_USER,
    CONF_PASS,
    CONF_DEVICE_ID
)

_LOGGER = logging.getLogger(__package__)

class BryxWebsocket:
    def __init__(self, username, password, device_id):
        self._running = False
        self._username = username
        self._password = password
        self._api_key = None
        self._device_id = device_id
        self._callbacks = set()
        self._watched_job_id = None

        self.session = aiohttp.ClientSession()
        self.ws_client = None
        self._message_id = 0
        self.latest = None
        self.jobs = {}
        self.registered_jobs = []
        self.responders = {}
        self.supplementals = {}
    
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
                    await self.ws_client.send_json(request)
                    _LOGGER.debug("start -> inital request sent")

                    await self.receiveMessages()

            except Exception as error:
                _LOGGER.exception("Unexpected exception occurred: %s", error)

        _LOGGER.debug("listen -> Finish")

    def close(self):
        self._running = False

    @property
    def message_id(self):
        self._message_id = self._message_id + 1
        if(self._message_id > 100000):
            self._message_id = 0
        return self._message_id

    async def ping(self):
        if self.ws_client == None:
            _LOGGER.error("Trying to ping a dead websocket!")
            return
        request = {
            "id" : self.message_id,
            "type" : 8
        }
        await self.ws_client.send_json(request)
    
    async def ack(self, ack_id):
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
                    _LOGGER.warn("Issue handling message! %s \nMessage: %s", sys.exc_info()[0], message.data)

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
        
        try:
            if msg.get("type") == TYPE_INITAL_JOBS:
                if msg.get("topic") == "jobs":
                    # Initial jobs load
                    if not msg["initialData"]["open"]:
                        await self.handle_job_update(msg["initialData"]["closed"][0])
                    else:
                        await self.handle_job_update(msg["initialData"]["open"][0])
                    for j in msg["initialData"]["open"]:
                        await self.handle_job_update(j)
                    for j in msg["initialData"]["closed"]:
                        await self.handle_job_update(j)
                elif msg.get("topic").startswith("jobs/"):
                    await self.handle_job_update(msg.get("initialData"))
            elif msg.get("type") == TYPE_UPDATE_PUSH:
                _LOGGER.debug("Got job push: %s", msg)
                topic = msg.get("topic") 
                if topic == "jobs":
                    # Got a job update
                    await self.ack(msg["data"].get("id"))
                    await self.handle_job_update(msg["data"].get("job"))
                elif topic.startswith("jobs/") and msg.get("data").get("type") == "responders":
                    # Responder update (no ack)
                    self.update_responders(topic.replace("jobs/",""), msg["data"]["responders"])
                elif topic.startswith("jobs/") and msg.get("data").get("type") == "supplementals":
                    # Supplemental Update (no ack)
                    pass
            else:
                _LOGGER.debug("Got message: %s", msg)
        except:
            _LOGGER.exception(f"Unable to handle message: {msg}")

    async def handle_job_update(self, job_update):
        if job_update is None:
            _LOGGER.warn("Trying to add a None job!")
            return

        job_id = job_update["id"]
        job = self.jobs.get(job_id, {})

        job["id"] = job_id

        if job.get("start") is None:
            job["start"] = datetime.fromtimestamp(job_update.get("ts"))

        if job.get("end") is None:
            job["end"] = job["start"] + timedelta(hours=1)
        
        job["open"] = job_update.get("disposition") != "closed" # or job_id == "622bd69216d1570c1bb03309" or job_id == "622b802664511c55d1d523e3"

        if job.get("address") is None:
            job["address"] = job_update.get("address", {}).get("original")

        if job.get("gps") is None or len(job.get("gps")) != 2:
            job["gps"] = job_update.get("centroid", {}).get("coordinates")

        if job.get("synopsis") is None:
            job["synopsis"] = job_update.get("synopsis")
        
        if job.get("type") is None:
            job["type"] = job_update.get("type", {}).get("description")
        
        if job_id not in self.responders and job_update.get("responders") is not None:
            self.update_responders(job_id, job_update.get("responders"))

        if job_id not in self.supplementals and job_update.get("supplementals") is not None:
            self.update_supplementals(job_id, job_update.get("supplementals"))

        self.jobs[job_id] = job
        
        if self.latest is None or self.latest.get("start") < job.get("start"):
            _LOGGER.debug(f"New Latest Job: {job}")
            self.latest = job
        
        if job["open"] and job_id not in self.registered_jobs:
            # Register for job updates
            _LOGGER.debug(f"Subscribing to job: {job_id}")
            request = {
                "type": TYPE_JOB_SUB,
                "topic" : f"jobs/{job_id}",
                "id" : self.message_id,
                "params" : {},
                "version" : 1
            }
            await self.ws_client.send_json(request)
            self.registered_jobs.append(job_id)
        elif not job["open"] and job_id in self.registered_jobs:
            # Unregister for job updates
            _LOGGER.debug(f"Unsubscribing to job: {job_id}")
            request = {
                "type": TYPE_JOB_UNSUB,
                "topic" : f"jobs/{job_id}",
                "id" : self.message_id,
                "params" : {},
                "version" : 1
            }
            await self.ws_client.send_json(request)
            self.registered_jobs.remove(job_id)
            if job_id in self.responders:
                del self.responders[job_id]
            if job_id in self.supplementals:
                del self.supplementals[job_id]

    def update_responders(self, job_id, inc_responders):
        # [{
		# 	"id": "1234",
		# 	"name": "John Doe",
		# 	"phone": "123",
		# 	"currentResponse": {
		# 		"ts": 1647018043,
		# 		"responseOption": {
		# 			"id": "1234",
		# 			"text": "No",
		# 			"type": "negative"
		# 		}
		# 	},
		# 	"isMe": false
		# }]
        self.responders[job_id] = {}
        for responder in inc_responders:
            response = responder.get("currentResponse").get("responseOption").get("text").lower().replace(" ", "_")    
            if response not in self.responders[job_id]:
                self.responders[job_id][response] = []
            self.responders[job_id][response].append(responder)
        pass
        
    def update_supplementals(self, job_id, supplementals):
        self.supplementals[job_id] = []
        for sup in supplementals:
            self.supplementals[job_id].append(sup.get("text"))

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
    websocket = BryxWebsocket(entry.data[CONF_USER], entry.data[CONF_PASS], entry.data[CONF_DEVICE_ID])
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
    # Calendar currently broken and I have no time...
    # hass.async_create_task(
    #     hass.config_entries.async_forward_entry_setup(entry, "calendar")
    # )

    _LOGGER.debug("setup complete")
    # Return boolean to indicate that initialization was successful.
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info("async_unload_entry -> Begin for user: %s", entry.data[CONF_USER])

    binary = await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")
    sensor = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    calendar = await hass.config_entries.async_forward_entry_unload(entry, "calendar")

    _LOGGER.info("async_unload_entry -> Complete for user: %s", entry.data[CONF_USER])
    return binary and sensor and calendar
