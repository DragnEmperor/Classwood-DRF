# Generated by Django 4.0.4 on 2023-03-07 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_classroommodel_teachers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classroommodel',
            name='teachers',
            field=models.ManyToManyField(blank=True, related_name='teachers_of_class', to='api.staffmodel'),
        ),
    ]
