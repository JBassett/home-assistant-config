import logging
from datetime import (datetime, timedelta)

from .const import DOMAIN

from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_VOLTAGE,
    DEVICE_CLASS_ENERGY
)

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

def get_power(device):
    data_time = datetime.strptime(device["DATATIME"], "%Y,%m,%d,%H,%M,%S")
    time_since_data = datetime.utcnow() - data_time

    return device["p_3phsum_kw"] if  time_since_data < timedelta(minutes=3) else 0

async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("async_setup_entry -> Start")
    sunpower = hass.data[DOMAIN]['sunpower']

    sensors = []
    for serial in sunpower.data:
        device = sunpower.data[serial]
        # Depending on device we need to add sensors we care about
        if(device["MODEL"] == "AC_Module_Type_D"):
            sensors.append(PanelPowerSensor(sunpower, device))
            sensors.append(PanelLifetimeEnergySensor(sunpower, device))
            sensors.append(PanelMpptVoltageSensor(sunpower, device))
            sensors.append(PanelMpptAmperageSensor(sunpower, device))
            sensors.append(PanelFrequencySensor(sunpower, device))
            sensors.append(PanelTemperatureSensor(sunpower, device))
        elif(device["MODEL"] == "PVS5M0400c"):
            sensors.append(HomeFrequencySensor(sunpower, device))
            sensors.append(HomePowerNetSensor(sunpower, device))
            sensors.append(HomePowerProductionSensor(sunpower, device))
            sensors.append(HomePowerUsageSensor(sunpower, device))
            sensors.append(HomeEnergyLifetimeProductionSensor(sunpower, device))
            sensors.append(HomeEnergyLifetimeNetSensor(sunpower, device))

    async_add_entities(sensors)
    _LOGGER.debug("async_setup_entry -> Complete")

class SunpowerSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self.device_serial = self._device["SERIAL"]
        self.device_name = self._device["DESCR"] if "DESCR" in self._device else ""
        self.device_model = self._device["MODEL"] if "MODEL" in self._device else ""
        self.device_sw_version = self._device["SWVER"] if "SWVER" in self._device else ""

    @property
    def unique_id(self):
        """Return the unique ID of this sensor."""
        return f'{self.device_name}_{self.name}'

    @property
    def name(self):
        return f'{self.name_prefix} {self.device_name}'

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device_serial)},
            "manufacturer": "SunPower",
            "model": self.device_model,
            "name": self.device_name,
            "sw_version": self.device_sw_version
        }

class PanelPowerSensor(SunpowerSensor):
    name_prefix = "Power"
    device_class = DEVICE_CLASS_POWER
    unit_of_measurement = "kW"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def state(self):
        """Return the state of the sensor."""
        return get_power(self.coordinator.data[self.device_serial])
        
class PanelLifetimeEnergySensor(SunpowerSensor):
    name_prefix = "Lifetime Enery"
    device_class = DEVICE_CLASS_ENERGY
    unit_of_measurement = "kWh"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.device_serial]["ltea_3phsum_kwh"]

class PanelMpptVoltageSensor(SunpowerSensor):
    name_prefix = "MPPT Voltage"
    device_class = DEVICE_CLASS_VOLTAGE
    unit_of_measurement = "V"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.device_serial]["v_mppt1_v"]

class PanelMpptAmperageSensor(SunpowerSensor):
    name_prefix = "MPPT Amperage"
    device_class = DEVICE_CLASS_CURRENT
    unit_of_measurement = "A"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.device_serial]["i_mppt1_a"]

class PanelFrequencySensor(SunpowerSensor):
    name_prefix = "Frequency"
    unit_of_measurement = "Hz"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.device_serial]["freq_hz"]

class PanelTemperatureSensor(SunpowerSensor):
    name_prefix = "Temperature"
    device_class = DEVICE_CLASS_TEMPERATURE
    unit_of_measurement = "°C"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.device_serial]["t_htsnk_degc"]

class HomeFrequencySensor(SunpowerSensor):
    unit_of_measurement = "Hz"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def name(self):
        return "Home Frequency"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.device_serial]["freq_hz"]

class HomePowerNetSensor(SunpowerSensor):
    device_class = DEVICE_CLASS_POWER
    unit_of_measurement = "kW"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def name(self):
        return "Home Power Net"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.device_serial]["p_3phsum_kw"]

class HomePowerProductionSensor(SunpowerSensor):
    device_class = DEVICE_CLASS_POWER
    unit_of_measurement = "kW"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def name(self):
        return "Home Power Production"

    @property
    def state(self):
        """Return the state of the sensor."""
        current_power = 0
        for serial in self.coordinator.data:
            device = self.coordinator.data[serial]
            # Depending on device we need to add sensors we care about
            if(device["MODEL"] == "AC_Module_Type_D"):
                current_power = current_power + float(get_power(device))
        return current_power

class HomePowerUsageSensor(SunpowerSensor):
    device_class = DEVICE_CLASS_POWER
    unit_of_measurement = "kW"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def name(self):
        return "Home Power Usage"

    @property
    def state(self):
        """Return the state of the sensor."""
        current_power_production = 0
        for serial in self.coordinator.data:
            device = self.coordinator.data[serial]
            # Depending on device we need to add sensors we care about
            if(device["MODEL"] == "AC_Module_Type_D"):
                current_power_production = current_power_production + float(get_power(device))

        return round(current_power_production + float(self.coordinator.data[self.device_serial]["p_3phsum_kw"]), 4)

class HomeEnergyLifetimeProductionSensor(SunpowerSensor):
    device_class = DEVICE_CLASS_ENERGY
    unit_of_measurement = "kWh"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def name(self):
        return "Home Enegry Lifetime Production"
    
    @property
    def state(self):
        """Return the state of the sensor."""
        lifetime_energy = 0
        for serial in self.coordinator.data:
            device = self.coordinator.data[serial]
            # Depending on device we need to add sensors we care about
            if(device["MODEL"] == "AC_Module_Type_D"):
                lifetime_energy = lifetime_energy + float(device["ltea_3phsum_kwh"])

        return lifetime_energy

class HomeEnergyLifetimeNetSensor(SunpowerSensor):
    device_class = DEVICE_CLASS_ENERGY
    unit_of_measurement = "kWh"
    state_class="measurement"

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)

    @property
    def name(self):
        return "Home Enegry Lifetime Net"
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.device_serial]["net_ltea_3phsum_kwh"]
