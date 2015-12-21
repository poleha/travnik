# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactForm',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=256, verbose_name='Ваше имя')),
                ('email', models.EmailField(max_length=254, verbose_name='E-MAIL')),
                ('body', models.TextField(verbose_name='Сообщение')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('status', models.IntegerField(default=1, choices=[(1, 'created'), (2, 'checked')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True)),
            ],
            options={
                'ordering': ['created'],
            },
        ),
    ]
