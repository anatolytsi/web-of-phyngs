import werkzeug.datastructures
from flask_restful import Resource, reqparse

from .case import auto_load_case
from .exceptions import catch_error
from wopsimulator.loader import save_case
from wopsimulator.exceptions import PhyngNotFound


class PhyngList(Resource):
    current_cases = None

    @catch_error
    @auto_load_case
    def get(self, case_name):
        obj_list = []
        for obj in self.current_cases[case_name].get_phyngs().values():
            dump = obj.dump_settings()
            if 'name' not in dump.keys():
                name = list(dump.keys())[0]
                dump = list(dump.values())[0]
                dump['name'] = name
            dump['type'] = obj.type_name
            obj_list.append(dump)
        return obj_list


class Phyng(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, help='Phyng name')
        self.reqparse.add_argument('type', type=str, help='Phyng type')
        self.reqparse.add_argument('url', type=str, help='Phyng STL url')
        self.reqparse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        self.reqparse.add_argument('dimensions', type=list, help='Phyng dimensions', location='json')
        self.reqparse.add_argument('location', type=list, help='Phyng location', location='json')
        self.reqparse.add_argument('rotation', type=list, help='Phyng rotation', location='json')
        self.reqparse.add_argument('template', type=str, help='Phyng template geometry')
        self.reqparse.add_argument('material', type=str, help='Phyng material')
        self.reqparse.add_argument('field', type=str, help='Sensor field')
        super(Phyng, self).__init__()

    @catch_error
    @auto_load_case
    def get(self, case_name, phyng_name):
        obj = self.current_cases[case_name].get_phyng(phyng_name)
        return obj.dump_settings()

    @catch_error
    @auto_load_case
    def post(self, case_name, phyng_name):
        args = self.reqparse.parse_args()
        file = args['file']
        if file and '.stl' in file.filename:
            file.save(f'{self.current_cases[case_name].path}/geometry/{phyng_name}.stl')
            self.current_cases[case_name].modify_phyng(phyng_name, {'custom': True})
            save_case(case_name, self.current_cases[case_name])
            return '', 200
        self.current_cases[case_name].add_phyng(phyng_name, args['type'], url=args['url'], template=args['template'],
                                                dimensions=args['dimensions'], location=args['location'],
                                                rotation=args['rotation'], sns_field=args['field'],
                                                material=args['material'])
        save_case(case_name, self.current_cases[case_name])
        return '', 201

    @catch_error
    @auto_load_case
    def patch(self, case_name, phyng_name):
        params = self.reqparse.parse_args()
        if phyng_name in self.current_cases[case_name].phyngs or phyng_name in self.current_cases[case_name].sensors:
            self.current_cases[case_name].modify_phyng(phyng_name, params)
            save_case(case_name, self.current_cases[case_name])
            return '', 200
        raise PhyngNotFound(f'Phyng {phyng_name} does not exist in case {case_name}')

    @catch_error
    @auto_load_case
    def delete(self, case_name, phyng_name):
        if phyng_name in self.current_cases[case_name].phyngs or phyng_name in self.current_cases[case_name].sensors:
            self.current_cases[case_name].remove_phyng(phyng_name)
            save_case(case_name, self.current_cases[case_name])
            return '', 200
        raise PhyngNotFound(f'Phyng {phyng_name} does not exist in case {case_name}')


class PhyngValue(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('value', type=str, help='Phyng value')
        super(PhyngValue, self).__init__()

    @catch_error
    @auto_load_case
    def get(self, case_name, phyng_name, obj_value):
        obj = self.current_cases[case_name].get_phyng(phyng_name)
        if obj_value in obj:
            return obj[obj_value]
        # TODO: move this error
        raise KeyError(f'Property "{obj_value}" for phyng "{phyng_name} does not exist')

    @catch_error
    @auto_load_case
    def post(self, case_name, phyng_name, obj_value):
        value = self.reqparse.parse_args(strict=True)['value']
        obj = self.current_cases[case_name].get_phyng(phyng_name)
        if obj_value in obj:
            obj[obj_value] = value
            return '', 200
        # TODO: move this error
        raise KeyError(f'Property "{obj_value}" for phyng "{phyng_name} does not exist')
