import argparse
import logging
import Queue

import Adafruit_DHT
import Adafruit_MCP3008
import RPi.GPIO as GPIO

import clock
import db_store
import dht11
import humidity_sensor
import light_sensor
import moisture_sensor
import pi_io
import poller
import record_processor
import temperature_sensor
import wiring_config_parser

logger = logging.getLogger(__name__)


def make_sensor_pollers(poll_interval, wiring_config, open_db_connection_func):
    logger.info('creating sensor pollers (poll interval=%d")', poll_interval)
    local_clock = clock.LocalClock()
    # The MCP3008 spec and Adafruit library use different naming for the
    # Raspberry Pi GPIO pins, so we translate as follows:
    # * CLK -> CLK
    # * CS/SHDN -> CS
    # * DOUT -> MISO
    # * DIN -> MOSI
    adc = Adafruit_MCP3008.MCP3008(
        clk=wiring_config.gpio_pins.mcp3008_clk,
        cs=wiring_config.gpio_pins.mcp3008_cs_shdn,
        miso=wiring_config.gpio_pins.mcp3008_dout,
        mosi=wiring_config.gpio_pins.mcp3008_din)
    local_dht11 = dht11.CachingDHT11(
        lambda: Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, wiring_config.gpio_pins.dht11),
        local_clock)

    poller_factory = poller.SensorPollerFactory(local_clock, poll_interval)
    pollers = []
    pollers.append(
        poller_factory.create_temperature_poller(
            temperature_sensor.TemperatureSensor(local_dht11),
            db_store.TemperatureStore(open_db_connection_func)))
    pollers.append(
        poller_factory.create_humidity_poller(
            humidity_sensor.HumiditySensor(local_dht11),
            db_store.HumidityStore(open_db_connection_func)))
    pollers.append(
        poller_factory.create_moisture_poller(
            moisture_sensor.MoistureSensor(
                adc,
                pi_io.IO(GPIO), wiring_config.adc_channels.soil_moisture_sensor,
                wiring_config.gpio_pins.soil_moisture_1,
                wiring_config.gpio_pins.soil_moisture_2, local_clock),
            db_store.SoilMoistureStore(open_db_connection_func)))
    pollers.append(
        poller_factory.create_ambient_light_poller(
            light_sensor.LightSensor(adc,
                                     wiring_config.adc_channels.light_sensor),
            db_store.AmbientLightStore(open_db_connection_func)))
    # TODO(jeetshetty): Add watering event poller.

    return pollers


def read_wiring_config(config_filename):
    logger.info('reading wiring config at "%s"', config_filename)
    with open(config_filename) as config_file:
        return wiring_config_parser.parse(config_file.read())


def configure_logging(verbose):
    """Configure the root logger for log output."""
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-15s %(levelname)-4s %(message)s',
        '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    if verbose:
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.WARNING)


def main(args):
    configure_logging(args.verbose)
    logger.info('starting greenpithumb')
    wiring_config = read_wiring_config(args.config_file)
    record_queue = Queue.Queue()
    open_db_connection_func = lambda: db_store.open_or_create_db(args.db_file)
    pollers = make_sensor_pollers(args.poll_interval, wiring_config,
                                  record_queue, open_db_connection_func)
    try:
        for current_poller in pollers:
            current_poller.start_polling_async()
        while True:
            record_processor.process_next_record()
    finally:
        for current_poller in pollers:
            current_poller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='GreenPiThumb',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-p',
        '--poll_interval',
        type=float,
        help='Number of seconds between each sensor poll',
        default=0.5)
    parser.add_argument(
        '-c',
        '--config_file',
        help='Wiring config file',
        default='greenpithumb/wiring_config.ini')
    parser.add_argument(
        '-s',
        '--sleep_window',
        action='append',
        type=str,
        help=('Time window during which GreenPiThumb will not activate its '
              'pump. Window should be in the form of a time range in 24-hour '
              'format, such as "03:15-03:45"'))
    parser.add_argument(
        '-i',
        '--image_path',
        type=str,
        help='Path to folder where images will be stored',
        default='images/')
    parser.add_argument(
        '-d',
        '--db_file',
        help='Location to store GreenPiThumb database file',
        default='greenpithumb/greenpithumb.db')
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Use verbose logging')
    main(parser.parse_args())
