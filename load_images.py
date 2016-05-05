import os
import sys


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travnik.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


from main import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage

save_path = os.path.join(settings.MEDIA_ROOT, 'plant')
storage = FileSystemStorage(save_path)

plants = models.Plant.objects.all()
count = 0

for plant in plants:
    try:
        f = open('load_images/' + str(plant.code) + '.jpg', 'rb')
    except:
        f = None
    if f:
        file_name = plant.alias + '.jpg'
        try:
            existing_f = storage.open(file_name)
            print(plant.pk)
        except:
            existing_f = None

        if not existing_f:
            storage.save(file_name, f)
            plant.image = 'plant/' + file_name
            plant.save()
            print(plant)
            count += 1
print(count)



