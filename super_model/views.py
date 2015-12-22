from django.http.response import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from . import helper
from django.utils.module_loading import import_string
from .app_settings import settings
from super_model import models
from allauth.account.models import EmailAddress
from django.http import JsonResponse, HttpResponse
from allauth.account.forms import LoginForm
from . import forms
from allauth.account.views import SignupView, LoginView, LogoutView, PasswordChangeView, PasswordResetView, PasswordResetDoneView, PasswordResetFromKeyView, PasswordResetFromKeyDoneView, ConfirmEmailView, EmailView
from allauth.socialaccount.views import SignupView as SocialSignupView, LoginCancelledView, LoginErrorView, ConnectionsView
from .decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.contrib import messages

Comment = import_string(settings.BASE_COMMENT_CLASS)
History = import_string(settings.BASE_HISTORY_CLASS)
Post = import_string(settings.BASE_POST_CLASS)


def restrict_by_role_mixin(*roles):
    class RoleOnlyMixin:
        def dispatch(self, request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated():
                return HttpResponseRedirect(reverse_lazy('login'))
            elif not user.user_profile.role in roles:
                return HttpResponseRedirect(reverse_lazy('main-page'))
            return super().dispatch(request, *args, **kwargs)
    return RoleOnlyMixin



class HistoryAjaxSave(generic.View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        pk = request.POST.get('pk', None)
        action = request.POST.get('action', None)

        if not pk or not action:
            data = {'saved': False}
            return JsonResponse(data)

        ip = request.client_ip
        user = request.user
        session_key = helper.set_and_get_session_key(request.session)

        if action == 'comment-mark':
            comment = Comment.objects.get(pk=pk)
            h = History.save_history(history_type=models.HISTORY_TYPE_COMMENT_RATED, post=comment.post, user=request.user, comment=comment, ip=ip, session_key=session_key)
            data = {'mark': comment.comment_mark}
            if h:
                data['saved'] = True
            else:
                data['saved'] = False
            return JsonResponse(data)
        elif action == 'comment-unmark':
            comment = Comment.objects.get(pk=pk)
            if request.user.is_authenticated():
                hs = History.objects.filter(history_type=models.HISTORY_TYPE_COMMENT_RATED, user=request.user, comment=comment, deleted=False)
            else:
                hs = History.objects.filter(history_type=models.HISTORY_TYPE_COMMENT_RATED, comment=comment, user=None, session_key=session_key, deleted=False)
                #if session_key:
                #    h = h.filter(Q(session_key=session_key)|Q(ip=ip))
                #else:
                #    h = h.filter(ip=ip)
            data = {}
            if hs.exists():
                for h in hs:
                    h.deleted = True
                    h.save()
                data['saved'] = True
            else:
                data['saved'] = False
            data['mark'] = comment.comment_mark
            return JsonResponse(data)
        elif action == 'comment-complain':
            comment = Comment.objects.get(pk=pk)
            h = History.save_history(history_type=models.HISTORY_TYPE_COMMENT_COMPLAINT, post=comment.post, user=request.user, comment=comment, ip=ip, session_key=session_key)
            data = {'mark': comment.complain_count}
            if h:
                data['saved'] = True
            else:
                data['saved'] = False
            return JsonResponse(data)
        elif action == 'comment-uncomplain':
            comment = Comment.objects.get(pk=pk)
            if request.user.is_authenticated():
                hs = History.objects.filter(history_type=models.HISTORY_TYPE_COMMENT_COMPLAINT, user=request.user, comment=comment, deleted=False)
            else:
                hs = History.objects.filter(history_type=models.HISTORY_TYPE_COMMENT_COMPLAINT, comment=comment, user=None, session_key=session_key, deleted=False)
            data = {}
            if hs.exists():
                for h in hs:
                    h.deleted = True
                    h.save()
                data['saved'] = True
            else:
                data['saved'] = False
            data['mark'] = comment.complain_count
            return JsonResponse(data)

        elif action == 'post-mark':
            mark = request.POST.get('mark', None)
            post = Post.objects.get(pk=pk)
            h = History.save_history(history_type=models.HISTORY_TYPE_POST_RATED, post=post, user=request.user, mark=mark, ip=ip, session_key=session_key)
            data = {}
            if h:
                data['saved'] = True
            else:
                data['saved'] = False
            data['average_mark'] = post.obj.average_mark,
            data['marks_count'] = post.obj.marks_count
            data['mark'] = post.get_mark_by_request(request)
            return JsonResponse(data)

        elif action == 'post-unmark':
            post = Post.objects.get(pk=pk)
            if request.user.is_authenticated():
                hs = History.objects.filter(user=user, history_type=models.HISTORY_TYPE_POST_RATED, post=post, deleted=False)
            else:
                hs = History.objects.filter(session_key=session_key, history_type=models.HISTORY_TYPE_POST_RATED, post=post, user=None, deleted=False)
            data = {}
            if hs.exists():
                for h in hs:
                    h.deleted = True
                    h.save()
                data['saved'] = True
            else:
                data['saved'] = False
            data['average_mark'] = post.obj.average_mark,
            data['marks_count'] = post.obj.marks_count
            data['mark'] = 0
            return JsonResponse(data)

        elif action == 'comment-delete':
            if not user.is_regular:
                comment = Comment.objects.get(pk=pk)
                if not comment.delete_mark:
                    comment.delete_mark = True
                    if not comment.session_key:
                        comment.session_key = session_key
                    comment.save()
                    return JsonResponse({'saved': True})
            return JsonResponse({'saved': False})

        elif action == 'comment-undelete':
            if not user.is_regular:
                comment = Comment.objects.get(pk=pk)
                if comment.delete_mark:
                    comment.delete_mark = False
                    comment.save()
                    return JsonResponse({'saved': True})
            return JsonResponse({'saved': False})


class SuperListView(generic.ListView):
    pages_to_show = settings.PAGES_TO_SHOW_FOR_LIST_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_page = context['page_obj'].number
        total_pages = context['paginator'].num_pages
        page_range = context['paginator'].page_range
        if total_pages <= self.pages_to_show:
            short_page_range = page_range
        else:
            i = j = current_page
            short_page_range = [current_page]
            while len(short_page_range) < self.pages_to_show:
                i += 1
                j -= 1
                if i in page_range:
                    short_page_range.append(i)
                if j in page_range:
                    short_page_range.append(j)
            #_short_page_range = [i for i in range(current_page - self.pages_to_show + 1, current_page + self.pages_to_show + 1) if i > 0]
            #for i in _short_page_range:
            short_page_range = sorted(short_page_range)
        context['short_page_range'] = short_page_range
        if not 1 in short_page_range:
            context['show_first_page'] = True
        if not total_pages in short_page_range:
            context['show_last_page'] = True

        return context

class SuperPostViewMixin(generic.View):
    def set_model(self):
        raise NotImplementedError


    def dispatch(self, request, *args, **kwargs):
        self.set_model()
        return super().dispatch(request, args, **kwargs)


class SuperPostListFilterMixin(SuperListView):
    context_object_name = 'objs'
    paginate_by = settings.POST_LIST_PAGE_SIZE

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        filter_form = self.get_filter_form()
        if filter_form:
            filter_form.full_clean()
            flt = {}
            for field_name, field_value in filter_form.cleaned_data.items():
            #usage_areas = drug_filter_form.cleaned_data['usage_areas']
                if len(field_value) > 0: #не exists() поскольку может быть list для component_type
                    #TODO Переделать на custom lookup
                    if field_name == 'alphabet':
                        ids = ()
                        for letter in field_value:
                            cur_ids = self.model.objects.filter(title__istartswith=letter).values_list('id', flat=True)
                            ids += tuple(cur_ids)
                        flt['id__in'] = ids
                    elif isinstance(field_value, str):
                        flt[field_name + '__icontains'] = field_value
                    else:
                        flt[field_name + '__in'] = field_value
            queryset = queryset.filter(**flt)
        return queryset

    def get_filter_form(self):
        raise NotImplementedError


class CommentConfirm(generic.TemplateView):
    template_name = 'super_model/comment/confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            comment_pk = kwargs['comment_pk']
            key = kwargs['key']
            comment = Comment.objects.get(pk=comment_pk, key=key)
            if comment.confirmed == False:
                comment.confirmed = True
                comment.save()
                context['saved'] = True

                if comment.user and not comment.user.email_confirmed:
                    email = EmailAddress.objects.get(user=comment.user, verified=False, email=comment.user.email)
                    email.verified = True
                    email.save()

            else:
                context['not_saved'] = True

        except:
            context['not_found'] = True
        return context


class CommentGetConfirmFormAjax(generic.TemplateView):
    template_name = 'super_model/comment/_get_confirm_form.html'
    confirmation_message = 'Отзыв подтвержден'
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.request.POST['pk']
        comment = Comment.objects.get(pk=pk)
        form = forms.CommentConfirmForm(initial={'comment': comment})
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        pk = self.request.POST['pk']
        comment = Comment.objects.get(pk=pk)
        if user.is_authenticated():
            try:
                email = EmailAddress.objects.get(user=user)
            except:
                email= None
            if email and email.verified and user.email == comment.email:
                comment.confirmed = True
                comment.save()
                return HttpResponse(self.confirmation_message)

        return self.render_to_response(self.get_context_data(**kwargs))


class CommentDoConfirmAjax(generic.TemplateView):
    template_name = 'super_model/comment/_get_confirm_form.html'
    confirmation_message = 'Отзыв подтвержден'

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        form = forms.CommentConfirmForm(request.POST)
        if form.is_valid():
            comment = form.cleaned_data['comment']

            if user.is_authenticated():
                try:
                    email = EmailAddress.objects.get(user=user)
                except:
                    email= None
                if email and email.verified and user.email == comment.email:
                    comment.confirmed = True
                    comment.save()
                    return HttpResponse(self.confirmation_message)
            email = form.cleaned_data['email']
            if comment.email == email:
                comment.send_confirmation_mail(request=request)
                return HttpResponse('На Ваш адрес электронной почту отправлено сообщение с дальнейшими инструкциями')
            else:
                form.add_error('email', 'Адрес электронной почты указан неверно')
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class GetAjaxLoginFormView(generic.TemplateView):
    template_name = 'super_model/user/_ajax_login.html'

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LoginForm()
        return context


    def post(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))


class AjaxLoginView(LoginView):
    template_name = 'super_model/user/_ajax_login.html'


class SuperSignupView(SignupView):
    template_name = 'super_model/user/signup.html'
    form_class = forms.SuperSignupForm

class SuperLoginView(LoginView):
    template_name = 'super_model/user/login.html'

class SuperLogoutView(LogoutView):
    pass

class SuperPasswordChangeView(PasswordChangeView):
    template_name = 'super_model/user/password_change.html'
    success_url = reverse_lazy("user-profile")

class SuperPasswordResetView(PasswordResetView):
    template_name = 'super_model/user/password_reset.html'
    success_url = reverse_lazy("password-reset-done")

class SuperPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'super_model/user/password_reset_done.html'

class SuperPasswordResetFromKeyView(PasswordResetFromKeyView):
    template_name = 'super_model/user/password_reset_from_key.html'
    success_url = reverse_lazy('password-reset-from-key-done')


class SuperPasswordResetFromKeyDoneView(PasswordResetFromKeyDoneView):
    template_name = 'super_model/user/password_reset_from_key_done.html'


class SuperSocialSignupView(SocialSignupView):
    template_name = 'super_model/user/social/signup.html'

class SuperLoginCancelledView(LoginCancelledView):
    template_name = 'super_model/user/social/login_cancelled.html'

class SuperLoginErrorView(LoginErrorView):
    template_name = 'super_model/user/social/authentication_error.html'

class SuperConnectionsView(ConnectionsView):
    template_name = 'super_model/user/social/connections.html'

    @login_required()
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class SuperEmailView(EmailView):
    template_name = 'super_model/user/email.html'


class SuperConfirmEmailView(ConfirmEmailView):
    def get_template_names(self):
        if self.request.method == 'POST':
            return ["main/user/email_confirmed.html"]
        else:
            return ["main/user/email_confirm.html"]


class SuperPostDetail(SuperListView):
    context_object_name = 'comments'
    paginate_by = settings.POST_COMMENTS_PAGE_SIZE
    template_name = 'super_model/post/post_detail.html'
    comment_form = forms.SuperCommentForm
    comment_options_form = forms.SuperCommentOptionsForm

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        request = self.request
        try:
            show_type = int(request.GET.get('show_type', forms.COMMENTS_SHOW_TYPE_PLAIN))
        except:
            show_type = forms.COMMENTS_SHOW_TYPE_PLAIN
        try:
            order_by_created = int(request.GET.get('order_by_created', forms.COMMENTS_ORDER_BY_CREATED_DEC))
        except:
            order_by_created = forms.COMMENTS_ORDER_BY_CREATED_DEC

        if show_type == forms.COMMENTS_SHOW_TYPE_TREE:
            comments = self.post.obj.comments.get_available().filter(parent=None)
        else:
            comments = self.post.obj.comments.get_available()
        if order_by_created == forms.COMMENTS_ORDER_BY_CREATED_DEC:
            comments = comments.order_by('-created')
        else:
            comments = comments.order_by('created')

        return comments


    def get(self, request, *args, **kwargs):
        self.set_obj()
        self.set_comment_page()
        res = super().get(request, *args, **kwargs)
        last_modified = self.obj.last_modified
        if last_modified:
            last_modified = helper.convert_date_for_last_modified(last_modified)
            expires = timezone.now() + timezone.timedelta(seconds=settings.CACHED_VIEW_DURATION)
            res['Last-Modified'] = last_modified
            res['Expires'] = helper.convert_date_for_last_modified(expires)
        return res

    @staticmethod
    def get_post(kwargs):
        if 'alias' in kwargs:
            alias = kwargs['alias']
            post = get_object_or_404(Post, alias=alias)
        else:
            pk = kwargs['pk']
            post = get_object_or_404(Post, pk=pk)
        return post

    def set_obj(self):
        post = self.get_post(self.kwargs)
        self.post = post
        self.obj = post.obj

    def set_comment_page(self):
        if self.kwargs['action'] == 'comment':
            try:
                comment = Comment.objects.get(pk=self.kwargs['comment_pk'])
                self.kwargs[self.page_kwarg] = comment.page
            except ObjectDoesNotExist:
                pass

    def get_context_data(self, comment_form=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        request = self.request
        try:
            show_type = int(request.GET.get('show_type', forms.COMMENTS_SHOW_TYPE_PLAIN))
        except:
            show_type = forms.COMMENTS_SHOW_TYPE_PLAIN

        if show_type == forms.COMMENTS_SHOW_TYPE_TREE:
            context['show_tree'] = True

        else:
            context['show_tree'] = False

        context['obj'] = self.obj

        if comment_form is None:
            comment_form = self.comment_form(request=self.request, post=self.post)
        context['comment_form'] = comment_form
        comments_options_form = self.comment_options_form(self.request.GET)
        context['comments_options_form'] = comments_options_form
        context['mark'] = self.post.obj.get_mark_by_request(request)

        if self.obj.can_be_rated:
            user_mark = self.obj.get_mark_by_request(request)
            if user_mark == 0:
                context['can_mark_blog'] = True
            else:
                context['can_mark_blog'] = False


        #visibility
        if context['mark']:
            if user.is_authenticated():
                hist_exists = History.objects.filter(history_type=models.HISTORY_TYPE_POST_RATED, user=user, post=self.post, deleted=False).exists()
            else:
                hist_exists = History.objects.filter(history_type=models.HISTORY_TYPE_POST_RATED, session_key=getattr(request.session, settings.SUPER_MODEL_KEY_NAME), post=self.post, deleted=False).exists()
            if hist_exists:
                show_your_mark_block_cls = ''
                show_make_mark_block_cls = 'hidden'
            else:
                show_your_mark_block_cls = 'hidden'
                show_make_mark_block_cls = ''
        else:
            show_your_mark_block_cls = 'hidden'
            show_make_mark_block_cls = ''
        context['show_your_mark_block_cls'] = show_your_mark_block_cls
        context['show_make_mark_block_cls'] = show_make_mark_block_cls
        return context

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        user = request.user
        self.set_obj()
        self.object_list = self.get_queryset()
        comment_form = self.comment_form(request.POST, request=request, post=self.post)
        comment_form.instance.post = self.post
        comment_form.instance.ip = request.client_ip
        comment_form.instance.session_key = helper.set_and_get_session_key(request.session)
        if user.is_authenticated() and not comment_form.instance.user:
            comment_form.instance.user = user

        if comment_form.is_valid():
            comment_form.instance.status = comment_form.instance.get_status()
            comment = comment_form.save()
            published = comment.status == models.COMMENT_STATUS_PUBLISHED

            if not published:
                messages.add_message(request, messages.INFO, 'Ваш отзыв будет опубликован после проверки модератором')
            comment.send_confirmation_mail(request=request)

            #models.History.save_history(history_type=models.HISTORY_TYPE_COMMENT_CREATED, post=self.post, user=request.user, ip=request.client_ip, comment=comment)
            if request.is_ajax():
                return JsonResponse({'href': comment.get_absolute_url(), 'status': 1, 'published': published})
            else:
                return HttpResponseRedirect(self.obj.get_absolute_url())
        else:
            if request.is_ajax():
                return JsonResponse({'comment_form': comment_form.as_p(), 'status': 2})
            else:
                return self.render_to_response(self.get_context_data(comment_form=comment_form, **kwargs))