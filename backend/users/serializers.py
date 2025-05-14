import base64
import uuid

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer as CreateSerializer
from djoser.serializers import UserSerializer
from rest_framework import serializers

from foodgram.constants import MAX_IMAGES, PASS
from users.models import CustomUser
from users.validators import validate_password


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
