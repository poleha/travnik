from django.conf import settings
from . import models
from super_model import views as super_views
from . import forms
from cache.decorators import cached_view
from super_model import models as super_models
from super_model import forms as super_forms
from django.views import generic
from allauth.account.views import SignupView, LoginView, LogoutView, PasswordChangeView, PasswordResetView, PasswordResetDoneView, PasswordResetFromKeyView, PasswordResetFromKeyDoneView, ConfirmEmailView, EmailView


class PostViewMixin(super_views.SuperPostViewMixin):
    def set_model(self):
        if self.kwargs['post_type'] == 'plant':
            self.model =  models.Plant
        elif self.kwargs['post_type'] == 'recipe':
            self.model = models.Recipe


class PostListFilterMixin(super_views.SuperPostListFilterMixin, PostViewMixin):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.model == models.Plant:
            context['post_type'] = 'plant'
        elif self.model == models.Recipe:
            context['post_type'] = 'recipe'

        context['list_view_default_template'] = 'main/post/_post_list_grid.html'
        return context

    def get_filter_form(self):
        if self.request.method.lower() == 'post':
            data = self.request.POST
        else:
            data = self.request.GET
        if self.model == models.Plant:
            if not hasattr(self, '_plant_filter_form'):
                self._drug_filter_form = forms.PlantFilterForm(data)
            return self._drug_filter_form
        elif self.model == models.Recipe:
            if not hasattr(self, '_recipe_filter_form'):
                self._cosmetics_filter_form = forms.RecipeFilterForm(data)
        else:
            return None


class PostList(PostListFilterMixin):
    template_name = 'main/post/post_list.html'

    @cached_view(timeout=60 * 60 * 12, test=super_models.request_with_empty_guest)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.get_filter_form()
        context['ajax_submit_url'] = self.model.ajax_submit_url()
        context['submit_url'] = self.model.submit_url()
        return context


class PostListAjax(PostListFilterMixin):
    template_name = 'main/post/_post_list_ajax.html'

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(**kwargs))


class PostCreateUpdateMixin(super_views.restrict_by_role_mixin(settings.USER_ROLE_ADMIN), PostViewMixin):
    def get_form_class(self):
        if self.model == models.Plant:
            return forms.PlantForm
        elif self.model == models.Recipe:
            return forms.RecipeForm


class PostCreate(PostCreateUpdateMixin, generic.CreateView):
    template_name ='main/post/post_create.html'


class PostUpdate(PostCreateUpdateMixin, generic.UpdateView):
    template_name ='main/post/post_create.html'

class ProzdoSignupView(SignupView):
    template_name = 'main/user/signup.html'
    form_class = super_forms.SuperSignupForm

class ProzdoLoginView(LoginView):
    template_name = 'main/user/login.html'
    #form_class = forms.ProzdoSignupForm


class ProzdoLogoutView(LogoutView):
    pass