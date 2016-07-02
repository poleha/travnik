#!/usr/bin/env python

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travnik.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


from main import models
from bs4 import BeautifulSoup

users = models.User.objects.all()

url = 'http://medavi.ru'

for user in users:
    posts = user.posts.all()
    for post in posts:
        if not post.is_recipe:
            continue
        user = post.user
        recipe = post.obj
        soup = BeautifulSoup(recipe.body, "html5lib")
        body = soup.get_text()
        body = body.replace('\n', ' ').replace('\r', '')
        print("{}|{}|{}|{}|{}".format(user.username, url + user.get_absolute_url(), recipe.title, url + recipe.get_absolute_url(), body))