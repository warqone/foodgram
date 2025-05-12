from rest_framework import filters


class IngredientFilter(filters.SearchFilter):
    search_param = 'name'
