# Generated by Django 4.0.4 on 2023-03-29 10:10

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_alter_timetablemodel_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetablemodel',
            name='school',
            field=models.ForeignKey(default='', editable=False, on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel'),
        ),
        migrations.AlterField(
            model_name='timetablemodel',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
