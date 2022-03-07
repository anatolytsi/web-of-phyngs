from ..exceptions import PhyngSetValueFailed
from ..openfoam.common.filehandling import get_latest_time
from .behavior.cht import set_boundary_to_outlet, set_boundary_to_wall, update_boundaries
from .base import Phyng


class DoorPhyng(Phyng):
    """
    Web of Phyngs Door phyng class
    Combines everything what a door phyng has (geometry, properties, etc)
    """
    type_name = 'door'

    def __init__(self, stl_name='', **kwargs):
        """
        Web of Phyngs door phyng initialization function
        :param name: name of the door phyng
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param stl_name: STL geometry name
        :param of_interface: OpenFoam interface
        """
        self._open = False
        self._velocity = [0, 0, 0]
        self._temperature = 293.15
        model_type = 'surface'
        templates_dir = 'doors'
        super(DoorPhyng, self).__init__(stl_name=stl_name, model_type=model_type,
                                        templates_dir=templates_dir, **kwargs)
        self._fields = 'all'

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a door phyng"""
        set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature)

    def dump_settings(self) -> dict:
        settings = super(DoorPhyng, self).dump_settings()
        settings[self.name].update({'temperature': self._temperature, 'velocity': self._velocity})
        return settings

    @property
    def open(self):
        """Door phyng open status getter"""
        return self._open

    @open.setter
    def open(self, is_open):
        """
        Sets door phyng type by modifying the latest results
        :param is_open: door phyng status
        """
        self._open = is_open
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            if is_open:
                set_boundary_to_outlet(self.name, self._boundary_conditions, self._velocity, self._temperature,
                                       latest_result, bg_name=self._bg_region, of_interface=self._of_interface)
            else:
                set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature, latest_result,
                                     bg_name=self._bg_region, of_interface=self._of_interface)
                self._velocity = [0, 0, 0]
        except Exception as e:
            raise PhyngSetValueFailed(e)

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, wind_speed):
        self._velocity = wind_speed
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            if self._open:
                update_boundaries(self._boundary_conditions, latest_result)
                self._boundary_conditions['U'][self.name].value = self._velocity
                self._boundary_conditions['U'][self.name].save()
        except Exception as e:
            raise PhyngSetValueFailed(e)

    @property
    def temperature(self):
        """Door phyng temperature getter"""
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """
        Sets door phyng temperature by modifying the latest results
        :param temperature: temperature in K
        """
        self._temperature = float(temperature)
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            self._boundary_conditions['T'].update_time(latest_result)
            self._boundary_conditions['T'][self.name].value = self._temperature
        except Exception as e:
            raise PhyngSetValueFailed(e)


def main():
    case_dir = 'test.case'
    door = DoorPhyng('inlet', case_dir, 'fluid', [1.5, 0, 2.5])
    door.bind_region_boundaries()
    door.model.show()


if __name__ == '__main__':
    main()
