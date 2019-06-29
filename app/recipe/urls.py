from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views

ROUTER = DefaultRouter()
ROUTER.register("tags", views.TagViewSet)
ROUTER.register("ingredients", views.IngredientViewSet)

app_name = "recipe"

urlpatterns = [path("", include(ROUTER.urls))]
