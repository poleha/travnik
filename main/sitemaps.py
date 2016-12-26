from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse_lazy

from .models import Plant, Recipe, UsageArea


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0

    def lastmod(self, obj):
        return obj.last_modified


class PlantSitemap(PostSitemap):
    def items(self):
        return Plant.objects.get_available()


class RecipeSitemap(PostSitemap):
    def items(self):
        return Recipe.objects.get_available()


class PlantListSitemap(Sitemap):
    def items(self):
        return [self]

    location = reverse_lazy('plant-list')
    changefreq = "daily"
    priority = 1.0


class UsageAreaSitemap(PostSitemap):
    def items(self):
        return UsageArea.objects.get_available()


sitemaps = {
    'plant-detail': PlantSitemap,
    'usage_area-detail': UsageAreaSitemap,
    'recipe-detail': RecipeSitemap,
    'plant-list': PlantListSitemap,
}
