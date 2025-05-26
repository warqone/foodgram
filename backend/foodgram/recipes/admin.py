from django.contrib import admin
from django.db.models import Count

from recipes.models import Ingredient, Recipe, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Администраторское меню для модели Recipe."""

    list_display = ('name', 'author', 'pub_date', 'favorites_count')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username')

    def get_queryset(self, request):
        """Возвращает queryset с дополнительными атрибутами."""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'author').prefetch_related(
            'tags', 'ingredients', 'favorites').annotate(
                favorites_count_cached=Count('favorites'))

    @admin.display(description='Добавлений в избранное')
    def favorites_count(self, obj):
        """Возвращает количество добавлений в избранное."""
        return obj.favorites_count_cached

    @admin.display(description='Короткая ссылка')
    def short_url(self, obj):
        """Возвращает короткую ссылку на рецепт."""
        return obj.get_short_url()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для модели Tag.

    Позволяет просматривать, фильтровать и поиск тегов.
    """

    list_display = ('name', 'slug')
    list_filter = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для модели Ingredient.

    Позволяет просматривать, фильтровать и поиск ингредиентов.
    """

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
