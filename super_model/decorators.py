from django.http.response import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy


def login_required(url_name='login'):
    def login_required_inner(dispatch):
        def wrapper(self, request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated():
                return HttpResponseRedirect(reverse_lazy(url_name))
            else:
                return dispatch(self, request, *args, **kwargs)
        return wrapper
    return login_required_inner