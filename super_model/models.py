from django.db import models
from django.utils import timezone
from cache.models import CachedModelMixin
from mptt.models import MPTTModel, TreeForeignKey
from mptt.querysets import TreeQuerySet
from django.contrib.auth.models import User, AnonymousUser
from cache.decorators import cached_property, cached_method
from .app_settings import settings
from django.core.urlresolvers import reverse
from math import ceil
from helper import helper
from django.utils.html import strip_tags
import re
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from django.db.models import ImageField
from django.core.cache import cache
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from allauth.account.models import EmailAddress, EmailConfirmation
from django.db.models.signals import post_save
from super_model.helper import generate_key
from django.db.models.aggregates import Count, Sum


class SuperModel(models.Model):
    created = models.DateTimeField(blank=True, verbose_name='Время создания', db_index=True)
    updated = models.DateTimeField(blank=True, null=True, verbose_name='Время изменения', db_index=True)

    class Meta:
        abstract = True

    @property
    def saved_version(self):
        if self.pk:
            try:
                saved_version = type(self).objects.get(pk=self.pk)
            except:
                saved_version = None
        else:
            saved_version = None
        return saved_version

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            self.created = timezone.now()
        if self.pk:
            self.updated = timezone.now()
        super().save(*args, **kwargs)


def class_with_published_mixin(published_status):
    class PublishedModelMixin(models.Model):
        class Meta:
            abstract = True

        published = models.DateTimeField(null=True, blank=True, verbose_name='Время публикации', db_index=True)

        def save(self, *args, **kwargs):
            if self.status == published_status and not self.published:
                self.published = timezone.now()
            super().save(*args, **kwargs)

    return PublishedModelMixin


COMMENT_STATUS_PENDING_APPROVAL = 1
COMMENT_STATUS_PUBLISHED = 2

COMMENT_STATUSES = (
    (COMMENT_STATUS_PENDING_APPROVAL, 'На согласовании'),
    (COMMENT_STATUS_PUBLISHED, 'Опубликован'),
)


class CommentTreeQueryset(TreeQuerySet):
    def get_available(self):
        queryset = self.filter(status=COMMENT_STATUS_PUBLISHED)
        return queryset



class CommentManager(models.manager.BaseManager.from_queryset(CommentTreeQueryset)):
    use_for_related_fields = True



