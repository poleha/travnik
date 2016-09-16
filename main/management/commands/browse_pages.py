from django.core.management.base import BaseCommand
from main import models
from super_model import models as super_models
import requests
from django.core.urlresolvers import reverse
import time
from django.conf import settings
from django.core.mail import mail_admins
from cache.decorators import construct_cached_view_key
from django.core.cache import cache
from main.views import PostDetail
from random import shuffle
from main.models import Post

class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        #parser.add_argument('poll_id', nargs='+', type=int)

        # Named (optional) arguments
        parser.add_argument('--full',
            action='store_true',
            dest='full',
            default=False,
            help='Browse all pages')

        parser.add_argument('--show',
                            action='store_true',
                            dest='show',
                            default=False,
                            help='Show visited pages')

        parser.add_argument('--posts',
                            action='store_true',
                            dest='posts',
                            default=False,
                            help='Visit only posts')

        parser.add_argument('--head',
                            action='store_true',
                            dest='head',
                            default=False,
                            help='Visit only posts')

        parser.add_argument('--all',
                            action='store_true',
                            dest='all',
                            default=False,
                            help='Visit only posts')


        parser.add_argument('--sleep_time',
                            dest='sleep_time',
                            type=float,
                            default=0.1,
                            help='Sleep after each visit')

        parser.add_argument('--exec_time',
                            dest='exec_time',
                            type=int,
                            default=60,
                            help='Max execution time')


    def handle(self, *args, **options):
        start_time = time.time()
        count = 0
        sleep_time = options['sleep_time']
        exec_time = options['exec_time']
        visit_posts = options['posts']
        visit_head = options['head']
        visit_all = options['all']

        urls = tuple()

        if visit_head or visit_all:
            urls += (reverse('plant-list'),)
            urls += ('/sitemap.xml',)

        errors = []

        urls_len = len(urls)
        if visit_posts or visit_all:
            urls_len += models.Post.objects.filter(status=super_models.POST_STATUS_PUBLISHED).count()

        for url in urls:
            cur_time = time.time()
            if cur_time - start_time > exec_time:
                break
            count += 1
            absolute_url = '{}{}'.format(settings.SITE_URL, url)
            try:
                for headers in ({}, {'user-agent': 'mobile'}):
                    res = requests.get(absolute_url, headers=headers)
                    if not res.status_code == 200:
                        errors.append('{0}-{1}'.format(url, res.status_code))
                    if sleep_time:
                        time.sleep(sleep_time)
                    if options['show']:
                        print('Visited url {}, {} of {}. Response code: {}'.format(absolute_url, count, urls_len,
                                                                               res.status_code))
            except:
                errors.append('{0}-{1}'.format(url, 'EXCEPTION'))

        if visit_posts or visit_all:
            posts = list(models.Post.objects.filter(status=super_models.POST_STATUS_PUBLISHED))
            shuffle(posts)
            for post in posts:
                cur_time = time.time()
                if cur_time - start_time > exec_time:
                    break
                if not (post.is_recipe or post.is_plant):
                    continue
                count += 1
                absolute_url = url = '{}{}'.format(settings.SITE_URL, post.get_absolute_url())
                alias = getattr(post, 'alias', None)
                if alias:
                    original_key = construct_cached_view_key(PostDetail.get, url=absolute_url, model_class=Post, kwarg='alias',
                                                alias=post.alias)
                else:
                    original_key = construct_cached_view_key(PostDetail.get, url=absolute_url, model_class=Post, kwarg='pk',
                                                    pk=post.pk)
                mobile_key = original_key.replace('flavour_None', 'flavour_mobile')
                full_key = original_key.replace('flavour_None', 'flavour_full')
                for key in (full_key, mobile_key):
                    resp = cache.get(key)
                    if resp is None or options['full']:
                        headers = {}
                        if key == mobile_key:
                            headers['user-agent'] = 'mobile'
                        try:
                            res = requests.get(absolute_url, headers=headers)
                            if res.status_code != 200:
                                errors.append('{0}-{1}'.format(url, res.status_code))

                            if sleep_time:
                                time.sleep(sleep_time)
                            if options['show']:
                                print(
                                    'Visited url {}, {} of {}. Response code: {}'.format(absolute_url, count, urls_len,
                                                                                         res.status_code))
                        except:
                            errors.append('{0}-{1}'.format(url, 'EXCEPTION'))

        if len(errors) > 0:
            mail_admins('Errors during crawling', '\n'.join(errors))
