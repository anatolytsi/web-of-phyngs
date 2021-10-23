"""
Case loader
"""
import os
import json
from pathlib import Path

from .cht_room import ChtRoom
from .openfoam.common.filehandling import force_remove_dir, copy_tree

CUR_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH_KEY = 'path'
CONFIG_TYPE_KEY = 'type'
CASE_TYPES = {
    'cht_room': ChtRoom,
}


def load_case(case_name: str, config_path: str = './wop-config.json'):
    """
    Loads case from wop-config.json
    :param case_name: name of the loaded case
    :param config_path: path to a wop-config.json. A __main__ script directory is taken by default
    :return: WoP Simulator class and OpenFOAM case path
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    if case_name in config.keys():
        if CONFIG_PATH_KEY in config[case_name] and os.path.exists(path := config[case_name][CONFIG_PATH_KEY]):
            case_path = path
        else:
            raise OSError(f'Path for case "{case_name}" is not defined')
        if CONFIG_TYPE_KEY in config[case_name] and \
                (case_type_name := config[case_name][CONFIG_TYPE_KEY]) in CASE_TYPES.keys():
            case_cls = CASE_TYPES[case_type_name]
        else:
            raise ValueError(f'Case type is wrong or not specified! Expected one of: {", ".join(CASE_TYPES)}')
        return case_cls, case_path
    raise ValueError(f'Case "{case_name}" is not defined in the config "{config_path}"')


def create_case(case_name: str, case_type: str, case_dir_path: str = './',
                config_path: str = './wop-config.json', replace_old: bool = False):
    """
    Creates a new WoP Simulator case by finding a OpenFOAM case template by a specified type, copying it to a path
    specified, and adding all this data to a wop-config.json.
    :param case_name: name of the project to name a new copied case and to refer to from wop-config.json
    :param case_type: WoP Simulator case type
    :param case_dir_path: OpenFOAM case creation folder path. A __main__ script directory is taken by default
    :param config_path: path to a wop-config.json. A __main__ script directory is taken by default
    :param replace_old: flag to replace the old project. Active -> files will be overwritten. Otherwise -> error
    :return: WoP Simulator class and OpenFOAM case path
    """
    if case_type not in CASE_TYPES.keys():
        raise ValueError(f'Case type is wrong or not specified! '
                         f'Got "{case_type}", expected one of: {", ".join(CASE_TYPES)}')
    case_cls = CASE_TYPES[case_type]

    # Load/Create config
    Path(config_path).touch(exist_ok=True)
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.decoder.JSONDecodeError:
        config = {}

    # Get the case path, check if it already exists and the copy case
    case_name = case_name if '.case' in case_name else f'{case_name}.case'
    case_path = f'{case_dir_path}{"/" if case_dir_path[-1] != "/" else ""}{case_name}'
    if case_name in config.keys() or os.path.exists(case_path):
        if replace_old:
            del config[case_name]
            force_remove_dir(case_path)
        else:
            raise FileExistsError(f'Project with name "{case_name}" already exists!')
    copy_tree(f'{CUR_FILE_DIR}/openfoam/cases/{case_type}', case_path)

    config.update({
        case_name: {
            CONFIG_TYPE_KEY: case_type,
            CONFIG_PATH_KEY: case_path
        }
    })

    with open(config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    return case_cls, case_path


def remove_case(case_name: str, config_path: str = './wop-config.json', remove_case_dir: bool = False):
    """
    Removes case from wop-config.json (optionally OpenFOAM case dir as well)
    :param case_name: name of the case to remove
    :param config_path: path to a wop-config.json. A __main__ script directory is taken by default
    :param remove_case_dir: flag to remove a case dir by its path
    :return: None
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    if remove_case_dir and os.path.exists(case_path := config[case_name][CONFIG_PATH_KEY]):
        force_remove_dir(case_path)
    del config[case_name]

    with open(config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def main():
    print(CUR_FILE_DIR)


if __name__ == '__main__':
    main()
