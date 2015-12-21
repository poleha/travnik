from .app_settings import settings
from django.db.models import Model
import inspect


def get_attr_or_item(obj, attr):
    res = getattr(obj, attr, None)
    if res is None:
        try:
            res = obj.get(attr, None)
        except:
            res = None
    return res


def rec_getattr(obj, attr):
    if '.' not in attr:
        return get_attr_or_item(obj, attr)
    else:
        L = attr.split('.')
        return rec_getattr(get_attr_or_item(obj, L[0]), '.'.join(L[1:]))


def make_key_from_args(args, kwargs):
    res_args = ''
    for arg in args + tuple(kwargs.values()):
        if isinstance(arg, tuple(settings.special_cases.keys())):
            res_arg = get_class_path(type(arg))
            for v in settings.special_cases[type(arg)]:
                res_arg += '_' + str(rec_getattr(arg, v))
            res_args += '_' + res_arg
        elif isinstance(arg, Model):
            res_args += '{0}-{1}'.format(get_class_path(type(arg)), arg.pk)
        elif isinstance(arg, str):
            res_args += '_' + arg
        else:
            res_args += '_' + str(arg)
    return res_args


def get_class_path(klass):
    return '{0}.{1}'.format(inspect.getmodule(klass).__name__, klass.__name__)


def get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
    if inspect.isfunction(meth):
        return getattr(inspect.getmodule(meth),
                       meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
    return None