from backend.python.wopsimulator.openfoam.common.filehandling import get_numerated_dirs

NUMBER_PATTERN = r'[+-]?[0-9]+[.]?[0-9]*[e]?[+-]?[0-9]*'
VECTOR_PATTERN = f'\\(\\s*({NUMBER_PATTERN})\\s+({NUMBER_PATTERN})\\s+({NUMBER_PATTERN})\\s*\\)\\s*'
FIELD_NAME_PATTERN = r'(\w+|\"\.\*\")\s+'
LIST_PATTERN = r'nonuniform\s+List<(scalar|vector)>\s*(\d+)\s*\(([^;]*)\)'
VALUE_PATTERN = f'(uniform)?\\s*(\\$?\\w*:*\\w*|{NUMBER_PATTERN}\\(?\\)?|{VECTOR_PATTERN})'
LIST_OR_VALUE_PATTERN = f'({VALUE_PATTERN}|{LIST_PATTERN})\\s*;'
BOUNDARY_FIELD_PATTERN = r'boundaryField\s+{\s+((.|\n)*)}'
BOUNDARY_BLOCK_PATTERN = f' *{FIELD_NAME_PATTERN}{{\\s+[^}}]*}}'
SPECIFIC_FIELD_PATTERN = r' *%s\s+{\s+[^}]*}'
SPECIFIC_FIELD_VALUES_PATTERN = r' *%s\s+{\s*([^}]*)}'
INTERNAL_FIELD_PATTERN = f'^\\s*internalField\\s+{LIST_OR_VALUE_PATTERN}'
SPECIAL_CHARACTERS = '"!@#$%^&*()-+?_=.,<>/'
SPECIFIC_VALUE_PATTERN = r' *%s\s+([^;]*);'


def get_latest_time(case_dir: str) -> float or int:
    """
    Returns latest time of the simulation that
    correspond to latest time result folder name
    :param case_dir: case directory
    :return: latest simulation time
    """
    try:
        latest_time = sorted([float(val) for val in get_numerated_dirs(case_dir, exception='0')])[-1]
        return int(latest_time) if latest_time.is_integer() else latest_time
    except IndexError:
        return 0
