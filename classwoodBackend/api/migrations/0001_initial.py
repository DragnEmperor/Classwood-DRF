# Generated by Django 4.0.4 on 2023-02-06 15:52

import api.models
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accounts',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Account',
                'verbose_name_plural': 'Accounts',
            },
        ),
        migrations.CreateModel(
            name='SchoolModel',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('school_name', models.CharField(max_length=100)),
                ('school_phone', models.CharField(max_length=13, validators=[django.core.validators.RegexValidator(message="Entered mobile number isn't in a right format!", regex='^[0-9]{10,13}$')])),
                ('school_address', models.CharField(max_length=100)),
                ('school_city', models.CharField(max_length=100)),
                ('school_state', models.CharField(max_length=100)),
                ('school_zipcode', models.CharField(max_length=100)),
                ('school_logo', models.ImageField(blank=True, null=True, upload_to=api.models.school_logo_upload)),
                ('school_website', models.URLField()),
                ('date_of_establishment', models.DateField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StaffModel',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('profile_pic', models.ImageField(blank=True, upload_to=api.models.staff_profile_upload)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('date_of_birth', models.DateField(auto_now_add=True)),
                ('gender', models.CharField(choices=[('1', 'Male'), ('2', 'Female'), ('3', 'Other')], max_length=1)),
                ('mobile_number', models.CharField(max_length=13, validators=[django.core.validators.RegexValidator(message="Entered mobile number isn't in a right format!", regex='^[0-9]{10,13}$')])),
                ('contact_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('date_of_joining', models.DateField()),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
            ],
            options={
                'ordering': ['date_of_joining', 'first_name', 'last_name'],
            },
        ),
        migrations.CreateModel(
            name='ClassroomModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('class_name', models.CharField(max_length=50)),
                ('section_name', models.CharField(max_length=1)),
                ('class_teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.staffmodel')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
                ('sub_class_teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sub_class_teacher', to='api.staffmodel')),
            ],
            options={
                'ordering': ['class_name', 'section_name'],
            },
        ),
        migrations.CreateModel(
            name='BlackListedToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=500)),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='token_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('token', 'user')},
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('subject_pic', models.ImageField(blank=True, upload_to=api.models.subject_profile_upload)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.classroommodel')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
                ('teacher', models.ManyToManyField(related_name='taught_by', to='api.staffmodel')),
            ],
            options={
                'verbose_name': 'Subject',
                'verbose_name_plural': 'Subjects',
                'ordering': ['name'],
                'unique_together': {('name', 'classroom')},
            },
        ),
        migrations.CreateModel(
            name='StudentModel',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('profile_pic', models.ImageField(blank=True, upload_to=api.models.student_profile_upload)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(choices=[('1', 'Male'), ('2', 'Female'), ('3', 'Other')], max_length=1)),
                ('address', models.TextField(max_length=200)),
                ('contact_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('father_name', models.CharField(max_length=50)),
                ('mother_name', models.CharField(max_length=50)),
                ('parent_mobile_number', models.CharField(blank=True, max_length=13, validators=[django.core.validators.RegexValidator(message="Entered mobile number isn't in a right format!", regex='^[0-9]{10,13}$')])),
                ('date_of_admission', models.DateField()),
                ('roll_no', models.CharField(max_length=20)),
                ('admission_no', models.CharField(max_length=35)),
                ('className', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.classroommodel', verbose_name='Class')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
            ],
            options={
                'ordering': ['roll_no'],
                'unique_together': {('school', 'roll_no')},
            },
        ),
    ]
