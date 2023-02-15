from rest_framework import serializers
from django.contrib.auth import get_user_model,authenticate
from . import models
from django.utils.translation import gettext as _
from rest_framework.validators import ValidationError
from .function import create_jwt_pair


def generate_staff_user(first_name,phone,joining):
    email = first_name.lower() + phone[-3:] + phone[3:5] + "@classwood.com"
    email_exists = models.Accounts.objects.filter(email=email).exists()
    if email_exists:
        raise ValidationError("User already exists with same name, mobile number")
    joining = joining.isoformat().split('-')
    if len(first_name) > 5:
        first_name = first_name.lower()[0:5]
    else:
        first_name = first_name.lower()[0:len(first_name)] + "5"*(5-len(first_name))
    password = first_name + str(joining[2]) + str(joining[1]) + phone[-2:]
    return {'email':email,'password':password} 



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
    class Meta:
        model = models.ClassroomModel
        fields = "__all__"
        
class ClassroomListSerializer(serializers.ModelSerializer):
    strength = serializers.CharField()
    no_of_subjects = serializers.SerializerMethodField()
    no_of_teachers = serializers.SerializerMethodField()
    
    class Meta:
        model = models.ClassroomModel
        fields = "__all__"
        
    def get_no_of_subjects(self, obj):
        return str(obj.no_of_subjects)
    
    def get_no_of_teachers(self,obj):
        return str(obj.no_of_teachers)
        
class SubjectListSerializer(serializers.ModelSerializer):
    # Doubt how to add property without disrupting swagger
    classroom = serializers.StringRelatedField()
    teacher = serializers.SerializerMethodField(method_name='get_full_name')
    class Meta:
        model = models.Subject
        fields = "__all__"
    
    def get_full_name(self, obj):
        return obj.teacher.full_name
    
# Staff Serializers
class StaffListSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    incharge_of = serializers.CharField()
    sub_incharge_of = serializers.StringRelatedField(many=True)
    class Meta:
        model = models.StaffModel
        fields = "__all__"
        
# class ClassroomDetailSerializer(serializers.ModelSerializer):
#     class_teacher = StaffProfileSerializer()
#     sub_class_teacher = StaffProfileSerializer()
#     class Meta:
#         model = models.ClassroomModel
#         fields = "__all__"
        
class SubjectCreateSerializer(serializers.ModelSerializer):
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
    total_attendance = serializers.SerializerMethodField()
    curent_month_attendance = serializers.SerializerMethodField()
    
    class Meta:
        model = models.StudentModel
        fields = "__all__"
        
    def get_total_attendance(self, obj):
        return str(obj.get_attendance)
    
    def get_current_month_attendance(self, obj):
        return str(obj.get_month_attendance)
    
class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attendance
        fields = "__all__"


    
    
         
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
    