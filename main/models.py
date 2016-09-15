from django.db import models
from django.db.models.aggregates import Sum
from django.conf import settings
from django.core.urlresolvers import reverse
from allauth.account.models import EmailAddress, EmailConfirmation
from sorl.thumbnail import ImageField, get_thumbnail
from ckeditor.fields import RichTextField
from cache.decorators import cached_property
from super_model import models as super_models
from django.utils.html import strip_tags
from helper import helper
from django.utils.html import mark_safe
from django.forms import ValidationError
from django.db.models import Q, Max
from django.contrib.auth.models import User



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
    class Meta:
        ordering = ['title']

    cached_views = (
        ('travnik_main.views.PostDetail', 'get'),
    )

    can_be_rated = True

    def __str__(self):
        return self.title.capitalize()

    @classmethod
    def get_post_type(cls):
        if cls == Plant:
            return settings.POST_TYPE_PLANT
        elif cls == Recipe:
            return settings.POST_TYPE_RECIPE
        elif cls == UsageArea:
            return settings.POST_TYPE_USAGE_AREA

    @property
    def is_plant(self):
        return self.post_type == settings.POST_TYPE_PLANT

    @property
    def is_recipe(self):
        return self.post_type == settings.POST_TYPE_RECIPE

    @property
    def is_usage_area(self):
        return self.post_type == settings.POST_TYPE_USAGE_AREA


    @classmethod
    def ajax_submit_url(cls):
        if cls == Plant:
            return reverse('plant-list-ajax')
        #elif cls == Recipe:
        #    return reverse('recipe-list-ajax')

    @classmethod
    def submit_url(cls):
        if cls == Plant:
            return reverse('plant-list')
        #elif cls == Recipe:
        #    return reverse('recipe-list')

    @classmethod
    def get_list_url(cls):
        if cls == Plant:
            return reverse('plant-list')
        #elif cls == Recipe:
        #    return reverse('recipe-list')


    @property
    def anons(self):
        if self.short_body:
            return self.short_body
        else:
            return helper.cut_text(strip_tags(self.body), 200)

    @property
    def update_url(self):
        if self.is_plant:
            return reverse('plant-update', kwargs={'pk': self.pk})
        elif self.is_recipe:
            return reverse('recipe-update', kwargs={'pk': self.pk})
        elif self.is_usage_area:
            return reverse('usage_area-update', kwargs={'pk': self.pk})


    @property
    def obj(self):
        if self.post_type == settings.POST_TYPE_PLANT:
            return self.plant
        elif self.post_type == settings.POST_TYPE_RECIPE:
            return self.recipe
        elif self.post_type == settings.POST_TYPE_USAGE_AREA:
            return self.usagearea

    def get_absolute_url(self):
        alias = self.alias
        if alias:
            return reverse('post-detail-alias', kwargs={'alias': alias})
        else:
            return reverse('post-detail-pk', kwargs={'pk': self.pk})



    def save(self, *args, **kwargs):
        self.title = helper.trim_title(self.title).lower()
        super().save(*args, **kwargs)


class Plant(Post):
    body = RichTextField(verbose_name='Описание', blank=True)
    image = ImageField(verbose_name='Изображение', upload_to='plant', blank=True, null=True, max_length=300)
    usage_areas = models.ManyToManyField('UsageArea', verbose_name='Области применения', blank=True, related_name='plants')
    short_body = models.TextField(verbose_name='Анонс', blank=True)
    wikipedia_link = models.TextField(blank=True, verbose_name='Страница на wikipedia')
    code = models.PositiveIntegerField(unique=True, blank=True)

    objects = super_models.PostManager()

    def type_str(self):
        return 'Растение'


    @cached_property
    def average_mark(self):
        try:
            mark = History.objects.filter(post=self, deleted=False).aggregate(Sum('mark'))['mark__sum']
            if mark is None:
                mark = 0
        except:
            mark = 0

        if mark > 0 and self.marks_count > 0:
            return int(round(mark / self.marks_count, 0))
        else:
            return 0

    @cached_property
    def marks_count(self):
        return History.objects.filter(post=self, history_type=super_models.HISTORY_TYPE_POST_RATED, deleted=False).count()


    @property
    def thumb110(self):
        try:
            return get_thumbnail(self.image, '110x200', quality=settings.DEFAULT_THUMBNAIL_QUALITY).url
        except:
            return ''

    @cached_property
    def published_recipes_count(self):
        return self.recipes.get_available().count()

    @cached_property
    def synonyms_text(self):
        return mark_safe(', '.join(self.synonyms.values_list('synonym', flat=True)))

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

    @staticmethod
    def get_plant_by_alias(alias):
        alias = alias.strip()
        plants = Plant.objects.filter(Q(Q(alias=alias) | Q(synonyms__alias=alias))).distinct()
        if plants.exists():
            return plants[0]
        else:
            return None

    @staticmethod
    def get_plant_by_title(title):
        title = helper.trim_title(title)
        plants = Plant.objects.filter(Q(Q(title=title) | Q(synonyms__synonym=title))).distinct()
        if plants.exists():
            return plants[0]
        else:
            return None

    @staticmethod
    def get_plant_by_slug(slug):
        plant = Plant.get_plant_by_alias(slug)
        if plant is None:
            plant = Plant.get_plant_by_title(slug)
        return plant if plant else None

    def clean(self):
        existing_plants = type(self).objects.filter(title=self.title).exclude(pk=self.pk)
        if existing_plants.exists():
            raise ValidationError('Растение с таким названием уже существует')

    def get_new_code(self):
        try:
            max_code = type(self).objects.exclude(pk=self.pk).aggregate(Max('code'))['code__max']
        except:
            max_code = 0
        code = max_code + 1
        return code

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.code:
            self.code = self.get_new_code()
        super().save(*args, **kwargs)



