# Generated by Django 4.0.4 on 2023-03-28 09:25

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_timetablemodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('present', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'StaffAttendance',
                'verbose_name_plural': 'StaffAttendance',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='SyllabusModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tag', models.CharField(max_length=50)),
                ('date_of_exam', models.DateField()),
            ],
            options={
                'ordering': ['-date_of_exam'],
            },
        ),
        migrations.RenameModel(
            old_name='Attendance',
            new_name='StudentAttendance',
        ),
        migrations.AlterModelOptions(
            name='studentattendance',
            options={'ordering': ['-date'], 'verbose_name': 'StudentAttendance', 'verbose_name_plural': 'StudentAttendance'},
        ),
        migrations.RemoveIndex(
            model_name='studentattendance',
            name='api_attenda_student_983d64_idx',
        ),
        migrations.AlterField(
            model_name='studentmodel',
            name='subjects',
            field=models.ManyToManyField(blank=True, related_name='learning_subjects', to='api.subject'),
        ),
        migrations.AddIndex(
            model_name='studentattendance',
            index=models.Index(fields=['student', 'date'], name='api_student_student_37c5a6_idx'),
        ),
        migrations.AddField(
            model_name='syllabusmodel',
            name='attachments',
            field=models.ManyToManyField(blank=True, to='api.attachment'),
        ),
        migrations.AddField(
            model_name='syllabusmodel',
            name='classroom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.classroommodel'),
        ),
        migrations.AddField(
            model_name='syllabusmodel',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel'),
        ),
        migrations.AddField(
            model_name='syllabusmodel',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.subject'),
        ),
        migrations.AddField(
            model_name='staffattendance',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel'),
        ),
        migrations.AddField(
            model_name='staffattendance',
            name='staff',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.staffmodel'),
        ),
        migrations.AlterUniqueTogether(
            name='syllabusmodel',
            unique_together={('school', 'classroom', 'subject', 'date_of_exam')},
        ),
        migrations.AddIndex(
            model_name='staffattendance',
            index=models.Index(fields=['staff', 'date'], name='api_staffat_staff_i_daa113_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='staffattendance',
            unique_together={('staff', 'date')},
        ),
    ]