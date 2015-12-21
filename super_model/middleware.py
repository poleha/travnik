from .helper import set_and_get_session_key
from .app_settings import settings
from django.middleware.cache import UpdateCacheMiddleware, FetchFromCacheMiddleware
from . import models


class SetClientIpMiddleware:
    def process_request(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        request.client_ip = ip


class SetUserKeyMiddleware:
    def process_request(self, request):
        key = request.session.get(settings.SUPER_MODEL_KEY_NAME, None)
        if key is None and request.user.is_authenticated():
            key = set_and_get_session_key(request.session)
        setattr(request.session, settings.SUPER_MODEL_KEY_NAME, key)


class SuperUpdateCacheMiddleware(UpdateCacheMiddleware):
    def _should_update_cache(self, request, response):
        if not settings.CACHE_ENABLED:
            return False
        if models.request_with_empty_guest(request):
            return super()._should_update_cache(request, response)
        else:
            return False


class SuperFetchFromCacheMiddleware(FetchFromCacheMiddleware):
    def process_request(self, request):
        if not settings.CACHE_ENABLED:
            request._cache_update_cache = False
            return None
        if models.request_with_empty_guest(request):
            return super().process_request(request)
        else:
            request._cache_update_cache = False
            return None
