# Generated by Django 4.0.4 on 2023-02-06 17:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_schoolmodel_school_website'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='classroommodel',
            unique_together={('class_name', 'section_name', 'school')},
        ),
    ]
