from django import template
from contact_form.forms import ContactFormModel

register = template.Library()

@register.inclusion_tag('contact_form/form.html', takes_context=True)
def get_contact_form(context):
    user = context['request'].user
    contact_form = ContactFormModel(user=user)
    return {'form': contact_form}

