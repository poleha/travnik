#!/var/www/medavi/venv/bin/python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travnik.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

from main import models
from super_model.models import POST_STATUS_PUBLISHED
from django.core.exceptions import ValidationError
from django.db.models import Count

# models.Plant.objects.all().delete()
# models.UsageArea.objects.all().delete()

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

plant_keys = []

with open('load.csv', 'r') as file:
    line_num = 0
    for line in file:
        line_num += 1
        line_as_list = line.split(';')

        if not (4 <= len(line_as_list) <= 5):
            print('List lenght error in line {}'.format(line_num))
            continue

        line_as_list = [elem.strip() for elem in line_as_list]
        code = line_as_list[0]
        plant_title = line_as_list[1].lower()
        usage_area_keys = line_as_list[4].split(',')
        try:
            usage_area_keys = [int(elem.strip()) for elem in usage_area_keys if elem]
        except:
            print(usage_area_keys)
            raise Exception
        usage_area_keys = set(usage_area_keys)

        try:
            code = int(code)
            plant_keys.append(code)
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

        synonyms = line_as_list[2].split(',')
        synonyms = [elem.strip().lower() for elem in synonyms if
                    elem.lower().strip() != plant.title.lower().strip() and elem.strip() != ""]
        synonyms = set(synonyms)

        for synonym in plant.synonyms.all():
            if synonym.synonym not in synonyms or synonym.synonym.lower() == plant.title.lower() or synonym.synonym.strip() == "":
                synonym.delete()
                print('Synonym {} deleted for plant with code {} and title {}'.format(synonym.synonym, plant.code,
                                                                                      plant.title))

        for synonym_text in synonyms:
            existing_synonyms = plant.synonyms.all().values_list('synonym', flat=True)
            if not synonym_text in existing_synonyms:
                try:
                    models.Synonym.objects.create(plant=plant, synonym=synonym_text)
                    print('Added synonym {} for plant {} with code {}'.format(synonym_text, plant.title, plant.code))
                except ValidationError as e:
                    print(e)

        for usage_area_key in usage_area_keys:
            try:
                usage_area = models.UsageArea.objects.get(code=usage_area_key)
            except:
                print('Usage area not found {} on line {}'.format(usage_area_key, line_num))
                continue
            if usage_area.status != POST_STATUS_PUBLISHED:
                usage_area.status = POST_STATUS_PUBLISHED
                usage_area.save()
            if not usage_area in plant.usage_areas.all():
                plant.usage_areas.add(usage_area)
                print(
                    'Usage area added "{0}" to plant "{1}" in line:{2}'.format(usage_area.title, plant.title, line_num))

        for usage_area in plant.usage_areas.all():
            if usage_area.code not in usage_area_keys:
                plant.usage_areas.remove(usage_area)
                print('Usage area with code {} and title {} removed for plant {}'.format(usage_area.code,
                                                                                         usage_area.title, plant.title))

        wikipedia_link = line_as_list[3].lower().strip()

        if plant.wikipedia_link != wikipedia_link:
            plant.wikipedia_link = wikipedia_link
            plant.save()

for code in models.Plant.objects.all().values_list('code', flat=True):
    if code not in plant_keys:
        plant = models.Plant.objects.get(code=code)
        txt = "deleted plant title={}, code={}".format(plant.title, plant.code)
        plant.delete()
        print(txt)

for usage_area in models.UsageArea.objects.annotate(plant_count=Count('plants')):
    if usage_area.plant_count == 0:
        print('Deleted usage area', usage_area)
        usage_area.delete()
