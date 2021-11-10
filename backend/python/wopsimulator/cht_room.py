import time
from typing import List

from backend.python.wopsimulator.openfoam.interface import get_latest_time
from backend.python.wopsimulator.case_base import OpenFoamCase
from backend.python.wopsimulator.objects.door import WopDoor
from backend.python.wopsimulator.objects.room import WopRoom
from backend.python.wopsimulator.objects.window import WopWindow
from backend.python.wopsimulator.objects.heater import WopHeater
from backend.python.wopsimulator.objects.wopthings import WopSensor
from backend.python.wopsimulator.openfoam.common.filehandling import force_remove_dir

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
CONFIG_OBJ_DIMENSIONS = 'dimensions'
CONFIG_OBJ_ROTATION = 'rotation'
CONFIG_SNS_FIELD = 'field'
CONFIG_LOCATION = 'location'
CONFIG_TEMPERATURE_KEY = 'temperature'
CONFIG_VELOCITY_KEY = 'velocity'


class ChtRoom(OpenFoamCase):
    case_type = 'cht_room'

    def __init__(self, *args, case_param=None, **kwargs):
        self.heaters = {}
        self.windows = {}
        self.doors = {}
        self.furniture = {}
        self.sensors = {}
        self.walls = None
        self._bg_region = 'fluid'
        if case_param:
            super(ChtRoom, self).__init__('chtMultiRegionFoam', case_dir=case_param['path'],
                                          is_blocking=case_param['blocking'], is_parallel=case_param['parallel'],
                                          num_of_cores=case_param['cores'])
            if case_param['initialized']:
                self.load_case(case_param)
                self.extract_boundary_conditions()
                self.bind_boundary_conditions()
                self.clean_case()
            else:
                self.remove_initial()
                self.remove_geometry()
        else:
            super(ChtRoom, self).__init__('chtMultiRegionFoam', *args, **kwargs)
            self.remove_initial()
            self.remove_geometry()

    def save_case(self):
        config = super(ChtRoom, self).save_case()
        config[CONFIG_BACKGROUND_KEY] = self._bg_region
        config[CONFIG_HEATERS_KEY] = {}
        config[CONFIG_WINDOWS_KEY] = {}
        config[CONFIG_DOORS_KEY] = {}
        config[CONFIG_SENSORS_KEY] = {}
        config[CONFIG_WALLS_KEY] = {
            CONFIG_NAME_KEY: self.walls.name,
            CONFIG_OBJ_DIMENSIONS: self.walls.model.dimensions,
            CONFIG_LOCATION: self.walls.model.location,
            CONFIG_TEMPERATURE_KEY: self.walls.temperature
        }
        for name, heater in self.heaters.items():
            config[CONFIG_HEATERS_KEY].update({name: {
                CONFIG_OBJ_DIMENSIONS: heater.model.dimensions,
                CONFIG_LOCATION: heater.model.location,
                CONFIG_OBJ_ROTATION: heater.model.rotation,
                CONFIG_TEMPERATURE_KEY: heater.temperature
            }})
        for name, window in self.windows.items():
            config[CONFIG_WINDOWS_KEY].update({name: {
                CONFIG_OBJ_DIMENSIONS: window.model.dimensions,
                CONFIG_LOCATION: window.model.location,
                CONFIG_OBJ_ROTATION: window.model.rotation,
                CONFIG_TEMPERATURE_KEY: window.temperature,
                CONFIG_VELOCITY_KEY: window.wind_speed
            }})
        for name, door in self.doors.items():
            config[CONFIG_DOORS_KEY].update({name: {
                CONFIG_OBJ_DIMENSIONS: door.model.dimensions,
                CONFIG_LOCATION: door.model.location,
                CONFIG_OBJ_ROTATION: door.model.rotation,
                CONFIG_TEMPERATURE_KEY: door.temperature,
                CONFIG_VELOCITY_KEY: door.wind_speed
            }})
        for name, sensor in self.sensors.items():
            config[CONFIG_SENSORS_KEY].update({name: {
                CONFIG_SNS_FIELD: sensor.field,
                CONFIG_LOCATION: sensor.location
            }})
        return config

    def load_case(self, case_param: dict):
        self._bg_region = case_param[CONFIG_BACKGROUND_KEY]
        self.add_object(name=case_param[CONFIG_WALLS_KEY][CONFIG_NAME_KEY], obj_type='walls',
                        dimensions=case_param[CONFIG_WALLS_KEY]['dimensions'],
                        location=case_param[CONFIG_WALLS_KEY]['location'])
        for name, heater in case_param[CONFIG_HEATERS_KEY].items():
            self.add_object(name, 'heater', dimensions=heater[CONFIG_OBJ_DIMENSIONS], location=heater[CONFIG_LOCATION])
            self.heaters[name].temperature = heater[CONFIG_TEMPERATURE_KEY]
        for name, window in case_param[CONFIG_WINDOWS_KEY].items():
            self.add_object(name, 'window', dimensions=window[CONFIG_OBJ_DIMENSIONS], location=window[CONFIG_LOCATION])
            self.windows[name].temperature = window[CONFIG_TEMPERATURE_KEY]
            self.windows[name].is_open = any(window[CONFIG_VELOCITY_KEY])
            self.windows[name].wind_speed = window[CONFIG_VELOCITY_KEY]
        for name, door in case_param[CONFIG_DOORS_KEY].items():
            self.add_object(name, 'door', dimensions=door[CONFIG_OBJ_DIMENSIONS], location=door[CONFIG_LOCATION])
            self.doors[name].temperature = door[CONFIG_TEMPERATURE_KEY]
            self.doors[name].is_open = any(door[CONFIG_VELOCITY_KEY])
            self.doors[name].wind_speed = door[CONFIG_VELOCITY_KEY]
        for name, sensor in case_param[CONFIG_SENSORS_KEY].items():
            self.add_object(name, 'sensor', location=sensor[CONFIG_LOCATION], sns_field=sensor[CONFIG_SNS_FIELD])

    def remove_initial(self):
        force_remove_dir(f'{self.case_dir}/0')

    def setup(self):
        self.prepare_geometry()
        self.partition_mesh(self._bg_region)
        self.prepare_partitioned_mesh()
        self.clean_case()
        self.run_block_mesh()
        self.run_snappy_hex_mesh()
        self.run_split_mesh_regions(cell_zones_only=True)
        self.run_setup_cht()
        self.extract_boundary_conditions()
        self.bind_boundary_conditions()
        self.initialized = True

    def add_object(self, name: str, obj_type: str,
                   dimensions: List[float] = (0, 0, 0), location: List[float] = (0, 0, 0),
                   rotation: List[float] = (0, 0, 0), sns_field: str = None):
        # TODO: check if name contains spaces
        if obj_type not in CHT_ROOM_OBJ_TYPES:
            raise Exception(f'Wrong object type! Possible types are {CHT_ROOM_OBJ_TYPES}')
        if obj_type == WopHeater.type_name:
            wop_object = WopHeater(name, self.case_dir, self._bg_region, dimensions=dimensions, location=location,
                                   rotation=rotation, of_interface=self)
            wop_object.bind_snappy(self.snappy_dict, 'cell_zone', refinement_level=2)
            self.heaters.update({name: wop_object})
        elif obj_type == WopWindow.type_name:
            wop_object = WopWindow(name, self.case_dir, self._bg_region, dimensions=dimensions, location=location,
                                   rotation=rotation, of_interface=self)
            wop_object.bind_snappy(self.snappy_dict, 'region', 'wall', refinement_level=2)
            self.windows.update({wop_object.name: wop_object})
            if self.walls:
                self.walls.model.geometry.cut_surface(wop_object.model.geometry)
        elif obj_type == WopDoor.type_name:
            wop_object = WopDoor(name, self.case_dir, self._bg_region, dimensions=dimensions, location=location,
                                 rotation=rotation, of_interface=self)
            wop_object.bind_snappy(self.snappy_dict, 'region', 'wall', refinement_level=2)
            self.doors.update({wop_object.name: wop_object})
            if self.walls:
                self.walls.model.geometry.cut_surface(wop_object.model.geometry)
        elif obj_type == WopRoom.type_name:
            wop_object = WopRoom(name, self.case_dir, self._bg_region, dimensions=dimensions, location=location,
                                 rotation=rotation, of_interface=self)
            wop_object.bind_snappy(self.snappy_dict, 'region', 'wall')
            self.walls = wop_object
            for window in self.windows.values():
                wop_object.model.geometry.cut_surface(window.model.geometry)
            for door in self.windows.values():
                wop_object.model.geometry.cut_surface(door.model.geometry)
        elif obj_type == WopSensor.type_name:
            sensor = WopSensor(name, self.case_dir, sns_field, self._bg_region, location)
            self.sensors.update({sensor.name: sensor})
            return
        self._objects.update({wop_object.name: wop_object})


