#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travnik.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


from main import models
from super_model.models import POST_STATUS_PUBLISHED

with open('load.csv', 'r') as file:
    for line in file:
        line_as_list = line.split(';')
        line_as_list = [elem.strip() for elem in line_as_list]

        plant_title = line_as_list[0]
        usage_area_titles = line_as_list[1].split(',')
        usage_area_titles = [elem.strip() for elem in usage_area_titles]


        plant, created = models.Plant.objects.get_or_create(title=plant_title)
        if plant.status != POST_STATUS_PUBLISHED:
            plant.status = POST_STATUS_PUBLISHED
            plant.save()

        for usage_area_title in usage_area_titles:
            usage_area, created = models.UsageArea.objects.get_or_create(title=usage_area_title)
            if usage_area.status != POST_STATUS_PUBLISHED:
                usage_area.status = POST_STATUS_PUBLISHED
                usage_area.save()
            if not usage_area in plant.usage_areas.all():
                plant.usage_areas.add(usage_area)

