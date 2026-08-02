PREFIX_REGISTRY = {}
DICT_TYPE_REVERSE_REGISTRY = {}


def register_dict(type_name: str | None = None):
    def wrapper(cls):
        name = type_name or cls.__name__
        PREFIX_REGISTRY[name] = cls
        DICT_TYPE_REVERSE_REGISTRY[cls] = name
        return cls

    return wrapper


__all__ = [register_dict, PREFIX_REGISTRY, DICT_TYPE_REVERSE_REGISTRY]
