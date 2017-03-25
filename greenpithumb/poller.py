import logging
import threading

import db_store

logger = logging.getLogger(__name__)


class SensorPollerFactory(object):
    """Factory to simplify the semantics of creating pollers."""

    def __init__(self, local_clock, poll_interval):
        self._local_clock = local_clock
        self._poll_interval = poll_interval

    def create_temperature_poller(self, temperature_sensor, temperature_store):
        return TemperaturePoller(self._local_clock, self._poll_interval,
                                 temperature_sensor, temperature_store)

    def create_humidity_poller(self, humidity_sensor, humidity_store):
        return HumidityPoller(self._local_clock, self._poll_interval,
                              humidity_sensor, humidity_store)

    def create_moisture_poller(self, moisture_sensor, moisture_store):
        return MoisturePoller(self._local_clock, self._poll_interval,
                              moisture_sensor, moisture_store)

    def create_ambient_light_poller(self, light_sensor, ambient_light_store):
        return AmbientLightPoller(self._local_clock, self._poll_interval,
                                  light_sensor, ambient_light_store)

    def create_watering_event_poller(self, pump_manager, soil_moisture_store,
                                     watering_event_store):
        return WateringEventPoller(self._local_clock, self._poll_interval,
                                   pump_manager, soil_moisture_store,
                                   watering_event_store)


class SensorPollerBase(object):
    """Base class for sensor polling."""

    def __init__(self, local_clock, poll_interval):
        """Creates a new SensorPollerBase object for polling sensors.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the sensor should be polled, in
                seconds.
        """
        self._local_clock = local_clock
        self._poll_interval = poll_interval
        self._closed = threading.Event()

    def _poll(self):
        """Polls at a fixed interval until caller calls close()."""
        logger.info('polling starting for %s', self.__class__.__name__)
        while not self._closed.is_set():
            self._poll_once()
            self._local_clock.wait(self._poll_interval)
        self._close_db_stores()
        logger.info('polling terminating for %s', self.__class__.__name__)

    def start_polling_async(self):
        """Starts a new thread to begin polling."""
        t = threading.Thread(target=self._poll)
        t.setDaemon(True)
        t.start()

    def close(self):
        """Stops polling."""
        self._closed.set()


class TemperaturePoller(SensorPollerBase):
    """Polls a temperature sensor and stores the readings."""

    def __init__(self, local_clock, poll_interval, temperature_sensor,
                 temperature_store):
        """Creates a new TemperaturePoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the sensor should be polled, in
                seconds.
            temperature_sensor: An interface for reading the temperature.
            temperature_store: Queue on which to place temperature records for
              storage.
        """
        super(TemperaturePoller, self).__init__(local_clock, poll_interval)
        self._temperature_sensor = temperature_sensor
        self._temperature_store = temperature_store

    def _poll_once(self):
        """Polls for current ambient temperature and queues DB record."""
        temperature = self._temperature_sensor.temperature()
        self._temperature_store.insert(
            db_store.TemperatureRecord(self._local_clock.now(), temperature))

    def _close_db_stores(self):
        self._temperature_store.close()


class HumidityPoller(SensorPollerBase):
    """Polls a humidity sensor and stores the readings."""

    def __init__(self, local_clock, poll_interval, humidity_sensor,
                 humidity_store):
        """Creates a new HumidityPoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the sensor should be polled, in
                seconds.
            humidity_sensor: An interface for reading the humidity.
            humidity_store: Queue on which to place humidity records for storage.
        """
        super(HumidityPoller, self).__init__(local_clock, poll_interval)
        self._humidity_sensor = humidity_sensor
        self._humidity_store = humidity_store

    def _poll_once(self):
        """Polls for and stores current relative humidity."""
        humidity = self._humidity_sensor.humidity()
        self._humidity_store.insert(
            db_store.HumidityRecord(self._local_clock.now(), humidity))

    def _close_db_stores(self):
        self._humidity_store.close()

class MoisturePoller(SensorPollerBase):
    """Polls a soil moisture sensor and stores the readings."""

    def __init__(self, local_clock, poll_interval, moisture_sensor,
                 moisture_store):
        """Creates a MoisturePoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the sensor should be polled, in
                seconds.
            moisture_sensor: An interface for reading the soil moisture level.
            moisture_store: Queue on which to place moisture records for storage.
        """
        super(MoisturePoller, self).__init__(local_clock, poll_interval)
        self._moisture_sensor = moisture_sensor
        self._moisture_store = moisture_store

    def _poll_once(self):
        """Polls current soil moisture."""
        soil_moisture = self._moisture_sensor.moisture()
        self._moisture_store.insert(
            db_store.SoilMoistureRecord(self._local_clock.now(), soil_moisture))

    def _close_db_stores(self):
        self._moisture_store.close()


class AmbientLightPoller(SensorPollerBase):
    """Polls an ambient light sensor and stores the readings."""

    def __init__(self, local_clock, poll_interval, light_sensor,
                 ambient_light_store):
        """Creates a new AmbientLightPoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the sensor should be polled, in
                seconds.
            light_sensor: An interface for reading the ambient light level.
            ambient_light_store: Queue on which to place ambient light records for
              storage.
        """
        super(AmbientLightPoller, self).__init__(local_clock, poll_interval)
        self._light_sensor = light_sensor
        self._ambient_light_store = ambient_light_store

    def _poll_once(self):
        ambient_light = self._light_sensor.ambient_light()
        self._ambient_light_store.insert(
            db_store.AmbientLightRecord(self._local_clock.now(), ambient_light))

    def _close_db_stores(self):
        self._ambient_light_store.close()


class WateringEventPoller(SensorPollerBase):
    """Polls for and records watering event data.

    Polls for latest soil moisture readings and oversees a water pump based on
    those readings.
    """

    def __init__(self, local_clock, poll_interval, pump_manager,
                 soil_moisture_store, watering_event_store):
        """Creates a new WateringEventPoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the data should be polled for,
                in seconds.
            pump_manager: An interface to manage a water pump.
            soil_moisture_store: An interface for retrieving soil moisture
                readings.
            watering_event_store: Queue on which to place watering event records
              for storage.
        """
        super(WateringEventPoller, self).__init__(local_clock, poll_interval)
        self._pump_manager = pump_manager
        self._soil_moisture_store = soil_moisture_store
        self._watering_event_store = watering_event_store

    def _poll_once(self):
        """Oversees a water pump, and polls for and stores watering event data.

        Polls for latest soil moisture readings and feeds them to a water pump.
        If the pump runs, it stores the event data.
        """
        soil_moisture = self._soil_moisture_store.get_latest()
        if soil_moisture:
            ml_pumped = self._pump_manager.pump_if_needed(soil_moisture)
            if ml_pumped > 0:
                self.watering_event_store.insert(
                    db_store.WateringEventRecord(self._local_clock.now(),
                                                 ml_pumped))

    def _close_db_stores(self):
        self._soil_moisture_store.close()
        self._watering_event_store.close()


class CameraPoller(SensorPollerBase):
    """Captures and stores pictures pictures from a camera."""

    def __init__(self, local_clock, poll_interval, camera_manager):
        """Creates a new CameraPoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the images should be captured,
                in seconds.
            camera_manager: An interface for capturing images.
        """
        super(CameraPoller, self).__init__(local_clock, poll_interval)
        self._camera_manager = camera_manager

    def _poll_once(self):
        """Captures and stores an image."""
        self._camera_manager.save_photo()

    def _close_db_stores(self):
        pass
