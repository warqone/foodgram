from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from hashids import Hashids

from recipes import constants

User = get_user_model()
hashids = Hashids(min_length=6, salt=settings.SECRET_KEY)


class Tag(models.Model):
    name = models.CharField(
        max_length=constants.MAX_TITLE_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=constants.MAX_TITLE_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=constants.MAX_TITLE_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=constants.MAX_TITLE_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to=settings.RECIPES_ROOT
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    is_favorited = models.BooleanField(
        'Добавлено в избранное',
        default=False
    )
    is_in_shopping_cart = models.BooleanField(
        'Добавлено в корзину',
        default=False)
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=constants.MAX_TITLE_LENGTH
    )
    text = models.CharField(
        max_length=constants.RECIPE_MAX_LENGTH,
        verbose_name='Описание рецепта'
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (минуты)'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации рецепта'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def get_short_url(self):
        """Генерирует короткую ссылку на рецепт."""
        hashid = hashids.encode(self.id)
        return f"{settings.HOST}/r/{hashid}"

    def __str__(self):
        return f'Рецепт от {self.author.username}: {self.name}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe'
            )
        ]

    def __str__(self):
        return (
            f'{self.amount} {self.ingredient.measurement_unit} '
            f'{self.ingredient.name}')


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='user_favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorite_recipes'
    )
    created = models.DateTimeField(
        verbose_name='Дата добавления в избранное',
        auto_now_add=True
    )

    class Meta:
        unique_together = ('user', 'recipe')
        ordering = ('-created',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    created = models.DateTimeField(
        verbose_name='Дата добавления в корзину',
        auto_now_add=True
    )

    class Meta:
        unique_together = ('user', 'recipe')
        ordering = ('-created',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
