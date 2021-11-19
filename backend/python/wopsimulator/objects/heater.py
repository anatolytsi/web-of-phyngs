import os

from backend.python.wopsimulator.exceptions import ObjectSetValueFailed
from backend.python.wopsimulator.objects.behavior.cht import set_boundary_to_heater
from backend.python.wopsimulator.objects.wopthings import WopObject
from backend.python.wopsimulator.openfoam.common.parsing import get_latest_time


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
        self.template = template
        stl_path = f'{os.path.dirname(os.path.abspath(__file__))}/geometry/heaters/{template}' \
                   f'{"" if template[-4:] == ".stl" else ".stl"}' if template else ''
        super(WopHeater, self).__init__(name, case_dir, model_type, bg_region, dimensions, location, rotation,
                                        stl_path=stl_path, of_interface=of_interface)
        self._region = name
        self._fields = ['T']

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
        if region_boundaries:
            self._boundary_conditions = region_boundaries
            self._add_initial_boundaries()

    def dump_settings(self):
        settings = super(WopHeater, self).dump_settings()
        settings[self.name].update({'temperature': self._temperature})
        return settings

    @property
    def temperature(self):
        """Temperature getter"""
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """
        Sets heater temperature by modifying the latest results
        :param temperature: temperature in K
        """
        self._temperature = float(temperature)
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            self._boundary_conditions[self.name]['T'].update_time(latest_result)
            if latest_result != 0:
                heater_boundary_name = f'{self.name}_to_{self._bg_region}'
                t = self._boundary_conditions[self.name]['T']
                t.internalField.value = temperature
                t[heater_boundary_name].value = temperature
            else:
                set_boundary_to_heater(self.name, self._bg_region, self._boundary_conditions, self._temperature,
                                       latest_result)
        except Exception as e:
            raise ObjectSetValueFailed(e)


def main():
    case_dir = 'test.case'
    heater = WopHeater('heater', case_dir, 'fluid', [1, 2, 3])
    heater.model.show()


if __name__ == '__main__':
    main()
