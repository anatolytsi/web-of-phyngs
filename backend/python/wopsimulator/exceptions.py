class CaseTypeError(Exception):
    """Incorrect case type"""
    pass


class CaseNotFound(Exception):
    """Required case was not found"""
    pass


class CaseAlreadyExists(Exception):
    """Case cannot be created as it already exists"""
    pass


class WrongObjectType(Exception):
    """Wrong object type error"""
    pass


class ObjectNotFound(Exception):
    """Required object was not found"""
    pass


class ObjectSetValueFailed(Exception):
    """Object value setting failed"""
    pass
