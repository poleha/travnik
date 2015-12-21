"""travnik URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#from main.sitemaps import sitemaps
from django.views.decorators.cache import cache_page
from django.contrib.sitemaps.views import sitemap


urlpatterns = [

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^', include('super_model.urls')),
    url(r'^', include('main.urls')),
    url(r'^contact_form/', include('contact_form.urls', namespace="contact_form")),
    #url(r'^sitemap\.xml$', cache_page(60 * 60 * 12)(sitemap), {'sitemaps': sitemaps},
    #name='django.contrib.sitemaps.views.sitemap'),


]

urlpatterns += [url(r'^ckeditor/', include('ckeditor_uploader.urls'))]


if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL,
                document_root=settings.MEDIA_ROOT)

if settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]


