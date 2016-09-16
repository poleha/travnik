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
from django.http.response import HttpResponseRedirect
from django.db.models import Q
from django.db import transaction
from super_model.helper import set_and_get_session_key
from django.core.urlresolvers import reverse_lazy


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

        context['list_view_default_template'] = 'main/post/_plant_list_content.html'
        return context

    def get_filter_form(self):
        if self.request.method.lower() == 'post':
            data = self.request.POST
        else:
            data = self.request.GET
        if self.model == models.Plant:
            if not hasattr(self, '_plant_filter_form'):
                self._post_filter_form = forms.PlantFilterForm(data)
            return self._post_filter_form
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
    template_name = 'main/post/_plant_list_ajax.html'

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(**kwargs))


class PostCreateUpdateMixin(PostViewMixin):
    def get_form_class(self):
        if self.model == models.Plant:
            return forms.PlantForm
        elif self.model == models.Recipe:
            user = self.request.user
            if user.is_regular:
                return forms.RecipeUserUpdateForm
            else:
                return forms.RecipeForm
        elif self.model == models.UsageArea:
            return forms.UsageAreaForm


class PostCreate(super_views.restrict_by_role_mixin(settings.USER_ROLE_ADMIN), PostCreateUpdateMixin, generic.CreateView):
    template_name ='main/post/post_create.html'


class PostUpdate(super_views.restrict_by_role_mixin(settings.USER_ROLE_ADMIN), PostCreateUpdateMixin, generic.UpdateView):
    template_name ='main/post/post_create.html'

class RecipeUserUpdate(PostCreateUpdateMixin, generic.UpdateView):
    template_name ='main/post/post_create.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user == request.user and self.object.is_project:
            return super().get(request, *args, **kwargs)
        elif request.user.is_authenticated():
            return HttpResponseRedirect(self.object.get_absolute_url())
        else:
            return HttpResponseRedirect(reverse_lazy('login'))


class PostDetail(super_views.SuperPostDetail):
    template_name = 'main/post/post_detail.html'
    comment_form = forms.CommentForm
    comment_options_form = forms.CommentOptionsForm

    @cached_view(test=super_models.request_with_empty_guest, model_class=models.Post, kwarg='alias')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, recipe_form=None, **kwargs):
        context = super().get_context_data(**kwargs)
        if recipe_form is None:
            recipe_form = forms.RecipeUserForm(plant=self.obj)
        context['recipe_form'] = recipe_form
        return context


class RecipeCreateFromPostDetail(PostDetail):
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            HttpResponseRedirect(self.obj.get_absolute_url())
        self.set_obj()
        self.object_list = self.get_queryset()
        recipe_form = forms.RecipeUserForm(request.POST, plant=self.obj)
        if recipe_form.is_valid():
            ip = request.client_ip
            session_key = set_and_get_session_key(request.session)
            recipe_form.instance.user = user
            if user.user_profile.can_publish_comment:
                recipe_form.instance.status = super_models.POST_STATUS_PUBLISHED
            recipe = recipe_form.save()

            h = models.History.objects.get(post=recipe, history_type=super_models.HISTORY_TYPE_POST_CREATED)
            h.ip = ip
            h.session_key = session_key
            h.user = user
            h.save()

            recipe.plants.add(self.obj)
            for plant in recipe.plants.all():
                models.History.save_history(history_type=super_models.HISTORY_TYPE_POST_SAVED, post=plant, user=user, ip=ip, session_key=session_key)
                plant.full_invalidate_cache()
            return JsonResponse({
                    'status': 1,
                    'published': recipe.status == super_models.POST_STATUS_PUBLISHED,
                    'href': recipe.get_absolute_url()
                })
        else:
            return JsonResponse({'recipe_form': recipe_form.as_p(), 'status': 2})
            #return self.render_to_response(self.get_context_data(recipe_form=recipe_form))


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
        #queryset = queryset.order_by('weight')
        return queryset


class AutocompleteView(generic.View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        q = request.POST.get('q', '').strip()

        if len(q) > 2:
            post_queryset = models.Post.objects.get_available().filter(
                Q(~Q(plant=None) | ~Q(recipe=None)),
                title__icontains=q).annotate(comment_count=Count('comments')).order_by('-comment_count')[:5]
            objects = [post.obj for post in post_queryset]
            post_suggestions = [obj.title for obj in objects]

            synonym_queryset = models.Synonym.objects.exclude(synonym__in=post_suggestions).filter(synonym__icontains=q).annotate(
                comment_count=Count('plant__comments')).order_by('-comment_count')[:5]
            synonym_suggestions = [synonym.synonym for synonym in synonym_queryset if synonym.plant not in objects]
            suggestions = post_suggestions + synonym_suggestions
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


class UserRecipesView(super_views.SuperListView):
    template_name = 'user/user_recipes.html'
    context_object_name = 'recipes'
    paginate_by = 50

    @cached_view(timeout= 60 * 60 * 24, test=super_models.request_with_empty_guest)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        pk = self.kwargs['pk']
        user = models.User.objects.get(pk=pk)
        recipes = models.Recipe.objects.filter(user=user)
        if not self.request.user == user:
            recipes = recipes.get_available()
        return recipes


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        user = models.User.objects.get(pk=pk)
        context['current_user'] = user
        return context

class MissionView(generic.TemplateView):
    template_name = 'main/static/mission.html'