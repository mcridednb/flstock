# Generated by Django 5.0.6 on 2024-05-22 18:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_rename_prompt_gptprompt_text_alter_gptprompt_model_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscriptiongptlimits',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='gpt', to='core.subscription'),
        ),
    ]
