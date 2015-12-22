from django.db import models
from django.db.models.aggregates import Sum, Count
from django.conf import settings
from django.core.urlresolvers import reverse
from allauth.account.models import EmailAddress, EmailConfirmation
from sorl.thumbnail import ImageField, get_thumbnail
from ckeditor.fields import RichTextField
from cache.decorators import cached_property, cached_method
from super_model import models as super_models


COMPONENT_TYPE_VITAMIN = 1
COMPONENT_TYPE_MINERAL = 2
COMPONENT_TYPE_PLANT = 3
COMPONENT_TYPE_OTHER = 4
COMPONENT_TYPES = (
    (COMPONENT_TYPE_VITAMIN, 'Витамин'),
    (COMPONENT_TYPE_MINERAL, 'Минеральное вещество'),
    (COMPONENT_TYPE_PLANT, 'Растение'),
    (COMPONENT_TYPE_OTHER, 'Прочее'),
)


class History(super_models.SuperHistory):
    post = models.ForeignKey('Post', related_name='history_post', db_index=True)


class Post(super_models.SuperPost):
    history_class = History

    cached_views = (
        ('travnik_main.views.PostDetail', 'get'),
    )

    can_be_rated = True

    @classmethod
    def get_post_type(cls):
        if cls == Plant:
            return settings.POST_TYPE_PLANT
        elif cls == Recipe:
            return settings.POST_TYPE_RECIPE

    @property
    def is_plant(self):
        return self.post_type == settings.POST_TYPE_PLANT

    @property
    def is_recipe(self):
        return self.post_type == settings.POST_TYPE_RECIPE


    @classmethod
    def ajax_submit_url(cls):
        if cls == Plant:
            return reverse('plant-list-ajax')
        elif cls == Recipe:
            return reverse('recipt-list-ajax')

    @classmethod
    def submit_url(cls):
        if cls == Plant:
            return reverse('plant-list')
        elif cls == Recipe:
            return reverse('recipe-list')

    @classmethod
    def get_list_url(cls):
        if cls == Plant:
            return reverse('plant-list')
        elif cls == Recipe:
            return reverse('recipe-list')

    @property
    def update_url(self):
        if self.is_plant:
            return reverse('plant-update', kwargs={'pk': self.pk})
        elif self.is_recipe:
            return reverse('recipe-update', kwargs={'pk': self.pk})


    @property
    def obj(self):
        if self.post_type == settings.POST_TYPE_PLANT:
            return self.plant
        elif self.post_type == settings.POST_TYPE_RECIPE:
            return self.recipe

    def get_absolute_url(self):
        alias = self.alias
        if alias:
            return reverse('post-detail-alias', kwargs={'alias': alias})
        else:
            return reverse('post-detail-pk', kwargs={'pk': self.pk})

    def get_mark_by_request(self, request):
        if super_models.request_with_empty_guest(request):
            return 0
        user = request.user
        if user.is_authenticated():
            try:
                mark = History.objects.get(user=user, history_type=super_models.HISTORY_TYPE_POST_RATED, post=self, deleted=False).mark
            except:
                mark = ''
        else:
            try:
                mark = History.objects.get(post=self, session_key=getattr(request.session, settings.SUPER_MODEL_KEY_NAME), history_type=super_models.HISTORY_TYPE_POST_RATED, user=None, deleted=False).mark
            except:
                mark = 0

        return mark

    @cached_property
    def average_mark(self):
        try:
            mark = History.objects.filter(post=self, deleted=False).aggregate(Sum('mark'))['mark__sum']
            if mark is None:
                mark = 0
        except:
            mark = 0

        if mark > 0 and self.marks_count > 0:
            return round(mark / self.marks_count, 2)
        else:
            return 0

    @cached_property
    def marks_count(self):
        return History.objects.filter(post=self, history_type=super_models.HISTORY_TYPE_POST_RATED, deleted=False).count()



class Plant(Post):
    body = RichTextField(verbose_name='Описание', blank=True)
    image = ImageField(verbose_name='Изображение', upload_to='plant', blank=True, null=True, max_length=300)

    objects = super_models.PostManager()

    def type_str(self):
        return 'Растение'

    @property
    def thumb110(self):
        try:
            return get_thumbnail(self.image, '110x200', quality=settings.DEFAULT_THUMBNAIL_QUALITY).url
        except:
            return ''

    @property
    def thumb150(self):
        try:
            return get_thumbnail(self.image, '150x300', quality=settings.DEFAULT_THUMBNAIL_QUALITY).url
        except:
            return ''

    @property
    def thumb220(self):
        try:
            return get_thumbnail(self.image, '220x400', quality=settings.DEFAULT_THUMBNAIL_QUALITY).url
        except:
            return ''


class Recipe(Post):
    body = RichTextField(verbose_name='Описание', blank=True)
    image = ImageField(verbose_name='Изображение', upload_to='plant', blank=True, null=True, max_length=300)
    plants = models.ManyToManyField(Plant, verbose_name='Растения', blank=True, related_name='plants')

    objects = super_models.PostManager()

    def type_str(self):
        return 'Рецепт'

    @property
    def thumb110(self):
        try:
            return get_thumbnail(self.image, '110x200', quality=settings.DEFAULT_THUMBNAIL_QUALITY).url
        except:
            return ''

    @property
    def thumb150(self):
        try:
            return get_thumbnail(self.image, '150x300', quality=settings.DEFAULT_THUMBNAIL_QUALITY).url
        except:
            return ''

    @property
    def thumb220(self):
        try:
            return get_thumbnail(self.image, '220x400', quality=settings.DEFAULT_THUMBNAIL_QUALITY).url
        except:
            return ''





class Comment(super_models.SuperComment):
    class Meta:
        ordering = ['-created']
    post = models.ForeignKey(Post, related_name='comments', db_index=True)
    consult_required = models.BooleanField(default=False, verbose_name='Нужна консультация провизора', db_index=True)
    old_id = models.PositiveIntegerField(null=True, blank=True)

    txt_template_name = 'main/comment/email/answer_to_comment.txt'
    html_template_name = 'main/comment/email/answer_to_comment.html'

    confirm_comment_text_template_name = 'main/comment/email/confirm_comment_html_template.html'
    confirm_comment_html_template_name = 'main/comment/email/confirm_comment_text_template.txt'



class UserProfile(super_models.SuperUserProfile):
    old_id = models.PositiveIntegerField(null=True, blank=True)

    @cached_property
    def can_publish_comment(self):
        if self.user.is_admin or self.user.is_author or self.user.is_doctor or self.get_user_karm >= settings.PUBLISH_COMMENT_WITHOUT_APPROVE_KARM:
            return True
        else:
            return False

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
        hists = History.objects.filter(author=self.user, history_type=super_models.HISTORY_TYPE_COMMENT_RATED, deleted=False)
        return hists


    def _activity_history(self):
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

    @property
    def thumb50(self):
        try:
            return get_thumbnail(self.image, '50x50', quality=settings.DEFAULT_THUMBNAIL_QUALITY).url
        except:
            return ''

    @property
    def thumb100(self):
        try:
            return get_thumbnail(self.image, '100x100', quality=settings.DEFAULT_THUMBNAIL_QUALITY).url
        except:
            return ''

class Mail(super_models.SuperMail):
    pass


