from django.contrib.auth import get_user_model

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets, permissions, pagination, response, status, filters)
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action

from api import serializers
from api.permissions import IsAdminOnly, IsAuthorOrReadOnly
from api.serializers import (
    SignUpSerializer, LoginSerializer,
    TagSerializer, IngredientSerializer,
    RecipeSerializer, RecipeCreateUpdateSerializer)
from recipes.models import Recipe, Tag, Ingredient

User = get_user_model()


# class LoginLogoutView(viewsets.ViewSet):
#     permission_classes = (permissions.AllowAny,)

#     @action(detail=False, methods=['post'])
#     def login(self, request):
#         serializer = LoginSerializer(
#             data=request.data, 
#             context={'request': request}
#         )
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']
#         token, created = Token.objects.get_or_create(user=user)
#         return response.Response(
#             {'auth_token': token.key}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = pagination.LimitOffsetPagination
    queryset = User.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^username',)
    serializer_class = serializers.UserSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(detail=False, methods=['get', 'patch'], url_path='me',
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return response.Response(
                serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(
            user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ModelViewSet):
    """
    Обрабатывает теги. Только чтение для всех пользователей.
    Фильтрация по slug.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['slug']
    pagination_class = None
    http_method_names = ['get']


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Обрабатывает ингредиенты. Только чтение для всех пользователей.
    Поиск по названию ингредиента.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']
    pagination_class = None
    http_method_names = ['get']


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Обрабатывает рецепты с полным CRUD для авторизованных пользователей.
    Фильтрация по: тегам, автору, избранному, списку покупок.
    """
    queryset = Recipe.objects.all()
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly & IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tags__slug', 'author__id']
    search_fields = ['name', 'text']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.query_params.get('is_favorited'):
            queryset = queryset.filter(favorites__user=self.request.user)

        if self.request.query_params.get('is_in_shopping_cart'):
            queryset = queryset.filter(shopping_carts__user=self.request.user)

        return queryset.distinct()
