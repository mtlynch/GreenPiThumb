from __future__ import absolute_import
import unittest

import mock

from greenpithumb import adc
from greenpithumb import humidity_sensor

class HumiditySensorTest(unittest.TestCase):

	def setUp(self):
		self.mock_adc = mock.Mock(spec=adc.Adc)
		self.humidity_sensor = humidity_sensor.HumiditySensor(self.mock_adc)

	def test_humidity_50_pct(self):
		"""Midpoint humidity value should return 50.0"""

		#placeholder midpoint value
		self.mock_adc.read_pin.return_value = 50.0
		humidity_level = self.humidity_sensor.get_humidity_level()
		self.assertAlmostEqual(humidity_level, 50.0)

	def test_humidity_level_too_low(self):
		"""Humidity sensor value less than min should raise a ValueError."""

		with self.assertRaises(ValueError):
			self.mock_adc.read_pin.return_value = (
				humidity_sensor._MIN_HUMIDITY_VALUE - 1)
			self.humidity_sensor.get_humidity_level()

	def test_humidity_level_too_high(self):
		"""Humidity sensor value greater than max should raise a ValueError"""

		with self.assertRaises(ValueError):
			self.mock_adc.read_pin.return_value = (
				humidity_sensor._MAX_HUMIDITY_VALUE + 1)
			self.humidity_sensor.get_humidity_level()

