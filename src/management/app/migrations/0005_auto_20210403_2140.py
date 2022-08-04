# Generated by Django 3.1.7 on 2021-04-04 04:40

import django.core.serializers.json
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0004_auto_20210403_0835"),
    ]

    operations = [
        migrations.AlterField(
            model_name="metric",
            name="last_updated",
            field=models.DateTimeField(
                auto_now=True, db_index=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="metric",
            name="properties",
            field=models.JSONField(
                blank=True,
                encoder=django.core.serializers.json.DjangoJSONEncoder,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="package",
            name="last_updated",
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
    ]
