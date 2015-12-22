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
