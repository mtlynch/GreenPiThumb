import dht11_exceptions

class HumiditySensor(object):
	"""Wrapper for humidity sensor."""

	def __init__(self, dht11_result):
		"""Creates a new HumiditySensor wrapper.

		Args:
			dht11_result: Result of a reading from a DHT11 humidity and
			temperature sensor.   
		"""
		self._dht11_result = dht11_result

	def get_humidity_level(self):
		"""Returns humidity level."""

		if self._dht11_result.error_code() == 1:
			raise dht11_exceptions.MissingDataError()
		elif self._dht11_result.error_code() == 2:
			raise dht11_exceptions.IncorrectCRCError()
		elif self._dht11_result.error_code() == 0:
			humidity_level = self._dht11_result.humidity()
		else:
			raise ValueError("DHT11 error code out of range")

		return humidity_level