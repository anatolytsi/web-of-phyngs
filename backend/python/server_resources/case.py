from flask_restful import Resource, reqparse

from backend.python.wopsimulator.loader import load_case, create_case, get_cases_names, save_case, remove_case


class Case(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('type', type=str, help='Web of Phyngs case type')
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
            return str(e)

    def post(self, case_name):
        args = self.reqparse.parse_args()
        try:
            case = create_case(case_name, args)
            return case.dump_case()
        except (ValueError, FileExistsError) as e:
            return str(e)
        except Exception as e:
            return str(e)

    def patch(self, case_name):
        args = self.reqparse.parse_args()
        try:
            case = load_case(case_name)
            for key, value in args.items():
                if value is not None:
                    case[key] = value
            save_case(case_name, case)
            return case.dump_case()
        except ValueError:
            return f'Case {case_name} is not defined'
        except Exception as e:
            return str(e)

    def delete(self, case_name):
        try:
            remove_case(case_name, remove_case_dir=True)
            return f'Case {case_name} was deleted'
        except Exception as e:
            return str(e)


class CaseList(Resource):
    def get(self):
        try:
            return get_cases_names()
        except Exception as e:
            return str(e)
