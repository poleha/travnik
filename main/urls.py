from django.conf.urls import url
from . import views
#from .feed import LatestBlogEntriesFeed
#from django.views.decorators.cache import cache_page

urlpatterns = [
    url(r'^plant/list/$', views.PostList.as_view(), name='plant-list', kwargs={'post_type': 'plant'}),
    url(r'^plant/create/$', views.PostCreate.as_view(), name='plant-create', kwargs={'post_type': 'plant'}),
    url(r'^plant/update/(?P<pk>\d+)/$', views.PostUpdate.as_view(), name='plant-update', kwargs={'post_type': 'plant'}),
    url(r'^plant/list_ajax/$', views.PostListAjax.as_view(), name='plant-list-ajax', kwargs={'post_type': 'plant'}),

    url(r'^recipe/list/$', views.PostList.as_view(), name='recipe-list', kwargs={'post_type': 'recipe'}),
    url(r'^recipe/create/$', views.PostCreate.as_view(), name='recipe-create', kwargs={'post_type': 'recipe'}),
    url(r'^recipe/update/(?P<pk>\d+)/$', views.PostUpdate.as_view(), name='recipe-update', kwargs={'post_type': 'recipe'}),
    url(r'^recipe/list_ajax/$', views.PostListAjax.as_view(), name='recipe-list-ajax', kwargs={'post_type': 'recipe'}),

    url(r'^login/$', views.ProzdoLoginView.as_view(), name='login'),

]

urlpatterns.append(url(r'^(?P<alias>[a-z0-9_\-]{1,})/$', views.PostDetail.as_view(), kwargs={'action': 'normal'}, name='post-detail-alias'))