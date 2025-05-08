import base64

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from recipes.models import Recipe, Tag, Ingredient, RecipeIngredient
from users import constants

User = get_user_model()


class TokenCreateSerializer(serializers.Serializer):

    def create(self, validated_data):
        user = validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return {'auth_token': token.key}


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        max_length=constants.EMAIL_LENGTH)
    username = serializers.CharField(
        required=True,
        max_length=constants.USERNAME_LENGTH,
        validators=[
            RegexValidator(
                regex=constants.USERNAME_VALIDATOR,
                message=(
                    'Имя пользователя может содержать только буквы, цифры и '
                    'символы @/./+/-/_'),
                code='invalid_username'
            )
        ]
    )
    first_name = serializers.CharField(
        required=True,
        max_length=constants.USERNAME_LENGTH
    )
    last_name = serializers.CharField(
        required=True,
        max_length=constants.USERNAME_LENGTH
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        max_length=constants.PASSWORD_LENGTH
    )
    avatar = serializers.ImageField(
        required=False,
    )
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        return self.context['request'].user.is_authenticated and \
            self.context['request'].user in obj.subscribers.all()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.')
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким именем уже существует.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar', 'password')
        read_only_fields = ('id',)
        extra_kwargs = {
            'password': {'write_only': True},
        }


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

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

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        )


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'author', 'name', 'image', 'text', 'ingredients', 'tags',
            'cooking_time'
        )

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть положительным числом')
        return value

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один ингредиент')

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться')

        return ingredients

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)

        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.recipe_ingredients.all().delete()
            recipe_ingredients = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=item['ingredient'],
                    amount=item['amount']
                ) for item in ingredients
            ]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        limit = self.context.get('request').query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
