import logging

from .const import DOMAIN

from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_VOLTAGE
)

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("async_setup_entry -> Start")
    autopi = hass.data[DOMAIN]['autopi']

    async_add_entities([
        StateOfChargeSensor(autopi),
        SpeedSensor(autopi),
        BatteryTempSensor(autopi),
        ExternalTempSensor(autopi),
        PiVoltageSensor(autopi),
        ShifterSensor(autopi),
        PowerSensor(autopi),
        VoltageSensor(autopi),
        CurrentSensor(autopi)
        ])
    _LOGGER.debug("async_setup_entry -> Complete")

class AutopiSensor(RestoreEntity):

    _last_state = None

    should_poll = False

    async def async_added_to_hass(self):
        self.autopi.register_callback(self.async_write_ha_state)
        state = await self.async_get_last_state()
        if state:
            self._last_state = state.state

    async def async_will_remove_from_hass(self):
        self.autopi.remove_callback(self.async_write_ha_state)
    
    @property
    def unique_id(self):
        """Return the unique ID of this sensor."""
        return f"{self.autopi.webhook_id} - {self.entity_id}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.autopi.webhook_id)},
            "manufacturer": "Chevrolet",
            "model": "Bolt",
            "device_name": "BoltyMcBoltface",
            "name": "BoltyMcBoltface",
            "sw_version": "2017",
        }

class StateOfChargeSensor(AutopiSensor):
    
    name = "Bolt - State of Charge"
    entity_id = "sensor.bolt_soc"
    device_class = DEVICE_CLASS_BATTERY
    unit_of_measurement = "%"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'soc' in self.autopi.latest:
            self._last_state = self.autopi.latest['soc']
        return self._last_state

class SpeedSensor(AutopiSensor):
    
    name = "Bolt - Speed"
    entity_id = "sensor.bolt_speed"
    unit_of_measurement = "mph"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'speed' in self.autopi.latest:
            self._last_state = round(self.autopi.latest['speed'] / 1.609344)
        return self._last_state

class BatteryTempSensor(AutopiSensor):
    
    name = "Bolt - Battery Temperature"
    entity_id = "sensor.bolt_battery_temp"
    device_class = DEVICE_CLASS_TEMPERATURE
    unit_of_measurement = "°C"

    def __init__(self, autopi):
        self.autopi = autopi
    
    async def async_added_to_hass(self):
        await AutopiSensor.async_added_to_hass(self)
        if self._last_state:
            self._last_state = round((float(self._last_state) - 32 ) * (5/9), 2)

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'battery_temp' in self.autopi.latest:
            self._last_state = self.autopi.latest['battery_temp']
        return self._last_state

class ExternalTempSensor(AutopiSensor):
    
    name = "Bolt - External Temperature"
    entity_id = "sensor.bolt_external_temp"
    device_class = DEVICE_CLASS_TEMPERATURE
    unit_of_measurement = "°C"

    def __init__(self, autopi):
        self.autopi = autopi
    
    async def async_added_to_hass(self):
        await AutopiSensor.async_added_to_hass(self)
        if self._last_state:
            self._last_state = round((float(self._last_state) - 32 ) * (5/9), 2)

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'external_temp' in self.autopi.latest:
            self._last_state = self.autopi.latest['external_temp']
        return self._last_state

class PiVoltageSensor(AutopiSensor):
    
    name = "Bolt - Pi Voltage"
    entity_id = "sensor.bolt_pi_voltage"
    device_class = DEVICE_CLASS_VOLTAGE
    unit_of_measurement = "V"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'pi_voltage' in self.autopi.latest:
            self._last_state = self.autopi.latest['pi_voltage']
        return self._last_state

class ShifterSensor(AutopiSensor):
    
    shifter_pos = {
        1: "Low",
        3: "Drive",
        6: "Neutral",
        7: "Reverse",
        8: "Park"
    }

    name = "Bolt - Shifter Position"
    entity_id = "sensor.bolt_shifter"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'shifter' in self.autopi.latest:
            self._last_state = self.shifter_pos.get(self.autopi.latest['shifter'], "Unknown")
        return self._last_state

class PowerSensor(AutopiSensor):
    
    name = "Bolt - Power"
    entity_id = "sensor.bolt_power"
    device_class = DEVICE_CLASS_POWER
    unit_of_measurement = "kW"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'power' in self.autopi.latest:
            self._last_state = self.autopi.latest['power']
        return self._last_state

class VoltageSensor(AutopiSensor):
    
    name = "Bolt - Voltage"
    entity_id = "sensor.bolt_voltage"
    device_class = DEVICE_CLASS_VOLTAGE
    unit_of_measurement = "V"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'voltage' in self.autopi.latest:
            self._last_state = self.autopi.latest['voltage']
        return self._last_state

class CurrentSensor(AutopiSensor):
    
    name = "Bolt - Current"
    entity_id = "sensor.bolt_current"
    device_class = DEVICE_CLASS_CURRENT
    unit_of_measurement = "A"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'current' in self.autopi.latest:
            self._last_state = self.autopi.latest['current']
        return self._last_state
