import contextlib
import datetime
import threading
import unittest

import mock
import pytz

from greenpithumb import db_store
from greenpithumb import poller

TEST_TIMEOUT_SECONDS = 3.0
TIMESTAMP_A = datetime.datetime(2016, 7, 23, 10, 51, 9, 928000, tzinfo=pytz.utc)
POLL_INTERVAL = 1


class PollerClassesTest(unittest.TestCase):

    def setUp(self):
        self.clock_wait_event = threading.Event()
        self.mock_local_clock = mock.Mock()
        self.mock_sensor = mock.Mock()
        self.mock_store = mock.Mock()

    def test_temperature_poller(self):
        with contextlib.closing(
                poller.TemperaturePoller(
                    self.mock_local_clock, POLL_INTERVAL, self.mock_sensor,
                    self.mock_store)) as temperature_poller:
            self.mock_local_clock.now.return_value = TIMESTAMP_A
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_sensor.temperature.return_value = 21.0

            temperature_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)

        self.mock_store.insert.assert_called_with(
            db_store.TemperatureRecord(TIMESTAMP_A, 21.0))
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)

    def test_humidity_poller(self):
        with contextlib.closing(
                poller.HumidityPoller(self.mock_local_clock, POLL_INTERVAL,
                                      self.mock_sensor,
                                      self.mock_store)) as humidity_poller:
            self.mock_local_clock.now.return_value = TIMESTAMP_A
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_sensor.humidity.return_value = 50.0

            humidity_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)

        self.mock_store.insert.assert_called_with(
            db_store.HumidityRecord(TIMESTAMP_A, 50.0))
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)

    def test_moisture_poller(self):
        with contextlib.closing(
                poller.MoisturePoller(self.mock_local_clock, POLL_INTERVAL,
                                      self.mock_sensor,
                                      self.mock_store)) as moisture_poller:
            self.mock_local_clock.now.return_value = TIMESTAMP_A
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_sensor.moisture.return_value = 300

            moisture_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)

        self.mock_store.insert.assert_called_with(
            db_store.SoilMoistureRecord(TIMESTAMP_A, 300))
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)

    def test_ambient_light_poller(self):
        with contextlib.closing(
                poller.AmbientLightPoller(
                    self.mock_local_clock, POLL_INTERVAL, self.mock_sensor,
                    self.mock_store)) as ambient_light_poller:
            self.mock_local_clock.now.return_value = TIMESTAMP_A
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_sensor.ambient_light.return_value = 50.0

            ambient_light_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)

        self.mock_store.insert.assert_called_with(
            db_store.AmbientLightRecord(TIMESTAMP_A, 50.0))
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)


class WateringEventPollerTest(unittest.TestCase):

    def setUp(self):
        self.clock_wait_event = threading.Event()
        self.mock_local_clock = mock.Mock()
        self.mock_pump_manager = mock.Mock()
        self.mock_soil_moisture_store = mock.Mock()
        self.mock_watering_event_store = mock.Mock()

    def test_watering_event_poller_when_pump_run(self):
        with contextlib.closing(
                poller.WateringEventPoller(
                    self.mock_local_clock, POLL_INTERVAL,
                    self.mock_pump_manager, self.mock_soil_moisture_store,
                    self.mock_watering_event_store)) as watering_event_poller:
            self.mock_local_clock.now.return_value = TIMESTAMP_A
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_pump_manager.pump_if_needed.return_value = 200
            self.mock_soil_moisture_store.get_latest.return_value = 100

            watering_event_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)
        self.mock_watering_event_store.insert.assert_called_with(
            db_store.WateringEventRecord(
                timestamp=TIMESTAMP_A, water_pumped=200.0))
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)
        self.mock_pump_manager.pump_if_needed.assert_called_with(100)

    def test_watering_event_poller_when_pump_not_run(self):
        with contextlib.closing(
                poller.WateringEventPoller(
                    self.mock_local_clock, POLL_INTERVAL,
                    self.mock_pump_manager, self.mock_soil_moisture_store,
                    self.mock_watering_event_store)) as watering_event_poller:
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_pump_manager.pump_if_needed.return_value = 0
            self.mock_soil_moisture_store.get_latest.return_value = 500

            watering_event_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)
        self.assertFalse(self.mock_watering_event_store.insert.called)
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)
        self.mock_pump_manager.pump_if_needed.assert_called_with(500)

    def test_watering_event_poller_when_moisture_is_None(self):
        with contextlib.closing(
                poller.WateringEventPoller(
                    self.mock_local_clock, POLL_INTERVAL,
                    self.mock_pump_manager, self.mock_soil_moisture_store,
                    self.mock_watering_event_store)) as watering_event_poller:
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_soil_moisture_store.get_latest.return_value = None

            watering_event_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)
        self.assertFalse(self.mock_watering_event_store.insert.called)
        self.assertFalse(self.mock_pump_manager.pump_if_needed.called)
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)


class CameraPollerTest(unittest.TestCase):

    def test_camera_poller(self):
        clock_wait_event = threading.Event()
        mock_local_clock = mock.Mock()
        mock_camera_manager = mock.Mock()
        with contextlib.closing(
                poller.CameraPoller(mock_local_clock, POLL_INTERVAL,
                                    mock_camera_manager)) as camera_poller:
            mock_local_clock.wait.side_effect = lambda _: clock_wait_event.set()

            camera_poller.start_polling_async()
            clock_wait_event.wait(TEST_TIMEOUT_SECONDS)
            mock_camera_manager.save_photo.assert_called()
