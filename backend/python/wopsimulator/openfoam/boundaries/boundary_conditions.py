import re
import os

from .boundary_types import GeometricBoundary, GeneralBoundary, InletBoundary, OutletBoundary, WallBoundary, \
    CoupledBoundary, GEOMETRIC_BOUNDARY_TYPES, GENERAL_BOUNDARY_TYPES, INLET_BOUNDARY_TYPES, OUTLET_BOUNDARY_TYPES, \
    WALL_BOUNDARY_TYPES, COUPLED_BOUNDARY_TYPES
from ..common.filehandling import get_numerated_dirs
from ..common.parsing import NUMBER_PATTERN, VECTOR_PATTERN

BOUNDARY_NEXT_PLACEHOLDER = '// next'

BOUNDARY_CONDITION_FILE_TEMPLATE = \
    r"""/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Version:  7
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       %s;%s
    object      %s;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      %s;

boundaryField
{
%s
    #includeEtc "caseDicts/setConstraintTypes"
}

// ************************************************************************* //
"""


class BoundaryConditionBase:
    _case_dir = ''
    _filepath = ''
    _filepath_latest = ''
    _file_lines = {}

    def __init__(self, case_dir, field, field_class, dimensions, region=None):
        # TODO: add a possibility to init from template?
        self._case_dir = case_dir
        self._filepath = f'{case_dir}/0/{(region + "/") if region else ""}{field}'
        self._field = field
        self._region = region
        self.initial = {}
        self.latest = {}
        self.latest_timestep = 0
        if os.path.exists(self._filepath):
            self._parse_file(self._filepath, self.initial)
        else:
            self._create_file(field_class, dimensions)

    def __getitem__(self, item):
        return self.__dict__[item]

    @staticmethod
    def _get_class_by_boundary_type(boundary_type):
        if boundary_type in GEOMETRIC_BOUNDARY_TYPES:
            return GeometricBoundary
        if boundary_type in GENERAL_BOUNDARY_TYPES:
            return GeneralBoundary
        elif boundary_type in INLET_BOUNDARY_TYPES:
            return InletBoundary
        elif boundary_type in OUTLET_BOUNDARY_TYPES:
            return OutletBoundary
        elif boundary_type in WALL_BOUNDARY_TYPES:
            return WallBoundary
        elif boundary_type in COUPLED_BOUNDARY_TYPES:
            return CoupledBoundary
        else:
            raise ValueError('TODO error')

    # def _parser(self, filepath, func, **kwargs):

    def _parse_file(self, filepath, boundary_dict, add_placeholder=True):
        lines = open(filepath).readlines()
        boundaries_found = False
        new_boundary = True
        # name_pattern = re.compile('^ *([a-zA-Z]+(_[a-zA-Z]+)*|\"\.\*\")\s*$')
        name_pattern = re.compile('^ *([a-zA-Z][a-zA-Z0-9_.-]*|\"\.\*\")\s*$')
        type_pattern = re.compile('^\s*type\s*(\w*|\w*:*\w*);\s*$')
        parameter_pattern = re.compile(
            f'^\s*(\w+)\s*(uniform)?\s*(\$?\w*|{NUMBER_PATTERN}\(?\)?|{VECTOR_PATTERN});\s*$')
        internal_field_pattern = re.compile(
            f'^\s*(internalField)\s*(uniform)?\s*(\$?\w*|{NUMBER_PATTERN}\(?\)?|{VECTOR_PATTERN});')
        # list_pattern = re.compile('(internalField|value)\s*((nonuniform)?\s+List<(scalar|vector)>)')
        list_pattern = re.compile('(internalField|value)\s*((nonuniform)?\s+List<(scalar|vector)>) *(\d*)?')
        list_start_found = False
        list_found = False
        list_name = ''
        name = ''
        num_of_lines = 0
        cls_instance = None
        placeholder_found = False
        end_reached = False
        new_lines = []
        for line in lines:
            if not end_reached:
                if BOUNDARY_NEXT_PLACEHOLDER in line:
                    placeholder_found = True
                internal_field_match = internal_field_pattern.search(line)
                if internal_field_match:
                    boundary_dict.update({'internalField': {}})
                    if internal_field_match.group(2):
                        boundary_dict['internalField'].update({'is_uniform': True})
                    else:
                        boundary_dict['internalField'].update({'is_uniform': False})
                    if not internal_field_match.group(3):
                        if internal_field_match.group(4).isnumeric() and internal_field_match.group(5).isnumeric() and \
                                internal_field_match.group(6).isnumeric():
                            value = [
                                float(internal_field_match.group(4)),
                                float(internal_field_match.group(5)),
                                float(internal_field_match.group(6))
                            ]
                        else:
                            value = [
                                internal_field_match.group(4),
                                internal_field_match.group(5),
                                internal_field_match.group(6)
                            ]
                    else:
                        if internal_field_match.group(3).isnumeric():
                            value = float(internal_field_match.group(3))
                        else:
                            value = internal_field_match.group(3)
                    boundary_dict['internalField'].update({'value': value})
                if list_found:
                    if '(' in line:
                        list_start_found = True
                    elif ')' in line:
                        list_start_found = False
                        list_found = False
                    elif list_start_found:
                        val = line.strip()
                        # scalar_pattern = re.compile(NUMBER_PATTERN)
                        # scalar_match = scalar_pattern.search(val)
                        vector_pattern = re.compile(VECTOR_PATTERN)
                        vector_match = vector_pattern.search(val)
                        if vector_match:
                            value = [vector_match.group(i) for i in range(1, 4)]
                        else:
                            value = float(val)
                        if name:
                            cls_instance.__dict__.update({list_name: value})
                        else:
                            boundary_dict[list_name] = value
                list_match = list_pattern.search(line)
                if list_match:
                    if list_match.group(5):
                        # TODO: vector inline list!
                        list_name = list_match.group(1)
                        list_length = int(list_match.group(5))
                        inline_list_pattern_str = f'({NUMBER_PATTERN}) *' * list_length
                        inline_list_pattern = re.compile(f'\({inline_list_pattern_str}\)')
                        inline_list_match = inline_list_pattern.search(line)
                        inline_list_values = [float(inline_list_match.group(i)) for i in range(1, list_length + 1)]
                        value_avg = sum(inline_list_values) / list_length
                        if name:
                            cls_instance.__dict__.update({list_name: value_avg})
                        else:
                            boundary_dict[list_name] = value_avg
                    else:
                        list_found = True
                        list_name = list_match.group(1)
                if boundaries_found:
                    if line.strip()[:2] == '//' and BOUNDARY_NEXT_PLACEHOLDER not in line:
                        continue
                    name_match = name_pattern.match(line)
                    if name_match:
                        name = name_match.group(1)
                        name = name if name != '".*"' else 'other_boundaries'
                        new_boundary = True
                    if new_boundary:
                        type_match = type_pattern.match(line)
                        parameter_match = parameter_pattern.match(line)
                        if '}' in line:
                            new_boundary = False
                            self._file_lines.update({name: num_of_lines})
                            boundary_dict.update({name: cls_instance})
                            name = None
                            cls_instance = None
                            num_of_lines = 0
                            new_lines.append(line)
                            continue
                        num_of_lines += 1
                        if type_match:
                            b_type = type_match.group(1)
                            cls_instance = self._get_class_by_boundary_type(b_type)(None, empty_instance=True)
                            cls_instance.__dict__.update({'type': b_type})
                        elif parameter_match:
                            if parameter_match.group(2):
                                cls_instance.__dict__.update({'is_uniform': True})
                            if not parameter_match.group(3):
                                if parameter_match.group(4).isnumeric() and parameter_match.group(5).isnumeric() and \
                                        parameter_match.group(6).isnumeric():
                                    cls_instance.__dict__.update({
                                        parameter_match.group(1): [
                                            float(parameter_match.group(4)),
                                            float(parameter_match.group(5)),
                                            float(parameter_match.group(6))
                                        ]
                                    })
                                else:
                                    cls_instance.__dict__.update({
                                        parameter_match.group(1): [
                                            parameter_match.group(4),
                                            parameter_match.group(5),
                                            parameter_match.group(6)
                                        ]
                                    })
                            else:
                                if parameter_match.group(3).isnumeric():
                                    value = float(parameter_match.group(3))
                                else:
                                    value = parameter_match.group(3)
                                cls_instance.__dict__.update({parameter_match.group(1): value})
                    elif '}' in line:
                        if not placeholder_found:
                            new_lines.append(f'{BOUNDARY_NEXT_PLACEHOLDER}\n')
                            end_reached = True
                        else:
                            break
                if 'boundaryField' in line:
                    boundaries_found = True
            new_lines.append(line)
        if not placeholder_found and add_placeholder:
            with open(filepath, 'w') as f:
                f.writelines(new_lines)

    def _create_file(self, field_class, dimensions):
        with open(self._filepath, 'w') as f:
            location = ''
            if self._field == 'cellToRegion':
                location = f'\n{" " * 4}location{" " * 4}"0/{self._region}";'
            f.writelines(BOUNDARY_CONDITION_FILE_TEMPLATE % (field_class, location, self._field, dimensions,
                                                             BOUNDARY_NEXT_PLACEHOLDER))

    def _add_boundary_to_file(self, name):
        if (boundary := self.initial[name]) is not None:
            boundary_data = str(boundary)
            boundary_data = boundary_data.replace('\n', f'\n{" " * 4}')
            name = name if name != "other_boundaries" else '".*"'
            boundary_data = f'{" " * 4}{name}{boundary_data}'
            lines = open(self._filepath).readlines()
            new_line = []
            placeholder_found = False
            for idx, line in enumerate(lines):
                if BOUNDARY_NEXT_PLACEHOLDER in line:
                    placeholder_found = True
                    if lines[idx - 1][0] != '\n':
                        new_line.append('\n')
                    new_line.append(f'{boundary_data}\n')
                    num_of_lines = boundary_data.count('\n')
                    self._file_lines.update({name: num_of_lines})
                new_line.append(line)
            if not placeholder_found:
                raise Exception(f'Error adding boundary to file "{self._filepath}"\n'
                                f'Placeholder "{BOUNDARY_NEXT_PLACEHOLDER}" not detected.')
            with open(self._filepath, 'w') as f:
                f.writelines(new_line)

    def _remove_boundary_from_file(self, name):
        lines = open(self._filepath).readlines()
        num_of_lines = self._file_lines[name] + 1
        new_lines = []
        name_found = False
        for idx, line in enumerate(lines):
            if not name_found and f'{name}\n' in line:
                new_lines.pop(idx - 1)
                name_found = True
            if name_found and num_of_lines:
                num_of_lines -= 1
            else:
                new_lines.append(line)
        with open(self._filepath, 'w') as f:
            f.writelines(new_lines)

    def _change_latest_boundaries(self):
        # TODO: parse the last boundary file and replace the old values with the new values.
        pass

    def update_latest_boundaries(self, latest_timestep, is_run_parallel=False):
        # TODO: account for processors
        # TODO: parse the latest boundary file and get the values to the "latest" dict
        self.latest_timestep = latest_timestep
        if is_run_parallel:
            processor_dirs = get_numerated_dirs(self._case_dir, 'processor')
            for processor_dir in processor_dirs:
                self._filepath_latest = f'{self._case_dir}/{processor_dir}/{latest_timestep}/{self._region}/{self._field}'
                if os.path.exists(self._filepath_latest):
                    self._parse_file(self._filepath_latest, self.latest, add_placeholder=False)
                # lines = open(self._filepath).readlines()
                # if any('boundaryField' in line for line in lines):
                #     break
                # raise Exception('no boundary field found in processor dirs!')
        else:
            self._filepath_latest = f'{self._case_dir}/{latest_timestep}/{self._region}/{self._field}'
            if os.path.exists(self._filepath_latest):
                self._parse_file(self._filepath_latest, self.latest, add_placeholder=False)

    def _save_latest_boundaries(self, filepath):
        if not os.path.exists(filepath):
            return
        lines = open(filepath).readlines()
        boundaries_found = False
        name_pattern = re.compile('^ *([a-zA-Z][a-zA-Z0-9_.-]*|\"\.\*\")\s*$')
        type_pattern = re.compile('^\s*type\s*(\w*|\w*:*\w*);\s*$')
        parameter_pattern = re.compile(
            f'^\s*(\w+)\s*((uniform\s*)?(\$?\w*|{NUMBER_PATTERN}\(?\)?|'
            f'\({NUMBER_PATTERN}\s*{NUMBER_PATTERN}\s*{NUMBER_PATTERN}\)));\s*$')
        # value_list_pattern = re.compile('(value)\s*((nonuniform)?\s+List<(scalar|vector)>)')
        list_pattern = re.compile('(internalField|value)\s*((nonuniform)?\s+List<(scalar|vector)>) *(\d*)?')
        end_reached = False
        list_name = ''
        list_found = False
        list_start_found = False
        new_lines = []
        current_boundary = None
        read_attr = []
        offset = 0
        for idx, line in enumerate(lines):
            idx += offset  # check if works as intended
            new_lines.append(line)
            if not end_reached:
                # value_list_match = value_list_pattern.search(line)
                list_match = list_pattern.search(line)
                if list_found:
                    if '(' in line:
                        list_start_found = True
                    elif ')' in line:
                        list_start_found = False
                        list_found = False
                        list_name = ''
                    elif list_start_found:
                        if list_name in self.latest:
                            new_lines[idx] = f'{self.latest[list_name]}\n'
                        else:
                            new_lines[idx] = f'{current_boundary[list_name]}\n'
                if list_match:
                    if list_match.group(5):
                        list_name = list_match.group(1)
                        list_length = int(list_match.group(5))
                        if list_name in self.latest:
                            value_str = str(self.latest[list_name])
                        else:
                            value_str = str(current_boundary[list_name])
                        value_list_string = ' '.join([value_str for _ in range(list_length)])
                        new_lines[idx] = f'{new_lines[idx][:list_match.end()]}({value_list_string});\n'
                    else:
                        list_found = True
                        list_name = list_match.group(1)
                if boundaries_found:
                    name_match = name_pattern.match(line)
                    if name_match:
                        name = name_match.group(1)
                        name = name if name != '".*"' else 'other_boundaries'
                        current_boundary = self.latest[name]  # It should be there, but maybe can check for error
                    if current_boundary:
                        type_match = type_pattern.match(line)
                        parameter_match = parameter_pattern.match(line)
                        if '}' in line:
                            if remaining_attr := list(set(current_boundary.__dict__.keys()) - set(read_attr)):
                                for attr_name in remaining_attr:
                                    if attr_name == 'type' or attr_name == 'is_uniform' or attr_name == 'value':
                                        continue
                                    # TODO: needs to be tested!
                                    attr = current_boundary.__dict__[attr_name]
                                    new_lines.insert(idx, f'{" " * 8}{attr_name} {attr};\n')
                                    offset += 1
                            current_boundary = None
                            read_attr = []
                            continue
                        if type_match:
                            b_type = type_match.group(1)
                            new_lines[idx] = new_lines[idx].replace(b_type, current_boundary['type'])
                        elif parameter_match:
                            value_name = parameter_match.group(1)
                            if value_name in current_boundary.__dict__.keys():
                                read_attr.append(value_name)
                                old_value = parameter_match.group(2)
                                value_name_small = value_name.lower()
                                new_value = ''
                                if 'is_uniform' in current_boundary.__dict__.keys() and current_boundary[
                                    'is_uniform'] and \
                                        'value' != value_name_small and \
                                        ('value' in value_name_small or 'gradient' in value_name_small) and \
                                        (old_value.split(' ')[-1].isnumeric() or '(' in old_value):
                                    new_value = 'uniform '
                                if isinstance((value := current_boundary[value_name]), list):
                                    new_value += f'({" ".join([str(num) for num in value])})'
                                else:
                                    new_value += f'{value}'
                                new_lines[idx] = new_lines[idx].replace(old_value, new_value)
                            else:
                                # This values is no longer used, delete it
                                new_lines.pop(idx)
                                offset -= 1
                        # elif value_list_match and 'value' in current_boundary.__dict__:
                        # elif list_match and ('value' in current_boundary.__dict__ or 'value' in self.latest):
                    elif '}' in line:
                        end_reached = True
                if 'boundaryField' in line:
                    boundaries_found = True
        with open(filepath, 'w') as f:
            f.writelines(new_lines)

    def save_latest_boundaries(self, is_run_parallel=False):
        # TODO: get latest boundaries and replace the lines in the latest file. Again, to replace I need to parse each
        #  string and if it is a match - replace the necessary data there
        if is_run_parallel:
            processor_dirs = get_numerated_dirs(self._case_dir, 'processor')
            for processor_dir in processor_dirs:
                filepath = f'{self._case_dir}/{processor_dir}/{self.latest_timestep}/{self._region}/{self._field}'
                self._save_latest_boundaries(filepath)
        else:
            self._save_latest_boundaries(self._filepath_latest)

    def add_initial_boundary(self, name, boundary_type, **kwargs):
        if name in self.initial:
            self._remove_boundary_from_file(name)
        cls_instance = self._get_class_by_boundary_type(boundary_type)(boundary_type, **kwargs)
        self.__dict__.update({name: cls_instance})
        self._add_boundary_to_file(name)

    def save_initial_internal_field(self):
        lines = open(self._filepath).readlines()
        new_lines = []
        internal_field_pattern = re.compile(
            f'^\s*(internalField)\s*(uniform)?\s*(\$?\w*|{NUMBER_PATTERN}\(?\)?|{VECTOR_PATTERN});')
        for idx, line in enumerate(lines):
            new_lines.append(line)
            internal_field_match = internal_field_pattern.search(line)
            if internal_field_match and internal_field_match.group(1):
                if isinstance(self.initial['internalField']['value'], list):
                    value = f'({" ".join(self.initial["internalField"]["value"])[:-1]})'
                else:
                    value = self.initial['internalField']['value']
                new_lines[idx] = f'internalField{" " * 4}' \
                                 f'{"uniform " if self.initial["internalField"]["is_uniform"] else ""}' \
                                 f'{value};\n'
        with open(self._filepath, 'w') as f:
            f.writelines(new_lines)

    def save_initial_boundary(self, name):
        if name not in self.initial:
            raise Exception('TODO: EXCEPTION')
        self._remove_boundary_from_file(name)
        self._add_boundary_to_file(name)

    def delete_initial_boundary(self, name):
        self._remove_boundary_from_file(name)
        del self.__dict__[name]
        del self._file_lines[name]


