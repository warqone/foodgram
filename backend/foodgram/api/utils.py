from django.shortcuts import get_object_or_404, redirect
from django.conf import settings

from recipes.models import Recipe, hashids


def redirect_to_recipe(request, short_id):
    """Перенаправляет на полный URL рецепта по короткой ссылке."""
    try:
        decoded = hashids.decode(short_id)
        if not decoded:
            return redirect(settings.HOST)

        recipe_id = decoded[0]
        recipe = get_object_or_404(Recipe, id=recipe_id)
        return redirect(f'/recipes/{recipe.id}/')
    except Exception:
        return redirect(settings.HOST)
