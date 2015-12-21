from django.forms.models import ModelForm
from django.forms import TextInput, Textarea
from contact_form.models import ContactForm

class ContactFormModel(ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and user.is_authenticated():
            if user.first_name or user.last_name:
                self.fields['name'].initial = "{0} {1}".format(user.first_name, user.last_name)
            self.fields['email'].initial = user.email
            self.instance.user = user

        self.fields['name'].widget = TextInput(attrs={'placeholder': 'Ваше имя', 'class': 'form-control'})

        self.fields['email'].widget = TextInput(attrs={'placeholder': 'Email', 'class': 'form-control'})

        self.fields['body'].widget = Textarea(attrs={'placeholder': 'Сообщение', 'class': 'form-control'})



    class Meta:
        model = ContactForm
        exclude = ['status', 'user', 'created']