def main():
    is_run_parallel = True
    timestep = 5
    case_dir = 'test.case'

    room_dimensions = [3, 4, 2.5]
    window_dimension = [1.5, 0, 1.25]
    door_dimension = [1.5, 0, 2]
    heater_dimensions = [1, 0.2, 0.7]

    window_location = [(room_dimensions[0] - window_dimension[0]) / 2,
                       0,
                       (room_dimensions[2] - window_dimension[2]) / 2]
    door_location = [(room_dimensions[0] - door_dimension[0]) / 2,
                     room_dimensions[1],
                     (room_dimensions[2] - door_dimension[2]) / 2]
    heater_location = [1, 1, 0.2]
    sensor_location = [1.5, 2, 1]

    room = ChtRoom(case_dir, is_blocking=False, is_parallel=is_run_parallel, num_of_cores=4)
    room.add_object(name='walls', obj_type='walls', dimensions=room_dimensions)
    room.add_object('inlet', 'window', dimensions=window_dimension, location=window_location)
    room.add_object('outlet', 'door', dimensions=door_dimension, location=door_location)
    room.add_object('heater', 'heater', dimensions=heater_dimensions, location=heater_location)
    room.add_object('temp_sensor', 'sensor', location=sensor_location, sns_field='T')

    # room.get_boundary_conditions()
    # current_time = get_latest_time(room.case_dir)
    # room.boundaries['fluid']['alphat'].update(current_time)
    # room.boundaries['fluid']['omega'].update(current_time)
    # room.boundaries['fluid']['k'].update(current_time)
    # room.boundaries['fluid']['nut'].update(current_time)
    # room.boundaries['fluid']['p'].update(current_time)
    # room.boundaries['fluid']['p_rgh'].update(current_time)
    # room.boundaries['fluid']['T'].update(current_time)
    # room.boundaries['fluid']['U'].update(current_time)
    # room.boundaries['heater']['p'].update(current_time)
    # room.boundaries['heater']['T'].update(current_time)

    room.setup()

    room.heaters['heater'].temperature = 450
    room.walls.temperature = 293.15

    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.case_dir)}')
    room.heaters['heater'].temperature = room.walls.temperature
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.case_dir)}')
    room.heaters['heater'].temperature = 450
    room.doors['outlet'].open = True
    room.doors['outlet'].wind_speed = [0, 0.1, 0]
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.case_dir)}')
    room.doors['outlet'].open = False
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.case_dir)}')
    room.windows['inlet'].open = True
    room.windows['inlet'].wind_speed = [0, 0.1, 0]
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.case_dir)}')
    room.windows['inlet'].open = False
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.case_dir)}')
    room.windows['inlet'].open = True
    room.windows['inlet'].wind_speed = [0, -0.1, 0]
    room.doors['outlet'].open = True
    room.doors['outlet'].wind_speed = [0, 0, 0]
    room.run()
    time.sleep(timestep)
    room.stop()


if __name__ == '__main__':
    main()
