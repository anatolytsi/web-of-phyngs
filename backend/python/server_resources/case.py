import traceback

from flask_restful import Resource, reqparse

from backend.python.wopsimulator.loader import load_case, create_case, get_cases_names, save_case, remove_case


class Case(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('type', type=str, help='Web of Phyngs case type')
        self.reqparse.add_argument('mesh_quality', type=int, help='Case mesh quality in percents')
        self.reqparse.add_argument('parallel', type=bool, help='Run case in parallel')
        self.reqparse.add_argument('cores', type=int, help='Number of cores for parallel run')
        self.reqparse.add_argument('background', type=str, help='Case background region')
        super(Case, self).__init__()

    def get(self, case_name):
        try:
            case = load_case(case_name)
            return case.dump_case()
        except ValueError:
            return f'Case is not defined'
        except Exception as e:
            traceback.print_exc()
            return str(e)

    def post(self, case_name):
        args = self.reqparse.parse_args()
        try:
            case = create_case(case_name, args)
            self.current_cases[case_name] = case
            return case.dump_case()
        except (ValueError, FileExistsError) as e:
            traceback.print_exc()
            return str(e)
        except Exception as e:
            traceback.print_exc()
            return str(e)

    def patch(self, case_name):
        args = self.reqparse.parse_args()
        try:
            if case_name not in self.current_cases:
                self.current_cases[case_name] = load_case(case_name)
            for key, value in args.items():
                if value is not None:
                    self.current_cases[case_name][key] = value
            save_case(case_name, self.current_cases[case_name])
            # Reload the case with new changes applied
            self.current_cases[case_name] = load_case(case_name)
            return self.current_cases[case_name].dump_case()
        except ValueError:
            return f'Case {case_name} is not defined'
        except Exception as e:
            traceback.print_exc()
            return e

    def delete(self, case_name):
        try:
            if case_name in self.current_cases:
                del self.current_cases[case_name]
            remove_case(case_name, remove_case_dir=True)
            return f'Case {case_name} was deleted'
        except Exception as e:
            traceback.print_exc()
            return str(e)


class CaseList(Resource):
    def get(self):
        try:
            return get_cases_names()
        except Exception as e:
            traceback.print_exc()
            return str(e)
