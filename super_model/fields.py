from . import validators
from django import forms
from .app_settings import settings
from django.utils.html import conditional_escape

class UserNameField(forms.CharField):
    default_validators = [validators.validate_first_is_letter, validators.validate_contains_russian, validators.validate_username]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, min_length=settings.ACCOUNT_USERNAME_MIN_LENGTH, max_length=30, label='Имя пользователя', **kwargs)


class SuperImageClearableFileInput(forms.ClearableFileInput):
    template_with_initial = (
        '%(initial_text)s: <img src="%(initial_url)s"> '
        '%(clear_template)s<br />%(input_text)s: %(input)s'
    )

    def get_template_substitution_values(self, value):
        """
        Return value-related substitutions.
        """
        return {
            'initial': conditional_escape(value),
            'initial_url': conditional_escape(getattr(value.instance, self._thumb_name)),
        }


    def __init__(self, thumb_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thumb_name = thumb_name
