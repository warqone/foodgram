from django.urls import include, path
from rest_framework import routers

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
