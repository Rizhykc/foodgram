from rest_framework import serializers

from foodgram.constants import MIN_UNIT, NULL
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from recipes.validators import (validate_amount, validate_favorite,
                                validate_ingredients, validate_shopping_cart,
                                validate_subscription)
from users.models import CustomUser, Subscription
from users.serializers import Base64ImageField as Base64
from users.serializers import CustomUserSerializer


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
    """"""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_UNIT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        """."""
        return validate_amount(self, value)


class RecipeReadSerializer(serializers.ModelSerializer):
    """"""
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'ingredients', 'tags', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = fields


class RecipeWriteSerializer(serializers.ModelSerializer):
    """"""
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64()
    cooking_time = serializers.IntegerField(min_value=MIN_UNIT)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        """."""
        return validate_ingredients(self, value)

    def create(self, validated_data):
        """."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags_data)
        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """."""
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        if tags_data is not None:
            instance.tags.set(tags_data)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._create_recipe_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def _create_recipe_ingredients(self, recipe, ingredients_data):
        """."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients_data
        ])

    def to_representation(self, instance):
        """."""
        return RecipeReadSerializer(instance, context=self.context).data


class MiniRecipeSerializer(serializers.ModelSerializer):
    image = Base64(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):

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


class SubscriptionGetSerializer(serializers.ModelSerializer):

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
        return MiniRecipeSerializer(
            instance.recipe
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):

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
