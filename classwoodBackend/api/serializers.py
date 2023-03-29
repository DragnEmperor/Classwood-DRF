from rest_framework import serializers
from django.contrib.auth import get_user_model,authenticate
from . import models
from django.utils.translation import gettext as _
from rest_framework.validators import ValidationError
from .function import create_jwt_pair
from .utils import generate_staff_user




class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Accounts
        fields = ("id","email","password")
        
    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)
       
        
# School Serializers
class SchoolSignUpSerializer(serializers.ModelSerializer):
    user= AccountSerializer()
    class Meta:
        model = models.SchoolModel
        fields = "__all__"
        extra_kwargs = {'password':{'write_only':True,'min-length':8}}
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        return models.SchoolModel.objects.create(user=models.Accounts.objects.create_user(**user_data),**validated_data)
    
class SchoolProfileSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    class Meta:
        model = models.SchoolModel
        fields = "__all__"
    
class StaffCreateSerializer(serializers.ModelSerializer):
    user = AccountSerializer(required=False)
    # school = SchoolProfileSerializer()
    class Meta:
        model = models.StaffModel
        fields = "__all__"
    
    def create(self, validated_data):
        # user_data = validated_data.pop('user')
        user_data = generate_staff_user(validated_data.get('first_name'), validated_data.get('mobile_number'), validated_data.get('date_of_joining'))
        return models.StaffModel.objects.create(user=models.Accounts.objects.create_user(**user_data),**validated_data)

class ClassroomCreateSerializer(serializers.ModelSerializer):
    
    def create(self, validated_data):
        teachers = []
        teachers.append(validated_data.get('class_teacher'))
        teachers.append(validated_data.get('sub_class_teacher'))
        classroom = models.ClassroomModel.objects.create(**validated_data)
        classroom.teachers.set(teachers)
        return classroom
    
    class Meta:
        model = models.ClassroomModel
        fields = "__all__"
        
class ClassroomListSerializer(serializers.ModelSerializer):
    strength = serializers.CharField()
    no_of_subjects = serializers.SerializerMethodField()
    no_of_teachers = serializers.SerializerMethodField()
    teachers = serializers.StringRelatedField(many=True)
    
    class Meta:
        model = models.ClassroomModel
        fields = "__all__"
        
    def get_no_of_subjects(self, obj):
        return str(obj.no_of_subjects)
    
    def get_no_of_teachers(self,obj):
        return str(obj.no_of_teachers)
    
        
class SubjectListSerializer(serializers.ModelSerializer):
    classroom = serializers.StringRelatedField()
    teacher = serializers.SerializerMethodField(method_name='get_full_name')
    teacher_id = serializers.SerializerMethodField()
    class Meta:
        model = models.Subject
        fields = "__all__"
    
    def get_full_name(self, obj):
        return obj.teacher.full_name
    
    def get_teacher_id(self,obj):
        return obj.teacher.user.id
    
# class AttachmentSerializer(serializers.ModelSerializer):
#     fileName = serializers.FileField()
#     class Meta:
#         model = models.Attachment
#         fields='__all__'
    
class NoticeCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(child=serializers.FileField(),required=False,write_only=True)
    read_by_students = serializers.ModelField(model_field=models.Notice._meta.get_field('read_by_students'),required=False)
    read_by_staff = serializers.ModelField(model_field=models.Notice._meta.get_field('read_by_staff'),required=False)
    class Meta:
        model = models.Notice
        fields = "__all__"
        
    def create(self, validated_data):
        attachments = []
        if 'attachments' in validated_data:
          attachments = validated_data.pop('attachments')
        notice = models.Notice.objects.create(**validated_data)
        for attach in attachments:
            attachment = models.Attachment.objects.create(fileName=attach,school = validated_data.get('school'),attachType='notice')
            notice.attachments.add(attachment)
        return notice
    
class NoticeListSerializer(serializers.ModelSerializer):
    attachments = serializers.StringRelatedField(many=True)
    read_status = serializers.SerializerMethodField()
    class Meta:
        model = models.Notice
        fields = '__all__'
            
    def get_read_status(self,obj):  
        currentUser = self.context['request'].user
        return obj.read_by_students.filter(user=currentUser).exists() | obj.read_by_staff.filter(user=currentUser).exists()
    
    
    
# Staff Serializers
class StaffListSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    incharge_of = serializers.CharField()
    sub_incharge_of = serializers.StringRelatedField(many=True)
    gender = serializers.SerializerMethodField()
    
    class Meta:
        model = models.StaffModel
        fields = "__all__"
        
    def get_gender(self, obj):
        return obj.get_gender_display
    
    
class SubjectCreateSerializer(serializers.ModelSerializer):
    
    def create(self, validated_data):
        teacher = validated_data.get('teacher')
        classroom = validated_data.get('classroom')
        classroom.teachers.add(teacher)
        return models.Subject.objects.create(**validated_data)
    
    class Meta:
        model = models.Subject
        fields = "__all__" 
        
