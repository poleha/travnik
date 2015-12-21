from django.core.cache import cache
from django.conf import settings


def set_conditional_cache(key, value, condition, expires=None):
    condition_key = settings.CONDITIONAL_CACHE_KEY_TEMPLATE.format(key)
    cache.set(condition_key, condition, expires)
    cache.set(key, value, expires)


def get_conditional_cache(key, condition):
    condition_key = settings.CONDITIONAL_CACHE_KEY_TEMPLATE.format(key)
    stored_condition = cache.get(condition_key)
    if not stored_condition == condition:
        cache.delete_many([key, condition_key])
    return cache.get(key)
