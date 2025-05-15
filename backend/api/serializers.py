import base64
import uuid

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer as CreateSerializer
from djoser.serializers import UserSerializer
from rest_framework import serializers

from api.validators import (validate_favorite, validate_password,
                            validate_recipe, validate_shopping_cart,
                            validate_subscription)
from foodgram.constants import MAX_IMAGES, MAX_UNIT, MIN_UNIT, NULL, PASS
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import CustomUser, Subscription


class Base64ImageField(serializers.ImageField):
    """Загрузка изображения в формате Base64 и конвертация их в файлы."""
    def __init__(self, *args, **kwargs):
        self.file_prefix = kwargs.pop('file_prefix', 'file')
        self.max_filename_length = kwargs.pop(
            'max_filename_length', MAX_IMAGES
        )
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f'{self.file_prefix}_{uuid.uuid4()}.{ext}'
            data = ContentFile(base64.b64decode(imgstr), name=filename)
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватарок пользователей."""
    avatar = Base64ImageField(allow_null=True, file_prefix='avatar')

    class Meta:
        model = CustomUser
        fields = ('avatar',)


class CustomUserCreateSerializer(CreateSerializer):
    """Кастомный сериализатор для регистрации пользователей."""
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Пароль должен быть не менее 8 символов"
    )

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password',)
        extra_kwargs = {
            'password': {'min_length': PASS},
            'email': {'required': True}
        }

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)

    def validate(self, data):
        return validate_password(self, data)


class CustomUserSerializer(UserSerializer):
    """Кастомный сериализатор для просмотра пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(allow_null=True, required=False)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'avatar', 'is_subscribed', )

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.subscriber.filter(author=author).exists()
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор связи рецепта и ингредиента (только чтение)."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_UNIT, max_value=MAX_UNIT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов co всеми связанными данными."""
    author = CustomUserSerializer(read_only=True)
    tag = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'ingredients', 'tag', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = fields


class RecipeWriteSerializer(serializers.ModelSerializer):
    """"Сериализатор для создания/обновления рецептов."""
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tag = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_UNIT,
                                            max_value=MAX_UNIT)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tag', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_recipe(self, value):
        return validate_recipe(self, value)

    def create(self, validated_data):
        """Создает рецепт c ингредиентами и тегами."""
        ingredients_data = validated_data.pop('ingredients')
        tag_data = validated_data.pop('tag')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tag_data)
        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт, ингредиенты и теги."""
        ingredients_data = validated_data.pop('ingredients', None)
        tag_data = validated_data.pop('tag', None)
        if tag_data is not None:
            instance.tag.set(tag_data)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._create_recipe_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def _create_recipe_ingredients(self, recipe, ingredients_data):
        """Создает связи между рецептом и ингредиентами."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients_data
        ])

    def to_representation(self, instance):
        """Возвращает данные через сериализатор чтения рецептов."""
        return RecipeReadSerializer(instance, context=self.context).data


class MiniRecipeSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецептов для избранного и корзины."""
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписок."""
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate_author(self, data):
        return validate_subscription(self, data)

    def to_representation(self, instance):
        """Возвращает данные через сериализатор получения информации."""
        request = self.context.get('request')
        return SubscriptionGetSerializer(
            instance.author, context={'request': request}
        ).data


class SubscriptionGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения информации o подписках."""
    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(default=NULL)
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar',
        )

    def get_recipes(self, author):
        """Возвращает рецепты автора c возможностью лимита."""
        recipes = author.recipes.all()
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        return MiniRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов в избранное."""
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        extra_kwargs = {
            'user': {'write_only': True},
            'recipe': {'write_only': True},
        }

    def validate(self, data):
        return validate_favorite(self, data)

    def to_representation(self, instance):
        """Возвращает упрощенные данные рецепта."""
        return MiniRecipeSerializer(
            instance.recipe
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов в корзину."""
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate(self, data):
        return validate_shopping_cart(self, data)

    def to_representation(self, instance):
        """Возвращает упрощенные данные рецепта."""
        return MiniRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
