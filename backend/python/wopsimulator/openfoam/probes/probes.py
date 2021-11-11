import os
import re
import math
import time
from threading import Thread, Lock
from typing import Union, List

from backend.python.wopsimulator.openfoam.common.parsing import VECTOR_PATTERN, NUMBER_PATTERN, get_latest_time

Num = Union[int, float, None]

PROBE_DICT_FILE_TEMPLATE = \
    r"""/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Version:  7
     \\/     M anipulation  |
-------------------------------------------------------------------------------
Description
    Writes out values of fields from cells nearest to specified locations.

\*---------------------------------------------------------------------------*/

#includeEtc "caseDicts/postProcessing/probes/probes.cfg"

fields (%s);
region %s;
functionObjectLibs ("libsampling.so");
probeLocations
(
%s
);
"""


def parse_probes_dict(dict_path: str,
                      on_field=lambda line, fields_str, fields: line,
                      on_region=lambda line, region: line,
                      on_location=lambda line, location_str, location: line,
                      on_location_end=lambda: ''):
    """
    A common function for parsing the probes dict
    Parses a probes dictionary at a specific location and calls the attached
    callbacks once it encounters field, region, location or end of location
    One can attach callbacks as arguments and change the lines provided
    to the callback and/or store the parsed data
    If a line is required to be skipped - return "" instead of the line in a callback and it would not be written
    :param dict_path: path to probes dictionary file
    :param on_field: on field found callback, must be of form: f(line, fields_str, fields): return line
    :param on_region: on region found callback, must be of form: f(line, region): return line
    :param on_location: on location found callback, must be of form: f(line, location_str, location): return line
    :param on_location_end: on location end found callback, must be of form: f(): return [str]
    :return: modified probes dictionary lines as a list
    """
    lines = open(dict_path, 'r').readlines()
    new_lines = []
    fields_pattern = re.compile(r'^\s*fields\s*\(([\w\s]*)\);\n*$')
    region_pattern = re.compile(r'^\s*region\s*([\w]+);\n*$')
    probe_loc_pattern = re.compile(f'{VECTOR_PATTERN}')
    probe_end_pattern = re.compile(r'^\);$')
    for line in lines:
        if '//' in line[:2]:
            continue
        fields_match = fields_pattern.search(line)
        if fields_match:
            line = on_field(line, fields_match.group(1), fields_match.group(1).split())
        region_match = region_pattern.search(line)
        if region_match:
            line = on_region(line, region_match.group(1))
        probe_loc_match = probe_loc_pattern.search(line)
        if probe_loc_match:
            cur_probe_loc = [float(probe_loc_match.group(i)) for i in range(1, 4)]
            line = on_location(line, probe_loc_match.group(), cur_probe_loc)
        if probe_end_pattern.match(line):
            new_line = on_location_end()
            if new_line:
                new_lines.append(new_line)
        if line != '':
            new_lines.append(line)
    return new_lines


