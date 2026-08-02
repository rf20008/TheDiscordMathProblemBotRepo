TYPE_TO_CLASS = {}
CLASS_TO_TYPE = {}


def register_problem(type_name=None):
    def wrapper(cls):
        name = type_name or cls.__name__
        TYPE_TO_CLASS[name] = cls
        CLASS_TO_TYPE[cls] = name
        return cls

    return wrapper


__all__ = [register_problem, TYPE_TO_CLASS, CLASS_TO_TYPE]
