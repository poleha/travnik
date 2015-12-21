from django import template
from super_model.templatetags import super_model as super_tags

register = template.Library()


get_child_comments = register.inclusion_tag('main/widgets/_get_child_comments.html', takes_context=True)(super_tags.get_child_comments)

get_comment = register.inclusion_tag('main/widgets/_get_comment.html', takes_context=True)(super_tags.get_comment)

recent_comments = register.inclusion_tag('main/widgets/_comments_portlet.html')(super_tags.recent_comments)

best_comments = register.inclusion_tag('main/widgets/_comments_portlet.html')(super_tags.best_comments)
