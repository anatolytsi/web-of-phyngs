import time

from wopsimulator.loader import create_case, load_case


def main():
    case_name = 'my_room'
    is_run_parallel = True
    timestep = 30
    try:
        case_cls, case_path = create_case(case_name, 'cht_room')
        room = case_cls(case_name, is_blocking=False, is_run_parallel=is_run_parallel, num_of_cores=4)
        # Here follows a desired future behavior after creation of a new case
        # room.create(dimensions=[2, 3, 4])
        # # or
        # room.create(stl_path='./room.stl')
        #
        # room.add_heater(name='heater1', location=[1.5, 0.5, 0], heater_template='convective1')
        # room.add_heater(name='heater2', location=[0, 0, 0], dimensions=[0.1, 0.2, 0.3], heater_type='convective',...)
        # room.add_window(dimensions=[1, 1], location=[0, 1.5, 2])
        # room.add_door(dimensions=[1, 2], location=[1.5, 0, 2])

    except FileExistsError:
        case_cls, case_path = load_case(case_name)
        room = case_cls(case_name, is_blocking=False, is_run_parallel=is_run_parallel, num_of_cores=4)
    room.setup()
    room.run()
    time.sleep(timestep)
    room.stop()
    # room['heater1'].turn_on(50)  # TODO: This is a desired future implementation
    # room.run()
    # time.sleep(timestep)
    # room.stop()
    # room['heater1'].turn_off  # TODO: This is a desired future implementation
    # room.run()
    # time.sleep(timestep)
    # room.stop()


if __name__ == '__main__':
    main()
