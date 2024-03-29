# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-02-02 06:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_usagearea_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Synonym',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('synonym', models.CharField(max_length=500, verbose_name='Синоним')),
            ],
        ),
        migrations.AddField(
            model_name='plant',
            name='code',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='synonym',
            name='plant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='synonyms', to='main.Plant', verbose_name='Растение'),
        ),
    ]
