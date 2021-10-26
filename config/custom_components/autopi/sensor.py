import logging

from .const import DOMAIN

from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_VOLTAGE,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_SIGNAL_STRENGTH
)
from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    SensorEntity
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("async_setup_entry -> Start")
    autopi = hass.data[DOMAIN]['autopi']

    sensors = [
        StateOfChargeSensor(autopi),
        SpeedSensor(autopi),
        BatteryTempSensor(autopi),
        ExternalTempSensor(autopi),
        PiVoltageSensor(autopi),
        ShifterSensor(autopi),
        PowerSensor(autopi),
        VoltageSensor(autopi),
        CurrentSensor(autopi),
        BatteryCapacitySensor(autopi),
        BatteryCoolantSpeedSensor(autopi),
        BatteryCoolantTempSensor(autopi),
        BatteryHeaterPowerSensor(autopi),
        CabinAcPowerSensor(autopi),
        CabinHeaterPowerSensor(autopi),
        Rssi(autopi),
        CellVoltageSensor(autopi, 'avg')
    ]
    for cell_num in range(1, 97):
        sensors.append(CellVoltageSensor(autopi, str(cell_num)))

    async_add_entities(sensors)
    _LOGGER.debug("async_setup_entry -> Complete")

class AutopiSensor(SensorEntity, RestoreEntity):

    _last_state = None

    _attr_should_poll = False
    _attr_state_class = STATE_CLASS_MEASUREMENT

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
    
    _attr_name = "Bolt - State of Charge"
    entity_id = "sensor.bolt_soc"
    _attr_device_class = DEVICE_CLASS_BATTERY
    _attr_native_unit_of_measurement = "%"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'soc' in self.autopi.latest:
            self._last_state = self.autopi.latest['soc']
        return self._last_state

class SpeedSensor(AutopiSensor):
    
    _attr_name = "Bolt - Speed"
    entity_id = "sensor.bolt_speed"
    _attr_native_unit_of_measurement = "mph"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'speed' in self.autopi.latest:
            self._last_state = round(self.autopi.latest['speed'] / 1.609344)
        return self._last_state

class BatteryTempSensor(AutopiSensor):
    
    _attr_name = "Bolt - Battery Temperature"
    entity_id = "sensor.bolt_battery_temp"
    _attr_device_class = DEVICE_CLASS_TEMPERATURE
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, autopi):
        self.autopi = autopi

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'battery_temp' in self.autopi.latest:
            self._last_state = self.autopi.latest['battery_temp']
        return self._last_state

class ExternalTempSensor(AutopiSensor):
    
    _attr_name = "Bolt - External Temperature"
    entity_id = "sensor.bolt_external_temp"
    _attr_device_class = DEVICE_CLASS_TEMPERATURE
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, autopi):
        self.autopi = autopi

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'external_temp' in self.autopi.latest:
            self._last_state = self.autopi.latest['external_temp']
        return self._last_state

class PiVoltageSensor(AutopiSensor):
    
    _attr_name = "Bolt - Pi Voltage"
    entity_id = "sensor.bolt_pi_voltage"
    _attr_device_class = DEVICE_CLASS_VOLTAGE
    _attr_native_unit_of_measurement = "V"

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

    _attr_name = "Bolt - Shifter Position"
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
    
    _attr_name = "Bolt - Power"
    entity_id = "sensor.bolt_power"
    _attr_device_class = DEVICE_CLASS_POWER
    _attr_native_unit_of_measurement = "kW"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'power' in self.autopi.latest:
            self._last_state = self.autopi.latest['power']
        return self._last_state

class VoltageSensor(AutopiSensor):
    
    _attr_name = "Bolt - Voltage"
    entity_id = "sensor.bolt_voltage"
    _attr_device_class = DEVICE_CLASS_VOLTAGE
    _attr_native_unit_of_measurement = "V"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'voltage' in self.autopi.latest:
            self._last_state = self.autopi.latest['voltage']
        return self._last_state

