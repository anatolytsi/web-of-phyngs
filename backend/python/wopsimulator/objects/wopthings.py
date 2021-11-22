"""Web of Phyngs base Phyngs (Object and Sensor)"""
from abc import ABC, abstractmethod

from ..geometry.manipulator import Model
from ..openfoam.probes.probes import Probe
from ..openfoam.system.snappyhexmesh import SnappyHexMeshDict, SnappyRegion, SnappyCellZoneMesh


class WopObject(ABC):
    """
    Web of Phyngs Object base class
    Refers to an object with a geometric model and boundary conditions
    """
    type_name = 'object'

    def __init__(self, name: str, case_dir: str, model_type: str, bg_region: str, dimensions=(0, 0, 0),
                 location=(0, 0, 0), rotation=(0, 0, 0), facing_zero=True, stl_path=None, of_interface=None):
        """
        Web of Phyngs object initialization function
        :param name: name of an object
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param facing_zero: normal vector direction towards zero coordinates, used for model_type = 'surface'
        :param stl_path: path to STL model, used for model_type = 'stl'
        :param of_interface: OpenFoam interface
        """
        self.name = name
        self._case_dir = case_dir
        self._boundary_conditions = None
        self._of_interface = of_interface
        self._snappy_dict = None
        self._bg_region = bg_region
        # Region and fields are used for stopping the case
        # and reconstructing only certain region and fields
        self._region = bg_region
        self._fields = []
        self.snappy = None
        self.model = Model(name, model_type, dimensions, location, rotation, facing_zero, stl_path)

    @abstractmethod
    def _add_initial_boundaries(self):
        """
        Method to add initial boundaries to the corresponding boundary conditions
        Must be implemented in all child classes
        """
        pass

    def dump_settings(self):
        return {self.name: {
            'dimensions': self.model.dimensions,
            'location': self.model.location,
            'rotation': self.model.rotation,
        }}

    def prepare(self):
        """Saves the model of an instance to a proper location (constant/triSurface)"""
        self.model.save(f'{self._case_dir}/constant/triSurface')

    def bind_snappy(self, snappy_dict: SnappyHexMeshDict, snappy_type: str, region_type='wall', refinement_level=0):
        """
        Binds a snappyHexMeshDict and WoP Object type for it
        Must be called before the case is setup
        :param snappy_dict: snappyHexMeshDict class instance
        :param snappy_type: type of object representation in snappyHexMeshDict
        :param region_type: initial region type
        :param refinement_level: mesh refinement level
        """
        self._snappy_dict = snappy_dict
        if snappy_type == 'cell_zone':
            self.snappy = SnappyCellZoneMesh(self.name, f'{self.name}.stl', refinement_level,
                                             inside_point=self.model.center)
        elif snappy_type == 'region':
            self.snappy = SnappyRegion(self.name, region_type, refinement_level)

    def bind_region_boundaries(self, region_boundaries: dict):
        """
        Binds the thing boundary conditions to a class
        Binding regions can only be performed once a case is setup,
        i.e., the boundary files are produced
        :param region_boundaries: dict of a region boundary conditions
        """
        if region_boundaries:
            self._boundary_conditions = region_boundaries[self._bg_region]
            self._add_initial_boundaries()

    def __getitem__(self, item):
        """Allow to access attributes of a class as in dictionary"""
        return getattr(self, item)

    def __setitem__(self, key, value):
        """Allow to set attributes of a class as in dictionary"""
        case_was_stopped = False
        if self._of_interface.running and self._fields:
            case_was_stopped = True
            self._of_interface.stop()
            if self._of_interface.parallel:
                if self._fields == 'all':
                    self._of_interface.run_reconstruct(latest_time=True, region=self._region)
                else:
                    self._of_interface.run_reconstruct(latest_time=True, region=self._region, fields=self._fields)
        setattr(self, key, value)
        if case_was_stopped:
            self._of_interface.run()

    def __iter__(self):
        """Allow to iterate over attribute names of a class"""
        for each in [b for b in dir(self) if '_' not in b[0]]:
            yield each

    def __delitem__(self, key):
        """Allow to delete individual attributes of a class"""
        del self.__dict__[key]


class WopSensor:
    """Web of Phyngs Sensor base class"""
    type_name = 'sensor'

    def __init__(self, name, case_dir, field, region, location):
        """
        Web of Phyngs sensor initialization function
        :param name: name of the sensor
        :param case_dir: case dictionary
        :param field: sensor field to monitor (e.g., T)
        :param region: region to sense
        :param location: sensor location
        """
        self.name = name
        self.location = location
        self.field = field
        self._case_dir = case_dir
        self._probe = Probe(case_dir, field, region, location)

    def dump_settings(self):
        return {self.name: {
            'location': self.location,
            'field': self.field
        }}

    @property
    def value(self):
        """Sensor value getter"""
        return self._probe.value

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
