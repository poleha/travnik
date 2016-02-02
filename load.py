#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travnik.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


from main import models
from super_model.models import POST_STATUS_PUBLISHED
from django.core.exceptions import ValidationError

#models.Plant.objects.all().delete()
#models.UsageArea.objects.all().delete()

with open('usage_areas.csv', 'r') as file:
    line_num = 0
    for line in file:
        line_num += 1
        line_as_list = line.split(';')

        if not len(line_as_list) == 2:
            print('List lenght error in usage areas in line {}'.format(line_num))
            continue

        line_as_list = [elem.strip() for elem in line_as_list]
        try:
            code = int(line_as_list[0])
        except:
            print('Number to int convertion error in usage areas in line {}'.format(line_num))
            continue

        title = line_as_list[1].lower()

        usage_area, created = models.UsageArea.objects.get_or_create(code=code)
        if not usage_area.title == title:
            usage_area.title = title
            usage_area.save()
        if created:
            print('Created usage area {} with code {}'.format(usage_area.title, usage_area.code))


with open('load.csv', 'r') as file:
    line_num = 0
    for line in file:
        line_num += 1
        line_as_list = line.split(';')

        if not (3 <= len(line_as_list) <= 4):
            print('List lenght error in line {}'.format(line_num))
            continue

        line_as_list = [elem.strip() for elem in line_as_list]
        code = line_as_list[0]
        plant_title = line_as_list[1].lower()
        usage_area_keys = line_as_list[2].split(',')
        usage_area_keys = [int(elem.strip()) for elem in usage_area_keys]

        try:
            code = int(code)
        except:
            print('Number to int convertion error in plants in line {}'.format(line_num))
            continue

        try:
            plant, created = models.Plant.objects.get_or_create(code=code)
        except ValidationError as e:
            print('Validation error "{0}" on creating plant {1} line {2}'.format(e, plant_title, line_num))
            continue

        if plant.title != plant_title:
                plant.title = plant_title
                plant.save()

        if plant.status != POST_STATUS_PUBLISHED:
            plant.status = POST_STATUS_PUBLISHED
            plant.save()
            print('Plant created "{0}" in line {1}'.format(plant.title, line_num))

        if len(line_as_list) == 4:
            synonyms = line_as_list[3].split(',')
            synonyms = [elem.strip().lower() for elem in synonyms]

            for synonym_text in synonyms:
                existing_synonyms = plant.synonyms.all().values_list('synonym', flat=True)
                if not synonym_text in existing_synonyms:
                    models.Synonym.objects.create(plant=plant, synonym=synonym_text)
                    print('Added synonym {} for plant {} with code {}'.format(synonym_text, plant.title, plant.code))

        for usage_area_key in usage_area_keys:
            try:
                usage_area = models.UsageArea.objects.get(code=usage_area_key)
            except:
                print('Usage area not found {}'.format(usage_area_key))
                continue
            if usage_area.status != POST_STATUS_PUBLISHED:
                usage_area.status = POST_STATUS_PUBLISHED
                usage_area.save()
            if not usage_area in plant.usage_areas.all():
                plant.usage_areas.add(usage_area)
                print('Usage area added "{0}" to plant "{1}" in line:{2}'.format(usage_area.title, plant.title, line_num))


