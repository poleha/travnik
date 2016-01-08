from super_model import forms as super_forms
from django.conf import settings
from django import forms
from . import models

class PlantFilterForm(super_forms.PostFilterForm):
    class Meta:
        post_type = settings.POST_TYPE_PLANT

    usage_areas = forms.ModelMultipleChoiceField(queryset=models.UsageArea.objects.all(), label='Область применения', widget=forms.CheckboxSelectMultiple(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['title']


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

