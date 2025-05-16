from django.urls import path, include
from rest_framework import routers

from api.views import (
    TagViewSet, IngredientViewSet, RecipeViewSet, UserViewSet)
from api.utils import redirect_to_recipe


router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('r/<str:short_id>/', redirect_to_recipe, name='short_url'),
]
