from django.conf import settings
from . import models
from super_model import views as super_views
from . import forms
from cache.decorators import cached_view
from super_model import models as super_models
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from super_model import forms as super_forms
from django.http import JsonResponse
from haystack.generic_views import SearchView as OriginalSearchView
from haystack.query import SearchQuerySet
from super_model import helper as super_helper
from django.db.models.aggregates import Count
from django.utils import timezone
from django.http.response import HttpResponseRedirect
from django.db.models import Case, Value, When, CharField


class PostViewMixin(super_views.SuperPostViewMixin):
    def set_model(self):
        if self.kwargs['post_type'] == 'plant':
            self.model =  models.Plant
        elif self.kwargs['post_type'] == 'recipe':
            self.model = models.Recipe
        elif self.kwargs['post_type'] == 'usage_area':
            self.model = models.UsageArea


class PostListFilterMixin(super_views.SuperPostListFilterMixin, PostViewMixin):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.model == models.Plant:
            context['post_type'] = 'plant'
        elif self.model == models.Recipe:
            context['post_type'] = 'recipe'

        context['list_view_default_template'] = 'main/post/_post_list_content.html'
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
        elif self.model == models.UsageArea:
            return forms.UsageAreaForm


class PostCreate(PostCreateUpdateMixin, generic.CreateView):
    template_name ='main/post/post_create.html'


class PostUpdate(PostCreateUpdateMixin, generic.UpdateView):
    template_name ='main/post/post_create.html'


class PostDetail(super_views.SuperPostDetail):
    template_name = 'main/post/post_detail.html'
    comment_form = forms.CommentForm
    comment_options_form = forms.CommentOptionsForm

    @cached_view(test=super_models.request_with_empty_guest)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



class CommentGetForAnswerToBlockAjax(generic.TemplateView):
    template_name = 'main/comment/_comment_for_answer_block.html'

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.request.POST['pk']
        context['comment'] = models.Comment.objects.get(pk=pk)
        return context

    def post(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))



class SearchView(OriginalSearchView):
    queryset = SearchQuerySet().all()
    form_class = super_forms.SuperSearchForm

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by('weight')
        return queryset


class AutocompleteView(generic.View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        q = request.POST.get('q', '').strip()

        if len(q) > 2:
            queryset = models.Post.objects.get_available().filter(title__icontains=q).annotate(
                comment_count=Count('comments')).order_by('-comment_count')[:5]
            suggestions = [post.title for post in queryset]
        else:
            suggestions = []
        data = {
            'results': suggestions
        }
        return JsonResponse(data)

class CommentGetTreeAjax(super_views.SuperCommentGetTreeAjax):
    template_name = 'main/widgets/_get_child_comments.html'


class CommentUpdate(generic.UpdateView):
    model = models.Comment
    form_class = forms.CommentUpdateForm
    template_name = 'main/comment/update.html'

    def post(self, request, *args, **kwargs):
        user = request.user
        pk = kwargs['pk']
        comment = self.model.objects.get(pk=pk)
        if not user == comment.user:
            return HttpResponseRedirect(comment.get_absolute_url())
        form = self.form_class(request.POST, instance=comment)
        form.instance.updater = request.user
        form.instance.session_key = super_helper.set_and_get_session_key(request.session)
        comment = form.save()
        return HttpResponseRedirect(comment.get_absolute_url())