class Synonym(models.Model):
    class Meta:
        ordering = ('synonym', )

    synonym = models.CharField(max_length=500, verbose_name='Синоним')
    alias = models.CharField(max_length=800, blank=True, verbose_name='Синоним', db_index=True)
    plant = models.ForeignKey(Plant, verbose_name='Растение', related_name='synonyms')


    def __str__(self):
        return self.synonym

    def clean(self):
        if self.synonym.strip() == "":
            raise ValidationError('Синоним обязателен к заполнению')

        if self.plant.title == self.synonym:
            raise ValidationError('Синоним "{}" не должен быть равен наименованию'.format(self.synonym))

        plants = Plant.objects.filter(title=self.synonym).exclude(pk=self.plant.pk)
        if plants.exists():
            raise ValidationError('Синоним "{}" уже используется как название растений'.format(self.synonym))

        plants = Plant.objects.filter(synonyms__synonym=self.synonym).exclude(synonyms__pk=self.pk)
        if plants.exists():
            raise ValidationError('Синоним "{}" уже используется как синоним растений "{}"'.format(self.synonym, plants.values_list('title', flat=True)))

        if self.synonym in self.plant.synonyms.exclude(pk=self.pk).values_list('synonym', flat=True):
            raise ValidationError('Синоним "{}" уже указан в этом растении'.format(self.synonym))


    def save(self, *args, **kwargs):
        self.synonym = helper.trim_title(self.synonym).lower()
        self.alias = helper.make_alias(self.synonym)
        self.full_clean()
        super().save(*args, **kwargs)


class Recipe(Post):
    body = RichTextField(verbose_name='Рецепт', config_name='basic')
    plants = models.ManyToManyField(Plant, verbose_name='Растения', related_name='recipes')
    usage_areas = models.ManyToManyField('UsageArea', verbose_name='Области применения', related_name='recipes')
    comment = models.TextField(null=True, blank=True)
    #user = models.ForeignKey(User, null=True, blank=True, related_name='recipes', db_index=True)

    objects = super_models.PostManager()
    alter_alias = True
    rate_type = 'votes'
    recreate_alias_on_save = True


    def type_str(self):
        return 'Рецепт'


class UsageArea(Post):
    code = models.PositiveIntegerField()

    def type_str(self):
        return 'Область применения'

    def save(self, *args, **kwargs):
        self.title = self.title.lower()
        super().save(*args, **kwargs)


class Comment(super_models.SuperComment):
    class Meta:
        ordering = ['-created']
    post = models.ForeignKey(Post, related_name='comments', db_index=True)
    consult_required = models.BooleanField(default=False, verbose_name='Нужна консультация провизора', db_index=True)
    old_id = models.PositiveIntegerField(null=True, blank=True)

    txt_template_name = 'main/comment/email/answer_to_comment.txt'
    html_template_name = 'main/comment/email/answer_to_comment.html'

    confirm_comment_text_template_name = 'main/comment/email/confirm_comment_text_template.txt'
    confirm_comment_html_template_name = 'main/comment/email/confirm_comment_html_template.html'


class UserProfile(super_models.SuperUserProfile):
    old_id = models.PositiveIntegerField(null=True, blank=True)

    @cached_property
    def can_publish_comment(self):
        if self.user.is_admin or self.get_user_karm >= settings.PUBLISH_COMMENT_WITHOUT_APPROVE_KARM:
            return True
        else:
            return False


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


