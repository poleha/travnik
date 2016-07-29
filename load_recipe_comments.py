import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travnik.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


from main import models

with open('load_comments.csv') as f:
    for line in f:
        line_list = line.split('|')
        if len(line_list) > 5:
            pk = line_list[0]
            comment = line_list[5]
            if comment:
                try:
                    recipe = models.Recipe.objects.get(pk=pk)
                    recipe.comment = comment
                    recipe.save()
                    print('Saved', pk)
                except:
                    print('Not found', pk)
        else:
            print('Line error', line_list)