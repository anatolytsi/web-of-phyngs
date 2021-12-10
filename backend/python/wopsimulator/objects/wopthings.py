"""Web of Phyngs base Phyngs (Object and Sensor)"""
import os
import re

from abc import ABC, abstractmethod

import gdown

from ..geometry.manipulator import Model
from ..openfoam.common.filehandling import force_remove_dir
from ..openfoam.probes.probes import Probe
from ..openfoam.system.snappyhexmesh import SnappyHexMeshDict, SnappyRegion, SnappyCellZoneMesh


class WopObject(ABC):
    """
    Web of Phyngs Object base class
    Refers to an object with a geometric model and boundary conditions
    """
    type_name = 'object'

    def __init__(self, name: str, case_dir: str, model_type: str, bg_region: str, url='', custom=False,
                 dimensions=(0, 0, 0), location=(0, 0, 0), rotation=(0, 0, 0),
                 facing_zero=True, template=None, of_interface=None, **kwargs):
        """
        Web of Phyngs object initialization function
        :param name: name of an object
        :param case_dir: case directory
        :param bg_region: background region name
        :param url: object URL
        :param custom: object was created from URL
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param facing_zero: normal vector direction towards zero coordinates, used for model_type = 'surface'
        :param template: template name
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
        self.custom = custom
        if url:
            model_type = 'stl'
            self._get_stl_from_url(url)
        elif template:
            self._get_stl_from_template(template)
        elif custom:
            self._get_custom_stl()
        else:
            self.path = ''
        self.template = template.split('/')[-1] if template else ''
        self.model = Model(name, model_type, dimensions, location, rotation, facing_zero, self.path, self._case_dir)

    def _get_stl_from_url(self, url):
        """
        Gets STL from a given URL
        :param url: STL URL
        """
        self.path = f'{self._case_dir}/geometry/{self.name}.stl'
        pattern = r'https://drive\.google\.com/file/d/([^/]+)(/view)?'
        match = re.match(pattern, url)
        if not match.group():
            raise ConnectionError(f'Provided download URL ({url}) does not match pattern {pattern}')
        url = f'https://drive.google.com/uc?id={match.group(1)}'
        gdown.download(url, self.path, quiet=True)
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'Custom STL was not loaded for object {self.name}')
        with open(self.path, 'r') as f:
            stl = f.read()
            stl_match = re.match(r'^solid [^\s]*\s[\S\s]+endsolid [^\s]*$', stl)
            if not stl_match.group():
                raise OSError('Verify provided STL file for integrity')
        self.custom = True

    def _get_stl_from_template(self, template):
        """
        Gets STL from a template
        :param template: STL template name
        """
        self.path = f'{os.path.dirname(os.path.abspath(__file__))}/geometry/{template}' \
                    f'{"" if template[-4:] == ".stl" else ".stl"}'
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'Template {template} STL does not exist for object {self.name}')

    def _get_custom_stl(self):
        """
        Gets a custom (URL created) STL
        """
        self.path = f'{self._case_dir}/geometry/{self.name}.stl'
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'Custom STL was not loaded for object {self.name}')

    @abstractmethod
    def _add_initial_boundaries(self):
        """
        Method to add initial boundaries to the corresponding boundary conditions
        Must be implemented in all child classes
        """
        pass

    def dump_settings(self):
        dump = {self.name: {
            'dimensions': self.model.dimensions,
            'location': self.model.location,
            'rotation': self.model.rotation,
            'template': self.template,
            'custom': self.custom
        }}
        return dump

    def set_dimensions(self, dimensions: list):
        self._of_interface.stop()
        location = self.model.location
        rotation = self.model.rotation
        facing_zero = self.model.facing_zero
        model_type = self.model.model_type
        self.model = Model(self.name, model_type, dimensions, location, rotation, facing_zero, self.path)
        self._of_interface.initialized = False

    def prepare(self):
        """Saves the model of an instance to a proper location (constant/triSurface)"""
        self.path = f'{self._case_dir}/constant/triSurface/{self.name}.stl'
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

    def destroy(self):
        """
        Destroys a Phyng object by removing all
        connected data, e.g., files, from simulation
        """
        if os.path.exists(path := f'{self._case_dir}/constant/triSurface/{self.name}.stl'):
            os.remove(path)
        if os.path.exists(path := f'{self._case_dir}/0/{self.name}'):
            force_remove_dir(path)
        if os.path.exists(path := f'{self._case_dir}/constant/{self.name}'):
            force_remove_dir(path)
        if os.path.exists(path := f'{self._case_dir}/system/{self.name}'):
            force_remove_dir(path)
        self._snappy_dict.remove(self.name)
        if self._boundary_conditions:
            for bc in self._boundary_conditions.values():
                if self.name in bc:
                    del bc[self.name]
                if reg := f'{self.name}_to_{self._bg_region}' in bc:
                    del bc[reg]
                if reg := f'{self._bg_region}_to_{self.name}' in bc:
                    del bc[reg]

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

    def destroy(self):
        """Destroys a Phyng Sensor by deleting a probe"""
        self._probe.remove()
        del self._probe

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
