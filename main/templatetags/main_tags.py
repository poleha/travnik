from django import template
from super_model.templatetags import super_model as super_tags
from django.core.urlresolvers import reverse_lazy
from super_model.forms import SuperSearchForm
from collections import namedtuple


register = template.Library()

MenuItem = namedtuple('MenuItem', ['title', 'url', 'cls'])

get_child_comments = register.inclusion_tag('main/widgets/_get_child_comments.html', takes_context=True)(super_tags.get_child_comments)

get_comment = register.inclusion_tag('main/widgets/_get_comment.html', takes_context=True)(super_tags.get_comment)

recent_comments = register.inclusion_tag('main/widgets/_comments_portlet.html')(super_tags.recent_comments)

best_comments = register.inclusion_tag('main/widgets/_comments_portlet.html')(super_tags.best_comments)

"""
@register.inclusion_tag('main/widgets/_top_menu.html', takes_context=True)
def top_menu(context):

    request = context['request']
    menu_items = []
    view_name = request.resolver_match.view_name
    menu_items.append(MenuItem(title='Главная', url=reverse_lazy('main-page'), cls='active' if view_name=='main-page' else ''))
    menu_items.append(MenuItem(title='Лекарственные растения', url=reverse_lazy('plant-list'), cls='active' if view_name=='plant-list' else ''))
    menu_items.append(MenuItem(title='Рецепты', url=reverse_lazy('recipe-list'), cls='active' if view_name=='cosmetics-list' else ''))

    search_form = SuperSearchForm(request.GET)

    return {'menu_items': menu_items, 'search_form': search_form }
"""


@register.inclusion_tag('main/widgets/_search_form.html', takes_context=True)
def search_form(context):

    request = context['request']
    search_form = SuperSearchForm(request.GET)

    return {'search_form': search_form }



Breadcrumb = namedtuple('Breadcrumb', ['title', 'href'])

@register.inclusion_tag('main/widgets/_breadcrumbs.html', takes_context=True)
def breadcrumbs(context):

    request = context['request']
    url_name = request.resolver_match.url_name
    #kwargs = request.resolver_match.kwargs

    if url_name == 'plant-list':
        return

    breadcrumbs_list = [Breadcrumb(title='Главная', href=reverse_lazy('plant-list'))]

    if url_name in ['post-detail-alias', 'post-detail-alias-comment', 'post-detail-pk', 'post-detail-pk-comment']:
        obj = context['obj']
        breadcrumbs_list.append(Breadcrumb(title=obj.title, href=obj.get_absolute_url()))

    elif url_name == 'user-profile':
        user = context['user']
        breadcrumbs_list.append(Breadcrumb(title='Профиль пользователя {0}'.format(user), href=reverse_lazy('user-profile')))

    elif url_name == 'user-detail':
        user = context['current_user']
        breadcrumbs_list.append(Breadcrumb(title='Информация о пользователе {0}'.format(user), href=reverse_lazy('user-detail', kwargs={'pk': user.pk})))

    elif url_name in ('user-comments', 'user-karma', 'user-activity'):
        user = context['current_user']
        breadcrumbs_list.append(Breadcrumb(title='Информация о пользователе {0}'.format(user), href=reverse_lazy('user-detail', kwargs={'pk': user.pk})))
        if url_name == 'user-comments':
            breadcrumbs_list.append(Breadcrumb(title='Сообщения пользователя {0}'.format(user), href=reverse_lazy('user-comments', kwargs={'pk': user.pk})))
        elif url_name == 'user-karma':
            breadcrumbs_list.append(Breadcrumb(title='Карма пользователя {0}'.format(user), href=reverse_lazy('user-karma', kwargs={'pk': user.pk})))
        elif url_name == 'user-activity':
            breadcrumbs_list.append(Breadcrumb(title='Действия пользователя {0}'.format(user), href=reverse_lazy('user-activity', kwargs={'pk': user.pk})))

    elif url_name == 'search':
        breadcrumbs_list.append(Breadcrumb(title="Поиск по сайту", href=reverse_lazy('search')))

    return {'breadcrumbs_list': breadcrumbs_list}


@register.inclusion_tag('main/widgets/_user_menu.html', takes_context=True)
def user_menu(context):
    user = context['request'].user
    if user.is_regular:
        return
    menu_items = []

    if user.is_admin:
        menu_items.append(MenuItem(title='Создать растение', url=reverse_lazy('plant-create'), cls=''))
        menu_items.append(MenuItem(title='Создать рецепт', url=reverse_lazy('recipe-create'), cls=''))

    return {'menu_items': menu_items}

@register.inclusion_tag('main/widgets/_metatags.html', takes_context=True)
def metatags(context):
    request = context['request']
    url_name = request.resolver_match.url_name
    #kwargs = request.resolver_match.kwargs

    metatags_dict = {}
    metatags_dict['title'] = 'Medavi.ru | Все о лекарственных растениях'
    metatags_dict['keywords'] = 'лекарственные растения, отзывы, рецепты'
    metatags_dict['description'] = 'Сайт о лекарственных растениях и обо всем, что с ними связано'
    metatags_dict['canonical'] = ''

    if url_name == 'main-page':
        pass

    elif url_name == 'plant-list':
        metatags_dict['title'] = 'Medavi | Лекарственные растения'

    elif url_name == 'recipe-list':
        metatags_dict['title'] = 'Medavi | Рецепты'

    elif url_name in ['post-detail-alias', 'post-detail-alias-comment', 'post-detail-pk', 'post-detail-pk-comment', 'post-detail-pk-comment']:
        obj = context['obj']
        if obj.is_plant:
            metatags_dict['title'] = '{0} | Medavi.ru'.format(obj.title)
            metatags_dict['keywords'] = "{0}, растение, рецепты, отзывы".format(obj.title, obj.title)
            metatags_dict['description'] = "Информация о лекарственном растении {0}.".format(obj.title)
        elif obj.is_recipe:
            metatags_dict['title'] = '{0} | Medavi.ru'.format(obj.title)
            metatags_dict['keywords'] = "{0}, рецепт, отзывы, {1}".format(obj.title, obj.title, obj.plant.title)
            metatags_dict['description'] = "Рецепт {0} с использованием лекарственного растения {1}.".format(obj.title, obj.plant.title)

        if 'page' in request.GET or url_name == 'post-detail-pk-comment':
            metatags_dict['canonical'] = obj.get_absolute_url()


    elif url_name == 'user-profile':
        user = context['user']

    elif url_name == 'user-detail':
        user = context['current_user']

    elif url_name in ['user-comments', 'user-karma']:
        user = context['current_user']
        if url_name == 'user-comments':
            pass
        elif url_name == 'user-karma':
            pass

    elif url_name == 'search':
        metatags_dict['title'] = 'Поиск по сайту | Medavi.ru'

    return metatags_dict

@register.inclusion_tag('main/widgets/_user_detail.html')
def user_detail(user):
    return {'user': user}