class Probe:
    """
    Probe class that represents a single probe for a specific field in a specific location
    """
    _dict_path = ''
    _instances = []
    _fields = set()
    _regions = set()

    def __new__(cls, case_dir: str, field: str, region: str, location: List[Num]):
        """
        Probe class creator
        Allows to remember all the existing instances of probes for the ProbeParser to use later
        If probe dictionary does not exist - creates it
        :param case_dir: case directory
        :param field: probe field (e.g., T)
        :param region: region to probe
        :param location: probe location
        """
        cls._dict_path = f'{case_dir}/system/probes'
        if not os.path.exists(cls._dict_path):
            location_str = f'{" " * 4}({" ".join([str(l) for l in location])})\n'
            with open(cls._dict_path, 'w') as f:
                f.writelines(PROBE_DICT_FILE_TEMPLATE % (field, region, location_str))
        instance = super(Probe, cls).__new__(cls)
        cls._fields.add(field)
        cls._regions.add(region)
        cls._instances.append(instance)
        return instance

    def __init__(self, case_dir: str, field: str, region: str, location: List[Num]):
        """
        Probe class initialization function
        :param case_dir: case directory
        :param field: probe field (e.g., T)
        :param region: region to probe
        :param location: probe location
        """
        self._case_dir = case_dir
        self._added = False
        self.field = field
        self.region = region
        self.location = location
        self.value = 0
        self.time = 0
        self._add_probe_to_dict()

    def _on_region_callback(self, line, region):
        """
        Callback for a probe parsing function, which is called when a region is found
        Used to change a region if it doesn't correspond to probe's region
        :param line: document line string
        :param region: region (e.g., 'fluid')
        :return: document line string
        """
        # FIXME: potential error if some probes use other regions
        if region != self.region:
            # TODO: check if one can append different regions (probably not)
            line.replace(region, self.region)
        return line

    def _on_field_callback(self, line, fields_str, fields):
        """
        Callback for a probe parsing function, which is called when a field is found
        Used to add a current probe's field to probes dictionary
        :param line: document line string
        :param fields_str: fields match string (e.g., '("T" "U")')
        :param fields: fields as list (e.g., ['T', 'U', ...]
        :return: document line string
        """
        if self.field not in fields:
            fields.append(self.field)
            line = line.replace(fields_str, ' '.join(fields))
        return line

    def _on_location_callback(self, line, location_str, location):
        """
        Callback for a probe parsing function, which is called when a location is found
        Used to check whether a current probe's location is added to probes dictionary
        :param line: document line string
        :param location_str: location match string
        :param location: location as coordinates [x, y, z]
        :return: document line string
        """
        if all([1 if math.isclose(probe1, probe2, abs_tol=0.5) else 0
                for probe1, probe2 in zip(self.location, location)]):
            self.location = location
            self._added = True
        return line

    def _on_location_end_callback(self):
        """
        Callback for a probe parsing function, which is called when a location end is found
        Used to add current probe's location to probes dictionary if it was not there
        :return: document line string
        """
        string = ''
        if not self._added:
            string = f'{" " * 4}({" ".join([str(l) for l in self.location])})\n'
        return string

    def _add_probe_to_dict(self):
        """
        Adds probe to probe dict
        """
        new_lines = parse_probes_dict(self.__class__._dict_path,
                                      on_field=self._on_field_callback,
                                      on_region=self._on_region_callback,
                                      on_location=self._on_location_callback,
                                      on_location_end=self._on_location_end_callback)
        with open(self.__class__._dict_path, 'w') as f:
            f.writelines(new_lines)


