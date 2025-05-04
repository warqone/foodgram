from django.urls import path, include
from rest_framework import routers

from api.views import (
    TagViewSet, IngredientViewSet, RecipeViewSet, UserViewSet)


router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/', include(router.urls)),
]
