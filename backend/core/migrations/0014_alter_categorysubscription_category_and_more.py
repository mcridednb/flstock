# Generated by Django 5.0.6 on 2024-05-29 17:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_project_price_max'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categorysubscription',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='category_subscriptions', to='core.category'),
        ),
        migrations.AlterField(
            model_name='categorysubscription',
            name='subcategory',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='category_subscriptions', to='core.subcategory'),
        ),
        migrations.AlterField(
            model_name='categorysubscription',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category_subscriptions', to='core.telegramuser'),
        ),
        migrations.CreateModel(
            name='SourceSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='source_subscriptions', to='core.source')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_subscriptions', to='core.telegramuser')),
            ],
            options={
                'unique_together': {('user', 'source')},
            },
        ),
    ]
