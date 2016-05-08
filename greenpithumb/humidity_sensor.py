import dht11_exceptions

class HumiditySensor(object):
	"""Wrapper for humidity sensor."""

	def __init__(self, dht11):
		"""Creates a new HumiditySensor wrapper.

		Args:
			dht11: Instance of DHT11 sensor reader class. 
		"""
		self._dht11 = dht11

	def get_humidity_level(self):
		"""Returns humidity level."""

		error_code = self._dht11.read().error_code

		# TODO(JeetShetty): Replace error codes with constants from dht11 
		# module
		
		if error_code != 0:
			if error_code == 1:
				raise dht11_exceptions.MissingDataError(
					"DHT11 sensor reported missing data")
			elif error_code == 2:
				raise dht11_exceptions.IncorrectCRCError()
			else:
				raise ValueError(
					"DHT11 error code out of range: %i" % error_code)

		humidity_level = self._dht11.read().humidity

		return humidity_level