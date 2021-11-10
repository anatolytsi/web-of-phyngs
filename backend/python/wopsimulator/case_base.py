import random
from abc import ABC, abstractmethod
from typing import List

from backend.python.wopsimulator.geometry.manipulator import combine_stls
from backend.python.wopsimulator.variables import CONFIG_DICT, CONFIG_TYPE_KEY, CONFIG_PATH_KEY, CONFIG_BLOCKING_KEY, \
    CONFIG_PARALLEL_KEY, CONFIG_CORES_KEY, CONFIG_INITIALIZED_KEY
from backend.python.wopsimulator.openfoam.interface import OpenFoamInterface
from backend.python.wopsimulator.openfoam.system.snappyhexmesh import SnappyRegion, SnappyPartitionedMesh, \
    SnappyCellZoneMesh


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
        self.initialized = initialized
        self._objects = {}
        self._partitioned_mesh = None
        self.sensors = {}
        if loaded:
            if initialized:
                self._setup_initialized_case(kwargs)
            else:
                self._setup_uninitialized_case(kwargs)

    def _setup_initialized_case(self, case_param: dict):
        """
        Setups the loaded initialized case
        :param case_param: loaded case parameters
        """
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
        for obj in self._objects.values():
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
                            for obj in self._objects.values() if type(obj.snappy) == SnappyCellZoneMesh]
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
        config = CONFIG_DICT.copy()
        config[CONFIG_TYPE_KEY] = self.case_type
        config[CONFIG_PATH_KEY] = self.path
        config[CONFIG_BLOCKING_KEY] = self.blocking
        config[CONFIG_PARALLEL_KEY] = self.parallel
        config[CONFIG_CORES_KEY] = self._cores
        config[CONFIG_INITIALIZED_KEY] = self.initialized
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
    def add_object(self, name: str, obj_type: str,
                   dimensions: List[float] = (0, 0, 0), location: List[float] = (0, 0, 0),
                   rotation: List[float] = (0, 0, 0), sns_field: str = None):
        """
        Adds WoP object/sensor to a case
        :param name: name of the object
        :param obj_type: type of an object, case specific
        :param dimensions: object dimensions
        :param location: object location
        :param rotation: object rotation
        :param sns_field: field to monitor for sensor
        """
        pass

    def get_object(self, object_name):
        """
        Gets object/sensor by its name
        :param object_name: name of an object/sensor
        :return: object/sensor instance
        """
        if object_name in self._objects:
            return self._objects[object_name]
        elif object_name in self.sensors:
            return self.sensors[object_name]
        raise ValueError(f'Object with name {object_name} was not found')

    def get_objects(self):
        """
        Gets all objects/sensors
        :return: objects/sensors dict
        """
        return {**self._objects, **self.sensors}

    def prepare_geometry(self):
        """Prepares each objects geometry"""
        for obj in self._objects.values():
            obj.prepare()

    def partition_mesh(self, partition_name: str):
        """
        Partitions mesh by producing a partitioned mesh out of partition regions
        :param partition_name: partitioned mesh name
        """
        regions = [obj.snappy for obj in self._objects.values() if type(obj.snappy) == SnappyRegion]
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
        partitions = [obj.snappy for obj in self._objects.values() if type(obj.snappy) == SnappyCellZoneMesh]
        partitions.insert(0, self._partitioned_mesh)
        # Add partitions to snappyHexMeshDict, get dimensions and find a location in mesh
        self.snappy_dict.add_meshes(partitions)
        minmax_coords = self._get_mesh_dimensions()
        self.snappy_dict.location_in_mesh = self._find_location_in_mesh(minmax_coords)
        # Create background mesh in blockMeshDict, which is bigger then the original dimensions
        blockmesh_min_coords = [coord[0] - 1 for coord in minmax_coords]
        blockmesh_max_coords = [coord[1] + 1 for coord in minmax_coords]
        self.blockmesh_dict.add_box(blockmesh_min_coords, blockmesh_max_coords, name=self._partitioned_mesh.name)
        self.decompose_dict.divide_domain([j - i for i, j in minmax_coords])

    def bind_boundary_conditions(self):
        """Binds boundary conditions to objects"""
        for obj in self._objects.values():
            obj.bind_region_boundaries(self.boundaries)

    def __getitem__(self, item):
        """Allow to access attributes of a class as in dictionary"""
        return getattr(self, item)

    def __setitem__(self, key, value):
        """Allow to set attributes of a class as in dictionary"""
        setattr(self, key, value)

    def __iter__(self):
        """Allow to iterate over attribute names of a class"""
        for each in [b for b in dir(self) if '_' not in b[0]]:
            yield each

    def __delitem__(self, key):
        """Allow to delete individual attributes of a class"""
        del self.__dict__[key]
