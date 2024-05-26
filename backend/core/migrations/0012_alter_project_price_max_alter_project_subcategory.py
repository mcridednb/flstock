# Generated by Django 5.0.6 on 2024-05-26 22:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_project_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='price_max',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='subcategory',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='core.subcategory'),
            preserve_default=False,
        ),
    ]