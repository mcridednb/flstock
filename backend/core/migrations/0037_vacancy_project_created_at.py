# Generated by Django 5.0.6 on 2024-06-26 02:45

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_category_order_subcategory_order_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vacancy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vacancy_id', models.IntegerField(unique=True)),
                ('title', models.CharField(max_length=255)),
                ('salary_from', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('salary_to', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('offers', models.IntegerField(default=0)),
                ('date_published', models.BigIntegerField()),
                ('currency_symbol', models.CharField(default='', max_length=255)),
                ('company', models.CharField(default='', max_length=255)),
                ('url', models.URLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Вакансия',
                'verbose_name_plural': 'Вакансии',
            },
        ),
        migrations.AddField(
            model_name='project',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
