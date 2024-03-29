# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-07-29 12:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_auto_20160315_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='code',
            field=models.PositiveIntegerField(blank=True, unique=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='post_type',
            field=models.IntegerField(blank=True, choices=[(1, 'Растение'), (2, 'Рецепт'), (3, 'Область применения')], db_index=True, verbose_name='Вид записи'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='plants',
            field=models.ManyToManyField(related_name='recipes', to='main.Plant', verbose_name='Растения'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='usage_areas',
            field=models.ManyToManyField(related_name='recipes', to='main.UsageArea', verbose_name='Области применения'),
        ),
    ]
