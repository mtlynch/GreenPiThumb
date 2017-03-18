import contextlib
import datetime
import threading
import unittest

import mock
import pytz

from greenpithumb import poller

TEST_TIMEOUT_SECONDS = 3.0
TIMESTAMP_A = datetime.datetime(2016, 7, 23, 10, 51, 9, 928000, tzinfo=pytz.utc)
TIMESTAMP_B = datetime.datetime(2016, 7, 23, 11, 5, 12, 248000, tzinfo=pytz.utc)
TIMESTAMP_C = datetime.datetime(2016, 7, 23, 11, 6, 59, 845000, tzinfo=pytz.utc)
POLL_INTERVAL = 1


class PollerClassesTest(unittest.TestCase):

    def setUp(self):
        self.clock_wait_event = threading.Event()
        self.mock_local_clock = mock.Mock()
        self.mock_sensor = mock.Mock()
        self.mock_store = mock.Mock()

    def mock_clock_wait(self, wait_time):
        print 'wait time = %d' % wait_time
        self.clock_wait_event.set()

    def test_temperature_poller(self):
        with contextlib.closing(
                poller.TemperaturePoller(
                    self.mock_local_clock, POLL_INTERVAL, self.mock_sensor,
                    self.mock_store)) as temperature_poller:
            self.mock_local_clock.now.return_value = TIMESTAMP_A
            self.mock_local_clock.wait.side_effect = self.mock_clock_wait()
            self.mock_sensor.temperature.return_value = 21.0

            temperature_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)
        self.mock_store.store_temperature.assert_called_with(TIMESTAMP_A, 21.0)
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)
"""
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
        self.mock_store.store_humidity.assert_called_with(TIMESTAMP_A, 50.0)
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
        self.mock_store.store_soil_moisture.assert_called_with(TIMESTAMP_A, 300)
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
        self.mock_store.store_ambient_light.assert_called_with(TIMESTAMP_A,
                                                               50.0)
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)


class WateringEventPollerTest(unittest.TestCase):

    def setUp(self):
        self.clock_wait_event = threading.Event()
        self.mock_local_clock = mock.Mock()
        self.mock_pump_manager = mock.Mock()
        self.mock_watering_event_store = mock.Mock()
        self.mock_soil_moisture_store = mock.Mock()

    def test_watering_event_poller_when_pump_run(self):
        with contextlib.closing(
                poller.WateringEventPoller(
                    self.mock_local_clock, POLL_INTERVAL,
                    self.mock_pump_manager, self.mock_watering_event_store,
                    self.mock_soil_moisture_store)) as watering_event_poller:
            self.mock_local_clock.now.return_value = TIMESTAMP_A
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_pump_manager.pump_if_needed.return_value = 200
            self.mock_soil_moisture_store.latest_soil_moisture.return_value = 100

            watering_event_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)
        self.mock_watering_event_store.store_water_pumped.assert_called_with(
            TIMESTAMP_A, 200)
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)
        self.mock_pump_manager.pump_if_needed.assert_called_with(100)

    def test_watering_event_poller_when_pump_not_run(self):
        with contextlib.closing(
                poller.WateringEventPoller(
                    self.mock_local_clock, POLL_INTERVAL,
                    self.mock_pump_manager, self.mock_watering_event_store,
                    self.mock_soil_moisture_store)) as watering_event_poller:
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_pump_manager.pump_if_needed.return_value = 0
            self.mock_soil_moisture_store.latest_soil_moisture.return_value = 500

            watering_event_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)
        self.assertFalse(
            self.mock_watering_event_store.store_water_pumped.called)
        self.mock_local_clock.wait.assert_called_with(POLL_INTERVAL)
        self.mock_pump_manager.pump_if_needed.assert_called_with(500)

    def test_watering_event_poller_when_moisture_is_None(self):
        with contextlib.closing(
                poller.WateringEventPoller(
                    self.mock_local_clock, POLL_INTERVAL,
                    self.mock_pump_manager, self.mock_watering_event_store,
                    self.mock_soil_moisture_store)) as watering_event_poller:
            self.mock_local_clock.wait.side_effect = (
                lambda _: self.clock_wait_event.set())
            self.mock_soil_moisture_store.latest_soil_moisture.return_value = None

            watering_event_poller.start_polling_async()
            self.clock_wait_event.wait(TEST_TIMEOUT_SECONDS)
            self.assertFalse(
                self.mock_watering_event_store.store_water_pumped.called)
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
"""
