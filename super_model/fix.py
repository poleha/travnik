# TODO monkey patch before django-haystack supports django 1.9
from django.db import models
from django.apps import apps
get_model = apps.get_model

models.get_model = get_model