class CurrentSensor(AutopiSensor):
    
    _attr_name = "Bolt - Current"
    entity_id = "sensor.bolt_current"
    _attr_device_class = DEVICE_CLASS_CURRENT
    _attr_native_unit_of_measurement = "A"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'current' in self.autopi.latest:
            self._last_state = self.autopi.latest['current']
        return self._last_state

class BatteryCapacitySensor(AutopiSensor):
    
    _attr_name = "Bolt - Battery Capacity"
    entity_id = "sensor.bolt_battery_capacity"
    _attr_device_class = DEVICE_CLASS_ENERGY
    _attr_native_unit_of_measurement = "kWh"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'battery_capacity' in self.autopi.latest:
            self._last_state = self.autopi.latest['battery_capacity']
        return self._last_state

class BatteryCoolantSpeedSensor(AutopiSensor):
    
    _attr_name = "Bolt - Battery Coolant Speed"
    entity_id = "sensor.bolt_battery_coolant_speed"
    _attr_native_unit_of_measurement = "rpm"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'battery_coolant_speed' in self.autopi.latest:
            self._last_state = self.autopi.latest['battery_coolant_speed']
        return self._last_state

class BatteryCoolantTempSensor(AutopiSensor):
    
    _attr_name = "Bolt - Battery Coolant Temp"
    entity_id = "sensor.bolt_battery_coolant_temp"
    _attr_device_class = DEVICE_CLASS_TEMPERATURE
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, autopi):
        self.autopi = autopi

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'battery_coolant_temp' in self.autopi.latest:
            self._last_state = self.autopi.latest['battery_coolant_temp']
        return self._last_state

class BatteryHeaterPowerSensor(AutopiSensor):
    
    _attr_name = "Bolt - Battery Heater Power"
    entity_id = "sensor.bolt_battery_heater_power"
    _attr_device_class = DEVICE_CLASS_POWER
    _attr_native_unit_of_measurement = "W"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'battery_heater_power' in self.autopi.latest:
            self._last_state = self.autopi.latest['battery_heater_power']
        return self._last_state

class CabinAcPowerSensor(AutopiSensor):
    
    _attr_name = "Bolt - Cabin AC Power"
    entity_id = "sensor.bolt_cabin_ac_power"
    _attr_device_class = DEVICE_CLASS_POWER
    _attr_native_unit_of_measurement = "W"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'cabin_ac_power' in self.autopi.latest:
            self._last_state = self.autopi.latest['cabin_ac_power']
        return self._last_state

class CabinHeaterPowerSensor(AutopiSensor):
    
    _attr_name = "Bolt - Cabin Heater Power"
    entity_id = "sensor.bolt_cabin_heater_power"
    _attr_device_class = DEVICE_CLASS_POWER
    _attr_native_unit_of_measurement = "W"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'cabin_heater_power' in self.autopi.latest:
            self._last_state = self.autopi.latest['cabin_heater_power']
        return self._last_state

class Rssi(AutopiSensor):
    
    _attr_name = "Bolt - RSSI"
    entity_id = "sensor.bolt_rssi"
    _attr_device_class = DEVICE_CLASS_SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"

    def __init__(self, autopi):
        self.autopi = autopi
    
    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and 'rssi' in self.autopi.latest:
            self._last_state = self.autopi.latest['rssi']
        return self._last_state

class CellVoltageSensor(AutopiSensor):
    _attr_device_class = DEVICE_CLASS_VOLTAGE
    _attr_native_unit_of_measurement = "V"

    def __init__(self, autopi, cell_num):
        self.autopi = autopi
        self.cell_num = cell_num
        self.entity_id = f'sensor.bolt_voltage_cell_{self.cell_num}'
    
    @property
    def name(self):
        return f'Bolt - Voltage Cell {self.cell_num}'

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.autopi.latest and f'cell_voltage_{self.cell_num}' in self.autopi.latest:
            self._last_state = self.autopi.latest[f'cell_voltage_{self.cell_num}']
        return self._last_state
