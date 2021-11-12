from flask_restful import Resource, reqparse

from backend.python.wopsimulator.loader import load_case, get_cases_names, save_case

COMMAND_HELP = 'help'
COMMAND_LIST = 'list'
COMMAND_CREATE = 'create'
COMMAND_LOAD = 'load'
COMMAND_MOD = 'modify'
COMMAND_SAVE = 'save'
COMMAND_CLEAN = 'clean'
COMMAND_SETUP = 'setup'
COMMAND_RUN = 'run'
COMMAND_STOP = 'stop'
COMMAND_PROCESS = 'postprocess'

COMMANDS = {
    COMMAND_HELP: 'Returns this JSON',
    COMMAND_SAVE: 'Saves case configuration',
    COMMAND_CLEAN: 'Cleans case',
    COMMAND_SETUP: 'Setups case',
    COMMAND_RUN: 'Runs case',
    COMMAND_STOP: 'Stops case',
    COMMAND_PROCESS: 'Post-process case'
}


class Command(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('fields', type=list, help='Fields to post-process', location='json')
        self.reqparse.add_argument('region', type=str, help='Region to post-process')
        super(Command, self).__init__()

    def get(self, case_name, command):
        if command not in COMMANDS:
            return f'Command {command} is on defined'
        return COMMANDS[command]

    def post(self, case_name, command):
        try:
            if command == COMMAND_HELP:
                return COMMANDS
            if case_name not in self.current_cases:
                self.current_cases[case_name] = load_case(case_name)
            if command == COMMAND_SAVE:
                save_case(case_name, self.current_cases[case_name])
                return self.current_cases[case_name].dump_case()
            elif command == COMMAND_CLEAN:
                self.current_cases[case_name].clean_case()
                save_case(case_name, self.current_cases[case_name])
                return f'Case {case_name} was cleaned'
            elif command == COMMAND_SETUP:
                self.current_cases[case_name].setup()
                save_case(case_name, self.current_cases[case_name])
                return f'Case {case_name} was setup'
            elif command == COMMAND_RUN:
                self.current_cases[case_name].run()
                return f'Case {case_name} is running'
            elif command == COMMAND_STOP:
                self.current_cases[case_name].stop()
                return f'Case {case_name} was stopped'
            elif command == COMMAND_PROCESS:
                args = self.reqparse.parse_args()
                if self.current_cases[case_name].running:
                    self.current_cases[case_name].stop()
                if self.current_cases[case_name].parallel:
                    if not args['region']:
                        self.current_cases[case_name].run_reconstruct(all_regions=True)
                    else:
                        self.current_cases[case_name].run_reconstruct(region=args['region'], fields=args['fields'])
        except Exception as e:
            return str(e)
