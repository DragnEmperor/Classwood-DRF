# Generated by Django 4.0.4 on 2023-02-14 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffmodel',
            name='account_no',
            field=models.CharField(default=543219876, max_length=100),
            preserve_default=False,
        ),
    ]