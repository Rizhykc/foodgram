import base64
import uuid

from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework.serializers import (BooleanField, CharField, ImageField,
                                        IntegerField, ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField,
                                        SlugRelatedField, ValidationError)

from api.validators import (validate_recipe, validate_shopping_cart,
                            validate_subscription)
from foodgram.constants import MAX_IMAGES, NULL
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import CustomUser, Subscription


class Base64ImageField(ImageField):

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


class AvatarSerializer(ModelSerializer):

    avatar = Base64ImageField(allow_null=True, file_prefix='avatar')

    class Meta:
        model = CustomUser
        fields = ('avatar',)


class CustomUserSerializer(UserSerializer):

    password = CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password',)

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class CustomUserGetSerializer(UserSerializer):

    is_subscribed = SerializerMethodField()
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


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(ModelSerializer):

    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if not value:
            ValidationError('Количество не может быть пустым.')
        return value


class RecipeIngredientGetSerializer(ModelSerializer):

    id = IntegerField(source='ingredient.id')
    name = CharField(source='ingredient.name')
    measurement_unit = CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeCreateSerializer(ModelSerializer):

    image = Base64ImageField(required=True, file_prefix='recipe')
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = SlugRelatedField(
        slug_field='username', read_only=True
    )

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'tags',
                  'image', 'name', 'text', 'cooking_time',)
        read_only_fields = ('author',)

    def validate(self, data):
        return validate_recipe(self, data)

    def add_ingredients(self, model, recipe, ingredients):
        model.objects.bulk_create(
            (
                model(
                    recipe=recipe,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            )
        )

    def _update_tags_and_ingredients(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(recipe=recipe, **ingredient)
                for ingredient in ingredients
            ]
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        validated_data.pop('author', None)
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        self._update_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        self._update_tags_and_ingredients(instance, tags, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeGetSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class RecipeGetSerializer(ModelSerializer):

    author = CustomUserGetSerializer(read_only=True, many=False)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientGetSerializer(
        read_only=True, many=True, source='recipe_ingredients')
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = SerializerMethodField(method_name='get_is_favorited')
    is_in_shopping_cart = SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def user_status(self, obj, model_class):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and model_class.objects.filter(recipe=obj,
                                           user=request.user).exists()
        )

    def get_is_favorited(self, obj):
        return self.user_status(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.user_status(obj, ShoppingCart)


class MiniRecipeSerializer(ModelSerializer):
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionSerializer(ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate_author(self, data):
        return validate_subscription(self, data)

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionGetSerializer(
            instance.author, context={'request': request}
        ).data


class SubscriptionGetSerializer(ModelSerializer):

    recipes = SerializerMethodField(method_name='get_recipes')
    recipes_count = SerializerMethodField(default=NULL)
    is_subscribed = BooleanField(default=True)

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar',
        )

    def get_recipes(self, author):
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


class FavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        if Favorite.objects.filter(**data).exists():
            raise ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return MiniRecipeSerializer(
            instance.recipe
        ).data


class ShoppingCartSerializer(ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate(self, data):
        return validate_shopping_cart(self, data)

    def to_representation(self, instance):
        return MiniRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
