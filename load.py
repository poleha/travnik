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

usage_areas_dict = {
    1:	'Стоматология',
    2:	'Лечение органов дыхания',
    3:	'Офтальмология',
    4:	'Аллергология',
    5:	'Лечение алкоголизма',
    6:	'Противоопухолевое средство',
    7:	'Противогрибковое средство',
    8:	'Противоглистное средство',
    9:	'Противовирусное средство',
    10:	'Дезинфицирующее средство, антисептик',
    11:	'Антибактериальное средство',
    12:	'Средство, регулирующее функцию органов мочеполовой системы и репродукцию',
    13:	'Лечение сердечно-сосудистой системы',
    14:	'Лечение костной и хрящевой ткани',
    15:	'Источник витаминов и минералов',
    16:	'Анальгетик',
    17:	'Дерматология',
    18:	'Желудочно-кишечное средство',
    19:	'Успокаивающее, снотворное',
    20:	'Повышение иммунитета',
    21:	'Мужское здоровье',
    22:	'Женское здоровье',
    23:	'Лактогонное средство',
}

with open('load.csv', 'r') as file:
    line_num = 0
    for line in file:
        line_num += 1
        line_as_list = line.split(';')

        if not len(line_as_list) == 2:
            print('List lenght error in line {}'.format(line_num))
            continue

        line_as_list = [elem.strip() for elem in line_as_list]
        plant_title = line_as_list[0].title()
        usage_area_keys = line_as_list[1].split(',')
        usage_area_keys = [int(elem.strip()) for elem in usage_area_keys]


        try:
            plant, created = models.Plant.objects.get_or_create(title=plant_title)
        except ValidationError as e:
            print('Validation error "{0}" on creating plant {1} line {2}'.format(e, plant_title, line_num))
            continue

        if plant.status != POST_STATUS_PUBLISHED:
            plant.status = POST_STATUS_PUBLISHED
            plant.save()
            print('Plant created "{0}" in line {1}'.format(plant.title, line_num))

        for usage_area_key in usage_area_keys:
            usage_area, created = models.UsageArea.objects.get_or_create(title=usage_areas_dict[usage_area_key])
            if usage_area.status != POST_STATUS_PUBLISHED:
                usage_area.status = POST_STATUS_PUBLISHED
                usage_area.save()
            if not usage_area in plant.usage_areas.all():
                plant.usage_areas.add(usage_area)
                print('Usage area added "{0}" to plant "{1}" in line:{2}'.format(usage_area.title, plant.title, line_num))


