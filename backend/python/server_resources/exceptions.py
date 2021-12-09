import traceback

from flask_restful import Resource
from wopsimulator.exceptions import CaseTypeError, CaseNotFound, CaseAlreadyExists, WrongObjectType, \
    ObjectNotFound

simulator_exceptions = {
    'texts': [],
    'traces': []
}


def catch_error(func):
    """
    WoP Flask error catching decorator
    :param func: function to decorate
    :return: Flask response
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (CaseTypeError, CaseAlreadyExists, WrongObjectType,) as e:
            error_text, status = str(e), 400
        except (CaseNotFound, ObjectNotFound) as e:
            error_text, status = str(e), 404
        except Exception as e:
            error_text, status = str(e), 500
        traceback.print_exc()
        simulator_exceptions['texts'].append(error_text)
        simulator_exceptions['traces'].append(traceback.format_exc())
        return error_text, status

    return wrapper


class ErrorList(Resource):

    @staticmethod
    def get():
        return simulator_exceptions

    @staticmethod
    def delete():
        simulator_exceptions['texts'].clear()
        simulator_exceptions['traces'].clear()
