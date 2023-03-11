# Generated by Django 4.0.4 on 2023-02-21 17:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_exammodel_resultmodel'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notice',
            old_name='author',
            new_name='school',
        ),
        migrations.AlterUniqueTogether(
            name='notice',
            unique_together={('school', 'title', 'date_posted')},
        ),
    ]