import re
import os
import time
from threading import Thread, Lock


class Probes:
    def __new__(cls, *args, **kwargs):
        if os.path.exists(f'{args[0]}/system/probes'):
            # Probes dictionary exists
            return super(Probes, cls).__new__(cls)
        else:
            # No probes are defined for this case.
            # Maybe in the future a new probes dict will be created here.
            # TODO: create a probes dict file if there is none
            return None

    def __init__(self, case_dir):
        self.case_dir = case_dir
        self.probes_dict_path = f'{case_dir}/system/probes'
        self.fields = []
        self.region = ''
        self.probes = []
        self.num_of_probes = 0
        self._locations = []
        self.running = False
        self.probes_mutex = Lock()
        self._read_probes_dict()
        self.data_read_thread = Thread(target=self._parse_probes_data_thread, daemon=True)

    def _add_probe_to_list(self, location):
        """
        Adds probe to probes list if it was not added before
        :param location: location of the probe
        :return:
        """
        if location not in self._locations:
            self.probes.append({el: 0 for el in self.fields})
            self.probes[self.num_of_probes]['location'] = location
            self.probes[self.num_of_probes]['alias'] = f'Probe {self.num_of_probes}'
            self.probes[self.num_of_probes]['time'] = 0
            self.num_of_probes += 1
            self._locations.append(location)
            return True
        return False

    def _read_probes_dict(self):
        """
        Reads probes dictionary
        :return:
        """
        lines = open(self.probes_dict_path).readlines()
        fields_pattern = re.compile('^\s*fields\s*\(([\w\s]*)\);$')  # TODO: consider the underscore case and so on
        region_pattern = re.compile('^\s*region\s*([\w]+);$')  # TODO: consider the underscore case and so on
        probe_loc_pattern = re.compile(
            '^\s+\(([+-]?[0-9]*[.]?[0-9]+)\s*([+-]?[0-9]*[.]?[0-9]+)\s*([+-]?[0-9]*[.]?[0-9]+)\)\s*$')  # TODO: take the common number if e.g. e-12
        for line in lines:
            fields_match = fields_pattern.search(line)
            if fields_match:
                self.fields = fields_match.group(1).split()
            region_match = region_pattern.search(line)
            if region_match:
                self.region = region_match.group(1)
            probe_loc_match = probe_loc_pattern.search(line)
            if probe_loc_match:
                self._add_probe_to_list(location=[float(probe_loc_match.group(i)) for i in range(1, 4)])

    def _parse_probes_data_thread(self):
        """
        Thread to parse data and (possibly) print it or plot it
        :return:
        """
        self.running = True
        self.probes_mutex.acquire()
        print('Starting thread monitor')
        while self.running:
            self.parse_probes_data()
            time.sleep(0.001)
            for probe in self.probes:
                if not self.running:
                    break
                probe_data_str = ' '.join([f'{field} - {probe[field]}' for field in self.fields])
                # print(f'{probe["alias"]}: Time - {probe["time"]} {probe_data_str}')
        print('Quiting thread monitor')
        self.probes_mutex.release()

    def start_parsing(self):
        self.data_read_thread = Thread(target=self._parse_probes_data_thread, daemon=True)
        self.data_read_thread.start()

    def stop_parsing(self):
        self.running = False
        self.probes_mutex.acquire()
        self.probes_mutex.release()

    def add_fields(self, fields):
        """
        Function to add new fields to monitor with probes
        :param fields: fields to monitor
        :return:
        """
        # TODO: should append the fields to the file if they don't exist
        raise NotImplementedError('Not yet implemented!')

    def add_region(self, region_name):
        """
        Function to add monitoring region to probes
        :param region_name: name of the region to monitor
        :return:
        """
        # TODO: should add a region field if doesn't exist. In single region it is not required to define the region
        raise NotImplementedError('Not yet implemented!')

    def add_probe(self, location):
        """
        Adds a probe with it's location to probes dict
        :param location: location of the probe
        :return:
        """
        location = [float(coord) for coord in location]
        lines = open(self.probes_dict_path).readlines()
        probe_location_found = False
        new_lines = lines.copy()
        for idx, line in enumerate(lines):
            if probe_location_found:
                if ');' in line:
                    if self._add_probe_to_list(location):
                        new_lines.insert(idx, ' ' * 4 + '(' + ' '.join([f'{loc}' for loc in location]) + ')\n')
            if 'probeLocations' in line:
                probe_location_found = True
        with open(self.probes_dict_path, 'w') as f:
            f.writelines(new_lines)

    def parse_probes_data(self):
        """
        Checks the postProcessing folder for probes data. Opens the corresponding fields data, parses last line
        and saves it to corresponding probe.
        :return:
        """
        path_to_probes_data = f'{self.case_dir}/postProcessing/probes/{self.region}'
        # Move these patterns to common ones
        number_pattern = r'[+-]?[0-9]*[.]?[0-9]+[e]?[+-]?[0-9]+'  # TODO: move this pattern to common one? Can parse any number
        scalar_pattern = f'^\s*({number_pattern})\s+'  # Time
        vector_pattern = f'^\s*({number_pattern})\s+'  # Time
        for _ in range(self.num_of_probes):
            scalar_pattern += f'({number_pattern})\s+'
            vector_pattern += f'\(\s*({number_pattern})\s+({number_pattern})\s+({number_pattern})\s*\)\s*'
        scalar_pattern = re.compile(scalar_pattern)
        vector_pattern = re.compile(vector_pattern)
        for field in self.fields:
            path_to_probes_field = f'{path_to_probes_data}/0/{field}'
            if os.path.exists(path_to_probes_field):
                with open(path_to_probes_field, 'rb') as f:
                    f.seek(-2, os.SEEK_END)
                    while f.read(1) != b'\n':
                        f.seek(-2, os.SEEK_CUR)
                    last_line = f.readline().decode()
                    scalar_match = scalar_pattern.search(last_line)
                    vector_match = vector_pattern.search(last_line)
                    if scalar_match:
                        for number, probe in enumerate(self.probes):
                            self.probes[number]['time'] = float(scalar_match.group(1))
                            self.probes[number][field] = float(scalar_match.group(number + 2))
                    elif vector_match:
                        for number, probe in enumerate(self.probes):
                            self.probes[number]['time'] = float(vector_match.group(1))
                            self.probes[number][field] = [float(vector_match.group(3 * number + 2 + i))
                                                          for i in range(3)]


if __name__ == '__main__':
    probes = Probes('../../../cht_room')
    probes.add_probe([1, 1, 1])
    probes.parse_probes_data()
