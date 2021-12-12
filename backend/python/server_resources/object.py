from flask_restful import Resource, reqparse

from .case import auto_load_case
from .exceptions import catch_error
from wopsimulator.loader import save_case


class ObjectList(Resource):
    current_cases = None

    @catch_error
    @auto_load_case
    def get(self, case_name):
        obj_list = []
        for obj in self.current_cases[case_name].get_objects().values():
            dump = obj.dump_settings()
            if 'name' not in dump.keys():
                name = list(dump.keys())[0]
                dump = list(dump.values())[0]
                dump['name'] = name
            dump['type'] = obj.type_name
            obj_list.append(dump)
        return obj_list


class Object(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, help='Object name')
        self.reqparse.add_argument('type', type=str, help='Object type')
        self.reqparse.add_argument('url', type=str, help='Object STL url')
        self.reqparse.add_argument('dimensions', type=list, help='Object dimensions', location='json')
        self.reqparse.add_argument('location', type=list, help='Object location', location='json')
        self.reqparse.add_argument('rotation', type=list, help='Object rotation', location='json')
        self.reqparse.add_argument('template', type=str, help='Object template geometry')
        self.reqparse.add_argument('material', type=str, help='Object material')
        self.reqparse.add_argument('field', type=str, help='Sensor field')
        super(Object, self).__init__()

    @catch_error
    @auto_load_case
    def get(self, case_name, obj_name):
        obj = self.current_cases[case_name].get_object(obj_name)
        return obj.dump_settings()

    @catch_error
    @auto_load_case
    def post(self, case_name, obj_name):
        args = self.reqparse.parse_args()
        self.current_cases[case_name].add_object(obj_name, args['type'], url=args['url'], template=args['template'],
                                                 dimensions=args['dimensions'], location=args['location'],
                                                 rotation=args['rotation'], sns_field=args['field'],
                                                 material=args['material'])
        save_case(case_name, self.current_cases[case_name])
        return '', 201

    @catch_error
    @auto_load_case
    def patch(self, case_name, obj_name):
        params = self.reqparse.parse_args()
        if obj_name in self.current_cases[case_name].objects or obj_name in self.current_cases[case_name].sensors:
            self.current_cases[case_name].modify_object(obj_name, params)
            save_case(case_name, self.current_cases[case_name])
            return '', 200
        return f'Object/sensor {obj_name} does not exist in case {case_name}', 404

    @catch_error
    @auto_load_case
    def delete(self, case_name, obj_name):
        if obj_name in self.current_cases[case_name].objects or obj_name in self.current_cases[case_name].sensors:
            self.current_cases[case_name].remove_object(obj_name)
            save_case(case_name, self.current_cases[case_name])
            return '', 200
        return f'Object/sensor {obj_name} does not exist in case {case_name}', 404


class ObjectValue(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('value', type=str, help='Object value')
        super(ObjectValue, self).__init__()

    @catch_error
    @auto_load_case
    def get(self, case_name, obj_name, obj_value):
        obj = self.current_cases[case_name].get_object(obj_name)
        if obj_value in obj:
            return obj[obj_value]
        # TODO: move this error
        raise KeyError(f'Property "{obj_value}" for object "{obj_name} does not exist')

    @catch_error
    @auto_load_case
    def post(self, case_name, obj_name, obj_value):
        value = self.reqparse.parse_args(strict=True)['value']
        obj = self.current_cases[case_name].get_object(obj_name)
        if obj_value in obj:
            obj[obj_value] = value
            return '', 200
        # TODO: move this error
        raise KeyError(f'Property "{obj_value}" for object "{obj_name} does not exist')
