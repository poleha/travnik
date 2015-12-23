from django.contrib.sitemaps import Sitemap
from .models import Plant, Recipe
from django.core.urlresolvers import reverse_lazy

class PostSitemap(Sitemap):
    changefreq = "daily"
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
    changefreq = "weekly"
    priority = 0.7


class RecipeListSitemap(Sitemap):
    def items(self):
        return [self]

    location = reverse_lazy('recipe-list')
    changefreq = "weekly"
    priority = 0.7



class MainPageSitemap(Sitemap):
    def items(self):
        return [self]

    location = reverse_lazy('main-page')
    changefreq = "daily"
    priority = 1.0

sitemaps = {
    'plant-detail': PlantSitemap,
    'recipe-detail': RecipeSitemap,
    'plant-list': PlantListSitemap,
    'recipe-list': RecipeListSitemap,
    'main-page' : MainPageSitemap,
}