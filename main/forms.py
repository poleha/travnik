from super_model import forms as super_forms
from django.conf import settings
from django import forms
from . import models
from django.db.models.aggregates import Count

class PlantFilterForm(super_forms.PostFilterForm):
    class Meta:
        post_type = settings.POST_TYPE_PLANT

    usage_areas = forms.MultipleChoiceField(choices=(), label='Область применения', widget=forms.CheckboxSelectMultiple(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['title']
        usage_areas = models.UsageArea.objects.get_available().annotate(plant_count=Count('plants'))
        usage_area_choices = ()
        for usage_area in usage_areas:
            usage_area_choices += ((usage_area.pk, "{0}({1})".format(usage_area, usage_area.plant_count)),)
        self.fields['usage_areas'] = forms.MultipleChoiceField(choices=usage_area_choices, label='Область применения', widget=forms.CheckboxSelectMultiple(), required=False)



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


class RecipeForm(forms.ModelForm):
    class Meta:
        model = models.Recipe
        exclude = ('post_type', 'created', 'updated', 'published')


class UsageAreaForm(forms.ModelForm):
    class Meta:
        model = models.UsageArea
        exclude = ('post_type', 'created', 'updated', 'published')



class CommentForm(super_forms.SuperCommentForm):
    class Meta:
        model = models.Comment
        fields = ('username', 'email', 'body', 'parent' )


class CommentOptionsForm(super_forms.SuperCommentOptionsForm):
        show_type_label = 'Вид показа комментариев'


class CommentUpdateForm(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ('body', )

