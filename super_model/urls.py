from django.conf.urls import url
from . import views

urlpatterns = [
url(r'^history/ajax_save/$', views.HistoryAjaxSave.as_view(), name='history-ajax-save'),
url(r'^comment/(?P<comment_pk>\d+)/confirm/(?P<key>[a-z0-9_./]{1,})/$', views.CommentConfirm.as_view(), name='comment-confirm'),
url(r'^comment/get_confirm_form_ajax/$', views.CommentGetConfirmFormAjax.as_view(), name='comment-get-confirm-form-ajax'),
url(r'^comment/do_confirm_ajax/$', views.CommentDoConfirmAjax.as_view(), name='comment-do-confirm-ajax'),
url(r'^get_ajax_login_form/$', views.GetAjaxLoginFormView.as_view(), name='get-ajax-login-form'),
url(r'^ajax_login/$', views.AjaxLoginView.as_view(), name='ajax-login'),
        ]