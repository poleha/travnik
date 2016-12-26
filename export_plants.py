#!/usr/bin/env python

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travnik.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

from main import models

plants = models.Plant.objects.get_available()

for plant in plants:
    print("{}|{}|{}|{}".format(
        plant.code,
        plant.title,
        ','.join(plant.synonyms.values_list('synonym', flat=True)),
        len(plant.body)
    )
    )
