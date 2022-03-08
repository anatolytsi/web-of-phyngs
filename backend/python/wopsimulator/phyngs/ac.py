from ..openfoam.system.snappyhexmesh import SnappyHexMeshDict, SnappyRegion
from ..geometry.manipulator import Model
from .base import Phyng
from .behavior.cht import set_boundary_to_wall


class AcPhyng(Phyng):
    """
    Web of Phyngs Air Conditioner phyng class
    Combines everything what an AC phyng has (geometry, properties, etc)
    """
    type_name = 'ac'

    def __init__(self, name, stl_name='',
                 dimensions_in=(0, 0, 0), location_in=(0, 0, 0), rotation_in=(0, 0, 0),
                 dimensions_out=(0, 0, 0), location_out=(0, 0, 0), rotation_out=(0, 0, 0),
                 **kwargs):
        """
        Web of Phyngs heater phyng initialization function
        :param name: name of the heater phyng
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param template: template name
        :param of_interface: OpenFoam interface
        """
        self._velocity_in = [0, 0, 0]
        self._velocity_out = [0, 0, 0]  # Default - 45 degrees TODO: should be perpendicular!!
        self._angle_out = 0
        self._temperature = 293.15

        self.name_in = f'{name}_in'
        self.name_out = f'{name}_out'
        self.model_type_in = 'surface'
        self.model_type_out = 'surface'
        self.path_in = ''
        self.path_out = ''

        model_type = 'box'
        templates_dir = 'acs'
        super(AcPhyng, self).__init__(name=name, stl_name=stl_name, model_type=model_type,
                                      templates_dir=templates_dir, **kwargs)

        if self.model_type == 'stl':
            self.model_type_in = 'stl'
            self.model_type_out = 'stl'
            self.stl_name_in = f'{stl_name}_in'
            self.stl_name_out = f'{stl_name}_out'
            self.path_in = self._get_stl(f'{self.stl_name_in}{"" if stl_name[-4:] == ".stl" else ".stl"}',
                                         templates_dir)
            self.path_out = self._get_stl(f'{self.stl_name_out}{"" if stl_name[-4:] == ".stl" else ".stl"}',
                                          templates_dir)

        self.model_in = Model(
            self.name_in,
            self.model_type_in,
            dimensions_in,
            location_in,
            rotation_in,
            True,
            self.path_in,
            self._case_dir
        )
        self.model_out = Model(
            self.name_out,
            self.model_type_out,
            dimensions_out,
            location_out,
            rotation_out,
            True,
            self.path_out,
            self._case_dir
        )
        self._region = name
        self._fields = ['all']

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a door phyng"""
        set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature)
        set_boundary_to_wall(self.name_in, self._boundary_conditions, self._temperature)
        set_boundary_to_wall(self.name_out, self._boundary_conditions, self._temperature)

    def dump_settings(self) -> dict:
        dump = {self.name: {
            'dimensions': self.model.dimensions,
            'location': self.model.location,
            'rotation': self.model.rotation,
            'stl_name': self.stl_name,
            'dimensions_in': self.model.dimensions_in,
            'location_in': self.model.location_in,
            'rotation_in': self.model.rotation_in,
            'stl_name_in': self.stl_name_out,
            'dimensions_out': self.model.dimensions_out,
            'location_out': self.model.location_out,
            'rotation_out': self.model.rotation_out,
            'stl_name_out': self.stl_name_out,
        }}
        return dump

    def set_dimensions(self, dimensions: list):
        raise NotImplementedError('Changing dimensions of an AC is not yet implemented')

    def prepare(self):
        """Saves the model of an instance to a proper location (constant/triSurface)"""
        super(AcPhyng, self).prepare()
        self.path_in = f'{self._case_dir}/constant/triSurface/{self.name_in}.stl'
        self.path_out = f'{self._case_dir}/constant/triSurface/{self.name_out}.stl'
        self.model_in.save(f'{self._case_dir}/constant/triSurface')
        self.model_out.save(f'{self._case_dir}/constant/triSurface')

    def bind_snappy(self, snappy_dict: SnappyHexMeshDict, snappy_type: str, region_type='wall', refinement_level=0):
        """
        Binds a snappyHexMeshDict and Phyng type for it
        Must be called before the case is setup
        :param snappy_dict: snappyHexMeshDict class instance
        :param snappy_type: type of phyng representation in snappyHexMeshDict
        :param region_type: initial region type
        :param refinement_level: mesh refinement level
        """
        super(AcPhyng, self).bind_snappy(snappy_dict, snappy_type, 'wall', refinement_level)
        snappy_in = SnappyRegion(self.name, region_type, refinement_level)
        snappy_out = SnappyRegion(self.name, region_type, refinement_level)
        self.snappy = [self.snappy, snappy_in, snappy_out]

    def destroy(self):
        raise NotImplementedError('Destroying of an AC is not yet implemented')

    def remove(self):
        raise NotImplementedError('Removal of an AC is not yet implemented')

    def __setitem__(self, key, value):
        raise NotImplementedError('Setting items of an AC is not yet implemented')

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        pass

    @property
    def velocity(self):
        return -self._velocity_in[2]

    @velocity.setter
    def velocity(self, value):
        # TODO: recalculate velocity out according to angle and set velocity in z axis directly
        pass

    @property
    def angle(self):
        return self._angle_out

    @angle.setter
    def angle(self, value):
        # TODO: set the velocity to itself to invoke recalculation of outlet velocity
        pass
