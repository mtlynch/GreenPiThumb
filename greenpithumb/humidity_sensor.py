import adc

#placeholder values
_MIN_HUMIDITY_VALUE = 0
_MAX_HUMIDITY_VALUE = 100

class HumiditySensor(object):
	"""Wrapper for humidity sensor."""

	def __init__(self, adc):
		"""Creates a new HumiditySensor wrapper.

		Args:
			adc: ADC(analog to digital) interface to receive
			analog signals from humidity sensor.
		"""
		self._adc = adc

	def get_humidity_level(self):
		"""Returns humidity level as percentage."""

		humidity_level = self._adc.read_pin(adc.PIN_HUMIDITY_SENSOR)

		if humidity_level < _MIN_HUMIDITY_VALUE or \
		humidity_level > _MAX_HUMIDITY_VALUE:
			raise ValueError('Humidity sensor reading out of range')

		humidity_level_as_pct = 100 * ((humidity_level - _MIN_HUMIDITY_VALUE) /
			(_MAX_HUMIDITY_VALUE - _MIN_HUMIDITY_VALUE))

		return humidity_level_as_pct