POST_MARKS_FOR_COMMENT = (
    (1, '1'),
    (1, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5'),
)


class SuperComment(SuperModel, CachedModelMixin, MPTTModel, class_with_published_mixin(COMMENT_STATUS_PUBLISHED)):
    class Meta:
        abstract = True

    username = models.CharField(max_length=256, verbose_name='Имя')
    email = models.EmailField(verbose_name='E-Mail')
    body = models.TextField(verbose_name='Сообщение')
    user = models.ForeignKey(User, null=True, blank=True, related_name='comments', db_index=True)
    ip = models.CharField(max_length=300, db_index=True)
    session_key = models.TextField(blank=True, null=True, db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    status = models.IntegerField(choices=COMMENT_STATUSES, verbose_name='Статус', db_index=True)
    updater = models.ForeignKey(User, null=True, blank=True, related_name='updated_comments')
    key = models.CharField(max_length=128, blank=True)
    confirmed = models.BooleanField(default=False, db_index=True)
    delete_mark = models.BooleanField(verbose_name='Пометка удаления', default=False, db_index=True)
    post_mark = models.IntegerField(choices=POST_MARKS_FOR_COMMENT, blank=True, null=True, verbose_name='Оценка')

    objects = CommentManager()

    txt_template_name = None
    html_template_name = None

    confirm_comment_text_template_name = None
    confirm_comment_html_template_name = None


    @cached_property
    def has_avaliable_children(self):
        return self.children.get_available().exists()

    @cached_property
    def comment_mark(self):
        History = import_string(settings.BASE_HISTORY_CLASS)
        try:
            mark = History.objects.filter(comment=self, history_type=HISTORY_TYPE_COMMENT_RATED, deleted=False).aggregate(Count('pk'))['pk__count']
            if mark is None:
                mark = 0
        except:
            mark = 0
        return mark

    @cached_property
    def complain_count(self):
        History = import_string(settings.BASE_HISTORY_CLASS)
        try:
            count = History.objects.filter(comment=self, history_type=HISTORY_TYPE_COMMENT_COMPLAINT, deleted=False).aggregate(Count('pk'))['pk__count']
            if count is None:
                count = 0
        except:
            count = 0
        return count

    @cached_method()
    def hist_exists_by_comment_and_user(self, history_type, user):
        History = import_string(settings.BASE_HISTORY_CLASS)
        return History.objects.filter(history_type=history_type, comment=self, user=user, deleted=False).exists()

    def hist_exists_by_request(self, history_type, request):
        History = import_string(settings.BASE_HISTORY_CLASS)
        if request_with_empty_guest(request):
            return False
        user = request.user
        if user and user.is_authenticated():
            hist_exists = self.hist_exists_by_comment_and_user(history_type, user)
        else:
            session_key = getattr(request.session, settings.SUPER_MODEL_KEY_NAME, None)
            if session_key is None:
                return False
            hist_exists = History.exists_by_comment(session_key, self, history_type)
        return hist_exists

    def show_do_action_button(self, history_type, request):
        if request_with_empty_guest(request):
            return True
        return not self.hist_exists_by_request(history_type, request) and not self.is_author_for_show_buttons(request)

    def show_undo_action_button(self, history_type, request):
        if request_with_empty_guest(request):
            return False
        return self.hist_exists_by_request(history_type, request) and not self.is_author_for_show_buttons(request)

    def is_author_for_show_buttons(self, request):
        if request_with_empty_guest(request):
            return False
        user = request.user
        if user and user.is_authenticated():
            return user == self.user
        else:
            session_key = getattr(request.session, settings.SUPER_MODEL_KEY_NAME, None)
            if session_key is None:
                return False
            else:
                return self.session_key == session_key


    def hist_exists_by_data(self, history_type, user=None, ip=None, session_key=None):
        History = import_string(settings.BASE_HISTORY_CLASS)
        if user and user.is_authenticated():
            hist_exists = History.objects.filter(history_type=history_type, comment=self, user=user, deleted=False).exists()
        elif not History.exists(session_key):
            return False
        else:
            if session_key:
                hist_exists_by_key = History.objects.filter(history_type=history_type, comment=self, session_key=session_key, deleted=False).exists()
            else:
                hist_exists_by_key = False
            if ip:
                hist_exists_by_ip = History.objects.filter(history_type=history_type, comment=self, ip=ip, deleted=False).exists()
            else:
                hist_exists_by_ip = False
            hist_exists = hist_exists_by_key or hist_exists_by_ip

        return hist_exists

    def can_do_action(self, history_type, user, ip, session_key):
        if user and not user.is_authenticated():
            return True
        return not self.hist_exists_by_data(history_type, user, ip, session_key) and not self.is_author_for_save_history(user, ip, session_key)


    @property
    def get_tree_level(self):
        if hasattr(self, 'tree_level'):
            return self.tree_level
        else:
            return 0

    def __str__(self):
        return self.short_body

    def type_str(self):
        return 'Сообщение'

    def get_confirm_url(self):
        return reverse('comment-confirm', kwargs={'comment_pk': self.pk, 'key': self.key})

    @property
    def consult_done(self):
        return self.available_children.filter(user__user_profile__role=settings.USER_ROLE_DOCTOR).exists()



    @property
    def update_url(self):
        return reverse('comment-update', kwargs={'pk': self.pk})


    @cached_property
    def get_children_tree(self):
        return self._get_children_tree()

    def _get_children_tree(self, cur=None, level=1):
        tree = []
        if cur is None:
            cur = self
        else:
            tree.append(cur)
        for child in cur.children.get_available().order_by('created'):
            child.tree_level = level
            tree += child._get_children_tree(child, level+1)
        return tree

    @property
    def page(self):
        comments = self.post.comments.get_available().order_by('-created')
        #count = comments.count()
        #pages_count = ceil(count / page_size)
        page_size = settings.POST_COMMENTS_PAGE_SIZE
        comments_tuple = tuple(comments)
        try:
            index = comments_tuple.index(self) + 1
            current_page = ceil(index / page_size)
        except:
            current_page = 1
        return current_page

    @cached_property
    def available_children(self):
        return self.get_descendants().filter(status=COMMENT_STATUS_PUBLISHED)

    @cached_property
    def available_children_count(self):
        return self.available_children.count()

    @cached_property
    def available_first_level_children(self):
        return type(self).objects.filter(parent=self)

    @property
    def short_body(self):
        return helper.cut_text(strip_tags(self.body))

    @cached_property
    def _cached_get_absolute_url(self):
        if self.status == COMMENT_STATUS_PUBLISHED:
            #return '{0}comment/{1}#c{1}'.format(self.post.get_absolute_url(), self.pk)
            return reverse('post-detail-pk-comment', kwargs={'pk': self.post.pk, 'comment_pk': self.pk}) + '#c' + str(self.pk)
        else:
            return self.post.get_absolute_url()

    def get_absolute_url(self):
        return self._cached_get_absolute_url

    def clean(self):
        if not self.pk:
                try:
                    comment = type(self).objects.filter(body=self.body, session_key=self.session_key, user=self.user, post=self.post).latest('created')
                except:
                    comment = None
                if comment:
                    delta = timezone.now() - comment.created
                    if delta.seconds < 180:
                        raise ValidationError('Повторный отзыв')

    def generate_key(self):
        if self.key:
            return self.key
        else:
            return generate_key(128)

    def get_status(self):
        if self.user and self.user.user_profile.can_publish_comment:
            return COMMENT_STATUS_PUBLISHED
        else:
            if (helper.comment_body_ok(self.body) and helper.comment_author_ok(self.username)) or self.email in (settings.AUTO_APPROVE_EMAILS + settings.AUTO_DONT_APPROVE_EMAILS):
                return COMMENT_STATUS_PUBLISHED
            else:
                return COMMENT_STATUS_PENDING_APPROVAL


    def delete(self, *args, **kwargs):
        post = self.post
        user = self.user
        ancestors = list(self.get_ancestors())
        descendants = list(self.get_descendants())
        super().delete(*args, **kwargs)
        if post:
            #invalidate_obj(post.obj)
            post.obj.full_invalidate_cache()
        if user:
            #invalidate_obj(user.user_profile)
            user.user_profile.full_invalidate_cache()
        for ancestor in ancestors:
            ancestor.full_invalidate_cache()
            #invalidate_obj(ancestor)
        for descendant in descendants:
            descendant.full_invalidate_cache()
            #invalidate_obj(descendant)


    def save(self, *args, **kwargs):
        History = import_string(settings.BASE_HISTORY_CLASS)
        saved_version = self.saved_version
        if not self.confirmed:
            if self.user and self.user.email_confirmed:
                self.confirmed = True
            elif self.email in settings.AUTO_APPROVE_EMAILS:
                self.confirmed = True

        if not self.key:
            self.key = self.generate_key()

        if not self.user or self.user.is_regular:
            self.body = strip_tags(self.body)
        super().save(*args, **kwargs)

        try:
            old_status = saved_version.status
        except:
            old_status = None

        if self.status == COMMENT_STATUS_PUBLISHED and old_status != self.status and self.parent and self.parent.confirmed and self.parent.user:
            self.send_answer_to_comment_message()
        History.save_history(history_type=HISTORY_TYPE_COMMENT_CREATED, post=self.post, comment=self, ip=self.ip, session_key=self.session_key, user=self.user)


    def send_answer_to_comment_message(self):
        Mail = import_string(settings.BASE_MAIL_CLASS)
        user = self.parent.user
        if user.user_profile.receive_messages and not self.user == self.parent.user and \
                        self.status == COMMENT_STATUS_PUBLISHED and \
                not Mail.objects.filter(mail_type=MAIL_TYPE_ANSWER_TO_COMMENT, entity_id=self.pk).exists():
            email_to = user.email

            email_sent = Mail.objects.filter(mail_type=MAIL_TYPE_ANSWER_TO_COMMENT,
                                                     entity_id=self.pk,
                                                     user=user).exists()
            if email_sent:
                return False


            text = render_to_string(self.txt_template_name, {'comment': self, 'site_url': settings.SITE_URL})
            html = render_to_string(self.html_template_name, {'comment': self, 'site_url': settings.SITE_URL})

            subject = 'Получен ответ на Ваш отзыв на {0}'.format(settings.SITE_NAME)
            from_email = settings.DEFAULT_FROM_EMAIL

            try:
                msg = EmailMultiAlternatives(subject, text, from_email, [email_to])
                msg.attach_alternative(html, "text/html")
                res = msg.send()
                if res:
                    Mail.objects.create(
                                mail_type=MAIL_TYPE_ANSWER_TO_COMMENT,
                                user=user if user.is_authenticated() else None,
                                subject=subject,
                                body_html=html,
                                body_text=text,
                                email=email_to,
                                ip=self.ip,
                                session_key=self.session_key,
                                entity_id=self.pk,
                                email_from=from_email,
                            )
                    return True

            except:
                pass


    def is_author_for_save_history(self, user=None, ip=None, session_key=None):
        if user and user.is_authenticated():
            return user == self.user
        else:
            return self.session_key == session_key or self.ip == ip

    def send_confirmation_mail(self, user=None, request=None):
        Mail = import_string(settings.BASE_MAIL_CLASS)
        to = self.email
        if to in (settings.AUTO_APPROVE_EMAILS + settings.AUTO_DONT_APPROVE_EMAILS):
            return
        if not user and request:
            user = request.user
        if request:
            ip = request.client_ip
            session_key = getattr(request.session, settings.SUPER_MODEL_KEY_NAME, None)
        else:
            ip = None
            session_key = None

        if not user.email_confirmed and not self.confirmed:
                html = render_to_string(self.confirm_comment_html_template_name, {'comment': self, 'site_url': settings.SITE_URL})
                text = render_to_string(self.confirm_comment_text_template_name, {'comment': self, 'site_url': settings.SITE_URL})
                subject = 'Вы оставили отзыв на {}'.format(settings.SITE_NAME)
                from_email = settings.DEFAULT_FROM_EMAIL
                try:
                    msg = EmailMultiAlternatives(subject, text, from_email, [to])
                    msg.attach_alternative(html, "text/html")
                    res = msg.send()
                    if res:
                        Mail.objects.create(
                            mail_type=MAIL_TYPE_COMMENT_CONFIRM,
                            user=user if user.is_authenticated() else None,
                            subject=subject,
                            body_html=html,
                            body_text=text,
                            email=to,
                            ip=ip,
                            session_key=session_key,
                            entity_id=self.pk,
                            email_from=from_email,
                        )
                except:
                    pass


class AbstractModel(SuperModel, CachedModelMixin):
    class Meta:
        abstract = True
        ordering = ('title', )
    title = models.CharField(max_length=500, verbose_name='Название', db_index=True)

    def __str__(self):
        return self.title

    def type_str(self):
        raise NotImplemented


POST_STATUS_PROJECT = 1
POST_STATUS_PUBLISHED = 2


POST_STATUSES = (
    (POST_STATUS_PROJECT, 'Проект'),
    (POST_STATUS_PUBLISHED, 'Опубликован'),
)


class PostQueryset(models.QuerySet):
    def get_available(self):
        queryset = self.filter(status=POST_STATUS_PUBLISHED)
        return queryset


class PostManager(models.manager.BaseManager.from_queryset(PostQueryset)):
    use_for_related_fields = True

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

class SuperPost(AbstractModel, class_with_published_mixin(POST_STATUS_PUBLISHED)):
    class Meta:
        abstract = True
    alias = models.CharField(max_length=800, blank=True, verbose_name='Синоним', db_index=True)
    status = models.IntegerField(choices=POST_STATUSES, verbose_name='Статус', default=POST_STATUS_PROJECT, db_index=True)
    post_type = models.IntegerField(choices=settings.POST_TYPES, verbose_name='Вид записи', db_index=True )

    can_be_rated = False

    objects = PostManager()


    def get_mark_by_request(self, request):
        History = import_string(settings.BASE_HISTORY_CLASS)
        user = request.user
        if user.is_authenticated():
            try:
                mark = History.objects.filter(user=user, history_type=HISTORY_TYPE_POST_RATED, post=self, deleted=False).count()
            except:
                mark = 0
        else:
            try:
                mark = History.objects.filter(post=self, history_type=HISTORY_TYPE_POST_RATED, user=None, deleted=False).filter(session_key=getattr(request.session, settings.SUPER_MODEL_KEY_NAME)).count()
            except:
                mark = 0

        return mark

    @cached_property
    def last_modified(self):
        History = import_string(settings.BASE_HISTORY_CLASS)
        try:
            latest_created = History.objects.filter(post=self).latest('created').created
            latest_updated = History.objects.filter(post=self).exclude(updated=None).latest('updated').updated
            latest_updated = latest_updated if latest_updated is not None else latest_created

            if latest_created is None:
                raise Exception

            return max(latest_created, latest_updated)

        except:
            if self.updated:
                return self.updated
            elif self.created:
                return self.created
            else:
                return None

    @cached_property
    def published_comments_count(self):
        return self.comments.get_available().count()

    @cached_property
    def last_comment_date(self):
        try:
            last_comment = self.comments.get_available().latest('created')
            date = last_comment.created
        except:
            date = None
        return date


    def make_alias(self):
        return helper.make_alias(self.title)

    def clean(self):
        if self.alias:
            try:
                self.alias.encode('ascii')
            except:
                raise ValidationError('Недопустимые символы в синониме {0}'.format(self.alias))

            result = re.match('[a-z0-9_\-]{1,}', self.alias)
            if not result:
                raise ValidationError('Недопустимые символы в синониме')
    def save(self, *args, **kwargs):
        self.clean()
        self.title = helper.trim_title(self.title)
        #saved_version = self.saved_version
        if hasattr(self, 'title') and self.title and not self.alias:
            self.alias = self.make_alias()
        if self.alias:
            BASE_POST_CLASS = import_string(settings.BASE_POST_CLASS)
            alias_is_busy = BASE_POST_CLASS.objects.filter(alias=self.alias).exclude(pk=self.pk)
            if alias_is_busy:
                raise ValidationError('Синоним {0} занят'.format(self.alias))

        self.post_type = self.get_post_type()
        super().save(*args, **kwargs)
        History = import_string(settings.BASE_HISTORY_CLASS)
        History.save_history(history_type=HISTORY_TYPE_POST_CREATED, post=self)




class SuperUserProfile(SuperModel, CachedModelMixin):
    class Meta:
        abstract = True

    user = models.OneToOneField(User, related_name='user_profile', db_index=True)  # reverse returns single object, not queryset
    role = models.PositiveIntegerField(choices=settings.USER_ROLES, default=settings.USER_ROLE_REGULAR, blank=True, db_index=True)
    image = ImageField(verbose_name='Изображение', upload_to='user_profile', blank=True, null=True)
    receive_messages = models.BooleanField(default=True, verbose_name='Получать e-mail сообщения с сайта', blank=True, db_index=True)

    @property
    def can_publish_comment(self):
        return False

    def __str__(self):
        return 'Профиль пользователя {0}, pk={1}'.format(self.user.username, self.user.pk)

    def get_email_confirmed(self):
        return EmailAddress.objects.filter(user=self.user, verified=True, email=self.user.email).exists()

    @classmethod
    def get_profile(cls, user):
        user_profile, created = cls.objects.get_or_create(user=user)
        if created:
            user_profile.save()
        return user_profile

    def save(self, *args, **kwargs):
        if self.user.is_staff:
            self.role = settings.USER_ROLE_ADMIN

        super().save(*args, **kwargs)
        #invalidate_obj(self.user)

    def get_unsubscribe_url(self):
        email_adress = EmailAddress.objects.get(email=self.user.email)
        try:
            key = email_adress.emailconfirmation_set.latest('created').key
        except:
            key = EmailConfirmation.create(email_adress).key

        return reverse('unsubscribe', kwargs={'email': self.user.email, 'key': key})

    def karm_history(self):
        return self._karm_history().order_by('-created')

    def _karm_history(self):
        History = import_string(settings.BASE_HISTORY_CLASS)
        hists = History.objects.filter(author=self.user, history_type=HISTORY_TYPE_COMMENT_RATED, deleted=False)
        return hists


    def _activity_history(self):
        History = import_string(settings.BASE_HISTORY_CLASS)
        return History.objects.filter(user=self.user, user_points__gt=0, deleted=False)

    @cached_property
    def activity_history(self):
        return self._activity_history().order_by('-created')

    @cached_property
    def get_user_activity(self):
        try:
            activity = self.activity_history.aggregate(Sum('user_points'))['user_points__sum']
        except:
            activity = ''
        return activity


    @cached_property
    def get_user_karm(self):
        try:
            karm = self.karm_history().aggregate(Sum('user_points'))['user_points__sum']
        except:
            karm = 0
        return karm if karm is not None else 0



def is_regular(self):
    if self.user_profile.role == settings.USER_ROLE_REGULAR:
        return True
    else:
        return False

def get_user_image(self):
    return self.user_profile.image

@property
def karm_history(self):
    return self.user_profile.karm_history

@property
def activity_history(self):
    return self.user_profile.activity_history

@property
def get_user_activity(self):
    return self.user_profile.get_user_activity

@property
def get_user_karm(self):
    return self.user_profile.get_user_karm


@property
def get_email_confirmed(self):
    return self.user_profile.get_email_confirmed()

User.is_regular = property(is_regular)
User.image = property(get_user_image)
User.karm_history = karm_history
User.activity_history = activity_history
User.karm = get_user_karm
User.get_karm_url = lambda self: reverse('user-karma', kwargs={'pk': self.pk})
User.get_comments_url = lambda self: reverse('user-comments', kwargs={'pk': self.pk})
User.get_activity_url = lambda self: reverse('user-activity', kwargs={'pk': self.pk})
User.get_absolute_url = lambda self: reverse('user-detail', kwargs={'pk': self.pk})

User.activity = get_user_activity
User.email_confirmed = get_email_confirmed

User.is_admin = property(lambda self: self.user_profile.role == settings.USER_ROLE_ADMIN)
User.is_regular = property(lambda self: self.user_profile.role == settings.USER_ROLE_REGULAR)
User.thumb100 = property(lambda self: self.user_profile.thumb100)
User.thumb50 = property(lambda self: self.user_profile.thumb50)


AnonymousUser.is_regular = True
AnonymousUser.is_doctor = False
AnonymousUser.is_admin = False
AnonymousUser.is_author = False

AnonymousUser.image = None
AnonymousUser.email_confirmed = False
AnonymousUser.karm = 0
AnonymousUser.activity = 0


HISTORY_TYPE_COMMENT_CREATED = 1
HISTORY_TYPE_COMMENT_SAVED = 2
HISTORY_TYPE_COMMENT_RATED = 3
HISTORY_TYPE_POST_CREATED = 4
HISTORY_TYPE_POST_SAVED = 5
HISTORY_TYPE_POST_RATED = 6
HISTORY_TYPE_COMMENT_COMPLAINT = 7
#HISTORY_TYPE_POST_COMPLAINT = 8
#HISTORY_TYPE_BLOG_RATED = 8

HISTORY_TYPES = (
    (HISTORY_TYPE_COMMENT_CREATED, 'Комментарий создан'),
    (HISTORY_TYPE_COMMENT_SAVED, 'Комментарий сохранен'),
    (HISTORY_TYPE_COMMENT_RATED, 'Комментарий оценен'),
    (HISTORY_TYPE_POST_CREATED, 'Материал создан'),
    (HISTORY_TYPE_POST_SAVED, 'Материал сохранен'),
    (HISTORY_TYPE_POST_RATED, 'Материал оценен'),
    (HISTORY_TYPE_COMMENT_COMPLAINT, 'Жалоба на комментарий'),
    #(HISTORY_TYPE_POST_COMPLAINT, 'Жалоба на материал'),
    #(HISTORY_TYPE_BLOG_RATED, 'Запись блога оценена'),

)

HISTORY_TYPES_POINTS = {
HISTORY_TYPE_COMMENT_CREATED: 3,
HISTORY_TYPE_COMMENT_SAVED: 0,
HISTORY_TYPE_COMMENT_RATED: 1,
HISTORY_TYPE_POST_CREATED: 0,
HISTORY_TYPE_POST_SAVED: 0,
HISTORY_TYPE_POST_RATED: 1,
HISTORY_TYPE_COMMENT_COMPLAINT: 0,
#HISTORY_TYPE_BLOG_RATED: 0,
}



class SuperHistory(SuperModel):
    class Meta:
        abstract = True
    history_type = models.IntegerField(choices=HISTORY_TYPES, db_index=True)
    author = models.ForeignKey(User, null=True, blank=True, related_name='history_author', db_index=True)
    user = models.ForeignKey(User, null=True, blank=True, related_name='history_user', db_index=True)
    comment = models.ForeignKey('Comment', null=True, blank=True, related_name='history_comment', db_index=True)
    user_points = models.PositiveIntegerField(default=0, blank=True)
    #author_points = models.PositiveIntegerField(default=0, blank=True)
    ip = models.CharField(max_length=300, null=True, blank=True, db_index=True)
    session_key = models.TextField(blank=True, null=True, db_index=True)
    mark = models.IntegerField(choices=POST_MARKS_FOR_COMMENT, blank=True, null=True, verbose_name='Оценка')

    old_id = models.PositiveIntegerField(null=True, blank=True)
    deleted = models.BooleanField(verbose_name='Удалена', default=False, db_index=True)

    @staticmethod
    def get_points(history_type):
        return HISTORY_TYPES_POINTS[history_type]

    def __str__(self):
        return "{0} - {1} - {2}".format(self.history_type, self.post, self.comment)

    @classmethod
    def save_history(cls, history_type, post, user=None, ip=None, session_key=None, comment=None, mark=None):
        if hasattr(post, 'post_ptr'):
            post = post.post_ptr
        History = cls
        if hasattr(post, 'user'):
            post_author = post.user
        else:
            post_author = None

        if user and not user.is_authenticated():
            user = None

        if history_type not in (HISTORY_TYPE_POST_CREATED, HISTORY_TYPE_POST_SAVED):
            if user is None and session_key is None:
                return None

        if isinstance(mark, str):
            mark = int(mark)

        if mark is None and comment is not None and comment.post_mark:
            mark = comment.post_mark

        if history_type == HISTORY_TYPE_POST_CREATED:
            hist_exists = History.objects.filter(history_type=history_type, post=post, deleted=False).exists()
            if not hist_exists:
                h = History.objects.create(history_type=history_type, post=post, user=user,
                                       user_points=History.get_points(history_type), ip=ip, author=post_author, session_key=session_key)
            else:
                h = History.save_history(HISTORY_TYPE_POST_SAVED, post, user, ip, session_key, comment)
            return h
        elif history_type == HISTORY_TYPE_POST_SAVED:
            h = History.objects.create(history_type=history_type, post=post, user=user, ip=ip, author=post_author, session_key=session_key)
            return h
        elif history_type == HISTORY_TYPE_COMMENT_CREATED:
            hist_exists = History.objects.filter(history_type=history_type, comment=comment, deleted=False).exists()
            if not hist_exists:

                h = History.objects.create(history_type=history_type, post=post, user=user, comment=comment, ip=ip,
                                       user_points=History.get_points(history_type),
                                       author=post_author, mark=mark, session_key=session_key)
            else:
                h = History.save_history(HISTORY_TYPE_COMMENT_SAVED, post, user, ip, session_key, comment, mark=mark)
            return h
        elif history_type == HISTORY_TYPE_COMMENT_SAVED:
            h = History.objects.create(history_type=history_type, post=post, user=user, comment=comment, ip=ip,
                                   user_points=History.get_points(history_type), author=post_author, session_key=session_key)
            return h
        elif history_type in [HISTORY_TYPE_COMMENT_RATED, HISTORY_TYPE_COMMENT_COMPLAINT]:
            #if history_type == HISTORY_TYPE_COMMENT_RATED:
            #    author_points = 1
            #else:
            #    author_points = 0
            if comment.can_do_action(history_type=history_type, user=user, session_key=session_key, ip=ip):
                History.objects.filter(post=post, user=user, session_key=session_key, comment=comment, history_type__in=[HISTORY_TYPE_COMMENT_RATED, HISTORY_TYPE_COMMENT_COMPLAINT]).delete()
                h = History.objects.create(history_type=history_type, post=post, user=user, comment=comment, ip=ip,
                                       user_points=History.get_points(history_type),
                                       author=comment.user, session_key=session_key)
                return h
        elif history_type == HISTORY_TYPE_POST_RATED:
            if user and user.is_authenticated():
                hist_exists = History.objects.filter(history_type=history_type, post=post, user=user, deleted=False).exists()
            else:
                hist_exists_by_key = History.objects.filter(history_type=history_type, post=post, session_key=session_key, user=None, deleted=False).exists()
                hist_exists_by_ip = History.objects.filter(history_type=history_type, post=post, ip=ip, user=None, deleted=False).exists()
                hist_exists = hist_exists_by_key or hist_exists_by_ip

            if not hist_exists and ((not post.is_blog and mark and mark > 0) or post.is_blog):
                h = History.objects.create(history_type=history_type, post=post, user=user, ip=ip, comment=comment,
                                   user_points=History.get_points(history_type), author=post_author, mark=mark, session_key=session_key)
                return h


    @classmethod
    def exists(cls, session_key):
        if not session_key:
            return False
        if not settings.CACHE_ENABLED:
            return cls.objects.filter(session_key=session_key, deleted=False).exists()
        prefix = '_cached_history_exists_'
        key = prefix + session_key
        res = cache.get(key)
        if res is None:
            res = cls.objects.filter(session_key=session_key, deleted=False).exists()
            cache.set(key, res, settings.HISTORY_EXISTS_DURATION)
        return res

    def invalidate_exists(self):
        if settings.CACHE_ENABLED and self.session_key:
            prefix = '_cached_history_exists_'
            key = prefix + self.session_key
            cache.delete(key)
            res = type(self).objects.filter(session_key=self.session_key, deleted=False).exists()
            cache.set(key, res, settings.HISTORY_EXISTS_DURATION)

    def delete_exists(self):
        if settings.CACHE_ENABLED and self.session_key:
            prefix = '_cached_history_exists_'
            key = prefix + self.session_key
            cache.delete(key)


    #TODO change to cached_method
    @classmethod
    def full_exists_by_comment(cls, session_key, comment):
        if not session_key:
            return False
        if not settings.CACHE_ENABLED or settings.HISTORY_FULL_EXISTS_BY_COMMENT_DURATION is None:
            return cls.objects.filter(session_key=session_key, comment=comment, deleted=False).exists()
        if not cls.exists(session_key):
            return False
        template = '_cached_history_full_exists_by_comment_{0}-{1}'
        key = template.format(session_key, comment.pk)
        res = cache.get(key)
        if res is None:
            res = cls.objects.filter(session_key=session_key, comment=comment, deleted=False).exists()
            cache.set(key, res, settings.HISTORY_FULL_EXISTS_BY_COMMENT_DURATION)
        return res

    def invalidate_full_exists_by_comment(self):
        if settings.CACHE_ENABLED and self.session_key and settings.HISTORY_FULL_EXISTS_BY_COMMENT_DURATION is not None:
            if self.comment:
                template = '_cached_history_full_exists_by_comment_{0}-{1}'
                key = template.format(self.session_key, self.comment.pk)
                cache.delete(key)
                res = type(self).objects.filter(session_key=self.session_key, comment=self.comment, deleted=False).exists()
                cache.set(key, res, settings.HISTORY_FULL_EXISTS_BY_COMMENT_DURATION)

    def delete_full_exists_by_comment(self):
        if settings.CACHE_ENABLED and self.session_key and settings.HISTORY_FULL_EXISTS_BY_COMMENT_DURATION is not None:
            if self.comment:
                template = '_cached_history_full_exists_by_comment_{0}-{1}'
                key = template.format(self.session_key, self.comment.pk)
                cache.delete(key)



    #TODO change to cached_method
    @classmethod
    def exists_by_comment(cls, session_key, comment, history_type=None):
        if not session_key:
            return False
        if not settings.CACHE_ENABLED or settings.HISTORY_EXISTS_BY_COMMENT_DURATION is None:
            q = cls.objects.filter(session_key=session_key, comment=comment, deleted=False, history_type=history_type)
            return q.exists()
        if not cls.exists(session_key):
            return False
        template = '_cached_history_exists_by_comment_{0}-{1}-{2}'
        key = template.format(session_key, comment.pk, history_type)
        res = cache.get(key)
        if res is None:
            q = cls.objects.filter(session_key=session_key, comment=comment, deleted=False, history_type=history_type).exists()
            cache.set(key, res, settings.HISTORY_EXISTS_BY_COMMENT_DURATION)
        return res

    def invalidate_exists_by_comment(self):
        if settings.CACHE_ENABLED and self.session_key and settings.HISTORY_EXISTS_BY_COMMENT_DURATION is not None:
            if self.comment:
                template = '_cached_history_exists_by_comment_{0}-{1}-{2}'
                key = template.format(self.session_key, self.comment.pk, self.history_type)
                cache.delete(key)
                res = type(self).objects.filter(session_key=self.session_key, comment=self.comment, history_type=self.history_type, deleted=False).exists()
                cache.set(key, res, settings.HISTORY_EXISTS_BY_COMMENT_DURATION)

    def delete_exists_by_comment(self):
        if settings.CACHE_ENABLED and self.session_key and settings.HISTORY_EXISTS_BY_COMMENT_DURATION is not None:
            if self.comment:
                template = '_cached_history_exists_by_comment_{0}-{1}'
                key = template.format(self.session_key, self.comment.pk, self.history_type)
                cache.delete(key)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.comment:
            self.comment.full_invalidate_cache()
            #invalidate_obj(self.comment)

            for ancestor in self.comment.get_ancestors():
                ancestor.full_invalidate_cache()
                #invalidate_obj(ancestor)
            for descendant in self.comment.get_descendants():
                descendant.full_invalidate_cache()
                #invalidate_obj(descendant)

        if self.post:
            self.post.obj.full_invalidate_cache()
            #invalidate_obj(self.post.obj)


        if self.user:
            self.user.user_profile.full_invalidate_cache()
        if self.author:
            self.author.user_profile.full_invalidate_cache()
            #invalidate_obj(self.author)
        self.invalidate_exists()
        self.invalidate_exists_by_comment()
        self.invalidate_full_exists_by_comment()


    def delete(self, *args, **kwargs):
        post = self.post
        comment = self.comment
        user = self.user
        author = self.author
        self.delete_exists_by_comment()
        self.delete_exists()
        super().delete(*args, **kwargs)
        if comment:
            comment.full_invalidate_cache()
            #invalidate_obj(comment)

            for ancestor in comment.get_ancestors():
                ancestor.full_invalidate_cache()
                #invalidate_obj(ancestor)
            for descendant in comment.get_descendants():
                descendant.full_invalidate_cache()
                #invalidate_obj(descendant)

        if post:
            post.obj.full_invalidate_cache()
            #invalidate_obj(post.obj)

        if user:
            user.user_profile.full_invalidate_cache()
            #invalidate_obj(user)
        if author:
            author.user_profile.full_invalidate_cache()
            #invalidate_obj(author)



MAIL_TYPE_COMMENT_CONFIRM = 1
MAIL_TYPE_USER_REGISTRATION = 2
MAIL_TYPE_PASSWORD_RESET = 3
MAIL_TYPE_ANSWER_TO_COMMENT = 4
MAIL_TYPE_EMAIL_CONFIRMATION = 5

MAIL_TYPES = (
    (MAIL_TYPE_COMMENT_CONFIRM, 'Подтверждение отзыва'),
    (MAIL_TYPE_USER_REGISTRATION, 'Регистрация пользователя'),
    (MAIL_TYPE_PASSWORD_RESET, 'Сброс пароля'),
    (MAIL_TYPE_ANSWER_TO_COMMENT, 'Ответ на отзыв'),
    (MAIL_TYPE_EMAIL_CONFIRMATION, 'Подтверждение электронного адреса'),
)

class SuperMail(SuperModel):
    class Meta:
        abstract = True
    mail_type = models.PositiveIntegerField(choices=MAIL_TYPES, db_index=True)
    subject = models.TextField()
    body_html=models.TextField(default='', blank=True)
    body_text=models.TextField(default='', blank=True)
    email = models.EmailField(db_index=True)
    user = models.ForeignKey(User, blank=True, null=True, db_index=True)
    ip = models.CharField(max_length=300, null=True, blank=True, db_index=True)
    session_key = models.TextField(null=True, blank=True, db_index=True)
    email_from = models.EmailField(db_index=True)
    entity_id = models.CharField(max_length=20, blank=True, db_index=True)

    @property
    def mail_type_text(self):
        for mail_type, text in MAIL_TYPES:
            if mail_type == self.mail_type:
                return text

    def __str__(self):
        return '{0} | {1} | {2} | {3}'.format(self.mail_type_text, self.email, self.user, self.created)

def create_user_profile(sender, instance, created, **kwargs):
    UserProfile = import_string(settings.BASE_USER_PROFILE_CLASS)
    profile, created = UserProfile.objects.get_or_create(user=instance)
    if created:
        profile.save()

def confirm_user_comments(sender, instance, created, **kwargs):
    if instance.email_confirmed:
        for comment in instance.comments.filter(confirmed=False):
            comment.confirmed = True
            comment.save()

def confirm_user_comments_by_email(sender, instance, created, **kwargs):
    if instance.verified:
        for comment in instance.user.comments.filter(confirmed=False):
            comment.confirmed = True
            comment.save()


post_save.connect(create_user_profile, sender=User)
post_save.connect(confirm_user_comments, sender=User)
post_save.connect(confirm_user_comments_by_email, sender=EmailAddress)


def request_with_empty_guest(request):
    user = request.user
    if user.is_authenticated():
        return False

    session_key = getattr(request.session, settings.SUPER_MODEL_KEY_NAME, None)

    if not session_key:
        return True

    History = import_string(settings.BASE_HISTORY_CLASS)
    exists = History.exists(session_key)
    if not exists:
        return True

    return False