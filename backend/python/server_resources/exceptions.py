import traceback

from wopsimulator.exceptions import CaseTypeError, CaseNotFound, CaseAlreadyExists, WrongObjectType, \
    ObjectNotFound


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
            traceback.print_exc()
            return str(e), 400
        except (CaseNotFound, ObjectNotFound) as e:
            traceback.print_exc()
            return str(e), 404
        except Exception as e:
            traceback.print_exc()
            resp = (str(e), 500)
            return resp

    return wrapper
