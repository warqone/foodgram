from django.contrib.auth import get_user_model, authenticate
from django.core.validators import RegexValidator
from rest_framework import serializers

from recipes.models import Recipe, Tag, Ingredient, RecipeIngredient
from users import constants

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)
            if not user:
                raise serializers.ValidationError(
                    'Неверный email или пароль.', code='authorization')
            data['user'] = user
            return data
        else:
            raise serializers.ValidationError(
                'Необходимо указать email и пароль.', code='authorization')


class SignUpSerializer(serializers.Serializer):
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
        required=True,
        max_length=constants.PASSWORD_LENGTH
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким именем уже существует.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.')
        return value

    def validate_role(self, value):
        if self.context['request'].user.is_admin:
            return value
        return constants.USER

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        return self.context['request'].user.is_authenticated and \
            self.context['request'].user in obj.subscribers.all()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar')
        read_only_fields = ('id',)


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
            'id', 'author', 'name', 'image', 'text', 'ingredients',
            'tags', 'cooking_time', 'pub_date'
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
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = (
            'author', 'name', 'image', 'text', 'ingredients', 'tags',
            'cooking_time')

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
