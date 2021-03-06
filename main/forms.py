from django import forms
from django.conf import settings
from django.db.models.aggregates import Count
from django.forms import ValidationError

from helper.helper import trim_title
from super_model import forms as super_forms
from . import models


class PlantFilterForm(super_forms.PostFilterForm):
    class Meta:
        post_type = settings.POST_TYPE_PLANT

    usage_areas = forms.MultipleChoiceField(choices=(), label='Область применения',
                                            widget=forms.CheckboxSelectMultiple(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['title']
        usage_areas = models.UsageArea.objects.get_available().annotate(plant_count=Count('plants'))
        usage_area_choices = ()
        for usage_area in usage_areas:
            if usage_area.plant_count > 0:
                usage_area_choices += ((usage_area.pk, "{0}({1})".format(usage_area, usage_area.plant_count)),)
        self.fields['usage_areas'] = forms.MultipleChoiceField(choices=usage_area_choices, label='Область применения',
                                                               widget=forms.CheckboxSelectMultiple(), required=False)


class RecipeFilterForm(super_forms.PostFilterForm):
    class Meta:
        post_type = settings.POST_TYPE_RECIPE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['title']


class PlantForm(forms.ModelForm):
    class Meta:
        model = models.Plant
        exclude = ('post_type', 'created', 'updated', 'published')


class BaseRecipeForm(forms.ModelForm):
    required_css_class = 'required'

    @staticmethod
    def create_plant_choices(exclude_plant=None):
        plants_choices = ()
        plants = models.Plant.objects.get_available()
        if exclude_plant:
            plants = plants.exclude(pk=exclude_plant.pk)
        for plant in plants:
            synonyms_list = plant.synonyms.all().values_list('synonym', flat=True)
            if synonyms_list:
                plants_choices += ((plant.pk, "{0}({1})".format(plant, ", ".join(synonyms_list))),)
            else:
                plants_choices += ((plant.pk, plant),)
        return plants_choices

    def __new__(cls, *args, **kwargs):
        cls.base_fields['plants'].widget = forms.CheckboxSelectMultiple()
        cls.base_fields['usage_areas'].widget = forms.CheckboxSelectMultiple()
        cls.base_fields['plants'].choices = cls.create_plant_choices()
        cls.base_fields['plants'].required = False
        cls.base_fields['usage_areas'].required = True
        return super().__new__(cls)


class RecipeForm(BaseRecipeForm):
    class Meta:
        model = models.Recipe
        exclude = ('post_type', 'created', 'updated', 'published')


class RecipeUserUpdateForm(BaseRecipeForm):
    class Meta:
        model = models.Recipe
        fields = ('title', 'body', 'usage_areas', 'plants')


class RecipeUserForm(BaseRecipeForm):
    class Meta:
        model = models.Recipe
        fields = ('title', 'body', 'usage_areas', 'plants')

    def __init__(self, *args, **kwargs):
        plant = kwargs.pop('plant')
        self.plant = plant
        super().__init__(*args, **kwargs)
        self.fields['plants'].queryset = models.Plant.objects.get_available().exclude(pk=plant.pk)
        self.fields['plants'].choices = self.create_plant_choices(plant)
        self.fields['plants'].label = 'Другие растения'
        self.fields['title'].label = ''
        self.fields['title'].widget.attrs['placeholder'] = 'Название рецепта*'
        self.fields['body'].required = True

    def clean(self):
        super().clean()
        plants = self.cleaned_data.get('plants', None)
        if plants:
            plants = list(plants)
            plants.append(self.plant)
            for plant in plants:
                title = self.cleaned_data.get('title', None)
                if title:
                    title = trim_title(title)
                    existing_recipes = models.Recipe.objects.filter(title__iexact=title, plants=plant).exclude(
                        pk=self.instance.pk)
                    if existing_recipes.exists():
                        raise ValidationError('Рецепт с таким названием уже существует для растения {}'.format(plant))


class UsageAreaForm(forms.ModelForm):
    class Meta:
        model = models.UsageArea
        exclude = ('post_type', 'created', 'updated', 'published')


class CommentForm(super_forms.SuperCommentForm):
    class Meta:
        model = models.Comment
        fields = ('username', 'email', 'body', 'parent')


class CommentOptionsForm(super_forms.SuperCommentOptionsForm):
    show_type_label = 'Вид показа комментариев'


class CommentUpdateForm(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ('body',)
