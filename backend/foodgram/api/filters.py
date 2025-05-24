from django_filters import rest_framework as rest_filter
from rest_framework import filters

from recipes.models import Recipe


class IngredientFilter(filters.SearchFilter):
    """Фильтр для ингредиентов.

    Фильтрует ингредиенты по названию.
    """

    search_param = 'name'


class RecipeFilter(rest_filter.FilterSet):
    """Фильтр для рецептов.

    Фильтрует рецепты по тегам, автору, избранному и корзине.

    Поля:
        tags - фильтрует по тегам
        author - фильтрует по автору
        is_favorited - фильтрует по избранному
        is_in_shopping_cart - фильтрует по корзине
    """

    tags = rest_filter.AllValuesMultipleFilter(field_name='tags__slug')
    author = rest_filter.NumberFilter(field_name='author__id')
    is_favorited = rest_filter.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = rest_filter.BooleanFilter(method='filter_is_in_cart')

    def filter_is_favorited(self, qs, name, value):
        """Фильтрует по избранному."""
        if not self.request.user.is_authenticated:
            return qs.none() if value else qs
        return qs.filter(
            favorites__user=self.request.user) if value else qs

    def filter_is_in_cart(self, qs, name, value):
        """Фильтрует по корзине."""
        if not self.request.user.is_authenticated:
            return qs.none() if value else qs
        return qs.filter(
            shoppingcarts__user=self.request.user) if value else qs

    class Meta:
        """Метаданные фильтра."""

        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']
