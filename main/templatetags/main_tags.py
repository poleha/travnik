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

Breadcrumb = namedtuple('Breadcrumb', ['title', 'href'])

@register.inclusion_tag('main/widgets/_breadcrumbs.html', takes_context=True)
def breadcrumbs(context):

    request = context['request']
    url_name = request.resolver_match.url_name
    #kwargs = request.resolver_match.kwargs

    if url_name == 'main-page':
        return

    breadcrumbs_list = [Breadcrumb(title='Главная', href=reverse_lazy('main-page'))]

    if url_name == 'plant-list':
        breadcrumbs_list.append(Breadcrumb(title='Лекарственные растения', href=reverse_lazy('plant-list')))

    elif url_name == 'recipe-list':
        breadcrumbs_list.append(Breadcrumb(title='Рецепты', href=reverse_lazy('recipe-list')))


    elif url_name in ['post-detail-alias', 'post-detail-alias-comment', 'post-detail-pk', 'post-detail-pk-comment']:
        obj = context['obj']
        if obj.is_plant:
            list_title = 'Лекарственные растения'
            href = reverse_lazy('plant-list')
        elif obj.is_recipe:
            list_title = 'Рецепты'
            href = reverse_lazy('recipe-list')

        breadcrumbs_list.append(Breadcrumb(title=list_title, href=href))
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