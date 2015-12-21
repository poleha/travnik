from django.conf import settings as project_settings
from django.utils.module_loading import import_string


class Settings:
    EMPTY_CACHE_PLACEHOLDER = '__EMPTY__'

    CACHED_VIEW_PARTIAL_TEMPLATE_PREFIX = "_cached_view-{0}-{1}"

    CACHED_VIEW_TEMLPATE_PREFIX = CACHED_VIEW_PARTIAL_TEMPLATE_PREFIX + "-{2}"

    CACHED_PROPERTY_KEY_TEMPLATE = '_cached_{0}-{1}-{2}'

    CACHED_METHOD_KEY_TEMPLATE = '_cached_method_{0}_{1}_{2}'

    CACHED_METHOD_KEY_FULL_TEMPLATE = CACHED_METHOD_KEY_TEMPLATE + '_{3}'

    CONDITIONAL_CACHE_KEY_TEMPLATE = '__conditional_cache__{0}'

    CACHED_VIEW_DURATION = 60 * 60 * 24 * 7

    CACHED_PROPERTY_DURATION = 60 * 60 * 24 * 7

    CACHED_METHOD_DURATION = 60 * 60

    CACHE_ENABLED = True

    CACHED_METHOD_SPECIAL_CASES = {}

    CACHED_VIEW_VARY_ON_REQUEST_PARAMS = ('flavour', )

    def __init__(self):
        result_special_cases = {}
        special_cases = self.CACHED_METHOD_SPECIAL_CASES
        special_cases_from_settings = getattr(project_settings, 'CACHED_METHOD_SPECIAL_CASES', {})
        special_cases.update(special_cases_from_settings)
        for path, val in special_cases.items():
            klass = import_string(path)
            result_special_cases[klass] = val
        self.special_cases = result_special_cases

    def __getattribute__(self, item):
        if hasattr(project_settings, item):
            return getattr(project_settings, item)
        else:
            return super().__getattribute__(item)


settings = Settings()