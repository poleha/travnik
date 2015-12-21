from django import forms
from haystack.forms import SearchForm
from allauth.account.forms import SignupForm
from . import fields
from django.contrib.auth.models import User
from django.utils.module_loading import import_string
from .app_settings import settings

UserProfile = import_string(settings.BASE_USER_PROFILE_CLASS)
Post = import_string(settings.BASE_POST_CLASS)
Comment = import_string(settings.BASE_COMMENT_CLASS)

class SuperSearchForm(SearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['q'].widget.attrs['placeholder'] = 'Поиск по сайту'
        self.fields['q'].widget.attrs['autocomplete'] = 'Off'

    def search(self):
        # First, store the SearchQuerySet received from other processing.
        sqs = super().search()

        return sqs

class SuperSignupForm(SignupForm):
    required_css_class = 'required'
    image = forms.ImageField(label='Изображение', required=False)
    username = fields.UserNameField()

    def save(self, request, *args, **kwargs):
        user = super().save(request, *args, **kwargs)
        if 'image' in self.cleaned_data:
            user_profile = user.user_profile
            user_profile.image = self.cleaned_data['image']
            user_profile.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('image', 'receive_messages')

    image = forms.ImageField(label='Изображение', widget=fields.SuperImageClearableFileInput(thumb_name='thumb100'), required=False)


class UserForm(forms.ModelForm):
    username = fields.UserNameField()
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')


class PostFilterForm(forms.Form):
    alphabet = forms.MultipleChoiceField(choices=(), label='Алфавитный указатель', required=False, widget=forms.CheckboxSelectMultiple())
    title = forms.CharField(label='Название', required=False)

    def __init__(self, *args, alphabet=True, **kwargs):
        from string import digits, ascii_lowercase
        super().__init__(*args, **kwargs)
        post_type = self.Meta.post_type
        if alphabet:
            alph = ()
            letters = digits + ascii_lowercase + 'абвгдеёжзийклмнопрстуфхцчшщъыбэюя'
            for letter in letters:
                posts = Post.objects.filter(post_type=post_type, title__istartswith=letter)
                count = posts.count()
                if count > 0:
                    alph += ((letter, '{0}({1})'.format(letter, count)), )
            self.fields['alphabet'] = forms.MultipleChoiceField(choices=alph, label='Алфавитный указатель', required=False, widget=forms.CheckboxSelectMultiple())


class CommentConfirmForm(forms.Form):
    email = forms.EmailField(label='Электронный адрес')
    comment = forms.ModelChoiceField(widget=forms.HiddenInput, queryset=Comment.objects.all())
