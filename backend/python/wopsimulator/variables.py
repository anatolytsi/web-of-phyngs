import os

CUR_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
PY_BACKEND_DIR = os.path.realpath(f'{CUR_FILE_DIR}/../')

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
