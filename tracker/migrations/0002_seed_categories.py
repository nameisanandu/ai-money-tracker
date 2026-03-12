# Generated data migration to seed default categories

from django.db import migrations


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('tracker', 'Category')
    default_categories = ['Food', 'Travel', 'Rent', 'Shopping', 'Utilities']
    for name in default_categories:
        Category.objects.get_or_create(name=name)


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model('tracker', 'Category')
    default_categories = ['Food', 'Travel', 'Rent', 'Shopping', 'Utilities']
    Category.objects.filter(name__in=default_categories).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, remove_default_categories),
    ]
