from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """
    Кастомный фильтр для рецептов
    """
    tags = filters.CharFilter(
        field_name='tags__slug', method='filter_tags')
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'tags']

    def filter_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags')
        return queryset.filter(tags__slug__in=tags)

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset
