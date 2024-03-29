# Generated by Django 4.0.4 on 2023-03-07 10:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_attachment_attchtype'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attachment',
            old_name='attchType',
            new_name='attachType',
        ),
        migrations.AlterUniqueTogether(
            name='exammodel',
            unique_together={('school', 'classroom', 'subject', 'date_of_exam')},
        ),
    ]
