"""Web of Phyngs base Phyngs (Object and Sensor)"""
import os
import re

from abc import ABC, abstractmethod

import gdown

from ..geometry.manipulator import Model
from ..openfoam.common.filehandling import force_remove_dir
from ..openfoam.system.snappyhexmesh import SnappyHexMeshDict, SnappyRegion, SnappyCellZoneMesh


class Phyng(ABC):
    """
    Phyng base class
    Refers to an object with a geometric model and boundary conditions
    """
    type_name = 'phyng'

    def __init__(self, name: str, case_dir: str, model_type: str, bg_region: str,
                 dimensions=(0, 0, 0), location=(0, 0, 0), rotation=(0, 0, 0),
                 facing_zero=True, stl_name='', templates_dir='',
                 of_interface=None, **kwargs):
        """
        Phyng initialization function
        :param name: name of an phyng
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param facing_zero: normal vector direction towards zero coordinates, used for model_type = 'surface'
        :param stl_name: STL geometry name
        :param templates_dir: STL templates directory name
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
        if stl_name:
            model_type = 'stl'
            self.path = self._get_stl(f'{stl_name}{"" if stl_name[-4:] == ".stl" else ".stl"}', templates_dir)
        else:
            self.path = ''
        self.stl_name = stl_name
        self.model = Model(name, model_type, dimensions, location, rotation, facing_zero, self.path, self._case_dir)
        self.model_type = model_type

    def _get_stl(self, stl_name: str, templates_dir: str):
        path = self._get_custom_stl(stl_name)
        if not path:
            path = self._get_template_stl(stl_name, templates_dir)
        if not path:
            raise Exception(f'Geometry "{stl_name}" was neither uploaded nor is present in templates')
        return path

    @staticmethod
    def _get_template_stl(stl_name, templates_dir):
        """
        Gets STL from a template
        :param stl_name: STL file template geometry name
        """
        path = f'{os.path.dirname(os.path.abspath(__file__))}/../geometry/templates/{templates_dir}/{stl_name}'
        if not os.path.exists(path):
            return ''
        return os.path.abspath(path)

    def _get_custom_stl(self, stl_name):
        """
        Gets a custom (uploaded) STL
        :param stl_name: uploaded STL file geometry name
        """
        path = f'{self._case_dir}/geometry/{stl_name}'
        if not os.path.exists(path):
            return ''
        return path

    @abstractmethod
    def _add_initial_boundaries(self):
        """
        Method to add initial boundaries to the corresponding boundary conditions
        Must be implemented in all child classes
        """
        pass

    def dump_settings(self) -> dict:
        dump = {self.name: {
            'dimensions': self.model.dimensions,
            'location': self.model.location,
            'rotation': self.model.rotation,
            'stl_name': self.stl_name
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
        Binds a snappyHexMeshDict and Phyng type for it
        Must be called before the case is setup
        :param snappy_dict: snappyHexMeshDict class instance
        :param snappy_type: type of phyng representation in snappyHexMeshDict
        :param region_type: initial region type
        :param refinement_level: mesh refinement level
        """
        self._snappy_dict = snappy_dict
        if snappy_type == 'cell_zone':
            if self.model_type == 'stl':
                self.snappy = SnappyCellZoneMesh(self.name, f'{self.name}.stl', refinement_level)
            else:
                self.snappy = SnappyCellZoneMesh(self.name, f'{self.name}.stl', refinement_level,
                                                 cell_zone_inside='insidePoint',
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
        Destroys a phyng by removing all
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

    def remove(self):
        self.model.remove()

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
                    self._of_interface.run_reconstruct(latest_time=True, region=self._region, waiting=True)
                else:
                    self._of_interface.run_reconstruct(latest_time=True, region=self._region,
                                                       fields=self._fields, waiting=True)
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
