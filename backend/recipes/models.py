from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram.constants import (MAX_LEN, MAX_NAME_LENGTH, MAX_TAG, MAX_UNIT,
                                MIN_UNIT, NAME_INGR, SHORT_LINK)
from users.models import CustomUser


class Tag(models.Model):
    """Модель тегов."""
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_TAG,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=MAX_TAG,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингридиентов."""
    name = models.CharField(
        max_length=NAME_INGR,
        verbose_name='Название ингридиента'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LEN,
        verbose_name='Еденицы измерения'
    )

    class Meta():
        default_related_name = 'ingredients'
        verbose_name = 'Ингридиенты'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецептов."""
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        verbose_name='Изображение рецепта',
        upload_to='recipes/images/'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredient = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tag = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_UNIT,),
                    MaxValueValidator(MAX_UNIT,)],
        verbose_name='Время приготовления в минутах'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    short_link = models.CharField(
        verbose_name='Короткая ссылка',
        max_length=SHORT_LINK,
        blank=True,
        unique=True,
        null=True
    )

    class Meta:
        ordering = ('-pub_date',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}, Автор: {self.author}'


class RecipeIngredient(models.Model):
    """Модель ингредиентов для рецепта пользователя."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_UNIT,),
                    MaxValueValidator(MAX_UNIT,)],
        verbose_name='Количество ингредиентов'
    )

    class Meta:
        ordering = ('ingredient', )
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты рецепта'
        default_related_name = 'recipe_ingredients'

    def __str__(self):
        return f'Ингредиенты для рецепта {self.recipe}'


class BaseFavoriteShoppingCart(models.Model):
    """Базовая модель для избранных рецептов и списка покупок."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True


class Favorite(BaseFavoriteShoppingCart):
    """Модель избранных рецептов пользователя."""

    class Meta:
        ordering = ('user',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorites',
            ),
        )

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном у {self.user}'


class ShoppingCart(BaseFavoriteShoppingCart):
    """Модель списка покупок пользователя."""

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        default_related_name = 'shopping_carts'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart',
            ),
        )

    def __str__(self):
        return f'Список покупок {self.user} для рецепта {self.recipe}'