class ProbeParser(Thread):
    """
    Probe parser class, which represents a probe
    results parsing thread
    """

    def __init__(self, case_dir, period: int = 0.001):
        """
        Probe parser initialization function
        :param case_dir: case directory
        :param period: parsing period
        """
        self._case_dir = case_dir
        self.running = False
        self._mutex = Lock()
        self._num_of_probes = 0
        self.parsing_period = period
        super(ProbeParser, self).__init__(daemon=True)

    def _on_location_count(self, line, location_str, location):
        """
        Callback for a probe parsing function, which is called when a location is found
        Used for counting the probes used in probe dictionary
        :param line: document line string
        :param location_str: location match string
        :param location: location as coordinates [x, y, z]
        :return: document line string
        """
        self._num_of_probes += 1
        return line

    def _get_number_of_probes(self):
        """
        Reads probe dictionary if it exists and returns number of probes in it
        This number doesn't have to necessarily match the number of probes defined
        in the scripts as some locations might be unused in the code
        """
        self._num_of_probes = 0
        probe_dict = f'{self._case_dir}/system/probes'
        if os.path.exists(probe_dict):
            parse_probes_dict(probe_dict, on_location=self._on_location_count)

    def _parse_region(self, region):
        """
        Checks the postProcessing folder for probes data
        Opens the corresponding fields data, parses last line
        and saves it to corresponding probe.
        """
        path_to_probes_data = f'{self._case_dir}/postProcessing/probes/{region}'
        scalar_pattern = f'^\\s*({NUMBER_PATTERN})\\s+'
        vector_pattern = f'^\\s*({NUMBER_PATTERN})\\s+'
        for _ in range(self._num_of_probes + 1):
            scalar_pattern += f'({NUMBER_PATTERN})\\s*'
            vector_pattern += f'{VECTOR_PATTERN}\\s*'
        scalar_pattern = re.compile(scalar_pattern)
        vector_pattern = re.compile(vector_pattern)
        region_probes = [[num, probe] for num, probe in enumerate(Probe._instances) if probe.region == region]
        for field in Probe._fields:
            try:
                latest_result = get_latest_time(path_to_probes_data)
            except FileNotFoundError:
                latest_result = 0
            path_to_probes_field = f'{path_to_probes_data}/{latest_result}/{field}'
            if os.path.exists(path_to_probes_field):
                field_probes = [[num, probe] for num, probe in region_probes if probe.field == field]
                with open(path_to_probes_field, 'rb') as f:
                    f.seek(-2, os.SEEK_END)
                    while f.read(1) != b'\n':
                        f.seek(-2, os.SEEK_CUR)
                    last_line = f.readline().decode()
                scalar_match = scalar_pattern.search(last_line)
                vector_match = vector_pattern.search(last_line)
                for number, probe in field_probes:
                    if vector_match:
                        probe.time = float(vector_match.group(1))
                        probe.value = [float(vector_match.group(3 * number + 2 + i)) for i in range(3)]
                    elif scalar_match:
                        probe.time = float(scalar_match.group(1))
                        probe.value = float(scalar_match.group(number + 2))

    @staticmethod
    def _on_field_remove(line, fields_str, fields, used_fields):
        """
        Callback for a probe parsing function, which is called when a field is found
        Used to replace the fields in probe dictionary with used fields
        :param line: document line string
        :param fields_str: fields match string (e.g., '("T" "U")')
        :param fields: fields as list (e.g., ['T', 'U', ...]
        :param used_fields: used fields as list (e.g., ['T', 'U', ...]
        :return: document line string
        """
        return line.replace(fields_str, ' '.join(used_fields))

    @staticmethod
    def _on_location_remove(line, location_str, location, used_locations):
        """
        Callback for a probe parsing function, which is called when a location is found
        Used to remove unused locations from probes dictionary
        :param line: document line string
        :param location_str: location match string
        :param location: location as coordinates [x, y, z]
        :param used_locations: used probe locations [[x, y, z], [x, y, z], ...]
        :return: document line string
        """
        if location not in used_locations:
            line = ''
        return line

    def remove_unused(self):
        """
        Removes unused probes and fields from a probe dictionary,
        counts the amount of used probes
        """
        probe_dict = f'{self._case_dir}/system/probes'
        if not os.path.exists(probe_dict):
            self._num_of_probes = 0
            return
        probe_locations = [probe.location for probe in Probe._instances]
        new_lines = parse_probes_dict(
            probe_dict,
            on_field=lambda line, fields_str, fields: self._on_field_remove(line, fields_str, fields,
                                                                            Probe._fields),
            on_location=lambda line, loc_str, loc: self._on_location_remove(line, loc_str, loc, probe_locations)
        )
        with open(probe_dict, 'w') as f:
            f.writelines(new_lines)
        self._num_of_probes = len(probe_locations)

    def run(self):
        """Thread function to parse data"""
        if not Probe._instances:
            # No probes were initialized
            return
        self.running = True
        self.remove_unused()
        self._mutex.acquire()
        print('Starting probe parser thread')
        while self.running:
            for region in Probe._regions:
                self._parse_region(region)
            time.sleep(self.parsing_period)
        print('Quiting probe parser thread')
        self._mutex.release()

    def stop(self):
        """Stops parsing thread"""
        self.running = False
        self._mutex.acquire()
        self._mutex.release()


if __name__ == '__main__':
    case = '.'
    temperature_probe = Probe(case, 'T', 'fluid', [1, 2, 1])
    parser = ProbeParser(case)
    parser.remove_unused()
    parser.start()
