from .app_settings import settings

def debug(request):
    ip = request.client_ip
    deb = settings.DEBUG or ip in settings.INTERNAL_IPS
    return {'debug': deb}


def show_ad(request):
    ip = request.client_ip
    deb = settings.DEBUG or ip in settings.INTERNAL_IPS
    user = request.user
    return {'show_ad': user.is_regular and not deb }


def base_template(request):
    return {'base_template': settings.BASE_TEMPLATE}