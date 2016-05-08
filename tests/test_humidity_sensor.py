from __future__ import absolute_import
import unittest

import mock

from greenpithumb import humidity_sensor
from greenpithumb import dht11_exceptions

class HumiditySensorTest(unittest.TestCase):

	def setUp(self):
		self.mock_dht11 = mock.Mock()
		self.humidity_sensor = humidity_sensor.HumiditySensor(
			self.mock_dht11)

	def test_humidity_50(self):
		"""Value given should be value returned."""

		self.mock_dht11.read().error_code = 0
		self.mock_dht11.read().humidity = 50.0
		humidity_level = self.humidity_sensor.get_humidity_level()
		self.assertEqual(humidity_level, 50.0)

	def test_missing_data_error(self):
		"""Error code of 1 should raise an exception."""

		with self.assertRaises(dht11_exceptions.MissingDataError):
			self.mock_dht11.read().error_code = 1
			self.humidity_sensor.get_humidity_level()

	def test_incorrect_crc_error(self):
		"""Error code of 2 should raise an exception."""

		with self.assertRaises(dht11_exceptions.IncorrectCRCError):
			self.mock_dht11.read().error_code = 2
			self.humidity_sensor.get_humidity_level()

	def test_error_code_out_of_range(self):
		"""Error code other than 0, 1, or 2 should raise an exception."""

		with self.assertRaises(ValueError):
			self.mock_dht11.read().error_code = 3
			self.humidity_sensor.get_humidity_level()

