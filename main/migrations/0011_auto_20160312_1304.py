# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-12 10:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_auto_20160312_1217'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=500, verbose_name='Название'),
        ),
    ]