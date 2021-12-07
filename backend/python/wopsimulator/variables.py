import os

from .objects.door import WopDoor
from .objects.heater import WopHeater
from .objects.room import WopRoom
from .objects.window import WopWindow
from .objects.wopthings import WopSensor

CUR_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
PY_BACKEND_DIR = os.path.realpath(f'{CUR_FILE_DIR}/../')

# Cases
CONFIG_TYPE_KEY = 'type'
CONFIG_PATH_KEY = 'path'
CONFIG_BLOCKING_KEY = 'blocking'
CONFIG_PARALLEL_KEY = 'parallel'
CONFIG_MESH_QUALITY_KEY = 'mesh_quality'
CONFIG_CLEAN_LIMIT_KEY = 'clean_limit'
CONFIG_CORES_KEY = 'cores'
CONFIG_INITIALIZED_KEY = 'initialized'
CONFIG_DICT = {
    CONFIG_TYPE_KEY: '',
    CONFIG_PATH_KEY: '',
    CONFIG_MESH_QUALITY_KEY: 50,
    CONFIG_CLEAN_LIMIT_KEY: 0,
    CONFIG_BLOCKING_KEY: False,
    CONFIG_PARALLEL_KEY: False,
    CONFIG_CORES_KEY: 1,
    CONFIG_INITIALIZED_KEY: False
}

# Objects
CONFIG_OBJ_NAME_KEY = 'name'
CONFIG_OBJ_DIMENSIONS = 'dimensions'
CONFIG_OBJ_ROTATION = 'rotation'
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
CONFIG_BACKGROUND_KEY = 'background'
CONFIG_WALLS_KEY = 'walls'
CONFIG_NAME_KEY = 'name'
CONFIG_HEATERS_KEY = 'heaters'
CONFIG_WINDOWS_KEY = 'windows'
CONFIG_DOORS_KEY = 'doors'
CONFIG_SENSORS_KEY = 'sensors'
