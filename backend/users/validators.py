from django.core.validators import RegexValidator
from rest_framework.serializers import ValidationError

from foodgram.constants import PASS

validate_name = RegexValidator(
    regex=r'^[А-Яа-яЁёA-Za-z]+$',
    message='Поле должно содержать только буквы',
    code='invalid_name',
)


def validate_password(serializer, data):
    """Проверка длины пароля."""
    if len(data['password']) < PASS:
        raise ValidationError("Пароль слишком короткий")
    return data
