import os

from backend.python.wopsimulator.objects.behavior.cht import set_boundary_to_wall, set_boundary_to_inlet, \
    update_boundaries
from backend.python.wopsimulator.objects.wopthings import WopObject
from backend.python.wopsimulator.openfoam.common.parsing import get_latest_time


class WopWindow(WopObject):
    """
    Web of Phyngs Window class
    Combines everything what a window has (geometry, properties, etc)
    """
    type_name = 'window'

    def __init__(self, name, case_dir, bg_region: str, dimensions=(0, 0, 0), location=(0, 0, 0), rotation=(0, 0, 0),
                 template=None, of_interface=None):
        """
        Web of Phyngs window initialization function
        :param name: name of the window
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param template: template name
        :param of_interface: OpenFoam interface
        """
        self._open = False
        self._velocity = [0, 0, 0]
        self._temperature = 293.15
        model_type = 'stl' if template else 'surface'
        stl_path = f'{os.path.abspath(__file__)}/geometry/doors/{template}.stl' if template else None
        super(WopWindow, self).__init__(name, case_dir, model_type, bg_region, dimensions, location, rotation,
                                        stl_path=stl_path, of_interface=of_interface)

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a window"""
        set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature)

    def dump_settings(self):
        settings = super(WopWindow, self).dump_settings()
        settings[self.name].update({'temperature': self._temperature, 'velocity': self._velocity})
        return settings

    @property
    def open(self):
        """Window open status getter"""
        return self._open

    @open.setter
    def open(self, is_open):
        """
        Sets window type by modifying the latest results
        :param is_open: windows status
        :return:
        """
        if self._snappy_dict is None or self._boundary_conditions is None:
            self._open = is_open
            return
        latest_result = get_latest_time(self._case_dir)
        self._open = is_open
        if is_open:
            set_boundary_to_inlet(self.name, self._boundary_conditions, self._velocity, self._temperature,
                                  latest_result, bg_name=self._bg_region, of_interface=self._of_interface)
        else:
            set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature, latest_result,
                                 bg_name=self._bg_region, of_interface=self._of_interface)
            self._velocity = [0, 0, 0]

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, wind_speed):
        if self._snappy_dict is None or self._boundary_conditions is None:
            self._velocity = wind_speed
            return
        latest_result = get_latest_time(self._case_dir)
        self._velocity = wind_speed
        if self._open:
            update_boundaries(self._boundary_conditions, latest_result)
            self._boundary_conditions['U'][self.name].value = self._velocity
            self._boundary_conditions['U'][self.name].save()

    @property
    def temperature(self):
        """Window temperature getter"""
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """
        Sets window temperature by modifying the latest results
        :param temperature: temperature in K
        """
        if self._snappy_dict is None or self._boundary_conditions is None:
            self._temperature = float(temperature)
            return
        latest_result = get_latest_time(self._case_dir)
        self._temperature = float(temperature)
        self._boundary_conditions['T'].update_time(latest_result)
        self._boundary_conditions['T'][self.name].value = self._temperature


def main():
    case_dir = 'test.case'
    door = WopWindow('outlet', case_dir, 'fluid', [2, 0, 2])
    door.model.show()


if __name__ == '__main__':
    main()
