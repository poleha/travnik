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


class PostDetail(super_views.SuperPostDetail):
    template_name = 'main/post/post_detail.html'
    comment_form = forms.CommentForm
    comment_options_form = forms.CommentOptionsForm

    @cached_view(test=super_models.request_with_empty_guest)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MainPageView(generic.TemplateView):
    template_name = 'main/base/main.html'

    @cached_view(timeout=60 * 60, test=super_models.request_with_empty_guest)
    def dispatch(self, request, *args, **kwargs):
        res = super().dispatch(request, *args, **kwargs)
        try:
            last_modified = models.History.objects.filter(history_type=super_models.HISTORY_TYPE_COMMENT_CREATED, deleted=False).latest('created').created
            res['Last-Modified'] = super_helper.convert_date_for_last_modified(last_modified)
            res['Expires'] = super_helper.convert_date_for_last_modified(last_modified + timezone.timedelta(seconds=60 * 60))
        except:
            pass

        return res

    def get_popular_plants(self):
        plants = models.Plant.objects.get_available().annotate(comment_count=Count('comments')).order_by('-comment_count')[:16]
        return plants

    def get_recent_recipes(self):
        recipes = models.Recipe.objects.get_available().order_by('-created')[:4]
        return recipes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['popular_plants'] = self.get_popular_plants()
        recent_recipes = self.get_recent_recipes()
        if recent_recipes.exists():
            context['recent_recipes'] = recent_recipes[1:4]
            context['main_recent_recipe'] = recent_recipes[0]
        return context



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

        suggestions = []
        data = {
            'results': suggestions
        }
        return JsonResponse(data)

class CommentGetTreeAjax(super_views.SuperCommentGetTreeAjax):
    template_name = 'main/widgets/_get_child_comments.html'