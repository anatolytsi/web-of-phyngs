import time

from .openfoam.common.filehandling import force_remove_dir, get_numerated_dirs
from .openfoam.interface import OpenFoamInterface


class ChtRoom(OpenFoamInterface):
    def __init__(self, *args, **kwargs):
        solver = 'chtMultiRegionFoam'
        super(ChtRoom, self).__init__(solver, *args, **kwargs)

    def clean_case(self):
        super(ChtRoom, self).clean_case()
        force_remove_dir(f'{self.case_dir}/0')
        force_remove_dir(f'{self.case_dir}/postProcessing')

    def setup(self):
        self.clean_case()
        self.copy_stls()
        self.run_block_mesh()
        self.run_snappy_hex_mesh()
        self.run_split_mesh_regions(cell_zones_only=True)
        self.run_setup_cht()
        self.get_boundary_conditions()
        self.boundaries['heater']['T']['initial']['internalField']['value'] = \
            self.boundaries['fluid']['T']['initial']['internalField']['value']
        self.boundaries['heater']['T']['initial']['internalField']['is_uniform'] = \
            self.boundaries['fluid']['T']['initial']['internalField']['is_uniform']
        self.boundaries['heater']['T'].save_initial_internal_field()
        # self.boundaries['heater']['T']['initial']['heater_to_fluid']['value'] = 310.0
        # self.boundaries['heater']['T']['initial']['heater_to_fluid']['is_uniform'] = True
        # self.boundaries['heater']['T'].save_initial_boundary('heater_to_fluid')

    def run(self):
        super(ChtRoom, self).run()
        # time.sleep(15)
        # self.solver.stopWithoutWrite()
        # test = self.solver.getSolutionDirectory()
        # print(test)
        # print(1)


