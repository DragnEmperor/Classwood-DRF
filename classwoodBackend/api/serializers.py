from rest_framework import serializers
from django.contrib.auth import get_user_model,authenticate
from . import models
from django.utils.translation import gettext as _
from rest_framework.validators import ValidationError
from .function import create_jwt_pair

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
    user = AccountSerializer()
    # school = SchoolProfileSerializer()
    class Meta:
        model = models.StaffModel
        fields = "__all__"
            
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        return models.StaffModel.objects.create(user=models.Accounts.objects.create_user(**user_data),**validated_data)

class ClassroomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClassroomModel
        fields = "__all__"
        
class AllSubjectSerializer(serializers.ModelSerializer):
    # Doubt
    classroom = serializers.StringRelatedField()
    teacher = serializers.StringRelatedField()
    class Meta:
        model = models.Subject
        fields = "__all__"
    
    
# Staff Serializers
class StaffProfileSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    class Meta:
        model = models.StaffModel
        fields = "__all__"
        
class ClassroomDetailSerializer(serializers.ModelSerializer):
    class_teacher = StaffProfileSerializer()
    sub_class_teacher = StaffProfileSerializer()
    class Meta:
        model = models.ClassroomModel
        fields = "__all__"
        
class SubjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subject
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
    