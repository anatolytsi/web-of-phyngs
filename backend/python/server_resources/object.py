from flask_restful import Resource, reqparse

from backend.python.wopsimulator.loader import load_case


class ObjectList(Resource):
    current_cases = None

    def get(self, case_name):
        try:
            if case_name not in self.current_cases:
                self.current_cases[case_name] = load_case(case_name)
            obj_dict = {}
            for obj in self.current_cases[case_name].get_objects().values():
                obj_dict.update(obj.dump_settings())
            return obj_dict
        except Exception as e:
            return str(e)


class Object(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, help='Object name')
        self.reqparse.add_argument('type', type=str, help='Object type')
        self.reqparse.add_argument('dimensions', type=list, help='Object dimensions', location='json')
        self.reqparse.add_argument('location', type=list, help='Object location', location='json')
        self.reqparse.add_argument('rotation', type=list, help='Object rotation', location='json')
        self.reqparse.add_argument('field', type=str, help='Sensor field')
        super(Object, self).__init__()

    def get(self, case_name, obj_name):
        try:
            if case_name not in self.current_cases:
                self.current_cases[case_name] = load_case(case_name)
            obj = self.current_cases[case_name].get_object(obj_name)
            return obj.dump_settings()
        except ValueError as e:
            return str(e)
        except Exception as e:
            return str(e)

    def post(self, case_name, obj_name):
        args = self.reqparse.parse_args()
        try:
            if case_name not in self.current_cases:
                self.current_cases[case_name] = load_case(case_name)
            self.current_cases[case_name].add_object(obj_name, args['type'], args['dimensions'],
                                                            args['location'], args['rotation'], args['field'])
        except Exception as e:
            return str(e)

    def patch(self, case_name):
        pass


class ObjectValue(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('value', type=str, help='Object value')
        super(ObjectValue, self).__init__()

    def get(self, case_name, obj_name, obj_value):
        try:
            obj = self.current_cases[case_name].get_object(obj_name)
            if obj_value in obj:
                return obj[obj_value]
            return f'Property {obj_value} is not implemented for object {obj_name}'
        except Exception as e:
            return str(e)

    def post(self, case_name, obj_name, obj_value):
        try:
            if case_name not in self.current_cases:
                self.current_cases[case_name] = load_case(case_name)
            value = self.reqparse.parse_args(strict=True)['value']
            obj = self.current_cases[case_name].get_object(obj_name)
            if obj_value in obj:
                obj[obj_value] = value
                return value
            else:
                return f'Property {obj_value} is not implemented for object {obj_name}'
        except Exception as e:
            return str(e)
