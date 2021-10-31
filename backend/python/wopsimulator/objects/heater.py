import os

from backend.python.wopsimulator.objects.behavior.cht import set_boundary_to_heater
from backend.python.wopsimulator.objects.wopthings import WopObject
from backend.python.wopsimulator.openfoam.interface import get_latest_time


class WopHeater(WopObject):
    """
    Web of Phyngs Heater class
    Combines everything what a heater has (geometry, properties, etc)
    """
    type_name = 'heater'

    def __init__(self, name, case_dir, bg_region: str, dimensions=(0, 0, 0), location=(0, 0, 0), rotation=(0, 0, 0),
                 template=None, of_interface=None):
        """
        Web of Phyngs heater initialization function
        :param name: name of the heater
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
        stl_path = f'{os.path.abspath(__file__)}/geometry/heaters/{template}.stl' if template else None
        super(WopHeater, self).__init__(name, case_dir, model_type, bg_region, dimensions, location, rotation,
                                        stl_path=stl_path, of_interface=of_interface)

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a heater"""
        set_boundary_to_heater(self.name, self._bg_region, self._boundary_conditions, self.temperature)
        self._boundary_conditions[self.name]['T'].internalField.value = self._temperature

    def bind_region_boundaries(self, region_boundaries: dict):
        """
        Binds the thing boundary conditions to a class
        Binding regions can only be performed once a case is setup,
        i.e., the boundary files are produced
        :param region_boundaries: dict of a region boundary conditions
        """
        self._boundary_conditions = region_boundaries
        self._add_initial_boundaries()

    @property
    def temperature(self):
        """Temperature getter"""
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """
        Sets heater temperature by modifying the latest results
        :param temperature: temperature in C
        """
        if self._snappy_dict is None and self._boundary_conditions is None:
            raise Exception('SnappyHexMesh and/or Boundary conditions were not bound')
        latest_result = get_latest_time(self._case_dir)
        self._temperature = float(temperature)
        set_boundary_to_heater(self.name, self._bg_region, self._boundary_conditions, self._temperature, latest_result)


def main():
    case_dir = 'test.case'
    heater = WopHeater('heater', case_dir, 'fluid', [1, 2, 3])
    heater.model.show()


if __name__ == '__main__':
    main()
