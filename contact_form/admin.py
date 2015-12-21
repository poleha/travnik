from django.contrib import admin
from contact_form.models import ContactForm, STATUS_CHECKED, STATUS_CREATED







def make_checked(ContactFormAdmin, request, queryset):
    queryset.update(status=STATUS_CHECKED)
make_checked.short_description = "Mark selected forms as checked"


def make_created(ContactFormAdmin, request, queryset):
    queryset.update(status=STATUS_CREATED)
make_created.short_description = "Mark selected forms as unchecked(created)"

class ContactFormAdmin(admin.ModelAdmin):
    model = ContactForm
    actions = [make_checked, make_created]
    list_filter = ['status']
    exclude = ['']

admin.site.register(ContactForm, ContactFormAdmin)
