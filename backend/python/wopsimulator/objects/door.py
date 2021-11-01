import os

from backend.python.wopsimulator.objects.behavior.cht import set_boundary_to_outlet, set_boundary_to_wall, \
    update_boundaries
from backend.python.wopsimulator.objects.wopthings import WopObject
from backend.python.wopsimulator.openfoam.interface import get_latest_time


class WopDoor(WopObject):
    """
    Web of Phyngs Door class
    Combines everything what a door has (geometry, properties, etc)
    """
    type_name = 'door'

    def __init__(self, name, case_dir, bg_region: str, dimensions=(0, 0, 0), location=(0, 0, 0), rotation=(0, 0, 0),
                 template=None, of_interface=None):
        """
        Web of Phyngs door initialization function
        :param name: name of the door
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param template: template name
        :param of_interface: OpenFoam interface
        """
        self._open = False
        self._wind_speed = [0, 0, 0]
        self._temperature = 293.15
        model_type = 'stl' if template else 'surface'
        stl_path = f'{os.path.abspath(__file__)}/geometry/doors/{template}.stl' if template else None
        super(WopDoor, self).__init__(name, case_dir, model_type, bg_region, dimensions, location, rotation,
                                      stl_path=stl_path, of_interface=of_interface)

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a door"""
        set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature)

    @property
    def open(self):
        """Door open status getter"""
        return self._open

    @open.setter
    def open(self, is_open):
        """
        Sets door type by modifying the latest results
        :param is_open: door status
        """
        latest_result = get_latest_time(self._case_dir)
        self._open = is_open
        if is_open:
            set_boundary_to_outlet(self.name, self._boundary_conditions, self._wind_speed, self._temperature,
                                   latest_result, bg_name=self._bg_region, of_interface=self._of_interface)
        else:
            set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature, latest_result,
                                 bg_name=self._bg_region, of_interface=self._of_interface)
            self._wind_speed = [0, 0, 0]

    @property
    def wind_speed(self):
        return self._wind_speed

    @wind_speed.setter
    def wind_speed(self, wind_speed):
        latest_result = get_latest_time(self._case_dir)
        self._wind_speed = wind_speed
        if self._open:
            update_boundaries(self._boundary_conditions, latest_result)
            self._boundary_conditions['U'][self.name].value = self._wind_speed
            self._boundary_conditions['U'][self.name].save()

    @property
    def temperature(self):
        """Door temperature getter"""
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """
        Sets door temperature by modifying the latest results
        :param temperature: temperature in K
        """
        latest_result = get_latest_time(self._case_dir)
        self._temperature = float(temperature)
        self._boundary_conditions['T'].update_time(latest_result)
        self._boundary_conditions['T'][self.name].value = self._temperature


def main():
    case_dir = 'test.case'
    door = WopDoor('inlet', case_dir, 'fluid', [1.5, 0, 2.5])
    door.bind_region_boundaries()
    door.model.show()


if __name__ == '__main__':
    main()
