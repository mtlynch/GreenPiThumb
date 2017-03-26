import collections
import logging
import os
import sqlite3

from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

# For each record, timestamp is a datetime representing the time of the reading
# or event.
SoilMoistureRecord = collections.namedtuple('SoilMoistureRecord',
                                            ['timestamp', 'soil_moisture'])
AmbientLightRecord = collections.namedtuple('AmbientLightRecord',
                                            ['timestamp', 'ambient_light'])
HumidityRecord = collections.namedtuple('HumidityRecord',
                                        ['timestamp', 'humidity'])
# temperature value is in degrees Celsius.
TemperatureRecord = collections.namedtuple('TemperatureRecord',
                                           ['timestamp', 'temperature'])
# water_pumped is the volume of water pumped in mL.
WateringEventRecord = collections.namedtuple('WateringEventRecord',
                                             ['timestamp', 'water_pumped'])

# SQL statements to create database tables. Each statement is separated by a
# semicolon and newline.
_CREATE_TABLE_COMMANDS = """
CREATE TABLE temperature
(
    timestamp TEXT,
    temperature REAL    --ambient temperature (in degrees Celsius)
);
CREATE TABLE ambient_humidity
(
    timestamp TEXT,
    humidity REAL
);
CREATE TABLE soil_moisture
(
    timestamp TEXT,
    soil_moisture INTEGER
);
CREATE TABLE ambient_light
(
    timestamp TEXT,
    light REAL
);
CREATE TABLE watering_events
(
    timestamp TEXT,
    water_pumped REAL   --amount of water pumped (in mL)
);
"""


def _serialize_timestamp(timestamp):
    """Converts a timestamp to a string.

    Args:
        timestamp: Timestamp as a datetime object.

    Returns:
        Timestamp as a string in ISO 8601 format.
    """
    return timestamp.isoformat('T')


def _open_db(db_path):
    logger.info('opening existing greenpithumb database at "%s"', db_path)
    return sqlite3.connect(db_path)


def _create_db(db_path):
    """Creates and initializes a SQLite database with a GreenPiThumb schema.

    Creates a SQLite database at the path specified and creates GreenPiThumb's
    data tables within the database.

    Args:
        db_path: Path to where to create database file.

    Returns:
        A sqlite connection object for the database. The caller is responsible
        for closing the object.
    """
    logger.info('creating new greenpithumb database at "%s"', db_path)
    sql_commands = _CREATE_TABLE_COMMANDS.split(';\n')
    connection = _open_db(db_path)
    cursor = connection.cursor()
    for sql_command in sql_commands:
        cursor.execute(sql_command)
    connection.commit()
    return connection


def open_or_create_db(db_path):
    """Opens a database file or creates one if the file does not exist.

    If a file exists at the given path, opens the file at that path as a
    database and returns a connection to it. If no file exists, creates and
    initializes a GreenPiThumb database at the given file path.

    Returns:
        A sqlite connection object for the database. The caller is responsible
        for closing the object.
    """
    if os.path.exists(db_path):
        return _open_db(db_path)
    else:
        return _create_db(db_path)


class _DbStoreBase(object):
    """Base class for storing information in a database."""

    def __init__(self, connection):
        """Creates a new _DbStoreBase object for storing information.

        Args:
            connection: SQLite database connection.
        """
        self._connection = connection
        self._cursor = connection.cursor()

    def _do_insert(self, sql, timestamp, value):
        """Executes and commits a SQL insert command.

        Args:
          sql: SQL query string for the insert command.
          timestamp: datetime instance representing the record timestamp.
          value: Value to insert for the record.
        """
        self._cursor.execute(sql, (_serialize_timestamp(timestamp), value))
        self._connection.commit()

    def _do_get(self, sql, record_type):
        """Executes a SQL select query and returns the results.

        Args:
          sql: SQL select query string.
          record_type: The record type to parse the SQL results into.

        Returns:
          A list of database records corresponding to the select query.
        """
        self._cursor.execute(sql)
        data = []
        for row in self._cursor.fetchall():
            data.append((date_parser.parse(row[0]), row[1]))
        typed_data = map(record_type._make, data)
        return typed_data


class SoilMoistureStore(_DbStoreBase):
    """Stores and retrieves timestamp and soil moisture readings."""

    def insert(self, soil_moisture_record):
        """Inserts moisture and timestamp info into an SQLite database.

        Args:
            soil_moisture_record: Moisture record to store.
        """
        self._do_insert('INSERT INTO soil_moisture VALUES (?, ?)',
                        soil_moisture_record.timestamp,
                        soil_moisture_record.soil_moisture)

    def get(self):
        """Retrieves timestamp and soil moisture readings.

        Returns:
            A list of objects with 'timestamp' and 'soil_moisture' fields.
        """
        return self._do_get('SELECT * FROM soil_moisture', SoilMoistureRecord)


class AmbientLightStore(_DbStoreBase):
    """Stores timestamp and ambient light readings."""

    def insert(self, ambient_light_record):
        """Inserts ambient light and timestamp info into an SQLite database.

        Args:
            ambient_light_record: Ambient light record to store.
        """
        self._do_insert('INSERT INTO ambient_light VALUES (?, ?)',
                        ambient_light_record.timestamp,
                        ambient_light_record.ambient_light)

    def get(self):
        """Retrieves timestamp and ambient light readings.

        Returns:
            A list of objects with 'timestamp' and 'ambient_light' fields.
        """
        return self._do_get('SELECT * FROM ambient_light', AmbientLightRecord)


class HumidityStore(_DbStoreBase):
    """Stores timestamp and ambient humidity readings."""

    def insert(self, humidity_record):
        """Inserts humidity and timestamp info into an SQLite database.

        Args:
            humidity_record: Humidity record to store.
        """
        self._do_insert('INSERT INTO ambient_humidity VALUES (?, ?)',
                        humidity_record.timestamp, humidity_record.humidity)

    def get(self):
        """Retrieves timestamp and relative humidity readings.

        Returns:
            A list of objects with 'timestamp' and 'humidity' fields.
        """
        return self._do_get('SELECT * FROM ambient_humidity', HumidityRecord)


class TemperatureStore(_DbStoreBase):
    """Stores timestamp and ambient temperature readings."""

    def insert(self, temperature_record):
        """Inserts temperature and timestamp info into an SQLite database.

        Args:
            temperature_record: Temperature record to store.
        """
        self._do_insert('INSERT INTO temperature VALUES (?, ?)',
                        temperature_record.timestamp,
                        temperature_record.temperature)

    def get(self):
        """Retrieves timestamp and temperature(C) readings.

        Returns:
            A list of objects with 'timestamp' and 'temperature' fields.
        """
        return self._do_get('SELECT * FROM temperature', TemperatureRecord)


class WateringEventStore(_DbStoreBase):
    """Stores timestamp and volume of water pumped to plant."""

    def insert(self, watering_event_record):
        """Inserts water volume and timestamp info into an SQLite database.

        Args:
            watering_event_record: Watering event record to store.
        """
        self._do_insert('INSERT INTO watering_events VALUES (?, ?)',
                        watering_event_record.timestamp,
                        watering_event_record.water_pumped)

    def get(self):
        """Retrieves timestamp and volume of water pumped(in mL).

        Returns:
            A list of objects with 'timestamp' and 'water_pumped' fields.
        """
        return self._do_get('SELECT * FROM watering_events',
                            WateringEventRecord)
