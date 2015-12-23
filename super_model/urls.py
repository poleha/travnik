from django.conf.urls import url
from . import views

urlpatterns = [
url(r'^history/ajax_save/$', views.HistoryAjaxSave.as_view(), name='history-ajax-save'),
url(r'^comment/(?P<comment_pk>\d+)/confirm/(?P<key>[a-z0-9_./]{1,})/$', views.CommentConfirm.as_view(), name='comment-confirm'),
url(r'^comment/get_confirm_form_ajax/$', views.CommentGetConfirmFormAjax.as_view(), name='comment-get-confirm-form-ajax'),
url(r'^comment/do_confirm_ajax/$', views.CommentDoConfirmAjax.as_view(), name='comment-do-confirm-ajax'),
url(r'^get_ajax_login_form/$', views.GetAjaxLoginFormView.as_view(), name='get-ajax-login-form'),
url(r'^ajax_login/$', views.AjaxLoginView.as_view(), name='ajax-login'),
url(r'^comment/get_tiny_ajax/$', views.CommentGetTinyAjax.as_view(), name='comment-get-tiny-ajax'),
url(r'^comment/show_marked_users_ajax/$', views.CommentShowMarkedUsersAjax.as_view(), name='comment-show-marked-users-ajax'),
url(r'^unsubscribe/(?P<email>[0-9a-zA-Z.\-_@]+)/(?P<key>[0-9A-Za-z]+)/$', views.UnsubscribeView.as_view(), name='unsubscribe'),
url(r'^user_profile/$', views.UserProfileView.as_view(), name='user-profile'),
url(r'^user/(?P<pk>\d+)/$', views.UserDetailView.as_view(), name='user-detail'),
url(r'^user/comments/(?P<pk>\d+)/$', views.UserCommentsView.as_view(), name='user-comments'),
url(r'^user/karma/(?P<pk>\d+)/$', views.UserKarmaView.as_view(), name='user-karma'),
url(r'^user/activity/(?P<pk>\d+)/$', views.UserActivityView.as_view(), name='user-activity'),


url(r'^signup/$', views.SuperSignupView.as_view(), name='signup'),
url(r'^login/$', views.SuperLoginView.as_view(), name='login'),
url(r'^logout/$', views.SuperLogoutView.as_view(), name='logout'),
url(r'^password_change/$', views.SuperPasswordChangeView.as_view(), name='password-change'),
url(r'^password_reset/$', views.SuperPasswordResetView.as_view(), name='password-reset'),
url(r'^password_reset_done/$', views.SuperPasswordResetDoneView.as_view(), name='password-reset-done'),
url(r"^password_reset_from_key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
    views.SuperPasswordResetFromKeyView.as_view(),
    name="password-reset-from-key"),
url(r"^password_reset_from_key_done/$", views.SuperPasswordResetFromKeyDoneView.as_view(),
    name="password-reset-from-key-done"),
url(r"^email/$", views.SuperEmailView.as_view(), name="account_email"),
url(r"^confirm-email/(?P<key>\w+)/$", views.SuperConfirmEmailView.as_view(), name="account_confirm_email"),
#social
url(r'^social_login/$', views.SuperSocialSignupView.as_view(), name='socialaccount_signup'), #Перекрываем их url. Иначе не получилось.
url(r'^login_cancelled/$', views.SuperLoginCancelledView.as_view(),
    name='socialaccount_login_cancelled'),
url(r'^login_error/$', views.SuperLoginErrorView.as_view(), name='socialaccount_login_error'),
url(r'^connections/$', views.SuperConnectionsView.as_view(), name='socialaccount_connections'),

    ]