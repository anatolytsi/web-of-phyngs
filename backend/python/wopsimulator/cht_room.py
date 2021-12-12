import time
from typing import List

from .exceptions import WrongObjectType
from .openfoam.common.parsing import get_latest_time
from .openfoam.constant.material_properties import FLUID_MATERIALS
from .case_base import OpenFoamCase
from .objects.door import WopDoor
from .objects.room import WopRoom
from .objects.window import WopWindow
from .objects.heater import WopHeater
from .objects.wopthings import WopSensor, WopObject
from .variables import (CHT_ROOM_OBJ_TYPES, CONFIG_BACKGROUND_KEY, CONFIG_WALLS_KEY, CONFIG_NAME_KEY,
                        CONFIG_HEATERS_KEY, CONFIG_WINDOWS_KEY, CONFIG_DOORS_KEY, CONFIG_SENSORS_KEY,
                        CONFIG_OBJ_DIMENSIONS, CONFIG_OBJ_ROTATION, CONFIG_SNS_FIELD, CONFIG_LOCATION, CONFIG_TEMPLATE,
                        CONFIG_CUSTOM, CONFIG_TEMPERATURE_KEY, CONFIG_VELOCITY_KEY, CONFIG_OBJ_MATERIAL,
                        CONFIG_OBJ_NAME_KEY, CONFIG_URL, CONFIG_MATERIAL_KEY)


