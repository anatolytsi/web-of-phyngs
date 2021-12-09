import random
import datetime
from abc import ABC, abstractmethod
from typing import List, Union

from .exceptions import ObjectNotFound
from .geometry.manipulator import combine_stls
from .objects.wopthings import WopObject, WopSensor
from .openfoam.common.parsing import get_latest_time, get_latest_time_parallel
from .variables import CONFIG_DICT, CONFIG_TYPE_KEY, CONFIG_PATH_KEY, CONFIG_BLOCKING_KEY, CONFIG_PARALLEL_KEY, \
    CONFIG_CORES_KEY, CONFIG_INITIALIZED_KEY, CONFIG_MESH_QUALITY_KEY, CONFIG_CLEAN_LIMIT_KEY, CONFIG_OBJ_DIMENSIONS, \
    CONFIG_OBJ_ROTATION, CONFIG_LOCATION, CONFIG_TEMPLATE, CONFIG_URL, CONFIG_SNS_FIELD, CONFIG_OBJ_NAME_KEY, \
    CONFIG_STARTED_TIMESTAMP_KEY
from .openfoam.interface import OpenFoamInterface
from .openfoam.system.snappyhexmesh import SnappyRegion, SnappyPartitionedMesh, SnappyCellZoneMesh


class OpenFoamCase(OpenFoamInterface, ABC):
    """OpenFOAM case base class"""
    case_type = ''

    def __init__(self, *args, loaded=False, initialized=False, **kwargs):
        """
        OpenFOAM case generic initializer
        :param args: OpenFOAM interface args
        :param loaded: case was loaded, i.e., was created in the past
        :param initialized: case was initialized (setup) in the past
        :param kwargs: OpenFOAM interface kwargs, i.e., case parameters
        """
        super(OpenFoamCase, self).__init__(*args, **kwargs)
        self.objects = {}
        self._partitioned_mesh = None
        self.sensors = {}
        self.start_time = kwargs[CONFIG_STARTED_TIMESTAMP_KEY] \
            if CONFIG_STARTED_TIMESTAMP_KEY in kwargs and kwargs[CONFIG_STARTED_TIMESTAMP_KEY] else 0
        if loaded:
            if initialized:
                self._setup_initialized_case(kwargs)
            else:
                self._setup_uninitialized_case(kwargs)
        self.initialized = initialized

    def _setup_initialized_case(self, case_param: dict):
        """
        Setups the loaded initialized case
        :param case_param: loaded case parameters
        """
        try:
            self.run_reconstruct(all_regions=True, latest_time=True)
        except Exception:
            pass
        self.extract_boundary_conditions()
        self.load_initial_objects(case_param)
        self.bind_boundary_conditions()
        self.set_initial_objects(case_param)

    def _setup_uninitialized_case(self, case_param: dict):
        """
        Setups the loaded uninitialized case
        :param case_param: loaded case parameters
        """
        self.clean_case()
        self.remove_geometry()

    def _get_mesh_dimensions(self) -> list:
        """
        Gets minimums and maximums of all axis
        :return: list of min and max, e.g., [(x_min, x_max), ...]
        """
        all_x, all_y, all_z = set(), set(), set()
        for obj in self.objects.values():
            obj_x, obj_y, obj_z = obj.model.geometry.get_used_coords()
            all_x = all_x | obj_x
            all_y = all_y | obj_y
            all_z = all_z | obj_z
        min_coords = [min(all_x), min(all_y), min(all_z)]
        max_coords = [max(all_x), max(all_y), max(all_z)]
        return list(zip(min_coords, max_coords))

    def _find_location_in_mesh(self, minmax_coords) -> [int, int, int]:
        """
        Finds a location in mesh, which is within the dimensions of the mesh
        and is not inside any cell zone mesh
        :param minmax_coords: dimensions of the mesh
        :return: x, y, z coordinates
        """
        # Find the forbidden coordinates, i.e., all cell zones' coordinates
        forbidden_coords = [{'min': obj.model.location,
                             'max': [c1 + c2 for c1, c2 in zip(obj.model.location, obj.model.dimensions)]}
                            for obj in self.objects.values() if type(obj.snappy) == SnappyCellZoneMesh]
        point_found = False
        coords_allowed = [False for _ in range(len(forbidden_coords))]
        # If there are no forbidden coordinates
        coords_allowed = [True] if not coords_allowed else coords_allowed
        x, y, z = 0, 0, 0
        # Loop while proper coordinates are found
        while not point_found:
            # Take a random point between the dimensions for each coordinate
            x = round(random.uniform(minmax_coords[0][0] + 0.1, minmax_coords[0][1] - 0.1), 3)
            y = round(random.uniform(minmax_coords[1][0] + 0.1, minmax_coords[1][1] - 0.1), 3)
            z = round(random.uniform(minmax_coords[2][0] + 0.1, minmax_coords[2][1] - 0.1), 3)
            # For each forbidden coordinate, check that it does not lie inside any forbidden zone
            for idx, coords in enumerate(forbidden_coords):
                coords_allowed[idx] = not (coords['min'][0] < x < coords['max'][0] and
                                           coords['min'][1] < y < coords['max'][1] and
                                           coords['min'][2] < z < coords['max'][2])
            point_found = all(coords_allowed)
        return x, y, z

    def dump_case(self):
        """
        Dumps case parameters into dictionary
        :return: parameter dump dict
        """
        config = {
            CONFIG_TYPE_KEY: self.case_type,
            CONFIG_PATH_KEY: self.path,
            CONFIG_BLOCKING_KEY: self.blocking,
            CONFIG_PARALLEL_KEY: self.parallel,
            CONFIG_CORES_KEY: self._cores,
            CONFIG_INITIALIZED_KEY: self.initialized,
            CONFIG_MESH_QUALITY_KEY: self.blockmesh_dict.mesh_quality,
            CONFIG_CLEAN_LIMIT_KEY: self.clean_limit,
            CONFIG_STARTED_TIMESTAMP_KEY: self.start_time
        }
        return config

    def remove_initial_boundaries(self):
        """Removes initial boundary conditions directory"""
        super(OpenFoamCase, self).remove_initial_boundaries()
        self.initialized = False

    @abstractmethod
    def set_initial_objects(self, case_param: dict):
        """
        Method to set case objects parameters from case_param dict
        Must be implemented in all child classes
        :param case_param: loaded case parameters
        """
        pass

    @abstractmethod
    def load_initial_objects(self, case_param: dict):
        """
        Method to load case objects parameters from case_param dict
        Must be implemented in all child classes
        :param case_param: loaded case parameters
        """
        pass

    @abstractmethod
    def add_object(self, name: str, obj_type: str, url: str = '', custom=False, template: str = '',
                   dimensions: List[float] = (0, 0, 0), location: List[float] = (0, 0, 0),
                   rotation: List[float] = (0, 0, 0), sns_field: str = None):
        """
        Adds WoP object/sensor to a case
        :param name: name of the object
        :param obj_type: type of an object, case specific
        :param url: object URL
        :param custom: object was created from URL
        :param template: object template
        :param dimensions: object dimensions
        :param location: object location
        :param rotation: object rotation
        :param sns_field: field to monitor for sensor
        """
        pass

    def get_object(self, object_name) -> Union[WopObject, WopSensor]:
        """
        Gets object/sensor by its name
        :param object_name: name of an object/sensor
        :return: object/sensor instance
        """
        if object_name in self.objects:
            return self.objects[object_name]
        elif object_name in self.sensors:
            return self.sensors[object_name]
        raise ObjectNotFound(f'Object with name {object_name} was not found')

    def modify_object(self, object_name: str, params: dict):
        """
        Modifies object by recreating it with new parameters
        :param object_name: object name
        :param params: object parameters to change, e.g., dimensions
        """
        geometric_set = {CONFIG_OBJ_DIMENSIONS, CONFIG_OBJ_ROTATION, CONFIG_LOCATION,
                         CONFIG_TEMPLATE, CONFIG_URL, CONFIG_SNS_FIELD}
        if not geometric_set.isdisjoint(params.keys()):
            self.stop()
            self.initialized = False
            obj = self.get_object(object_name)
            obj_type = obj.type_name
            if obj.type_name == 'sensor':
                new_params = {
                    CONFIG_OBJ_NAME_KEY: obj.name,
                    CONFIG_LOCATION: params[CONFIG_LOCATION] if params[CONFIG_LOCATION] else obj.model.location,
                    CONFIG_SNS_FIELD: params[CONFIG_SNS_FIELD] if params[CONFIG_SNS_FIELD] else obj.field,
                }
                self.remove_object(object_name)
                self.add_object(new_params[CONFIG_OBJ_NAME_KEY], obj_type, location=new_params[CONFIG_LOCATION],
                                sns_field=new_params[CONFIG_SNS_FIELD])
            else:
                new_params = {
                    CONFIG_OBJ_NAME_KEY: obj.name,
                    CONFIG_OBJ_DIMENSIONS: obj.model.dimensions,
                    CONFIG_LOCATION: params[CONFIG_LOCATION] if params[CONFIG_LOCATION] else obj.model.location,
                    CONFIG_OBJ_ROTATION: params[CONFIG_OBJ_ROTATION] if params[CONFIG_OBJ_ROTATION]
                    else obj.model.rotation,
                    CONFIG_TEMPLATE: obj.template,
                    CONFIG_URL: None
                }
                custom = obj.custom
                if params[CONFIG_OBJ_DIMENSIONS]:
                    new_params[CONFIG_OBJ_DIMENSIONS] = params[CONFIG_OBJ_DIMENSIONS]
                    new_params[CONFIG_TEMPLATE] = ''
                    custom = False
                elif params[CONFIG_TEMPLATE]:
                    new_params[CONFIG_OBJ_DIMENSIONS] = [0, 0, 0]
                    new_params[CONFIG_TEMPLATE] = params[CONFIG_TEMPLATE]
                    custom = False
                elif params[CONFIG_URL]:
                    new_params[CONFIG_OBJ_DIMENSIONS] = [0, 0, 0]
                    new_params[CONFIG_TEMPLATE] = ''
                    new_params[CONFIG_URL] = params[CONFIG_URL]
                    custom = True
                self.remove_object(object_name)
                self.add_object(new_params[CONFIG_OBJ_NAME_KEY], obj_type, new_params[CONFIG_URL], custom,
                                new_params[CONFIG_TEMPLATE], new_params[CONFIG_OBJ_DIMENSIONS],
                                new_params[CONFIG_LOCATION], new_params[CONFIG_OBJ_ROTATION])

    def remove_object(self, object_name):
        """
        Removes an object with a specified name from case
        :param object_name: object name to remove
        """
        obj = self.get_object(object_name)
        type_name = obj.type_name
        obj.destroy()
        if type_name == 'sensor':
            del self.sensors[object_name]
            self._probe_parser.remove_unused()
        else:
            del self.objects[object_name]
        self.initialized = False

    def get_objects(self):
        """
        Gets all objects/sensors
        :return: objects/sensors dict
        """
        return {**self.objects, **self.sensors}

    def prepare_geometry(self):
        """Prepares each objects geometry"""
        for obj in self.objects.values():
            obj.prepare()

    def partition_mesh(self, partition_name: str):
        """
        Partitions mesh by producing a partitioned mesh out of partition regions
        :param partition_name: partitioned mesh name
        """
        regions = [obj.snappy for obj in self.objects.values() if type(obj.snappy) == SnappyRegion]
        region_paths = [f'{self.path}/constant/triSurface/{region.name}.stl' for region in regions]
        combine_stls(f'{self.path}/constant/triSurface/{partition_name}.stl', region_paths)
        self._partitioned_mesh = SnappyPartitionedMesh(partition_name, f'{partition_name}.stl')
        self._partitioned_mesh.add_regions(regions)

    def prepare_partitioned_mesh(self):
        """
        Prepares partitioned mesh, i.e., adds it to snappyHexMeshDict and
        adds background mesh to blockMeshDict
        """
        # Get all partitions
        partitions = [obj.snappy for obj in self.objects.values() if type(obj.snappy) == SnappyCellZoneMesh]
        partitions.insert(0, self._partitioned_mesh)
        for partition in partitions:
            self.material_props.add_object(partition.name, partition.material_type, partition.material)
        # Add partitions to snappyHexMeshDict, get dimensions and find a location in mesh
        self.snappy_dict.add_meshes(partitions)
        minmax_coords = self._get_mesh_dimensions()
        self.snappy_dict.location_in_mesh = self._find_location_in_mesh(minmax_coords)
        # Create background mesh in blockMeshDict, which is bigger then the original dimensions
        blockmesh_min_coords = [coord[0] - 1 for coord in minmax_coords]
        blockmesh_max_coords = [coord[1] + 1 for coord in minmax_coords]
        self.blockmesh_dict.add_box(blockmesh_min_coords, blockmesh_max_coords, name=self._partitioned_mesh.name)
        # TODO: move it to more generalized function
        self.decompose_dict.divide_domain([j - i for i, j in minmax_coords])

    def bind_boundary_conditions(self):
        """Binds boundary conditions to objects"""
        for obj in self.objects.values():
            obj.bind_region_boundaries(self.boundaries)

    def get_simulation_time_ms(self):
        """
        Gets simulation time in datetime and epoch ms
        :return: epoch ms, datetime
        """
        simulation_timestamp = self.start_time + self._time_probe.time * 1000
        simulation_time = datetime.datetime.fromtimestamp(simulation_timestamp / 1000)
        return simulation_timestamp, simulation_time

    @staticmethod
    def get_current_time():
        """
        Gets current real time in datetime and epoch ms
        :return: epoch ms, datetime
        """
        time_now = datetime.datetime.now()
        timestamp_now = time_now.timestamp() * 1000
        return timestamp_now, time_now

    def get_time_difference(self, simulation_timestamp=None, timestamp_now=None):
        """
        Gets time difference in seconds
        :param simulation_timestamp: simulation time in epoch ms
        :param timestamp_now: real time in epoch ms
        :return: time difference in seconds
        """
        if bool(simulation_timestamp) != bool(timestamp_now):
            raise ValueError(f'Either both simulation time and now time or none should be specified')
        if not simulation_timestamp and not timestamp_now:
            simulation_timestamp, _ = self.get_simulation_time_ms()
            timestamp_now, _ = self.get_current_time()
        return round((simulation_timestamp - timestamp_now) / 1000, 3)

    def get_time(self) -> dict:
        """
        Gets real time, simulation time and
        a difference between real and simulation
        :return: dictionary
        """
        timestamp_now, time_now = self.get_current_time()
        times = {
            'real_time': time_now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'simulation_time': '0',
            'time_difference': 0
        }
        if self.start_time:
            simulation_timestamp, simulation_time = self.get_simulation_time_ms()
            times['simulation_time'] = simulation_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            times['time_difference'] = self.get_time_difference(simulation_timestamp, timestamp_now)
        return times

    def run(self):
        """
        Runs solver and monitor threads
        Case must be setup before running
        """
        get_time = get_latest_time
        if self.parallel:
            get_time = get_latest_time_parallel
        if not get_time(self.path):
            self.start_time = datetime.datetime.now().timestamp() * 1000
        if not self.initialized:
            self.clean_case()
            self.setup()
        super(OpenFoamCase, self).run()

    def __getitem__(self, item):
        """Allow to access attributes of a class as in dictionary"""
        return getattr(self, item)

    def __setitem__(self, key, value):
        """Allow to set attributes of a class as in dictionary"""
        if key != CONFIG_CLEAN_LIMIT_KEY:
            self.initialized = False
        if key == CONFIG_MESH_QUALITY_KEY:
            self.blockmesh_dict.mesh_quality = value
        else:
            setattr(self, key, value)

    def __iter__(self):
        """Allow to iterate over attribute names of a class"""
        for each in [b for b in dir(self) if '_' not in b[0]]:
            yield each

    def __delitem__(self, key):
        """Allow to delete individual attributes of a class"""
        del self.__dict__[key]
