# Generated by Django 4.0.4 on 2023-02-07 12:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_alter_classroommodel_class_teacher_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classroommodel',
            name='class_teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.staffmodel'),
        ),
    ]
