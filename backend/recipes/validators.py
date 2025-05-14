from django.core.exceptions import ValidationError

from foodgram.constants import MIN_UNIT
from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import Subscription


def validate_subscription(serializer, data):
    """Проверяет возможность подписки."""
    user = data['user']
    author = data['author']
    if user == author:
        raise ValidationError('Нельзя подписаться на самого себя')
    if Subscription.objects.filter(user=user, author=author).exists():
        raise ValidationError('Вы уже подписались на этого автора')
    return data


def validate_recipe(serializer, data):
    """Проверяет корректное создание рецепта."""
    ingredients = data.get('ingredients', [])
    if not ingredients:
        raise ValidationError(
            'Рецепт должен содержать хотя бы один ингредиент.'
        )
    ingredient_ids = [item['id'] for item in ingredients]
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValidationError('Ингредиенты должны быть уникальными.')
    for ingredient in ingredients:
        if 'amount' not in ingredient or not ingredient['amount']:
            raise ValidationError(
                'Для каждого ингредиента должно быть указано количество.'
            )

    tags = data.get('tags', [])
    if not tags:
        raise ValidationError('Рецепт должен содержать хотя бы один тег.')

    cooking_time = data.get('cooking_time')
    if cooking_time < MIN_UNIT:
        raise ValidationError(
            f'Время приготовления должно быть не меньше {MIN_UNIT} минуты'
        )

    name = data.get('name')
    author = serializer.context['request'].user
    if not serializer.instance and (Recipe.objects
                                    .filter(name=name, author=author)
                                    .exists()):
        raise ValidationError('Вы уже добавили этот рецепт.')

    return data


def validate_shopping_cart(serializer, data):
    """Проверяет возможность добавления в корзину."""
    user = data['user']
    recipe = data['recipe']
    if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
        raise ValidationError('Рецепт уже добавлен в корзину')
    return data


def validate_amount(serializer, data):
    """Проверяет количество ингредиента."""
    if not data:
        ValidationError('Количество не может быть пустым.')
    return data


def validate_favorite(serializer, data):
    """Проверяет возможность добавления в избранное."""
    if Favorite.objects.filter(**data).exists():
        raise ValidationError(
            'Рецепт уже добавлен в избранное.'
        )
    return data