class StudentCreateSerializer(serializers.ModelSerializer):
    user = AccountSerializer(required=False)
    class Meta:
        model = models.StudentModel
        fields = "__all__"
        
    def create(self, validated_data):
        user_data = generate_staff_user(validated_data.get('first_name'), validated_data.get('parent_mobile_number'), validated_data.get('date_of_admission'))
        subjects = validated_data.pop('subjects')
        instance = models.StudentModel.objects.create(user=models.Accounts.objects.create_user(**user_data),**validated_data)
        instance.subjects.set(subjects)
        return instance
    
class StudentListSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    subjects = serializers.StringRelatedField(many=True)
    classroom = serializers.StringRelatedField()
    total_attendance = serializers.SerializerMethodField()
    month_attendance = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    
    class Meta:
        model = models.StudentModel
        fields = "__all__"
        
    def get_total_attendance(self, obj):
        return str(obj.get_attendance)
    
    def get_month_attendance(self, obj):
        return str(obj.get_month_attendance)
    
    def get_gender(self, obj):
        return obj.get_gender_display
    
class StudentAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StudentAttendance
        fields = "__all__"
        
        
class StudentAttendanceListSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    classroom = serializers.StringRelatedField()
    school = serializers.StringRelatedField()
    class Meta:
        model = models.StudentAttendance
        fields = "__all__"
        
class StaffAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StaffAttendance
        fields = "__all__"
        
        
class StaffAttendanceListSerializer(serializers.ModelSerializer):
    staff = serializers.StringRelatedField()
    classroom = serializers.StringRelatedField()
    school = serializers.StringRelatedField()
    class Meta:
        model = models.StaffAttendance
        fields = "__all__"


class ExamCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(child=serializers.FileField(),required=False,write_only=True)
    class Meta:
        model = models.ExamModel
        fields = "__all__"
        
    def create(self, validated_data):
        attachments = []
        if 'attachments' in validated_data:
          attachments = validated_data.pop('attachments')
        exam = models.ExamModel.objects.create(**validated_data)
        for attach in attachments:
            attachment = models.Attachment.objects.create(fileName=attach,school = validated_data.get('school'),attachType='exam')
            exam.attachments.add(attachment)
        return exam
    
class ExamListSerializer(serializers.ModelSerializer):
    attachments = serializers.StringRelatedField(many=True)
    class Meta:
        model = models.ExamModel
        fields = '__all__'
        
class ResultSerializer(serializers.ModelSerializer):
    
    def validate(self, attrs):
        if(attrs.get('score') > (attrs.get('exam')).max_marks):
            res = ValidationError('Marks Obtained cannot be greater than Max Marks')
            res.status_code = 200
            raise res
        return attrs
        
    class Meta:
        model = models.ResultModel
        fields = "__all__"
        
class SyllabusSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(child=serializers.FileField(),required=False,write_only=True)
    class Meta:
        model = models.SyllabusModel
        fields = "__all__"
        
    def create(self, validated_data):
        attachments = []
        if 'attachments' in validated_data:
          attachments = validated_data.pop('attachments')
        syllabus = models.SyllabusModel.objects.create(**validated_data)
        for attach in attachments:
            attachment = models.Attachment.objects.create(fileName=attach,school = validated_data.get('school'),attachType='syllabus')
            syllabus.attachments.add(attachment)
        return syllabus
    
class SyllabusListSerializer(serializers.ModelSerializer):
    attachments = serializers.StringRelatedField(many=True)
    class Meta:
        model = models.SyllabusModel
        fields = '__all__'
        
class TimeTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TimeTableModel
        fields = "__all__"
        
        
class TimeTableListSerializer(serializers.ModelSerializer):
    subject = serializers.StringRelatedField()
    classroom = serializers.StringRelatedField()
    school =  serializers.StringRelatedField()
    class Meta:
       model = models.TimeTableModel
       fields = "__all__"
       
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(min_length=8,max_length=20)
         
# class AuthTokenSerializer(serializers.Serializer):
#     """
#     Serializer for the user authentication object
#     """
#     email = serializers.EmailField()
#     password = serializers.CharField(
#         style={'input_type': 'password'},
#         trim_whitespace=False,
#     )
    
#     def validate(self, attrs):
#         email = attrs.get('email')
#         password = attrs.get('password')
#         user = authenticate(email=email,password=password)
#         if user is not None:
#             school = SchoolModel.objects.get(user=user)
#             print('school',school.school_phone)
#             tokens = create_jwt_pair(user)
#             response = {"message": "Login Successfull", "tokens": tokens,"user:":str(school)}
#             return Response(data=response,status=status.HTTP_200_OK)
#         else:
#             return Response(data={"message": "Invalid email or password"})
    