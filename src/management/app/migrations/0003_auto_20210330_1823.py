# Generated by Django 3.1.7 on 2021-03-31 01:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20210329_2151'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metric',
            name='key',
            field=models.CharField(db_index=True, max_length=256),
        ),
        migrations.AlterField(
            model_name='package',
            name='package_url',
            field=models.CharField(db_index=True, max_length=256),
        ),
    ]