import os

from .objects.door import WopDoor
from .objects.heater import WopHeater
from .objects.room import WopRoom
from .objects.window import WopWindow
from .objects.wopthings import WopSensor

CUR_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
PY_BACKEND_DIR = os.path.realpath(f'{CUR_FILE_DIR}/../')

WOP_CONFIG_FILE = 'wop.config.json'

# Cases
CONFIG_TYPE_KEY = 'type'
CONFIG_PATH_KEY = 'path'
CONFIG_BLOCKING_KEY = 'blocking'
CONFIG_PARALLEL_KEY = 'parallel'
CONFIG_MESH_QUALITY_KEY = 'mesh_quality'
CONFIG_CLEAN_LIMIT_KEY = 'clean_limit'
CONFIG_CORES_KEY = 'cores'
CONFIG_INITIALIZED_KEY = 'initialized'
CONFIG_STARTED_TIMESTAMP_KEY = 'started_timestamp'
CONFIG_REALTIME_KEY = 'realtime'
CONFIG_END_TIME_KEY = 'end_time'

CONFIG_CASE_KEYS = [
    CONFIG_TYPE_KEY,
    CONFIG_MESH_QUALITY_KEY,
    CONFIG_CLEAN_LIMIT_KEY,
    CONFIG_PARALLEL_KEY,
    CONFIG_CORES_KEY,
    CONFIG_REALTIME_KEY,
    CONFIG_END_TIME_KEY
]

DEFAULT_MESH_QUALITY = 50
DEFAULT_CLEAN_LIMIT = 0
DEFAULT_PARALLEL = True
DEFAULT_CORES = 4
DEFAULT_REALTIME = True
DEFAULT_END_TIME = 1000

CONFIG_DEFAULTS = {
    CONFIG_MESH_QUALITY_KEY: DEFAULT_MESH_QUALITY,
    CONFIG_CLEAN_LIMIT_KEY: DEFAULT_CLEAN_LIMIT,
    CONFIG_PARALLEL_KEY: DEFAULT_PARALLEL,
    CONFIG_CORES_KEY: DEFAULT_CORES,
    CONFIG_REALTIME_KEY: DEFAULT_REALTIME,
    CONFIG_END_TIME_KEY: DEFAULT_END_TIME
}

# Objects
CONFIG_OBJ_NAME_KEY = 'name'
CONFIG_OBJ_DIMENSIONS = 'dimensions'
CONFIG_OBJ_ROTATION = 'rotation'
CONFIG_OBJ_MATERIAL = 'material'
CONFIG_SNS_FIELD = 'field'
CONFIG_LOCATION = 'location'
CONFIG_TEMPLATE = 'template'
CONFIG_URL = 'url'
CONFIG_CUSTOM = 'custom'
CONFIG_TEMPERATURE_KEY = 'temperature'
CONFIG_VELOCITY_KEY = 'velocity'

# Specific cases data
CHT_ROOM_OBJ_TYPES = [
    WopHeater.type_name,
    WopWindow.type_name,
    WopRoom.type_name,
    WopDoor.type_name,
    WopSensor.type_name,
    # TODO:
    'furniture',
]
CONFIG_MATERIAL_KEY = 'material'
DEFAULT_MATERIAL = 'air'
CONFIG_CASE_KEYS.append(CONFIG_MATERIAL_KEY)
CONFIG_DEFAULTS.update({CONFIG_MATERIAL_KEY: DEFAULT_MATERIAL})
CONFIG_BACKGROUND_KEY = 'background'
DEFAULT_BACKGROUND = 'fluid'
CONFIG_CASE_KEYS.append(CONFIG_BACKGROUND_KEY)
CONFIG_DEFAULTS.update({CONFIG_BACKGROUND_KEY: DEFAULT_BACKGROUND})

CONFIG_WALLS_KEY = 'walls'
CONFIG_NAME_KEY = 'name'
CONFIG_HEATERS_KEY = 'heaters'
CONFIG_WINDOWS_KEY = 'windows'
CONFIG_DOORS_KEY = 'doors'
CONFIG_SENSORS_KEY = 'sensors'
