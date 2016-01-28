from django.conf.urls import url

from contact_form import views

urlpatterns = [
    url(r'add/$', views.add, name='add'),
    ]