import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, Tag,
    ShoppingCart, Favorite,
)
from users.models import Subscription

User = get_user_model()


class TokenCreateSerializer(serializers.Serializer):
    def create(self, validated_data):
        user = validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return {'auth_token': token.key}


class UserCreateSerializer(serializers.ModelSerializer):
    """Регистрация нового пользователя."""

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.'
            )
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким именем уже существует.'
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password'
        )
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True, 'required': True},
        }


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.subscriptions.filter(author=obj).exists()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar', 'password')
        read_only_fields = ('id', 'is_subscribed')
        extra_kwargs = {'password': {'write_only': True}}


class Base64ImageField(serializers.ImageField):
    """Принимает изображение в виде base64-строки."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            fmt, img = data.split(';base64,')
            ext = fmt.split('/')[-1]
            data = ContentFile(base64.b64decode(img), name=f'temp.{ext}')
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return getattr(obj, 'is_favorited',
                       Favorite.objects.filter(user=user, recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return getattr(obj, 'is_in_shopping_cart',
                       ShoppingCart.objects.filter(user=user,
                                                   recipe=obj).exists())

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('is_favorited', 'is_in_shopping_cart')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient')
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('author', 'name', 'image', 'text',
                  'ingredients', 'tags', 'cooking_time')

    def validate(self, attrs):
        """При partial_update требуем tags и ingredients."""
        if self.instance and not {'tags', 'ingredients'} <= attrs.keys():
            raise serializers.ValidationError(
                'При обновлении нужно передать tags и ingredients полностью.'
            )
        return attrs

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть положительным числом.')
        return value

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один ингредиент.')
        ids = [item['ingredient'].id for item in data]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')
        return data

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один тег.')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return tags

    @staticmethod
    def _set_tags_and_ingredients(recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(recipe=recipe,
                             ingredient=item['ingredient'],
                             amount=item['amount'])
            for item in ingredients
        ])

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._set_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.recipe_ingredients.all().delete()
        self._set_tags_and_ingredients(instance, tags, ingredients)
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionCreateSerializer(serializers.Serializer):
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def validate_author(self, author):
        user = self.context['request'].user
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.')
        return author

    def create(self, validated_data):
        user = self.context['request'].user
        author = validated_data['author']
        Subscription.objects.create(user=user, author=author)
        return author


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and user.subscriptions.filter(author=obj).exists())

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get('recipes_limit')
        qs = obj.recipes.all()
        if limit:
            qs = qs[:int(limit)]
        return ShortRecipeSerializer(qs, many=True).data
