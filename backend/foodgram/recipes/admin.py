from django.contrib import admin

from recipes.models import Ingredient, Recipe, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'pub_date', 'favorites_count')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username')

    @admin.display(description='Добавлений в избранное')
    def favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorite_recipes.count()

    @admin.display(description='Короткая ссылка')
    def short_url(self, obj):
        """Возвращает короткую ссылку на рецепт."""
        return obj.get_short_url()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_filter = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)