class BoundaryConditionT(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionT, self).__init__(case_dir, 'T', 'volScalarField', '[0 0 0 1 0 0 0]', region)


class BoundaryConditionAlphat(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionAlphat, self).__init__(case_dir, 'alphat', 'volScalarField', '[1 -1 -1 0 0 0 0]', region)


class BoundaryConditionCellToRegion(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionCellToRegion, self).__init__(case_dir, 'cellToRegion', 'volScalarField',
                                                            '[0 0 0 0 0 0 0]', region)


class BoundaryConditionEpsilon(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionEpsilon, self).__init__(case_dir, 'epsilon', 'volScalarField',
                                                       '[0 2 -3 0 0 0 0]', region)


class BoundaryConditionK(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionK, self).__init__(case_dir, 'k', 'volScalarField', '[0 2 -2 0 0 0 0]', region)


class BoundaryConditionNut(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionNut, self).__init__(case_dir, 'nut', 'volScalarField', '[0 2 -1 0 0 0 0]', region)


class BoundaryConditionOmega(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionOmega, self).__init__(case_dir, 'omega', 'volScalarField', '[0 0 -1 0 0 0 0]', region)


class BoundaryConditionP(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionP, self).__init__(case_dir, 'p', 'volScalarField', '[1 -1 -2 0 0 0 0]', region)


