from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from .models import User
from super_model.models import MAIL_TYPE_USER_REGISTRATION, MAIL_TYPE_EMAIL_CONFIRMATION, MAIL_TYPE_PASSWORD_RESET
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from .validators import validate_contains_russian, validate_first_is_letter, validate_username
from .app_settings import settings

Mail = import_string(settings.BASE_MAIL_CLASS)

#I could do it with a signal, but it looks more convenient to store apapter here
class SuperSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if not request.user.is_authenticated():
            email_adress = None
            for email in sociallogin.email_addresses:
                if email.verified:
                    email_adress = email.email
                    break
            if email_adress:
                try:
                    user = User.objects.get(email=email_adress)
                    if user.email_confirmed:
                        sociallogin.connect(request, user)
                except:
                    pass
        super().pre_social_login(request, sociallogin)


    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        name = data.get('name')

        user.username = None
        for username_variant in (name, first_name, last_name, "{0}-{1}".format(first_name, last_name), username):
            if self.username_valid(username_variant):
                user.username = username_variant
                break

        if not user.username:
            user.username = 'social-auth-user'



    @staticmethod
    def username_valid(username):
        if username:
            min_length_ok = len(username) > settings.ACCOUNT_USERNAME_MIN_LENGTH
            exists = User.objects.filter(username=username).exists()

            for validator in (validate_contains_russian, validate_first_is_letter, validate_username):
                try:
                    validator(username)
                except ValidationError:
                    return False

            if min_length_ok and not exists:
                return True
            else:
                return False
        else:
            return False


class SuperAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        msg = self.render_mail(template_prefix, email, context)
        res = msg.send()
        if res:
            if template_prefix == 'account/email/email_confirmation_signup':
                mail_type = MAIL_TYPE_USER_REGISTRATION
            elif template_prefix == 'account/email/email_confirmation':
                mail_type = MAIL_TYPE_EMAIL_CONFIRMATION
            elif template_prefix == 'account/email/password_reset_key':
                mail_type = MAIL_TYPE_PASSWORD_RESET
            else:
                return

            if len(msg.alternatives) > 0:
                html = msg.alternatives[0]

            else:
                html = ''
            txt = msg.body

            Mail.objects.create(
                                mail_type=mail_type,
                                subject=msg.subject,
                                body_html=html,
                                body_text=txt,
                                email=msg.to,
                                email_from=msg.from_email,
                            )