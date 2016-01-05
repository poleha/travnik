from django.contrib import admin
from . import models
from sorl.thumbnail.admin import AdminImageMixin
import reversion
from super_model import models as super_models

class PostAdminMixin(reversion.VersionAdmin):
    readonly_fields = ['post_type']


@admin.register(models.Plant)
class DrugAdmin(AdminImageMixin, PostAdminMixin):
    list_filter = ('status', )
    search_fields = ('title', 'alias', 'body')


@admin.register(models.Recipe)
class DrugAdmin(AdminImageMixin, PostAdminMixin):
    list_filter = ('status', )
    search_fields = ('title', 'alias', 'body')


@admin.register(models.UsageArea)
class DrugAdmin(AdminImageMixin, PostAdminMixin):
    list_filter = ('status', )
    search_fields = ('title', 'alias')


@admin.register(models.Post)
class PostAdmin(PostAdminMixin):
    list_filter = ('status', 'post_type')
    search_fields = ('title', 'alias')

@admin.register(models.History)
class HistoryAdmin(reversion.VersionAdmin):
    list_filter = ('history_type', )


@admin.register(models.UserProfile)
class UserProfileAdmin(AdminImageMixin, reversion.VersionAdmin):
    list_filter = ('role', )
    search_fields = ('user__username', )



@admin.register(models.Mail)
class MailAdmin(reversion.VersionAdmin):
    list_filter = ('mail_type', )


def comment_mass_publish(CommentAdmin, request, queryset):
    queryset.update(status=super_models.COMMENT_STATUS_PUBLISHED)
comment_mass_publish.short_description = "Опубликовать выбранные сообщения"


def comment_mass_unpublish(CommentAdmin, request, queryset):
    queryset.update(status=super_models.COMMENT_STATUS_PENDING_APPROVAL)
comment_mass_unpublish.short_description = "Снять с публикации выбранные сообщения"


@admin.register(models.Comment)
class CommentAdmin(reversion.VersionAdmin):
    list_filter = ('status', 'consult_required', 'confirmed', 'delete_mark' )
    search_fields = ('body', )
    actions = [comment_mass_publish, comment_mass_unpublish]
    readonly_fields = ('post_str', 'parent_str')
    exclude = ('post', 'parent')

    def parent_str(self, instance):
        return instance.parent.__str__()

    parent_str.short_description = 'Parent'

    def post_str(self, instance):
        return instance.post.__str__()

    post_str.short_description = 'Post'