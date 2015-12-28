from haystack import indexes
from . import models


class BaseIndex(indexes.SearchIndex):
    class Meta:
        abstract = True

    text = indexes.CharField(document=True, use_template=True)
    created = indexes.DateTimeField(model_attr='created')

    def index_queryset(self, using=None):
        return self.get_model().objects.get_available()

class PlantIndex(BaseIndex, indexes.Indexable):

    def get_model(self):
        return models.Plant

class RecipeIndex(BaseIndex, indexes.Indexable):

    def get_model(self):
        return models.Recipe

class CommentIndex(BaseIndex, indexes.Indexable):

    def get_model(self):
        return models.Comment
