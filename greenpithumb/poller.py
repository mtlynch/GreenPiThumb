import logging
import threading

import db_store

logger = logging.getLogger(__name__)


class SensorPollerFactory(object):
    """Factory to simplify the semantics of creating pollers."""

    def __init__(self, local_clock, poll_interval, record_queue):
        self._local_clock = local_clock
        self._poll_interval = poll_interval
        self._record_queue = record_queue

    def create_temperature_poller(self, temperature_sensor):
        return TemperaturePoller(self._local_clock, self._poll_interval,
                                 temperature_sensor, self._record_queue)

    def create_humidity_poller(self, humidity_sensor):
        return HumidityPoller(self._local_clock, self._poll_interval,
                              humidity_sensor, self._record_queue)

    def create_soil_watering_poller(self, moisture_sensor, pump_manager):
        return SoilWateringPoller(self._local_clock, self._poll_interval,
                                  moisture_sensor, pump_manager,
                                  self._record_queue)

    def create_ambient_light_poller(self, light_sensor):
        return AmbientLightPoller(self._local_clock, self._poll_interval,
                                  light_sensor, self._record_queue)


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
                 record_queue):
        """Creates a new TemperaturePoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the sensor should be polled, in
                seconds.
            temperature_sensor: An interface for reading the temperature.
            record_queue: Queue on which to place temperature records for
              storage.
        """
        super(TemperaturePoller, self).__init__(local_clock, poll_interval)
        self._temperature_sensor = temperature_sensor
        self._record_queue = record_queue

    def _poll_once(self):
        """Polls for current ambient temperature and queues DB record."""
        temperature = self._temperature_sensor.temperature()
        self._record_queue.put(
            db_store.TemperatureRecord(self._local_clock.now(), temperature))


class HumidityPoller(SensorPollerBase):
    """Polls a humidity sensor and stores the readings."""

    def __init__(self, local_clock, poll_interval, humidity_sensor,
                 record_queue):
        """Creates a new HumidityPoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the sensor should be polled, in
                seconds.
            humidity_sensor: An interface for reading the humidity.
            record_queue: Queue on which to place humidity records for storage.
        """
        super(HumidityPoller, self).__init__(local_clock, poll_interval)
        self._humidity_sensor = humidity_sensor
        self._record_queue = record_queue

    def _poll_once(self):
        """Polls for and stores current relative humidity."""
        humidity = self._humidity_sensor.humidity()
        self._record_queue.put(
            db_store.HumidityRecord(self._local_clock.now(), humidity))


class AmbientLightPoller(SensorPollerBase):
    """Polls an ambient light sensor and stores the readings."""

    def __init__(self, local_clock, poll_interval, light_sensor, record_queue):
        """Creates a new AmbientLightPoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the sensor should be polled, in
                seconds.
            light_sensor: An interface for reading the ambient light level.
            record_queue: Queue on which to place ambient light records for
              storage.
        """
        super(AmbientLightPoller, self).__init__(local_clock, poll_interval)
        self._light_sensor = light_sensor
        self._record_queue = record_queue

    def _poll_once(self):
        ambient_light = self._light_sensor.ambient_light()
        self._record_queue.put(
            db_store.AmbientLightRecord(self._local_clock.now(), ambient_light))


class SoilWateringPoller(SensorPollerBase):
    """Polls for and records watering event data.

    Polls soil moisture sensor and oversees a water pump based to add water when
    the moisture drops too low. Records both soil moisture and watering events.
    """

    def __init__(self, local_clock, poll_interval, soil_moisture_sensor,
                 pump_manager, record_queue):
        """Creates a new SoilWateringPoller object.

        Args:
            local_clock: A local time zone clock interface.
            poll_interval: An int of how often the data should be polled for,
                in seconds.
            soil_moisture_sensor: An interface for reading the soil moisture
                level.
            pump_manager: An interface to manage a water pump.
            record_queue: Queue on which to place soil moisture records and
                watering event records for storage.
        """
        super(SoilWateringPoller, self).__init__(local_clock, poll_interval)
        self._pump_manager = pump_manager
        self._soil_moisture_sensor = soil_moisture_sensor
        self._record_queue = record_queue

    def _poll_once(self):
        """Polls soil moisture and adds water if moisture is too low.

        Checks soil moisture levels and records the current level. Using the
        current soil moisture level, checks if the pump needs to run, and if so,
        runs the pump and records the watering event.
        """
        soil_moisture = self._soil_moisture_sensor.moisture()
        self._record_queue.put(
            db_store.SoilMoistureRecord(self._local_clock.now(), soil_moisture))
        ml_pumped = self._pump_manager.pump_if_needed(soil_moisture)
        if ml_pumped > 0:
            self._record_queue.put(
                db_store.WateringEventRecord(self._local_clock.now(),
                                             ml_pumped))


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
