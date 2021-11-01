import time

from backend.python.wopsimulator.objects.heater import WopHeater
from backend.python.wopsimulator.loader import create_case, load_case, save_case


def main():
    case_name = 'my_room'
    timestep = 30
    case_parameters = {
        "type": "cht_room",
        "path": "./my_room.case",
        "blocking": False,
        "parallel": True,
        "cores": 4,
        "background": "fluid"
    }
    try:
        room = create_case(case_name, case_parameters)
        room_dimensions = [3, 4, 2.5]
        window_dimension = [1.5, 0, 1.25]
        door_dimension = [1.5, 0, 2]
        heater_dimensions = [1, 0.2, 0.7]

        window_location = [(room_dimensions[0] - window_dimension[0]) / 2,
                           0,
                           (room_dimensions[2] - window_dimension[2]) / 2]
        door_location = [(room_dimensions[0] - door_dimension[0]) / 2,
                         room_dimensions[1],
                         (room_dimensions[2] - door_dimension[2]) / 2]
        heater_location = [1, 1, 0.2]
        sensor_location = [1.5, 2, 1]
        room.add_object(name='walls', obj_type='walls', dimensions=room_dimensions)
        room.add_object('inlet', 'window', dimensions=window_dimension, location=window_location)
        room.add_object('outlet', 'door', dimensions=door_dimension, location=door_location)
        room.add_object('heater', 'heater', dimensions=heater_dimensions, location=heater_location)
        room.add_object('temp_sensor', 'sensor', location=sensor_location, sns_field='T')
        room.setup()
        room.heaters['heater'].temperature = 450
        save_case(case_name, room)

    except FileExistsError:
        room = load_case(case_name)

    room.run()
    time.sleep(timestep)
    room.stop()


if __name__ == '__main__':
    main()
