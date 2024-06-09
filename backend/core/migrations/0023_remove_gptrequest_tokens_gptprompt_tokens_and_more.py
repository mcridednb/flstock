# Generated by Django 5.0.6 on 2024-06-07 14:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_payment_idempotent_uuid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gptrequest',
            name='tokens',
        ),
        migrations.AddField(
            model_name='gptprompt',
            name='tokens',
            field=models.PositiveIntegerField(default=2),
        ),
        migrations.AddField(
            model_name='gptprompt',
            name='type',
            field=models.CharField(choices=[('response', 'Отклик'), ('analyze', 'Анализ')], default='analyze', max_length=50),
        ),
        migrations.AddField(
            model_name='transaction',
            name='tokens',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='gptrequest',
            name='type',
            field=models.CharField(choices=[('response', 'Отклик'), ('analyze', 'Анализ'), ('sale_plan', 'План продажи')], default='analyze', max_length=100),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='gpt_request',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.gptrequest'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='subscription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='core.subscription'),
        ),
    ]