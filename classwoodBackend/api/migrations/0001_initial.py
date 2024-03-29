# Generated by Django 4.0.4 on 2023-02-19 11:06

import api.models
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
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
            name='ClassroomModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('class_name', models.CharField(max_length=50)),
                ('section_name', models.CharField(max_length=1)),
            ],
            options={
                'ordering': ['class_name', 'section_name'],
            },
        ),
        migrations.CreateModel(
            name='FeesDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('due_date', models.DateField()),
                ('description', models.TextField()),
                ('for_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.classroommodel')),
            ],
            options={
                'ordering': ['-due_date'],
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
                ('school_logo_url', models.CharField(blank=True, max_length=500, null=True)),
                ('school_website', models.URLField(blank=True, null=True)),
                ('date_of_establishment', models.DateField(blank=True, null=True)),
                ('staff_limit', models.CharField(default=25, max_length=10)),
                ('student_limit', models.CharField(default=500, max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='StaffModel',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('profile_pic', models.ImageField(blank=True, upload_to=api.models.staff_profile_upload)),
                ('profile_pic_url', models.CharField(blank=True, max_length=500, null=True)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('date_of_birth', models.DateField(auto_now_add=True)),
                ('gender', models.CharField(choices=[('1', 'Male'), ('2', 'Female'), ('3', 'Other')], max_length=1)),
                ('mobile_number', models.CharField(max_length=13, validators=[django.core.validators.RegexValidator(message="Entered mobile number isn't in a right format!", regex='^[0-9]{10,13}$')])),
                ('contact_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('address', models.CharField(max_length=100)),
                ('account_no', models.CharField(max_length=100)),
                ('is_class_teacher', models.BooleanField(default=False)),
                ('date_of_joining', models.DateField()),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
            ],
            options={
                'ordering': ['date_of_joining', 'first_name', 'last_name'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('subject_pic', models.ImageField(blank=True, upload_to=api.models.subject_profile_upload)),
                ('subject_pic_url', models.CharField(blank=True, max_length=500, null=True)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.classroommodel')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
                ('teacher', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='taught_by', to='api.staffmodel')),
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
                ('profile_pic', models.ImageField(blank=True, null=True, upload_to=api.models.student_profile_upload)),
                ('profile_pic_url', models.CharField(blank=True, max_length=500, null=True)),
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
                ('classroom', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.classroommodel', verbose_name='Class')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
                ('subjects', models.ManyToManyField(related_name='learning_subjects', to='api.subject')),
            ],
            options={
                'ordering': ['roll_no'],
                'unique_together': {('school', 'roll_no', 'admission_no', 'classroom')},
            },
        ),
        migrations.AddField(
            model_name='classroommodel',
            name='class_teacher',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.staffmodel'),
        ),
        migrations.AddField(
            model_name='classroommodel',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel'),
        ),
        migrations.AddField(
            model_name='classroommodel',
            name='sub_class_teacher',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sub_class_teacher', to='api.staffmodel'),
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
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('present', models.BooleanField(default=False)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.classroommodel')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.studentmodel')),
            ],
            options={
                'verbose_name': 'Attendance',
                'verbose_name_plural': 'Attendance',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fileName', models.FileField(blank=True, null=True, upload_to=api.models.notice_attach_upload)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
            ],
        ),
        migrations.CreateModel(
            name='PaymentInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_mode', models.CharField(choices=[('1', 'Cheque'), ('2', 'Cash at Counter'), ('3', 'Net Banking'), ('4', 'Demand Draft')], max_length=1)),
                ('payment_date', models.DateField()),
                ('reference', models.CharField(blank=True, max_length=50, null=True)),
                ('fees', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.feesdetails')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.studentmodel')),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'ordering': ['-payment_date'],
                'unique_together': {('student', 'fees')},
            },
        ),
        migrations.CreateModel(
            name='Notice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('date_posted', models.DateTimeField(default=django.utils.timezone.now)),
                ('attachments', models.ManyToManyField(blank=True, to='api.attachment')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.schoolmodel')),
                ('read_by_staff', models.ManyToManyField(blank=True, related_name='read_by_teachers', to='api.staffmodel')),
                ('read_by_students', models.ManyToManyField(blank=True, related_name='read_by_students', to='api.studentmodel')),
            ],
            options={
                'ordering': ['-date_posted'],
                'unique_together': {('author', 'title', 'date_posted')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='classroommodel',
            unique_together={('class_name', 'section_name', 'school')},
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['student', 'date'], name='api_attenda_student_983d64_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together={('student', 'date')},
        ),
    ]