def turn_on_heater(room, latest_result, is_run_parallel):
    room.boundaries['heater']['T'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    room.boundaries['heater']['T']['latest']['heater_to_fluid']['value'] = 500.0
    room.boundaries['heater']['T']['latest']['internalField'] = 500.0
    for field in room.boundaries['heater']['T']['latest'].keys():
        if 'procBoundary' in field:
            room.boundaries['heater']['T']['latest'][field]['value'] = 500.0
    room.boundaries['heater']['T'].save_latest_boundaries(is_run_parallel=is_run_parallel)


def turn_off_heater(room, latest_result, is_run_parallel):
    room.boundaries['heater']['T'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    room.boundaries['fluid']['T'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    room_temperature = room.boundaries['fluid']['T']['latest']['internalField']
    room.boundaries['heater']['T']['latest']['heater_to_fluid']['value'] = room_temperature
    room.boundaries['heater']['T']['latest']['internalField'] = room_temperature
    for field in room.boundaries['heater']['T']['latest'].keys():
        if 'procBoundary' in field:
            room.boundaries['heater']['T']['latest'][field]['value'] = room_temperature
    room.boundaries['heater']['T'].save_latest_boundaries(is_run_parallel=is_run_parallel)


def open_window(room, latest_result, is_run_parallel):
    room.boundaries['fluid']['alphat'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    room.boundaries['fluid']['epsilon'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    room.boundaries['fluid']['k'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    room.boundaries['fluid']['nut'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    # room.boundaries['fluid']['p'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    # room.boundaries['fluid']['p_rgh'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    room.boundaries['fluid']['T'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    room.boundaries['fluid']['U'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)

    room.boundaries['fluid']['alphat']['latest']['outlet']['type'] = 'calculated'
    room.boundaries['fluid']['alphat'].save_latest_boundaries(is_run_parallel=is_run_parallel)

    # room.boundaries['fluid']['epsilon']['latest']['outlet']['type'] = 'inletOutlet'
    # room.boundaries['fluid']['epsilon']['latest']['outlet']['value'] = 0.001
    # room.boundaries['fluid']['epsilon']['latest']['outlet']['is_uniform'] = True
    # room.boundaries['fluid']['epsilon']['latest']['outlet']['inletValue'] = 0.001

    room.boundaries['fluid']['k']['latest']['outlet']['type'] = 'inletOutlet'
    room.boundaries['fluid']['k']['latest']['outlet']['value'] = 0.02
    room.boundaries['fluid']['k']['latest']['outlet']['is_uniform'] = True
    room.boundaries['fluid']['k']['latest']['outlet']['inletValue'] = 0.02
    room.boundaries['fluid']['k'].save_latest_boundaries(is_run_parallel=is_run_parallel)

    room.boundaries['fluid']['nut']['latest']['outlet']['type'] = 'calculated'
    room.boundaries['fluid']['nut'].save_latest_boundaries(is_run_parallel=is_run_parallel)

    room.boundaries['fluid']['T']['latest']['outlet']['type'] = 'inletOutlet'
    room.boundaries['fluid']['T']['latest']['outlet']['value'] = 280
    room.boundaries['fluid']['T']['latest']['outlet']['is_uniform'] = True
    room.boundaries['fluid']['T']['latest']['outlet']['inletValue'] = 280
    room.boundaries['fluid']['T'].save_latest_boundaries(is_run_parallel=is_run_parallel)

    room.boundaries['fluid']['U']['latest']['outlet']['type'] = 'pressureInletOutletVelocity'
    room.boundaries['fluid']['U']['latest']['outlet']['value'] = '$internalField'
    room.boundaries['fluid']['U'].save_latest_boundaries(is_run_parallel=is_run_parallel)


def main():
    is_run_parallel = True
    timestep = 30
    start = time.time()
    room = ChtRoom('cht_room', is_blocking=False, is_run_parallel=is_run_parallel, num_of_cores=4)

    # room.get_boundary_conditions()
    # room.case_is_decomposed = True
    #
    # latest_result = '1'
    # room.boundaries['heater']['T'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    # room.boundaries['heater']['T']['latest']['heater_to_fluid']['value'] = 500.0
    # room.boundaries['heater']['T']['latest']['internalField'] = 500.0
    # for field in room.boundaries['heater']['T']['latest'].keys():
    #     if 'procBoundary' in field:
    #         room.boundaries['heater']['T']['latest'][field]['value'] = 500.0
    # room.boundaries['heater']['T'].save_latest_boundaries(is_run_parallel=is_run_parallel)

    # Start a normal case
    room.setup()
    room.run()
    time.sleep(timestep)

    # # Stop, change the latest boundaries and run (Temperature)
    # end = time.time()
    # room.stop()
    # print(f'Elapsed time: {end - start}')
    # # make a function to update all boundaries from latest
    # # make function to get latest run time getter
    # latest_result = sorted(
    #     [int(val) for val in get_numerated_dirs(f'cht_room{"/processor0" if is_run_parallel else ""}', exception='0')])[
    #     -1]
    # print(f'Latest simulation result is: {latest_result}')
    # print(f'1 s of simulation per real time: {(end - start) / latest_result}')
    # start = end
    # turn_on_heater(room, latest_result, is_run_parallel)
    # room.run()
    # time.sleep(timestep)

    # # Stop, change the latest boundaries and run (Window)
    # end = time.time()
    # room.stop()
    # print(f'Elapsed time: {end - start}')
    # # make a function to update all boundaries from latest
    # # make function to get latest run time getter
    # latest_result = sorted(
    #     [int(val) for val in get_numerated_dirs(f'cht_room{"/processor0" if is_run_parallel else ""}', exception='0')])[
    #     -1]
    # print(f'Latest simulation result is: {latest_result}')
    # print(f'1 s of simulation per real time: {(end - start) / latest_result}')
    # start = end
    # open_window(room, latest_result, is_run_parallel)
    # room.run()
    # time.sleep(timestep)

    for _ in range(3):
        # Stop, change the latest boundaries and run (Temperature)
        end = time.time()
        room.stop()
        print(f'Elapsed time: {end - start}')
        # make a function to update all boundaries from latest
        # make function to get latest run time getter
        latest_result = sorted(
            [int(val) for val in
             get_numerated_dirs(f'cht_room{"/processor0" if is_run_parallel else ""}', exception='0')])[
            -1]
        print(f'Latest simulation result is: {latest_result}')
        print(f'1 s of simulation per real time: {(end - start) / latest_result}')
        start = end
        turn_on_heater(room, latest_result, is_run_parallel)
        room.run()
        time.sleep(timestep)

        # Stop, change the latest boundaries and run (Temperature)
        end = time.time()
        room.stop()
        print(f'Elapsed time: {end - start}')
        # make a function to update all boundaries from latest
        # make function to get latest run time getter
        latest_result = sorted(
            [int(val) for val in
             get_numerated_dirs(f'cht_room{"/processor0" if is_run_parallel else ""}', exception='0')])[
            -1]
        print(f'Latest simulation result is: {latest_result}')
        print(f'1 s of simulation per real time: {(end - start) / latest_result}')
        start = end
        turn_off_heater(room, latest_result, is_run_parallel)
        room.run()
        time.sleep(timestep)

    # # Stop, change the latest boundaries and run (Wind speed)
    # end = time.time()
    # room.stop()
    # print(f'Elapsed time: {end - start}')
    # latest_result = sorted(
    #     [int(val) for val in get_numerated_dirs(f'cht_room{"/processor0" if is_run_parallel else ""}', exception='0')])[
    #     -1]
    # print(f'Latest simulation result is: {latest_result}')
    # print(f'1 s of simulation per real time: {(end - start) / latest_result}')
    # start = end
    # room.boundaries['fluid']['U'].update_latest_boundaries(latest_result, is_run_parallel=is_run_parallel)
    # room.boundaries['fluid']['U']['latest']['inlet']['value'] = [0, 1, 0]
    # room.boundaries['fluid']['U'].save_latest_boundaries(is_run_parallel=is_run_parallel)
    # room.run()
    # time.sleep(timestep)

    # Finally, stop the simulation for good
    end = time.time()
    room.stop()
    print(f'Elapsed time: {end - start}')
    latest_result = sorted(
        [int(val) for val in get_numerated_dirs(f'cht_room{"/processor0" if is_run_parallel else ""}', exception='0')])[
        -1]
    print(f'Latest simulation result is: {latest_result}')
    print(f'1 s of simulation per real time: {(end - start) / latest_result}')

    # Should be done in a separate function (e.g. postprocess)
    room.run_reconstruct(all_regions=True)
    # Saving new boundaries works for now
    # TODO: Next step: stopping mid simulation, changing some value, continuing and observing how data changed
    # print(1)


if __name__ == '__main__':
    main()
