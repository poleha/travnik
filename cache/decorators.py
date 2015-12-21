from .app_settings import settings
from django.core.cache import cache
from .helper import make_key_from_args, get_class_path, rec_getattr, get_class_that_defined_method


class CachedProperty(property):
    pass


def cached_property(func):
    @CachedProperty
    def wrapper(self):
        if settings.CACHE_ENABLED:
            key = settings.CACHED_PROPERTY_KEY_TEMPLATE.format(get_class_path(type(self)), func.__name__, self.pk)
            res = cache.get(key)
            if res is None:
                res = func(self)
                if res is None:
                    res = settings.EMPTY_CACHE_PLACEHOLDER
                cache.set(key, res, settings.CACHED_PROPERTY_DURATION)
            if res == settings.EMPTY_CACHE_PLACEHOLDER:
                res = None
            return res
        else:
            return func(self)
    return wrapper


def cached_method(timeout=settings.CACHED_METHOD_DURATION):
    def _cached_method(func):
        def wrapper(self, *args, **kwargs):
            if settings.CACHE_ENABLED:
                key = settings.CACHED_METHOD_KEY_FULL_TEMPLATE.format(get_class_path(type(self)), func.__name__, self.pk, make_key_from_args(args, kwargs))
                res = cache.get(key)
                if res is None:
                    res = func.__get__(self)(*args, **kwargs)
                    if res is None:
                        res = settings.EMPTY_CACHE_PLACEHOLDER
                    cache.set(key, res, timeout)
                if res == settings.EMPTY_CACHE_PLACEHOLDER:
                    res = None
                return res
            else:
                return func.__get__(self)(*args, **kwargs)
        wrapper.__is_cached_method__ = True
        return wrapper
    return _cached_method


def cached_view(timeout=settings.CACHED_VIEW_DURATION, test=lambda request: True):
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            if settings.CACHE_ENABLED and test(request):
                url = request.build_absolute_uri()
                cls = get_class_that_defined_method(func)
                params = ''
                for param in settings.CACHED_VIEW_VARY_ON_REQUEST_PARAMS:
                    params += '__{0}_{1}'.format(param, rec_getattr(request, param))
                prefix = settings.CACHED_VIEW_TEMLPATE_PREFIX.format(get_class_path(cls), func.__name__, params)
                key = "{0}-{1}".format(prefix, url)
                res = cache.get(key)
                if res is None:
                    res = func(self, request, *args, **kwargs)
                    if hasattr(res, 'render'):
                        res.render()
                    cache.set(key, res, timeout)
            else:
                res = func(self, request, *args, **kwargs)
            return res
        return wrapper
    return decorator
