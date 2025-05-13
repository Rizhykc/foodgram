import os
from csv import reader

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """
    Кастомная команда для загрузки данных из CSV-файлов
    в модели Ingredient и Tag.
    Реализует автоматическое заполнение базы данных.
    """

    help = 'Заполняет базу данных ингредиентами и тегами из CSV'

    def _process_csv_file(self, file_path, model_class, fields_map):
        """Внутренний метод для обработки CSV файла и создания записей."""
        items_to_create = []
        existing_count = 0

        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                csv_data = reader(file)
                for record in csv_data:
                    if not record:
                        continue
                    item_data = {
                        field: record[i].strip()
                        for i, field in fields_map.items()
                    }
                    if model_class == Ingredient:
                        exists = model_class.objects.filter(
                            name=item_data['name'],
                            measurement_unit=item_data['measurement_unit']
                        ).exists()
                    elif model_class == Tag:
                        exists = model_class.objects.filter(
                            slug=item_data['slug']
                        ).exists()

                    if not exists:
                        items_to_create.append(model_class(**item_data))
                    else:
                        existing_count += 1

            model_class.objects.bulk_create(items_to_create)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Загружено {len(items_to_create)}'
                    f'в {model_class.__name__}. '
                    f'Пропущено {existing_count} существующих записей.'
                )
            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
        except Exception as error:
            self.stdout.write(self.style.ERROR(f'Ошибка: {str(error)}'))

    def handle(self, *args, **kwargs):
        """
        Основной метод, вызываемый при выполнении команды.
        Обрабатывает файлы ingredients.csv и tags.csv.
        """
        ingredients_path = os.path.join(
            settings.BASE_DIR,
            'data',
            'ingredients.csv'
        )
        self._process_csv_file(
            file_path=ingredients_path,
            model_class=Ingredient,
            fields_map={
                0: 'name',
                1: 'measurement_unit'
            }
        )

        tags_path = os.path.join(
            settings.BASE_DIR,
            'data',
            'tags.csv'
        )
        self._process_csv_file(
            file_path=tags_path,
            model_class=Tag,
            fields_map={
                0: 'name',
                1: 'slug'
            }
        )