class ChtRoom(OpenFoamCase):
    """Conjugate Heat Transfer (CHT) OpenFOAM case"""
    case_type = 'cht_room'

    def __init__(self, *args, material='air', **kwargs):
        """
        Conjugate Heat Transfer case initialization function
        :param args: OpenFOAM base case args
        :param kwargs: OpenFOAM base case kwargs
        """
        self.heaters = {}
        self.windows = {}
        self.doors = {}
        self.furniture = {}
        self.walls = None
        self.background = 'fluid'
        self._material = material
        super(ChtRoom, self).__init__('chtMultiRegionFoam', *args, **kwargs)

    def _setup_uninitialized_case(self, case_param: dict):
        """
        Setups the loaded uninitialized CHT case
        :param case_param: loaded case parameters
        """
        super(ChtRoom, self)._setup_uninitialized_case(case_param)
        self.remove_initial_boundaries()
        self.load_initial_objects(case_param)
        self.set_initial_objects(case_param)

    def _get_model_param_set(self):
        return super(ChtRoom, self)._get_model_param_set() | {CONFIG_OBJ_MATERIAL}

    def _get_new_params(self, obj: WopObject, params: dict):
        new_params = super(ChtRoom, self)._get_new_params(obj, params)
        if CONFIG_OBJ_MATERIAL in obj:
            new_params.update({
                CONFIG_OBJ_MATERIAL: params[CONFIG_OBJ_MATERIAL] if params[CONFIG_OBJ_MATERIAL] else obj.material
            })
        return new_params

    def _add_obj_from_parameters(self, object_name, params: dict, custom: bool):
        self.add_object(params[CONFIG_OBJ_NAME_KEY], object_name, params[CONFIG_URL], custom, params[CONFIG_TEMPLATE],
                        params[CONFIG_OBJ_DIMENSIONS], params[CONFIG_LOCATION], params[CONFIG_OBJ_ROTATION],
                        params[CONFIG_OBJ_MATERIAL])

    def prepare_partitioned_mesh(self):
        super(ChtRoom, self).prepare_partitioned_mesh()
        self._partitioned_mesh.material = self._material

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, material):
        if material not in FLUID_MATERIALS:
            raise ValueError(f'Background material cannot be {material}, '
                             f'possible values are {", ".join(FLUID_MATERIALS)}')
        self._material = material

    def dump_case(self):
        """
        Dumps CHT case parameters into dictionary
        :return: parameter dump dict
        """
        config = super(ChtRoom, self).dump_case()
        config[CONFIG_BACKGROUND_KEY] = self.background
        config[CONFIG_MATERIAL_KEY] = self.material
        config[CONFIG_HEATERS_KEY] = {}
        config[CONFIG_WINDOWS_KEY] = {}
        config[CONFIG_DOORS_KEY] = {}
        config[CONFIG_SENSORS_KEY] = {}
        config[CONFIG_WALLS_KEY] = {}
        if self.walls:
            config[CONFIG_WALLS_KEY] = self.walls.dump_settings()
        for name, heater in self.heaters.items():
            config[CONFIG_HEATERS_KEY].update({name: heater.dump_settings()})
        for name, window in self.windows.items():
            config[CONFIG_WINDOWS_KEY].update({name: window.dump_settings()})
        for name, door in self.doors.items():
            config[CONFIG_DOORS_KEY].update({name: door.dump_settings()})
        for name, sensor in self.sensors.items():
            config[CONFIG_SENSORS_KEY].update({name: sensor.dump_settings()})
        return config

    def set_initial_objects(self, case_param: dict):
        """
        Sets CHT case objects parameters from case_param dict
        :param case_param: loaded case parameters
        """
        if CONFIG_HEATERS_KEY in case_param and case_param[CONFIG_HEATERS_KEY]:
            for name, heater in case_param[CONFIG_HEATERS_KEY].items():
                self.heaters[name].temperature = heater[CONFIG_TEMPERATURE_KEY]
        if CONFIG_WINDOWS_KEY in case_param and case_param[CONFIG_WINDOWS_KEY]:
            for name, window in case_param[CONFIG_WINDOWS_KEY].items():
                self.windows[name].temperature = window[CONFIG_TEMPERATURE_KEY]
                self.windows[name].is_open = any(window[CONFIG_VELOCITY_KEY])
                self.windows[name].velocity = window[CONFIG_VELOCITY_KEY]
        if CONFIG_DOORS_KEY in case_param and case_param[CONFIG_DOORS_KEY]:
            for name, door in case_param[CONFIG_DOORS_KEY].items():
                self.doors[name].temperature = door[CONFIG_TEMPERATURE_KEY]
                self.doors[name].is_open = any(door[CONFIG_VELOCITY_KEY])
                self.doors[name].velocity = door[CONFIG_VELOCITY_KEY]

    def load_initial_objects(self, case_param: dict):
        """
        Loads CHT case objects parameters from case_param dict
        :param case_param: loaded case parameters
        """
        self.background = case_param[CONFIG_BACKGROUND_KEY]
        if CONFIG_WALLS_KEY in case_param and case_param[CONFIG_WALLS_KEY]:
            walls = case_param[CONFIG_WALLS_KEY]
            self.add_object(name=walls[CONFIG_NAME_KEY], custom=walls[CONFIG_CUSTOM], obj_type='walls',
                            dimensions=walls[CONFIG_OBJ_DIMENSIONS], location=walls[CONFIG_LOCATION],
                            template=walls[CONFIG_TEMPLATE])
        if CONFIG_HEATERS_KEY in case_param and case_param[CONFIG_HEATERS_KEY]:
            for name, heater in case_param[CONFIG_HEATERS_KEY].items():
                self.add_object(name, 'heater', custom=heater[CONFIG_CUSTOM], dimensions=heater[CONFIG_OBJ_DIMENSIONS],
                                location=heater[CONFIG_LOCATION], template=heater[CONFIG_TEMPLATE],
                                material=heater[CONFIG_OBJ_MATERIAL])
        if CONFIG_WINDOWS_KEY in case_param and case_param[CONFIG_WINDOWS_KEY]:
            for name, window in case_param[CONFIG_WINDOWS_KEY].items():
                self.add_object(name, 'window', custom=window[CONFIG_CUSTOM], dimensions=window[CONFIG_OBJ_DIMENSIONS],
                                location=window[CONFIG_LOCATION], template=window[CONFIG_TEMPLATE])
        if CONFIG_DOORS_KEY in case_param and case_param[CONFIG_DOORS_KEY]:
            for name, door in case_param[CONFIG_DOORS_KEY].items():
                self.add_object(name, 'door', custom=door[CONFIG_CUSTOM], dimensions=door[CONFIG_OBJ_DIMENSIONS],
                                location=door[CONFIG_LOCATION], template=door[CONFIG_TEMPLATE])
        if CONFIG_SENSORS_KEY in case_param and case_param[CONFIG_SENSORS_KEY]:
            for name, sensor in case_param[CONFIG_SENSORS_KEY].items():
                self.add_object(name, 'sensor', location=sensor[CONFIG_LOCATION],
                                sns_field=sensor[CONFIG_SNS_FIELD])

    def setup(self):
        """Setups CHT case"""
        self.prepare_geometry()
        self.partition_mesh(self.background)
        self.prepare_partitioned_mesh()
        self.clean_case()
        self.run_block_mesh()
        self.run_snappy_hex_mesh()
        self.run_split_mesh_regions(cell_zones_only=True)
        self.run_setup_cht()
        self.extract_boundary_conditions()
        self.bind_boundary_conditions()
        self.initialized = True

    def add_object(self, name: str, obj_type: str, url: str = '', custom=False, template: str = '',
                   dimensions: List[float] = (0, 0, 0), location: List[float] = (0, 0, 0),
                   rotation: List[float] = (0, 0, 0), material: str = None, sns_field: str = None):
        """
        Adds WoP object/sensor to a CHT case
        :param name: name of the object
        :param obj_type: type of an object, one of: 'heater', 'walls', 'door', 'window'
        :param url: object URL
        :param custom: object was created from URL
        :param template: object template
        :param dimensions: object dimensions
        :param location: object location
        :param rotation: object rotation
        :param sns_field: field to monitor for sensor
        :param material: material of an object
        """
        # TODO: check if name contains spaces
        if obj_type == WopHeater.type_name:
            wop_object = WopHeater(name, self.path, self.background, url, custom, dimensions=dimensions,
                                   location=location, rotation=rotation, template=template, of_interface=self,
                                   material=material)
            wop_object.bind_snappy(self.snappy_dict, 'cell_zone', refinement_level=2)
            self.heaters.update({name: wop_object})
        elif obj_type == WopWindow.type_name:
            wop_object = WopWindow(name, self.path, self.background, url, custom, dimensions=dimensions,
                                   location=location, rotation=rotation, template=template, of_interface=self)
            wop_object.bind_snappy(self.snappy_dict, 'region', 'wall', refinement_level=2)
            self.windows.update({wop_object.name: wop_object})
            if self.walls:
                self.walls.model.geometry.cut_surface(wop_object.model.geometry)
        elif obj_type == WopDoor.type_name:
            wop_object = WopDoor(name, self.path, self.background, url, custom, dimensions=dimensions,
                                 location=location, rotation=rotation, template=template, of_interface=self)
            wop_object.bind_snappy(self.snappy_dict, 'region', 'wall', refinement_level=2)
            self.doors.update({wop_object.name: wop_object})
            if self.walls:
                self.walls.model.geometry.cut_surface(wop_object.model.geometry)
        elif obj_type == WopRoom.type_name:
            wop_object = WopRoom(name, self.path, self.background, url, custom, dimensions=dimensions,
                                 location=location, rotation=rotation, template=template, of_interface=self)
            wop_object.bind_snappy(self.snappy_dict, 'region', 'wall')
            self.walls = wop_object
            for window in self.windows.values():
                wop_object.model.geometry.cut_surface(window.model.geometry)
            for door in self.windows.values():
                wop_object.model.geometry.cut_surface(door.model.geometry)
        elif obj_type == WopSensor.type_name:
            sensor = WopSensor(name, self.path, sns_field, self.background, location)
            self.sensors.update({sensor.name: sensor})
            self.initialized = False
            return
        else:
            raise WrongObjectType(f'Wrong object type! Possible types are {CHT_ROOM_OBJ_TYPES}')
        self.initialized = False
        self.objects.update({wop_object.name: wop_object})

    def remove_object(self, object_name):
        """
        Removes an object with a specified name from case
        :param object_name: object name to remove
        """
        type_name = self.get_object(object_name).type_name
        super(ChtRoom, self).remove_object(object_name)
        type_name = f'{type_name}s' if 's' not in type_name[-1] else type_name
        if type_name != 'sensors':
            del self[type_name][object_name]


def main():
    is_run_parallel = True
    timestep = 5
    case_dir = '../my_room.case'

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

    room = ChtRoom(case_dir, blocking=False, parallel=is_run_parallel, cores=4)
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
    print(f'Latest time: {get_latest_time(room.path)}')
    room.heaters['heater'].temperature = room.walls.temperature
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.heaters['heater'].temperature = 450
    room.doors['outlet'].open = True
    room.doors['outlet'].velocity = [0, 0.1, 0]
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.doors['outlet'].open = False
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.windows['inlet'].open = True
    room.windows['inlet'].velocity = [0, 0.1, 0]
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.windows['inlet'].open = False
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.windows['inlet'].open = True
    room.windows['inlet'].velocity = [0, -0.1, 0]
    room.doors['outlet'].open = True
    room.doors['outlet'].velocity = [0, 0, 0]
    room.run()
    time.sleep(timestep)
    room.stop()


if __name__ == '__main__':
    main()
