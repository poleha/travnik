from django import http
from . import models


class PlantSynonymsFallbackMiddleware:

    # Defined as class-level attributes to be subclassing-friendly.
    response_redirect_class = http.HttpResponsePermanentRedirect

    def process_response(self, request, response):
        # No need to check for a redirect for non-404 responses.
        if response.status_code != 404:
            return response

        path = request.path.split('/')
        slug = path[1]

        plant = models.Plant.get_plant_by_slug(slug)

        if plant:
            return self.response_redirect_class(plant.get_absolute_url())

        # No redirect was found. Return the response.
        return response