# Generated by Django 4.0.4 on 2023-03-07 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_rename_attchtype_attachment_attachtype_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroommodel',
            name='teachers',
            field=models.ManyToManyField(related_name='teachers_of_class', to='api.staffmodel'),
        ),
    ]
