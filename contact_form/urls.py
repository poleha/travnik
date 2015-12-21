from django.conf.urls import patterns, url

from contact_form import views

urlpatterns = patterns('',
    url(r'add/$', views.add, name='add'),
    )