class BoundaryConditionPrgh(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionPrgh, self).__init__(case_dir, 'p_rgh', 'volScalarField', '[1 -1 -2 0 0 0 0 ]', region)


class BoundaryConditionU(BoundaryConditionBase):
    def __init__(self, case_dir, region=None):
        super(BoundaryConditionU, self).__init__(case_dir, 'U', 'volVectorField', '[0 1 -1 0 0 0 0]', region)


BOUNDARY_CONDITION_CLASSES = {
    'T': BoundaryConditionT,
    'U': BoundaryConditionU,
    'p_rgh': BoundaryConditionPrgh,
    'p': BoundaryConditionP,
    'omega': BoundaryConditionOmega,
    'alphat': BoundaryConditionAlphat,
    'cellToRegion': BoundaryConditionCellToRegion,
    'epsilon': BoundaryConditionEpsilon,
    'k': BoundaryConditionK,
    'nut': BoundaryConditionNut,
}


def get_boundary_condition_class_by_field(field):
    if field in BOUNDARY_CONDITION_CLASSES:
        return BOUNDARY_CONDITION_CLASSES[field]
    else:
        print(f'No such field known: "{field}"')
        return None


if __name__ == '__main__':
    t_boundary_cond = BoundaryConditionT('../../../cht_room', region='fluid')
    t_boundary_cond.add_initial_boundary('inlet2', 'outletInlet', outletValue=[1, 2, 3], value=[1, 2, 3],
                                         is_uniform=True)

    boundary_condition = BoundaryConditionBase('../../../cht_room', 'T', 'volScalarField', '[0 0 0 1 0 0 0]',
                                               region='fluid')
    boundary_condition.add_initial_boundary('inlet', 'outletInlet', outletValue=[1, 2, 3], value=[1, 2, 3],
                                            is_uniform=True)
    # boundary_condition.delete_boundary('inlet2')
    boundary_condition.inlet.value = [3, 2, 1]
    boundary_condition['inlet'].outletValue = [10, 20, 30]
    boundary_condition.save_initial_boundary('inlet')
    # boundary_condition.add_boundary('inlet', 'outletInlet', outletValue=[1, 2, 3], value=[1, 2, 3], is_uniform=True)
    print(1)
