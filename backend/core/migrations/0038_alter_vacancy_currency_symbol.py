# Generated by Django 5.0.6 on 2024-06-26 02:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_vacancy_project_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vacancy',
            name='currency_symbol',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
    ]