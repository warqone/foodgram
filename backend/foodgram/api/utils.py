from django.conf import settings
from django.shortcuts import redirect

from recipes.models import hashids


def redirect_to_recipe(request, short_id):
    """Перенаправляет на полный URL рецепта по короткой ссылке."""
    try:
        decoded = hashids.decode(short_id)
        if not decoded:
            return redirect(settings.HOST)

        recipe_id = decoded[0]
        return redirect(f'/recipes/{recipe_id}/')
    except Exception:
        return redirect(settings.HOST)
