# Generated by Django 5.0.6 on 2024-06-24 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_category_telegram_group_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='category',
            name='telegram_group_id',
            field=models.CharField(help_text='-100...', max_length=255, null=True),
        ),
    ]
