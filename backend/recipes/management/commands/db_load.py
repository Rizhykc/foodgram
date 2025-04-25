import os
from csv import reader

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Автоматически заполняем базу данных списками ингредиентов и тегов"""

    help = 'Загрузка данных из CSV-файлов в базу данных'

    def load_data_from_csv(self, file_path, model, field_mapping):
        objects_to_create = []
        try:
            with open(file_path, encoding='utf-8') as csv_file:
                csv_reader = reader(csv_file)
                for row in csv_reader:
                    data = {
                        field: row[index].strip()
                        for index, field in field_mapping.items()
                    }
                    objects_to_create.append(model(**data))
            model.objects.bulk_create(objects_to_create)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Данные в {model.__name__} загружены!'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка при обработке файла {file_path}: {e}'
                )
            )

    def handle(self, *args, **options):
        """Чтение ingredients.csv и tags.csv и их загрузка в базу данных."""
        ingredients_file_path = os.path.join(
            settings.BASE_DIR, 'data', 'ingredients.csv'
        )
        self.load_data_from_csv(
            file_path=ingredients_file_path,
            model=Ingredient,
            field_mapping={0: 'name', 1: 'measurement_unit'},
        )
        tags_file_path = os.path.join(settings.BASE_DIR, 'data', 'tags.csv')
        self.load_data_from_csv(
            file_path=tags_file_path,
            model=Tag,
            field_mapping={0: 'name', 1: 'slug'},
        )
