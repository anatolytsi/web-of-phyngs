import atexit
import os
import signal
import configparser

from flask import Flask
from flask_restful import Api

from server_resources.exceptions import ErrorList
from server_resources.case import Case, CaseList
from server_resources.commands import Command
from server_resources.object import Object, ObjectList, ObjectValue
from server_resources.postprocess import Postprocess


class Server:
    def __init__(self, host, port, debug):
        self.host = host
        self.port = port
        self.debug = debug
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.current_cases = {}
        Case.current_cases = self.current_cases
        Command.current_cases = self.current_cases
        ObjectList.current_cases = self.current_cases
        Object.current_cases = self.current_cases
        ObjectValue.current_cases = self.current_cases
        self.api.add_resource(Command, '/case/<string:case_name>/<string:command>', endpoint='command')
        self.api.add_resource(CaseList, '/case', endpoint='cases')
        self.api.add_resource(Case, '/case/<string:case_name>', endpoint='case')
        self.api.add_resource(ObjectList, '/case/<string:case_name>/object/', endpoint='objects')
        self.api.add_resource(Object, '/case/<string:case_name>/object/<string:obj_name>', endpoint='object')
        self.api.add_resource(ObjectValue, '/case/<string:case_name>/object/<string:obj_name>/<string:obj_value>',
                              endpoint='object_value')
        self.api.add_resource(ErrorList, '/errors')
        self.api.add_resource(Postprocess, '/postprocess', '/postprocess/<string:command>')

    def run(self):
        self.app.run(self.host, self.port, self.debug)


def main():
    # Kill all spawned processes before exiting
    atexit.register(lambda: os.killpg(os.getpid(), signal.SIGINT))
    config = configparser.ConfigParser()
    config.read(f'{os.path.dirname(os.path.abspath(__file__))}/server.ini')
    server = Server(host=config['DEFAULT']['Host'],
                    port=config.getint('DEFAULT', 'Port'),
                    debug=config.getboolean('DEFAULT', 'Debug'))
    server.run()


if __name__ == '__main__':
    main()
