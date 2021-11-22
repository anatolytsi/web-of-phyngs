from flask_restful import Resource, reqparse

from .case import auto_load_case
from .exceptions import catch_error


class ObjectList(Resource):
    current_cases = None

    @catch_error
    @auto_load_case
    def get(self, case_name):
        obj_list = []
        for obj in self.current_cases[case_name].get_objects().values():
            dump = obj.dump_settings()
            dump_dict = list(dump.values())[0]
            dump_dict['name'] = list(dump.keys())[0]
            dump_dict['type'] = obj.type_name
            obj_list.append(dump_dict)
        return obj_list


class Object(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, help='Object name')
        self.reqparse.add_argument('type', type=str, help='Object type')
        self.reqparse.add_argument('dimensions', type=list, help='Object dimensions', location='json')
        self.reqparse.add_argument('location', type=list, help='Object location', location='json')
        self.reqparse.add_argument('rotation', type=list, help='Object rotation', location='json')
        self.reqparse.add_argument('template', type=str, help='Object template geometry')
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
        self.current_cases[case_name].add_object(obj_name, args['type'], args['template'], args['dimensions'],
                                                 args['location'], args['rotation'], args['field'])
        return '', 201

    @catch_error
    def patch(self, case_name, obj_name):
        pass


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
