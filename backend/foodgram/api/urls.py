from django.urls import path, include
from rest_framework import routers

from api.views import (
    LoginLogoutView, TagViewSet, IngredientViewSet, RecipeViewSet, UserViewSet)


router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')

# auth_urls = [
#     path('token/login/', LoginLogoutView, name='login'),
#     path('token/logout/', LoginLogoutView, name='logout'),
# ]

urlpatterns = [
    path('api/auth/', include(auth_urls)),
    path('api/', include(router.urls)),
]
