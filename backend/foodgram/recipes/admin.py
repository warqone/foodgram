from django.contrib import admin

from recipes.models import Recipe, Tag, Ingredient


admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
