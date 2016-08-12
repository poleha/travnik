import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travnik.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


#from main import models
users = {}


with open('check_recipes.csv') as f:
    for line in f:
        line_list = line.split('|')
        username = line_list[1]
        mark =  line_list[7]
        if username not in users:
            users[username] = []
        users[username].append(mark)


    for username, marks in users.items():
        new_marks = []
        for mark in marks:
            if mark:
                if mark in ['1,5', '1.5']:
                    new_mark = 2
                else:
                    new_mark = int(mark)
                new_marks.append(new_mark)

        old_marks = marks
        marks = new_marks

        if 1 not in marks and 3 in marks:
            average = sum(marks) / len(marks)
            if average > 2 and len(old_marks) > 1:
                print(username)


