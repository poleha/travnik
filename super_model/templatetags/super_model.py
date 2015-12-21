from .. import models
from django.utils.module_loading import import_string
from ..app_settings import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models.aggregates import Count

Comment = import_string(settings.BASE_COMMENT_CLASS)

def get_child_comments(context):
    res = {}
    comment = context['comment']
    children_list = comment.get_children_tree
    res['children'] = children_list
    res['request'] = context['request'] #Поскольку мы будем вызывать get_comment, требующий request, нам нужно,
    # чтобы request был доступен. Иначе _get_child_comments не получит request тк это inclusion tag, а request
    # доступен в контексте view
    res['show_as_child'] = True
    return res


def get_comment(context, comment):
    res = {}
    request = context['request']
    show_as_child = context.get('show_as_child', False)
    res['show_as_child'] = show_as_child
    res['show_tree'] = context.get('show_tree', False)

    res['comment'] = comment
    #res['is_author'] = comment.is_author(request=request)


    res['can_unmark'] = comment.show_undo_action_button(history_type=models.HISTORY_TYPE_COMMENT_RATED, request=request)
    res['can_uncomplain'] = comment.show_undo_action_button(history_type=models.HISTORY_TYPE_COMMENT_COMPLAINT, request=request)



    if not res['can_uncomplain']:
        res['can_mark'] = comment.show_do_action_button(history_type=models.HISTORY_TYPE_COMMENT_RATED, request=request)
    else:
        res['can_mark'] = False


    #if show_as_child:
    res['comment_class'] = 'single-comment-with-level-{0}'.format(comment.get_tree_level)
    res['user'] = request.user
    #else:
    #    res['comment_class'] = 'single-comment-with-level-{0}'.format(0)
    return res


def recent_comments():
    res = {}
    comments = Comment.objects.get_available().order_by('-created')[:10]
    res['comments'] = comments
    res['portlet_type'] = 'recent_comments'
    res['cache_duration'] = 60 * 60 * 2
    return res


def best_comments():
    res = {}
    date = timezone.now() - timedelta(days=settings.BEST_COMMENTS_DAYS)
    comments = Comment.objects.filter(history_comment__history_type=models.HISTORY_TYPE_COMMENT_RATED, created__gte=date).annotate(hist_count=Count('history_comment')).order_by('-hist_count')[:10]

    res['comments'] = comments
    res['portlet_type'] = 'best_comments'
    res['cache_duration'] = 60 * 60 * 24
    return res