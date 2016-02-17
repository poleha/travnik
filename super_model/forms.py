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
            letters = digits + ascii_lowercase + 'абвгдеёжзийклмнопрстуфхцчшщэюя'
            for letter in letters:
                posts = Post.objects.get_available().filter(post_type=post_type, title__istartswith=letter)
                count = posts.count()
                if count > 0:
                    alph += ((letter, '{0}({1})'.format(letter, count)), )
            self.fields['alphabet'] = forms.MultipleChoiceField(choices=alph, label='Алфавитный указатель', required=False, widget=forms.CheckboxSelectMultiple())


class CommentConfirmForm(forms.Form):
    email = forms.EmailField(label='Электронный адрес')
    comment = forms.ModelChoiceField(widget=forms.HiddenInput, queryset=Comment.objects.all())


class SuperCommentForm(forms.ModelForm):
    required_css_class = 'required'
    class Meta:
        model = Comment
        fields = ('username', 'email', 'body', 'parent' )

    def __init__(self, *args, request=None, post=None, **kwargs):
        super().__init__(*args, **kwargs)
        user = request.user
        self.fields['parent'].widget = forms.HiddenInput()
        self.fields['parent'].queryset = post.comments.all()

        if user.is_authenticated():
            self.fields['username'].widget = forms.HiddenInput()
            self.fields['username'].initial = user.username
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['email'].initial = user.email

COMMENTS_ORDER_BY_CREATED_DEC = 1
COMMENTS_ORDER_BY_CREATED_INC = 2


COMMENTS_ORDER_BY_CREATED_CHOICES = (
    (COMMENTS_ORDER_BY_CREATED_DEC, 'Последние отзывы сверху'),
    (COMMENTS_ORDER_BY_CREATED_INC, 'Последние отзывы снизу'),

)

COMMENTS_SHOW_TYPE_PLAIN = 1
COMMENTS_SHOW_TYPE_TREE = 2

COMMENTS_SHOW_TYPE_CHOICES = (
    (COMMENTS_SHOW_TYPE_PLAIN, 'Простой'),
    (COMMENTS_SHOW_TYPE_TREE, 'Деревом'),
)


class SuperCommentOptionsForm(forms.Form):
    show_type_label = 'Вид показа сообщений'
    order_by_created = forms.ChoiceField(choices=COMMENTS_ORDER_BY_CREATED_CHOICES, initial=COMMENTS_ORDER_BY_CREATED_DEC, label='Упорядочить по дате добавления', required=False)
    show_type= forms.ChoiceField(choices=COMMENTS_SHOW_TYPE_CHOICES, label=show_type_label, initial=COMMENTS_SHOW_TYPE_PLAIN, required=False)
