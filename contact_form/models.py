from django.db import models
from django.contrib.auth.models import User

STATUS_CREATED = 1
STATUS_CHECKED = 2

STATUSES = (
    (STATUS_CREATED, 'created'),
    (STATUS_CHECKED, 'checked'),
)


class ContactForm(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False, verbose_name='Ваше имя')
    user = models.ForeignKey(User, null=True, blank=True)
    email = models.EmailField(blank=False, null=False, verbose_name='E-MAIL')
    body = models.TextField(blank=False, verbose_name='Сообщение')
    created = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=STATUS_CREATED, choices=STATUSES)

    def __str__(self):
        return "{0} - {1} - {2} - {3}".format(self.name, self.status, self.created, self.body[:300])

    class Meta:
        ordering = ['created']