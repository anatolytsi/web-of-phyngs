import os

from backend.python.wopsimulator.objects.behavior.cht import set_boundary_to_wall
from backend.python.wopsimulator.objects.wopthings import WopObject
from backend.python.wopsimulator.openfoam.common.parsing import get_latest_time


class WopRoom(WopObject):
    """
    Web of Phyngs Room class
    Combines everything what a room has (wall geometry, properties, etc)
    """
    type_name = 'walls'

    def __init__(self, name, case_dir, bg_region: str, dimensions=(0, 0, 0), location=(0, 0, 0), rotation=(0, 0, 0),
                 template=None, of_interface=None):
        """
        Web of Phyngs room initialization function
        :param name: name of the room walls
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param template: template name
        :param of_interface: OpenFoam interface
        """
        self._temperature = 293.15
        model_type = 'stl' if template else 'box'
        stl_path = f'{os.path.abspath(__file__)}/geometry/doors/{template}.stl' if template else None
        super(WopRoom, self).__init__(name, case_dir, model_type, bg_region, dimensions, location, rotation,
                                      stl_path=stl_path, of_interface=of_interface)
        self._fields = ['T']

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a room"""
        set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature)

    def dump_settings(self):
        settings = super(WopRoom, self).dump_settings()
        settings[self.name].update({'temperature': self._temperature})
        return settings

    @property
    def temperature(self):
        """Room temperature getter"""
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """
        Sets room temperature by modifying the latest results
        :param temperature: temperature in K
        """
        if self._snappy_dict is None or self._boundary_conditions is None:
            self._temperature = float(temperature)
            return
        latest_result = get_latest_time(self._case_dir)
        self._temperature = float(temperature)
        self._boundary_conditions['T'].update_time(latest_result)
        self._boundary_conditions['T'].internalField.value = temperature


def main():
    case_dir = 'test.case'
    heater = WopRoom('heater', case_dir, 'fluid', [1, 2, 3])
    heater.model.show()


if __name__ == '__main__':
    main()
